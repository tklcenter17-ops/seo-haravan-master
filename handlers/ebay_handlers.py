"""Handler cho lệnh /radarebay: Radar săn đấu giá bật lửa trên eBay sắp tàn phiên."""
from __future__ import annotations

import logging
from typing import Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from ebay_service import fetch_ebay_auctions, format_ebay_message

logger = logging.getLogger(__name__)

# Cache kết quả eBay gần nhất phục vụ lật trang và đổi tab tức thì
_EBAY_CACHE: dict[str, Any] = {
    "items": [],
    "keyword": "lighters",
}


def _get_ebay_page_keyboard(current_page: int, total_pages: int, keyword: str) -> InlineKeyboardMarkup:
    """Tạo bàn phím điều khiển và phân trang cho eBay Radar."""
    keyboard = []

    # Hàng 1: Nút điều hướng phân trang nếu có nhiều trang
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ Trước", callback_data=f"ebay_page:{current_page - 1}"))
    nav_buttons.append(InlineKeyboardButton(f"Trang {current_page}/{total_pages}", callback_data="ebay_noop"))
    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Sau ▶️", callback_data=f"ebay_page:{current_page + 1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Hàng 2: Nút lọc nhanh theo thương hiệu
    keyboard.append([
        InlineKeyboardButton("🔥 Tất Cả", callback_data="ebay_brand:all"),
        InlineKeyboardButton("✨ Dupont", callback_data="ebay_brand:dupont"),
        InlineKeyboardButton("🎩 Dunhill", callback_data="ebay_brand:dunhill"),
        InlineKeyboardButton("⚡ Zippo", callback_data="ebay_brand:zippo"),
    ])

    # Hàng 3: Làm mới
    keyboard.append([
        InlineKeyboardButton(f"🔄 Quét lại ({keyword.upper()})", callback_data=f"ebay_refresh:{keyword}"),
    ])

    return InlineKeyboardMarkup(keyboard)


async def radarebay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /radarebay [từ khóa]:
    
    Ví dụ:
    • /radarebay: Quét toàn bộ bật lửa có bids sắp kết thúc
    • /radarebay dupont: Quét Dupont
    • /radarebay dunhill: Quét Dunhill
    • /radarebay zippo: Quét Zippo
    """
    msg = update.effective_message
    if not msg:
        return

    args = context.args or []
    raw_kw = " ".join(args).strip() if args else "all"
    keyword = raw_kw.lower()

    try:
        await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
    except Exception:
        pass

    wait_msg = await msg.reply_html(
        f"🦅 <b>Đang quét sàn đấu giá eBay cho: <code>{keyword.upper()}</code>...</b>\n"
        f"<i>Đang lọc các cây có ít nhất 1 bid kết thúc trước 11:00 AM mai, anh chờ em xíu nhé!</i>"
    )

    try:
        items = await fetch_ebay_auctions(keyword=keyword, limit=100, min_bids=1)
        _EBAY_CACHE["items"] = items
        _EBAY_CACHE["keyword"] = keyword

        formatted_text, total_pages = format_ebay_message(
            items, page=1, per_page=6, keyword=keyword
        )
        keyboard = _get_ebay_page_keyboard(1, total_pages, keyword)

        await wait_msg.edit_text(
            formatted_text,
            parse_mode="HTML",
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Lỗi khi thực thi /radarebay: {e}", exc_info=True)
        await wait_msg.edit_text(f"⚠️ <i>Lỗi khi quét eBay: {e}</i>", parse_mode="HTML")


async def ebay_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm inline của eBay Radar: lật trang, đổi brand, làm mới."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    await query.answer()

    if data == "ebay_noop":
        return

    curr_items = _EBAY_CACHE.get("items") or []
    curr_kw = _EBAY_CACHE.get("keyword", "all")

    if data.startswith("ebay_page:"):
        page_num = int(data.split(":")[1])
        formatted_text, total_pages = format_ebay_message(
            curr_items, page=page_num, per_page=6, keyword=curr_kw
        )
        keyboard = _get_ebay_page_keyboard(page_num, total_pages, curr_kw)
        try:
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    elif data.startswith("ebay_brand:"):
        brand = data.split(":")[1].strip()
        try:
            await query.edit_message_text(f"🦅 <i>Đang quét eBay cho {brand.upper()}...</i>", parse_mode="HTML")
            items = await fetch_ebay_auctions(keyword=brand, limit=100, min_bids=1)
            _EBAY_CACHE["items"] = items
            _EBAY_CACHE["keyword"] = brand

            formatted_text, total_pages = format_ebay_message(
                items, page=1, per_page=6, keyword=brand
            )
            keyboard = _get_ebay_page_keyboard(1, total_pages, brand)
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Lỗi đổi brand eBay: {e}")
            await query.edit_message_text(f"⚠️ <i>Lỗi: {e}</i>", parse_mode="HTML")

    elif data.startswith("ebay_refresh:"):
        kw = data.split(":")[1].strip() if ":" in data else curr_kw
        try:
            await query.edit_message_text(f"🔄 <i>Đang làm mới eBay ({kw.upper()})...</i>", parse_mode="HTML")
            items = await fetch_ebay_auctions(keyword=kw, limit=100, min_bids=1)
            _EBAY_CACHE["items"] = items
            _EBAY_CACHE["keyword"] = kw

            formatted_text, total_pages = format_ebay_message(
                items, page=1, per_page=6, keyword=kw
            )
            keyboard = _get_ebay_page_keyboard(1, total_pages, kw)
            await query.edit_message_text(
                formatted_text,
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Lỗi làm mới eBay: {e}")
            await query.edit_message_text(f"⚠️ <i>Lỗi: {e}</i>", parse_mode="HTML")
