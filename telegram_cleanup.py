"""Tự xoá các tin có link bot đã gửi vào Telegram cho nhẹ Telegram và VPS.

Telegram chỉ cho bot xoá tin dưới 48 giờ, nên mốc xoá mặc định là 46 giờ
(biến môi trường LAMQUET_MSG_DELETE_AFTER_HOURS, 0 = tắt, tối đa 47).
Bot chỉ xoá những tin mình đã ghi lại id (bảng sent_messages), không đụng tin nào khác.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from telegram.error import BadRequest, Forbidden, NetworkError, RetryAfter, TelegramError

from db import get_db_connection
from repository import delete_sent_message_rows, get_sent_messages_due, track_sent_message

logger = logging.getLogger(__name__)

DEFAULT_DELETE_AFTER_HOURS = 46.0
MAX_DELETE_AFTER_HOURS = 47.0
# Quá mốc này Telegram từ chối xoá (48 giờ): bỏ ghi nhớ, không gọi nữa
UNDELETABLE_AFTER_SECONDS = 47 * 3600 + 50 * 60
CHUNK_SIZE = 100  # deleteMessages nhận tối đa 100 id mỗi lần


def delete_after_hours() -> float:
    """Số giờ sau khi gửi thì xoá tin (0 = tắt)."""
    raw = os.getenv("LAMQUET_MSG_DELETE_AFTER_HOURS", "").strip()
    if not raw:
        return DEFAULT_DELETE_AFTER_HOURS
    try:
        hours = float(raw)
    except ValueError:
        return DEFAULT_DELETE_AFTER_HOURS
    return max(0.0, min(hours, MAX_DELETE_AFTER_HOURS))


def track_sent(db_path: Any, chat_id: int, result: Any, kind: str) -> None:
    """Ghi nhớ tin (hoặc danh sách tin của một album) vừa gửi. Không bao giờ làm hỏng việc gửi tin."""
    try:
        if result is None:
            return
        items = result if isinstance(result, (list, tuple)) else [result]
        ids = [getattr(m, "message_id", None) for m in items]
        ids = [i for i in ids if isinstance(i, int) and not isinstance(i, bool)]
        if not ids:
            return
        conn = get_db_connection(db_path)
        try:
            for mid in ids:
                track_sent_message(conn, chat_id, mid, kind)
        finally:
            conn.close()
    except Exception as err:  # ghi nhớ lỗi thì bỏ qua, tin vẫn đã gửi
        logger.debug(f"Không ghi nhớ được tin để tự xoá: {err}")


async def cleanup_old_messages(bot: Any, db_path: Any, hours: float | None = None, now: float | None = None) -> dict[str, int]:
    """Xoá các tin đã gửi quá `hours` giờ. Trả về số liệu: deleted / dropped / kept."""
    hours = delete_after_hours() if hours is None else hours
    stats = {"deleted": 0, "dropped": 0, "kept": 0}
    if hours <= 0:
        return stats
    now = time.time() if now is None else now

    conn = get_db_connection(db_path)
    try:
        due = get_sent_messages_due(conn, now - hours * 3600, limit=1000)
    finally:
        conn.close()
    if not due:
        return stats

    forget: list[int] = []  # id dòng sẽ quên sau khi xoá xong
    deletable: dict[int, list[dict[str, Any]]] = {}
    for row in due:
        if row["sent_ts"] <= now - UNDELETABLE_AFTER_SECONDS:
            forget.append(row["id"])
            stats["dropped"] += 1
        else:
            deletable.setdefault(row["chat_id"], []).append(row)

    stop = False
    for chat_id, rows in deletable.items():
        if stop:
            break
        for i in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[i : i + CHUNK_SIZE]
            ids = [r["message_id"] for r in chunk]
            try:
                await bot.delete_messages(chat_id=chat_id, message_ids=ids)
                forget.extend(r["id"] for r in chunk)
                stats["deleted"] += len(chunk)
            except Forbidden as err:
                logger.warning(f"Tự xoá tin: chat {chat_id} đã chặn bot / không cho xoá ({err}), bỏ ghi nhớ {len(rows)} tin của chat này.")
                forget.extend(r["id"] for r in rows)
                stats["dropped"] += len(rows)
                break
            except RetryAfter as err:
                logger.warning(f"Tự xoá tin: Telegram yêu cầu chờ {err.retry_after}s, dừng đợt này, giữ lại để xoá sau.")
                stats["kept"] += len(rows) - i
                stop = True
                break
            except BadRequest as err:
                logger.info(f"Tự xoá tin: xoá theo lô bị từ chối ({err}), thử từng tin.")
                for r in chunk:
                    try:
                        await bot.delete_message(chat_id=chat_id, message_id=r["message_id"])
                        stats["deleted"] += 1
                    except (BadRequest, Forbidden):
                        stats["dropped"] += 1  # đã bị xoá tay / không xoá được nữa
                    except (RetryAfter, NetworkError, TelegramError) as one_err:
                        stats["kept"] += 1
                        logger.warning(f"Tự xoá tin: lỗi tạm thời khi xoá {r['message_id']}: {one_err}")
                        continue
                    forget.append(r["id"])
            except (NetworkError, TelegramError, asyncio.TimeoutError) as err:
                logger.warning(f"Tự xoá tin: lỗi mạng / Telegram ({err}), dừng đợt này, giữ lại để xoá sau.")
                stats["kept"] += len(rows) - i
                stop = True
                break
            await asyncio.sleep(0.3)

    if forget:
        conn = get_db_connection(db_path)
        try:
            delete_sent_message_rows(conn, forget)
        finally:
            conn.close()
    if stats["deleted"] or stats["dropped"]:
        logger.info(f"Tự xoá tin Telegram quá {hours:g} giờ: đã xoá {stats['deleted']}, bỏ ghi nhớ {stats['dropped']}, giữ lại {stats['kept']}.")
    return stats
