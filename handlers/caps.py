"""Handler quản lý trần bid cá nhân: /cap <ID> <giá> và /cap <ID> off."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from db import get_db_connection
from models import BidCap
from parser import parse_jpy_amount
from pricing import format_currency_amount, format_jpy
from repository import disable_bid_cap, get_record, set_bid_cap
from search import format_scope_title


async def cap_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /cap <ID> <giá hoặc off>."""
    if not update.effective_message:
        return

    text = update.effective_message.text or ""
    parts = text.split()
    if len(parts) < 3:
        await update.effective_message.reply_html(
            "<b>Cú pháp đặt trần bid cá nhân:</b>\n"
            "• Đặt trần: <code>/cap Q0001 13400Y</code>\n"
            "• Tắt trần: <code>/cap Q0001 off</code>"
        )
        return

    rec_id = parts[1].strip().upper()
    val_str = parts[2].strip()

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        record = get_record(conn, rec_id)
        if not record:
            await update.effective_message.reply_text(f"Không tìm thấy bản ghi #{rec_id}.")
            return

        scope_key = record.scope_key()
        title = format_scope_title(record)

        if val_str.lower() == "off":
            ok = disable_bid_cap(conn, scope_key)
            if ok:
                await update.effective_message.reply_html(
                    f"🛑 Đã tắt trần bid cá nhân cho nhóm:\n<b>{title}</b>"
                )
            else:
                await update.effective_message.reply_text("Nhóm này hiện chưa được đặt trần bid nào.")
            return

        amount, err = parse_jpy_amount(val_str)
        if err or amount is None:
            await update.effective_message.reply_text(f"Số tiền không hợp lệ: {err or val_str}")
            return

        cap = BidCap(
            id=None,
            scope_key=scope_key,
            brand=record.brand,
            line=record.line,
            material=record.material,
            color=record.color,
            box=record.box,
            condition=record.cosmetic_condition,
            cap_amount_jpy=amount,
            source_record_id=record.id,
            is_active=True,
        )
        set_bid_cap(conn, cap)

        await update.effective_message.reply_html(
            f"🎯 <b>Đã đặt trần bid cá nhân: {format_jpy(amount)} yên</b>\n"
            f"Nhóm: <b>{title}</b>\n"
            f"Nguồn tham chiếu: #{record.id}"
        )
    finally:
        conn.close()


async def cap_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý bấm nút Đặt trần từ tin nhắn kết quả."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "cap_set":
        return

    _, rec_id, amount_str = parts
    try:
        amount = int(amount_str)
    except ValueError:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        record = get_record(conn, rec_id)
        if not record:
            await query.message.reply_text(f"Không tìm thấy bản ghi #{rec_id}.")
            return

        scope_key = record.scope_key()
        title = format_scope_title(record)

        cap = BidCap(
            id=None,
            scope_key=scope_key,
            brand=record.brand,
            line=record.line,
            material=record.material,
            color=record.color,
            box=record.box,
            condition=record.cosmetic_condition,
            cap_amount_jpy=amount,
            source_record_id=record.id,
            is_active=True,
        )
        set_bid_cap(conn, cap)

        price_cap_fmt = format_currency_amount(amount, record.currency)
        await query.message.reply_html(
            f"🎯 <b>Đã đặt trần bid cá nhân: {price_cap_fmt}</b>\n"
            f"Nhóm áp dụng: <b>{title}</b>\n"
            f"Lần tới khi tra cứu nhóm này, bot sẽ nhắc đúng mức trần anh đã đặt."
        )
    finally:
        conn.close()
