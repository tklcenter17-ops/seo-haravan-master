"""Tầng truy xuất dữ liệu (Repository) thực hiện CRUD, bảo đảm Transaction, Revisions và Undo."""
from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from models import BidCap, Draft, Record, RecordRevision, utc_now_iso
from normalizer import clean_search_text


def generate_next_id(conn: sqlite3.Connection) -> str:
    """Tạo mã bản ghi tăng dần có định dạng Q0001, Q0002..."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM records WHERE id LIKE 'Q%' ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if not row:
        return "Q0001"
    last_id = row["id"]
    try:
        num = int(last_id[1:])
        return f"Q{num + 1:04d}"
    except (ValueError, IndexError):
        return "Q0001"


def create_record(conn: sqlite3.Connection, record: Record) -> Record:
    """Thêm một bản ghi mới với Transaction, FTS5 và ghi nhận Revision."""
    now_iso = utc_now_iso()
    record.created_at = record.created_at or now_iso
    record.updated_at = now_iso
    record.normalized_search_text = clean_search_text(record.raw_text)

    with conn:
        conn.execute(
            """
            INSERT INTO records (
                id, owner_user_id, raw_text, display_name, normalized_search_text,
                amount_jpy, brand, line, size_submodel, material, finish, color,
                edition, box, papers, accessories_note, cosmetic_condition,
                functional_state, authenticity_note, currency, record_type,
                price_basis, fee_jpy, fee_vnd, is_lot, note, auction_date,
                auction_id, source_url, created_at, updated_at, deleted_at,
                version, duplicate_of, parser_version
            ) VALUES (
                :id, :owner_user_id, :raw_text, :display_name, :normalized_search_text,
                :amount_jpy, :brand, :line, :size_submodel, :material, :finish, :color,
                :edition, :box, :papers, :accessories_note, :cosmetic_condition,
                :functional_state, :authenticity_note, :currency, :record_type,
                :price_basis, :fee_jpy, :fee_vnd, :is_lot, :note, :auction_date,
                :auction_id, :source_url, :created_at, :updated_at, :deleted_at,
                :version, :duplicate_of, :parser_version
            );
            """,
            record.to_dict(),
        )

        # Cập nhật FTS5
        conn.execute(
            """
            INSERT INTO records_fts (
                id, display_name, normalized_search_text, brand, line, material, color, box
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                record.id,
                record.display_name,
                record.normalized_search_text,
                record.brand,
                record.line,
                record.material,
                record.color,
                record.box,
            ),
        )

        # Ghi nhận lịch sử revision
        conn.execute(
            """
            INSERT INTO record_revisions (record_id, action, previous_data, new_data, created_at)
            VALUES (?, 'create', NULL, ?, ?);
            """,
            (record.id, json.dumps(record.to_dict(), ensure_ascii=False), now_iso),
        )

    return record


def get_record(conn: sqlite3.Connection, record_id: str, include_deleted: bool = False) -> Record | None:
    """Lấy bản ghi theo ID."""
    query = "SELECT * FROM records WHERE id = ?"
    if not include_deleted:
        query += " AND deleted_at IS NULL"
    cur = conn.cursor()
    cur.execute(query, (record_id,))
    row = cur.fetchone()
    if not row:
        return None
    return Record.from_dict(dict(row))


def update_record(conn: sqlite3.Connection, record: Record) -> tuple[bool, str | None]:
    """Cập nhật bản ghi có kiểm tra version để chống xung đột ghi đè."""
    old_record = get_record(conn, record.id, include_deleted=True)
    if not old_record:
        return False, "Bản ghi không tồn tại."

    if old_record.version != record.version:
        return False, f"Xung đột dữ liệu (Bản ghi hiện tại đã là version {old_record.version}, không thể áp dụng version {record.version})."

    new_version = old_record.version + 1
    record.version = new_version
    record.updated_at = utc_now_iso()
    record.normalized_search_text = clean_search_text(record.raw_text)

    with conn:
        conn.execute(
            """
            UPDATE records SET
                raw_text = :raw_text,
                display_name = :display_name,
                normalized_search_text = :normalized_search_text,
                amount_jpy = :amount_jpy,
                brand = :brand,
                line = :line,
                size_submodel = :size_submodel,
                material = :material,
                finish = :finish,
                color = :color,
                edition = :edition,
                box = :box,
                papers = :papers,
                accessories_note = :accessories_note,
                cosmetic_condition = :cosmetic_condition,
                functional_state = :functional_state,
                authenticity_note = :authenticity_note,
                price_basis = :price_basis,
                fee_jpy = :fee_jpy,
                fee_vnd = :fee_vnd,
                is_lot = :is_lot,
                note = :note,
                auction_date = :auction_date,
                updated_at = :updated_at,
                version = :version
            WHERE id = :id AND version = :old_version;
            """,
            {**record.to_dict(), "old_version": old_record.version},
        )

        # Cập nhật FTS
        conn.execute("DELETE FROM records_fts WHERE id = ?;", (record.id,))
        if not record.deleted_at:
            conn.execute(
                """
                INSERT INTO records_fts (
                    id, display_name, normalized_search_text, brand, line, material, color, box
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.id,
                    record.display_name,
                    record.normalized_search_text,
                    record.brand,
                    record.line,
                    record.material,
                    record.color,
                    record.box,
                ),
            )

        # Ghi revision
        conn.execute(
            """
            INSERT INTO record_revisions (record_id, action, previous_data, new_data, created_at)
            VALUES (?, 'update', ?, ?, ?);
            """,
            (
                record.id,
                json.dumps(old_record.to_dict(), ensure_ascii=False),
                json.dumps(record.to_dict(), ensure_ascii=False),
                record.updated_at,
            ),
        )

    return True, None


def soft_delete_record(conn: sqlite3.Connection, record_id: str) -> tuple[bool, str | None]:
    """Xóa mềm bản ghi bằng cách set deleted_at và xóa khỏi FTS."""
    record = get_record(conn, record_id, include_deleted=False)
    if not record:
        return False, f"Không tìm thấy bản ghi {record_id} để xóa."

    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            "UPDATE records SET deleted_at = ?, updated_at = ? WHERE id = ?;",
            (now_iso, now_iso, record_id),
        )
        conn.execute("DELETE FROM records_fts WHERE id = ?;", (record_id,))

        conn.execute(
            """
            INSERT INTO record_revisions (record_id, action, previous_data, new_data, created_at)
            VALUES (?, 'delete', ?, NULL, ?);
            """,
            (record_id, json.dumps(record.to_dict(), ensure_ascii=False), now_iso),
        )

    return True, None


def undo_last_action(conn: sqlite3.Connection) -> tuple[bool, str]:
    """Hoàn tác thao tác dữ liệu gần nhất còn hợp lệ."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM record_revisions ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if not row:
        return False, "Không có thao tác nào để hoàn tác."

    rev_id = row["id"]
    record_id = row["record_id"]
    action = row["action"]
    prev_data_str = row["previous_data"]
    new_data_str = row["new_data"]

    now_iso = utc_now_iso()

    with conn:
        if action == "create":
            # Hoàn tác tạo mới -> xóa mềm bản ghi đó
            conn.execute(
                "UPDATE records SET deleted_at = ?, updated_at = ? WHERE id = ?;",
                (now_iso, now_iso, record_id),
            )
            conn.execute("DELETE FROM records_fts WHERE id = ?;", (record_id,))
            conn.execute("DELETE FROM record_revisions WHERE id = ?;", (rev_id,))
            return True, f"Đã hoàn tác: Thu hồi bản ghi #{record_id} vừa tạo."

        elif action == "delete":
            # Hoàn tác xóa mềm -> phục hồi lại bản ghi
            if not prev_data_str:
                return False, "Thiếu dữ liệu phục hồi."
            prev_data = json.loads(prev_data_str)
            conn.execute(
                "UPDATE records SET deleted_at = NULL, updated_at = ? WHERE id = ?;",
                (now_iso, record_id),
            )
            conn.execute(
                """
                INSERT INTO records_fts (
                    id, display_name, normalized_search_text, brand, line, material, color, box
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record_id,
                    prev_data["display_name"],
                    prev_data["normalized_search_text"],
                    prev_data["brand"],
                    prev_data["line"],
                    prev_data["material"],
                    prev_data["color"],
                    prev_data["box"],
                ),
            )
            conn.execute("DELETE FROM record_revisions WHERE id = ?;", (rev_id,))
            return True, f"Đã hoàn tác: Khôi phục lại bản ghi #{record_id}."

        elif action == "update":
            # Hoàn tác chỉnh sửa -> khôi phục dữ liệu trước chỉnh sửa
            if not prev_data_str:
                return False, "Thiếu dữ liệu trước khi sửa."
            prev_record = Record.from_dict(json.loads(prev_data_str))
            prev_record.updated_at = now_iso
            conn.execute(
                """
                UPDATE records SET
                    raw_text = :raw_text,
                    display_name = :display_name,
                    normalized_search_text = :normalized_search_text,
                    amount_jpy = :amount_jpy,
                    brand = :brand,
                    line = :line,
                    size_submodel = :size_submodel,
                    material = :material,
                    finish = :finish,
                    color = :color,
                    edition = :edition,
                    box = :box,
                    papers = :papers,
                    accessories_note = :accessories_note,
                    cosmetic_condition = :cosmetic_condition,
                    functional_state = :functional_state,
                    authenticity_note = :authenticity_note,
                    price_basis = :price_basis,
                    fee_jpy = :fee_jpy,
                    fee_vnd = :fee_vnd,
                    is_lot = :is_lot,
                    note = :note,
                    auction_date = :auction_date,
                    updated_at = :updated_at
                WHERE id = :id;
                """,
                prev_record.to_dict(),
            )
            conn.execute("DELETE FROM records_fts WHERE id = ?;", (record_id,))
            conn.execute(
                """
                INSERT INTO records_fts (
                    id, display_name, normalized_search_text, brand, line, material, color, box
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record_id,
                    prev_record.display_name,
                    prev_record.normalized_search_text,
                    prev_record.brand,
                    prev_record.line,
                    prev_record.material,
                    prev_record.color,
                    prev_record.box,
                ),
            )
            conn.execute("DELETE FROM record_revisions WHERE id = ?;", (rev_id,))
            return True, f"Đã hoàn tác: Khôi phục trạng thái trước khi sửa của #{record_id}."

    return False, "Không thể hoàn tác."


def get_recent_records(conn: sqlite3.Connection, limit: int = 10, offset: int = 0) -> list[Record]:
    """Lấy danh sách bản ghi mới lưu gần nhất, chưa bị xóa mềm."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM records
        WHERE deleted_at IS NULL
        ORDER BY created_at DESC, id DESC
        LIMIT ? OFFSET ?;
        """,
        (limit, offset),
    )
    rows = cur.fetchall()
    return [Record.from_dict(dict(r)) for r in rows]


def get_records_by_scope(conn: sqlite3.Connection, record: Record) -> list[Record]:
    """Lấy tất cả bản ghi cùng nhóm so sánh chưa bị xóa mềm."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM records
        WHERE deleted_at IS NULL
          AND brand = ?
          AND line = ?
          AND material = ?
          AND color = ?
          AND box = ?
          AND cosmetic_condition = ?
        ORDER BY auction_date DESC, created_at DESC;
        """,
        (
            record.brand,
            record.line,
            record.material,
            record.color,
            record.box,
            record.cosmetic_condition,
        ),
    )
    rows = cur.fetchall()
    return [Record.from_dict(dict(r)) for r in rows]


# Quản lý Trần Bid Cá Nhân (Bid Caps)
def get_bid_cap(conn: sqlite3.Connection, scope_key: str) -> BidCap | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM bid_caps WHERE scope_key = ? AND is_active = 1;",
        (scope_key,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return BidCap.from_dict(dict(row))


def set_bid_cap(conn: sqlite3.Connection, cap: BidCap) -> None:
    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO bid_caps (
                scope_key, brand, line, material, color, box, condition,
                cap_amount_jpy, source_record_id, is_active, created_at, updated_at
            ) VALUES (
                :scope_key, :brand, :line, :material, :color, :box, :condition,
                :cap_amount_jpy, :source_record_id, 1, :created_at, :updated_at
            )
            ON CONFLICT(scope_key) DO UPDATE SET
                cap_amount_jpy = excluded.cap_amount_jpy,
                source_record_id = excluded.source_record_id,
                is_active = 1,
                updated_at = excluded.updated_at;
            """,
            {**cap.to_dict(), "updated_at": now_iso},
        )


def disable_bid_cap(conn: sqlite3.Connection, scope_key: str) -> bool:
    now_iso = utc_now_iso()
    with conn:
        cur = conn.execute(
            "UPDATE bid_caps SET is_active = 0, updated_at = ? WHERE scope_key = ? AND is_active = 1;",
            (now_iso, scope_key),
        )
        return cur.rowcount > 0


# Quản lý Bản Nháp (Drafts)
def save_draft(conn: sqlite3.Connection, draft: Draft) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO drafts (draft_id, user_id, draft_type, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(draft_id) DO UPDATE SET
                draft_type = excluded.draft_type,
                payload = excluded.payload;
            """,
            (
                draft.draft_id,
                draft.user_id,
                draft.draft_type,
                json.dumps(draft.payload, ensure_ascii=False),
                draft.created_at,
            ),
        )


def get_draft(conn: sqlite3.Connection, draft_id: str) -> Draft | None:
    cur = conn.cursor()
    cur.execute("SELECT * FROM drafts WHERE draft_id = ?;", (draft_id,))
    row = cur.fetchone()
    if not row:
        return None
    return Draft(
        draft_id=row["draft_id"],
        user_id=row["user_id"],
        draft_type=row["draft_type"],
        payload=json.loads(row["payload"]),
        created_at=row["created_at"],
    )


def delete_draft(conn: sqlite3.Connection, draft_id: str) -> None:
    with conn:
        conn.execute("DELETE FROM drafts WHERE draft_id = ?;", (draft_id,))


# Bảo đảm Idempotent theo update_id Telegram
def register_update_if_new(conn: sqlite3.Connection, update_id: int) -> bool:
    """Trả về True nếu update_id chưa từng xuất hiện. Nếu đã có -> trả về False."""
    now_iso = utc_now_iso()
    try:
        with conn:
            conn.execute(
                "INSERT INTO processed_updates (update_id, received_at, status) VALUES (?, ?, 'pending');",
                (update_id, now_iso),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def mark_update_processed(conn: sqlite3.Connection, update_id: int) -> None:
    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            "UPDATE processed_updates SET processed_at = ?, status = 'processed' WHERE update_id = ?;",
            (now_iso, update_id),
        )


# Export dữ liệu an toàn
def export_records_json(conn: sqlite3.Connection) -> str:
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY id ASC;")
    rows = [dict(r) for r in cur.fetchall()]
    payload = {
        "export_date": utc_now_iso(),
        "total_records": len(rows),
        "records": rows,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_records_csv(conn: sqlite3.Connection) -> str:
    """Xuất CSV UTF-8 kèm xử lý chống CSV Formula Injection (các ô bắt đầu bằng =, +, -, @)."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY id ASC;")
    rows = cur.fetchall()

    output = io.StringIO()
    # Ghi UTF-8 BOM để Excel hiển thị tiếng Việt chuẩn
    output.write("\ufeff")

    if not rows:
        return output.getvalue()

    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for r in rows:
        row_dict = dict(r)
        # Sanitization chống injection
        sanitized_dict = {}
        for k, v in row_dict.items():
            if isinstance(v, str) and v and v[0] in ("=", "+", "-", "@"):
                sanitized_dict[k] = "'" + v
            else:
                sanitized_dict[k] = v
        writer.writerow(sanitized_dict)

    return output.getvalue()


def add_auction_alarm(
    conn: sqlite3.Connection,
    auction_id: str,
    chat_id: int,
    title: str,
    price_jpy: int | None,
    url: str,
    end_time_iso: str,
    trigger_at_ts: float,
) -> int:
    """Lưu một báo thức hẹn giờ canh tàn phiên Yahoo."""
    with conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO auction_alarms (
                auction_id, chat_id, title, price_jpy, url, end_time_iso, trigger_at_ts, is_sent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?);
            """,
            (auction_id, chat_id, title, price_jpy, url, end_time_iso, trigger_at_ts, utc_now_iso()),
        )
        return cur.lastrowid or 0


def has_auction_alarm(conn: sqlite3.Connection, auction_id: str, chat_id: int) -> bool:
    """Kiểm tra xem lô này đã được đặt báo thức cho chat_id chưa."""
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM auction_alarms WHERE auction_id = ? AND chat_id = ? LIMIT 1;",
        (auction_id, chat_id),
    )
    return cur.fetchone() is not None


def get_pending_alarms(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Lấy danh sách các báo thức hẹn giờ chưa gửi."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM auction_alarms WHERE is_sent = 0 ORDER BY trigger_at_ts ASC;")
    return [dict(r) for r in cur.fetchall()]


def mark_alarm_sent(conn: sqlite3.Connection, alarm_id: int) -> None:
    """Đánh dấu báo thức đã gửi thành công."""
    with conn:
        conn.execute("UPDATE auction_alarms SET is_sent = 1 WHERE id = ?;", (alarm_id,))


def claim_alarm(conn: sqlite3.Connection, alarm_id: int) -> bool:
    """Giành quyền gửi một báo thức (chỉ 1 nơi thắng): True nếu báo thức chưa gửi và nay đã được nhận gửi.

    Báo thức người dùng tự đặt có 2 nơi cùng gửi (tác vụ hẹn giờ riêng + vòng kiểm 60 s);
    đánh dấu trước khi gửi để không bao giờ gửi 2 lần.
    """
    with conn:
        cur = conn.execute("UPDATE auction_alarms SET is_sent = 1 WHERE id = ? AND is_sent = 0;", (alarm_id,))
        return cur.rowcount == 1


def find_recent_similar_record(conn: sqlite3.Connection, brand: str, line: str = "") -> Record | None:
    """Tìm bản ghi tương tự gần nhất trong kho của user để đối chiếu giá quá khứ."""
    if not brand or brand == "unknown":
        return None
    cur = conn.cursor()
    if line and line != "unknown":
        cur.execute(
            """
            SELECT * FROM records 
            WHERE brand = ? AND line = ? AND deleted_at IS NULL AND is_lot = 0
            ORDER BY created_at DESC LIMIT 1;
            """,
            (brand, line),
        )
    else:
        cur.execute(
            """
            SELECT * FROM records 
            WHERE brand = ? AND deleted_at IS NULL AND is_lot = 0
            ORDER BY created_at DESC LIMIT 1;
            """,
            (brand,),
        )
    row = cur.fetchone()
    if not row:
        return None
    return Record(**dict(row))


def update_lot_restoration(
    conn: sqlite3.Connection,
    record_id_or_auction_id: str,
    song: int,
    chet: int,
) -> dict[str, Any] | None:
    """Cập nhật kết quả dọn lô và phân bổ lại giá vốn thực tế cho từng cây sống."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM records 
        WHERE (id = ? OR auction_id = ?) AND deleted_at IS NULL LIMIT 1;
        """,
        (record_id_or_auction_id, record_id_or_auction_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    
    rec = Record(**dict(row))
    rate = 165
    total_cost_vnd = round((rec.amount_jpy + (rec.fee_jpy or 0)) * rate)
    
    cost_per_alive_vnd = round(total_cost_vnd / song) if song > 0 else total_cost_vnd
    
    restoration_note = (
        f"Đã dọn: {song} sống, {chet} rã xác. "
        f"Giá vốn thực: ~{cost_per_alive_vnd:,} đ/cây sống (Tổng vốn: ~{total_cost_vnd:,} đ)."
    ).replace(",", ".")
    
    updated_note = f"{rec.note} | {restoration_note}" if rec.note else restoration_note
    rec.note = updated_note
    rec.updated_at = utc_now_iso()
    
    with conn:
        conn.execute(
            "UPDATE records SET note = ?, updated_at = ? WHERE id = ?;",
            (rec.note, rec.updated_at, rec.id),
        )
        
    return {
        "record_id": rec.id,
        "display_name": rec.display_name,
        "total_cost_vnd": total_cost_vnd,
        "song": song,
        "chet": chet,
        "cost_per_alive_vnd": cost_per_alive_vnd,
        "note": rec.note,
    }


def is_lot_seen(conn: sqlite3.Connection, auction_id: str, seen_date: str) -> bool:
    """Kiểm tra xem lô này đã được thông báo trong ngày seen_date chưa."""
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM radar_seen_lots WHERE auction_id = ? AND seen_date = ? LIMIT 1;",
        (auction_id, seen_date),
    )
    return cur.fetchone() is not None


def is_lot_seen_any(conn: sqlite3.Connection, auction_id: str) -> bool:
    """Lô này đã từng được gửi vào bot chưa (bất kể ngày nào).

    Radar lấy lô "hôm nay" theo giờ Nhật, lệch ngày VN 2 tiếng: lô báo lúc 22h-24h VN
    qua 0h VN vẫn còn trong danh sách. Chống trùng theo ngày sẽ gửi lại lần 2, nên chỉ xét auction_id.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM radar_seen_lots WHERE auction_id = ? LIMIT 1;",
        (auction_id,),
    )
    return cur.fetchone() is not None


def mark_lot_seen(
    conn: sqlite3.Connection,
    auction_id: str,
    seen_date: str,
    title: str,
    price_jpy: int,
    bids: int,
    end_time: str,
) -> None:
    """Đánh dấu lô đã thông báo trong ngày seen_date để chống spam lặp lại."""
    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO radar_seen_lots (auction_id, seen_date, title, price_jpy, bids, end_time, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (auction_id, seen_date, title, price_jpy, bids, end_time, now_iso),
        )


def get_radar_setting(conn: sqlite3.Connection, key: str, default: str = "1") -> str:
    """Lấy giá trị cài đặt radar."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM radar_settings WHERE key = ? LIMIT 1;", (key,))
    row = cur.fetchone()
    if not row:
        return default
    return str(row["value"])


def set_radar_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    """Lưu giá trị cài đặt radar."""
    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO radar_settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at;
            """,
            (key, value, now_iso),
        )


def get_exchange_rate(conn: sqlite3.Connection, default: int = 165) -> int:
    """Lấy tỷ giá JPY sang VND (mặc định 165)."""
    val = get_radar_setting(conn, "exchange_rate_jpy_vnd", default=str(default))
    try:
        r = int(val)
        return r if r > 0 else default
    except (ValueError, TypeError):
        return default


def set_exchange_rate(conn: sqlite3.Connection, rate: int) -> None:
    """Lưu tỷ giá JPY sang VND."""
    set_radar_setting(conn, "exchange_rate_jpy_vnd", str(rate))


def save_lot_audit_log(
    conn: sqlite3.Connection,
    auction_id: str,
    title: str,
    decision_code: str,
    lighter_count: int | None = None,
    condition_label: str = "",
    brands: str = "",
    evidence_reason: str = "",
    price_jpy: int = 0,
    bids: int = 0,
    end_time: str = "",
    url: str = "",
    image_url: str = "",
) -> None:
    """Lưu vết phân loại kiểm toán của một phiên đấu Yahoo."""
    now_iso = utc_now_iso()
    with conn:
        conn.execute(
            """
            INSERT INTO yahoo_lot_audit_log (
                auction_id, title, decision_code, lighter_count, condition_label,
                brands, evidence_reason, price_jpy, bids, end_time, url, image_url, scanned_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                auction_id, title, decision_code, lighter_count, condition_label,
                brands, evidence_reason, price_jpy, bids, end_time, url, image_url, now_iso
            ),
        )


def get_lot_audit_logs(
    conn: sqlite3.Connection,
    decision_code: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Truy vấn danh sách audit log các phiên Yahoo đã phân loại."""
    cur = conn.cursor()
    if decision_code:
        cur.execute(
            """
            SELECT * FROM yahoo_lot_audit_log
            WHERE decision_code = ?
            ORDER BY scanned_at DESC, id DESC
            LIMIT ?;
            """,
            (decision_code, limit),
        )
    else:
        cur.execute(
            """
            SELECT * FROM yahoo_lot_audit_log
            ORDER BY scanned_at DESC, id DESC
            LIMIT ?;
            """,
            (limit,),
        )
    rows = cur.fetchall()
    return [dict(r) for r in rows]


def get_lot_audit_stats(conn: sqlite3.Connection) -> dict[str, int]:
    """Thống kê tổng quan các ca audit theo từng decision_code."""
    cur = conn.cursor()
    cur.execute("SELECT decision_code, COUNT(*) as cnt FROM yahoo_lot_audit_log GROUP BY decision_code;")
    stats: dict[str, int] = {}
    total = 0
    for r in cur.fetchall():
        code = str(r["decision_code"])
        cnt = int(r["cnt"])
        stats[code] = cnt
        total += cnt
    stats["total"] = total
    return stats


def prune_old_radar_data(
    conn: sqlite3.Connection,
    retention_days: int = 3,
) -> dict[str, int]:
    """Xóa an toàn các dữ liệu link radar, audit logs, báo thức và tracking cũ hơn retention_days ngày.
    
    Giúp giảm dung lượng SQLite, tối ưu hiệu năng Dashboard Admin và giải phóng RAM/Disk VPS.
    Tuyệt đối bảo toàn 100% dữ liệu kho quẹt (records), trần bid (bid_caps), revisions.
    """
    if retention_days < 1:
        retention_days = 1

    now_utc = datetime.now(timezone.utc)
    threshold_dt = now_utc - timedelta(days=retention_days)
    threshold_iso = threshold_dt.isoformat()
    # Mốc ngày Việt Nam YYYY-MM-DD
    threshold_date_vn = (now_utc.astimezone(timezone(timedelta(hours=7))) - timedelta(days=retention_days)).strftime("%Y-%m-%d")
    threshold_ts = threshold_dt.timestamp()

    result = {
        "audit_logs": 0,
        "seen_lots": 0,
        "alarms": 0,
        "processed_updates": 0,
        "total": 0,
    }

    cur = conn.cursor()
    with conn:
        # 1. Dọn bảng audit logs cũ
        cur.execute("DELETE FROM yahoo_lot_audit_log WHERE scanned_at < ?;", (threshold_iso,))
        result["audit_logs"] = cur.rowcount if cur.rowcount > 0 else 0

        # 2. Dọn bảng link radar đã quét cũ
        cur.execute("DELETE FROM radar_seen_lots WHERE seen_date < ? OR sent_at < ?;", (threshold_date_vn, threshold_iso))
        result["seen_lots"] = cur.rowcount if cur.rowcount > 0 else 0

        # 3. Dọn bảng báo thức đã gửi xong cũ
        cur.execute("DELETE FROM auction_alarms WHERE is_sent = 1 AND trigger_at_ts < ?;", (threshold_ts,))
        result["alarms"] = cur.rowcount if cur.rowcount > 0 else 0

        # 4. Dọn bảng processed_updates cũ
        cur.execute("DELETE FROM processed_updates WHERE received_at < ?;", (threshold_iso,))
        result["processed_updates"] = cur.rowcount if cur.rowcount > 0 else 0

    result["total"] = (
        result["audit_logs"]
        + result["seen_lots"]
        + result["alarms"]
        + result["processed_updates"]
    )
    return result


def vacuum_database(conn: sqlite3.Connection) -> None:
    """Thực thi VACUUM để SQLite thu hồi dung lượng đĩa thực tế sau khi xóa dữ liệu.
    
    Lưu ý: Phải commit transaction trước khi chạy VACUUM.
    """
    conn.commit()
    conn.execute("VACUUM;")


def get_db_file_size_bytes(db_path: Path | str) -> int:
    """Lấy kích thước file database theo bytes."""
    try:
        return Path(db_path).stat().st_size
    except OSError:
        return 0


# ==========================================
# KANBAN & P&L TRACKING REPOSITORY FUNCTIONS
# ==========================================

VALID_KANBAN_STAGES = ("bidding", "transit", "restoring", "selling", "sold")


def create_kanban_item(
    conn: sqlite3.Connection,
    title: str,
    brand: str = "unknown",
    auction_id: str = "",
    stage: str = "bidding",
    buy_price_jpy: int = 0,
    buy_price_vnd: int = 0,
    shipping_cost_vnd: int = 0,
    repair_cost_vnd: int = 0,
    sale_price_vnd: int = 0,
    image_url: str = "",
    source_url: str = "",
    notes: str = "",
) -> dict[str, Any]:
    """Tạo một thẻ hàng hóa mới trên luồng Kanban."""
    stage_clean = stage.lower().strip()
    if stage_clean not in VALID_KANBAN_STAGES:
        stage_clean = "bidding"

    now_iso = datetime.now(timezone.utc).isoformat()
    cur = conn.cursor()
    with conn:
        cur.execute(
            """
            INSERT INTO kanban_items (
                auction_id, title, brand, stage,
                buy_price_jpy, buy_price_vnd, shipping_cost_vnd,
                repair_cost_vnd, sale_price_vnd, image_url,
                source_url, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                auction_id,
                title,
                brand,
                stage_clean,
                buy_price_jpy,
                buy_price_vnd,
                shipping_cost_vnd,
                repair_cost_vnd,
                sale_price_vnd,
                image_url,
                source_url,
                notes,
                now_iso,
                now_iso,
            ),
        )
        item_id = cur.lastrowid

    return {
        "id": item_id,
        "auction_id": auction_id,
        "title": title,
        "brand": brand,
        "stage": stage_clean,
        "buy_price_jpy": buy_price_jpy,
        "buy_price_vnd": buy_price_vnd,
        "shipping_cost_vnd": shipping_cost_vnd,
        "repair_cost_vnd": repair_cost_vnd,
        "sale_price_vnd": sale_price_vnd,
        "image_url": image_url,
        "source_url": source_url,
        "notes": notes,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def get_kanban_items(conn: sqlite3.Connection, stage: str | None = None) -> list[dict[str, Any]]:
    """Lấy danh sách các thẻ Kanban, có thể lọc theo stage."""
    cur = conn.cursor()
    if stage and stage in VALID_KANBAN_STAGES:
        cur.execute(
            "SELECT * FROM kanban_items WHERE stage = ? ORDER BY id DESC;",
            (stage,),
        )
    else:
        cur.execute("SELECT * FROM kanban_items ORDER BY id DESC;")

    rows = cur.fetchall()
    return [dict(r) for r in rows]


def update_kanban_stage(conn: sqlite3.Connection, item_id: int, new_stage: str) -> bool:
    """Chuyển thẻ hàng hóa sang cột quy trình mới."""
    stage_clean = new_stage.lower().strip()
    if stage_clean not in VALID_KANBAN_STAGES:
        return False

    now_iso = datetime.now(timezone.utc).isoformat()
    with conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE kanban_items SET stage = ?, updated_at = ? WHERE id = ?;",
            (stage_clean, now_iso, item_id),
        )
        return cur.rowcount > 0


def update_kanban_item(conn: sqlite3.Connection, item_id: int, data: dict[str, Any]) -> bool:
    """Cập nhật chi phí, giá bán hoặc ghi chú của thẻ Kanban."""
    allowed_fields = [
        "title", "brand", "stage", "buy_price_jpy", "buy_price_vnd",
        "shipping_cost_vnd", "repair_cost_vnd", "sale_price_vnd",
        "notes", "image_url", "source_url"
    ]
    updates = []
    params = []
    for k, v in data.items():
        if k in allowed_fields:
            updates.append(f"{k} = ?")
            params.append(v)

    if not updates:
        return False

    now_iso = datetime.now(timezone.utc).isoformat()
    updates.append("updated_at = ?")
    params.append(now_iso)
    params.append(item_id)

    with conn:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE kanban_items SET {', '.join(updates)} WHERE id = ?;",
            tuple(params),
        )
        return cur.rowcount > 0


def delete_kanban_item(conn: sqlite3.Connection, item_id: int) -> bool:
    """Xóa một thẻ hàng hóa khỏi Kanban."""
    with conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM kanban_items WHERE id = ?;", (item_id,))
        return cur.rowcount > 0


def get_kanban_pnl_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    """Tính toán toàn diện các chỉ số tài chính P&L từ dữ liệu Kanban."""
    cur = conn.cursor()

    # 1. Thống kê số lượng theo từng cột stage
    cur.execute("SELECT stage, COUNT(*) as cnt FROM kanban_items GROUP BY stage;")
    stage_counts = {s: 0 for s in VALID_KANBAN_STAGES}
    for r in cur.fetchall():
        stage_counts[r["stage"]] = r["cnt"]

    # 2. Tổng vốn đầu tư (VND) cho các lô đã mua (transit, restoring, selling, sold)
    cur.execute(
        """
        SELECT 
            COALESCE(SUM(buy_price_vnd + shipping_cost_vnd + repair_cost_vnd), 0) as total_invested,
            COALESCE(SUM(buy_price_vnd), 0) as total_purchase,
            COALESCE(SUM(shipping_cost_vnd), 0) as total_shipping,
            COALESCE(SUM(repair_cost_vnd), 0) as total_restoring
        FROM kanban_items
        WHERE stage != 'bidding';
        """
    )
    inv_row = cur.fetchone()
    total_invested = inv_row["total_invested"]
    total_purchase = inv_row["total_purchase"]
    total_shipping = inv_row["total_shipping"]
    total_restoring = inv_row["total_restoring"]

    # 3. Hàng đã bán (stage = 'sold') -> Lợi nhuận ròng thực tế
    cur.execute(
        """
        SELECT 
            COALESCE(SUM(sale_price_vnd), 0) as realized_revenue,
            COALESCE(SUM(buy_price_vnd + shipping_cost_vnd + repair_cost_vnd), 0) as realized_cogs,
            COUNT(*) as sold_count
        FROM kanban_items
        WHERE stage = 'sold';
        """
    )
    sold_row = cur.fetchone()
    realized_revenue = sold_row["realized_revenue"]
    realized_cogs = sold_row["realized_cogs"]
    sold_count = sold_row["sold_count"]
    realized_net_profit = realized_revenue - realized_cogs
    roi_pct = round((realized_net_profit / realized_cogs * 100), 1) if realized_cogs > 0 else 0.0

    # 4. Hàng đang tồn kho (transit, restoring, selling)
    cur.execute(
        """
        SELECT 
            COALESCE(SUM(buy_price_vnd + shipping_cost_vnd + repair_cost_vnd), 0) as active_inventory_cost,
            COALESCE(SUM(sale_price_vnd), 0) as projected_revenue,
            COUNT(*) as active_inventory_count
        FROM kanban_items
        WHERE stage IN ('transit', 'restoring', 'selling');
        """
    )
    stock_row = cur.fetchone()
    active_inv_cost = stock_row["active_inventory_cost"]
    projected_revenue = stock_row["projected_revenue"]
    active_inv_count = stock_row["active_inventory_count"]
    projected_profit = projected_revenue - active_inv_cost if projected_revenue > 0 else 0

    return {
        "stage_counts": stage_counts,
        "total_invested": total_invested,
        "total_purchase": total_purchase,
        "total_shipping": total_shipping,
        "total_restoring": total_restoring,
        "realized_revenue": realized_revenue,
        "realized_cogs": realized_cogs,
        "realized_net_profit": realized_net_profit,
        "roi_pct": roi_pct,
        "sold_count": sold_count,
        "active_inventory_cost": active_inv_cost,
        "projected_revenue": projected_revenue,
        "projected_profit": projected_profit,
        "active_inventory_count": active_inv_count,
    }



