"""Quản lý kết nối SQLite, migrations, WAL mode và Backup API native."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

MIGRATION_V1 = """
-- Bảng lưu lịch sử migration
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Bảng bản ghi quẹt đấu thắng
CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY,
    owner_user_id INTEGER NOT NULL,
    raw_text TEXT NOT NULL,
    display_name TEXT NOT NULL,
    normalized_search_text TEXT NOT NULL,
    amount_jpy INTEGER NOT NULL,
    brand TEXT NOT NULL DEFAULT 'unknown',
    line TEXT NOT NULL DEFAULT 'unknown',
    size_submodel TEXT NOT NULL DEFAULT 'unknown',
    material TEXT NOT NULL DEFAULT 'unknown',
    finish TEXT NOT NULL DEFAULT 'unknown',
    color TEXT NOT NULL DEFAULT 'unknown',
    edition TEXT NOT NULL DEFAULT 'unknown',
    box TEXT NOT NULL DEFAULT 'unknown',
    papers TEXT NOT NULL DEFAULT 'unknown',
    accessories_note TEXT NOT NULL DEFAULT '',
    cosmetic_condition TEXT NOT NULL DEFAULT 'unknown',
    functional_state TEXT NOT NULL DEFAULT 'unknown',
    authenticity_note TEXT NOT NULL DEFAULT 'unknown',
    currency TEXT NOT NULL DEFAULT 'JPY',
    record_type TEXT NOT NULL DEFAULT 'win',
    price_basis TEXT NOT NULL DEFAULT 'pure',
    fee_jpy INTEGER NOT NULL DEFAULT 0,
    fee_vnd INTEGER NOT NULL DEFAULT 0,
    is_lot INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    auction_date TEXT,
    auction_id TEXT,
    source_url TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    duplicate_of TEXT,
    parser_version TEXT NOT NULL DEFAULT 'v1'
);

CREATE INDEX IF NOT EXISTS idx_records_owner ON records(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_records_brand_line ON records(brand, line);
CREATE INDEX IF NOT EXISTS idx_records_deleted_at ON records(deleted_at);
CREATE INDEX IF NOT EXISTS idx_records_auction_date ON records(auction_date);

-- FTS5 Full-Text Search Table
CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(
    id UNINDEXED,
    display_name,
    normalized_search_text,
    brand,
    line,
    material,
    color,
    box,
    tokenize = 'unicode61'
);

-- Bảng trần bid cá nhân theo nhóm so sánh
CREATE TABLE IF NOT EXISTS bid_caps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope_key TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    line TEXT NOT NULL,
    material TEXT NOT NULL,
    color TEXT NOT NULL,
    box TEXT NOT NULL,
    condition TEXT NOT NULL,
    cap_amount_jpy INTEGER NOT NULL,
    source_record_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bid_caps_scope ON bid_caps(scope_key);

-- Bảng lịch sử thay đổi để phục vụ /undo
CREATE TABLE IF NOT EXISTS record_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_data TEXT,
    new_data TEXT,
    created_at TEXT NOT NULL
);

-- Bảng lưu bản nháp chờ người dùng xác nhận
CREATE TABLE IF NOT EXISTS drafts (
    draft_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    draft_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Bảng bảo đảm idempotent theo update_id của Telegram
CREATE TABLE IF NOT EXISTS processed_updates (
    update_id INTEGER PRIMARY KEY,
    received_at TEXT NOT NULL,
    processed_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);

-- Bảng outbox gửi tin nhắn chống mất mát khi mạng lỗi
CREATE TABLE IF NOT EXISTS outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_text TEXT NOT NULL,
    reply_markup_json TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    sent_at TEXT
);

-- Bảng hẹn giờ nhắc tàn phiên đấu giá Yahoo
CREATE TABLE IF NOT EXISTS auction_alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id TEXT NOT NULL,
    chat_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    price_jpy INTEGER,
    url TEXT,
    end_time_iso TEXT NOT NULL,
    trigger_at_ts REAL NOT NULL,
    is_sent INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_alarms_pending ON auction_alarms(is_sent, trigger_at_ts);

-- Bảng lưu các lô bật lửa đã quét và thông báo qua Radar
CREATE TABLE IF NOT EXISTS radar_seen_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id TEXT NOT NULL,
    seen_date TEXT NOT NULL,
    title TEXT NOT NULL,
    price_jpy INTEGER NOT NULL,
    bids INTEGER NOT NULL DEFAULT 0,
    end_time TEXT NOT NULL,
    sent_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_radar_seen_aid_date ON radar_seen_lots(auction_id, seen_date);

-- Bảng cài đặt radar
CREATE TABLE IF NOT EXISTS radar_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_db_connection(db_path: Path | str) -> sqlite3.Connection:
    """Tạo kết nối SQLite với WAL mode, foreign keys và row_factory là sqlite3.Row."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: Path | str) -> None:
    """Khởi tạo schema và chạy migrations nếu chưa chạy."""
    conn = get_db_connection(db_path)
    try:
        with conn:
            # Luôn bảo đảm tất cả bảng và index IF NOT EXISTS được áp dụng
            conn.executescript(MIGRATION_V1)
            cur = conn.cursor()
            cur.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);"
            )
            cur.execute("SELECT version FROM schema_migrations WHERE version = 1;")
            row = cur.fetchone()
            if not row:
                now_iso = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?);",
                    (now_iso,),
                )
    finally:
        conn.close()


def backup_database(src_conn: sqlite3.Connection, backup_file_path: Path | str) -> bool:
    """Thực hiện snapshot sao lưu an toàn bằng SQLite Backup API native."""
    dest_path = Path(backup_file_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    dest_conn = sqlite3.connect(str(dest_path))
    try:
        with dest_conn:
            src_conn.backup(dest_conn)
        return True
    finally:
        dest_conn.close()


def restore_database(backup_file_path: Path | str, target_db_path: Path | str) -> bool:
    """Khôi phục database từ file backup vào file target_db_path có kiểm tra integrity."""
    backup_path = Path(backup_file_path)
    if not backup_path.exists():
        return False

    # Kiểm tra integrity của file backup trước
    test_conn = sqlite3.connect(str(backup_path))
    try:
        cur = test_conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()
        if not res or res[0] != "ok":
            return False
    finally:
        test_conn.close()

    target_path = Path(target_db_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    src_conn = sqlite3.connect(str(backup_path))
    target_conn = sqlite3.connect(str(target_path))
    try:
        with target_conn:
            src_conn.backup(target_conn)
        return True
    finally:
        src_conn.close()
        target_conn.close()
