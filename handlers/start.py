"""Handler lệnh /start, /help và menu chính."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

HELP_TEXT = """🔥 <b>TRỢ LÝ SĂN & DỌN QUẸT CHUYÊN SÂU (V4.1)</b>

<b>1. Dán link Yahoo Auctions & Proxy:</b>
• Dán trực tiếp link Yahoo, Buyee, ZenMarket, Doorzo, hoặc mã <code>#f1242609776</code>.
• Bot tự bóc tách: giá sàn, phí ship, đếm số cây trong lô, soi tình trạng đánh lửa, đối chiếu giá chốt quá khứ.
• Phím tắt: <b>[📸 Soi ảnh nét]</b>, <b>[⏰ Nhắc canh tàn phiên]</b>, <b>[🛒 Mở Buyee]</b>.

<b>2. Tra cứu mộc đáy & năm sản xuất:</b>
• <code>zippo 1994</code> hoặc <code>zippo X</code> hoặc <code>mộc đáy IX</code>
• <code>zippo 1974</code> (thời kỳ gạch cổ <code>/// ///</code>)
• <code>zippo solid brass</code>, <code>zippo sterling</code>, <code>mộc đáy dunhill</code>

<b>3. Cẩm nang bắt bệnh & kích thước O-Ring:</b>
• <code>thay ron dunhill rollagas</code> / <code>bệnh dunhill</code>
• <code>bệnh dupont xì gas</code> / <code>thay ron dupont</code>
• <code>kẹt đá zippo</code> / <code>bay xăng zippo</code> / <code>ronson xì gas</code>

<b>4. Radar Săn Lô Bật Lửa (Hôm Nay):</b>
• <code>/radar</code> hoặc <code>/radar_lot</code>: Quét ngay các lô bật lửa có lượt bid kết thúc trong ngày hôm nay trên Yahoo Auctions.

<b>5. Quản lý dọn lô & phân bổ giá vốn:</b>
• <code>/donlo</code>: Xem danh sách các lô quẹt trong kho chờ dọn
• <code>/donlo Q0006 6 8</code>: Cập nhật dọn sống 6 cây, rã xác 8 cây ➔ Tự động tính giá vốn thực/cây sống.

<b>6. Nhập giá & Quản lý kho:</b>
• <code>/data [tên quẹt] [giá Y/VND/$]</code>: Nhập nhanh giá thắng
• <code>/recent</code>: Xem 10 bản ghi gần nhất | <code>/view Q0001</code>: Xem chi tiết
• <code>/cap Q0001 [giá]</code>: Đặt mốc trần bid cá nhân | <code>/undo</code>: Hoàn tác
• <code>/export</code>: Xuất toàn bộ kho ra CSV & JSON | <code>/stats</code>: Thống kê kho
"""


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("➕ Thêm giá", callback_data="menu:add_price"),
            InlineKeyboardButton("🔍 Tra giá", callback_data="menu:search_price"),
        ],
        [
            InlineKeyboardButton("🎯 Radar Lô Hôm Nay", callback_data="radar_refresh"),
            InlineKeyboardButton("📊 Thống kê", callback_data="menu:stats"),
        ],
        [
            InlineKeyboardButton("📋 Đã lưu gần đây", callback_data="menu:recent"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return
    text = (
        "Chào anh Lâm! Đây là bot ghi nhớ giá đấu quẹt riêng của anh.\n\n"
        "Anh có thể nhập một dòng để lưu giá thắng hoặc gõ tên quẹt để tra cứu ngay khi đang đấu."
    )
    await update.effective_message.reply_html(text, reply_markup=get_main_menu_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_message:
        return
    await update.effective_message.reply_html(HELP_TEXT, reply_markup=get_main_menu_keyboard())


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    if data == "menu:add_price":
        await query.message.reply_html(
            "<b>Mẫu thêm giá thắng:</b>\n"
            "<code>/data dupont sơn mài 1 line xanh lá có box 13.400Y</code>\n\n"
            "Anh có thể copy mẫu trên và chỉnh sửa theo đúng cây vừa đấu xong."
        )
    elif data == "menu:search_price":
        await query.message.reply_html(
            "Anh chỉ cần gõ tên quẹt trực tiếp vào ô chat này.\n"
            "Ví dụ: <code>dupont xanh la 1 line son mai</code>"
        )
