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

from config import load_config
from db import get_db_connection
from parser import fetch_yahoo_auction_info, verify_yahoo_lighter_lot
from repository import save_lot_audit_log

logger = logging.getLogger(__name__)

# Regex loại trừ hàng không phải bật lửa (IQOS, vape, quần áo, rượu, đồng hồ, kính, trang sức, túi xách...)
_NON_LIGHTER_EXCLUDE_RE = re.compile(
    r"(アイコス|iqos|iluma|イルマ|glo|グロー|ploom|プルーム|ベイプ|vape|電子タバコ|電子たばこ|加熱式タバコ|加熱式|ポッド|relx|"
    r"ドクターベイプ|dr\.vape|myblu|juul|シーシャ|shisha|リキッド|ニコチン|アトマイザー|"
    r"靴下|ソックス|時計|ウォッチ|腕時計|バッグ|財布|コインケース|小銭入れ|名刺入れ|カードケース|パスケース|マネークリップ|"
    r"ネクタイ|カフス|タイピン|タイバー|香水|フレグランス|洋酒|古酒|ウイスキー|ブランデー|"
    r"万年筆|ボールペン|ペン先|シャツ|ジャケット|コート|シューズ|ベルト|マフラー|スカーフ|ハンカチ|スーツ|"
    # 'リング' (nhẫn) không được khớp nhầm 'スターリング' (bạc sterling), 'Oリング/オーリング' (gioăng), 'スプリング' (lò xo)
    r"メガネ|眼鏡|サングラス|めがね|(?<!スター)(?<!オー)(?<![OoＯｏ])(?<!スプ)リング|指輪|ネックレス|ブレスレット|ペンダント|ピアス|イヤリング|ブローチ|"
    r"キーリング|キーケース|キーホルダー|灰皿|アッシュトレイ|シガーカッター|葉巻カッター|熱収縮チューブ|ハンダ|配線修理|ガスボンベ|フリントのみ|替え芯のみ)",
    re.IGNORECASE,
)

# Nhóm loại trừ tuyệt đối: thuốc lá điện tử / thuốc lá nung nóng, chỉ bán đá lửa / bấc (loại kể cả khi tiêu đề có chữ ライター)
_HARD_NON_LIGHTER_RE = re.compile(
    r"(アイコス|iqos|iluma|イルマ|glo|グロー|ploom|プルーム|ベイプ|vape|電子タバコ|電子たばこ|加熱式タバコ|加熱式|ポッド|relx|"
    r"ドクターベイプ|dr\.vape|myblu|juul|シーシャ|shisha|リキッド|ニコチン|アトマイザー|フリントのみ|替え芯のみ)",
    re.IGNORECASE,
)


def _is_non_lighter_title(title: str) -> bool:
    """Tiêu đề thuộc hàng không phải bật lửa?

    - Thuốc lá điện tử / chỉ bán đá lửa, bấc: luôn loại.
    - Từ chỉ món khác (đồng hồ, gạt tàn, bút, bình gas...): chỉ loại khi tiêu đề KHÔNG có chữ ライター thật
      (không tính 'ライター用'), vì lô bật lửa hay ghi kèm món phụ, ví dụ 'ZIPPO 4点まとめ ... 懐中時計 ... オイルライター'.
    """
    if not title:
        return False
    if _HARD_NON_LIGHTER_RE.search(title):
        return True
    if _NON_LIGHTER_EXCLUDE_RE.search(title):
        return not re.search(r"ライター(?!用)", title)
    return False

# Regex chỉ báo bật lửa / phụ kiện châm lửa hoặc các nhãn hiệu bật lửa danh tiếng
_LIGHTER_INDICATOR_RE = re.compile(
    r"(ライター|zippo|ジッポ|dupont|デュポン|dunhill|ダンヒル|cartier|カルティエ|ronson|ロンソン|maruman|マルマン|オイル|ガス|喫煙|着火|火花|パイプ)",
    re.IGNORECASE,
)

# Regex nhận diện dấu hiệu bán theo lô / nhiều cây
_LOT_KEYWORDS_RE = re.compile(
    r"(まとめ(?:売り)?|大量|セット|アソート|ジャンク|\d+\s*(?:点|本|個|台)|詰め合わせ|詰合せ|遺品整理|遺品|蔵出し|蔵出|引き取り品|引取品|実家|ガラクタ|当時物|旧家|"
    r"複数(?!出品)|多数(?!出品)|色々|いろいろ|一括)",
    re.IGNORECASE,
)

# Regex loại trừ nếu chỉ là 1 cây đơn chiếc
_SINGLE_ITEM_EXCLUDE_RE = re.compile(r"(\b1点のみ\b|単品|単体|1本のみ)", re.IGNORECASE)

# Regex chỉ bán phụ kiện, vỏ hộp rỗng, linh kiện/ruột
_ACCESSORY_ONLY_TITLE_RE = re.compile(
    r"(?:^|[\s/・_])(?:箱のみ|ケースのみ|空箱|元箱のみ|木箱のみ|インサイドユニット|インナーユニット|ユニットのみ|部品のみ|パーツのみ|フリントのみ|発火石のみ|替え芯のみ|ガスボンベのみ|ガス缶のみ)(?:$|[\s/・_])"
    r"|(?:空箱|ケースのみ|箱のみ|インサイドユニット)\s*\d+\s*(?:個|点|個まとめ|点セット)",
    re.IGNORECASE,
)

# Regex bán chọn món, giá từng cây
_PER_PIECE_CHOICE_TITLE_RE = re.compile(
    r"(?:どれか1つ|どれか1点|お選び(?:ください|頂|願)?|1つお選び|ご希望の(?:番号|品|種類|カラー|ものを)|好きなものを|"
    r"(?:各1個|各1本|各1点|1個|1本|1点|単品)(?:あたり)?(?:の)?(?:価格|値段|金額|お値段)|単品価格)",
    re.IGNORECASE,
)

# Danh mục truy vấn quét sâu toàn bộ danh mục lô bật lửa Yahoo Auctions
LOT_SEARCH_QUERIES = [
    # Bật lửa nói chung & từ khóa bán gom
    "ライター まとめ売り",
    "ライター まとめて",
    "ライター 大量",
    "ライター セット",
    "ライター 大量まとめ",
    "ライター ジャンク まとめ",
    # Dòng bật lửa
    "オイルライター まとめ",
    "ガスライター まとめ",
    "オイルライター セット",
    "ガスライター セット",
    # Các thương hiệu danh tiếng
    "ZIPPO まとめ",
    "ジッポ まとめ",
    "ジッポー セット",
    "デュポン まとめ",
    "ダンヒル ライター セット",
    "ダンヒル まとめ",
    "カルティエ ライター まとめ",
    "カルティエ まとめ",
    "ロンソン まとめ",
    # Dấu hiệu số lượng cụ thể
    "ライター 2個",
    "ライター 3個",
    "ライター 5本",
    "ライター 10点",
    "ライター 複数",
    "ライター 着火未確認 まとめ",
    "ライター 現状品 まとめて",
    # Săn hàng Di vật dọn nhà / Dọn kho cổ gia truyền (Hidden Gems)
    "遺品整理 ライター",
    "蔵出し ライター",
    "引き取り品 ライター",
    "実家 片付け ライター",
    "ガラクタ ライター まとめて",
    "当時物 ライター セット",
    "喫煙具 大量 放出",
]


def is_lot_title(title: str) -> bool:
    """Kiểm tra chính xác tiêu đề có phải là LÔ BẬT LỬA hay không (100% precision)."""
    if not title:
        return False
    title_clean = title.strip()

    # 1. Loại trừ hàng phụ kiện, trang sức, rượu, đồng hồ, tất vớ
    if _is_non_lighter_title(title_clean):
        return False

    # 2. Loại trừ nếu chỉ bán hộp rỗng hoặc linh kiện/ruột
    if _ACCESSORY_ONLY_TITLE_RE.search(title_clean) and not any(k in title_clean for k in ["ライター", "オイルライター", "ガスライター"]):
        return False

    # 3. Loại trừ nếu bán chọn món hoặc giá tính theo từng cây
    if _PER_PIECE_CHOICE_TITLE_RE.search(title_clean):
        return False

    # 4. Loại trừ nếu người bán ghi rõ là bán 1 cây lẻ (trừ khi có từ まとめ/大量 đi kèm)
    if _SINGLE_ITEM_EXCLUDE_RE.search(title_clean) and "まとめ" not in title_clean and "大量" not in title_clean:
        return False

    # 5. Loại trừ bản giới hạn số lượng (ví dụ: 1000個限定, 限定1000個) nếu không có từ khóa lot thực sự
    if re.search(r"(?:限定\s*\d+\s*(?:個|本|点)|(?:\d+)\s*個限定)", title_clean) and not any(k in title_clean for k in ["まとめ", "大量", "詰め合わせ", "本まとめ"]):
        return False

    # 6. Bắt buộc phải có chỉ báo bật lửa (ライター, zippo, gas, dầu, v.v.)
    if not _LIGHTER_INDICATOR_RE.search(title_clean):
        return False

    # 7. Bắt buộc phải có từ khóa lô (まとめ, セット, 大量, 10点, v.v.)
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

    # Trường hợp 2: ISO 8601 string (ví dụ: "2026-09-14T22:05:07+09:00") hoặc chuỗi ngày
    str_val = str(endtime_val).strip()
    end_dt = None
    try:
        iso_dt = datetime.fromisoformat(str_val)
        if iso_dt.tzinfo is None:
            end_dt = iso_dt.replace(tzinfo=jst)
        else:
            end_dt = iso_dt.astimezone(jst)
    except Exception:
        pass

    if not end_dt:
        clean_str = str_val.replace("/", "-").split(".")[0]
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


async def fetch_yahoo_search_full_blocks(
    query: str = "",
    limit: int = 100,
    category_id: int | str = "",
    offset: int = 1,
    sort_key: str = "end",
    sort_order: str = "a",
) -> list[dict[str, Any]]:
    """Gửi request tìm kiếm trên Yahoo Auctions và trích xuất TOÀN BỘ (lên đến 100 sản phẩm) từ HTML blocks và pageData.

    Khóa chặt danh mục bật lửa đồ cổ/sưu tầm: 26138 (アンティーク、コレクション > 雑貨 > 喫煙グッズ > ライター).
    offset/sort_key/sort_order: lật trang (b=1, 101, 201...) và kiểu sắp xếp (mặc định s1=end&o1=a = sắp hết giờ trước).
    """
    LIGHTER_ROOT_CAT = "26138"
    target_cat = str(category_id).strip() if category_id else LIGHTER_ROOT_CAT
    b_offset = max(1, int(offset or 1))

    if query:
        encoded_q = urllib.parse.quote_plus(query)
        # Bắt buộc kèm auccat={target_cat} để giới hạn tìm kiếm trong danh mục bật lửa 26138
        url = f"https://auctions.yahoo.co.jp/search/search?p={encoded_q}&auccat={target_cat}&exflg=1&b={b_offset}&n={limit}&s1={sort_key}&o1={sort_order}"
    else:
        url = f"https://auctions.yahoo.co.jp/category/list/{target_cat}/?b={b_offset}&n={limit}&s1={sort_key}&o1={sort_order}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    items: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.warning(f"Yahoo search status {resp.status_code} for: {query or category_id}")
                return []

            html = resp.text

            # 1. Trích xuất từ thẻ dữ liệu JSON chuẩn __NEXT_DATA__ (Next.js SSR mới của Yahoo Auctions)
            m_next = re.search(r'<script id="__NEXT_DATA__"[^>]*>([^<]+)</script>', html)
            if m_next:
                try:
                    data = json.loads(m_next.group(1))
                    listing = (
                        data.get("props", {})
                        .get("pageProps", {})
                        .get("initialState", {})
                        .get("search", {})
                        .get("items", {})
                        .get("listing", {})
                    )
                    raw_items = listing.get("items", [])
                    for it in raw_items:
                        aid = str(it.get("auctionId") or "").strip()
                        title = str(it.get("title") or "").strip()
                        price = int(it.get("price") or 0)
                        bids = int(it.get("bidCount") or 0)
                        endtime_raw = str(it.get("endTime") or "").strip()
                        img_url = str(it.get("imageUrl") or "").strip()
                        # Phí ship nội địa Nhật: chỉ lấy khi miễn phí (0) hoặc phí cố định (SINGLE/QUANTITY).
                        # Phí theo tỉnh / kích thước / theo giá chốt (AMOUNT) / trả sau (着払い, 落札後) -> None để không báo sai.
                        ship_fee = None
                        if it.get("isFreeShipping"):
                            ship_fee = 0
                        elif it.get("hasShippingFee") and str(it.get("currentPriceShippingFeeType") or "").upper() in ("SINGLE", "QUANTITY"):
                            try:
                                fee_val = int(it.get("currentPriceShippingFee") or 0)
                                ship_fee = fee_val if fee_val > 0 else None
                            except (TypeError, ValueError):
                                ship_fee = None
                        if aid and title and not any(x["auction_id"] == aid for x in items):
                            items.append({
                                "auction_id": aid,
                                "title": title,
                                "price_jpy": price,
                                "bids": bids,
                                "end_time": endtime_raw,
                                "url": f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                                "image_url": img_url,
                                "shipping_fee_jpy": ship_fee,
                            })
                except Exception as json_err:
                    logger.debug(f"Không thể parse __NEXT_DATA__: {json_err}")

            # 2. Fallback nếu không có __NEXT_DATA__: Trích xuất từ các thẻ <li class="Product"> trong HTML cũ
            if not items:
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

                    m_img = re.search(r'class="Product__imageData"[^>]*src="([^"]+)"', b)
                    if not m_img:
                        m_img = re.search(r'src="(https://auctions\.c\.yimg\.jp/images\.auctions\.yahoo\.co\.jp/image/[^"]+)"', b)
                    img_url = m_img.group(1).strip() if m_img else ""

                    if aid and title and not any(x["auction_id"] == aid for x in items):
                        items.append({
                            "auction_id": aid,
                            "title": title,
                            "price_jpy": price,
                            "bids": bids,
                            "end_time": endtime_raw,
                            "url": f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                            "image_url": img_url,
                        })

            # 3. Fallback: Bổ sung thêm từ pageData nếu có
            if not items:
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
                            img_val = it.get("image") or it.get("thumbnail") or ""
                            if aid and title and not any(x["auction_id"] == aid for x in items):
                                items.append({
                                    "auction_id": aid,
                                    "title": title,
                                    "price_jpy": price,
                                    "bids": bids,
                                    "end_time": endtime,
                                    "url": f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                                    "image_url": str(img_val),
                                })
                    except Exception:
                        pass

    except Exception as e:
        logger.error(f"Lỗi tải Yahoo search '{query}': {e}")

    return items


# Kết quả quét trọn danh mục được dùng lại trong 4 phút: worker chạy 10 phút/lần nên luôn lấy mới,
# chỉ các lần bấm nút chế độ liền nhau mới dùng lại, tránh mỗi lần bấm lại tải thêm ~20 trang Yahoo.
_BID_SWEEP_TTL_SECS = 240
_BID_SWEEP_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


async def fetch_category_bid_sweep(
    category_id: str = "26138",
    max_pages: int = 40,
    concurrency_sem: Any = None,
) -> list[dict[str, Any]]:
    """Quét TRỌN danh mục theo thứ tự 'nhiều bid nhất trước', dừng khi gặp phiên 0 bid.

    Lý do (đo thật 11/11/2026): danh mục 26138 có ~58.000 phiên, riêng 1 ngày ~7.000 phiên kết thúc,
    nên trang 100 phiên 'sắp hết giờ' chỉ phủ được khoảng 1 giờ tới. Toàn danh mục chỉ ~1.900 phiên có bid
    (~19 trang), nên quét theo số bid lấy ĐỦ mọi phiên có bid mà vẫn nhẹ.
    Trên Yahoo hiện tại s1=bids&o1=a mới là 'nhiều bid trước' (-BID_COUNT); nếu Yahoo đảo lại thì tự thử o1=d.
    """
    import asyncio

    cache_key = str(category_id)
    cached = _BID_SWEEP_CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < _BID_SWEEP_TTL_SECS:
        return [dict(x) for x in cached[1]]

    sem = concurrency_sem or asyncio.Semaphore(4)
    page_size = 100
    batch_size = 4

    async def _page(page_idx: int, order: str) -> list[dict[str, Any]]:
        for attempt in range(2):
            async with sem:
                res = await fetch_yahoo_search_full_blocks(
                    query="",
                    limit=page_size,
                    category_id=category_id,
                    offset=1 + page_idx * page_size,
                    sort_key="bids",
                    sort_order=order,
                )
            if res:
                return res
            if attempt == 0:
                await asyncio.sleep(1.5)  # Yahoo hay ngắt kết nối thoáng qua: thử lại 1 lần
        return []

    def _bids(it: dict[str, Any]) -> int:
        try:
            return int(it.get("bids") or 0)
        except (TypeError, ValueError):
            return 0

    def _is_last_page(pg: list[dict[str, Any]]) -> bool:
        return len(pg) < page_size or _bids(pg[-1]) == 0

    order = "a"
    first = await _page(0, order)
    if first and _bids(first[0]) == 0:
        alt = await _page(0, "d")
        if alt and _bids(alt[0]) > 0:
            order, first = "d", alt

    collected: list[dict[str, Any]] = list(first)
    if not first:
        return collected  # Yahoo lỗi/chặn: không lưu cache để lượt sau quét lại

    failed = False
    if not _is_last_page(first):
        page_idx = 1
        while page_idx < max_pages:
            idxs = list(range(page_idx, min(page_idx + batch_size, max_pages)))
            pages = await asyncio.gather(*[_page(i, order) for i in idxs], return_exceptions=True)
            stop = False
            for pg in pages:
                if isinstance(pg, Exception) or not pg:
                    logger.warning(f"Quét bid danh mục {category_id}: 1 trang lỗi/rỗng sau khi thử lại ({pg!r:.80}), dừng ở {len(collected)} phiên")
                    failed = True
                    stop = True
                    continue
                collected.extend(pg)
                if _is_last_page(pg):
                    stop = True
                    break  # các trang sau trong cùng lượt chỉ còn phiên 0 bid
            if stop:
                break
            page_idx += batch_size

    logger.info(f"Quét trọn danh mục {category_id} theo bid: {len(collected)} phiên, {sum(1 for x in collected if _bids(x) > 0)} phiên có bid")
    if not failed:
        _BID_SWEEP_CACHE[cache_key] = (time.monotonic(), [dict(x) for x in collected])
    return collected


def classify_lighter_lot_type(title: str) -> tuple[str, str, str]:
    """Phân loại lô bật lửa vào 4 nhóm chính theo yêu cầu người dùng:
    1. 'gas_da': Lot Gas Đá (Bật lửa gas, đá lửa, flint) -> (code='gas_da', tag='[LOT GAS ĐÁ]', icon='⚡')
    2. 'dau': Bật lửa dầu (Oil lighter, xăng dầu) -> (code='dau', tag='[BẬT LỬA DẦU]', icon='🛢️')
    3. 'zippo': Zippo các loại -> (code='zippo', tag='[ZIPPO]', icon='🔥')
    4. 'thapcam': Lô thập cẩm, tổng hợp, tạp nham, junk gom -> (code='thapcam', tag='[LOT THẬP CẨM]', icon='📦')

    Trả về: (code, tag_display, icon)
    """
    if not title:
        return "thapcam", "[LOT THẬP CẨM]", "📦"

    t = title.lower()
    is_gem = bool(re.search(r"(遺品整理|遺品|蔵出し|蔵出|引き取り品|引取品|実家|片付け|ガラクタ|当時物|旧家|初だし|初出|処分品)", t, re.IGNORECASE))
    if is_gem:
        return "gem", "[💎 DI VẬT DỌN KHO]", "💎"

    is_zippo = bool(re.search(r"(zippo|ジッポ|ジッポー)", t, re.IGNORECASE))
    is_oil = bool(re.search(r"(オイル|oil|オイルライター|油|xăng|petrol)", t, re.IGNORECASE))
    is_gas = bool(re.search(r"(ガス|gas|フリント|flint|着火石|発火石|ガスライター|石)", t, re.IGNORECASE))

    # Nếu chỉ có Zippo
    if is_zippo and not (is_gas and is_oil):
        return "zippo", "[ZIPPO]", "🔥"

    # Bật lửa dầu đơn thuần
    if is_oil and not is_gas:
        return "dau", "[BẬT LỬA DẦU]", "🛢️"

    # Bật lửa gas đá đơn thuần
    if is_gas and not is_oil:
        return "gas_da", "[LOT GAS ĐÁ]", "⚡"

    # Nếu pha trộn hoặc gom tổng hợp
    return "thapcam", "[LOT THẬP CẨM]", "📦"


BRAND_RADAR_CONFIGS = {
    "lot": {
        "title": "LÔ BẬT LỬA",
        "queries": LOT_SEARCH_QUERIES,
        "is_lot_only": True,
    },
    "thapcam": {
        "title": "LÔ THẬP CẨM",
        "queries": [
            "ライター まとめ売り",
            "ライター まとめて",
            "ライター 大量",
            "ライター セット",
            "ライター ジャンク まとめ",
            "ライター 詰め合わせ",
            "喫煙具 まとめ",
            "ライター 大量まとめ",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(まとめ|セット|大量|詰め合わせ|ジャンク|色々|詰合せ|アソート)", re.IGNORECASE),
    },
    "gas_da": {
        "title": "LOT GAS ĐÁ",
        "queries": [
            "ガスライター まとめ",
            "ガスライター セット",
            "ガスライター まとめて",
            "ガスライター 大量",
            "ライター フリント まとめ",
            "ライター 着火石 まとめ",
            "ガスライター ジャンク",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(ガス|gas|フリント|flint|着火石|発火石|石)", re.IGNORECASE),
    },
    "dau": {
        "title": "BẬT LỬA DẦU",
        "queries": [
            "オイルライター まとめ",
            "オイルライター セット",
            "オイルライター 大量",
            "オイルライター まとめて",
            "オイルライター ジャンク",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(オイル|oil|油|xăng)", re.IGNORECASE),
    },
    "zippo": {
        "title": "ZIPPO (LÔ)",
        "queries": [
            "ジッポ まとめ",
            "ジッポー まとめ",
            "zippo まとめて",
            "zippo セット",
            "ジッポ 大量",
            "zippo 大量",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(zippo|ジッポ|ジッポー)", re.IGNORECASE),
    },
    "dupont": {
        "title": "S.T. DUPONT (LÔ)",
        "queries": [
            "デュポン まとめ",
            "デュポン まとめて",
            "デュポン ライター セット",
            "デュポン 大量",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(dupont|デュポン)", re.IGNORECASE),
    },
    "dunhill": {
        "title": "ALFRED DUNHILL (LÔ)",
        "queries": [
            "ダンヒル まとめ",
            "ダンヒル まとめて",
            "ダンヒル ライター セット",
            "ダンヒル 大量",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(dunhill|ダンヒル)", re.IGNORECASE),
    },
    "gem": {
        "title": "💎 DI VẬT DỌN KHO (HIDDEN GEMS)",
        "queries": [
            "遺品整理 ライター",
            "蔵出し ライター",
            "引き取り品 ライター",
            "実家 片付け ライター",
            "ガラクタ ライター まとめて",
            "当時物 ライター セット",
            "喫煙具 大量 放出",
            "旧家 蔵出 ライター",
        ],
        "is_lot_only": True,
        "match_re": re.compile(r"(遺品整理|遺品|蔵出し|蔵出|引き取り品|引取品|実家|片付け|ガラクタ|当時物|旧家|初だし|初出|処分品)", re.IGNORECASE),
    },
}


async def scan_today_lighter_lots(queries: list[str] | None = None, mode: str = "lot") -> list[dict[str, Any]]:
    """Quét TOÀN DIỆN tất cả các phiên đấu Yahoo Auctions theo chế độ CHỈ SĂN LOT ĐÃ XÁC MINH:
    
    1. Quét theo bộ từ khóa và danh mục bật lửa Yahoo 42531
    2. Lọc nhanh các điều kiện: bids > 0 và kết thúc hôm nay
    3. Tải chi tiết phiên đấu (fetch_yahoo_auction_info)
    4. Xác minh nghiêm ngặt bằng verify_yahoo_lighter_lot (>= 2 cây bật lửa, bán chung cả lot)
    5. Lưu vết audit log vào CSDL
    6. Chỉ trả về danh sách lot đã xác minh (loại bỏ 100% hàng lẻ, phụ kiện và chưa rõ)
    """
    raw_mode = (mode or "lot").lower().strip()
    if raw_mode in ("gas", "gasda", "gas_da", "da", "flint"):
        mode_clean = "gas_da"
    elif raw_mode in ("dau", "oil", "xang", "xangdau", "xang_dau"):
        mode_clean = "dau"
    elif raw_mode in ("thapcam", "thap_cam", "mix", "honhop", "hon_hop"):
        mode_clean = "thapcam"
    elif raw_mode in ("gem", "gems", "divat", "di_vat", "kho", "don_kho", "ve_chai"):
        mode_clean = "gem"
    else:
        mode_clean = raw_mode

    mode_cfg = BRAND_RADAR_CONFIGS.get(mode_clean, BRAND_RADAR_CONFIGS["lot"])

    if queries is None:
        queries = mode_cfg["queries"]

    now_utc = datetime.now(timezone.utc)
    all_matched: dict[str, dict[str, Any]] = {}

    import asyncio
    # Giới hạn 4 requests đồng thời để không làm Yahoo CDN ngắt kết nối (tránh lỗi 503 / disconnect)
    sem = asyncio.Semaphore(4)

    async def _fetch_with_sem(q_or_cat: str, is_cat: bool = False) -> list[dict[str, Any]]:
        async with sem:
            if is_cat:
                return await fetch_yahoo_search_full_blocks(query="", limit=100, category_id=q_or_cat)
            else:
                return await fetch_yahoo_search_full_blocks(q_or_cat, limit=100)

    # 1. Tìm kiếm qua bộ từ khóa
    tasks = [_fetch_with_sem(q) for q in queries]
    # Bổ sung 1 task quét thẳng danh mục gốc bật lửa đồ cổ/sưu tầm Yahoo 26138
    tasks.append(_fetch_with_sem("26138", is_cat=True))
    # Bổ sung quét TRỌN mọi phiên có bid trong danh mục 26138 (không sót phiên nằm ngoài 100 kết quả đầu của từ khóa)
    tasks.append(fetch_category_bid_sweep("26138", concurrency_sem=sem))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, Exception):
            logger.warning(f"Lỗi quét query Yahoo: {res}")
            continue
        for it in res:
            aid = it["auction_id"]
            if aid in all_matched:
                continue

            title = it.get("title", "")
            bids = it.get("bids", 0)
            endtime_raw = it.get("end_time", "")

            # Bộ lọc sơ bộ danh mục / hàng không phải bật lửa
            if _is_non_lighter_title(title):
                continue
            if not _LIGHTER_INDICATOR_RE.search(title):
                continue

            # Bắt buộc có lượt Bid (> 0)
            if bids <= 0:
                continue

            # Bắt buộc kết thúc trong ngày hôm nay
            is_today, remain_str, remain_mins = is_ending_today(endtime_raw, now_utc=now_utc)
            if not is_today:
                continue

            # Nếu là chế độ lot, kiểm tra sơ bộ tiêu đề
            if mode_cfg["is_lot_only"]:
                if not is_lot_title(title):
                    continue
            else:
                match_re = mode_cfg.get("match_re")
                if match_re and not match_re.search(title):
                    continue

            it["remain_text"] = remain_str
            it["remain_mins"] = remain_mins
            all_matched[aid] = it

    # 2. Bước xác minh LOT trực tiếp từ dữ liệu tìm kiếm (tốc độ siêu tốc ~8s, không spam 50 request gây lỗi 500 từ Yahoo)
    candidate_items = list(all_matched.values())
    valid_lots: list[dict[str, Any]] = []

    cfg = load_config()
    conn = None
    try:
        conn = get_db_connection(cfg.db_path)
    except Exception:
        conn = None

    try:
        for it in candidate_items:
            aid = it["auction_id"]
            title = it.get("title", "")

            # Dựng mock info từ dữ liệu search để xác thực lot với parser chuẩn
            info = {
                "auction_id": aid,
                "title": title,
                "current_price_jpy": it.get("price_jpy", 0),
                "bids": it.get("bids", 0),
                "end_time": it.get("end_time", ""),
                "remain_text": it.get("remain_text", ""),
                "remain_mins": it.get("remain_mins", -1),
                "url": it.get("url") or f"https://auctions.yahoo.co.jp/jp/auction/{aid}",
                "image_url": it.get("image_url", ""),
                "shipping_fee_jpy": it.get("shipping_fee_jpy"),
                "status": "open",
                "is_fetched": True,
                "category_id": "26138",
                "category_path": [{"id": "26138", "name": "ライター"}],
            }

            verify = verify_yahoo_lighter_lot(info)

            # Lưu vết phân loại audit vào database nếu có kết nối
            if conn:
                try:
                    save_lot_audit_log(
                        conn,
                        auction_id=aid,
                        title=title,
                        decision_code=verify["decision_code"],
                        lighter_count=verify.get("lighter_count"),
                        condition_label=verify.get("condition_label", ""),
                        brands=", ".join(verify.get("brands", [])),
                        evidence_reason=verify.get("evidence_reason", ""),
                        price_jpy=it.get("price_jpy", 0),
                        bids=it.get("bids", 0),
                        end_time=it.get("end_time", ""),
                        url=info.get("url") or it.get("url", ""),
                        image_url=info.get("image_url", ""),
                    )
                except Exception:
                    pass

            # Lọc theo chế độ lot hoặc chế độ thương hiệu
            if mode_cfg.get("is_lot_only", True):
                if not verify.get("is_verified_lot"):
                    continue
                match_re = mode_cfg.get("match_re")
                if match_re and not match_re.search(title):
                    continue
            else:
                match_re = mode_cfg.get("match_re")
                if match_re and not match_re.search(title):
                    continue

            lot_code, lot_tag, lot_icon = classify_lighter_lot_type(title)
            it["lot_type_code"] = lot_code
            it["lot_type_tag"] = lot_tag
            it["lot_type_icon"] = lot_icon
            it.update(verify)
            valid_lots.append(it)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    # Sắp xếp toàn bộ danh sách lot đã xác minh theo thời gian kết thúc sớm nhất lên đầu
    sorted_lots = sorted(valid_lots, key=lambda x: x.get("remain_mins", 999999))
    return sorted_lots


def format_single_lot_block(idx: int, it: dict[str, Any], rate: int = 165) -> str:
    """Định dạng 1 khối hiển thị thông tin sản phẩm bật lửa theo chuẩn LOT đã xác minh."""
    title = it.get("title", "Bật lửa đấu giá")
    if len(title) > 65:
        title = title[:62] + "..."

    price = it.get("price_jpy", 0)
    effective_rate = rate if rate > 0 else 165
    price_vnd = round(price * effective_rate)
    bids = it.get("bids", 0)
    remain = it.get("remain_text", "Hôm nay")
    aid = it.get("auction_id", "")
    raw_url = it.get("url") or f"https://auctions.yahoo.co.jp/jp/auction/{aid}"
    y_url = raw_url.replace("https://page.auctions.yahoo.co.jp", "https://auctions.yahoo.co.jp")
    buyee_url = f"https://buyee.jp/item/yahoo/auction/{aid}?lang=vi"
    price_str = f"{price:,} yên (~{price_vnd:,} đ)".replace(",", ".")

    badge = it.get("badge_label")
    lot_tag = it.get("lot_type_tag", "")
    tag_prefix = f"{lot_tag} " if lot_tag else ""
    hdr = f"[{badge}] {tag_prefix}{title}" if badge else f"{tag_prefix}{title}"
    brand_sum = it.get("brand_summary")
    cond_lbl = it.get("condition_label")
    evidence = it.get("evidence_reason")
    unit_jpy = it.get("unit_price_jpy")
    unit_vnd = it.get("unit_price_vnd")
    ship_jpy = it.get("shipping_fee_jpy")

    lines = [
        f"<b>{idx}. {hdr}</b>",
    ]
    if brand_sum and brand_sum not in ["Bật lửa", "Bật lửa tổng hợp"]:
        lines.append(f"🏷️ <b>Hãng:</b> {brand_sum}")

    p_line = f"💰 <b>Giá:</b> {price_str} | 🔨 <b>Bids:</b> {bids}"
    if ship_jpy and ship_jpy > 0:
        p_line += f" | 🚚 Ship: {ship_jpy:,}Y"
    if unit_jpy and unit_vnd:
        p_line += f"\n📊 <b>Đơn giá:</b> ~{unit_jpy:,} yên/cây (~{unit_vnd:,} đ/cây)".replace(",", ".")
    lines.append(p_line)

    time_line = f"⏳ <b>Hạn:</b> {remain}"
    if cond_lbl:
        time_line += f" | ⚙️ <b>Tình trạng:</b> {cond_lbl}"
    lines.append(time_line)

    if evidence:
        lines.append(f"💡 <i>{evidence}</i>")

    lines.append(
        f"👉 <a href='{y_url}'>Xem Yahoo</a> | <a href='{buyee_url}'>Mở Buyee</a>\n"
        f"🔗 <a href='{y_url}'>{y_url}</a>\n"
        f"📸 <i>Soi ảnh nét:</i> /img_{aid}\n"
        f"💡 <i>Lưu data:</i> <code>/data #{aid}</code>"
    )
    return "\n".join(lines)



def format_radar_chunks(lots: list[dict[str, Any]], chunk_size: int = 8, rate: int = 165, category_name: str = "LÔ BẬT LỬA") -> list[str]:
    """Chia toàn bộ danh sách thành các tin nhắn riêng biệt để không vượt quá giới hạn 4096 ký tự."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y")

    if not lots:
        return [
            f"🎯 <b>RADAR {category_name} (HÔM NAY {date_str})</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện tại không có sản phẩm nào có bid kết thúc trong ngày hôm nay hoặc các phiên đã tàn hết.\n"
            f"Radar vẫn đang chạy ngầm trên VPS và sẽ tự động thông báo ngay khi có phiên mới!</i>"
        ]

    total_lots = len(lots)
    total_parts = (total_lots + chunk_size - 1) // chunk_size
    chunks: list[str] = []

    for part_idx in range(total_parts):
        start_i = part_idx * chunk_size
        end_i = min(start_i + chunk_size, total_lots)
        slice_lots = lots[start_i:end_i]

        lines = [
            f"🎯 <b>RADAR {category_name} HÔM NAY ({date_str}) — PHẦN {part_idx + 1}/{total_parts}</b>",
            f"🔥 <i>Tổng cộng phát hiện: <b>{total_lots} phiên</b> đang có lượt bid</i>",
            f"━━━━━━━━━━━━━━━━━━━━━",
        ]

        for i, it in enumerate(slice_lots, start=start_i + 1):
            lines.append(format_single_lot_block(i, it, rate=rate))
            lines.append("─────────────────────")

        if part_idx + 1 == total_parts:
            lines.append(f"💡 <i>Đã gửi đủ toàn bộ {total_lots} phiên kết thúc hôm nay! Gõ <code>/radar</code> để cập nhật giá mới nhất.</i>")

        chunks.append("\n".join(lines))

    return chunks


def format_radar_message(lots: list[dict[str, Any]], page: int = 1, per_page: int = 8, rate: int = 165, category_name: str = "LÔ BẬT LỬA") -> tuple[str, int]:
    """Định dạng trang hiển thị Radar cho tương tác lật trang Inline Keyboard."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m/%Y")

    if not lots:
        if category_name == "LÔ BẬT LỬA":
            empty_text = (
                f"🎯 <b>RADAR LÔ BẬT LỬA (HÔM NAY {date_str})</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Hiện tại không có lô bật lửa nào có bid kết thúc trong ngày hôm nay hoặc các phiên đã tàn hết.\n"
                f"Radar vẫn đang chạy ngầm trên VPS và sẽ tự động thông báo ngay khi có lô mới!</i>"
            )
        else:
            empty_text = (
                f"🎯 <b>RADAR {category_name} (HÔM NAY {date_str})</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"<i>Hiện tại không có phiên {category_name.lower()} nào có bid kết thúc hôm nay hoặc các phiên đã tàn hết.\n"
                f"Anh có thể thử: <code>/radar dupont</code>, <code>/radar dunhill</code> hoặc <code>/radar zippo</code>!</i>"
            )
        return empty_text, 1

    total_lots = len(lots)
    total_pages = (total_lots + per_page - 1) // per_page
    page = max(1, min(page, total_pages))

    start_i = (page - 1) * per_page
    end_i = min(start_i + per_page, total_lots)
    slice_lots = lots[start_i:end_i]

    lines = [
        f"🎯 <b>RADAR {category_name} (HÔM NAY {date_str})</b>",
        f"🔥 <i>Tìm thấy <b>{total_lots} phiên</b> có bid — Trang {page}/{total_pages}</i>",
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    for i, it in enumerate(slice_lots, start=start_i + 1):
        lines.append(format_single_lot_block(i, it, rate=rate))
        lines.append("─────────────────────")

    lines.append(f"💡 <i>Gõ <code>/radar all</code> để gửi liền tất cả, hoặc <code>/radar dupont</code> để lọc Dupont!</i>")
    return "\n".join(lines), total_pages


def curate_top_radar_lots(lots: list[dict[str, Any]], max_items: int = 5) -> list[dict[str, Any]]:
    """Tuyển chọn kỹ càng TOP các lô bật lửa đáng tiền và sôi nổi nhất (LỰA CHỌN KỸ).
    
    Tiêu chí:
    - Bắt buộc có lượt đấu (bids >= 1), ưu tiên các lô đang tranh chấp sôi nổi.
    - Ưu tiên các thương hiệu có tiếng (Dupont, Dunhill, Zippo, Cartier, Ronson).
    - Loại bỏ các lô giá ảo hoặc không có ai quan tâm.
    - Sắp xếp: Nhiều bids nhất -> Hạn gần nhất -> Lấy tối đa max_items (mặc định 3-5 lô).
    """
    if not lots:
        return []

    # 1. Lọc các lô có bids >= 1
    active_lots = [lot for lot in lots if int(lot.get("bids", 0)) >= 1]
    if not active_lots:
        active_lots = lots

    # 2. Chấm điểm độ ưu tiên (Priority Score):
    def _score_lot(it: dict[str, Any]) -> float:
        score = 0.0
        bids = int(it.get("bids", 0))
        score += bids * 2.0

        brands = it.get("brands", [])
        if any("Dupont" in b for b in brands):
            score += 30.0
        if any("Dunhill" in b for b in brands):
            score += 25.0
        if any("Zippo" in b for b in brands):
            score += 20.0
        if any("Cartier" in b for b in brands):
            score += 20.0
        if any("Ronson" in b for b in brands):
            score += 15.0

        cnt = it.get("lighter_count")
        if cnt and 2 <= cnt <= 20:
            score += 10.0

        # Ưu tiên các phiên sắp kết thúc trong 1-4 giờ tới
        rem_mins = it.get("remain_mins", 9999)
        if 0 < rem_mins <= 240:
            score += 15.0

        return score

    sorted_lots = sorted(active_lots, key=_score_lot, reverse=True)
    return sorted_lots[:max_items]


def format_curated_top_radar_message(
    top_lots: list[dict[str, Any]],
    total_scanned: int = 0,
    rate: int = 165,
    header_title: str | None = None,
) -> str:
    """Tạo duy nhất 1 bản tin tinh gọn, sang trọng hiển thị Top 3-5 lô đáng tiền nhất (chống spam)."""
    now_vn = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=7)))
    date_str = now_vn.strftime("%d/%m")

    title_header = header_title or f"🎯 <b>[BẢN TIN CHỌN LỌC] TOP {len(top_lots)} LÔ BẬT LỬA ĐÁNG ĐẤU ({date_str})</b>"

    if not top_lots:
        return (
            f"{title_header}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Hiện chưa có lô bật lửa nào đạt chuẩn tranh đấu sôi nổi hôm nay. Bot đang tiếp tục canh chừng ngầm!</i>"
        )

    effective_rate = rate if rate > 0 else 165
    lines = [
        title_header,
        f"━━━━━━━━━━━━━━━━━━━━━",
    ]

    for idx, it in enumerate(top_lots, start=1):
        title = it.get("title", "Lô bật lửa")
        if len(title) > 60:
            title = title[:57] + "..."

        price = it.get("price_jpy", 0)
        price_vnd = round(price * effective_rate)
        bids = it.get("bids", 0)
        remain = it.get("remain_text", "Hôm nay")
        aid = it.get("auction_id", "")
        cnt = it.get("lighter_count")
        cnt_badge = f"LOT {cnt} CÂY" if cnt else "LOT SỈ"
        brand_sum = it.get("brand_summary") or "Hỗn hợp"
        cond = it.get("condition_label") or "Hiện trạng"
        y_url = f"https://auctions.yahoo.co.jp/jp/auction/{aid}"
        buyee_url = f"https://buyee.jp/item/yahoo/auction/{aid}?lang=vi"

        lines.append(f"🔥 <b>{idx}. [{cnt_badge}] {title}</b>")
        lines.append(f"🏷️ <i>{brand_sum} · {cond}</i>")
        lines.append(
            f"💰 <b>{price:,} yên</b> (~{price_vnd:,} đ) | 🔨 <b>{bids} Bids</b> | ⏳ <b>{remain}</b>".replace(",", ".")
        )
        lines.append(f"👉 <a href='{buyee_url}'>🛒 Mở Buyee Đấu</a> | <a href='{y_url}'>Yahoo</a> | Soi ảnh: /img_{aid}")
        lines.append("─────────────────────")

    footer = f"💡 <i>Đã chọn lọc từ {total_scanned} lô hôm nay. Chỉ gửi các lô hot có bids & đáng tiền!</i>" if total_scanned > 0 else "💡 <i>Chỉ gửi các lô hot có bids & đáng tiền nhất!</i>"
    lines.append(footer)
    return "\n".join(lines)

