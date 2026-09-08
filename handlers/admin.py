"""Handler quản trị: /export (JSON & CSV), /stats và /cancel."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from db import get_db_connection
from repository import export_records_csv, export_records_json


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /export: Xuất JSON đầy đủ và CSV UTF-8 BOM."""
    if not update.effective_message:
        return

    await update.effective_message.reply_text("Đang trích xuất dữ liệu, vui lòng chờ một chút...")

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        json_data = export_records_json(conn)
        csv_data = export_records_csv(conn)
    finally:
        conn.close()

    now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Gửi file JSON
    json_bytes = io.BytesIO(json_data.encode("utf-8"))
    json_bytes.name = f"quet_vault_{now_str}.json"
    await update.effective_message.reply_document(
        document=json_bytes,
        filename=f"quet_vault_{now_str}.json",
        caption="📦 File JSON đầy đủ schema và phiên bản.",
    )

    # Gửi file CSV
    csv_bytes = io.BytesIO(csv_data.encode("utf-8-sig"))
    csv_bytes.name = f"quet_vault_{now_str}.csv"
    await update.effective_message.reply_document(
        document=csv_bytes,
        filename=f"quet_vault_{now_str}.csv",
        caption="📊 File CSV UTF-8 dễ mở trực tiếp trên Excel.",
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /stats: Báo cáo thống kê dữ liệu hiện có."""
    if not update.effective_message:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM records WHERE deleted_at IS NULL;")
        total_records = cur.fetchone()["cnt"]

        cur.execute(
            """
            SELECT brand, COUNT(*) as cnt
            FROM records
            WHERE deleted_at IS NULL
            GROUP BY brand
            ORDER BY cnt DESC;
            """
        )
        brand_rows = cur.fetchall()

        cur.execute("SELECT COUNT(*) as cnt FROM bid_caps WHERE is_active = 1;")
        total_caps = cur.fetchone()["cnt"]

        lines = [
            "<b>📊 THỐNG KÊ KHO DỮ LIỆU ĐẤU GIÁ:</b>",
            f"• Tổng số bản ghi đang lưu: <b>{total_records}</b> cây",
            f"• Số nhóm đã đặt trần bid: <b>{total_caps}</b> nhóm\n",
            "<b>Phân bổ theo nhãn hiệu:</b>",
        ]
        for r in brand_rows:
            b_name = r["brand"].capitalize() if r["brand"] != "unknown" else "Chưa rõ hiệu"
            lines.append(f"• {b_name}: <b>{r['cnt']}</b> bản ghi")

        await update.effective_message.reply_html("\n".join(lines))
    finally:
        conn.close()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /cancel: Hủy thao tác hiện tại."""
    if not update.effective_message:
        return
    await update.effective_message.reply_text("Đã hủy thao tác hiện tại.")
