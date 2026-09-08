"""Module Radar chuyên biệt: Quét và lọc các lô bật lửa (Lots) có lượt bid kết thúc hôm nay trên Yahoo Auctions."""
from __future__ import annotations

import json
import logging
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Regex nhận diện dấu hiệu bán theo lô / nhiều cây trong tiếng Nhật
_LOT_KEYWORDS_RE = re.compile(
    r"(まとめ(?:売り)?|大量|セット|アソート|ジャンク|\d+\s*(?:点|本|個|台)|詰め合わせ|詰合せ)",
    re.IGNORECASE,
)

# Regex loại trừ nếu chỉ là 1 cây đơn chiếc hoặc phụ kiện dụng cụ không phải bật lửa
_SINGLE_ITEM_EXCLUDE_RE = re.compile(r"(\b1点のみ\b|単品|単体|1本のみ|熱収縮チューブ|ハンダ|配線修理|ガスボンベ|フリントのみ|替え芯のみ)", re.IGNORECASE)

# Bắt buộc phải có từ khóa liên quan đến bật lửa / thương hiệu bật lửa
_LIGHTER_KEYWORD_RE = re.compile(r"(ライター|zippo|ジッポ|dupont|デュポン|dunhill|ダンヒル|cartier|カルティエ|ronson|ロンソン|喫煙具|オイル|ガス)", re.IGNORECASE)

# Các từ khóa tìm kiếm lô bật lửa đa dạng trên Yahoo Auctions Nhật
LOT_SEARCH_QUERIES = [
    "ライター まとめ",
    "ライター 大量",
    "ライター セット",
    "ライター ジャンク",
    "ジッポ まとめ",
    "デュポン まとめ",
    "ダンヒル まとめ",
]


def is_lot_title(title: str) -> bool:
    """Kiểm tra xem tiêu đề có phải là lô/nhiều cây bật lửa hay không."""
    if not title:
        return False
    title_clean = title.strip()
    
    # 1. Loại trừ phụ kiện dây hàn, đồ nghề sửa chữa hoặc ghi rõ 1 cây
    if _SINGLE_ITEM_EXCLUDE_RE.search(title_clean):
        return False

    # 2. Bắt buộc phải có chữ liên quan đến bật lửa hoặc nhãn hiệu bật lửa
    if not _LIGHTER_KEYWORD_RE.search(title_clean):
        return False

    # 3. Phải có dấu hiệu bán theo lô
    return bool(_LOT_KEYWORDS_RE.search(title_clean))


def is_ending_today(endtime_str: str, now_utc: datetime | None = None) -> tuple[bool, str, int]:
    """Kiểm tra xem thời điểm kết thúc có nằm trong ngày HÔM NAY (theo giờ Nhật JST UTC+9 hoặc VN UTC+7) không.
    
    Trả về: (is_today, formatted_remaining, remaining_minutes)
    """
    if not endtime_str:
        return False, "", -1

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    # Giờ Nhật Bản JST (UTC+9)
    jst = timezone(timedelta(hours=9))
    now_jst = now_utc.astimezone(jst)
    today_jst = now_jst.date()

    # Parse endtime từ format Yahoo: "YYYY-MM-DD HH:MM:SS" hoặc "YYYY/MM/DD HH:MM:SS"
    clean_str = endtime_str.strip().replace("/", "-")
    # Cắt bỏ phần miligiây nếu có
    clean_str = clean_str.split(".")[0]

    end_dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            naive_dt = datetime.strptime(clean_str, fmt)
            # Yahoo endtime mặc định là giờ Nhật Bản (JST)
            end_dt = naive_dt.replace(tzinfo=jst)
            break
        except ValueError:
            continue

    if not end_dt:
        return False, "", -1

    # Kiểm tra điều kiện:
    # 1. Chưa kết thúc (end_dt > now_jst)
    # 2. Kết thúc trong cùng ngày hôm nay (end_dt.date() == today_jst)
    if end_dt <= now_jst:
        return False, "Đã hết giờ", -1

    if end_dt.date() != today_jst:
        return False, f"Ngày mai ({end_dt.strftime('%d/%m')})", -1

    remaining_delta = end_dt - now_jst
    total_mins = int(remaining_delta.total_seconds() // 60)
    hours = total_mins // 60
    mins = total_mins % 60

    if hours > 0:
        remain_text = f"còn {hours}h{mins:02d}m"
    else:
        remain_text = f"còn {mins} phút"

    return True, remain_text, total_mins


async def fetch_yahoo_search_items(query: str, limit: int = 50) -> list[dict[str, Any]]:
    """Gửi request tìm kiếm trên Yahoo Auctions và trích xuất danh sách sản phẩm.
    
    Sắp xếp theo s1=end&o1=a (sắp kết thúc sớm nhất lên đầu) để tối ưu việc tìm kèo kết thúc hôm nay.
    """
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_q}&va={encoded_q}&exflg=1&b=1&n={limit}&s1=end&o1=a"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    items: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Yahoo search error {resp.status_code} for query: {query}")
                return []

            html = resp.text
            # 1. Thử bóc tách qua pageData
            m = re.search(r"var pageData\s*=\s*(\{.*?\});\s*(?:var|</script>)", html, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    raw_items = data.get("items", [])
                    for it in raw_items:
                        aid = str(it.get("productID") or it.get("auctionID") or it.get("id") or "").strip()
                        title = str(it.get("productName") or it.get("title") or "").strip()
                        price = int(it.get("price") or 0)
                        bids = int(it.get("bids") or 0)
                        endtime = str(it.get("endtime") or "").strip()

                        if aid and title:
                            items.append({
                                "auction_id": aid,
                                "title": title,
                                "price_jpy": price,
                                "bids": bids,
                                "end_time": endtime,
                                "url": f"https://page.auctions.yahoo.co.jp/jp/auction/{aid}",
                            })
                except Exception as ex:
                    logger.warning(f"Error parsing pageData JSON for {query}: {ex}")

            # 2. Fallback regex nếu pageData rỗng
            if not items:
                matches = re.findall(
                    r'https?://(?:page\.)?auctions\.yahoo\.co\.jp/jp/auction/([a-zA-Z0-9]+)',
                    html,
                )
                seen = set()
                for aid in matches:
                    if aid not in seen:
                        seen.add(aid)
                        items.append({
                            "auction_id": aid,
                            "title": f"Lô bật lửa Yahoo #{aid}",
                            "price_jpy": 0,
                            "bids": 1,
                            "end_time": "",
                            "url": f"https://page.auctions.yahoo.co.jp/jp/auction/{aid}",
                        })
    except Exception as e:
        logger.error(f"Failed to fetch Yahoo search for {query}: {e}")

    return items


async def scan_today_lighter_lots(queries: list[str] | None = None) -> list[dict[str, Any]]:
    """Quét toàn bộ Yahoo Auctions với các từ khóa lô, áp dụng bộ lọc:
    
    1. is_lot_title(title) == True (Bán theo lô nhiều cây)
    2. bids > 0 (Có ít nhất 1 lượt bid)
    3. is_ending_today(endtime) == True (Kết thúc trong ngày hôm nay)
    """
    if queries is None:
        queries = LOT_SEARCH_QUERIES

    now_utc = datetime.now(timezone.utc)
    all_matched: dict[str, dict[str, Any]] = {}

    for q in queries:
        try:
            raw_items = await fetch_yahoo_search_items(q, limit=50)
            for it in raw_items:
                aid = it["auction_id"]
                if aid in all_matched:
                    continue

                title = it.get("title", "")
                bids = it.get("bids", 0)
                endtime = it.get("end_time", "")

                # Bộ lọc 1: Bắt buộc là Lot (Nhiều cây)
                if not is_lot_title(title):
                    continue

                # Bộ lọc 2: Bắt buộc phải có lượt Bid (đang có người tranh đấu)
                if bids <= 0:
                    continue

                # Bộ lọc 3: Bắt buộc kết thúc trong ngày hôm nay
                is_today, remain_str, remain_mins = is_ending_today(endtime, now_utc=now_utc)
                if not is_today:
                    continue

                it["remain_text"] = remain_str
                it["remain_mins"] = remain_mins
                all_matched[aid] = it
        except Exception as err:
            logger.warning(f"Error scanning query '{q}': {err}")

    # Sắp xếp kết quả: Phiên sắp hết giờ nhất lên đầu (remain_mins tăng dần)
    sorted_lots = sorted(all_matched.values(), key=lambda x: x.get("remain_mins", 999999))
    return sorted_lots


def format_radar_message(lots: list[dict[str, Any]], max_items: int = 15) -> str:
    """Định dạng danh sách các lô bật lửa thành tin nhắn Telegram HTML trực quan, hấp dẫn."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y")

    if not lots:
        return (
            f"🎯 <b>RADAR LÔ BẬT LỬA (HÔM NAY {date_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện tại chưa có lô bật lửa nào có bid kết thúc trong ngày hôm nay hoặc các phiên đã tàn hết.\n"
            f"Radar sẽ tiếp tục quét ngầm và thông báo ngay khi có lô mới xuất hiện!</i>"
        )

    lines = [
        f"🎯 <b>RADAR BẬT LỬA THEO LÔ (KẾT THÚC HÔM NAY {date_str})</b>",
        f"🔥 <i>Đã lọc: <b>Bán theo lô nhiều cây</b> + <b>Đang có lượt Bid</b></i>",
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    rate = 165  # Tỷ giá tạm tính Yên sang VNĐ
    display_lots = lots[:max_items]

    for idx, it in enumerate(display_lots, 1):
        title = it.get("title", "Lô bật lửa")
        # Rút gọn tiêu đề nếu quá dài để hiển thị thoáng mắt
        if len(title) > 65:
            title = title[:62] + "..."
        
        price = it.get("price_jpy", 0)
        price_vnd = round(price * rate)
        bids = it.get("bids", 0)
        remain = it.get("remain_text", "Hôm nay")
        aid = it.get("auction_id", "")
        y_url = it.get("url", f"https://page.auctions.yahoo.co.jp/jp/auction/{aid}")
        buyee_url = f"https://buyee.jp/item/yahoo/auction/{aid}?lang=vi"

        price_str = f"{price:,} yên (~{price_vnd:,} đ)".replace(",", ".")

        block = (
            f"<b>{idx}. {title}</b>\n"
            f"💰 <b>Giá hiện tại:</b> {price_str} | 🔨 <b>Bids:</b> {bids}\n"
            f"⏳ <b>Thời gian:</b> {remain}\n"
            f"👉 <a href='{y_url}'>Xem trên Yahoo</a> | <a href='{buyee_url}'>Xem qua Buyee</a>\n"
            f"👉 <i>Phân tích:</i> <code>/data {y_url}</code>"
        )
        lines.append(block)
        lines.append("─────────────────────")

    if len(lots) > max_items:
        lines.append(f"<i>... và còn {len(lots) - max_items} lô khác đang kết thúc hôm nay.</i>")

    lines.append("\n💡 <i>Gõ <code>/radar</code> để quét cập nhật giá mới nhất bất kỳ lúc nào!</i>")
    return "\n".join(lines)
