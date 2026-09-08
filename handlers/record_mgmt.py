"""Handler quản lý bản ghi: /recent, /view, /edit, /delete và /undo."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from repository import (
    get_recent_records,
    get_record,
    soft_delete_record,
    undo_last_action,
)


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị 10 bản ghi gần nhất."""
    if not update.effective_message:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        records = get_recent_records(conn, limit=10, offset=0)
        if not records:
            await update.effective_message.reply_text("Chưa có bản ghi nào được lưu trong hệ thống.")
            return

        lines = ["<b>📋 10 BẢN GHI ĐÃ LƯU GẦN NHẤT:</b>\n"]
        for idx, r in enumerate(records, start=1):
            date_part = f"({r.auction_date})" if r.auction_date else "(Chưa rõ ngày)"
            lines.append(f"<b>{idx}. #{r.id}</b>: {r.display_name} — <b>{r.amount_jpy:,}Y</b> {date_part}")

        keyboard = []
        for r in records[:5]:
            keyboard.append([InlineKeyboardButton(f"Xem #{r.id}: {r.display_name[:24]}", callback_data=f"view_rec:{r.id}")])

        await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        conn.close()


async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xem chi tiết một bản ghi theo ID: /view Q0001."""
    if not update.effective_message:
        return

    text = update.effective_message.text or ""
    parts = text.split()
    if len(parts) < 2:
        await update.effective_message.reply_text("Vui lòng nhập ID bản ghi. Ví dụ: /view Q0001")
        return

    rec_id = parts[1].strip().upper()
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        record = get_record(conn, rec_id)
        if not record:
            await update.effective_message.reply_text(f"Không tìm thấy bản ghi #{rec_id}.")
            return

        lines = [
            f"<b>CHI TIẾT BẢN GHI #{record.id}</b>",
            f"<b>Mô tả:</b> {record.display_name}",
            f"<b>Giá thắng:</b> {record.amount_jpy:,} JPY",
            f"<b>Nhãn hiệu:</b> {record.brand.capitalize()} | <b>Dòng:</b> {record.line}",
            f"<b>Chất liệu:</b> {record.material} | <b>Màu:</b> {record.color}",
            f"<b>Hộp:</b> {record.box} | <b>Phụ kiện:</b> {record.accessories_note or 'Không có'}",
            f"<b>Tình trạng:</b> {record.cosmetic_condition}",
            f"<b>Ngày đấu:</b> {record.auction_date or 'Chưa nhập'}",
            f"<b>Ngày tạo:</b> {record.created_at[:19].replace('T', ' ')} UTC",
            f"<b>Version:</b> {record.version}",
        ]
        if record.fee_jpy > 0:
            lines.append(f"<b>Phí Nhật:</b> {record.fee_jpy:,} JPY")
        if record.fee_vnd > 0:
            lines.append(f"<b>Phí VN:</b> {record.fee_vnd:,} VND")
        if record.note:
            lines.append(f"<b>Ghi chú:</b> {record.note}")

        keyboard = [
            [
                InlineKeyboardButton(f"🎯 Đặt trần {record.amount_jpy:,}Y", callback_data=f"cap_set:{record.id}:{record.amount_jpy}"),
                InlineKeyboardButton("🗑️ Xóa bản ghi", callback_data=f"del_prompt:{record.id}"),
            ]
        ]

        await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        conn.close()


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yêu cầu xóa mềm bản ghi có xác nhận: /delete Q0001."""
    if not update.effective_message:
        return

    text = update.effective_message.text or ""
    parts = text.split()
    if len(parts) < 2:
        await update.effective_message.reply_text("Vui lòng nhập ID bản ghi cần xóa. Ví dụ: /delete Q0001")
        return

    rec_id = parts[1].strip().upper()
    keyboard = [
        [
            InlineKeyboardButton(f"⚠️ Xác nhận xóa #{rec_id}", callback_data=f"del_confirm:{rec_id}"),
            InlineKeyboardButton("Hủy", callback_data="del_cancel"),
        ]
    ]
    await update.effective_message.reply_html(
        f"Anh có chắc chắn muốn xóa mềm bản ghi <b>#{rec_id}</b> không?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /undo: Hoàn tác thao tác gần nhất."""
    if not update.effective_message:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        ok, msg = undo_last_action(conn)
        if ok:
            await update.effective_message.reply_html(f"↩️ {msg}")
        else:
            await update.effective_message.reply_text(f"⚠️ {msg}")
    finally:
        conn.close()


async def record_mgmt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các callback liên quan đến xem, xóa, hoàn tác bản ghi."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    data = query.data
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        if data.startswith("del_prompt:"):
            rec_id = data.split(":")[1]
            keyboard = [
                [
                    InlineKeyboardButton(f"⚠️ Xác nhận xóa #{rec_id}", callback_data=f"del_confirm:{rec_id}"),
                    InlineKeyboardButton("Hủy", callback_data="del_cancel"),
                ]
            ]
            await query.edit_message_text(
                f"Anh có chắc chắn muốn xóa mềm bản ghi <b>#{rec_id}</b> không?",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        elif data.startswith("del_confirm:"):
            rec_id = data.split(":")[1]
            ok, err = soft_delete_record(conn, rec_id)
            if ok:
                await query.edit_message_text(f"🗑️ Đã xóa mềm bản ghi #{rec_id}. Anh có thể gõ /undo để khôi phục lại.")
            else:
                await query.edit_message_text(f"❌ Lỗi: {err}")
        elif data == "del_cancel":
            await query.edit_message_text("Đã hủy thao tác xóa.")
        elif data.startswith("undo_rec:"):
            ok, msg = undo_last_action(conn)
            if ok:
                await query.edit_message_text(f"↩️ {msg}")
            else:
                await query.edit_message_text(f"⚠️ {msg}")
        elif data.startswith("view_rec:"):
            rec_id = data.split(":")[1]
            rec = get_record(conn, rec_id)
            if rec:
                lines = [
                    f"<b>BẢN GHI #{rec.id}</b>",
                    f"<b>Mô tả:</b> {rec.display_name}",
                    f"<b>Giá thắng:</b> {rec.amount_jpy:,} JPY",
                    f"<b>Hộp:</b> {rec.box} | <b>Tình trạng:</b> {rec.cosmetic_condition}",
                ]
                await query.message.reply_html("\n".join(lines))
        elif data.startswith("lot_guide:"):
            rec_id = data.split(":")[1]
            await query.message.reply_html(
                f"<b>Mẫu lệnh dọn cho lô #{rec_id}:</b>\n\n"
                f"<code>/donlo {rec_id} 6 8</code>\n\n"
                f"<i>(Anh copy dòng trên, sửa lại số cây sống và chết theo thực tế dọn được).</i>"
            )
    finally:
        conn.close()


async def donlo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cập nhật kết quả dọn lô và phân bổ giá vốn thực tế: /donlo <mã_bản_ghi> <số_cây_sống> <số_cây_rã_xác>."""
    if not update.effective_message:
        return

    text = update.effective_message.text or ""
    parts = text.split()
    if len(parts) < 4:
        db_path = context.bot_data["config"].db_path
        conn = get_db_connection(db_path)
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM records WHERE is_lot = 1 AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 5;"
            )
            lots = cur.fetchall()
            lines = ["🛠️ <b>QUẢN LÝ & CẬP NHẬT KẾT QUẢ DỌN LÔ</b>\n"]
            if lots:
                lines.append("📋 <b>Các lô quẹt trong kho gần đây:</b>")
                keyboard = []
                for l in lots:
                    rate = 165
                    tot_vnd = round((l["amount_jpy"] + (l["fee_jpy"] or 0)) * rate)
                    tot_vnd_fmt = f"{tot_vnd:,}".replace(",", ".")
                    lines.append(f"• <b>#{l['id']}</b>: <i>{l['display_name']}</i> (~{tot_vnd_fmt} đ)")
                    keyboard.append([
                        InlineKeyboardButton(f"🔧 Hướng dẫn dọn #{l['id']}", callback_data=f"lot_guide:{l['id']}")
                    ])
                lines.append("\n<b>Cú pháp cập nhật:</b>")
                lines.append("<code>/donlo &lt;mã_lô&gt; &lt;số_cây_sống&gt; &lt;số_cây_rã_xác&gt;</code>")
                lines.append("<i>Ví dụ: <code>/donlo Q0006 6 8</code></i>")
                await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                lines.append("<i>Chưa có lô quẹt nào được lưu trong kho.</i>\n")
                lines.append("<b>Cú pháp khi có lô:</b> <code>/donlo &lt;mã_lô&gt; &lt;số_sống&gt; &lt;số_chết&gt;</code>")
                await update.effective_message.reply_html("\n".join(lines))
        finally:
            conn.close()
        return

    rec_id = parts[1].strip()
    try:
        song = int(parts[2].replace("song=", "").replace("sống=", ""))
        chet = int(parts[3].replace("chet=", "").replace("chết=", ""))
        if song < 0 or chet < 0 or (song + chet == 0):
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("Số lượng cây sống và chết phải là số nguyên không âm hợp lệ.")
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        from repository import update_lot_restoration
        res = update_lot_restoration(conn, rec_id, song, chet)
        if not res:
            await update.effective_message.reply_html(f"❌ Không tìm thấy bản ghi hoặc lô <b>#{rec_id}</b> trong kho.")
            return

        tot_fmt = f"{res['total_cost_vnd']:,}".replace(",", ".")
        u_alive_fmt = f"{res['cost_per_alive_vnd']:,}".replace(",", ".")
        rec_retail_min = f"{round(res['cost_per_alive_vnd'] * 1.8):,}".replace(",", ".")
        rec_retail_max = f"{round(res['cost_per_alive_vnd'] * 2.5):,}".replace(",", ".")

        msg = (
            f"🛠️ <b>CẬP NHẬT KẾT QUẢ DỌN LÔ THÀNH CÔNG!</b>\n"
            f"📦 <b>Lô:</b> #{res['record_id']} — <i>{res['display_name']}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Tổng vốn lô (gồm ship): <b>~{tot_fmt} đ</b>\n"
            f"• Số cây dọn sống lên lửa: <b>{song} cây</b> 🔥\n"
            f"• Số cây rã xác lấy linh kiện: <b>{chet} cây</b> 🔩\n\n"
            f"👉 <b>GIÁ VỐN THỰC TẾ: ~{u_alive_fmt} đ/cây sống</b>\n"
            f"💡 <b>Giá bán lẻ đề xuất tại VN:</b> <b>{rec_retail_min} - {rec_retail_max} đ/cây</b>\n"
            f"<i>(Đã lưu phân bổ giá vốn vào kho để anh tiện tra cứu P&L sau này!)</i>"
        )
        await update.effective_message.reply_html(msg)
    finally:
        conn.close()

