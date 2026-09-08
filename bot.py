"""Entry point chính khởi chạy Telegram Bot với Long Polling và Middleware bảo mật."""
from __future__ import annotations

import logging
import sys
from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import (
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
from db import get_db_connection, init_database
from handlers.admin import cancel_command, export_command, stats_command
from handlers.caps import cap_callback, cap_command
from handlers.data_entry import data_command, draft_callback, price_draft_callback
from handlers.record_mgmt import (
    delete_command,
    donlo_command,
    recent_command,
    record_mgmt_callback,
    undo_command,
    view_command,
)
from handlers.search_handlers import find_command, quick_add_callback, search_callback, text_search_handler
from handlers.start import help_command, menu_callback, start_command
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

    # Nếu chưa thiết lập owner_id (owner_id == 0), tự động khoá với tài khoản đầu tiên kích hoạt
    if cfg.owner_id == 0 and user:
        save_owner_id_to_env(user.id)
        context.bot_data["config"] = AppConfig(
            bot_token=cfg.bot_token,
            owner_id=user.id,
            db_path=cfg.db_path,
            backup_dir=cfg.backup_dir,
            price_high_threshold_jpy=cfg.price_high_threshold_jpy,
        )
        logger.info(f"Đã tự động xác thực và khoá TELEGRAM_OWNER_ID = {user.id}")
        if update.effective_message:
            await update.effective_message.reply_html(
                f"🔐 <b>Kích hoạt bảo mật thành công!</b>\n"
                f"Tài khoản của anh (ID: <code>{user.id}</code>) đã được khoá làm Chủ sở hữu (Owner) duy nhất của bot."
            )

    # 1. Kiểm tra quyền sở hữu
    if not user or user.id != context.bot_data["config"].owner_id:
        if update.effective_message:
            await update.effective_message.reply_text("⛔ Bạn không có quyền truy cập bot này.")
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


async def post_init(application: Application) -> None:
    """Tự động khôi phục các báo thức hẹn giờ canh tàn phiên khi bot khởi động lại."""
    cfg = application.bot_data.get("config")
    if not cfg:
        return
    conn = get_db_connection(cfg.db_path)
    try:
        from repository import get_pending_alarms, mark_alarm_sent
        alarms = get_pending_alarms(conn)
        if not alarms:
            return

        import asyncio
        import time
        now = time.time()
        logger.info(f"Phát hiện {len(alarms)} báo thức phiên đấu cần phục hồi...")

        db_path = cfg.db_path

        def _safe_mark_sent(aid: int) -> None:
            c = get_db_connection(db_path)
            try:
                mark_alarm_sent(c, aid)
            except Exception:
                pass
            finally:
                c.close()

        for a in alarms:
            alarm_id = a["id"]
            chat_id = a["chat_id"]
            title = a["title"]
            price = a["price_jpy"]
            url = a["url"]
            auc_id = a["auction_id"]
            trigger_at = a["trigger_at_ts"]
            wait_secs = trigger_at - now

            p_text = f" (Giá hiện tại: {price:,} yên)".replace(",", ".") if price else ""
            alert_msg = (
                f"🚨 <b>BÁO ĐỘNG TÀN PHIÊN (CÒN 15 PHÚT NỮA HẾT GIỜ)!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 Cây: <b>{title}</b>\n"
                f"⚡ {p_text}\n"
                f"👉 <a href='{url}'>Mở Yahoo</a> | <a href='https://buyee.jp/item/yahoo/auction/{auc_id}?lang=vi'>Mở Buyee để Snipe</a>\n\n"
                f"<i>Vào đặt bid ngay kẻo vuột cây ngon anh nhé!</i>"
            )

            if wait_secs <= 0:
                async def _send_past(cid=chat_id, aid=alarm_id, msg=alert_msg):
                    try:
                        await application.bot.send_message(chat_id=cid, text=msg, parse_mode="HTML")
                    except Exception:
                        pass
                    _safe_mark_sent(aid)

                asyncio.create_task(_send_past())
            else:
                async def _send_future(delay=wait_secs, cid=chat_id, aid=alarm_id, msg=alert_msg):
                    await asyncio.sleep(delay)
                    try:
                        await application.bot.send_message(chat_id=cid, text=msg, parse_mode="HTML")
                    except Exception:
                        pass
                    _safe_mark_sent(aid)

                asyncio.create_task(_send_future())
    finally:
        conn.close()


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

    # Nếu chạy trên Cloud (Render, Koyeb...) có biến PORT thì mở health check endpoint
    port_env = os.environ.get("PORT")
    if port_env:
        try:
            _start_health_check_server(int(port_env))
        except ValueError:
            pass

    if not config.bot_token:
        print("LỖI: Chưa thiết lập TELEGRAM_BOT_TOKEN trong file .env hoặc biến môi trường.", file=sys.stderr)
        sys.exit(1)

    if not config.owner_id:
        print("CẢNH BÁO: Chưa cấu hình TELEGRAM_OWNER_ID. Hãy điền ID của bạn vào .env để sử dụng.", file=sys.stderr)

    # Khởi tạo DB
    init_database(config.db_path)
    logger.info(f"Khởi tạo database tại {config.db_path} thành công.")

    # Khởi tạo Telegram Bot Application
    app = Application.builder().token(config.bot_token).post_init(post_init).build()
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

    # Đăng ký Callback Handlers
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
