"""Module AI Vision thẩm định bật lửa: Sử dụng Google Gemini Vision API
nhận diện cây quẹt giá trị cao (Dupont, Dunhill, Cartier, Zippo bạc...) ẩn trong các lô rác / dọn nhà.
"""
from __future__ import annotations

import base64
import logging
import os
import re
from typing import Any

import httpx

from config import load_config

logger = logging.getLogger(__name__)

GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
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
    if "CỰC HOT" in upper_text or "ĐỒ HIẾM" in upper_text:
        is_gem = True
        rating = "CỰC HOT"
    elif "TIỀM NĂNG" in upper_text or "ĐỒ XỊN" in upper_text or "ĐỒ QUÝ" in upper_text:
        is_gem = True
        rating = "TIỀM NĂNG"

    # Nhận diện thương hiệu
    known_brands = ["DUPONT", "DUNHILL", "CARTIER", "ZIPPO", "RONSON", "MARUMAN", "CARAN D'ACHE", "SAROME", "COLIBRI"]
    for b in known_brands:
        if b in upper_text:
            brands.append(b.title())

    if any(b in ["Dupont", "Dunhill", "Cartier"] for b in brands):
        is_gem = True

    # Chuẩn hóa loại bỏ dấu markdown bold/italic để parse regex chính xác
    clean_raw = raw.replace("**", "").replace("__", "")

    # Trích xuất dòng điểm sáng
    highlights = ""
    m_high = re.search(r"(?:ĐIỂM SÁNG|ĐIỂM NHẤN|CHI TIẾT ĐÁNG GIÁ)[:\s]+([^\n\r]+)", clean_raw, re.IGNORECASE)
    if m_high:
        highlights = m_high.group(1).strip()
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


async def inspect_lighter_lot_image(
    image_bytes: bytes,
    api_key: str | None = None,
    model: str = "gemini-2.5-flash",
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Gửi ảnh lô bật lửa tới Google Gemini Vision API để thẩm định và phát hiện hàng hiệu ẩn."""
    if not image_bytes:
        return {"success": False, "error": "Ảnh rỗng hoặc không tải được"}

    if not api_key:
        cfg = load_config()
        api_key = cfg.gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        logger.debug("Chưa cấu hình GEMINI_API_KEY, bỏ qua soi AI Vision.")
        return {"success": False, "error": "Chưa cấu hình GEMINI_API_KEY"}

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    url = GEMINI_API_URL_TEMPLATE.format(model=model, api_key=api_key)

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

    import asyncio
    max_retries = 2
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        raw_text = "".join(p.get("text", "") for p in parts if "text" in p)
                        parsed = parse_gemini_vision_response(raw_text)
                        parsed["success"] = True
                        return parsed
                    return {"success": False, "error": "Gemini không trả về kết quả nội dung"}
                elif resp.status_code in (429, 503) and attempt < max_retries - 1:
                    await asyncio.sleep(1.5)
                    continue
                else:
                    err_msg = f"Gemini API lỗi HTTP {resp.status_code}: {resp.text[:200]}"
                    logger.warning(err_msg)
                    return {"success": False, "error": err_msg}
        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                await asyncio.sleep(1.0)
                continue
            return {"success": False, "error": "Gemini API timeout"}
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini Vision API: {e}")
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Gemini API không phản hồi"}
