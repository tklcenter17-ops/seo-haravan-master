"""Handler tra cứu tự nhiên (tin nhắn thường) và lệnh /find."""
from __future__ import annotations
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from models import Record
from parser import get_price_suggestions, parse_jpy_amount
from pricing import format_currency_amount, format_jpy
from repository import create_record, delete_draft, generate_next_id
from search import SearchGroup, search_records


def format_group_detail_message(group: SearchGroup) -> str:
    """Định dạng chi tiết một nhóm theo Thẻ Khuyến Nghị Đi Bid Tức Thì (Instant Bid Advisory Card)."""
    curr = group.records[0].currency if group.records else "JPY"
    from pricing import get_bid_advisory
    advisory = get_bid_advisory(group.pricing, curr)

    lines = [
        "🎯 <b>KHUYẾN NGHỊ ĐI BID TỨC THÌ</b>",
        f"📦 <b>{group.display_title}</b>",
        "━━━━━━━━━━━━━━━━━━━━━",
    ]

    if advisory["has_recommendation"]:
        lines.append(f"👉 <b>NÊN BID TỐI ĐA: {advisory['max_bid_text']}</b>")
        if advisory["landing_cost_text"]:
            lines.append(f"🚚 <i>Dự kiến về tay: {advisory['landing_cost_text']}</i>\n")

        lines.append(f"🛡️ <b>Chiến thuật:</b> Vùng an toàn <code>{advisory['safe_zone_text']}</code>.")
        lines.append(f"⚠️ {advisory['stop_warning_text']}")
        lines.append(f"📌 <i>Cơ sở: {advisory['basis_text']}.</i>")
        if advisory["condition_hint"]:
            lines.append(f"\n{advisory['condition_hint']}")
    else:
        lines.append(f"💰 <b>{group.pricing.summary_text}</b>")
        if group.pricing.note_text:
            lines.append(f"<i>{group.pricing.note_text}</i>")

    lines.append(f"\n📊 <b>Lịch sử giao dịch ({len(group.records)} lần):</b>")
    for r in group.records[:5]:
        d_str = f" · {r.auction_date}" if r.auction_date else ""
        cond_str = f" [{r.cosmetic_condition}]" if r.cosmetic_condition != "unknown" else ""
        lines.append(f"• #{r.id}: <b>{format_currency_amount(r.amount_jpy, r.currency, with_approx=True)}</b>{cond_str}{d_str}")

    return "\n".join(lines)


def get_group_detail_keyboard(group: SearchGroup) -> InlineKeyboardMarkup:
    first_rec = group.records[0] if group.records else None
    keyboard = []
    row1 = []
    if first_rec:
        row1.append(
            InlineKeyboardButton(
                "⚡ Vừa thắng cây này",
                callback_data=f"quick_win:{group.scope_key[:32]}",
            )
        )
        row1.append(
            InlineKeyboardButton(
                "🎯 Đổi mốc trần",
                callback_data=f"cap_set:{first_rec.id}:{first_rec.amount_jpy}",
            )
        )
    if row1:
        keyboard.append(row1)

    keyboard.append([
        InlineKeyboardButton("📊 Bảng giá 4 tình trạng", callback_data=f"matrix:{group.scope_key[:32]}"),
        InlineKeyboardButton("📋 Xem tất cả lần mua", callback_data=f"grp_tx:{group.scope_key[:32]}")
    ])

    keyboard.append([
        InlineKeyboardButton("🎯 Radar Lô Hôm Nay", callback_data="radar_refresh"),
        InlineKeyboardButton("🎛 Bảng Menu", callback_data="menu:main"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query_text: str, page: int = 1) -> None:
    """Xử lý logic tìm kiếm từ query text."""
    if not update.effective_message:
        return

    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        res = search_records(conn, query_text, page=page, page_size=5)

        # 1. Trường hợp màu sắc mơ hồ (xanh lá hay xanh dương)
        if res.is_ambiguous:
            keyboard = [
                [
                    InlineKeyboardButton(
                        opt,
                        callback_data=f"srch_opt:{res.cleaned_query} {opt}",
                    )
                    for opt in res.ambiguous_options
                ]
            ]
            await update.effective_message.reply_html(
                f"❓ {res.ambiguous_prompt}",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
            return

        # 2. Trường hợp có đúng 1 nhóm khớp -> Trả về Instant Bid Advisory Card ngay!
        if res.total_groups == 1 and len(res.groups) == 1:
            group = res.groups[0]
            msg_text = format_group_detail_message(group)
            reply_markup = get_group_detail_keyboard(group)
            await update.effective_message.reply_html(msg_text, reply_markup=reply_markup)
            return

        # 3. Trường hợp có nhiều nhóm khớp -> Trả về Zero-Click Group List với mốc giá nên bid trực tiếp
        if res.total_groups > 1:
            from pricing import get_bid_advisory
            lines = [f"🔍 Tìm thấy <b>{res.total_groups}</b> nhóm quẹt phù hợp với: <i>{query_text}</i>\n"]
            keyboard = []

            for idx, g in enumerate(res.groups, start=(res.page - 1) * 5 + 1):
                c = g.records[0].currency if g.records else "JPY"
                adv = get_bid_advisory(g.pricing, c)
                if adv["has_recommendation"]:
                    bid_line = f"👉 <b>NÊN BID: {adv['max_bid_text']}</b>"
                else:
                    p_text = f"{format_jpy(g.pricing.reference_price_jpy)}Y" if g.pricing.reference_price_jpy else "Xem giá"
                    bid_line = f"👉 {p_text}"

                lines.append(f"<b>{idx}. {g.display_title}</b>\n   {bid_line} ({len(g.records)} lần mua)")
                keyboard.append([
                    InlineKeyboardButton(f"🔎 Xem chi tiết nhóm {idx}", callback_data=f"view_grp:{g.scope_key[:32]}")
                ])

            # Các nút phân trang nếu > 5 nhóm
            nav_buttons = []
            if res.page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"srch_page:{res.page - 1}:{query_text}"))
            if (res.page * 5) < res.total_groups:
                nav_buttons.append(InlineKeyboardButton("Tiếp ➡️", callback_data=f"srch_page:{res.page + 1}:{query_text}"))
            if nav_buttons:
                keyboard.append(nav_buttons)

            await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # 4. Không có nhóm nào khớp hoàn toàn
        # Kiểm tra xem người dùng có bản nháp nào đang chờ không
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM drafts WHERE user_id = ? ORDER BY created_at DESC LIMIT 1;",
            (update.effective_user.id,),
        )
        draft_row = cur.fetchone()

        keyboard = []
        if draft_row:
            d_payload = json.loads(draft_row["payload"])
            d_desc = d_payload.get("raw_desc", "")
            d_id = draft_row["draft_id"]
            q_lower = query_text.lower().strip()
            if q_lower in d_desc.lower() or any(w in d_desc.lower() for w in q_lower.split()):
                no_match_text = (
                    f"⚠️ Chưa có bản ghi chính thức cho: <i>{query_text}</i>.\n\n"
                    f"👉 Nhưng anh đang có 1 bản nháp: <b>{d_desc}</b> (chưa xong giá).\n"
                    f"Anh có muốn chọn mức giá để lưu ngay không?"
                )
                raw_tok = d_payload.get("raw_price_token", "300k")
                from parser import get_multicurrency_suggestions
                multis = get_multicurrency_suggestions(raw_tok)
                if multis:
                    row = []
                    for s in multis[:4]:
                        amt = s["amount"]
                        c = s["currency"]
                        lbl = s["label"]
                        row.append(InlineKeyboardButton(lbl, callback_data=f"price_draft:{d_id}:{amt}:{c}"))
                        if len(row) == 2:
                            keyboard.append(row)
                            row = []
                    if row:
                        keyboard.append(row)
                else:
                    sugg = get_price_suggestions(raw_tok) or [300000, 30000, 3000]
                    price_row = [
                        InlineKeyboardButton(f"{format_jpy(p)} yên", callback_data=f"price_draft:{d_id}:{p}:JPY")
                        for p in sugg[:3]
                    ]
                    if price_row:
                        keyboard.append(price_row)
                keyboard.append([InlineKeyboardButton("❌ Hủy bản nháp", callback_data=f"price_cancel:{d_id}")])
                await update.effective_message.reply_html(no_match_text, reply_markup=InlineKeyboardMarkup(keyboard))
                return

        no_match_text = f"Không tìm thấy bản ghi nào khớp hoàn toàn với: <i>{query_text}</i>."
        if res.similar_groups:
            no_match_text += "\n\n<b>Mẫu gần giống (khác dòng hoặc phụ kiện):</b>"
            for sg in res.similar_groups:
                no_match_text += f"\n• {sg.display_title}"

        # Nút gợi ý thêm nhanh mẫu
        keyboard.append([
            InlineKeyboardButton(f"➕ Thêm nhanh: /data {query_text}", callback_data=f"quick_add:{query_text}")
        ])
        await update.effective_message.reply_html(no_match_text, reply_markup=InlineKeyboardMarkup(keyboard))
    finally:
        conn.close()


async def text_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bắt các tin nhắn văn bản thông thường không phải command để tìm kiếm, tính nhẩm hoặc hoàn tất nháp."""
    if not update.effective_message or not update.effective_message.text:
        return
    text = update.effective_message.text.strip()
    if text.startswith("/"):
        return

    # 0.1 Bắt các nút bấm từ Bảng Menu bàn phím cố định để thực thi lệnh tức thì
    if "🎯 Radar Lô Hôm Nay" in text:
        from handlers.radar_handlers import radar_command
        await radar_command(update, context)
        return
    if "📜 Toàn Bộ Lô" in text or "📜 Báo Toàn Bộ" in text:
        from handlers.radar_handlers import radar_command
        context.args = ["all"]
        await radar_command(update, context)
        return
    if "📦 Dọn Lô Kho" in text or "📦 Dọn Lô" in text:
        from handlers.record_mgmt import donlo_command
        await donlo_command(update, context)
        return
    if "📋 10 Cây Gần Nhất" in text or "📋 Kho Gần Đây" in text:
        from handlers.record_mgmt import recent_command
        await recent_command(update, context)
        return
    if "📊 Thống Kê Kho" in text or "📊 Thống Kê" in text:
        from handlers.admin import stats_command
        await stats_command(update, context)
        return
    if "❓ Hướng Dẫn" in text:
        from handlers.start import help_command
        await help_command(update, context)
        return

    # 0.2 Bắt các từ khóa chào hỏi hoặc yêu cầu xem menu trực tiếp
    t_clean = text.lower().strip()
    if t_clean in ["hi", "hello", "alo", "chao", "chào", "xin chao", "xin chào", "menu", "bảng menu", "bang menu", "bàn phím", "ban phim"]:
        from handlers.start import menu_command
        await menu_command(update, context)
        return

    # 0.3 Kiểm tra tra cứu nhanh mã bản ghi trong kho: Q0001 hoặc #Q0001
    import re
    m_qid = re.match(r"^#?(Q\d{4})$", text, re.IGNORECASE)
    if m_qid:
        qid = m_qid.group(1).upper()
        db_path = context.bot_data["config"].db_path
        conn = get_db_connection(db_path)
        try:
            from repository import get_record
            rec = get_record(conn, qid)
            if rec:
                from pricing import format_currency_amount
                lines = [
                    f"📦 <b>CHI TIẾT BẢN GHI #{rec.id}</b>",
                    f"🏷️ <b>Mô tả:</b> {rec.display_name}",
                    f"⚡ <b>Giá chốt:</b> <b>{format_currency_amount(rec.amount_jpy, rec.currency, with_approx=True)}</b>",
                    f"🔖 <b>Phân loại:</b> {rec.brand.capitalize()} | {rec.line.replace('_', ' ').title()}",
                    f"🎨 <b>Chất liệu:</b> {rec.material.capitalize()} | <b>Màu:</b> {rec.color.capitalize()}",
                    f"📦 <b>Hộp:</b> {rec.box} | <b>Tình trạng:</b> {rec.cosmetic_condition}",
                ]
                if rec.auction_date:
                    lines.append(f"📅 <b>Ngày đấu:</b> {rec.auction_date}")
                if rec.auction_id:
                    lines.append(f"🔗 <b>Mã Yahoo:</b> #{rec.auction_id}")
                if rec.source_url:
                    lines.append(f"🌐 <b>Link nguồn:</b> {rec.source_url}")
                if rec.fee_jpy > 0:
                    lines.append(f"🚚 <b>Phí Nhật:</b> +{rec.fee_jpy:,} JPY")
                if rec.fee_vnd > 0:
                    lines.append(f"🚚 <b>Phí VN:</b> +{rec.fee_vnd:,} VND")
                if rec.note:
                    lines.append(f"📝 <b>Ghi chú:</b> {rec.note}")

                kb = [
                    [
                        InlineKeyboardButton(f"🎯 Đặt trần {rec.amount_jpy:,} {rec.currency}", callback_data=f"cap_set:{rec.id}:{rec.amount_jpy}"),
                        InlineKeyboardButton("🗑️ Xóa", callback_data=f"del_prompt:{rec.id}"),
                    ]
                ]
                await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(kb))
                return
            else:
                await update.effective_message.reply_html(f"❌ Không tìm thấy bản ghi <b>#{qid}</b> trong kho.")
                return
        finally:
            conn.close()

    # Tra cứu bảng tỷ giá nhanh
    norm_text = text.lower().strip()
    if norm_text in ["ty gia", "tỷ giá", "ty gia yen", "tỷ giá yên", "doi tien", "đổi tiền", "ti gia"]:
        msg = (
            "💴 <b>BẢNG TỶ GIÁ THAM KHẢO & CÔNG THỨC SHIP:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "• 🇯🇵 <b>1 JPY (Yên):</b> ~165 VND\n"
            "• 🇯🇵 <b>1 Man (10.000 JPY / 1 Vạn):</b> ~1.650.000 VND\n"
            "• 🇺🇸 <b>1 USD (Đô):</b> ~25.500 VND\n\n"
            "📦 <b>Chi phí phụ trợ ước tính về tay:</b>\n"
            "• Ship nội địa Nhật: ~500 - 1.200 yên (~82.000 - 198.000 đ)\n"
            "• Cước bay Nhật - VN: ~180.000 - 200.000 đ/cây\n"
            "• Ron + bấc + đá bảo dưỡng: ~30.000 - 50.000 đ/cây\n\n"
            "💡 <i>Anh có thể gõ nhanh số tiền (ví dụ: <code>15000Y</code> hoặc <code>15k yen</code>) để bot tính nhẩm về tay tức thì!</i>"
        )
        await update.effective_message.reply_html(msg)
        return

    # 1. Kiểm tra Link Yahoo Auctions / Buyee / ZenMarket (HƯỚNG 1)
    from parser import extract_yahoo_auction_id, fetch_yahoo_auction_info
    auction_id = extract_yahoo_auction_id(text)
    if auction_id:
        await update.effective_message.reply_chat_action("typing")
        info = await fetch_yahoo_auction_info(auction_id)
        title = info["title"]
        curr_price = info["current_price_jpy"]
        url = info["url"]

        if not title:
            # Kiểm tra xem user có gõ kèm tiêu đề hoặc mô tả trong tin nhắn không
            clean_hint = re.sub(r"https?://\S+", "", text)
            clean_hint = re.sub(rf"#?{re.escape(auction_id)}", "", clean_hint).strip()
            if len(clean_hint) >= 3:
                info["title"] = clean_hint
                title = clean_hint
            else:
                msg = (
                    f"🔗 <b>NHẬN DIỆN LINK YAHOO AUCTIONS (#{auction_id})</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 Link: {url}\n\n"
                    f"⚠️ <i>Không thể đọc tự động tiêu đề do giới hạn kết nối của Yahoo Nhật.</i>\n"
                    f"👉 Anh hãy <b>copy tiêu đề tiếng Nhật</b> của cây quẹt dán vào đây, bot sẽ phân tích mốc bid tức thì cho anh nhé!"
                )
                await update.effective_message.reply_html(msg)
                return

        # Đã fetch được thông tin chi tiết phiên đấu Yahoo
        from parser import deep_analyze_yahoo_auction
        analysis = deep_analyze_yahoo_auction(info)
        lot_info = analysis["lot_info"]
        ignition_status = analysis["ignition_status"]
        condition_vn = analysis["condition_vn"]
        accessories = analysis["accessories"]
        expert_notes = analysis["expert_notes"]
        status = info.get("status", "open")
        shipping_fee = info.get("shipping_fee_jpy")
        bids = info.get("bids", 0)

        db_path = context.bot_data["config"].db_path
        conn = get_db_connection(db_path)
        try:
            srch_res = search_records(conn, title)
            group = srch_res.groups[0] if (srch_res.groups and srch_res.total_groups >= 1) else None

            # Phân loại Lô hay Cây lẻ
            if lot_info["is_lot"] and lot_info["count"]:
                kind_badge = f"LÔ {lot_info['count']} CÂY BẬT LỬA"
                if "ガス" in title or "gas" in title.lower():
                    kind_badge += " GAS"
                elif "zippo" in title.lower() or "オイル" in title:
                    kind_badge += " XĂNG"
                kind_badge += " (Bán gom / Sỉ)"
            else:
                kind_badge = group.display_title if group else title

            lines = [
                f"🔗 <b>PHÂN TÍCH CHUYÊN SÂU YAHOO AUCTIONS (#{auction_id})</b>",
                f"🏷️ <b>Tiêu đề:</b> <i>{title}</i>",
                f"📦 <b>Phân loại:</b> <b>{kind_badge}</b>",
                "━━━━━━━━━━━━━━━━━━━━━",
            ]

            # 1. Trạng thái phiên đấu
            rate = 165
            if status == "closed":
                lines.append("🔴 <b>TRẠNG THÁI: PHIÊN ĐÃ KẾT THÚC (TÀN PHIÊN)</b>")
                if curr_price:
                    p_fmt = f"{curr_price:,}".replace(",", ".")
                    p_vnd = f"{round(curr_price * rate):,}".replace(",", ".")
                    bids_str = f" ({bids} lượt bid)" if bids else ""
                    lines.append(f"⚡ <b>Giá chốt cuối cùng:</b> <b>{p_fmt} yên</b> (~{p_vnd} đ){bids_str}")
            else:
                lines.append("🟢 <b>TRẠNG THÁI: PHIÊN ĐANG DIỄN RA</b>")
                if curr_price:
                    p_fmt = f"{curr_price:,}".replace(",", ".")
                    p_vnd = f"{round(curr_price * rate):,}".replace(",", ".")
                    lines.append(f"⚡ <b>Giá sàn hiện tại:</b> <b>{p_fmt} yên</b> (~{p_vnd} đ)")

            # Phí ship nội địa Nhật
            if shipping_fee is not None:
                ship_fmt = f"{shipping_fee:,}".replace(",", ".")
                ship_vnd = f"{round(shipping_fee * rate):,}".replace(",", ".")
                lines.append(f"🚚 <b>Ship nội địa Nhật:</b> +{ship_fmt} yên (~{ship_vnd} đ)")
                if curr_price:
                    tot_jpy = curr_price + shipping_fee
                    tot_vnd = round(tot_jpy * rate)
                    tot_jpy_fmt = f"{tot_jpy:,}".replace(",", ".")
                    tot_vnd_fmt = f"{tot_vnd:,}".replace(",", ".")
                    lines.append(f"👉 <b>Tổng tiền trên sàn Nhật:</b> ~{tot_jpy_fmt} yên (~{tot_vnd_fmt} đ)")

            # 2. Bóc tách đơn giá từng cây trong lô (nếu là lô)
            if lot_info["is_lot"] and lot_info["count"] and curr_price:
                lines.append("\n🧮 <b>BÓC TÁCH ĐƠN GIÁ TỪNG CÂY TRONG LÔ:</b>")
                lines.append(f"• Số lượng đếm được: <b>{lot_info['count']} cây</b>")
                u_jpy_fmt = f"{lot_info['unit_price_jpy']:,}".replace(",", ".")
                u_vnd_fmt = f"{lot_info['unit_price_vnd']:,}".replace(",", ".")
                lines.append(f"• Đơn giá mua: <b>~{u_jpy_fmt} yên/cây (~{u_vnd_fmt} đ/cây)</b>")
                if lot_info["unit_cost_with_ship_jpy"]:
                    u_s_jpy_fmt = f"{lot_info['unit_cost_with_ship_jpy']:,}".replace(",", ".")
                    u_s_vnd_fmt = f"{lot_info['unit_cost_with_ship_vnd']:,}".replace(",", ".")
                    lines.append(f"• Đơn giá gồm ship Nhật: <b>~{u_s_jpy_fmt} yên/cây (~{u_s_vnd_fmt} đ/cây)</b>")

            # 3. Đối chiếu mốc trần (nếu là cây lẻ đã có trong kho)
            if not lot_info["is_lot"] and group and (group.pricing.reference_price_jpy or group.pricing.cap_amount_jpy):
                ref_jpy = group.pricing.cap_amount_jpy or group.pricing.reference_price_jpy
                from pricing import format_currency_amount
                rec_curr = group.records[0].currency if group.records else "JPY"
                ref_text = format_currency_amount(ref_jpy, rec_curr, with_approx=True)
                lines.append(f"\n🎯 <b>NÊN BID TỐI ĐA:</b> {ref_text}")
                if curr_price and rec_curr == "JPY":
                    diff = ref_jpy - curr_price
                    if diff > 0:
                        diff_fmt = f"{diff:,}".replace(",", ".")
                        lines.append(f"📈 <b>Dư địa còn lại:</b> Anh còn được bid thêm <b>+{diff_fmt} yên</b> nữa!")
                        lines.append(f"🛡️ <b>Chiến thuật:</b> Canh bid trong khoảng {curr_price:,} → {ref_jpy:,} yên.".replace(",", "."))
                    else:
                        lines.append(f"⚠️ <b>CẢNH BÁO:</b> Giá sàn <b>ĐÃ VƯỢT QUÁ</b> mốc trần ({ref_jpy:,} yên)!".replace(",", "."))
                        lines.append("🛑 <b>DỪNG LẠI NGAY</b>, bỏ phiên không theo để tránh mua đắt / ôm hớ!")

            # 4. Đối chiếu lịch sử giá đã từng mua/chốt trong quá khứ (Historical Memory)
            from parser import match_brand_and_model_from_title
            from repository import find_recent_similar_record
            brand_match = match_brand_and_model_from_title(title)
            sim_rec = find_recent_similar_record(conn, brand_match["brand"], brand_match["line"])
            if sim_rec and curr_price:
                sim_rate = 165
                sim_vnd = round(sim_rec.amount_jpy * sim_rate)
                sim_vnd_fmt = f"{sim_vnd:,}".replace(",", ".")
                sim_date = sim_rec.created_at[:10] if sim_rec.created_at else ""
                lines.append(f"\n🧠 <b>LỊCH SỬ KHO CỦA ANH ({brand_match['vn_name']}):</b>")
                lines.append(f"• Cây tương tự đã chốt: <b>{sim_rec.display_name}</b>")
                lines.append(f"• Giá chốt lần trước: <b>{sim_rec.amount_jpy:,} yên (~{sim_vnd_fmt} đ)</b> ({sim_date})".replace(",", "."))
                diff_old = curr_price - sim_rec.amount_jpy
                if diff_old < 0:
                    diff_abs_fmt = f"{abs(diff_old):,}".replace(",", ".")
                    lines.append(f"👉 <i>Phiên này đang <b>RẺ HƠN -{diff_abs_fmt} yên</b> so với lần anh chốt trước!</i>")
                elif diff_old > 0:
                    diff_fmt = f"{diff_old:,}".replace(",", ".")
                    lines.append(f"👉 <i>Phiên này đang <b>CAO HƠN +{diff_fmt} yên</b> so với lần anh chốt trước.</i>")
                else:
                    lines.append("👉 <i>Giá phiên này ngang bằng với lần anh chốt trước.</i>")

            # 5. Soi kỹ thuật & tình trạng
            lines.append("\n🔍 <b>KẾT QUẢ SOI KỸ THUẬT & TÌNH TRẠNG:</b>")
            lines.append(f"• 🔥 <b>Đánh lửa:</b> {ignition_status}")
            lines.append(f"• 🌟 <b>Ngoại hình:</b> 👌 {condition_vn}")
            lines.append(f"• 📦 <b>Phụ kiện:</b> {accessories}")

            # 6. Phân tích chuyên sâu từ góc nhìn thợ / người chơi
            if expert_notes:
                lines.append("\n💡 <b>ĐÁNH GIÁ CHUYÊN SÂU TỪ EXPERT:</b>")
                for note in expert_notes:
                    lines.append(note)
            else:
                lines.append("\n💡 <b>LƯU Ý KỸ THUẬT & PHÂN TÍCH:</b>")
                tech = analysis.get("tech_grade", "")
                if tech in ["untested", "junk"]:
                    lines.append("• ⚠️ <b>Hàng chưa thử lửa (未確認):</b> Người bán không cam kết hoạt động, có thể kẹt đá, chai ron hoặc xì van gas.")
                    lines.append("• 🔧 <b>Phương án xử lý:</b> Thích hợp cho thợ có sẵn ron chịu dầu, đá lửa và đồ nghề mở buồng van để phục chế hoặc rã phụ tùng.")
                elif tech == "spark_only":
                    lines.append("• ⚡ <b>Có tia đá (火花確認):</b> Cụm đá và bánh xe còn tốt, khả năng cao chỉ cần vệ sinh van xả hoặc nạp lại gas.")
                elif tech == "working":
                    lines.append("• 🔥 <b>Đã lên lửa (着火確認):</b> Máy hoạt động bình thường, cần soi kỹ ren ốc đáy và độ khít nắp xem có bị xì sau khi đóng nắp không.")
                lines.append("• 🔍 <b>Lưu ý ngoại quan:</b> Nên soi kỹ ảnh các góc cạnh xem có vết cấn móp nặng ảnh hưởng buồng kín hay không.")

            # Caching dữ liệu cho Album ảnh và Alarm
            context.bot_data[f"yh_imgs:{auction_id}"] = info.get("images", [])
            context.bot_data[f"yh_info:{auction_id}"] = {
                "title": title,
                "current_price_jpy": curr_price,
                "shipping_fee_jpy": shipping_fee,
                "url": url,
                "end_time": info.get("end_time", ""),
                "formatted_end_time": info.get("formatted_end_time", ""),
            }

            # Keyboard actions (Đầy đủ tiện ích thực chiến V4.0)
            keyboard = []
            p_val = curr_price or 13400
            s_val = shipping_fee or 0
            cnt_val = lot_info["count"] or 1

            # Hàng 1: Lưu chốt hoặc Thắng nhanh
            if status == "closed":
                save_label = "📥 Lưu kết quả chốt lô này vào kho" if lot_info["is_lot"] else "📥 Lưu kết quả chốt cây này vào kho"
                keyboard.append([
                    InlineKeyboardButton(save_label, callback_data=f"save_yahoo_lot:{auction_id}:{p_val}:{s_val}:{cnt_val}")
                ])
            else:
                p_btn_fmt = f"{p_val:,}".replace(",", ".")
                keyboard.append([
                    InlineKeyboardButton(f"⚡ Vừa thắng cây này ({p_btn_fmt}Y)", callback_data=f"quick_win_yahoo:{auction_id}:{p_val}")
                ])

            # Hàng 2: Soi ảnh nét & Báo thức canh tàn phiên
            row2 = []
            imgs = info.get("images", [])
            if imgs:
                row2.append(InlineKeyboardButton(f"📸 Soi {len(imgs)} ảnh nét", callback_data=f"yh_imgs:{auction_id}"))
            if status != "closed":
                row2.append(InlineKeyboardButton("⏰ Nhắc canh tàn phiên (15p)", callback_data=f"yh_alarm:{auction_id}"))
            if row2:
                keyboard.append(row2)

            # Hàng 3: Link mua hộ Buyee & ZenMarket
            keyboard.append([
                InlineKeyboardButton("🛒 Mở Buyee", url=f"https://buyee.jp/item/yahoo/auction/{auction_id}?lang=vi"),
                InlineKeyboardButton("🛒 Mở ZenMarket", url=f"https://zenmarket.jp/vi/auction.aspx?itemCode={auction_id}")
            ])

            # Hàng 4: Bảng giá 4 tình trạng & Yahoo gốc
            keyboard.append([
                InlineKeyboardButton("📊 Bảng giá 4 tình trạng", callback_data=f"matrix_price:{p_val}"),
                InlineKeyboardButton("🌐 Mở trên Yahoo", url=url)
            ])
            await update.effective_message.reply_html("\n".join(lines), reply_markup=InlineKeyboardMarkup(keyboard))
            return
        finally:
            conn.close()

    # 2. Kiểm tra Tính ngược lợi nhuận (HƯỚNG 2)
    from parser import parse_reverse_profit_input
    rev_input = parse_reverse_profit_input(text)
    if rev_input:
        from pricing import calculate_reverse_profit
        calc = calculate_reverse_profit(
            target_sale_vnd=rev_input["target_sale_vnd"],
            profit_pct=rev_input["profit_pct"],
            profit_vnd=rev_input["profit_vnd"],
        )
        sale_fmt = f"{calc['target_sale_vnd']:,}".replace(",", ".")
        ship_fmt = f"{calc['shipping_fee_vnd']:,}".replace(",", ".")
        maint_fmt = f"{calc['maintenance_fee_vnd']:,}".replace(",", ".")
        max_pur_fmt = f"{calc['max_purchase_vnd']:,}".replace(",", ".")
        max_bid_fmt = f"{calc['max_bid_jpy']:,}".replace(",", ".")

        msg = (
            f"🧮 <b>TÍNH NGƯỢC GIÁ BID THEO LỢI NHUẬN</b>\n"
            f"📦 <b>Mục tiêu:</b> {rev_input['item_desc']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Giá anh định bán tại VN: <b>{sale_fmt} đ</b>\n"
            f"• Lợi nhuận kỳ vọng ({calc['profit_label']}): <b>-{calc['profit_vnd']:,} đ</b>\n"
            f"• Phí ship Nhật - VN & kho: <b>-{ship_fmt} đ</b>\n"
            f"• Phí bảo dưỡng xăng đá dự kiến: <b>-{maint_fmt} đ</b>\n"
            f"👉 <b>TIỀN MUA TỐI ĐA TRÊN SÀN: {max_pur_fmt} đ (~{max_bid_fmt} yên)</b>\n\n"
            f"🎯 <b>KHUYẾN NGHỊ:</b> Trên sàn Yahoo chỉ được bid tối đa <b>{max_bid_fmt} yên</b>!\n"
            f"⚠️ <i>Nếu sàn vượt quá {max_bid_fmt} yên ➔ <b>DỪNG LẠI</b>, vì mua tiếp sẽ bị hụt lãi!</i>"
        )
        keyboard = [
            [InlineKeyboardButton(f"➕ Đặt trần: {max_bid_fmt}Y", callback_data=f"quick_calc_data:{calc['max_bid_jpy']}")]
        ]
        await update.effective_message.reply_html(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 3. Kiểm tra Hẹn giờ canh tàn phiên (HƯỚNG 4 - Sniper Alert)
    from parser import parse_sniper_timer_input
    sniper = parse_sniper_timer_input(text)
    if sniper:
        import asyncio
        from datetime import datetime, timedelta
        chat_id = update.effective_chat.id
        item = sniper["item_desc"]

        if sniper["type"] == "countdown":
            wait_secs = sniper["minutes"] * 60
            wait_label = f"{sniper['minutes']} phút"
        else:
            now = datetime.now()
            target_hour = sniper["hour"]
            target_min = sniper["minute"]
            target_dt = now.replace(hour=target_hour, minute=target_min, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += timedelta(days=1)
            wait_secs = int((target_dt - now).total_seconds())
            wait_label = f"{target_hour:02d}:{target_min:02d}"

        async def _sniper_job(delay: int, bot, cid: int, itm: str, lbl: str):
            if delay > 300:
                await asyncio.sleep(delay - 300)
                try:
                    await bot.send_message(
                        chat_id=cid,
                        text=f"⏰ <b>NHẮC CANH BID (CÒN 5 PHÚT):</b>\n\nCây <b>{itm}</b> sắp tàn phiên lúc {lbl}! Anh vào sàn chuẩn bị sẵn sàng nhé! 🎯",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
                await asyncio.sleep(300)
            else:
                await asyncio.sleep(delay)

            try:
                await bot.send_message(
                    chat_id=cid,
                    text=f"🔔 <b>ĐÃ ĐẾN GIỜ TÀN PHIÊN!</b>\n\nCây <b>{itm}</b> đang ở những giây cuối cùng! Anh vào sàn chốt bid ngay nhé! ⚡",
                    parse_mode="HTML"
                )
            except Exception:
                pass

        asyncio.create_task(_sniper_job(wait_secs, context.bot, chat_id, item, wait_label))
        await update.effective_message.reply_html(
            f"✅ <b>Đã đặt lịch canh bid cho:</b> <i>{item}</i>\n"
            f"⏰ Thời điểm hẹn: <b>{wait_label}</b> (sau {wait_secs // 60} phút nữa)\n\n"
            f"<i>Bot sẽ réo chuông báo trước 5 phút và đúng thời điểm để anh không bao giờ bị lỡ phiên!</i>"
        )
        return

    # 4. Kiểm tra tính nhẩm nhanh giá Yahoo/eBay (Quick JPY Bid Calculator)
    from parser import parse_quick_calc_input
    calc_res = parse_quick_calc_input(text)
    if calc_res:
        jpy_fmt = f"{calc_res['amount_jpy']:,}".replace(",", ".")
        base_vnd_fmt = f"{calc_res['base_vnd']:,}".replace(",", ".")
        fee_vnd_fmt = f"{calc_res['shipping_fee_vnd']:,}".replace(",", ".")
        total_vnd_fmt = f"{calc_res['total_landing_vnd']:,}".replace(",", ".")

        msg = (
            f"🧮 <b>TÍNH NHANH GIÁ BID & VỀ TAY</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Giá bid trên sàn: <b>{jpy_fmt} yên</b>\n"
            f"• Tiền mua quy đổi (tỷ giá {calc_res['rate']}): <b>~{base_vnd_fmt} đ</b>\n"
            f"• Phí vận chuyển & kho ước tính: <b>~{fee_vnd_fmt} đ</b>\n"
            f"👉 <b>TỔNG TIỀN VỀ TAY DỰ KIẾN: ~{total_vnd_fmt} đ</b>\n\n"
            f"💡 <i>Mẹo đi bid: Nếu định giá bán lại cây này tại VN trên {total_vnd_fmt} đ "
            f"thì mức bid {jpy_fmt} yên vẫn có lời!</i>"
        )
        keyboard = [
            [InlineKeyboardButton(f"➕ Gợi ý lưu: /data ... {jpy_fmt}Y", callback_data=f"quick_calc_data:{calc_res['amount_jpy']}")]
        ]
        await update.effective_message.reply_html(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # 5. Kiểm tra Tra cứu mộc đáy & năm sản xuất Zippo / Vintage
    from parser import decode_lighter_stamp
    stamp_res = decode_lighter_stamp(text)
    if stamp_res:
        msg = (
            f"🔍 <b>GIẢI MÃ MỘC ĐÁY & NĂM SẢN XUẤT</b>\n"
            f"📦 <b>Dòng quẹt:</b> <b>{stamp_res['model']}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>Năm sản xuất:</b> <b>{stamp_res['year']}</b> (Mã: <code>{stamp_res['stamp_code']}</code>)\n"
            f"📝 <b>Đặc điểm mộc đáy:</b> {stamp_res['stamp_desc']}\n"
            f"⚙️ <b>Đặc điểm ruột (Insert):</b> {stamp_res['insert_features']}\n"
            f"💰 <b>Giá thị trường VN tham khảo:</b> <b>{stamp_res['market_price_vnd']}</b>\n\n"
            f"💡 <b>Lưu ý dân chơi:</b> <i>{stamp_res['collector_note']}</i>"
        )
        await update.effective_message.reply_html(msg)
        return

    # 6. Kiểm tra Cẩm nang bắt bệnh & thông số ron sửa quẹt
    from parser import get_lighter_repair_guide
    rep_res = get_lighter_repair_guide(text)
    if rep_res:
        rep_lines = [
            f"🔧 <b>{rep_res['title'].upper()}</b>",
            f"━━━━━━━━━━━━━━━━━━━━━",
            f"⚠️ <b>Triệu chứng:</b> {rep_res['symptoms']}",
            f"\n📐 <b>THÔNG SỐ RON (O-RING) CHUẨN XÁC:</b>",
        ]
        for sp in rep_res["oring_specs"]:
            rep_lines.append(sp)
        rep_lines.append(f"\n🛠️ <b>CÁC BƯỚC XỬ LÝ CHUẨN THỢ:</b>")
        for st in rep_res["fix_steps"]:
            rep_lines.append(st)
        rep_lines.append(f"\n{rep_res['warning']}")
        await update.effective_message.reply_html("\n".join(rep_lines))
        return

    # 7. Kiểm tra xem user có đang có bản nháp chờ giá (clarify_price) không
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM drafts WHERE user_id = ? AND draft_type = 'clarify_price' ORDER BY created_at DESC LIMIT 1;",
            (update.effective_user.id,),
        )
        draft_row = cur.fetchone()
        if draft_row:
            # Kiểm tra xem tin nhắn có phải là số tiền không (ví dụ: 300k, 300k vnd, 50$, 1tr5, 30000, 30.000Y)
            from parser import parse_multi_currency_price
            val, curr, err, sugg = parse_multi_currency_price(text)

            lower_text = text.lower().strip()
            if lower_text in ["vnd", "vnđ", "đ", "tien viet", "tiền việt", "d"]:
                val = 300000
                curr = "VND"
            elif lower_text in ["yen", "yên", "jpy", "y"]:
                val = 30000
                curr = "JPY"
            elif lower_text in ["usd", "$", "do", "dola", "đô"]:
                val = 50
                curr = "USD"
            elif val is None and sugg:
                val = sugg[0]["amount"]
                curr = sugg[0]["currency"]
            elif curr == "AMBIGUOUS" and sugg:
                val = sugg[0]["amount"]
                curr = sugg[0]["currency"]

            if val is not None and val > 0:
                payload = json.loads(draft_row["payload"])
                next_id = generate_next_id(conn)
                from handlers.data_entry import format_saved_record_message, get_saved_record_keyboard
                record = Record(
                    id=next_id,
                    owner_user_id=update.effective_user.id,
                    raw_text=payload["raw_desc"],
                    display_name=payload.get("display_name", payload["raw_desc"]),
                    normalized_search_text="",
                    amount_jpy=val,
                    currency=curr,
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
                from handlers.data_entry import auto_set_record_bid_cap
                auto_set_record_bid_cap(conn, saved)
                delete_draft(conn, draft_row["draft_id"])

                msg_text = format_saved_record_message(saved)
                reply_markup = get_saved_record_keyboard(saved)
                price_notif = format_currency_amount(val, curr)
                await update.effective_message.reply_html(
                    f"🎯 <i>Đã nhận diện giá {price_notif} và lưu thành công bản nháp:</i>\n\n{msg_text}",
                    reply_markup=reply_markup,
                )
                return
    finally:
        conn.close()

    await handle_search_query(update, context, text)


async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tất cả các callback liên quan đến tìm kiếm và khuyến nghị đi bid."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    data = query.data
    db_path = context.bot_data["config"].db_path
    conn = get_db_connection(db_path)
    try:
        if data.startswith("view_grp:"):
            sk_prefix = data.split(":", 1)[1]
            cur = conn.cursor()
            cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY created_at DESC;")
            rows = cur.fetchall()
            all_recs = [Record.from_dict(dict(r)) for r in rows]
            matched_recs = [r for r in all_recs if r.scope_key().startswith(sk_prefix)]
            if matched_recs:
                first = matched_recs[0]
                sk = first.scope_key()
                from repository import get_bid_cap
                from pricing import calculate_reference_pricing
                from search import format_scope_title
                cap = get_bid_cap(conn, sk)
                pricing = calculate_reference_pricing(matched_recs, cap)
                group = SearchGroup(
                    scope_key=sk,
                    display_title=format_scope_title(first),
                    brand=first.brand,
                    line=first.line,
                    material=first.material,
                    color=first.color,
                    box=first.box,
                    condition=first.cosmetic_condition,
                    records=matched_recs,
                    pricing=pricing,
                )
                msg_text = format_group_detail_message(group)
                reply_markup = get_group_detail_keyboard(group)
                await query.message.reply_html(msg_text, reply_markup=reply_markup)
            else:
                await query.message.reply_text("Không tìm thấy thông tin nhóm quẹt này.")

        elif data.startswith("grp_tx:"):
            sk_prefix = data.split(":", 1)[1]
            cur = conn.cursor()
            cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY created_at DESC;")
            rows = cur.fetchall()
            all_recs = [Record.from_dict(dict(r)) for r in rows]
            matched_recs = [r for r in all_recs if r.scope_key().startswith(sk_prefix)]
            if matched_recs:
                lines = [f"📋 <b>LỊCH SỬ MUA CHO NHÓM ({len(matched_recs)} LẦN):</b>\n"]
                for idx, r in enumerate(matched_recs, start=1):
                    d_str = f" ({r.auction_date})" if r.auction_date else ""
                    cond = f" - Tình trạng: {r.cosmetic_condition}" if r.cosmetic_condition != "unknown" else ""
                    lines.append(f"<b>{idx}. #{r.id}</b>: {r.display_name}\n   ➔ {format_currency_amount(r.amount_jpy, r.currency, with_approx=True)}{d_str}{cond}")
                await query.message.reply_html("\n".join(lines))
            else:
                await query.message.reply_text("Chưa có lịch sử giao dịch.")

        elif data.startswith("srch_page:"):
            parts = data.split(":", 2)
            page = int(parts[1])
            q_text = parts[2]
            await handle_search_query(update, context, q_text, page=page)

        elif data.startswith("srch_opt:"):
            q_text = data.split(":", 1)[1]
            await handle_search_query(update, context, q_text)

        elif data.startswith("quick_win:"):
            sk_prefix = data.split(":", 1)[1]
            cur = conn.cursor()
            cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY created_at DESC;")
            rows = cur.fetchall()
            matched_name = ""
            for r in rows:
                rec = Record.from_dict(dict(r))
                if rec.scope_key().startswith(sk_prefix):
                    matched_name = rec.display_name
                    break
            if not matched_name:
                matched_name = "quẹt vừa thắng"

            await query.message.reply_html(
                f"🎉 <b>Chúc mừng anh đã thắng phiên!</b>\n\n"
                f"Để lưu nhanh giá thắng vào kho, anh copy dòng lệnh dưới đây và sửa số tiền thực tế:\n\n"
                f"<code>/data {matched_name} 13.400Y</code>\n\n"
                f"<i>(Sau khi gửi, bot sẽ tự động cập nhật mốc trần mới cho cây này!)</i>"
            )

        elif data.startswith("quick_calc_data:"):
            amt = data.split(":", 1)[1]
            amt_fmt = f"{int(amt):,}".replace(",", ".")
            await query.message.reply_html(
                f"<b>Mẫu lưu nhanh cho giá {amt_fmt} yên:</b>\n\n"
                f"<code>/data dupont sơn mài 1 line xanh lá {amt_fmt}Y</code>\n\n"
                f"<i>Anh thay tên cây quẹt và gửi để lưu vào kho nhé!</i>"
            )
        elif data.startswith("matrix:"):
            sk_prefix = data.split(":", 1)[1]
            cur = conn.cursor()
            cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY created_at DESC;")
            rows = cur.fetchall()
            all_recs = [Record.from_dict(dict(r)) for r in rows]
            matched_recs = [r for r in all_recs if r.scope_key().startswith(sk_prefix)]
            if matched_recs:
                first = matched_recs[0]
                sk = first.scope_key()
                from repository import get_bid_cap
                from pricing import calculate_reference_pricing, get_condition_price_matrix
                from search import format_scope_title
                cap = get_bid_cap(conn, sk)
                pricing = calculate_reference_pricing(matched_recs, cap)
                base_p = pricing.cap_amount_jpy or pricing.reference_price_jpy or 13400
                matrix = get_condition_price_matrix(base_p, first.currency)
                title = format_scope_title(first)

                lines = [
                    "📊 <b>BẢNG GIÁ 4 CẤP ĐỘ TÌNH TRẠNG</b>",
                    f"📦 <b>{title}</b>",
                    "━━━━━━━━━━━━━━━━━━━━━",
                ]
                for lvl in matrix:
                    lines.append(f"{lvl['label']}:")
                    lines.append(f"👉 <b>{lvl['price_text']}</b>")
                    lines.append(f"<i>({lvl['note']})</i>\n")

                lines.append("💡 <i>Anh nhìn ảnh cây quẹt trên sàn xem thuộc cấp độ nào để chốt mức bid tương ứng nhé!</i>")
                await query.message.reply_html("\n".join(lines))
            else:
                await query.message.reply_text("Không tìm thấy dữ liệu nhóm để tính bảng giá.")

        elif data.startswith("quick_win_yahoo:"):
            parts = data.split(":", 2)
            auc_id = parts[1]
            p_str = parts[2] if len(parts) >= 3 else "13400"
            p_fmt = f"{int(p_str):,}".replace(",", ".")
            await query.message.reply_html(
                f"🎉 <b>Chúc mừng anh đã thắng phiên Yahoo (#{auc_id})!</b>\n\n"
                f"Để lưu nhanh vào kho, anh copy dòng dưới và sửa số tiền thực tế nếu cần:\n\n"
                f"<code>/data Yahoo #{auc_id} {p_fmt}Y</code>\n\n"
                f"<i>(Sau khi gửi, bot sẽ tự động cập nhật mốc trần mới cho cây này!)</i>"
            )

        elif data.startswith("matrix_price:"):
            price_jpy = int(data.split(":")[1])
            from pricing import get_condition_price_matrix
            matrix = get_condition_price_matrix(price_jpy, "JPY")
            lines = [
                "📊 <b>BẢNG GIÁ 4 CẤP ĐỘ TÌNH TRẠNG</b>",
                f"Mốc giá gốc tham chiếu: <b>{price_jpy:,} yên</b>".replace(",", "."),
                "━━━━━━━━━━━━━━━━━━━━━",
            ]
            for lvl in matrix:
                lines.append(f"{lvl['label']}:")
                lines.append(f"👉 <b>{lvl['price_text']}</b>")
                lines.append(f"<i>({lvl['note']})</i>\n")

            lines.append("💡 <i>Anh nhìn ảnh cây quẹt trên sàn xem thuộc cấp độ nào để chốt mức bid tương ứng nhé!</i>")
            await query.message.reply_html("\n".join(lines))

        elif data.startswith("save_yahoo_lot:"):
            parts = data.split(":")
            auc_id = parts[1]
            price_jpy = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 7281
            ship_jpy = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            cnt = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 1

            rec_id = generate_next_id(conn)
            title = f"Lô {cnt} cây bật lửa gas Yahoo #{auc_id}" if cnt > 1 else f"Quẹt Yahoo #{auc_id}"
            u_p = round(price_jpy / cnt) if cnt > 1 else price_jpy
            note = f"Lô {cnt} cây (~{u_p:,} yên/cây, ship {ship_jpy}Y). Chưa thử lửa (動作未確認). Giá chốt tàn phiên." if cnt > 1 else f"Quẹt Yahoo #{auc_id}, ship {ship_jpy}Y."

            from normalizer import clean_search_text
            new_rec = Record(
                id=rec_id,
                owner_user_id=query.from_user.id if query.from_user else 0,
                raw_text=f"{title} {price_jpy}Y",
                display_name=title,
                normalized_search_text=clean_search_text(f"{title} {auc_id} lô {cnt} cây"),
                amount_jpy=price_jpy,
                currency="JPY",
                brand="unknown",
                is_lot=(cnt > 1),
                fee_jpy=ship_jpy,
                auction_id=auc_id,
                source_url=f"https://page.auctions.yahoo.co.jp/jp/auction/{auc_id}",
                note=note,
                cosmetic_condition="Xước nhẹ theo thời gian",
                functional_state="Chưa thử lửa (chưa kiểm tra)",
            )
            create_record(conn, new_rec)

            u_p_fmt = f"{u_p:,}".replace(",", ".")
            p_fmt = f"{price_jpy:,}".replace(",", ".")
            ship_fmt = f"{ship_jpy:,}".replace(",", ".")

            await query.message.reply_html(
                f"✅ <b>ĐÃ LƯU KẾT QUẢ ĐẤU GIÁ VÀO KHO DATA!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"• Mã bản ghi: <b>#{rec_id}</b>\n"
                f"• Phân loại: <b>Lô {cnt} cây</b>\n"
                f"• Giá chốt: <b>{p_fmt} yên</b> (~{u_p_fmt} yên/cây)\n"
                f"• Phí ship Nhật: <b>{ship_fmt} yên</b>\n"
                f"• Ghi chú: <i>{note}</i>\n\n"
                f"💡 <i>Anh có thể tra cứu lại bất kỳ lúc nào bằng cách gõ: <code>{auc_id}</code> hoặc <code>lô {cnt} cây</code>!</i>"
            )

        elif data.startswith("val_fin:"):
            parts = data.split(":")
            p_val = int(parts[1])
            s_val = int(parts[2])
            cnt_val = int(parts[3])
            is_lot_val = parts[4] == "1"
            brand_val = parts[5] if len(parts) > 5 else "unknown"

            from pricing import estimate_market_valuation, format_financial_pnl_report
            val = estimate_market_valuation(
                title=brand_val,
                description="",
                current_price_jpy=p_val,
                shipping_fee_jpy=s_val,
                is_lot=is_lot_val,
                lot_count=cnt_val,
            )
            msg = format_financial_pnl_report(val)
            await query.message.reply_html(msg)

        elif data.startswith("yh_imgs:"):
            auc_id = data.split(":")[1]
            imgs = context.bot_data.get(f"yh_imgs:{auc_id}", [])
            if not imgs:
                await query.answer("Đang tải ảnh từ Yahoo...", show_alert=False)
                from parser import fetch_yahoo_auction_info
                info = await fetch_yahoo_auction_info(f"https://page.auctions.yahoo.co.jp/jp/auction/{auc_id}")
                imgs = info.get("images", [])
                context.bot_data[f"yh_imgs:{auc_id}"] = imgs

            if not imgs:
                await query.message.reply_text("Không tìm thấy ảnh chi tiết cho phiên đấu này.")
                return

            from telegram import InputMediaPhoto
            media = [InputMediaPhoto(media=u) for u in imgs[:5] if u.startswith("http")]
            if media:
                await query.answer(f"Đang gửi {len(media)} ảnh nét...")
                try:
                    if len(media) >= 2:
                        await context.bot.send_media_group(chat_id=query.message.chat_id, media=media)
                    else:
                        await context.bot.send_photo(
                            chat_id=query.message.chat_id,
                            photo=media[0].media,
                            caption=f"📸 <b>Ảnh chi tiết #{auc_id}</b>",
                            parse_mode="HTML",
                        )
                except Exception:
                    img_links = "\n".join([f"• <a href='{u}'>Ảnh chi tiết {i+1}</a>" for i, u in enumerate(imgs[:5])])
                    await query.message.reply_html(f"📸 <b>Album ảnh #{auc_id}:</b>\n{img_links}")
            else:
                await query.message.reply_text("Không có link ảnh hợp lệ.")

        elif data.startswith("yh_alarm:"):
            auc_id = data.split(":")[1]
            info = context.bot_data.get(f"yh_info:{auc_id}", {})
            title = info.get("title", f"Phiên đấu #{auc_id}")
            price = info.get("current_price_jpy")
            end_iso = info.get("end_time", "")
            url = info.get("url", f"https://page.auctions.yahoo.co.jp/jp/auction/{auc_id}")

            import asyncio
            import time
            from datetime import datetime, timezone

            wait_secs = 15 * 60  # Mặc định 15 phút
            if end_iso:
                try:
                    target_dt = datetime.fromisoformat(end_iso)
                    now_dt = datetime.now(target_dt.tzinfo or timezone.utc)
                    rem = (target_dt - now_dt).total_seconds()
                    if rem > 15 * 60:
                        wait_secs = rem - (15 * 60)
                    elif rem > 60:
                        wait_secs = rem - 60
                    else:
                        wait_secs = 10
                except Exception:
                    wait_secs = 15 * 60

            chat_id = query.message.chat_id
            trigger_at = time.time() + wait_secs

            from repository import add_auction_alarm
            alarm_id = add_auction_alarm(conn, auc_id, chat_id, title, price, url, end_iso, trigger_at)

            async def _alarm_coro(aid=alarm_id, db_p=db_path):
                await asyncio.sleep(wait_secs)
                p_text = f" (Giá hiện tại: {price:,} yên)".replace(",", ".") if price else ""
                alert_msg = (
                    f"🚨 <b>BÁO ĐỘNG TÀN PHIÊN (CÒN 15 PHÚT NỮA HẾT GIỜ)!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📦 Cây: <b>{title}</b>\n"
                    f"⚡ {p_text}\n"
                    f"👉 <a href='{url}'>Mở Yahoo</a> | <a href='https://buyee.jp/item/yahoo/auction/{auc_id}?lang=vi'>Mở Buyee để Snipe</a>\n\n"
                    f"<i>Vào đặt bid ngay kẻo vuột cây ngon anh nhé!</i>"
                )
                try:
                    await context.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode="HTML")
                except Exception:
                    pass
                if aid:
                    c = get_db_connection(db_p)
                    try:
                        from repository import mark_alarm_sent
                        mark_alarm_sent(c, aid)
                    except Exception:
                        pass
                    finally:
                        c.close()

            asyncio.create_task(_alarm_coro())
            wait_m = round(wait_secs / 60)
            await query.answer("Đã hẹn giờ canh tàn phiên!")
            await query.message.reply_html(
                f"⏰ <b>ĐÃ ĐẶT HẸN GIỜ CANH TÀN PHIÊN (#{auc_id})!</b>\n"
                f"• Cây: <i>{title}</i>\n"
                f"• Thời điểm nhắc: <b>Trước khi hết giờ 15 phút</b> (khoảng {wait_m} phút nữa).\n\n"
                f"<i>Bot sẽ tự động réo Telegram kèm link Buyee & Yahoo để anh vào snipe kịp thời!</i>"
            )
    finally:
        conn.close()


async def quick_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý nút gợi ý thêm nhanh."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()
    kw = query.data.split(":", 1)[1]
    await query.message.reply_html(
        f"<b>Mẫu nhập nhanh cho {kw}:</b>\n\n"
        f"<code>/data {kw} 13.400Y</code>\n\n"
        f"<i>Anh copy dòng trên và chỉnh sửa giá theo thực tế cây vừa đấu.</i>"
    )


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /find <từ khóa>."""
    if not update.effective_message:
        return
    text = update.effective_message.text or ""
    query = text[len("/find"):].strip()
    if not query:
        await update.effective_message.reply_text("Vui lòng nhập từ khóa cần tìm. Ví dụ: /find dupont sơn mài")
        return
    await handle_search_query(update, context, query)
