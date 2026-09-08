"""Handler tiếp nhận dữ liệu /data, xử lý bản nháp và lưu bản ghi."""
from __future__ import annotations

import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from models import Draft, Record
from parser import parse_data_input
from pricing import format_currency_amount, format_jpy
from repository import (
    create_record,
    delete_draft,
    generate_next_id,
    get_draft,
    save_draft,
    undo_last_action,
)


def format_saved_record_message(record: Record) -> str:
    """Định dạng bản tóm tắt sau khi lưu theo đặc tả mục 3.2."""
    brand_str = record.brand.capitalize() if record.brand != "unknown" else ""
    line_str = record.line.replace("_", " ").title() if record.line != "unknown" else ""
    mat_str = record.material.replace("_", " ").title() if record.material != "unknown" else ""
    col_str = record.color.capitalize() if record.color != "unknown" else ""

    header_parts = [p for p in [brand_str, line_str, mat_str, col_str] if p]
    header = " · ".join(header_parts) or record.display_name

    box_str = "Có hộp" if record.box == "yes" else ("Không hộp" if record.box == "no" else "Chưa rõ")
    if record.papers == "yes":
        box_str = "Đủ hộp, giấy, phụ kiện"

    cond_str = record.cosmetic_condition if record.cosmetic_condition != "unknown" else "Chưa rõ"
    date_str = record.auction_date if record.auction_date else "Chưa nhập"
    price_str = format_currency_amount(record.amount_jpy, record.currency, with_approx=True)

    fee_str = ""
    if record.fee_jpy > 0:
        fee_str += f"\nPhí Nhật: {format_jpy(record.fee_jpy)} yên"
    if record.fee_vnd > 0:
        fee_str += f"\nPhí VN: {record.fee_vnd:,}đ"

    return (
        f"✅ <b>Đã lưu #{record.id}</b> · 🎯 <b>Đã đặt trần: {price_str}</b>\n"
        f"<b>{header}</b>\n"
        f"<b>Giá thắng:</b> {price_str}\n"
        f"<b>Phụ kiện:</b> {box_str}\n"
        f"<b>Tình trạng:</b> {cond_str}\n"
        f"<b>Ngày đấu:</b> {date_str}"
        f"{fee_str}"
    )


def auto_set_record_bid_cap(conn, record: Record) -> None:
    """Tự động chốt trần bid cá nhân ngay khi lưu bản ghi, không cần click thêm."""
    from models import BidCap
    from repository import set_bid_cap
    cap = BidCap(
        id=None,
        scope_key=record.scope_key(),
        brand=record.brand,
        line=record.line,
        material=record.material,
        color=record.color,
        box=record.box,
        condition=record.cosmetic_condition,
        cap_amount_jpy=record.amount_jpy,
        source_record_id=record.id,
        is_active=True,
    )
    set_bid_cap(conn, cap)


def get_saved_record_keyboard(record: Record) -> InlineKeyboardMarkup:
    """Tạo các nút hành động nhanh sau khi lưu (trần bid đã được tự động kích hoạt)."""
    keyboard = [
        [
            InlineKeyboardButton(
                "✏️ Bổ sung tình trạng",
                callback_data=f"edit_cond:{record.id}",
            ),
            InlineKeyboardButton("🔧 Sửa", callback_data=f"edit_rec:{record.id}"),
        ],
        [
            InlineKeyboardButton("↩️ Hoàn tác", callback_data=f"undo_rec:{record.id}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def data_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /data <mô tả> <giá>."""
    if not update.effective_message:
        return

    raw_text = update.effective_message.text or ""
    res = parse_data_input(raw_text)

    # Nếu cú pháp thiếu thông tin hoặc cần xác nhận
    if res.needs_confirmation:
        if res.confirmation_type == "ambiguous_box":
            # Tạo draft chờ xác nhận "full boc"
            draft_id = uuid.uuid4().hex[:8]
            payload = {
                "amount_jpy": res.amount_jpy,
                "raw_desc": res.raw_desc,
                "brand": res.brand,
                "line": res.line,
                "material": res.material,
                "color": res.color,
                "cosmetic_condition": res.cosmetic_condition,
                "fee_jpy": res.fee_jpy,
                "fee_vnd": res.fee_vnd,
                "auction_date": res.auction_date,
                "note": res.note,
            }
            db_path = context.bot_data["config"].db_path
            conn = get_db_connection(db_path)
            try:
                save_draft(
                    conn,
                    Draft(
                        draft_id=draft_id,
                        user_id=update.effective_user.id,
                        draft_type="ambiguous_box",
                        payload=payload,
                    ),
                )
            finally:
                conn.close()

            keyboard = [
                [
                    InlineKeyboardButton("Có hộp", callback_data=f"box_draft:{draft_id}:box_yes"),
                    InlineKeyboardButton("Đủ hộp, giấy, phụ kiện", callback_data=f"box_draft:{draft_id}:full_set"),
                ],
                [
                    InlineKeyboardButton("Giữ nguyên mô tả", callback_data=f"box_draft:{draft_id}:keep_raw"),
                ],
            ]
            await update.effective_message.reply_html(
                f"⚠️ {res.confirmation_message}",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        elif res.confirmation_type == "clarify_price":
            draft_id = uuid.uuid4().hex[:8]
            payload = {
                "raw_desc": res.raw_desc,
                "display_name": res.display_name,
                "brand": res.brand,
                "line": res.line,
                "size_submodel": res.size_submodel,
                "material": res.material,
                "finish": res.finish,
                "color": res.color,
                "edition": res.edition,
                "box": res.box,
                "papers": res.papers,
                "accessories_note": res.accessories_note,
                "cosmetic_condition": res.cosmetic_condition,
                "fee_jpy": res.fee_jpy,
                "fee_vnd": res.fee_vnd,
                "auction_date": res.auction_date,
                "note": res.note,
            }
            db_path = context.bot_data["config"].db_path
            conn = get_db_connection(db_path)
            try:
                save_draft(
                    conn,
                    Draft(
                        draft_id=draft_id,
                        user_id=update.effective_user.id,
                        draft_type="clarify_price",
                        payload=payload,
                    ),
                )
            finally:
                conn.close()

            keyboard = []
            if res.suggested_currency_prices:
                row = []
                for s in res.suggested_currency_prices[:4]:
                    amt = s["amount"]
                    curr = s["currency"]
                    lbl = s["label"]
                    row.append(InlineKeyboardButton(lbl, callback_data=f"price_draft:{draft_id}:{amt}:{curr}"))
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                if row:
                    keyboard.append(row)
            else:
                price_row = [
                    InlineKeyboardButton(f"{format_jpy(p)} yên", callback_data=f"price_draft:{draft_id}:{p}:JPY")
                    for p in res.suggested_prices[:3]
                ]
                if price_row:
                    keyboard.append(price_row)

            keyboard.append([
                InlineKeyboardButton("❌ Hủy", callback_data=f"price_cancel:{draft_id}")
            ])

            await update.effective_message.reply_html(
                f"⚠️ {res.confirmation_message}\n\n"
                f"<i>(Hoặc anh có thể nhắn trực tiếp số tiền vào đây, ví dụ: 300k vnd, 50$ hoặc 30000Y để lưu ngay).</i>",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        elif res.confirmation_type in ("missing_price", "missing_desc", "missing_all"):
            await update.effective_message.reply_html(
                f"⚠️ {res.confirmation_message}\n\n<i>Lưu ý: {res.error_message}</i>"
            )
            return

    if not res.is_valid:
        await update.effective_message.reply_html(f"❌ Lỗi: {res.error_message}")
        return

    # Lưu bản ghi hợp lệ
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        next_id = generate_next_id(conn)
        new_record = Record(
            id=next_id,
            owner_user_id=update.effective_user.id,
            raw_text=raw_text,
            display_name=res.display_name,
            normalized_search_text="",
            amount_jpy=res.amount_jpy or 0,
            currency=res.currency or "JPY",
            brand=res.brand,
            line=res.line,
            size_submodel=res.size_submodel,
            material=res.material,
            finish=res.finish,
            color=res.color,
            edition=res.edition,
            box=res.box,
            papers=res.papers,
            accessories_note=res.accessories_note,
            cosmetic_condition=res.cosmetic_condition,
            functional_state=res.functional_state,
            fee_jpy=res.fee_jpy,
            fee_vnd=res.fee_vnd,
            auction_date=res.auction_date,
            auction_id=res.auction_id,
            price_basis=res.price_basis,
            note=res.note,
        )
        saved = create_record(conn, new_record)
        auto_set_record_bid_cap(conn, saved)
        msg_text = format_saved_record_message(saved)
        reply_markup = get_saved_record_keyboard(saved)
        await update.effective_message.reply_html(msg_text, reply_markup=reply_markup)
    finally:
        conn.close()


async def draft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lựa chọn từ inline keyboard cho bản nháp."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3 or parts[0] != "box_draft":
        return

    _, draft_id, choice = parts
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        draft = get_draft(conn, draft_id)
        if not draft:
            await query.message.reply_text("Bản nháp này đã hết hạn hoặc đã được xử lý.")
            return

        payload = draft.payload
        box = "unknown"
        papers = "unknown"
        acc_note = ""

        if choice == "box_yes":
            box = "yes"
            acc_note = "Có hộp"
        elif choice == "full_set":
            box = "yes"
            papers = "yes"
            acc_note = "Đủ hộp, giấy, phụ kiện"
        elif choice == "keep_raw":
            box = "unknown"
            acc_note = "full boc"

        next_id = generate_next_id(conn)
        record = Record(
            id=next_id,
            owner_user_id=draft.user_id,
            raw_text=payload["raw_desc"],
            display_name=payload["raw_desc"],
            normalized_search_text="",
            amount_jpy=payload["amount_jpy"],
            brand=payload.get("brand", "unknown"),
            line=payload.get("line", "unknown"),
            material=payload.get("material", "unknown"),
            color=payload.get("color", "unknown"),
            box=box,
            papers=papers,
            accessories_note=acc_note,
            cosmetic_condition=payload.get("cosmetic_condition", "unknown"),
            fee_jpy=payload.get("fee_jpy", 0),
            fee_vnd=payload.get("fee_vnd", 0),
            auction_date=payload.get("auction_date"),
            note=payload.get("note", ""),
        )
        saved = create_record(conn, record)
        auto_set_record_bid_cap(conn, saved)
        delete_draft(conn, draft_id)

        msg_text = format_saved_record_message(saved)
        reply_markup = get_saved_record_keyboard(saved)
        await query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=reply_markup)
    finally:
        conn.close()


async def price_draft_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lựa chọn mức giá từ nút bấm cho bản nháp."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    parts = query.data.split(":")
    if parts[0] == "price_cancel":
        draft_id = parts[1]
        db_path = context.bot_data["config"].db_path
        conn = get_db_connection(db_path)
        try:
            delete_draft(conn, draft_id)
        finally:
            conn.close()
        await query.edit_message_text("Đã hủy bản nháp.")
        return

    if parts[0] != "price_draft":
        return

    currency = "JPY"
    if len(parts) == 3:
        _, draft_id, amount_str = parts
    elif len(parts) == 4:
        _, draft_id, amount_str, currency = parts
    else:
        return

    try:
        amount = int(amount_str)
    except ValueError:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        draft = get_draft(conn, draft_id)
        if not draft:
            await query.message.reply_text("Bản nháp này đã hết hạn hoặc đã được lưu.")
            return

        payload = draft.payload
        next_id = generate_next_id(conn)
        record = Record(
            id=next_id,
            owner_user_id=draft.user_id,
            raw_text=payload["raw_desc"],
            display_name=payload.get("display_name", payload["raw_desc"]),
            normalized_search_text="",
            amount_jpy=amount,
            currency=currency,
            brand=payload.get("brand", "unknown"),
            line=payload.get("line", "unknown"),
            size_submodel=payload.get("size_submodel", "unknown"),
            material=payload.get("material", "unknown"),
            finish=payload.get("finish", "unknown"),
            color=payload.get("color", "unknown"),
            edition=payload.get("edition", "unknown"),
            box=payload.get("box", "unknown"),
            papers=payload.get("papers", "unknown"),
            accessories_note=payload.get("accessories_note", ""),
            cosmetic_condition=payload.get("cosmetic_condition", "unknown"),
            fee_jpy=payload.get("fee_jpy", 0),
            fee_vnd=payload.get("fee_vnd", 0),
            auction_date=payload.get("auction_date"),
            note=payload.get("note", ""),
        )
        saved = create_record(conn, record)
        auto_set_record_bid_cap(conn, saved)
        delete_draft(conn, draft_id)

        msg_text = format_saved_record_message(saved)
        reply_markup = get_saved_record_keyboard(saved)
        await query.edit_message_text(msg_text, parse_mode="HTML", reply_markup=reply_markup)
    finally:
        conn.close()
