"""Module Radar chuyên sâu: Quét toan bộ (FULL) các lô bật lửa có lượt bid kết thúc hôm nay trên Yahoo Auctions."""
from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Regex loại trừ hàng không phải bật lửa (quần áo, rượu, đồng hồ, túi xách, dụng cụ hàn, nước hoa...)
_NON_LIGHTER_EXCLUDE_RE = re.compile(
    r"(靴下|ソックス|時計|ウォッチ|バッグ|財布|ネクタイ|カフス|タイピン|香水|フレグランス|洋酒|古酒|ウイスキー|ブランデー|万年筆|ボールペン|ペン先|シャツ|ジャケット|コート|シューズ|ベルト|熱収縮チューブ|ハンダ|配線修理|ガスボンベ|フリントのみ|替え芯のみ)",
    re.IGNORECASE,
)

# Regex chỉ báo bật lửa / phụ kiện châm lửa hoặc các nhãn hiệu bật lửa danh tiếng
_LIGHTER_INDICATOR_RE = re.compile(
    r"(ライター|zippo|ジッポ|dupont|デュポン|dunhill|ダンヒル|cartier|カルティエ|ronson|ロンソン|maruman|マルマン|オイル|ガス|喫煙|着火|火花|パイプ)",
    re.IGNORECASE,
)

# Regex nhận diện dấu hiệu bán theo lô / nhiều cây
_LOT_KEYWORDS_RE = re.compile(
    r"(まとめ(?:売り)?|大量|セット|アソート|ジャンク|\d+\s*(?:点|本|個|台)|詰め合わせ|詰合せ)",
    re.IGNORECASE,
)

# Regex loại trừ nếu chỉ là 1 cây đơn chiếc
_SINGLE_ITEM_EXCLUDE_RE = re.compile(r"(\b1点のみ\b|単品|単体|1本のみ)", re.IGNORECASE)

# Danh sách 10 truy vấn quét sâu toàn bộ danh mục lô bật lửa Yahoo Auctions
LOT_SEARCH_QUERIES = [
    "ライター まとめ",
    "ライター 大量",
    "ライター セット",
    "ライター ジャンク",
    "ジッポ まとめ",
    "ダンヒル まとめ",
    "デュポン まとめ",
    "オイルライター まとめ",
    "ガスライター まとめ",
    "喫煙具 まとめ",
]


def is_lot_title(title: str) -> bool:
    """Kiểm tra chính xác tiêu đề có phải là LÔ BẬT LỬA hay không (100% precision)."""
    if not title:
        return False
    title_clean = title.strip()

    # 1. Loại trừ hàng phụ kiện, trang sức, rượu, đồng hồ, tất vớ
    if _NON_LIGHTER_EXCLUDE_RE.search(title_clean):
        return False

    # 2. Loại trừ nếu người bán ghi rõ là bán 1 cây lẻ (trừ khi có từ まとめ/大量 đi kèm)
    if _SINGLE_ITEM_EXCLUDE_RE.search(title_clean) and "まとめ" not in title_clean and "大量" not in title_clean:
        return False

    # 3. Bắt buộc phải có chỉ báo bật lửa (ライター, zippo, gas, dầu, v.v.)
    if not _LIGHTER_INDICATOR_RE.search(title_clean):
        return False

    # 4. Bắt buộc phải có từ khóa lô (まとめ, セット, 大量, 10点, v.v.)
    return bool(_LOT_KEYWORDS_RE.search(title_clean))


def is_ending_today(endtime_val: str | int, now_utc: datetime | None = None) -> tuple[bool, str, int]:
    """Kiểm tra xem thời điểm kết thúc có nằm trong ngày HÔM NAY (JST UTC+9) không.
    
    Hỗ trợ cả UNIX timestamp (int/str) và chuỗi ngày 'YYYY-MM-DD HH:MM:SS'.
    Trả về: (is_today, formatted_remaining, remaining_minutes)
    """
    if not endtime_val:
        return False, "", -1

    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    jst = timezone(timedelta(hours=9))
    now_jst = now_utc.astimezone(jst)
    now_ts = int(now_utc.timestamp())

    end_of_today_jst = now_jst.replace(hour=23, minute=59, second=59, microsecond=999999)
    end_of_today_ts = int(end_of_today_jst.timestamp())

    # Trường hợp 1: UNIX timestamp số nguyên (rất chính xác từ data-auction-endtime)
    if isinstance(endtime_val, (int, float)) or (isinstance(endtime_val, str) and endtime_val.isdigit() and len(endtime_val) >= 9):
        end_ts = int(endtime_val)
        if end_ts <= now_ts:
            return False, "Đã hết giờ", -1
        if end_ts > end_of_today_ts:
            end_dt = datetime.fromtimestamp(end_ts, tz=jst)
            return False, f"Ngày mai ({end_dt.strftime('%d/%m')})", -1

        remain_secs = end_ts - now_ts
        total_mins = remain_secs // 60
        h = total_mins // 60
        m = total_mins % 60
        remain_text = f"còn {h}h{m:02d}m" if h > 0 else f"còn {m} phút"
        return True, remain_text, total_mins

    # Trường hợp 2: Chuỗi ngày "YYYY-MM-DD HH:MM:SS"
    clean_str = str(endtime_val).strip().replace("/", "-").split(".")[0]
    end_dt = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            naive_dt = datetime.strptime(clean_str, fmt)
            end_dt = naive_dt.replace(tzinfo=jst)
            break
        except ValueError:
            continue

    if not end_dt:
        return False, "", -1

    if end_dt <= now_jst:
        return False, "Đã hết giờ", -1

    if end_dt.date() != now_jst.date():
        return False, f"Ngày mai ({end_dt.strftime('%d/%m')})", -1

    delta = end_dt - now_jst
    total_mins = int(delta.total_seconds() // 60)
    h = total_mins // 60
    m = total_mins % 60
    remain_text = f"còn {h}h{m:02d}m" if h > 0 else f"còn {m} phút"
    return True, remain_text, total_mins


async def fetch_yahoo_search_full_blocks(query: str, limit: int = 100) -> list[dict[str, Any]]:
    """Gửi request tìm kiếm trên Yahoo Auctions và trích xuất TOÀN BỘ (lên đến 100 sản phẩm) từ HTML blocks và pageData."""
    encoded_q = urllib.parse.quote_plus(query)
    url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_q}&va={encoded_q}&exflg=1&b=1&n={limit}&s1=end&o1=a"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    items: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Yahoo search status {resp.status_code} for: {query}")
                return []

            html = resp.text

            # 1. Trích xuất từ 100 thẻ <li class="Product"> trong HTML (Đầy đủ và toàn diện nhất)
            blocks = re.findall(r'<li class="Product[^>]*>(.*?)</li>', html, re.DOTALL)
            for b in blocks:
                m_id = re.search(r'data-auction-id="([^"]+)"', b)
                if not m_id:
                    continue
                aid = m_id.group(1).strip()

                m_title = re.search(r'data-auction-title="([^"]+)"', b)
                if not m_title:
                    m_title = re.search(r'class="Product__titleLink[^"]*"[^>]*title="([^"]*)"', b)
                title = m_title.group(1).strip() if m_title else ""

                m_price = re.search(r'data-auction-price="(\d+)"', b)
                price = int(m_price.group(1)) if m_price else 0

                m_end = re.search(r'data-auction-endtime="(\d+)"', b)
                endtime_raw = m_end.group(1) if m_end else ""

                m_bids = re.search(r'class="Product__bid"[^>]*>(\d+)<', b)
                bids = int(m_bids.group(1)) if m_bids else 0

                if aid and title:
                    items.append({
                        "auction_id": aid,
                        "title": title,
                        "price_jpy": price,
                        "bids": bids,
                        "end_time": endtime_raw,
                        "url": f"https://page.auctions.yahoo.co.jp/jp/auction/{aid}",
                    })

            # 2. Bổ sung thêm từ pageData nếu có thêm item chưa có
            m_pdata = re.search(r"var pageData\s*=\s*(\{.*?\});\s*(?:var|</script>)", html, re.DOTALL)
            if m_pdata:
                try:
                    pdata = json.loads(m_pdata.group(1))
                    for it in pdata.get("items", []):
                        aid = str(it.get("productID") or it.get("auctionID") or it.get("id") or "").strip()
                        title = str(it.get("productName") or it.get("title") or "").strip()
                        price = int(it.get("price") or 0)
                        bids = int(it.get("bids") or 0)
                        endtime = str(it.get("endtime") or "").strip()
                        if aid and title and not any(x["auction_id"] == aid for x in items):
                            items.append({
                                "auction_id": aid,
                                "title": title,
                                "price_jpy": price,
                                "bids": bids,
                                "end_time": endtime,
                                "url": f"https://page.auctions.yahoo.co.jp/jp/auction/{aid}",
                            })
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Lỗi tải Yahoo search '{query}': {e}")

    return items


async def scan_today_lighter_lots(queries: list[str] | None = None) -> list[dict[str, Any]]:
    """Quét TOÀN DIỆN tất cả các truy vấn lô bật lửa trên Yahoo Auctions, lọc đầy đủ 100%:
    
    1. is_lot_title(title) == True (Chỉ nhận lô bật lửa, loại bỏ hàng phụ kiện/thời trang)
    2. bids > 0 (Có ít nhất 1 lượt bid)
    3. is_ending_today(endtime) == True (Kết thúc trong ngày hôm nay)
    """
    if queries is None:
        queries = LOT_SEARCH_QUERIES

    now_utc = datetime.now(timezone.utc)
    all_matched: dict[str, dict[str, Any]] = {}

    for q in queries:
        try:
            items = await fetch_yahoo_search_full_blocks(q, limit=100)
            for it in items:
                aid = it["auction_id"]
                if aid in all_matched:
                    continue

                title = it.get("title", "")
                bids = it.get("bids", 0)
                endtime_raw = it.get("end_time", "")

                # Bộ lọc 1: Bắt buộc là Lot bật lửa thực sự
                if not is_lot_title(title):
                    continue

                # Bộ lọc 2: Bắt buộc có lượt Bid (> 0)
                if bids <= 0:
                    continue

                # Bộ lọc 3: Bắt buộc kết thúc trong ngày hôm nay
                is_today, remain_str, remain_mins = is_ending_today(endtime_raw, now_utc=now_utc)
                if not is_today:
                    continue

                it["remain_text"] = remain_str
                it["remain_mins"] = remain_mins
                all_matched[aid] = it
        except Exception as err:
            logger.warning(f"Lỗi quét query '{q}': {err}")

    # Sắp xếp toàn bộ danh sách theo thời gian kết thúc sớm nhất lên đầu
    sorted_lots = sorted(all_matched.values(), key=lambda x: x.get("remain_mins", 999999))
    return sorted_lots


def format_single_lot_block(idx: int, it: dict[str, Any], rate: int = 165) -> str:
    """Định dạng 1 khối hiển thị thông tin lô bật lửa."""
    title = it.get("title", "Lô bật lửa")
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

    return (
        f"<b>{idx}. {title}</b>\n"
        f"💰 <b>Giá:</b> {price_str} | 🔨 <b>Bids:</b> {bids}\n"
        f"⏳ <b>Hạn:</b> {remain}\n"
        f"👉 <a href='{y_url}'>Xem Yahoo</a> | <a href='{buyee_url}'>Mở Buyee</a>\n"
        f"👉 <i>Phân tích:</i> <code>/data {y_url}</code>"
    )


def format_radar_chunks(lots: list[dict[str, Any]], chunk_size: int = 8) -> list[str]:
    """Chia toàn bộ danh sách lô thành các tin nhắn riêng biệt (mỗi tin nhắn 8 lô) để không bao giờ bị tràn giới hạn 4096 ký tự của Telegram."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y")

    if not lots:
        return [
            f"🎯 <b>RADAR LÔ BẬT LỬA (HÔM NAY {date_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện tại không có lô bật lửa nào có bid kết thúc trong ngày hôm nay hoặc các phiên đã tàn hết.\n"
            f"Radar vẫn đang chạy ngầm trên VPS và sẽ tự động thông báo ngay khi có lô mới!</i>"
        ]

    total_lots = len(lots)
    total_parts = (total_lots + chunk_size - 1) // chunk_size
    chunks: list[str] = []

    for part_idx in range(total_parts):
        start_i = part_idx * chunk_size
        end_i = min(start_i + chunk_size, total_lots)
        slice_lots = lots[start_i:end_i]

        lines = [
            f"🎯 <b>RADAR LÔ BẬT LỬA HÔM NAY ({date_str}) — PHẦN {part_idx + 1}/{total_parts}</b>",
            f"🔥 <i>Tổng cộng phát hiện: <b>{total_lots} lô</b> đang có lượt bid</i>",
            f"━━━━━━━━━━━━━━━━━━━━━",
        ]

        for i, it in enumerate(slice_lots, start=start_i + 1):
            lines.append(format_single_lot_block(i, it))
            lines.append("─────────────────────")

        if part_idx + 1 == total_parts:
            lines.append(f"💡 <i>Đã gửi đủ toàn bộ {total_lots} lô kết thúc hôm nay! Gõ <code>/radar</code> để cập nhật giá mới nhất.</i>")

        chunks.append("\n".join(lines))

    return chunks


def format_radar_message(lots: list[dict[str, Any]], page: int = 1, per_page: int = 8) -> tuple[str, int]:
    """Định dạng trang hiển thị Radar cho tương tác lật trang Inline Keyboard."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y")

    if not lots:
        empty_text = (
            f"🎯 <b>RADAR LÔ BẬT LỬA (HÔM NAY {date_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện tại không có lô bật lửa nào có bid kết thúc trong ngày hôm nay hoặc các phiên đã tàn hết.\n"
            f"Radar vẫn đang chạy ngầm trên VPS và sẽ tự động thông báo ngay khi có lô mới!</i>"
        )
        return empty_text, 1

    total_lots = len(lots)
    total_pages = (total_lots + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start_i = (page - 1) * per_page
    end_i = min(start_i + per_page, total_lots)
    slice_lots = lots[start_i:end_i]

    lines = [
        f"🎯 <b>RADAR BẬT LỬA THEO LÔ (HÔM NAY {date_str})</b>",
        f"🔥 <i>Tìm thấy <b>{total_lots} lô</b> có bid — Trang {page}/{total_pages}</i>",
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, it in enumerate(slice_lots, start=start_i + 1):
        lines.append(format_single_lot_block(i, it))
        lines.append("─────────────────────")

    lines.append(f"💡 <i>Gõ <code>/radar all</code> để bot gửi liền toàn bộ {total_lots} lô trong 1 lần!</i>")
    return "\n".join(lines), total_pages
