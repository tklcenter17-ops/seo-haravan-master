"""Handler cho lệnh /radar và /radar_lot: Quét và hiển thị các lô bật lửa có bid kết thúc hôm nay."""
from __future__ import annotations

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from db import get_db_connection
from radar_service import format_radar_message, scan_today_lighter_lots
from repository import get_radar_setting, set_radar_setting

logger = logging.getLogger(__name__)


def _get_radar_keyboard(is_auto_on: bool) -> InlineKeyboardMarkup:
    """Tạo bàn phím điều khiển cho Radar."""
    toggle_text = "🔔 Tự động: ĐANG BẬT" if is_auto_on else "🔕 Tự động: ĐANG TẮT"
    keyboard = [
        [
            InlineKeyboardButton("🔄 Quét lại ngay", callback_data="radar_refresh"),
            InlineKeyboardButton(toggle_text, callback_data="radar_toggle_auto"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def radar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /radar hoặc /radar_lot: Quét ngay các lô bật lửa có bid kết thúc trong ngày hôm nay."""
    msg = update.effective_message
    if not msg:
        return

    wait_msg = await msg.reply_text("🔍 <i>Radar đang quét Yahoo Auctions tìm các lô bật lửa có lượt bid kết thúc hôm nay... Chờ em 3-5 giây!</i>", parse_mode="HTML")

    try:
        lots = await scan_today_lighter_lots()
        formatted_text = format_radar_message(lots)

        cfg = context.bot_data.get("config")
        is_auto_on = True
        if cfg:
            conn = get_db_connection(cfg.db_path)
            try:
                val = get_radar_setting(conn, "auto_radar_enabled", default="1")
                is_auto_on = (val == "1")
            finally:
                conn.close()

        keyboard = _get_radar_keyboard(is_auto_on)
        await wait_msg.edit_text(formatted_text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Lỗi khi thực thi lệnh /radar: {e}", exc_info=True)
        await wait_msg.edit_text(f"⚠️ <i>Có lỗi xảy ra khi quét Yahoo Auctions: {e}</i>", parse_mode="HTML")


async def radar_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm inline của Radar (quét lại, bật/tắt tự động)."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    await query.answer()

    cfg = context.bot_data.get("config")
    if not cfg:
        return

    if data == "radar_refresh":
        try:
            await query.edit_message_text("🔄 <i>Đang làm mới dữ liệu lô từ Yahoo Auctions...</i>", parse_mode="HTML")
            lots = await scan_today_lighter_lots()
            formatted_text = format_radar_message(lots)

            conn = get_db_connection(cfg.db_path)
            try:
                val = get_radar_setting(conn, "auto_radar_enabled", default="1")
                is_auto_on = (val == "1")
            finally:
                conn.close()

            keyboard = _get_radar_keyboard(is_auto_on)
            await query.edit_message_text(formatted_text, parse_mode="HTML", reply_markup=keyboard, disable_web_page_preview=True)
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
        keyboard = _get_radar_keyboard(is_auto_on)
        try:
            await query.edit_message_reply_markup(reply_markup=keyboard)
        except Exception:
            pass
