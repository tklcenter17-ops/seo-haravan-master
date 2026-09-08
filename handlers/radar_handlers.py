"""Handler cho lệnh /radar và /radar_lot: Quét và hiển thị ĐẦY ĐỦ (FULL) các lô bật lửa có bid kết thúc hôm nay."""
from __future__ import annotations

import logging
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from radar_service import format_radar_chunks, format_radar_message, scan_today_lighter_lots
from repository import get_radar_setting, set_radar_setting

logger = logging.getLogger(__name__)

# Bộ nhớ tạm lưu kết quả quét gần nhất để lật trang tức thì
_RADAR_CACHE: dict[str, Any] = {
    "lots": [],
    "cached_at": 0,
}


def _get_radar_page_keyboard(current_page: int, total_pages: int, total_lots: int, is_auto_on: bool) -> InlineKeyboardMarkup:
    """Tạo bàn phím điều khiển và phân trang cho Radar."""
    keyboard = []

    # Hàng 1: Nút điều hướng phân trang nếu có nhiều trang
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Trước", callback_data=f"radar_page:{current_page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"Trang {current_page}/{total_pages}", callback_data="radar_noop"))
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Sau ▶️", callback_data=f"radar_page:{current_page + 1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Hàng 2: Nút gửi toàn bộ dạng loạt tin nhắn (nếu có nhiều hơn 8 lô)
    if total_lots > 8:
        keyboard.append([
            InlineKeyboardButton(f"📜 Gửi toàn bộ {total_lots} lô (Full)", callback_data="radar_send_all")
        ])

    # Hàng 3: Cài đặt và làm mới
    toggle_text = "🔔 Tự động: BẬT" if is_auto_on else "🔕 Tự động: TẮT"
    keyboard.append([
        InlineKeyboardButton("🔄 Quét lại", callback_data="radar_refresh"),
        InlineKeyboardButton(toggle_text, callback_data="radar_toggle_auto"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /radar hoặc /radar_lot.
    
    Cú pháp:
    • /radar: Xem trang đầu kèm nút bấm lật trang và nút gửi toàn bộ
    • /radar all: Bắn toàn bộ 100% tất cả các lô hôm nay thành nhiều tin nhắn
    """
    msg = update.effective_message
    if not msg:
        return

    args = context.args or []
    send_all_requested = any(a.lower() in ("all", "full", "tatca") for a in args)

    wait_msg = await msg.reply_text(
        "🔍 <i>Radar đang quét sâu toàn bộ Yahoo Auctions tìm các lô bật lửa có bid kết thúc hôm nay... Chờ em 3-5 giây!</i>",
        parse_mode="HTML",
    )

    try:
        lots = await scan_today_lighter_lots()
        _RADAR_CACHE["lots"] = lots

        cfg = context.bot_data.get("config")
        is_auto_on = True
        if cfg:
            conn = get_db_connection(cfg.db_path)
            try:
                val = get_radar_setting(conn, "auto_radar_enabled", default="1")
                is_auto_on = (val == "1")
            finally:
                conn.close()

        if send_all_requested:
            # Gửi toàn bộ dạng chunks
            chunks = format_radar_chunks(lots, chunk_size=8)
            await wait_msg.delete()
            for chunk in chunks:
                await msg.reply_text(chunk, parse_mode="HTML", disable_web_page_preview=True)
        else:
            formatted_text, total_pages = format_radar_message(lots, page=1, per_page=8)
            keyboard = _get_radar_page_keyboard(1, total_pages, len(lots), is_auto_on)
            await wait_msg.edit_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
    except Exception as e:
        logger.error(f"Lỗi khi thực thi lệnh /radar: {e}", exc_info=True)
        await wait_msg.edit_text(f"⚠️ <i>Có lỗi xảy ra khi quét Yahoo Auctions: {e}</i>", parse_mode="HTML")


async def radar_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm inline của Radar: lật trang, gửi tất cả, quét lại, bật/tắt tự động."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    await query.answer()

    if data == "radar_noop":
        return

    cfg = context.bot_data.get("config")
    if not cfg:
        return

    conn = get_db_connection(cfg.db_path)
    try:
        val = get_radar_setting(conn, "auto_radar_enabled", default="1")
        is_auto_on = (val == "1")
    finally:
        conn.close()

    if data.startswith("radar_page:"):
        page_num = int(data.split(":")[1])
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots()
            _RADAR_CACHE["lots"] = lots

        formatted_text, total_pages = format_radar_message(lots, page=page_num, per_page=8)
        keyboard = _get_radar_page_keyboard(page_num, total_pages, len(lots), is_auto_on)
        try:
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    elif data == "radar_send_all":
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots()
            _RADAR_CACHE["lots"] = lots

        chunks = format_radar_chunks(lots, chunk_size=8)
        await query.answer("Đang gửi toàn bộ danh sách các lô...", show_alert=False)
        chat = query.message.chat if query.message else None
        if chat:
            for chunk in chunks:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=chunk,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

    elif data == "radar_refresh":
        try:
            await query.edit_message_text("🔄 <i>Đang quét lại toàn bộ Yahoo Auctions...</i>", parse_mode="HTML")
            lots = await scan_today_lighter_lots()
            _RADAR_CACHE["lots"] = lots

            formatted_text, total_pages = format_radar_message(lots, page=1, per_page=8)
            keyboard = _get_radar_page_keyboard(1, total_pages, len(lots), is_auto_on)
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Lỗi khi refresh radar: {e}")
            await query.edit_message_text(f"⚠️ <i>Lỗi làm mới: {e}</i>", parse_mode="HTML")

    elif data == "radar_toggle_auto":
        conn = get_db_connection(cfg.db_path)
        try:
            current_val = get_radar_setting(conn, "auto_radar_enabled", default="1")
            new_val = "0" if current_val == "1" else "1"
            set_radar_setting(conn, "auto_radar_enabled", new_val)
            is_auto_on = (new_val == "1")
        finally:
            conn.close()

        status_str = "BẬT" if is_auto_on else "TẮT"
        await query.answer(f"Đã {status_str} tính năng quét tự động định kỳ!", show_alert=True)
        lots = _RADAR_CACHE.get("lots") or []
        total_pages = max(1, (len(lots) + 7) // 8)
        keyboard = _get_radar_page_keyboard(1, total_pages, len(lots), is_auto_on)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception:
            pass
