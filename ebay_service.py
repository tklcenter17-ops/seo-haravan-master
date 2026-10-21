"""Module tích hợp eBay: Quét các phiên đấu giá (Auction) sắp kết thúc có bids."""
from __future__ import annotations

import asyncio
import logging
import re
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Bộ đệm kết quả cào eBay tạm thời (TTL 10 phút) tránh bị chặn bot
_EBAY_QUERY_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
EBAY_CACHE_TTL_SECS = 600

EBAY_BRAND_KEYWORDS: dict[str, str] = {
    "all": "(lighter,lighters)",
    "lighter": "(lighter,lighters)",
    "lighters": "(lighter,lighters)",
    "dupont": "(dupont lighter,dupont lighters,st dupont)",
    "dunhill": "(dunhill lighter,dunhill lighters,alfred dunhill)",
    "zippo": "(zippo lighter,zippo lighters,vintage zippo)",
    "lot": "(lighters lot,lighter lot,mixed lighters)",
    "cartier": "(cartier lighter,cartier lighters)",
    "ronson": "(ronson lighter,ronson lighters)",
}

DEFAULT_USD_RATE = 25500


def parse_ebay_price_and_vnd(price_str: str, usd_rate: int = DEFAULT_USD_RATE) -> tuple[str, str]:
    """Phân tích chuỗi giá từ eBay và quy đổi sang VND."""
    clean_p = price_str.replace(",", "").strip()
    # Trường hợp eBay hiển thị tiền VND trực tiếp: 845935.16 VND
    m_vnd = re.search(r"([\d.]+)\s*VND", clean_p, re.IGNORECASE)
    if m_vnd:
        try:
            val_vnd = round(float(m_vnd.group(1)))
            val_usd = round(val_vnd / usd_rate, 1)
            return f"${val_usd}", f"{val_vnd:,}".replace(",", ".")
        except ValueError:
            pass

    # Trường hợp tiền USD: $25.00 hoặc USD 35.50
    m_usd = re.search(r"(?:USD|\$)\s*([\d.]+)", clean_p, re.IGNORECASE)
    if m_usd:
        try:
            val_usd = float(m_usd.group(1))
            val_vnd = round(val_usd * usd_rate)
            return f"${val_usd:,.2f}", f"{val_vnd:,}".replace(",", ".")
        except ValueError:
            pass

    return price_str or "Xem sàn", ""


def is_ending_before_tomorrow_noon(time_text: str) -> bool:
    """Kiểm tra phiên có kết thúc trước 11:00 AM ngày mai (trong vòng ~24-26 giờ) không."""
    t_lower = time_text.lower()
    # Nếu còn >= 2 ngày (vd: 2d left, 3d 4h left) -> Không thuộc diện tàn phiên trước 11h mai
    m_days = re.search(r"(\d+)\s*d", t_lower)
    if m_days and int(m_days.group(1)) >= 2:
        return False
    if m_days and int(m_days.group(1)) == 1:
        # 1d ...: kiểm tra số giờ, nếu quá 6h thì vượt 30h
        m_hours = re.search(r"1\s*d\s*(\d+)\s*h", t_lower)
        if m_hours and int(m_hours.group(1)) > 6:
            return False

    return True


def _scrape_ebay_sync(
    keyword: str = "lighters",
    limit: int = 100,
    min_bids: int = 1,
    max_pages: int = 6,
) -> list[dict[str, Any]]:
    """Cào danh sách đấu giá sắp kết thúc từ eBay có phân trang (chạy đồng bộ trong thread)."""
    import time
    clean_kw = keyword.strip().lower()
    search_query = EBAY_BRAND_KEYWORDS.get(clean_kw)
    if not search_query:
        if clean_kw in ("lighter", "lighters", "all"):
            search_query = "(lighter,lighters)"
        else:
            search_query = clean_kw
    encoded_kw = urllib.parse.quote_plus(search_query)

    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    consecutive_expired_count = 0

    try:
        from curl_cffi import requests
        session = requests.Session(impersonate="chrome124")

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }

        # Khởi tạo session với eBay
        try:
            session.get("https://www.ebay.com/", headers=headers, timeout=10)
        except Exception:
            pass

        headers["Sec-Fetch-Site"] = "same-origin"
        headers["Referer"] = "https://www.ebay.com/"

        # Duyệt qua các trang kết quả (Pagination Loop)
        for page in range(1, max_pages + 1):
            search_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_kw}&LH_Auction=1&_sop=1&_pgn={page}"
            try:
                resp = session.get(search_url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    logger.warning(f"eBay search p{page} status {resp.status_code}")
                    break

                html_lower = resp.text.lower()
                if "pardon our interruption" in html_lower or "distil_identification" in html_lower:
                    logger.warning(f"eBay anti-bot triggered on p{page}, retrying once...")
                    time.sleep(1.5)
                    resp = session.get(search_url, headers=headers, timeout=15)
                    if "pardon our interruption" in resp.text.lower():
                        logger.warning(f"eBay anti-bot active on p{page}, stopping pagination.")
                        break

                soup = BeautifulSoup(resp.text, "html.parser")
                containers = soup.select("ul.srp-results > li")
                if not containers:
                    containers = soup.select(".s-item, .s-card")

                if not containers:
                    break

                for c in containers:
                    # 1. Tìm Link & ID
                    link_el = c.select_one("a[href*='/itm/']")
                    if not link_el or "href" not in link_el.attrs:
                        continue
                    raw_url = link_el["href"]
                    clean_url = raw_url.split("?")[0]
                    m_id = re.search(r"/itm/(\d+)", clean_url)
                    if not m_id:
                        continue
                    item_id = m_id.group(1)
                    if item_id in seen_ids:
                        continue

                    # 2. Tìm Title
                    title = ""
                    title_el = c.select_one(".s-card__title, .s-item__title")
                    if title_el:
                        title = title_el.get_text(strip=True)
                    if not title:
                        spans = [s.get_text(strip=True) for s in c.select("span") if s.get_text(strip=True)]
                        for s_txt in spans:
                            if len(s_txt) > 10 and not any(skip in s_txt.lower() for skip in ["shop on ebay", "find more", "new listing", "opens in a new"]):
                                title = s_txt
                                break
                    if not title:
                        title = link_el.get_text(strip=True)
                    if not title or "Shop on eBay" in title:
                        continue

                    # 3. Tìm Bids (Bắt buộc >= min_bids)
                    c_text = c.get_text(" ", strip=True)
                    m_bids = re.search(r"(\d+)\s*bids?", c_text, re.IGNORECASE)
                    if not m_bids:
                        continue
                    bids_cnt = int(m_bids.group(1))
                    if bids_cnt < min_bids:
                        continue

                    # 4. Tìm Thời gian còn lại
                    time_left = ""
                    m_time = re.search(r"((?:\d+\s*[dhm]\s*)+left(?:\([^)]+\))?)", c_text, re.IGNORECASE)
                    if m_time:
                        time_left = m_time.group(1)
                    else:
                        m_ends = re.search(r"Ends\s+(?:in\s+)?((?:\d+\s*[dhm]\s*)+)", c_text, re.IGNORECASE)
                        if m_ends:
                            time_left = m_ends.group(1).strip() + " left"
                        else:
                            for s in c.select("span"):
                                s_txt = s.get_text(strip=True)
                                if "left" in s_txt.lower() or "today" in s_txt.lower() or "tomorrow" in s_txt.lower():
                                    time_left = s_txt
                                    break
                    if not time_left:
                        time_left = "Sắp tàn phiên"

                    # Lọc khung giờ: kết thúc trước 11h sáng mai
                    if not is_ending_before_tomorrow_noon(time_left):
                        m_days = re.search(r"(\d+)\s*d", time_left.lower())
                        if m_days and int(m_days.group(1)) >= 2:
                            consecutive_expired_count += 1
                        continue

                    consecutive_expired_count = 0

                    # 5. Tìm Giá
                    price_el = c.select_one(".s-card__price, .s-item__price")
                    price_str = price_el.get_text(strip=True) if price_el else ""
                    if not price_str:
                        for s in c.select("span"):
                            s_txt = s.get_text(strip=True)
                            if "$" in s_txt or "VND" in s_txt or "USD" in s_txt:
                                price_str = s_txt
                                break

                    # 6. Ảnh thumbnail
                    img_el = c.select_one("img")
                    photo_url = img_el.get("src") or img_el.get("data-src") or "" if img_el else ""

                    seen_ids.add(item_id)
                    items.append({
                        "id": item_id,
                        "title": title,
                        "price_raw": price_str,
                        "bids": bids_cnt,
                        "time_left": time_left,
                        "url": clean_url,
                        "photo_url": photo_url,
                    })

                    if len(items) >= limit:
                        break

                if consecutive_expired_count >= 8:
                    break

                if len(items) >= limit:
                    break

                time.sleep(0.3)

            except Exception as page_err:
                logger.warning(f"Lỗi khi cào eBay page {page}: {page_err}")
                break

    except Exception as e:
        logger.error(f"Lỗi khi cào eBay auctions ('{search_query}'): {e}", exc_info=True)

    return items


async def fetch_ebay_auctions(
    keyword: str = "lighters",
    limit: int = 100,
    min_bids: int = 1,
    max_pages: int = 6,
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """Tìm kiếm các phiên đấu giá eBay có bid kết thúc trước 11h sáng mai (Async wrapper có TTL cache)."""
    clean_k = keyword.strip().lower()
    now = time.time()

    if not force_refresh and clean_k in _EBAY_QUERY_CACHE:
        cached_ts, cached_items = _EBAY_QUERY_CACHE[clean_k]
        if (now - cached_ts) < EBAY_CACHE_TTL_SECS:
            logger.info(f"⚡ Trả về {len(cached_items)} kết quả eBay ('{clean_k}') từ bộ đệm.")
            return cached_items

    items = await asyncio.to_thread(_scrape_ebay_sync, keyword, limit, min_bids, max_pages)
    if items:
        _EBAY_QUERY_CACHE[clean_k] = (now, items)
    return items


def format_single_ebay_block(idx: int, it: dict[str, Any], usd_rate: int = DEFAULT_USD_RATE) -> str:
    """Định dạng 1 phiên đấu giá eBay."""
    title = it.get("title", "Bật lửa eBay")
    if len(title) > 65:
        title = title[:62] + "..."

    price_raw = it.get("price_raw", "")
    price_usd, price_vnd = parse_ebay_price_and_vnd(price_raw, usd_rate=usd_rate)
    bids = it.get("bids", 0)
    time_left = it.get("time_left", "Sắp kết thúc")
    url = it.get("url", "https://www.ebay.com")

    vnd_part = f" (~{price_vnd} đ)" if price_vnd else ""

    return (
        f"<b>{idx}. {title}</b>\n"
        f"⚡ <b>Giá sàn:</b> <b>{price_usd}</b>{vnd_part} | 🔨 <b>{bids} bids</b>\n"
        f"⏳ <b>Hạn:</b> <b>{time_left}</b>\n"
        f"👉 <a href='{url}'>🛒 Bấm Mở Đấu Giá Trên eBay</a>"
    )


def format_ebay_message(
    items: list[dict[str, Any]],
    page: int = 1,
    per_page: int = 6,
    keyword: str = "lighters",
    usd_rate: int = DEFAULT_USD_RATE,
) -> tuple[str, int]:
    """Định dạng danh sách các phiên eBay có phân trang."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y %H:%M")

    if not items:
        empty_text = (
            f"🦅 <b>RADAR ĐẤU GIÁ EBAY ({date_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện chưa tìm thấy phiên đấu giá nào có bid cho từ khóa <code>{keyword.upper()}</code> kết thúc trước 11:00 AM sáng mai.\n"
            f"Anh có thể thử: <code>/radarebay dupont</code>, <code>/radarebay dunhill</code> hoặc <code>/radarebay zippo</code>!</i>"
        )
        return empty_text, 1

    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start_i = (page - 1) * per_page
    end_i = min(start_i + per_page, total_items)
    slice_items = items[start_i:end_i]

    lines = [
        f"🦅 <b>RADAR ĐẤU GIÁ EBAY (SẮP TÀN PHIÊN)</b>",
        f"🔥 <i>Từ khóa: <b>{keyword.upper()}</b> — Trang {page}/{total_pages} ({total_items} cây có bids)</i>",
        f"⏰ <i>Khung giờ: Kết thúc từ nay đến 11:00 AM sáng mai</i>",
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, it in enumerate(slice_items, start=start_i + 1):
        lines.append(format_single_ebay_block(i, it, usd_rate=usd_rate))
        lines.append("─────────────────────")

    lines.append(f"💡 <i>Tất cả các cây trên đều ĐÃ CÓ BIDS (loại bỏ toàn bộ 0 bid). Anh thấy cây nào ưng ý bấm vào link soi và cân nhắc bid nhé!</i>")
    return "\n".join(lines), total_pages
