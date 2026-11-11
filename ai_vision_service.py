"""Module AI Vision thẩm định bật lửa: Sử dụng Google Gemini Vision API
nhận diện cây quẹt giá trị cao (Dupont, Dunhill, Cartier, Zippo bạc...) ẩn trong các lô rác / dọn nhà.
"""
from __future__ import annotations

import base64
import logging
import os
import re
import time
from typing import Any

import httpx

from config import load_config

logger = logging.getLogger(__name__)

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

# Từ phủ định: tên hãng đứng sau trong cùng câu là hãng KHÔNG có trong lô
_BRAND_NEGATION_RE = re.compile(
    r"(?:không|chưa|chẳng)\s+(?:hề\s+)?(?:thấy|phải|có|phát hiện|xuất hiện|rõ|giống)|chứ không|thay vì",
    re.IGNORECASE,
)

# Prompt chuyên gia thẩm định bật lửa cổ Nhật Bản
LIGHTER_INSPECTION_PROMPT = """Bạn là chuyên gia thẩm định bật lửa cổ và sưu tầm cao cấp Nhật Bản (Dunhill, Dupont, Cartier, Zippo, Ronson, Maruman...).
Hãy soi thật kỹ bức ảnh chụp lô bật lửa này (thường là lô ve chai, dọn nhà, thanh lý kho bên Nhật) và phân tích:

1. [THƯƠNG HIỆU QUÝ]: Có phát hiện cây nào của các hãng cao cấp không?
   - S.T. Dupont (Ligne 1, Ligne 2, Gatsby, mạ vàng, sơn mài urushi...)
   - Dunhill (Rollagas bánh xe ngang, Unique, Dress...)
   - Cartier (Santos, Oval...)
   - Zippo (Zippo bạc khối Sterling / 925, đáy la mã, vintage replica 1932/1937/1941, đồng khối...)
   - Ronson, Maruman, Caran d'Ache, Colibri, Sarome cổ.
2. [SỐ LƯỢNG & TỔNG QUAN]: Ước tính có khoảng bao nhiêu cây bật lửa trong ảnh?
3. [ĐÁNH GIÁ ĐỒ QUÝ / LỌC VÀNG TRONG CÁT]: 
   - Có dấu hiệu "ngọc trong đá" (cây xịn ẩn lẫn trong đống bật lửa nhựa/gas rẻ tiền) không?
   - Đánh giá: [CỰC HOT / ĐỒ HIẾM] hay [TIỀM NĂNG] hay [LÔ BÌNH DÂN / RÁC]?

Trả lời ngắn gọn, rõ ràng theo định dạng sau:
- ĐÁNH GIÁ: [CỰC HOT / TIỀM NĂNG / BÌNH DÂN]
- THƯƠNG HIỆU PHÁT HIỆN: <tên các hãng phát hiện được hoặc 'Chưa thấy hãng danh tiếng'>
- ĐIỂM SÁNG: <1-2 câu chỉ rõ cây nào đáng giá, ví dụ: 1 cây Dunhill mạ vàng sọc ngang, 1 Zippo kim loại đáy cổ>
- ƯỚC TÍNH: ~<số lượng> cây
"""


def parse_gemini_vision_response(text: str) -> dict[str, Any]:
    """Phân tích kết quả text trả về từ Gemini thành cấu trúc dữ liệu."""
    if not text:
        return {
            "gem_detected": False,
            "detected_brands": [],
            "rating": "BÌNH DÂN",
            "highlights": "Không có thông tin phân tích",
            "estimated_count": "Không rõ",
            "summary_short": "Chưa có phân tích ảnh",
            "raw_text": "",
        }

    raw = text.strip()
    is_gem = False
    rating = "BÌNH DÂN"
    brands: list[str] = []

    upper_text = raw.upper()
    plain_text = raw.replace("**", "").replace("__", "")

    # Mức đánh giá: ưu tiên đọc đúng dòng "ĐÁNH GIÁ:" (AI hay nhắc lại các mức khác ở phần giải thích).
    # Dòng chép nguyên khuôn mẫu "[CỰC HOT / TIỀM NĂNG / BÌNH DÂN]" (nhiều mức một lúc) -> coi là chưa rõ, không gắn đồ hiếm.
    m_rate = re.search(r"ĐÁNH GIÁ\s*:\s*([^\n\r]+)", plain_text, re.IGNORECASE)
    if m_rate:
        rate_line = m_rate.group(1).upper()
        levels = [
            lvl for lvl, keys in (
                ("CỰC HOT", ("CỰC HOT", "ĐỒ HIẾM")),
                ("TIỀM NĂNG", ("TIỀM NĂNG", "ĐỒ XỊN", "ĐỒ QUÝ")),
                ("BÌNH DÂN", ("BÌNH DÂN", "RÁC")),
            )
            if any(k in rate_line for k in keys)
        ]
        if len(levels) == 1 and levels[0] != "BÌNH DÂN":
            is_gem = True
            rating = levels[0]
    elif "CỰC HOT" in upper_text or "ĐỒ HIẾM" in upper_text:
        is_gem = True
        rating = "CỰC HOT"
    elif "TIỀM NĂNG" in upper_text or "ĐỒ XỊN" in upper_text or "ĐỒ QUÝ" in upper_text:
        is_gem = True
        rating = "TIỀM NĂNG"

    # Nhận diện thương hiệu: bỏ các hãng nằm sau từ phủ định trong cùng câu
    # ("Không thấy ... Dupont, Dunhill hay Cartier", "không phải Zippo chính hãng").
    known_brands = ["DUPONT", "DUNHILL", "CARTIER", "ZIPPO", "RONSON", "MARUMAN", "CARAN D'ACHE", "SAROME", "COLIBRI"]
    brand_scope = re.sub(r"S\.?\s*T\.?\s*(?=DUPONT|DU\s*PONT)", "", plain_text, flags=re.IGNORECASE)
    m_brand_line = re.search(r"THƯƠNG HIỆU PHÁT HIỆN\s*:\s*([^\n\r]+)", brand_scope, re.IGNORECASE)
    m_high_line = re.search(r"(?:ĐIỂM SÁNG|ĐIỂM NHẤN|CHI TIẾT ĐÁNG GIÁ)\s*:\s*([^\n\r]*(?:[\n\r]+[^\n\r]*){0,5})", brand_scope, re.IGNORECASE)
    if m_brand_line:
        brand_scope = m_brand_line.group(1) + "\n" + (m_high_line.group(1) if m_high_line else "")
    kept_parts = []
    for clause in re.split(r"[.;!?()\[\]\n\r]+", brand_scope):
        neg = _BRAND_NEGATION_RE.search(clause)
        kept_parts.append(clause[: neg.start()] if neg else clause)
    brand_text = " ".join(kept_parts).upper()
    for b in known_brands:
        if b in brand_text:
            brands.append(b.title())

    if any(b in ["Dupont", "Dunhill", "Cartier"] for b in brands):
        is_gem = True

    # Chuẩn hóa loại bỏ dấu markdown bold/italic để parse regex chính xác
    clean_raw = raw.replace("**", "").replace("__", "")

    # Trích xuất dòng điểm sáng
    highlights = ""
    m_high = re.search(r"(?:ĐIỂM SÁNG|ĐIỂM NHẤN|CHI TIẾT ĐÁNG GIÁ)[:\s]+([^\n\r]+)", clean_raw, re.IGNORECASE)
    if m_high:
        highlights = m_high.group(1).strip().lstrip("-*•+ ").strip()  # bỏ gạch đầu dòng thừa khi AI xuống dòng
    else:
        # Lấy dòng đầu tiên có chứa thương hiệu hoặc thông tin
        lines = [line.strip("- *•").strip() for line in clean_raw.splitlines() if line.strip()]
        for l in lines:
            if any(b.lower() in l.lower() for b in known_brands):
                highlights = l
                break
        if not highlights and lines:
            highlights = lines[0]

    # Trích xuất ước tính số lượng
    count_str = "Nhiều cây"
    m_cnt = re.search(r"(?:ƯỚC TÍNH|SỐ LƯỢNG)[:\s]+([^\n\r]+)", clean_raw, re.IGNORECASE)
    if m_cnt:
        count_str = m_cnt.group(1).strip()

    # Escape HTML để đảm bảo an toàn tuyệt đối khi gửi caption Telegram
    highlights_safe = highlights.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    count_safe = count_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Tạo tóm tắt ngắn (summary_short) cho caption Telegram
    icon = "💎" if is_gem else "🔍"
    brand_str = ", ".join(brands) if brands else "Chưa rõ hiệu lớn"
    summary_short = f"{icon} <b>AI Soi:</b> [{rating}] {brand_str} ({count_safe})\n• <i>{highlights_safe}</i>"

    return {
        "gem_detected": is_gem,
        "detected_brands": brands,
        "rating": rating,
        "highlights": highlights,
        "estimated_count": count_str,
        "summary_short": summary_short,
        "raw_text": raw,
    }


# Chuỗi model Gemini dùng gói MIỄN PHÍ (cùng 1 key, quota tính RIÊNG từng model, reset 0h giờ Pacific).
# Đo thật 11/11/2026: gemini-2.5-flash free chỉ còn 20 lượt/ngày -> hết từ sáng; gemini-3.1-flash-lite trả lời 2-5 s, đúng định dạng.
# Có thể đổi bằng biến môi trường GEMINI_VISION_MODELS="model1,model2,...".
# (gemini-2.5-flash-lite trả 404 "no longer available to new users" nên không dùng.)
DEFAULT_VISION_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]

# Model đang tạm khóa (hết quota ngày / phút, hoặc không còn tồn tại) -> thời điểm (time.monotonic) được thử lại
_MODEL_BLOCKED_UNTIL: dict[str, float] = {}


def _vision_model_chain(preferred: str | None = None) -> list[str]:
    env_models = [m.strip() for m in os.getenv("GEMINI_VISION_MODELS", "").split(",") if m.strip()]
    chain = env_models or list(DEFAULT_VISION_MODELS)
    if preferred:
        chain = [preferred] + [m for m in chain if m != preferred]
    return chain


def _quota_block_seconds(resp: httpx.Response) -> tuple[float, str]:
    """Đọc lỗi 429 của Gemini: (số giây nên khóa model, loại quota). Quota ngày khóa tới khi Google mở lại."""
    per_day = False
    retry_secs = 0.0
    try:
        err = resp.json().get("error", {})
        for d in err.get("details", []) or []:
            for v in d.get("violations", []) or []:
                if "PerDay" in str(v.get("quotaId", "")):
                    per_day = True
            m = re.match(r"^\s*([\d.]+)s\s*$", str(d.get("retryDelay") or ""))
            if m:
                retry_secs = float(m.group(1))
    except Exception:
        pass
    if per_day:
        return max(retry_secs, 600.0), "ngày"
    return max(retry_secs, 30.0), "phút"


async def inspect_lighter_lot_image(
    image_bytes: bytes,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Gửi ảnh lô bật lửa tới Google Gemini Vision API để thẩm định và phát hiện hàng hiệu ẩn.

    Thử lần lượt các model miễn phí: model nào hết quota (429) / quá tải (500, 503) / quá giờ thì chuyển ngay model kế.
    Ảnh hỏng (400) thì model nào cũng lỗi như nhau nên trả lỗi ngay, không tốn quota model khác.
    Key gửi qua header x-goog-api-key (không nằm trong URL nên không lộ ra log).
    """
    if not image_bytes:
        return {"success": False, "error": "Ảnh rỗng hoặc không tải được"}

    if not api_key:
        cfg = load_config()
        api_key = cfg.gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.debug("Chưa cấu hình GEMINI_API_KEY, bỏ qua soi AI Vision.")
        return {"success": False, "error": "Chưa cấu hình GEMINI_API_KEY"}

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data,
                        }
                    },
                    {"text": LIGHTER_INSPECTION_PROMPT},
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 600,
        },
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}

    started = time.monotonic()
    budget = max(timeout * 2.5, timeout + 5.0)  # tổng thời gian tối đa cho cả chuỗi model / 1 ảnh
    last_error = "Gemini API không phản hồi"
    tried = 0

    for mdl in _vision_model_chain(model):
        now = time.monotonic()
        if _MODEL_BLOCKED_UNTIL.get(mdl, 0.0) > now:
            continue
        if tried and now - started > budget:
            break
        tried += 1
        url = GEMINI_API_URL_TEMPLATE.format(model=mdl)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException:
            last_error = f"Gemini {mdl} quá {timeout:.0f}s"
            continue
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini Vision API ({mdl}): {e}")
            last_error = str(e)
            continue

        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                # Bỏ phần 'suy nghĩ' (thought) của model, chỉ lấy câu trả lời
                raw_text = "".join(p.get("text", "") for p in parts if "text" in p and not p.get("thought"))
                if raw_text.strip():
                    parsed = parse_gemini_vision_response(raw_text)
                    parsed["success"] = True
                    parsed["model"] = mdl
                    return parsed
            last_error = f"Gemini {mdl} không trả về kết quả nội dung"
            continue

        if resp.status_code == 429:
            secs, kind = _quota_block_seconds(resp)
            _MODEL_BLOCKED_UNTIL[mdl] = time.monotonic() + secs
            logger.warning(f"Gemini {mdl} hết quota miễn phí theo {kind}, tạm bỏ qua {secs / 3600:.1f} giờ, chuyển model kế.")
            last_error = f"Gemini {mdl} hết quota miễn phí ({kind})"
            continue
        if resp.status_code == 404:
            _MODEL_BLOCKED_UNTIL[mdl] = time.monotonic() + 86400
            logger.warning(f"Gemini model {mdl} không còn tồn tại (404), bỏ qua 24 giờ.")
            last_error = f"Gemini model {mdl} không tồn tại"
            continue
        last_error = f"Gemini API lỗi HTTP {resp.status_code} ({mdl}): {resp.text[:200]}"
        if resp.status_code in (500, 502, 503, 504):
            logger.info(last_error)
            continue
        logger.warning(last_error)
        return {"success": False, "error": last_error}

    if not tried:
        last_error = "Tất cả model Gemini miễn phí đều đã hết quota, chờ Google mở lại (0h giờ Pacific)"
    return {"success": False, "error": last_error}
