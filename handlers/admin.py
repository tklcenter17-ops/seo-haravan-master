"""Handler quản trị: /export (JSON & CSV), /stats và /cancel."""
from __future__ import annotations

import io
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from db import get_db_connection
from repository import (
    export_records_csv,
    export_records_json,
    get_db_file_size_bytes,
    prune_old_radar_data,
    vacuum_database,
)


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


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /rate: Xem hoặc cập nhật tỷ giá JPY sang VND."""
    if not update.effective_message:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        from repository import get_exchange_rate, set_exchange_rate

        args = context.args or []
        if args:
            raw_val = args[0].strip().replace("k", "").replace(".", "").replace(",", "")
            try:
                new_rate = int(raw_val)
                if new_rate < 50 or new_rate > 500:
                    await update.effective_message.reply_html(
                        "⚠️ Tỷ giá không hợp lý (chỉ nhận từ 50 đến 500 VND/JPY).\n"
                        "<i>Ví dụ: <code>/rate 168</code></i>"
                    )
                    return
                set_exchange_rate(conn, new_rate)
                one_man = new_rate * 10000
                await update.effective_message.reply_html(
                    f"✅ <b>ĐÃ CẬP NHẬT TỶ GIÁ THÀNH CÔNG!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"• 🇯🇵 <b>1 JPY:</b> <b>{new_rate} VND</b>\n"
                    f"• 🇯🇵 <b>1 Man (10.000 JPY):</b> <b>{one_man:,} đ</b>\n\n"
                    f"<i>Toàn bộ tính nhẩm về tay, phân tích lô và mốc bid sẽ áp dụng tỷ giá mới này!</i>".replace(",", ".")
                )
                return
            except ValueError:
                await update.effective_message.reply_html(
                    "⚠️ Tỷ giá phải là số nguyên hợp lệ.\n"
                    "<i>Ví dụ: <code>/rate 168</code></i>"
                )
                return

        # Xem tỷ giá hiện tại
        current_rate = get_exchange_rate(conn)
        one_man = current_rate * 10000
        five_man = current_rate * 50000
        msg = (
            f"💴 <b>TỶ GIÁ YÊN NHẬT HIỆN TẠI TRONG HỆ THỐNG:</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"• <b>1 JPY:</b> <b>{current_rate} VND</b>\n"
            f"• <b>1.000 JPY:</b> ~{current_rate * 1000:,} đ\n"
            f"• <b>1 Man (10.000 JPY):</b> ~{one_man:,} đ\n"
            f"• <b>5 Man (50.000 JPY):</b> ~{five_man:,} đ\n\n"
            f"💡 <b>Cách đổi tỷ giá mới:</b>\n"
            f"Gõ: <code>/rate 168</code> (hoặc mức tỷ giá thực tế thẻ/chợ đen của anh)".replace(",", ".")
        )
        await update.effective_message.reply_html(msg)
    finally:
        conn.close()


async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /clean [số_ngày]: Dọn dẹp an toàn các link radar, audit log và chuông báo thức cũ.
    
    Mặc định dọn dẹp các link cũ quá 3 ngày, chạy VACUUM SQLite giúp nhẹ admin và VPS.
    Bảo toàn 100% dữ liệu kho quẹt (records).
    """
    if not update.effective_message:
        return

    config = context.bot_data.get("config")
    user = update.effective_user
    if config and config.owner_id and user and user.id != config.owner_id:
        await update.effective_message.reply_text("⛔ Lệnh này chỉ dành riêng cho Admin/Owner của Bot.")
        return

    days = 3
    if context.args:
        try:
            val = int(context.args[0])
            if 1 <= val <= 30:
                days = val
        except ValueError:
            pass

    status_msg = await update.effective_message.reply_html(
        f"🧹 <b>ĐANG BẮT ĐẦU DỌN DẸP DỮ LIỆU CŨ QUÁ {days} NGÀY...</b>\n"
        f"<i>Hệ thống đang quét các bảng radar_seen_lots, yahoo_lot_audit_log, auction_alarms và chạy VACUUM SQLite. Vui lòng chờ vài giây...</i>"
    )

    db_path = config.db_path
    size_before = get_db_file_size_bytes(db_path)

    conn = get_db_connection(db_path)
    try:
        res = prune_old_radar_data(conn, retention_days=days)
        vacuum_database(conn)
    finally:
        conn.close()

    size_after = get_db_file_size_bytes(db_path)
    size_before_mb = size_before / (1024 * 1024)
    size_after_mb = size_after / (1024 * 1024)
    freed_mb = (size_before - size_after) / (1024 * 1024)
    if freed_mb < 0:
        freed_mb = 0.0

    report = (
        f"✅ <b>DỌN DẸP DỮ LIỆU CŨ THÀNH CÔNG!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Mốc thời gian:</b> Xóa dữ liệu cũ hơn <b>{days} ngày</b>\n"
        f"🛡️ <b>Audit Logs cũ đã xóa:</b> <b>{res['audit_logs']:,}</b> ca\n"
        f"🎯 <b>Link Radar đã quét cũ:</b> <b>{res['seen_lots']:,}</b> link\n"
        f"⏰ <b>Báo thức cũ đã kết thúc:</b> <b>{res['alarms']:,}</b> chuông\n"
        f"🔄 <b>Telegram updates cũ:</b> <b>{res['processed_updates']:,}</b> update\n"
        f"📦 <b>Tổng cộng đã dọn:</b> <b>{res['total']:,}</b> bản ghi\n\n"
        f"💾 <b>DUNG LƯỢNG DATABASE TRÊN VPS:</b>\n"
        f"• Trước khi dọn: <b>{size_before_mb:.2f} MB</b>\n"
        f"• Sau khi VACUUM: <b>{size_after_mb:.2f} MB</b>\n"
        f"• Tiết kiệm được: <b>{freed_mb:.2f} MB</b>\n\n"
        f"💎 <b>KHO QUẸT CHÍNH:</b> Bảo toàn <b>100%</b> dữ liệu nguyên vẹn!".replace(",", ".")
    )
    if status_msg:
        await status_msg.edit_text(report, parse_mode="HTML")
    else:
        await update.effective_message.reply_html(report)

