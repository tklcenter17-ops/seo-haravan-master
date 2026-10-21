"""Handler cho lệnh /radar và /radar_lot: Quét và hiển thị ĐẦY ĐỦ (FULL) các lô bật lửa có bid kết thúc hôm nay."""
from __future__ import annotations

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from radar_service import format_radar_chunks, format_radar_message, scan_today_lighter_lots
from repository import get_radar_setting, set_radar_setting

logger = logging.getLogger(__name__)

# Bộ nhớ tạm lưu kết quả quét gần nhất để lật trang tức thì
_RADAR_CACHE: dict[str, Any] = {
    "lots": [],
    "mode": "lot",
    "cat_name": "LÔ BẬT LỬA",
    "rate": 165,
    "min_count": 0,
    "cond_filter": "all",
    "cached_at": 0,
}


def _filter_lots(lots: list[dict[str, Any]], min_count: int = 0, cond_filter: str = "all") -> list[dict[str, Any]]:
    """Lọc danh sách lot theo số cây và tình trạng hoạt động."""
    filtered: list[dict[str, Any]] = []
    for it in lots:
        cnt = it.get("lighter_count") or 0
        # Quy tắc: Lot chưa rõ số lượng (cnt == 0) không được tự động xếp vào bộ lọc "từ 5 cây" hoặc "từ 10 cây"
        if min_count > 0:
            if cnt == 0 and min_count >= 5:
                continue
            if cnt > 0 and cnt < min_count:
                continue

        cond_lbl = (it.get("condition_label") or "").lower()
        if cond_filter == "working" and not any(k in cond_lbl for k in ("hoạt động", "đã kiểm tra")):
            continue
        elif cond_filter == "untested" and "chưa kiểm tra" not in cond_lbl:
            continue
        elif cond_filter == "junk" and "junk" not in cond_lbl:
            continue

        filtered.append(it)
    return filtered


def _get_radar_page_keyboard(
    current_page: int,
    total_pages: int,
    total_lots: int,
    is_auto_on: bool,
    current_mode: str = "lot",
    min_count: int = 0,
    cond_filter: str = "all",
) -> InlineKeyboardMarkup:
    """Tạo bàn phím điều khiển và phân trang cho Radar với các bộ lọc chuẩn."""
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

    # Hàng 2: Lọc theo số cây (Quy tắc người dùng yêu cầu: Tất cả / ≥2 / ≥5 / ≥10 cây)
    c0 = "🔘 Tất cả" if min_count == 0 else "⚪ Tất cả"
    c2 = "🔘 ≥2 cây" if min_count == 2 else "⚪ ≥2 cây"
    c5 = "🔘 ≥5 cây" if min_count == 5 else "⚪ ≥5 cây"
    c10 = "🔘 ≥10 cây" if min_count == 10 else "⚪ ≥10 cây"
    keyboard.append([
        InlineKeyboardButton(c0, callback_data="radar_count:0"),
        InlineKeyboardButton(c2, callback_data="radar_count:2"),
        InlineKeyboardButton(c5, callback_data="radar_count:5"),
        InlineKeyboardButton(c10, callback_data="radar_count:10"),
    ])

    # Hàng 3: Lọc nhanh 4 phân loại chính theo yêu cầu người dùng
    b_thapcam = "🔘 Thập Cẩm" if current_mode in ("lot", "thapcam") else "📦 Thập Cẩm"
    b_gas = "🔘 Gas Đá" if current_mode in ("gas_da", "gas") else "⚡ Gas Đá"
    b_dau = "🔘 Dầu" if current_mode in ("dau", "oil") else "🛢️ Dầu"
    b_zippo = "🔘 Zippo" if current_mode == "zippo" else "🔥 Zippo"
    keyboard.append([
        InlineKeyboardButton(b_thapcam, callback_data="radar_brand:thapcam"),
        InlineKeyboardButton(b_gas, callback_data="radar_brand:gas_da"),
        InlineKeyboardButton(b_dau, callback_data="radar_brand:dau"),
        InlineKeyboardButton(b_zippo, callback_data="radar_brand:zippo"),
    ])

    # Hàng 4: Lọc theo tình trạng
    k_all = "✔️ Tất cả" if cond_filter == "all" else "Tất cả"
    k_work = "⚡ Hoạt động" if cond_filter == "working" else "Hoạt động"
    k_untested = "❓ Chưa test" if cond_filter == "untested" else "Chưa test"
    k_junk = "⚠️ Junk/Xác" if cond_filter == "junk" else "Junk"
    keyboard.append([
        InlineKeyboardButton(k_all, callback_data="radar_cond:all"),
        InlineKeyboardButton(k_work, callback_data="radar_cond:working"),
        InlineKeyboardButton(k_untested, callback_data="radar_cond:untested"),
        InlineKeyboardButton(k_junk, callback_data="radar_cond:junk"),
    ])

    # Hàng 5: Nút xem Album ảnh, Audit & Gửi toàn bộ
    row5 = [
        InlineKeyboardButton("🖼️ Lướt Album Ảnh", callback_data="radar_album"),
        InlineKeyboardButton("🛡️ Xem ca bị loại", callback_data="radar_view_audit"),
    ]
    if total_lots > 8:
        row5.append(InlineKeyboardButton(f"📜 Gửi hết {total_lots} lô", callback_data="radar_send_all"))
    keyboard.append(row5)

    # Hàng 6: Cài đặt và làm mới
    toggle_text = "🔔 Tự động: BẬT" if is_auto_on else "🔕 Tự động: TẮT"
    keyboard.append([
        InlineKeyboardButton("🔄 Quét lại", callback_data="radar_refresh"),
        InlineKeyboardButton(toggle_text, callback_data="radar_toggle_auto"),
    ])

    return InlineKeyboardMarkup(keyboard)


def _resolve_brand_mode(args: list[str]) -> tuple[str, str]:
    """Phân giải tham số lệnh để xác định phân loại cần quét."""
    for a in args:
        al = a.lower().strip()
        if al in ("gas", "gasda", "gas_da", "da", "flint"):
            return "gas_da", "LOT GAS ĐÁ"
        elif al in ("dau", "oil", "xang", "xangdau", "xang_dau"):
            return "dau", "BẬT LỬA DẦU"
        elif al in ("zippo", "zp"):
            return "zippo", "ZIPPO (LÔ)"
        elif al in ("thapcam", "thap_cam", "mix", "honhop"):
            return "thapcam", "LÔ THẬP CẨM"
        elif al in ("dupont", "dp"):
            return "dupont", "S.T. DUPONT"
        elif al in ("dunhill", "dh"):
            return "dunhill", "ALFRED DUNHILL"
        elif al in ("lot", "lo", "si", "sỉ"):
            return "lot", "LÔ BẬT LỬA"
    return "lot", "LÔ BẬT LỬA"


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /radar hoặc /radar_lot.
    
    Cú pháp:
    • /radar: Xem các lô bật lửa có bid hôm nay
    • /radar gas: Quét riêng Lot Gas Đá kết thúc hôm nay
    • /radar dau: Quét riêng Bật Lửa Dầu kết thúc hôm nay
    • /radar zippo: Quét riêng Zippo có bid hôm nay
    • /radar thapcam: Quét riêng Lô Thập Cẩm kết thúc hôm nay
    • /radar all: Bắn toàn bộ 100% tất cả các lô hôm nay thành nhiều tin nhắn
    """
    msg = update.effective_message
    if not msg:
        return

    logger.info(f"🎯 [RADAR] Nhận lệnh từ user: {msg.from_user.id if msg.from_user else None} | text='{msg.text}'")

    args = context.args or []
    send_all_requested = any(a.lower() in ("all", "full", "tatca") for a in args)
    brand_mode, cat_name = _resolve_brand_mode(args)

    # 1. Báo trạng thái typing ngay lập tức
    try:
        await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
    except Exception:
        pass

    # 2. Gửi tin nhắn thông báo tiến trình rõ ràng cho người dùng
    wait_msg = None
    try:
        wait_msg = await msg.reply_html(
            f"🔍 <b>Radar đang quét sâu {cat_name} hôm nay trên Yahoo Auctions...</b>\n"
            f"<i>Đang rà soát các phiên có lượt bid, anh chờ em 3-5 giây nhé!</i>"
        )
    except Exception as e:
        logger.warning(f"Không thể gửi tin nhắn loading ban đầu: {e}")

    try:
        cfg = context.bot_data.get("config")
        rate = 165
        is_auto_on = True
        if cfg:
            conn = get_db_connection(cfg.db_path)
            try:
                from repository import get_exchange_rate
                rate = get_exchange_rate(conn)
                val = get_radar_setting(conn, "auto_radar_enabled", default="1")
                is_auto_on = (val == "1")
            finally:
                conn.close()

        import asyncio
        lots = await scan_today_lighter_lots(mode=brand_mode)
        _RADAR_CACHE["lots"] = lots
        _RADAR_CACHE["mode"] = brand_mode
        _RADAR_CACHE["cat_name"] = cat_name
        _RADAR_CACHE["rate"] = rate

        min_c = _RADAR_CACHE.get("min_count", 0)
        cond_f = _RADAR_CACHE.get("cond_filter", "all")
        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)

        if send_all_requested:
            # Gửi toàn bộ dạng chunks với giãn cách an toàn
            chunks = format_radar_chunks(active_lots, chunk_size=8, rate=rate, category_name=cat_name)
            if wait_msg:
                try:
                    await wait_msg.delete()
                except Exception:
                    pass
            for chunk in chunks:
                await msg.reply_html(chunk, disable_web_page_preview=True)
                await asyncio.sleep(1.0)
        else:
            formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=cat_name)
            keyboard = _get_radar_page_keyboard(
                1, total_pages, len(active_lots), is_auto_on, current_mode=brand_mode, min_count=min_c, cond_filter=cond_f
            )
            if wait_msg:
                await wait_msg.edit_text(
                    formatted_text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
            else:
                await msg.reply_html(
                    formatted_text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
    except Exception as e:
        logger.error(f"Lỗi khi thực thi lệnh /radar: {e}", exc_info=True)
        err_text = f"⚠️ <i>Có lỗi xảy ra khi quét Yahoo Auctions: {e}</i>"
        if wait_msg:
            try:
                await wait_msg.edit_text(err_text, parse_mode="HTML")
            except Exception:
                await msg.reply_html(err_text)
        else:
            await msg.reply_html(err_text)


async def radar_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm inline của Radar: lật trang, đổi hãng, đổi lọc số cây/tình trạng, xem audit."""
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

    rate = 165
    conn = get_db_connection(cfg.db_path)
    try:
        from repository import get_exchange_rate, get_lot_audit_logs
        rate = get_exchange_rate(conn)
        val = get_radar_setting(conn, "auto_radar_enabled", default="1")
        is_auto_on = (val == "1")
    finally:
        conn.close()

    curr_mode = _RADAR_CACHE.get("mode", "lot")
    cat_name = _RADAR_CACHE.get("cat_name", "LÔ BẬT LỬA")
    min_c = _RADAR_CACHE.get("min_count", 0)
    cond_f = _RADAR_CACHE.get("cond_filter", "all")

    if data.startswith("radar_page:"):
        page_num = int(data.split(":")[1])
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots

        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        formatted_text, total_pages = format_radar_message(active_lots, page=page_num, per_page=8, rate=rate, category_name=cat_name)
        keyboard = _get_radar_page_keyboard(page_num, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
        try:
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    elif data.startswith("radar_count:"):
        # Thay đổi bộ lọc số cây (0, 2, 5, 10)
        new_c = int(data.split(":")[1])
        _RADAR_CACHE["min_count"] = new_c
        min_c = new_c

        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots

        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=cat_name)
        keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
        try:
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    elif data.startswith("radar_cond:"):
        # Thay đổi bộ lọc tình trạng (all, working, untested, junk)
        new_cond = data.split(":")[1].strip()
        _RADAR_CACHE["cond_filter"] = new_cond
        cond_f = new_cond

        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots

        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=cat_name)
        keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
        try:
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    elif data.startswith("radar_brand:"):
        new_brand = data.split(":")[1].strip()
        brand_map = {
            "gas_da": "LOT GAS ĐÁ",
            "dau": "BẬT LỬA DẦU",
            "zippo": "ZIPPO (LÔ)",
            "thapcam": "LÔ THẬP CẨM",
            "lot": "LÔ BẬT LỬA",
            "dupont": "S.T. DUPONT",
            "dunhill": "ALFRED DUNHILL",
        }
        new_cat = brand_map.get(new_brand, "LÔ BẬT LỬA")
        try:
            await query.edit_message_text(f"🔄 <i>Đang quét Yahoo cho {new_cat}...</i>", parse_mode="HTML")
            lots = await scan_today_lighter_lots(mode=new_brand)
            _RADAR_CACHE["lots"] = lots
            _RADAR_CACHE["mode"] = new_brand
            _RADAR_CACHE["cat_name"] = new_cat
            _RADAR_CACHE["rate"] = rate

            active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
            formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=new_cat)
            keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=new_brand, min_count=min_c, cond_filter=cond_f)
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Lỗi khi chuyển brand radar: {e}")
            await query.edit_message_text(f"⚠️ <i>Lỗi: {e}</i>", parse_mode="HTML")

    elif data == "radar_view_audit":
        # Hiển thị các ca bị loại gần đây từ bảng Audit Log
        conn = get_db_connection(cfg.db_path)
        try:
            from repository import get_lot_audit_logs
            logs = get_lot_audit_logs(conn, limit=6)
        finally:
            conn.close()

        if not logs:
            audit_text = (
                "🛡️ <b>NHẬT KÝ KIỂM TOÁN PHÂN LOẠI (AUDIT)</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "<i>Chưa có phiên nào bị ghi nhận loại trừ gần đây. Mọi phiên nghi ngờ đều đang được kiểm soát chặt!</i>"
            )
        else:
            lines = [
                "🛡️ <b>CÁC PHIÊN BỊ LOẠI / AUDIT GẦN ĐÂY</b>",
                "<i>Hệ thống lọc chặt: chỉ duyệt phiên bán từ 2 cây bật lửa trở lên.</i>",
                "━━━━━━━━━━━━━━━━━━━━━",
            ]
            for idx, lg in enumerate(logs, 1):
                aid = lg.get("auction_id", "")
                title = lg.get("title", "")
                if len(title) > 40:
                    title = title[:38] + "..."
                code = lg.get("decision_code", "UNKNOWN")
                reason = lg.get("evidence_reason", "")
                price = lg.get("price_jpy", 0)

                lines.append(
                    f"<b>{idx}. [{code}]</b> <code>{aid}</code>\n"
                    f"📝 <i>{title}</i>\n"
                    f"💰 {price:,} yên | 💡 {reason}\n"
                    f"👉 <a href='https://page.auctions.yahoo.co.jp/jp/auction/{aid}'>Xem link Yahoo</a>"
                )
                lines.append("─────────────────────")
            lines.append("<i>Nếu phát hiện bot loại nhầm, vui lòng báo lại để cập nhật rule!</i>")
            audit_text = "\n".join(lines)

        back_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Quay lại danh sách Lot", callback_data="radar_back_lots")]
        ])
        try:
            await query.edit_message_text(audit_text, parse_mode="HTML", reply_markup=back_kb, disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"Lỗi hiển thị audit: {e}")

    elif data == "radar_back_lots":
        # Quay lại hiển thị danh sách lot bình thường
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots

        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=cat_name)
        keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
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
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots

        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        chunks = format_radar_chunks(active_lots, chunk_size=8, rate=rate, category_name=cat_name)
        await query.answer(f"Đang gửi toàn bộ danh sách {cat_name}...", show_alert=False)
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
            await query.edit_message_text(f"🔄 <i>Đang quét lại {cat_name} trên Yahoo...</i>", parse_mode="HTML")
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots
            _RADAR_CACHE["rate"] = rate

            active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
            formatted_text, total_pages = format_radar_message(active_lots, page=1, per_page=8, rate=rate, category_name=cat_name)
            keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
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
        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        total_pages = max(1, (len(active_lots) + 7) // 8)
        keyboard = _get_radar_page_keyboard(1, total_pages, len(active_lots), is_auto_on, current_mode=curr_mode, min_count=min_c, cond_filter=cond_f)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception:
            pass

    elif data == "radar_album":
        await query.answer("Đang mở album ảnh...", show_alert=False)
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode=curr_mode)
            _RADAR_CACHE["lots"] = lots
        active_lots = _filter_lots(lots, min_count=min_c, cond_filter=cond_f)
        valid_lots = [it for it in active_lots if it.get("image_url") and it.get("image_url", "").startswith("http")]
        if not valid_lots:
            await query.message.reply_text("Không tìm thấy ảnh lô nào trong danh sách hiện tại.")
            return

        media_group = []
        for idx, lot in enumerate(valid_lots[:8], start=1):
            title = lot.get("title", "")
            if len(title) > 40:
                title = title[:38] + "..."
            p_jpy = lot.get("price_jpy", 0)
            bids = lot.get("bids", 0)
            remain = lot.get("remain_text", "")
            aid = lot.get("auction_id", "")
            url = lot.get("url", f"https://auctions.yahoo.co.jp/jp/auction/{aid}")
            caption = (
                f"<b>#{idx}. {title}</b>\n"
                f"💰 {p_jpy:,}Y | 🔨 {bids} bids | ⏳ {remain}\n"
                f"👉 <a href='{url}'>Xem Yahoo</a> | Soi: /img_{aid}"
            ).replace(",", ".")
            media_group.append(InputMediaPhoto(media=lot["image_url"], caption=caption, parse_mode="HTML"))

        try:
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
        except Exception as e:
            logger.error(f"Lỗi khi gửi album ảnh: {e}")
            await query.message.reply_text(f"Không thể gửi album ảnh: {e}")


async def radar_img_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /radar_img hoặc /album: Lướt album ảnh của các lô hot nhất hôm nay."""
    msg = update.effective_message
    if not msg:
        return
    wait_msg = await msg.reply_html("🖼️ <i>Đang bốc album ảnh các lô bật lửa hôm nay...</i>")
    try:
        from radar_service import scan_today_lighter_lots
        lots = _RADAR_CACHE.get("lots") or []
        if not lots:
            lots = await scan_today_lighter_lots(mode="lot")
            _RADAR_CACHE["lots"] = lots

        valid_lots = [it for it in lots if it.get("image_url") and it.get("image_url", "").startswith("http")]
        if not valid_lots:
            await wait_msg.edit_text("Hiện chưa tìm thấy ảnh lô nào hôm nay.")
            return

        top_lots = valid_lots[:8]
        media_group = []
        for idx, lot in enumerate(top_lots, start=1):
            title = lot.get("title", "")
            if len(title) > 40:
                title = title[:38] + "..."
            p_jpy = lot.get("price_jpy", 0)
            bids = lot.get("bids", 0)
            remain = lot.get("remain_text", "")
            aid = lot.get("auction_id", "")
            url = lot.get("url", f"https://auctions.yahoo.co.jp/jp/auction/{aid}")

            caption = (
                f"<b>#{idx}. {title}</b>\n"
                f"💰 {p_jpy:,}Y | 🔨 {bids} bids | ⏳ {remain}\n"
                f"👉 <a href='{url}'>Xem Yahoo</a> | Soi: /img_{aid}"
            ).replace(",", ".")
            media_group.append(InputMediaPhoto(media=lot["image_url"], caption=caption, parse_mode="HTML"))

        await wait_msg.delete()
        await context.bot.send_media_group(chat_id=msg.chat_id, media=media_group)
    except Exception as e:
        logger.error(f"Lỗi khi gửi album ảnh: {e}", exc_info=True)
        await wait_msg.edit_text(f"⚠️ <i>Lỗi gửi album ảnh: {e}</i>", parse_mode="HTML")


async def img_detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /img hoặc /img_<aid>: Soi trọn bộ ảnh nét (đáy, bánh xe, góc) của 1 cây quẹt."""
    msg = update.effective_message
    if not msg:
        return

    aid = ""
    text = msg.text or ""
    if text.startswith("/img_"):
        parts = text.split()
        cmd_part = parts[0]
        aid = cmd_part[len("/img_"):].strip()
    elif context.args:
        aid = context.args[0].strip().lstrip("#")
    elif len(text.split()) > 1:
        aid = text.split()[1].strip().lstrip("#")

    if not aid:
        await msg.reply_html("❓ Vui lòng nhập mã lô, ví dụ: <code>/img t1248688687</code> hoặc bấm trực tiếp link <code>/img_t1248688687</code>")
        return

    wait_msg = await msg.reply_html(f"🔍 <i>Đang tải ảnh nét của phiên #{aid} từ Yahoo...</i>")
    try:
        from parser import fetch_yahoo_auction_info
        info = await fetch_yahoo_auction_info(aid)
        imgs = info.get("images", [])
        if not imgs and info.get("image_url"):
            imgs = [info["image_url"]]

        if not imgs:
            await wait_msg.edit_text(f"⚠️ Không tìm thấy ảnh chi tiết cho phiên <code>#{aid}</code>.")
            return

        title = info.get("title", f"Bật lửa #{aid}")
        price = info.get("current_price_jpy")
        p_str = f"{price:,} yên".replace(",", ".") if price else "Đang đấu"
        bids = info.get("bids", 0)
        url = info.get("url", f"https://auctions.yahoo.co.jp/jp/auction/{aid}")
        buyee_url = f"https://buyee.jp/item/yahoo/auction/{aid}?lang=vi"

        media_group = []
        for i, u in enumerate(imgs[:8]):
            if not u or not u.startswith("http"):
                continue
            if i == 0:
                caption = (
                    f"📸 <b>ẢNH CHI TIẾT ĐẤU GIÁ #{aid}</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📦 <b>{title}</b>\n"
                    f"💰 Giá: <b>{p_str}</b> | 🔨 <b>{bids} bids</b>\n"
                    f"👉 <a href='{url}'>Mở Yahoo</a> | <a href='{buyee_url}'>Mở Buyee để Bid</a>\n"
                    f"💡 <i>Lưu data:</i> <code>/data #{aid}</code>"
                )
            else:
                caption = f"Ảnh {i + 1}/{len(imgs)} (#{aid})"
            media_group.append(InputMediaPhoto(media=u, caption=caption, parse_mode="HTML"))

        if media_group:
            await wait_msg.delete()
            if len(media_group) >= 2:
                await context.bot.send_media_group(chat_id=msg.chat_id, media=media_group)
            else:
                await context.bot.send_photo(chat_id=msg.chat_id, photo=media_group[0].media, caption=media_group[0].caption, parse_mode="HTML")
        else:
            await wait_msg.edit_text("Không có link ảnh hợp lệ để hiển thị.")
    except Exception as e:
        logger.error(f"Lỗi khi soi ảnh #{aid}: {e}", exc_info=True)
        await wait_msg.edit_text(f"⚠️ <i>Lỗi tải ảnh: {e}</i>", parse_mode="HTML")
