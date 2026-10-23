"""Entry point chính khởi chạy Telegram Bot với Long Polling và Middleware bảo mật."""
from __future__ import annotations

import logging
import sys
import time
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.request import HTTPXRequest
from telegram.ext import (
    AIORateLimiter,
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    TypeHandler,
    filters,
)

from config import AppConfig, load_config, save_owner_id_to_env
from dashboard_server import start_dashboard_server
from db import get_db_connection, init_database
from handlers.admin import cancel_command, clean_command, export_command, rate_command, stats_command
from handlers.caps import cap_callback, cap_command
from handlers.data_entry import data_command, draft_callback, price_draft_callback
from handlers.ebay_handlers import ebay_callback_handler, radarebay_command
from ai_vision_service import inspect_lighter_lot_image
from handlers.radar_handlers import (
    ai_inspect_command,
    img_detail_command,
    radar_callback_handler,
    radar_command,
    radar_img_command,
)
from handlers.record_mgmt import (
    delete_command,
    donlo_command,
    recent_command,
    record_mgmt_callback,
    undo_command,
    view_command,
)
from handlers.search_handlers import find_command, quick_add_callback, search_callback, text_search_handler
from handlers.start import help_command, menu_callback, menu_command, start_command
from repository import mark_update_processed, register_update_if_new

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def auth_and_idempotency_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Middleware kiểm tra quyền sở hữu (Owner ID) và chống trùng update (Idempotency)."""
    cfg = context.bot_data["config"]
    user = update.effective_user
    msg = update.effective_message
    text_content = msg.text if msg else (update.callback_query.data if update.callback_query else "")

    logger.info(f"👉 [NHẬN UPDATE {update.update_id}] user={user.id if user else None} (@{user.username if user else None}) | type={update.effective_chat.type if update.effective_chat else None} | content='{text_content}'")

    # Nếu chưa thiết lập owner_id, tự động khoá với tài khoản đầu tiên kích hoạt
    allowed_owners = set(cfg.owner_ids) if getattr(cfg, "owner_ids", None) else ({cfg.owner_id} if cfg.owner_id else set())
    if not allowed_owners and user:
        save_owner_id_to_env(user.id)
        new_cfg = AppConfig(
            bot_token=cfg.bot_token,
            owner_id=user.id,
            db_path=cfg.db_path,
            backup_dir=cfg.backup_dir,
            price_high_threshold_jpy=cfg.price_high_threshold_jpy,
            owner_ids=(user.id,),
        )
        context.bot_data["config"] = new_cfg
        allowed_owners = {user.id}
        logger.info(f"Đã tự động xác thực và khoá TELEGRAM_OWNER_ID = {user.id}")
        if update.effective_message:
            await update.effective_message.reply_html(
                f"🔐 <b>Kích hoạt bảo mật thành công!</b>\n"
                f"Tài khoản của anh (ID: <code>{user.id}</code>) đã được khoá làm Chủ sở hữu (Owner) của bot."
            )

    # 1. Kiểm tra quyền sở hữu
    if not user or user.id not in allowed_owners:
        logger.warning(f"⛔ TỪ CHỐI USER: user_id={user.id if user else None} không thuộc danh sách owner_ids={allowed_owners}")
        if update.effective_message:
            try:
                await update.effective_message.reply_text(f"⛔ Bạn không có quyền truy cập bot này (ID của bạn: {user.id if user else 'unknown'}).")
            except Exception as e:
                logger.warning(f"Không thể gửi tin từ chối: {e}")
        return

    # 2. Kiểm tra Idempotency cho update
    if update.update_id:
        conn = get_db_connection(cfg.db_path)
        try:
            is_new = register_update_if_new(conn, update.update_id)
            if not is_new:
                logger.warning(f"Bỏ qua update lặp lại: {update.update_id}")
                return
        finally:
            conn.close()


async def post_process_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Đánh dấu update đã xử lý thành công."""
    if update.update_id:
        cfg = context.bot_data["config"]
        conn = get_db_connection(cfg.db_path)
        try:
            mark_update_processed(conn, update.update_id)
        finally:
            conn.close()


async def inline_search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tra cứu nhanh bằng Inline Query khi gõ @LamQuetVault_bot <từ khóa>."""
    if not update.inline_query:
        return
    query = update.inline_query.query.strip()
    if not query:
        return

    cfg = context.bot_data["config"]
    conn = get_db_connection(cfg.db_path)
    results = []
    try:
        from search import search_records
        from handlers.search_handlers import format_group_detail_message
        from pricing import get_bid_advisory
        res = search_records(conn, query, page=1, page_size=5)
        for idx, g in enumerate(res.groups):
            msg_content = format_group_detail_message(g)
            c = g.records[0].currency if g.records else "JPY"
            adv = get_bid_advisory(g.pricing, c)
            desc_text = f"👉 Nên bid: {adv['max_bid_text']} ({len(g.records)} lần mua)" if adv["has_recommendation"] else f"{len(g.records)} lần mua"

            results.append(
                InlineQueryResultArticle(
                    id=f"grp_{idx}_{g.scope_key[:16]}",
                    title=g.display_title,
                    description=desc_text,
                    input_message_content=InputTextMessageContent(
                        msg_content,
                        parse_mode="HTML",
                    ),
                )
            )
        await update.inline_query.answer(results, cache_time=5)
    except Exception as e:
        logger.error(f"Lỗi inline query: {e}")
    finally:
        conn.close()


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bắt và log ngoại lệ mà không làm crash bot."""
    logger.error(f"Xảy ra lỗi khi xử lý update {update}:", exc_info=context.error)


async def download_image_bytes(url: str, timeout: float = 6.0) -> bytes | None:
    """Tải trực tiếp nội dung ảnh từ Yahoo CDN về RAM với timeout ngắn và headers chống chặn."""
    if not url or not url.startswith("http"):
        return None
    import httpx
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://auctions.yahoo.co.jp/",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200 and resp.content and len(resp.content) > 500:
                return resp.content
    except Exception as e:
        logger.debug(f"Không thể tải ảnh trực tiếp từ {url}: {e}")
    return None


async def post_init(application: Application) -> None:
    """Tự động khởi động các worker chạy nền an toàn (Báo thức đấu giá & Radar tự động)."""
    cfg = application.bot_data.get("config")
    if not cfg:
        return

    import asyncio

    # 1. Vòng lặp kiểm tra báo thức đấu giá định kỳ mỗi 60 giây (bền bỉ, an toàn khi restart)
    async def _alarm_poller_loop():
        import time
        from repository import get_pending_alarms, mark_alarm_sent

        logger.info("Đã kích hoạt vòng lặp Poller giám sát báo thức tàn phiên đấu giá (chu kỳ 60s).")
        while True:
            try:
                now = time.time()
                conn = get_db_connection(cfg.db_path)
                alarms = []
                try:
                    alarms = get_pending_alarms(conn)
                finally:
                    conn.close()

                for a in alarms:
                    alarm_id = a["id"]
                    chat_id = a["chat_id"]
                    trigger_at = a["trigger_at_ts"]
                    if trigger_at <= now:
                        title = a["title"]
                        price = a["price_jpy"]
                        url = a["url"]
                        auc_id = a["auction_id"]
                        price_str = f"{price:,}Y".replace(",", ".") if price else "chưa cập nhật"
                        alert_msg = (
                            f"🚨 <b>Lô hot [{title}] chỉ còn đúng 15 phút nữa hết giờ!</b>\n"
                            f"⚡ Giá hiện tại: <b>{price_str}</b>. Vào snipe ngay kẻo vuột!\n"
                            f"👉 <a href='https://buyee.jp/item/yahoo/auction/{auc_id}?lang=vi'>🛒 Mở Buyee để Snipe</a> | <a href='{url}'>Mở Yahoo</a>"
                        )
                        try:
                            await application.bot.send_message(chat_id=chat_id, text=alert_msg, parse_mode="HTML")
                        except Exception as send_err:
                            logger.warning(f"Không thể gửi báo thức {alarm_id}: {send_err}")

                        c = get_db_connection(cfg.db_path)
                        try:
                            mark_alarm_sent(c, alarm_id)
                        finally:
                            c.close()
            except Exception as loop_err:
                logger.error(f"Lỗi trong vòng lặp báo thức poller: {loop_err}")

            await asyncio.sleep(60)

    asyncio.create_task(_alarm_poller_loop())

    # 2. Khởi động vòng lặp Radar: Quét ngầm, Auto-Alarm 15p Top Lô & Điểm Tin Giờ Vàng (11:30 & 20:30)
    async def _radar_worker_loop():
        await asyncio.sleep(60)  # Đợi bot ổn định 1 phút sau khi khởi động
        from datetime import datetime, timezone, timedelta
        from radar_service import scan_today_lighter_lots, curate_top_radar_lots, format_curated_top_radar_message
        from repository import (
            get_radar_setting,
            set_radar_setting,
            is_lot_seen,
            mark_lot_seen,
            add_auction_alarm,
            has_auction_alarm,
            get_exchange_rate,
        )

        logger.info("Đã kích hoạt vòng lặp Radar: Quét ngầm, Auto-Alarm 15p Top Lô & Điểm Tin Giờ Vàng (chu kỳ 10 phút).")
        while True:
            try:
                target_chat_ids = list(cfg.owner_ids) if getattr(cfg, "owner_ids", None) else ([cfg.owner_id] if cfg.owner_id else [])
                if target_chat_ids:
                    c = get_db_connection(cfg.db_path)
                    try:
                        is_enabled = (get_radar_setting(c, "auto_radar_enabled", default="1") == "1")
                        if is_enabled:
                            now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
                            today_vn = now_vn.strftime("%Y-%m-%d")
                            hour_vn = now_vn.hour
                            min_vn = now_vn.minute
                            rate = get_exchange_rate(c)

                            lots = await scan_today_lighter_lots()

                            # 1. Gửi thông báo tức thì (Realtime Alert) & Đánh dấu lô đã gửi thành công vào SQLite
                            for lot in lots:
                                aid = lot.get("auction_id")
                                if aid and not is_lot_seen(c, aid, today_vn):
                                    price = lot.get("price_jpy", 0)
                                    price_vnd = round(price * rate)
                                    title = lot.get("title", "Lô bật lửa")
                                    bids = lot.get("bids", 0)
                                    remain_str = lot.get("remain_text", "Hôm nay")
                                    lot_tag = lot.get("lot_type_tag", "[LOT BẬT LỬA]")
                                    lot_icon = lot.get("lot_type_icon", "🎯")
                                    y_url = lot.get("url") or f"https://auctions.yahoo.co.jp/jp/auction/{aid}"
                                    buyee_url = f"https://buyee.jp/item/yahoo/auction/{aid}?lang=vi"
                                    photo = lot.get("image_url", "")

                                    # Tải bytes ảnh từ CDN Yahoo để Telegram không bị chặn và để AI Vision soi
                                    photo_bytes = await download_image_bytes(photo) if (photo and photo.startswith("http")) else None

                                    # Pha 3: AI Vision nhận diện cây quẹt giá trị cao qua ảnh
                                    ai_note = ""
                                    if photo_bytes and cfg.gemini_api_key:
                                        try:
                                            ai_res = await inspect_lighter_lot_image(photo_bytes, api_key=cfg.gemini_api_key, timeout=7.0)
                                            if ai_res.get("success"):
                                                if ai_res.get("gem_detected"):
                                                    lot_tag = f"💎 [ĐỒ HIẾM] {lot_tag}"
                                                    lot_icon = "💎"
                                                ai_note = f"\n{ai_res.get('summary_short', '')}\n"
                                        except Exception as ai_err:
                                            logger.debug(f"AI Vision soi lô {aid} bỏ qua do: {ai_err}")

                                    alert_text = (
                                        f"{lot_icon} <b>[YAHOO RADAR] {lot_tag} PHÁT HIỆN LÔ MỚI</b>\n"
                                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                                        f"📦 <b>{title[:100]}</b>\n"
                                        f"💰 Giá sàn: <b>{price:,} yên</b> (~{price_vnd:,} đ) | 🔨 Bids: <b>{bids}</b>\n"
                                        f"⏳ Thời gian: <b>{remain_str}</b>\n"
                                        f"{ai_note}"
                                        f"👉 <a href='{buyee_url}'>🛒 Mở Buyee Đấu Giá</a> | <a href='{y_url}'>Mở Yahoo Auctions</a>\n"
                                        f"🔗 <code>{y_url}</code>\n"
                                        f"📸 Soi ảnh: /img_{aid} | 🤖 AI Soi lại: /soi_{aid} | 💡 Lưu: <code>/data #{aid}</code>"
                                    ).replace(",", ".")

                                    any_sent_ok = False

                                    for owner_chat_id in target_chat_ids:
                                        sent_this = False
                                        if photo_bytes:
                                            try:
                                                await application.bot.send_photo(
                                                    chat_id=owner_chat_id,
                                                    photo=photo_bytes,
                                                    caption=alert_text,
                                                    parse_mode="HTML",
                                                )
                                                sent_this = True
                                                any_sent_ok = True
                                            except Exception as send_photo_err:
                                                logger.warning(f"Lỗi gửi photo bytes lô {aid} tới {owner_chat_id}: {send_photo_err}. Thử fallback send_message...")

                                        # Fallback sang gửi tin text nếu không có ảnh hoặc gửi ảnh lỗi
                                        if not sent_this:
                                            try:
                                                await application.bot.send_message(
                                                    chat_id=owner_chat_id,
                                                    text=alert_text,
                                                    parse_mode="HTML",
                                                    disable_web_page_preview=False,
                                                )
                                                any_sent_ok = True
                                            except Exception as send_msg_err:
                                                logger.warning(f"Lỗi gửi tin text lô {aid} tới {owner_chat_id}: {send_msg_err}")

                                        await asyncio.sleep(1.2)

                                    # Chỉ đánh dấu lô đã thấy khi ít nhất 1 tin nhắn đã được gửi thành công
                                    if any_sent_ok:
                                        mark_lot_seen(
                                            c,
                                            aid,
                                            today_vn,
                                            lot.get("title", ""),
                                            lot.get("price_jpy", 0),
                                            lot.get("bids", 0),
                                            lot.get("end_time", ""),
                                        )

                            # 2. Tự động đặt báo thức ngầm 15 phút cho Top 3 lô hot nhất trong ngày (Auto-Alarm Top Lô)
                            top_alarm_lots = curate_top_radar_lots(lots, max_items=3)
                            now_ts = time.time()
                            for hot_lot in top_alarm_lots:
                                aid = hot_lot.get("auction_id")
                                rem_mins = hot_lot.get("remain_mins", 0)
                                if aid and rem_mins > 15:
                                    for owner_chat_id in target_chat_ids:
                                        if not has_auction_alarm(c, aid, owner_chat_id):
                                            trigger_at = now_ts + (rem_mins - 15) * 60
                                            add_auction_alarm(
                                                conn=c,
                                                auction_id=aid,
                                                chat_id=owner_chat_id,
                                                title=hot_lot.get("title", "Lô bật lửa"),
                                                price_jpy=hot_lot.get("price_jpy", 0),
                                                url=f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                                                end_time_iso=hot_lot.get("end_time", ""),
                                                trigger_at_ts=trigger_at,
                                            )
                                            logger.info(f"Đã tự động đặt báo thức ngầm 15 phút cho lô hot {aid}: {hot_lot.get('title')} (còn {rem_mins}p) tới chat_id={owner_chat_id}")

                            # 3. Chế Độ 'Điểm Tin Giờ Vàng' (Daily Curated Briefing): Đúng 2 khung giờ
                            # Khung 1: 11:30 Trưa (Điểm danh các lô sáng mới lên sàn có bids tốt)
                            is_noon_window = (hour_vn == 11 and min_vn >= 30) or (hour_vn == 12 and min_vn <= 15)
                            noon_key = f"briefing_noon_{today_vn}"
                            if is_noon_window and get_radar_setting(c, noon_key, default="0") != "1":
                                top_picks = curate_top_radar_lots(lots, max_items=4)
                                if top_picks:
                                    header = f"☀️ <b>[ĐIỂM TIN GIỜ VÀNG 11:30] TOP LÔ SÁNG NAY CÓ BIDS TỐT</b>"
                                    digest_msg = format_curated_top_radar_message(
                                        top_picks,
                                        total_scanned=len(lots),
                                        rate=rate,
                                        header_title=header,
                                    )
                                    for owner_chat_id in target_chat_ids:
                                        try:
                                            await application.bot.send_message(
                                                chat_id=owner_chat_id,
                                                text=digest_msg,
                                                parse_mode="HTML",
                                                disable_web_page_preview=True,
                                            )
                                        except Exception as send_err:
                                            logger.warning(f"Lỗi gửi tin nhắn điểm tin trưa tới {owner_chat_id}: {send_err}")
                                    set_radar_setting(c, noon_key, "1")
                                    logger.info(f"Đã gửi Bản tin Giờ Vàng 11:30 ngày {today_vn}.")

                            # Khung 2: 20:30 Tối (Tổng hợp các lô chuẩn bị tàn phiên đêm nay của sàn Nhật: 21h - 23h)
                            is_night_window = (hour_vn == 20 and min_vn >= 30) or (hour_vn == 21 and min_vn <= 15)
                            night_key = f"briefing_night_{today_vn}"
                            if is_night_window and get_radar_setting(c, night_key, default="0") != "1":
                                # Lọc các lô sắp kết thúc đêm nay (còn trong khoảng 30 đến 240 phút)
                                night_lots = [l for l in lots if 0 < l.get("remain_mins", 9999) <= 240]
                                top_night = curate_top_radar_lots(night_lots if night_lots else lots, max_items=4)
                                if top_night:
                                    header = f"🌙 <b>[ĐIỂM TIN GIỜ VÀNG 20:30] CÁC LÔ SẮP TÀN PHIÊN ĐÊM NAY (CHUẨN BỊ SNIPE)</b>"
                                    digest_msg = format_curated_top_radar_message(
                                        top_night,
                                        total_scanned=len(lots),
                                        rate=rate,
                                        header_title=header,
                                    )
                                    for owner_chat_id in target_chat_ids:
                                        try:
                                            await application.bot.send_message(
                                                chat_id=owner_chat_id,
                                                text=digest_msg,
                                                parse_mode="HTML",
                                                disable_web_page_preview=True,
                                            )
                                        except Exception as send_err:
                                            logger.warning(f"Lỗi gửi tin nhắn điểm tin tối tới {owner_chat_id}: {send_err}")
                                    set_radar_setting(c, night_key, "1")
                                    logger.info(f"Đã gửi Bản tin Giờ Vàng 20:30 ngày {today_vn}.")

                    finally:
                        c.close()
            except Exception as loop_err:
                logger.error(f"Lỗi trong vòng lặp Radar worker: {loop_err}", exc_info=True)

            # Quét định kỳ mỗi 10 phút (600 giây) để bắt chuẩn khung giờ và kịp đặt báo thức 15 phút
            await asyncio.sleep(600)

    # Bật worker loop tự động chạy nền với cơ chế chống spam
    asyncio.create_task(_radar_worker_loop())


    # 4. Khởi động vòng lặp tự động dọn dẹp link radar và audit logs cũ quá 3 ngày (chu kỳ 24h)
    async def _auto_clean_worker_loop():
        await asyncio.sleep(300)  # Đợi 5 phút sau khi khởi động bot
        from repository import prune_old_radar_data, vacuum_database

        logger.info("Đã kích hoạt vòng lặp tự động dọn dẹp dữ liệu cũ quá 3 ngày (chu kỳ 24 giờ).")
        while True:
            try:
                c = get_db_connection(cfg.db_path)
                try:
                    res = prune_old_radar_data(c, retention_days=3)
                    if res["total"] > 0:
                        vacuum_database(c)
                        logger.info(
                            f"🧹 Auto-Clean hoàn tất: Đã xóa {res['total']} bản ghi cũ quá 3 ngày "
                            f"(audit_logs={res['audit_logs']}, seen_lots={res['seen_lots']}, "
                            f"alarms={res['alarms']}, updates={res['processed_updates']})."
                        )
                finally:
                    c.close()
            except Exception as clean_err:
                logger.error(f"Lỗi trong vòng lặp auto-clean: {clean_err}")

            # Chạy định kỳ mỗi 24 giờ (86400 giây)
            await asyncio.sleep(86400)

    asyncio.create_task(_auto_clean_worker_loop())

    # Đăng ký danh sách lệnh trực quan vào nút Menu chuẩn của Telegram
    try:
        from telegram import BotCommand
        await application.bot.set_my_commands([
            BotCommand("radar", "🎯 Quét các lô bật lửa có bid hôm nay"),
            BotCommand("radar_img", "🖼️ Lướt album ảnh lô hot hôm nay"),
            BotCommand("radarebay", "🦅 Radar đấu giá eBay kết thúc sáng mai"),
            BotCommand("dashboard", "📱 Mở WebApp Dashboard trực quan"),
            BotCommand("rate", "💴 Xem & đổi tỷ giá JPY/VND"),
            BotCommand("clean", "🧹 Dọn link radar & audit cũ > 3 ngày"),
            BotCommand("menu", "🎛 Bật bảng menu bàn phím bấm nhanh"),
            BotCommand("donlo", "📦 Quản lý dọn lô & phân bổ vốn"),
            BotCommand("recent", "📋 10 bản ghi gần nhất"),
            BotCommand("stats", "📊 Thống kê kho quẹt"),
            BotCommand("help", "❓ Hướng dẫn sử dụng"),
        ])
        logger.info("Đã đăng ký danh sách lệnh nhanh cho Telegram Bot Menu.")
    except Exception as cmd_err:
        logger.warning(f"Không thể cập nhật set_my_commands: {cmd_err}")


async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mở Mini WebApp Dashboard trực quan."""
    import os
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

    port = int(os.environ.get("PORT", 8989))
    webapp_url = os.environ.get("WEBAPP_URL") or os.environ.get("DASHBOARD_URL")
    if not webapp_url:
        webapp_url = f"http://103.166.185.85:{port}/dashboard"

    keyboard = []
    if webapp_url.startswith("https://"):
        keyboard.append([
            InlineKeyboardButton("📱 Mở Bảng Điều Khiển WebApp", web_app=WebAppInfo(url=webapp_url))
        ])
    keyboard.append([
        InlineKeyboardButton("🌐 Mở Trên Trình Duyệt Web", url=webapp_url)
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        "👑 <b>BẢNG ĐIỀU KHIỂN VAULT TRỰC QUAN (WEBAPP DASHBOARD)</b>\n\n"
        "✨ Khám phá toàn bộ dữ liệu kho quẹt & radar qua giao diện luxury đen vàng:\n"
        "• <b>Thẻ hình ảnh (Card Grid)</b>: Chi tiết từng cây Dupont, Dunhill, Zippo...\n"
        "• <b>Thống kê danh mục & Tỷ trọng</b>: Dupont / Dunhill / Zippo trực quan\n"
        "• <b>Live Radar & Đồng hồ đếm ngược</b>: Canh đấu giá theo thời gian thực!\n\n"
        f"🔗 <b>Đường dẫn:</b> <code>{webapp_url}</code>"
    )
    if update.effective_message:
        await update.effective_message.reply_html(msg, reply_markup=reply_markup)


def _start_health_check_server(port: int) -> None:
    """Máy chủ HTTP siêu nhẹ phục vụ Health-Check cho các nền tảng Cloud (Render, Koyeb, Railway)."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import threading

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"LamQuetVault Bot is running healthy 24/7!")

        def log_message(self, format, *args):
            pass  # Im lặng không ghi log rác

    try:
        server = HTTPServer(("0.0.0.0", port), HealthHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        logger.info(f"Health-check server đã khởi động trên cổng {port}.")
    except Exception as e:
        logger.warning(f"Không thể khởi động health-check server trên cổng {port}: {e}")


def main() -> None:
    import os
    config = load_config()

    # Khởi động WebApp Dashboard & Health Check server (hỗ trợ Render, Koyeb, Localhost, VPS)
    port_env = os.environ.get("PORT", "8989")
    try:
        start_dashboard_server(config, int(port_env))
    except Exception as srv_err:
        logger.warning(f"Không thể khởi động WebApp Dashboard server trên cổng {port_env}: {srv_err}")

    if not config.bot_token:
        print("LỖI: Chưa thiết lập TELEGRAM_BOT_TOKEN trong file .env hoặc biến môi trường.", file=sys.stderr)
        sys.exit(1)

    if not config.owner_id:
        print("CẢNH BÁO: Chưa cấu hình TELEGRAM_OWNER_ID. Hãy điền ID của bạn vào .env để sử dụng.", file=sys.stderr)

    # Khởi tạo DB
    init_database(config.db_path)
    logger.info(f"Khởi tạo database tại {config.db_path} thành công.")

    # Khởi tạo Telegram Bot Application với timeout 30s đảm bảo đường truyền ổn định
    client_request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
    )
    rate_limiter = None
    try:
        from telegram.ext import AIORateLimiter
        rate_limiter = AIORateLimiter()
    except Exception as rl_err:
        logger.warning(f"AIORateLimiter chưa sẵn sàng: {rl_err}")

    builder = Application.builder().token(config.bot_token).request(client_request).post_init(post_init)
    if rate_limiter:
        builder = builder.rate_limiter(rate_limiter)
    app = builder.build()
    app.bot_data["config"] = config

    # Đăng ký Security Middleware (Group -1 chạy đầu tiên)
    app.add_handler(TypeHandler(Update, auth_and_idempotency_middleware), group=-1)

    # Đăng ký Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("data", data_command))
    app.add_handler(CommandHandler("find", find_command))
    app.add_handler(CommandHandler("recent", recent_command))
    app.add_handler(CommandHandler("view", view_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("undo", undo_command))
    app.add_handler(CommandHandler("cap", cap_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("donlo", donlo_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler(["radar", "radar_lot"], radar_command))
    app.add_handler(CommandHandler(["radar_img", "album"], radar_img_command))
    app.add_handler(CommandHandler("img", img_detail_command))
    app.add_handler(MessageHandler(filters.Regex(r"^/img_[a-zA-Z0-9]+"), img_detail_command))
    app.add_handler(CommandHandler(["soi", "ai"], ai_inspect_command))
    app.add_handler(MessageHandler(filters.Regex(r"^/soi_[a-zA-Z0-9]+"), ai_inspect_command))
    app.add_handler(CommandHandler("rate", rate_command))
    app.add_handler(CommandHandler(["clean", "prune"], clean_command))
    app.add_handler(CommandHandler("dashboard", dashboard_command))
    app.add_handler(CommandHandler("radarebay", radarebay_command))

    # Đăng ký Callback Handlers
    app.add_handler(CallbackQueryHandler(radar_callback_handler, pattern=r"^radar_"))
    app.add_handler(CallbackQueryHandler(ebay_callback_handler, pattern=r"^ebay_"))
    app.add_handler(CallbackQueryHandler(draft_callback, pattern=r"^box_draft:"))
    app.add_handler(CallbackQueryHandler(price_draft_callback, pattern=r"^(price_draft:|price_cancel:)"))
    app.add_handler(CallbackQueryHandler(quick_add_callback, pattern=r"^quick_add:"))
    app.add_handler(CallbackQueryHandler(search_callback, pattern=r"^(view_grp:|grp_tx:|srch_page:|srch_opt:|quick_win:|quick_calc_data:|matrix:|matrix_price:|quick_win_yahoo:|save_yahoo_lot:|val_fin:|yh_imgs:|yh_alarm:)"))
    app.add_handler(CallbackQueryHandler(cap_callback, pattern=r"^cap_set:"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(record_mgmt_callback))

    # Đăng ký Message Handler cho tra cứu tự nhiên
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_search_handler))

    # Đăng ký Inline Query Handler (HƯỚNG 5)
    app.add_handler(InlineQueryHandler(inline_search_handler))

    # Đăng ký Post-process Middleware (Group 1 chạy sau cùng)
    app.add_handler(TypeHandler(Update, post_process_middleware), group=1)

    # Error handler
    app.add_error_handler(error_handler)

    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    import time
    retry_count = 0
    while True:
        try:
            logger.info("Bot đang khởi động ở chế độ Long Polling...")
            app.run_polling(drop_pending_updates=False)
            break
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bot nhận tín hiệu dừng từ người dùng.")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Lỗi mạng hoặc mất kết nối ({e}). Thử khởi động lại sau 5s (Lần {retry_count})...")
            time.sleep(5)


if __name__ == "__main__":
    main()
