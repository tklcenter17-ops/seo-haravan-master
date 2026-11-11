"""Bộ phân tích cú pháp (Parser) cho tin nhắn nhập dữ liệu và tra cứu."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from normalizer import clean_search_text, normalize_unicode, strip_vietnamese_accents


@dataclass
class ParseResult:
    is_valid: bool
    amount_jpy: int | None = None
    currency: str = "JPY"
    raw_desc: str = ""
    display_name: str = ""
    brand: str = "unknown"
    line: str = "unknown"
    size_submodel: str = "unknown"
    material: str = "unknown"
    finish: str = "unknown"
    color: str = "unknown"
    edition: str = "unknown"
    box: str = "unknown"  # yes | no | unknown
    papers: str = "unknown"  # yes | no | unknown
    accessories_note: str = ""
    cosmetic_condition: str = "unknown"
    functional_state: str = "unknown"
    authenticity_note: str = "unknown"
    price_basis: str = "pure"  # pure | all_in
    fee_jpy: int = 0
    fee_vnd: int = 0
    is_lot: bool = False
    note: str = ""
    auction_date: str | None = None
    auction_id: str | None = None
    source_url: str | None = None
    # Trạng thái cần hỏi lại / bản nháp
    needs_confirmation: bool = False
    confirmation_type: str = ""  # ambiguous_box | missing_price | missing_desc | clarify_price
    confirmation_message: str = ""
    error_message: str = ""
    suggested_prices: list[int] = field(default_factory=list)
    suggested_currency_prices: list[dict[str, Any]] = field(default_factory=list)
    raw_price_token: str = ""


# Regex nhận diện tiền tệ không hợp lệ ở V1
_VND_USD_RE = re.compile(r"(\b\d[\d.,]*\s*(?:vnd|vnđ|đ|usd|\$)\b|\b(?:usd|\$)\s*\d[\d.,]*)", re.IGNORECASE)

# Regex số thập phân (1-2 chữ số thập phân, vd 13.4Y, 13,4Y) hoặc viết tắt (13k4, 1man34, 13.400k)
_ABBR_PRICE_RE = re.compile(r"\b(\d+[.,]\d{1,2}[yY]|\d+k\d*|\d+man\d*|\d+[.,]\d+k)\b", re.IGNORECASE)

# Regex số phân nhóm sai kiểu 1.34.00Y
_BAD_GROUPING_RE = re.compile(r"\b\d+([.,]\d{1,2})+([.,]\d+)+[yY]?\b")


def parse_jpy_amount(token: str) -> tuple[int | None, str | None]:
    """Phân tích một token giá thành số nguyên JPY hoặc trả về lỗi cụ thể."""
    cleaned = normalize_unicode(token).strip()

    # Kiểm tra tiền tệ khác (VND / USD)
    if _VND_USD_RE.search(cleaned):
        return None, "V1 chỉ nhận giá thắng JPY, không tự đổi tiền."

    # Kiểm tra số thập phân hoặc viết tắt (13.4Y, 13k4, 1man34)
    if _ABBR_PRICE_RE.search(cleaned):
        return None, "Không tự suy đoán giá viết tắt hoặc số thập phân. Vui lòng nhập số yên đầy đủ (ví dụ: 13400Y hoặc 13.400Y)."

    # Bỏ các ký tự đơn vị ở đuôi hoặc đầu: Y, yen, 円, ¥
    t = cleaned
    if t.startswith("¥"):
        t = t[1:].strip()
    for suffix in ["yen", "y", "円"]:
        if t.lower().endswith(suffix):
            t = t[: -len(suffix)].strip()
            break

    # Kiểm tra phân nhóm sai kiểu 1.34.00
    if "." in t and "," in t:
        return None, "Số phân nhóm sai định dạng (vui lòng dùng dấu chấm hoặc phẩy nhất quán theo cụm 3 chữ số)."
    
    # Kiểm tra cụm phân nhóm bằng dấu chấm hoặc phẩy
    for sep in [".", ","]:
        if sep in t:
            parts = t.split(sep)
            # Phần đầu tiên có từ 1-3 chữ số, các phần sau bắt buộc đúng 3 chữ số
            if not parts[0].isdigit() or not (1 <= len(parts[0]) <= 3):
                return None, "Số phân nhóm sai định dạng."
            for p in parts[1:]:
                if not (p.isdigit() and len(p) == 3):
                    return None, "Số phân nhóm sai định dạng."
            t = "".join(parts)
            break

    # Bỏ khoảng trắng nếu có (ví dụ '13 400')
    t = t.replace(" ", "")

    if not t.isdigit():
        return None, f"Giá không hợp lệ: {cleaned}"

    val = int(t)
    if val <= 0:
        return None, "Từ chối giá không dương (giá phải lớn hơn 0 JPY)."

    return val, None


def get_multicurrency_suggestions(token: str) -> list[dict[str, Any]]:
    """Tạo danh sách mốc giá gợi ý đa tiền tệ (VND, JPY, USD) từ token viết tắt."""
    raw = normalize_unicode(token).strip()
    t = raw.lower()
    for s in ["yen", "y", "円", "vnd", "vnđ", "đ", "usd", "$"]:
        if t.endswith(s):
            t = t[:-len(s)].strip()

    suggestions: list[dict[str, Any]] = []

    # Dạng '300k' hoặc '500k' hoặc '30k'
    m_k = re.match(r"^(\d+)\s*k$", t)
    if m_k:
        base = int(m_k.group(1))
        # 1. VNĐ: 300k -> 300.000 VNĐ
        vnd_amt = base * 1000
        vnd_fmt = f"{vnd_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": vnd_amt,
            "currency": "VND",
            "label": f"🇻🇳 {vnd_fmt} đ",
        })
        
        # 2. Yên: Nếu base >= 100 (như 300k):
        if base >= 100:
            jpy_30k = base * 100
            jpy_30k_fmt = f"{jpy_30k:,}".replace(",", ".")
            suggestions.append({
                "amount": jpy_30k,
                "currency": "JPY",
                "label": f"🇯🇵 {jpy_30k_fmt} yên",
            })
            jpy_300k = base * 1000
            jpy_300k_fmt = f"{jpy_300k:,}".replace(",", ".")
            suggestions.append({
                "amount": jpy_300k,
                "currency": "JPY",
                "label": f"🇯🇵 {jpy_300k_fmt} yên",
            })
        else:
            jpy_amt = base * 1000
            jpy_fmt = f"{jpy_amt:,}".replace(",", ".")
            suggestions.append({
                "amount": jpy_amt,
                "currency": "JPY",
                "label": f"🇯🇵 {jpy_fmt} yên",
            })

        # 3. USD ước lượng: 300k đ ~ $12
        approx_usd = round(vnd_amt / 25500)
        if approx_usd > 0:
            suggestions.append({
                "amount": approx_usd,
                "currency": "USD",
                "label": f"🇺🇸 ${approx_usd} (~{base}k đ)",
            })

        return suggestions

    # Dạng '13k4' -> 13.400 yên hoặc 1.340.000 đ
    m_k_dot = re.match(r"^(\d+)k(\d+)$", t)
    if m_k_dot:
        int_part = int(m_k_dot.group(1)) * 1000
        dec_part = int(m_k_dot.group(2).ljust(3, "0"))
        jpy_amt = int_part + dec_part
        jpy_fmt = f"{jpy_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": jpy_amt,
            "currency": "JPY",
            "label": f"🇯🇵 {jpy_fmt} yên",
        })
        vnd_amt = (int(m_k_dot.group(1)) * 1000 + int(m_k_dot.group(2)) * 100) * 100
        if vnd_amt >= 10000:
            vnd_fmt = f"{vnd_amt:,}".replace(",", ".")
            suggestions.append({
                "amount": vnd_amt,
                "currency": "VND",
                "label": f"🇻🇳 {vnd_fmt} đ",
            })
        return suggestions

    # Dạng '1man34' -> 13.400 yên
    m_man = re.match(r"^(\d+)man(\d*)$", t)
    if m_man:
        int_part = int(m_man.group(1)) * 10000
        dec_part = int(m_man.group(2).ljust(4, "0")) if m_man.group(2) else 0
        jpy_amt = int_part + dec_part
        jpy_fmt = f"{jpy_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": jpy_amt,
            "currency": "JPY",
            "label": f"🇯🇵 {jpy_fmt} yên",
        })
        return suggestions

    # Dạng '50' (số nhỏ <= 500 không có đơn vị): có thể là $50, 50k VND, 5.000 yên
    if t.isdigit() and 1 <= int(t) <= 500:
        base = int(t)
        suggestions.append({
            "amount": base,
            "currency": "USD",
            "label": f"🇺🇸 ${base}",
        })
        vnd_amt = base * 1000
        vnd_fmt = f"{vnd_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": vnd_amt,
            "currency": "VND",
            "label": f"🇻🇳 {vnd_fmt} đ",
        })
        jpy_amt = base * 100
        jpy_fmt = f"{jpy_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": jpy_amt,
            "currency": "JPY",
            "label": f"🇯🇵 {jpy_fmt} yên",
        })
        return suggestions

    # Dạng thập phân '13.4Y' hoặc '13,4Y'
    m_dec = re.match(r"^(\d+)[.,](\d+)[yY]?$", raw)
    if m_dec:
        int_part = int(m_dec.group(1)) * 1000
        dec_part = int(m_dec.group(2).ljust(3, "0")[:3])
        jpy_amt = int_part + dec_part
        jpy_fmt = f"{jpy_amt:,}".replace(",", ".")
        suggestions.append({
            "amount": jpy_amt,
            "currency": "JPY",
            "label": f"🇯🇵 {jpy_fmt} yên",
        })
        return suggestions

    # Dạng '13.400k' -> 13.400 yên hoặc 13.400.000 đ
    m_dot_k = re.match(r"^(\d+)[.,](\d+)k$", t)
    if m_dot_k:
        base_int = int(m_dot_k.group(1)) * 1000 + int(m_dot_k.group(2).ljust(3, "0"))
        suggestions.append({
            "amount": base_int,
            "currency": "JPY",
            "label": f"🇯🇵 {base_int:,} yên".replace(",", "."),
        })
        vnd_amt = base_int * 1000
        suggestions.append({
            "amount": vnd_amt,
            "currency": "VND",
            "label": f"🇻🇳 {vnd_amt:,} đ".replace(",", "."),
        })
        return suggestions

    return suggestions


def get_price_suggestions(token: str) -> list[int]:
    """Tạo danh sách mốc giá gợi ý từ số tiền viết tắt (giữ tương thích int list)."""
    multis = get_multicurrency_suggestions(token)
    return [s["amount"] for s in multis]


def parse_multi_currency_price(token: str) -> tuple[int | None, str, str | None, list[dict[str, Any]]]:
    """Phân tích số tiền hỗ trợ đa tiền tệ (JPY, VND, USD) và sinh gợi ý thông minh nếu viết tắt."""
    raw = normalize_unicode(token).strip()
    t = raw.lower()

    # 1. USD: có ký hiệu $ hoặc đuôi usd, dollar, dola, đô
    is_usd = "$" in t or bool(re.search(r"(?:usd|dollar|dola|đô|do)", t))
    if is_usd:
        num_str = re.sub(r"[^\d.,]", "", t).strip()
        num_str = num_str.replace(",", ".")
        try:
            val = int(round(float(num_str)))
            if val <= 0:
                return None, "USD", "Giá USD phải lớn hơn 0.", []
            return val, "USD", None, []
        except ValueError:
            return None, "USD", f"Giá USD không hợp lệ: {raw}", []

    # 2. VND: có hậu tố vnd, vnđ, đ, d, dong, đồng HOẶC chứa tr, trieu, triệu HOẶC có đuôi k vnd
    is_explicit_vnd = bool(re.search(r"(vnd|vnđ|đ|\bdong\b|\bđồng\b|tr|\btrieu\b|\btriệu\b)", t))
    if is_explicit_vnd:
        # Trường hợp triệu: 1tr5, 1.5tr, 1,5 triệu, 2tr
        m_tr = re.search(r"^(\d+(?:[.,]\d+)?)\s*(?:tr|trieu|triệu)\s*(\d+)?", t)
        if m_tr:
            base_str = m_tr.group(1).replace(",", ".")
            tail_str = m_tr.group(2)
            base_num = float(base_str)
            if tail_str:
                tail_len = len(tail_str)
                tail_val = int(tail_str) * (10 ** (6 - tail_len))
                total = int(base_num * 1_000_000) + tail_val
            else:
                total = int(base_num * 1_000_000)
            if total > 0:
                return total, "VND", None, []

        # Trường hợp 300k vnd, 300k đ, 300kd
        m_k_vnd = re.search(r"^(\d+)\s*k\s*(?:vnd|vnđ|đ|d)?", t)
        if m_k_vnd:
            val = int(m_k_vnd.group(1)) * 1000
            if val > 0:
                return val, "VND", None, []

        # Trường hợp số phân nhóm: 300.000đ, 300.000 vnd
        num_str = re.sub(r"[^\d]", "", t)
        if num_str.isdigit():
            val = int(num_str)
            if val > 0:
                return val, "VND", None, []

    # 3. JPY rõ ràng: có ký hiệu Y, yen, 円, ¥
    is_explicit_jpy = (
        t.endswith("y") or t.endswith("yen") or t.endswith("円") or t.startswith("¥")
    )
    if is_explicit_jpy:
        val, err = parse_jpy_amount(raw)
        if val is not None:
            return val, "JPY", None, []
        sugg = get_multicurrency_suggestions(raw)
        return None, "JPY", err or "Giá Yên chưa rõ ràng", sugg

    # 4. Viết tắt hoặc mơ hồ chưa rõ tiền tệ (ví dụ '300k', '50', '13k4', '1man34')
    sugg = get_multicurrency_suggestions(raw)
    if sugg:
        return None, "AMBIGUOUS", "Giá viết tắt cần xác nhận loại tiền", sugg

    # 5. Kiểm tra nếu là số thuần túy không đơn vị
    val, err = parse_jpy_amount(raw)
    if val is not None:
        return val, "JPY", None, []

    return None, "UNKNOWN", err or f"Không nhận diện được số tiền: {raw}", []


def _is_valid_price_candidate(cand: str, prev_token: str = "", next_token: str = "") -> bool:
    """Kiểm tra xem một token (hoặc 2 token ghép lại) có khả năng là giá hay không."""
    cand_raw = cand.strip().lower()
    prev_raw = prev_token.strip().lower()
    next_raw = next_token.strip().lower()

    # 1. Loại trừ các số đi kèm thuộc tính
    if prev_raw in ["line", "ligne", "l", "serial", "so", "số", "ban", "bản", "edition", "doi", "đời"]:
        return False
    if next_raw in ["line", "ligne", "l", "doi", "đời", "cay", "cây", "chiec", "chiếc", "nam", "năm", "bản", "ban", "star"]:
        return False
    if cand_raw in ["1941", "1935", "1932", "1933", "1968", "1970", "2000"]:
        return False
    if cand_raw.endswith("%"):
        return False
    if cand_raw in ["925", "18k", "14k", "10k"]:
        return False
    if cand_raw in ["1", "2"] and (prev_raw in ["line", "ligne"] or next_raw in ["line", "ligne"]):
        return False
    if cand_raw in ["box", "hop", "hộp", "đẹp", "dep", "keng", "mới", "moi", "cu", "cũ", "used", "qua", "dùng", "dung"]:
        return False

    # Thử parse bằng parse_multi_currency_price
    val, curr, err, sugg = parse_multi_currency_price(cand)
    if val is not None and val > 0:
        return True
    if curr == "AMBIGUOUS" or len(sugg) > 0:
        return True
    return False


def extract_price_and_desc_multi(main_text: str) -> tuple[str, int | None, str, str | None, list[dict[str, Any]], str]:
    """Tách mô tả và token giá thắng ở BẤT KỲ VỊ TRÍ NÀO trong câu lệnh, hỗ trợ đa tiền tệ."""
    clean_input = main_text.strip()
    tokens = clean_input.split()
    if not tokens:
        return "", None, "JPY", "Thiếu mô tả và giá.", [], ""

    _CURRENCY_SUFFIXES = {
        "yen", "y", "円", "vnd", "vnđ", "đ", "d", "usd", "$",
        "dollar", "dola", "đô", "tr", "trieu", "triệu"
    }

    price_token_idx_start = -1
    price_token_idx_end = -1
    candidate_price = ""

    # Bước 1: Thử kiểm tra ở cuối câu trước (giữ tương thích với cú pháp chuẩn: /data ... 13.400Y)
    if len(tokens) >= 2 and tokens[-1].lower() in _CURRENCY_SUFFIXES:
        prev_t = tokens[-3] if len(tokens) >= 3 else ""
        cand = tokens[-2] + tokens[-1]
        if _is_valid_price_candidate(cand, prev_t, ""):
            price_token_idx_start = len(tokens) - 2
            price_token_idx_end = len(tokens)
            candidate_price = cand
    elif len(tokens) >= 2 and tokens[-2] == "$":
        cand = "$" + tokens[-1]
        price_token_idx_start = len(tokens) - 2
        price_token_idx_end = len(tokens)
        candidate_price = cand
    elif len(tokens) >= 1:
        prev_t = tokens[-2] if len(tokens) >= 2 else ""
        cand = tokens[-1]
        if _is_valid_price_candidate(cand, prev_t, ""):
            price_token_idx_start = len(tokens) - 1
            price_token_idx_end = len(tokens)
            candidate_price = cand

    # Bước 2: Nếu cuối câu KHÔNG phải là giá (ví dụ: '... thì 600k quay đầu . có box'):
    # Ta quét toàn bộ danh sách tokens để tìm token giá ở giữa câu
    if price_token_idx_start == -1:
        # 2.1. Quét các cặp 2 tokens ghép có đuôi tiền tệ (ví dụ '600k vnd', '50 $', '1.5 tr')
        for i in range(len(tokens) - 1):
            if tokens[i+1].lower() in _CURRENCY_SUFFIXES or tokens[i] == "$":
                cand = (tokens[i] + tokens[i+1]) if tokens[i] != "$" else ("$" + tokens[i+1])
                prev_t = tokens[i-1] if i > 0 else ""
                next_t = tokens[i+2] if i + 2 < len(tokens) else ""
                if _is_valid_price_candidate(cand, prev_t, next_t):
                    price_token_idx_start = i
                    price_token_idx_end = i + 2
                    candidate_price = cand
                    break

        # 2.2. Quét từng token đơn lẻ ở giữa câu (ví dụ '600k', '13.400Y', '50$')
        if price_token_idx_start == -1:
            for i in range(len(tokens)):
                cand = tokens[i]
                prev_t = tokens[i-1] if i > 0 else ""
                next_t = tokens[i+1] if i + 1 < len(tokens) else ""
                # Ở giữa câu, nếu là số trần nhỏ (<= 500) mà không có tiền tệ đi kèm và không có từ báo giá đi trước,
                # thì không tự suy đoán là giá (tránh nhầm số thứ tự, line 1, 2 v.v.)
                if cand.isdigit() and int(cand) <= 500:
                    prev_clean = strip_vietnamese_accents(prev_t).lower()
                    if prev_clean not in ["gia", "tam", "khoang", "chot", "bid", "thi", "duoi"]:
                        continue
                if _is_valid_price_candidate(cand, prev_t, next_t):
                    price_token_idx_start = i
                    price_token_idx_end = i + 1
                    candidate_price = cand
                    break

    # Nếu vẫn không tìm thấy token giá nào trong toàn bộ câu
    if price_token_idx_start == -1:
        return clean_input, None, "JPY", "Thiếu giá thắng.", [], ""

    # Bước 3: Đã tìm thấy token giá tại [price_token_idx_start : price_token_idx_end]
    # Ta mở rộng loại bỏ các từ đệm liên kết giá xung quanh token này:
    cut_start = price_token_idx_start
    cut_end = price_token_idx_end

    # Kiểm tra từ đệm phía trước: 'thì', 'tầm', 'khoảng', 'giá', 'chốt', 'tối đa', 'dưới'
    if cut_start > 0:
        prev_w = tokens[cut_start - 1].lower().strip()
        if prev_w in ["thi", "thì", "tam", "tầm", "khoang", "khoảng", "gia", "giá", "chot", "chốt", "toi da", "tối đa", "duoi", "dưới"]:
            cut_start -= 1

    # Kiểm tra từ đệm phía sau: 'quay đầu', 'đổ lại', 'quay về', 'thôi', 'được giá'
    if cut_end < len(tokens):
        next_w = tokens[cut_end].lower().strip()
        if next_w in ["thoi", "thôi"]:
            cut_end += 1
        elif cut_end + 1 < len(tokens):
            two_next = (tokens[cut_end] + " " + tokens[cut_end + 1]).lower().strip()
            if two_next in ["quay dau", "quay đầu", "do lai", "đổ lại", "quay ve", "quay về", "tro lai", "trở lại", "duoc gia", "được giá"]:
                cut_end += 2

    # Ghép phần mô tả từ các token còn lại (loại trừ các dấu chấm, phẩy đứng bơ vơ)
    remaining_tokens = tokens[:cut_start] + tokens[cut_end:]
    cleaned_desc_tokens = []
    for t in remaining_tokens:
        if t in [".", ",", "-", "|", ";", ":"]:
            continue
        cleaned_desc_tokens.append(t)

    desc = " ".join(cleaned_desc_tokens).strip()
    desc = re.sub(r"\s+[.,]\s+", " ", desc).strip()
    if desc.endswith("."):
        desc = desc[:-1].strip()

    amount, currency, err, suggestions = parse_multi_currency_price(candidate_price)
    return desc, amount, currency, err, suggestions, candidate_price


def extract_price_and_desc(main_text: str) -> tuple[str, int | None, str | None]:
    """Tách mô tả và token giá thắng ở cuối phần tin nhắn chính (giữ tương thích 3-tuple)."""
    desc, amount, _, err, _, _ = extract_price_and_desc_multi(main_text)
    return desc or main_text.strip(), amount, err


def parse_attributes(desc: str) -> dict[str, Any]:
    """Phân tích các thuộc tính quẹt từ mô tả: nhãn hiệu, dòng, chất liệu, màu, phụ kiện."""
    normalized = strip_vietnamese_accents(desc)
    raw_lower = normalize_unicode(desc).lower()
    
    attrs: dict[str, Any] = {
        "brand": "unknown",
        "line": "unknown",
        "size_submodel": "unknown",
        "material": "unknown",
        "finish": "unknown",
        "color": "unknown",
        "edition": "unknown",
        "box": "unknown",
        "papers": "unknown",
        "accessories_note": "",
        "cosmetic_condition": "unknown",
        "functional_state": "unknown",
        "is_ambiguous_box": False,
    }

    # 1. Nhận diện phụ kiện (QUY TẮC CỐT LÕI: Phủ định đi trước)
    negative_box_patterns = [
        "khong hop", "khong box", "no box", "mat hop", "ko hop", "k hop", "khong co hop", "khong co box",
        "箱なし", "本体のみ",
    ]
    has_negative_box = any(pat in normalized or pat in raw_lower for pat in negative_box_patterns)

    if has_negative_box:
        attrs["box"] = "no"
        attrs["accessories_note"] = "Không hộp"
    elif "full boc" in normalized or "ful boc" in normalized:
        attrs["is_ambiguous_box"] = True
        attrs["box"] = "unknown"
    elif any(pat in normalized for pat in ["full box", "full set", "du hop giay", "du hop phu kien", "du hop so"]):
        attrs["box"] = "yes"
        attrs["papers"] = "yes"
        attrs["accessories_note"] = "Đủ hộp, giấy, phụ kiện"
    elif any(pat in normalized for pat in ["co hop", "co box", "box", "hop"]) or any(pat in raw_lower for pat in ["箱付き", "元箱", "共箱", "ケース付き", "箱有"]):
        attrs["box"] = "yes"
        attrs["accessories_note"] = "Có hộp"

    # 2. Nhận diện Nhãn hiệu (Brand) - Hỗ trợ đầy đủ các hãng quẹt kinh điển & Tiếng Nhật Yahoo
    if any(b in normalized for b in ["dupont", "s.t. dupont", "st dupont", "s.t dupont", "st. dupont"]) or "デュポン" in raw_lower:
        attrs["brand"] = "dupont"
    elif "zippo" in normalized or any(z in raw_lower for z in ["ジッポー", "ジッポ"]):
        attrs["brand"] = "zippo"
    elif "ronson" in normalized or "ロンソン" in raw_lower:
        attrs["brand"] = "ronson"
    elif "dunhill" in normalized or "ダンヒル" in raw_lower:
        attrs["brand"] = "dunhill"
    elif "cartier" in normalized or "カルティエ" in raw_lower:
        attrs["brand"] = "cartier"
    elif "colibri" in normalized or "コリブリ" in raw_lower:
        attrs["brand"] = "colibri"
    elif "maruman" in normalized or "マルマン" in raw_lower:
        attrs["brand"] = "maruman"
    elif "sarome" in normalized or "サロメ" in raw_lower:
        attrs["brand"] = "sarome"
    elif "penguin" in normalized or "ペンギン" in raw_lower:
        attrs["brand"] = "penguin"
    elif "givenchy" in normalized or any(g in raw_lower for g in ["ジバンシィ", "ジバンシー"]):
        attrs["brand"] = "givenchy"
    elif "caran dache" in normalized or "caran d'ache" in raw_lower or "カランダッシュ" in raw_lower:
        attrs["brand"] = "caran_dache"

    # 3. Nhận diện Dòng (Line)
    if any(pat in normalized for pat in ["la ma", "lama", "la-ma"]):
        if attrs["brand"] == "unknown":
            attrs["brand"] = "zippo"
        attrs["line"] = "la_ma"
    elif any(pat in normalized for pat in ["rollagas", "ro la", "rola"]) or any(r in raw_lower for r in ["ローラガス", "ロールガス"]):
        if attrs["brand"] == "unknown":
            attrs["brand"] = "dunhill"
        attrs["line"] = "rollagas"
    elif any(pat in normalized for pat in ["1 line", "line 1", "ligne 1", "line_1", "l1"]) or "ライン1" in raw_lower:
        attrs["line"] = "line_1"
    elif any(pat in normalized for pat in ["2 line", "line 2", "ligne 2", "line_2", "l2"]) or "ライン2" in raw_lower:
        attrs["line"] = "line_2"
    elif any(pat in normalized for pat in ["v-mark", "v mark", "vmark"]):
        attrs["line"] = "v_mark"
    elif "standard" in normalized or "スタンダード" in raw_lower:
        attrs["line"] = "standard"
    elif "varaflame" in normalized or any(v in raw_lower for v in ["ヴァラフレーム", "バラフレーム"]):
        attrs["line"] = "varaflame"
    elif "banjo" in normalized or "バンジョー" in raw_lower:
        attrs["line"] = "banjo"
    elif "whirlwind" in normalized:
        attrs["line"] = "whirlwind"
    elif "premier" in normalized:
        attrs["line"] = "premier"
    elif "gatsby" in normalized or "ギャッツビー" in raw_lower:
        attrs["line"] = "gatsby"
    elif "soubreny" in normalized:
        attrs["line"] = "soubreny"
    elif "urban" in normalized:
        attrs["line"] = "urban"
    elif "d-light" in raw_lower or "d light" in normalized:
        attrs["line"] = "d_light"
    elif "windproof" in normalized:
        attrs["line"] = "windproof"
    elif "unique" in normalized:
        attrs["line"] = "unique"
    elif "replica" in normalized or "レプリカ" in raw_lower:
        attrs["line"] = "replica"
    elif any(pat in normalized for pat in ["armor", "vo day", "vỏ dày"]) or "アーマー" in raw_lower:
        attrs["line"] = "armor"
    elif "slim" in normalized or "スリム" in raw_lower:
        attrs["line"] = "slim"

    # 4. Nhận diện Chất liệu (Material)
    if any(m in normalized for m in ["son mai", "sơn mài", "urushi", "lacquer"]) or any(m in raw_lower for m in ["漆", "本漆"]):
        attrs["material"] = "son_mai"
    elif any(m in normalized for m in ["sterling silver", "bac khoi", "sterling", "925"]) or any(m in raw_lower for m in ["純銀", "スターリング"]):
        attrs["material"] = "sterling_silver"
    elif any(m in normalized for m in ["bac", "silver", "ma bac", "sp"]) or any(m in raw_lower for m in ["銀", "シルバー", "銀製"]):
        attrs["material"] = "silver"
    elif any(m in normalized for m in ["solid gold", "vang khoi", "18k", "14k"]) or any(m in raw_lower for m in ["金無垢", "18金"]):
        attrs["material"] = "solid_gold"
    elif any(m in normalized for m in ["boc vang", "ma vang", "gold plated", "gp", "vang"]) or any(m in raw_lower for m in ["金", "ゴールド", "金製"]):
        attrs["material"] = "gold"
    elif any(m in normalized for m in ["brass", "barass", "dong thau", "đồng thau", "dong", "đồng"]) or any(m in raw_lower for m in ["真鍮", "ブラス"]):
        attrs["material"] = "brass"

    # 5. Nhận diện Màu sắc (Color)
    if any(c in normalized for c in ["xanh la", "xanh luc", "green"]) or "緑" in raw_lower:
        attrs["color"] = "green"
    elif any(c in normalized for c in ["xanh duong", "xanh bien", "blue", "navy"]) or "青" in raw_lower:
        attrs["color"] = "blue"
    elif any(c in normalized for c in ["do", "red"]) or "赤" in raw_lower:
        attrs["color"] = "red"
    elif any(c in normalized for c in ["den", "black"]) or "黒" in raw_lower:
        attrs["color"] = "black"
    elif any(c in normalized for c in ["nau", "brown"]) or "茶" in raw_lower:
        attrs["color"] = "brown"

    # 6. Nhận diện Hoàn thiện (Finish)
    if any(f in normalized for f in ["xuoc", "hairline", "brushed"]):
        attrs["finish"] = "brushed"
    elif any(f in normalized for f in ["caro", "guilloche", "o vuong"]):
        attrs["finish"] = "guilloche"
    elif any(f in normalized for f in ["van ke", "ke soc", "stripes", "lines"]):
        attrs["finish"] = "lines"

    # 7. Nhận diện Tình trạng (Condition) từ mô tả chính (Việt + Nhật)
    if any(pat in raw_lower for pat in ["未着火", "デッドストック"]):
        attrs["cosmetic_condition"] = "Mới (NOS/Chưa lên lửa)"
    elif any(pat in raw_lower for pat in ["美品", "極美品"]):
        attrs["cosmetic_condition"] = "Rất đẹp (Sưu tầm/Like new)"
    elif any(pat in raw_lower for pat in ["着火確認", "動作品"]):
        attrs["cosmetic_condition"] = "Đã thử lửa / Cháy tốt"
    elif any(pat in raw_lower for pat in ["ジャンク"]):
        attrs["cosmetic_condition"] = "Junk / Xác / Hư hỏng"
    elif any(pat in raw_lower for pat in ["現状品"]):
        attrs["cosmetic_condition"] = "Hiện trạng / Chưa kiểm tra"
    elif any(pat in raw_lower for pat in ["中古"]):
        attrs["cosmetic_condition"] = "Đã qua sử dụng"
    elif any(pat in normalized for pat in ["qua dung", "da qua su dung", "da qua dung", "used", "xai roi", "hang luot", "luot", "cu"]):
        attrs["cosmetic_condition"] = "Đã qua sử dụng"
    elif any(pat in normalized for pat in ["chua len lua", "moi 100%", "nguyen seal", "chua qua su dung", "chua xai", "nos", "new", "moi"]):
        attrs["cosmetic_condition"] = "Mới (NOS/Chưa lên lửa)"
    elif any(pat in normalized for pat in ["like new", "likenew", "99%", "98%", "dep", "keng", "long lanh", "suu tam"]):
        attrs["cosmetic_condition"] = "Rất đẹp (Sưu tầm/Like new)"
    elif any(pat in normalized for pat in ["xuoc nhe", "can nhe", "tray nhe"]):
        attrs["cosmetic_condition"] = "Xước dăm nhẹ"
    elif any(pat in normalized for pat in ["can mop", "mop", "xuoc nhieu"]):
        attrs["cosmetic_condition"] = "Cấn móp / Trầy xước"

    return attrs


def parse_quick_calc_input(text: str, rate: int = 165) -> dict[str, Any] | None:
    """Nhận diện câu lệnh hoặc con số tính nhẩm nhanh giá bid trên sàn Yahoo (Quick JPY Bid Calculator).
    
    Ví dụ:
    - '15000Y', '15.000Y', '15000 yen', '15000 jpy', '¥15000', '15000円'
    - 'calc 15000', 'tinh 15000', 'gia 15000', 'bid 15000'
    - '15k jpy', '20k yen'
    - '15000' (nếu là số nguyên từ 1.000 đến 1.000.000 không có từ khóa tên quẹt)
    """
    raw = normalize_unicode(text).strip()
    norm = strip_vietnamese_accents(raw).lower()
    
    # Nếu có chứa từ khóa tên hãng quẹt thì không phải lệnh tính nhẩm đơn thuần
    brand_keywords = [
        "dupont", "zippo", "ronson", "dunhill", "cartier", "colibri", "maruman",
        "sarome", "penguin", "givenchy", "son mai", "sơn mài", "line", "ligne",
        "デュポン", "ロンソン", "ジッポー", "ダンヒル"
    ]
    if any(bk in norm or bk in raw.lower() for bk in brand_keywords):
        return None

    # Bỏ tiền tố nếu có: calc, tinh, gia, bid
    prefix_pattern = r"^(?:calc|tinh|gia|bid|doigiayen|doi)\s+"
    m_pref = re.match(prefix_pattern, norm)
    token = norm
    if m_pref:
        token = norm[m_pref.end():].strip()

    # Kiểm tra dạng 15k jpy / 15k yen
    m_k_yen = re.match(r"^(\d+)\s*k\s*(?:y|yen|jpy|円)?$", token)
    if m_k_yen:
        amt_jpy = int(m_k_yen.group(1)) * 1000
    else:
        # Thử parse bằng parse_jpy_amount
        amt_jpy, err = parse_jpy_amount(token)
        if err or amt_jpy is None:
            # Kiểm tra xem có dạng ¥15000 hay 15000円
            clean_num = token.replace("¥", "").replace("円", "").replace("jpy", "").replace("yen", "").replace("y", "").strip()
            amt_jpy, err2 = parse_jpy_amount(clean_num)
            if err2 or amt_jpy is None:
                return None

    # Giới hạn số tiền hợp lý cho quẹt đấu giá: 100 JPY đến 5.000.000 JPY
    if amt_jpy < 100 or amt_jpy > 5000000:
        return None

    # Nếu chỉ là số trần trụi (ví dụ '15000') mà không có ký hiệu tiền tệ hoặc prefix calc/tinh:
    # Chỉ nhận diện nếu số >= 1000 (đúng tầm giá đấu quẹt)
    has_explicit_currency = any(s in norm for s in ["y", "yen", "jpy", "¥", "円", "k"]) or bool(m_pref)
    if not has_explicit_currency and amt_jpy < 1000:
        return None

    effective_rate = rate if rate > 0 else 165
    base_vnd = amt_jpy * effective_rate
    # Phí ship quốc tế + kho dịch vụ tạm tính: ~180.000 - 200.000 đ/cây
    shipping_fee_vnd = 200000
    total_landing_vnd = base_vnd + shipping_fee_vnd

    return {
        "amount_jpy": amt_jpy,
        "rate": effective_rate,
        "base_vnd": base_vnd,
        "shipping_fee_vnd": shipping_fee_vnd,
        "total_landing_vnd": total_landing_vnd,
    }


def parse_data_input(raw_input: str) -> ParseResult:
    """Phân tích lệnh /data <mô tả> <giá> [| field=value ...]."""
    text = raw_input.strip()
    if text.startswith("/data"):
        text = text[len("/data"):].strip()

    if not text:
        return ParseResult(
            is_valid=False,
            needs_confirmation=True,
            confirmation_type="missing_all",
            confirmation_message="Vui lòng nhập cú pháp: /data <mô tả quẹt> <giá JPY>\nVí dụ: /data dupont sơn mài 1 line xanh lá có box 13.400Y",
            error_message="Chưa có dữ liệu nhập.",
        )

    # Tách các trường phân tách bởi dấu pipe '|'
    parts = [p.strip() for p in text.split("|") if p.strip()]
    main_section = parts[0]
    pipe_sections = parts[1:] if len(parts) > 1 else []

    desc, amount, currency, err, suggestions, candidate_price = extract_price_and_desc_multi(main_section)

    # Tự động trích xuất link Yahoo hoặc mã đấu giá từ phần mô tả để làm sạch tiêu đề
    extracted_aid = None
    extracted_url = None
    if desc:
        m_url = re.search(r"(https?://\S+)", desc)
        if m_url:
            found_url = m_url.group(1)
            aid = extract_yahoo_auction_id(found_url)
            if aid:
                extracted_aid = aid
                extracted_url = found_url
                desc = desc.replace(found_url, "").strip()
        else:
            m_tag = re.search(r"(#([a-zA-Z]\d{8,11}))\b", desc)
            if m_tag:
                extracted_aid = m_tag.group(2)
                extracted_url = f"https://page.auctions.yahoo.co.jp/jp/auction/{extracted_aid}"
                desc = desc.replace(m_tag.group(1), "").strip()

        desc = re.sub(r"\s+", " ", desc).strip()

    if not desc and extracted_aid:
        desc = f"Quẹt Yahoo #{extracted_aid}"

    if amount is None:
        # Nếu thiếu giá hoặc giá viết tắt cần làm rõ
        if not desc:
            return ParseResult(
                is_valid=False,
                needs_confirmation=True,
                confirmation_type="missing_desc",
                confirmation_message="Chỉ có giá hoặc chưa có tên/mô tả quẹt. Vui lòng nhập tên quẹt.",
                error_message=err or "Thiếu mô tả",
            )

        attrs = parse_attributes(desc)
        brand_fmt = attrs["brand"].capitalize() if attrs["brand"] != "unknown" else ""
        line_fmt = attrs["line"].replace("_", " ").title() if attrs["line"] != "unknown" else ""
        hdr = " · ".join(p for p in [brand_fmt, line_fmt] if p) or desc

        if suggestions:
            return ParseResult(
                is_valid=False,
                raw_desc=desc,
                display_name=desc,
                currency=currency if currency != "AMBIGUOUS" else "JPY",
                brand=attrs["brand"],
                line=attrs["line"],
                size_submodel=attrs["size_submodel"],
                material=attrs["material"],
                finish=attrs["finish"],
                color=attrs["color"],
                edition=attrs["edition"],
                box=attrs["box"],
                papers=attrs["papers"],
                accessories_note=attrs["accessories_note"],
                cosmetic_condition=attrs["cosmetic_condition"],
                functional_state=attrs["functional_state"],
                needs_confirmation=True,
                confirmation_type="clarify_price",
                confirmation_message=(
                    f"Tôi đã nhận diện: <b>{hdr}</b>\n"
                    f"Giá nhập dạng viết tắt: <code>{candidate_price}</code>.\n"
                    f"Anh muốn lưu theo mức giá và loại tiền nào dưới đây?"
                ),
                suggested_prices=[s["amount"] for s in suggestions],
                suggested_currency_prices=suggestions,
                raw_price_token=candidate_price,
                error_message=err or "",
            )

        return ParseResult(
            is_valid=False,
            raw_desc=desc,
            display_name=desc,
            brand=attrs["brand"],
            line=attrs["line"],
            needs_confirmation=True,
            confirmation_type="missing_price",
            confirmation_message=f"Tôi đã nhận diện mô tả: '{desc}'. {err}",
            raw_price_token=candidate_price,
            error_message=err or "",
        )

    if not desc:
        return ParseResult(
            is_valid=False,
            amount_jpy=amount,
            currency=currency,
            needs_confirmation=True,
            confirmation_type="missing_desc",
            confirmation_message=f"Tôi hiểu giá là {amount:,} {currency} nhưng chưa có mô tả quẹt. Anh vui lòng nhập tên quẹt.",
            error_message="Chỉ có giá, không có mô tả.",
        )

    # Phân tích thuộc tính từ mô tả
    attrs = parse_attributes(desc)

    # Khởi tạo kết quả
    result = ParseResult(
        is_valid=True,
        amount_jpy=amount,
        currency=currency,
        raw_desc=desc,
        display_name=desc,
        brand=attrs["brand"],
        line=attrs["line"],
        size_submodel=attrs["size_submodel"],
        material=attrs["material"],
        finish=attrs["finish"],
        color=attrs["color"],
        edition=attrs["edition"],
        box=attrs["box"],
        papers=attrs["papers"],
        accessories_note=attrs["accessories_note"],
        cosmetic_condition=attrs["cosmetic_condition"],
        functional_state=attrs["functional_state"],
        auction_id=extracted_aid,
        source_url=extracted_url,
    )

    # Kiểm tra trường hợp mơ hồ 'full boc'
    if attrs.get("is_ambiguous_box"):
        result.needs_confirmation = True
        result.confirmation_type = "ambiguous_box"
        result.confirmation_message = (
            f"Tôi hiểu giá là {amount:,} yên.\n"
            f"{result.brand.capitalize()} · {result.line.replace('_', ' ').title()} · "
            f"{result.material.replace('_', ' ').title()} · {result.color.capitalize()}\n"
            f"Cụm 'full boc' ở đây anh muốn ghi nhận thế nào?"
        )

    # Phân tích các trường sau dấu pipe
    for sec in pipe_sections:
        if "=" in sec:
            key, val = sec.split("=", 1)
            key = key.strip().lower()
            val = val.strip()
        elif ":" in sec:
            key, val = sec.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
        else:
            continue

        norm_key = strip_vietnamese_accents(key)
        if norm_key in ["tinh trang", "condition"]:
            result.cosmetic_condition = val
            result.functional_state = val
        elif norm_key in ["ngay", "date"]:
            # Chuẩn hóa ngày đấu YYYY-MM-DD
            result.auction_date = val
        elif norm_key in ["phi nhat", "phi jpy", "fee_jpy"]:
            fee_val, _ = parse_jpy_amount(val)
            if fee_val:
                result.fee_jpy = fee_val
        elif norm_key in ["phi vn", "phi vnd", "fee_vnd"]:
            val_clean = re.sub(r"[^\d]", "", val)
            if val_clean:
                result.fee_vnd = int(val_clean)
        elif norm_key in ["ghi chu", "note"]:
            result.note = val
        elif norm_key in ["auction_id", "ma dau"]:
            result.auction_id = val
        elif norm_key in ["url", "link", "source_url"]:
            result.source_url = val
        elif norm_key in ["lo", "lot"]:
            result.is_lot = True
        elif norm_key in ["price_basis", "all in", "all_in"]:
            result.price_basis = "all_in"

    return result


def extract_yahoo_auction_id(text: str) -> str | None:
    """Trích xuất mã đấu giá (Auction ID) từ link Yahoo Auctions / Buyee / ZenMarket / Doorzo / FromJapan hoặc mã trực tiếp #f123..."""
    t = text.strip()
    # 1. Mã trực tiếp (ví dụ: #f1242609776 hoặc f1242609776)
    m_direct = re.match(r"^#?([a-zA-Z]\d{8,11})$", t)
    if m_direct:
        return m_direct.group(1)

    # 2. Các dạng link Yahoo và Proxy mua hộ
    patterns = [
        r"(?:auctions\.yahoo\.co\.jp/(?:jp/)?auction/|page\.auctions\.yahoo\.co\.jp/(?:jp/)?auction/)([a-zA-Z0-9]+)",
        r"(?:buyee\.jp/item/yahoo/auction/)([a-zA-Z0-9]+)",
        r"(?:zenmarket\.jp/.*[?&]itemCode=)([a-zA-Z0-9]+)",
        r"(?:doorzo\.com/.*(?:auction|item)/)([a-zA-Z0-9]+)",
        r"(?:fromjapan\.co\.jp/.*(?:auction|item)/)([a-zA-Z0-9]+)",
        r"(?:jauce\.com/auction/)([a-zA-Z0-9]+)",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return m.group(1)
    return None


async def fetch_yahoo_auction_info(auction_id: str) -> dict[str, Any]:
    """Fetch thông tin chi tiết phiên đấu Yahoo Auctions (tiêu đề, giá, trạng thái, phí ship, tình trạng, mô tả)."""
    import httpx
    import json
    clean_aid = extract_yahoo_auction_id(auction_id) or str(auction_id).strip().lstrip("#")
    url = f"https://auctions.yahoo.co.jp/jp/auction/{clean_aid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    info: dict[str, Any] = {
        "auction_id": clean_aid,
        "url": url,
        "title": "",
        "current_price_jpy": None,
        "status": "open",  # "open" hoặc "closed"
        "bids": 0,
        "end_time": "",
        "formatted_end_time": "",
        "conditionName": "",
        "description": "",
        "shipping_fee_jpy": None,
        "image_url": "",
        "images": [],
        "category_id": "",
        "category_path": [],
        "is_fetched": False,
    }
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                html = resp.text

                # 1. Thử parse qua dữ liệu cấu trúc __NEXT_DATA__ (Chính xác 100%)
                m_next = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
                if m_next:
                    try:
                        data = json.loads(m_next.group(1))
                        item = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("item", {}).get("detail", {}).get("item", {})
                        detail = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("item", {}).get("detail", {})
                        if item:
                            info["title"] = item.get("title", "").strip()
                            info["status"] = item.get("status", "open")
                            info["current_price_jpy"] = item.get("price")
                            info["bids"] = item.get("bids", 0)
                            info["end_time"] = item.get("endTime", "")
                            info["formatted_end_time"] = item.get("formattedEndTime", "")
                            info["conditionName"] = item.get("conditionName", "")

                            cat_info = item.get("category") or detail.get("category") or {}
                            if isinstance(cat_info, dict):
                                path = cat_info.get("path", [])
                                if isinstance(path, list):
                                    info["category_path"] = path
                                    if path:
                                        info["category_id"] = str(path[-1].get("id") or "")

                            desc_val = item.get("description", "")
                            if isinstance(desc_val, list):
                                info["description"] = "\n".join(str(d) for d in desc_val if d)
                            else:
                                info["description"] = str(desc_val or "")

                            ship_methods = item.get("shipping", {}).get("methods", [])
                            if ship_methods and isinstance(ship_methods, list):
                                first_fee = ship_methods[0].get("shippingFee")
                                if isinstance(first_fee, int):
                                    info["shipping_fee_jpy"] = first_fee

                            imgs = item.get("img") or item.get("images", [])
                            if imgs and isinstance(imgs, list):
                                img_list = []
                                for im in imgs:
                                    if isinstance(im, dict) and im.get("image"):
                                        img_list.append(im.get("image"))
                                    elif isinstance(im, str) and im.startswith("http"):
                                        img_list.append(im)
                                info["images"] = img_list
                                if img_list:
                                    info["image_url"] = img_list[0]

                            info["is_fetched"] = bool(info["title"])
                    except Exception:
                        pass

                # 2. Fallback nếu không có __NEXT_DATA__
                if not info["is_fetched"]:
                    cat_matches = re.findall(r'href="[^"]*(?:category/list/|list5/)(\d+)[^"]*"[^>]*>([^<]+)</a>', html)
                    if cat_matches:
                        info["category_path"] = [{"id": cid, "name": cname.strip()} for cid, cname in cat_matches]
                        info["category_id"] = cat_matches[-1][0]
                    m_og = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html)
                    if m_og:
                        raw_title = m_og.group(1)
                    else:
                        m_title = re.search(r'<title>([^<]+)</title>', html)
                        raw_title = m_title.group(1) if m_title else ""
                    
                    clean_t = raw_title.replace(" - Yahoo!オークション", "").replace(" - ヤフオク!", "").strip()
                    info["title"] = clean_t

                    m_price = re.search(r'class=["\'][^"\']*Price__value[^"\']*["\'][^>]*>([\d,]+)\s*円', html)
                    if not m_price:
                        m_price = re.search(r'(?:現在価格|即決|価格|落札価格)[^\d]*([\d,]+)\s*円', html)
                    if m_price:
                        p_num = m_price.group(1).replace(",", "")
                        if p_num.isdigit():
                            info["current_price_jpy"] = int(p_num)

                    if any(c in html for c in ["オークションは終了しました", "落札者", "終了日時"]):
                        info["status"] = "closed"

                    all_imgs = re.findall(r'https://auctions\.c\.yimg\.jp/images\.auctions\.yahoo\.co\.jp/image/[^"\'\s<>]+', html)
                    if all_imgs:
                        seen = set()
                        uniq_imgs = []
                        for u in all_imgs:
                            if u not in seen:
                                seen.add(u)
                                uniq_imgs.append(u)
                        info["images"] = uniq_imgs[:10]
                        if uniq_imgs and not info.get("image_url"):
                            info["image_url"] = uniq_imgs[0]
                    else:
                        m_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
                        if m_img:
                            info["image_url"] = m_img.group(1)
                            info["images"] = [m_img.group(1)]

                    info["is_fetched"] = bool(clean_t)
    except Exception:
        pass

    return info


# ==============================================================================
# BỘ XÁC MINH LOT BẬT LỬA YAHOO CHUYÊN SÂU (STRICT LOT VERIFICATION ENGINE)
# ==============================================================================

_NON_LIGHTER_EXCLUDE_RE = re.compile(
    r"(アイコス|iqos|iluma|イルマ|glo|グロー|ploom|プルーム|ベイプ|vape|電子タバコ|電子たばこ|加熱式タバコ|加熱式|ポッド|relx|"
    r"ドクターベイプ|dr\.vape|myblu|juul|シーシャ|shisha|リキッド|ニコチン|アトマイザー|"
    r"靴下|ソックス|時計|ウォッチ|腕時計|バッグ|財布|コインケース|小銭入れ|名刺入れ|カードケース|パスケース|マネークリップ|"
    r"ネクタイ|カフス|タイピン|タイバー|香水|フレグランス|洋酒|古酒|ウイスキー|ブランデー|"
    r"万年筆|ボールペン|ペン先|シャツ|ジャケット|コート|シューズ|ベルト|マフラー|スカーフ|ハンカチ|スーツ|"
    # 'リング' (nhẫn) không được khớp nhầm 'スターリング' (bạc sterling), 'Oリング/オーリング' (gioăng), 'スプリング' (lò xo)
    r"メガネ|眼鏡|サングラス|めがね|(?<!スター)(?<!オー)(?<![OoＯｏ])(?<!スプ)リング|指輪|ネックレス|ブレスレット|ペンダント|ピアス|イヤリング|ブローチ|"
    r"キーリング|キーケース|キーホルダー|灰皿|アッシュトレイ|シガーカッター|葉巻カッター|熱収縮チューブ|ハンダ|配線修理)",
    re.IGNORECASE,
)

# Bật lửa nhựa rẻ tiền dùng 1 lần, bật lửa khò bếp gas dài, đồ tiện lợi 100 yên
_DISPOSABLE_TRASH_RE = re.compile(
    r"(使い捨て|百円ライター|100円ライター|チャッカマン|ガストーチ|ミニトーチ|"
    r"クッキングバーナー|トーチバーナー|点火棒|"
    r"\btokai\b|東海ライター|\bbic\b|\bcricket\b|\bclipper\b)",
    re.IGNORECASE,
)

_LIGHTER_INDICATOR_RE = re.compile(
    r"(ライター|zippo|ジッポ|dupont|デュポン|dunhill|ダンヒル|cartier|カルティエ|ronson|ロンソン|maruman|マルマン|givenchy|ジバンシ|colibri|コリブリ|sarome|サロメ|オイルライター|ガスライター|喫煙具|着火|火花|rollagas|gatsby|ligne)",
    re.IGNORECASE,
)


def is_genuine_lighter_item(title: str, description: str = "") -> bool:
    """Kiểm tra nghiêm ngặt xem sản phẩm (từ Yahoo Auctions, eBay) có đúng là BẬT LỬA hay không.
    
    Loại bỏ 100% thuốc lá điện tử (IQOS, Iluma, Glo, Ploom, Vape), hàng thời trang (ví, thắt lưng, bút, đồng hồ),
    phụ kiện đơn thuần (chỉ bán bao da/case, hộp rỗng, đá lửa, gạt tàn), và bật lửa nhựa dùng 1 lần 100 yên.
    """
    text = f"{title} {description}".strip()
    if not text:
        return False

    # 1. Bắt buộc loại bỏ thuốc lá điện tử (IQOS, vape, pod) và hàng thời trang ngoài quẹt
    if _NON_LIGHTER_EXCLUDE_RE.search(text):
        return False

    # 1.5. Loại bỏ bật lửa nhựa rẻ tiền 100 yên / dùng 1 lần (trừ khi có thương hiệu cao cấp đi kèm)
    if _DISPOSABLE_TRASH_RE.search(text):
        has_premium_brand = bool(re.search(r"(?:dupont|デュポン|dunhill|ダンヒル|zippo|ジッポ|cartier|カルティエ)", text, re.IGNORECASE))
        if not has_premium_brand:
            return False
        return False

    # 2. Loại bỏ trường hợp phụ kiện đơn thuần (bao da/case, gạt tàn, hộp rỗng, dao cắt xì gà) khi không có bật lửa thật đi kèm
    is_acc_word = bool(re.search(r"(?:ケース|カバー|ホルダー|スリーブ|ポーチ|灰皿|シガーカッター|空箱|元箱のみ|箱のみ)", text, re.IGNORECASE))
    if is_acc_word:
        # Nếu có từ chỉ phụ kiện, bắt buộc phải có từ chỉ bật lửa thật sự ("ライター", "オイルライター", "ガスライター", "ライター本体", "着火")
        has_actual_lighter = bool(re.search(r"(?:ライター|オイルライター|ガスライター|ライター本体|着火)", text, re.IGNORECASE))
        if not has_actual_lighter:
            return False
        # Nếu là caseのみ / 箱のみ thì dù có chữ zippo/dupont cũng loại
        if re.search(r"(?:ケースのみ|カバーのみ|ホルダーのみ|空箱|箱のみ|元箱のみ|ポーチのみ)", text, re.IGNORECASE):
            if not re.search(r"ライター本体", text, re.IGNORECASE):
                return False

    # 3. Bắt buộc phải có chỉ báo bật lửa (Whitelist)
    if not _LIGHTER_INDICATOR_RE.search(text):
        return False

    return True


def is_genuine_lighter_lot(title: str, description: str = "") -> bool:
    """Kiểm tra nghiêm ngặt: CHỈ CHẤP NHẬN LOT BẬT LỬA (từ 2 cây trở lên), LOẠI BỎ 100% CÂY LẺ.
    
    Quy tắc:
    1. Bắt buộc vượt qua is_genuine_lighter_item (phải là bật lửa, không phải IQOS, vape, phụ kiện hay hàng thời trang).
    2. Bóc tách số lượng và dấu hiệu gom lô:
       - Nếu count == 1 hoặc có dấu hiệu bán 1 cây đơn lẻ -> FALSE (LOẠI BỎ HÀNG LẺ).
       - Nếu count >= 2 -> TRUE (LOT HỢP LỆ).
       - Nếu có từ khóa lot rõ ràng (まとめ, まとめ売り, まとめて, 大量, セット, 詰め合わせ, アソート, おまとめ)
         và không có từ khóa phủ định bán lẻ -> TRUE.
       - Mọi trường hợp còn lại (hàng 1 cây không có dấu hiệu lot) -> FALSE.
    """
    if not is_genuine_lighter_item(title, description):
        return False

    full_text = f"{title} {description}".strip()

    # 1. Kiểm tra dấu hiệu bán lẻ 1 cây rõ rệt (Single item indicators)
    if _SINGLE_CHOICE_FROM_PHOTO_RE.search(full_text):
        return False
    if re.search(r"(?:1本のみ|1点のみ|単品|単体|1個のみ|本体のみ|1本出品|1点出品)", full_text):
        if not re.search(r"(?:まとめ|セット|大量)", full_text):
            return False

    # 2. Bóc tách số lượng cây thực tế bằng engine chuyên sâu
    count, is_multiple_confirmed, reason = extract_actual_lighter_count(title, description)

    if count is not None:
        if count >= 2:
            return True
        if count == 1:
            return False

    if is_multiple_confirmed:
        return True

    # 3. Kiểm tra các từ khóa lot tích cực
    has_lot_kw = any(k in full_text for k in [
        "まとめ売り", "まとめて", "大量まとめ", "大量", "詰め合わせ", "詰合せ",
        "一括", "アソート", "アソートセット", "おまとめ", "まとめ"
    ])

    # Kiểm tra từ "セット" (set) nếu đi kèm từ 2 trở lên hoặc có từ khóa set
    has_set_kw = bool(re.search(r"(?:[2-9]|\d{2,})\s*点セット", full_text)) or "セット" in full_text

    if has_lot_kw or has_set_kw:
        # Đảm bảo không bị bán tách lẻ
        has_split = bool(re.search(r"バラ売り", full_text))
        has_no_split = bool(re.search(r"バラ売り(不可|はできません|はいたしません|NG|しません|出来ません)", full_text))
        if has_split and not has_no_split:
            return False
        return True

    # Nếu chỉ là 1 cây bình thường (không có từ khóa lot nào) -> LOẠI BỎ HÀNG LẺ
    return False


# Chỉ bán phụ kiện, vỏ hộp rỗng, linh kiện/ruột
_ACCESSORY_ONLY_RE = re.compile(
    r"(?:箱のみ|ケースのみ|空箱|元箱のみ|木箱のみ|インサイドユニット|インナーユニット|ユニットのみ|部品のみ|パーツのみ|フリントのみ|発火石のみ|替え芯のみ|ガスボンベのみ|ガス缶のみ|ガスボンベ|発火石|替え芯|ウィック)",
    re.IGNORECASE,
)

# Bán chọn từng món / giá tính riêng từng cây
_PER_PIECE_CHOICE_RE = re.compile(
    r"(?:どれか1つ|どれか1点|お選び(?:ください|頂|願)?|1つお選び|ご希望の(?:番号|品|種類|カラー|ものを)|好きなものを|"
    r"(?:各1個|各1本|各1点|1個|1本|1点|単品)(?:あたり)?(?:の)?(?:価格|値段|金額|お値段)|単品価格)",
    re.IGNORECASE,
)

# Bán 1 cây đơn lẻ hoặc chụp nhiều cây nhưng mô tả nói chỉ bán 1 cây chỉ định
_SINGLE_CHOICE_FROM_PHOTO_RE = re.compile(
    r"(?:1点のみの出品|1本のみの出品|出品物は1点|商品は1本|赤丸の1点|指定の1点|画像のうち1点|写真のうち1点|単品|単体|1本のみ|1点のみ|本体のみ)",
    re.IGNORECASE,
)

_LOT_POSITIVE_KEYWORDS = [
    "まとめ売り", "まとめて", "大量まとめ", "大量", "詰め合わせ", "詰合せ", "一括", "アソート", "アソートセット"
]

# Cụm gom ship / mua nhiều phiên / người bán đăng nhiều phiên: KHÔNG phải dấu hiệu bán chung 1 lô
_NOT_LOT_PHRASE_RE = re.compile(
    r"(?:お?まとめ(?:て)?\s*(?:買い|がい|取引|発送|配送|購入|落札|割引|割|同梱)|(?:複数|多数)\s*出品)"
)

# Từ bán gom bổ sung: 'まとめ' / 'おまとめ' đứng riêng, 多数, 色々, いろいろ, 'N品おまとめ / N品セット'
_EXTRA_LOT_KEYWORD_RE = re.compile(r"(?:まとめ|多数|色々|いろいろ|\d+\s*品\s*(?:お?まとめ|セット))")

# Chỉ bán hộp / ruột / linh kiện (không có bật lửa hoàn chỉnh)
_BOX_UNIT_ONLY_RE = re.compile(
    r"(?:空箱|箱のみ|ケースのみ|元箱のみ|木箱のみ|カバーのみ|ポーチのみ|インサイドユニット|インナーユニット|ユニットのみ|"
    r"部品のみ|パーツのみ|フリントのみ|発火石のみ|替え芯のみ|ガスボンベのみ|ガス缶のみ)"
)

# Số lượng đồ tiêu hao (gas, dầu, đá lửa, bấc): không được tính là số cây bật lửa
_CONSUMABLE_QTY_RE = re.compile(
    r"(?:ガスボンベ|ガス缶|ガス|オイル缶|オイル|フリント|発火石|着火石|石|替え芯|芯|ウィック)\s*[:：xX×]?\s*\d+\s*(?:本入|個入|本|個|点|粒|缶|セット)"
)


# Chủ thể là phụ kiện (ライターケース, ライター オイル, 化粧箱 5個, ポーチ まとめ...): khi đó 'まとめ' là gom phụ kiện, không phải gom bật lửa
_ACCESSORY_SUBJECT_RE = re.compile(
    r"(?:ライター\s*(?:ケース|カバー|ポーチ|オイル|ガス(?!ライター)|用)|"
    r"(?:ケース|カバー|ポーチ|化粧箱|空き箱|空箱|元箱|箱|オイル缶|オイル|インナー|ユニット|フリント|着火石|発火石|ガスボンベ|ボンベ|替え芯|芯)\s*"
    r"(?:\d+\s*(?:点|個|本|缶|箱|枚|セット)|お?まとめ|セット))"
)


def _has_lot_keyword(text: str) -> bool:
    """Có từ khóa bán gom nhiều cây không (sau khi bỏ các cụm gom ship / nhiều phiên như まとめ買い, おまとめ取引, 複数出品).

    Từ bổ sung ('まとめ' đứng riêng, 多数, 色々...) chỉ tính khi chủ thể tiêu đề không phải phụ kiện.
    """
    t = _NOT_LOT_PHRASE_RE.sub(" ", text or "")
    if any(k in t for k in _LOT_POSITIVE_KEYWORDS):
        return True
    return bool(_EXTRA_LOT_KEYWORD_RE.search(t)) and not _ACCESSORY_SUBJECT_RE.search(t)

_BRAND_PATTERNS = [
    ("Dupont", re.compile(r"(dupont|デュポン|st dupont|s\.t\. dupont)", re.IGNORECASE)),
    ("Zippo", re.compile(r"(zippo|ジッポ|ジッポー)", re.IGNORECASE)),
    ("Dunhill", re.compile(r"(dunhill|ダンヒル)", re.IGNORECASE)),
    ("Cartier", re.compile(r"(cartier|カルティエ)", re.IGNORECASE)),
    ("Ronson", re.compile(r"(ronson|ロンソン)", re.IGNORECASE)),
    ("Maruman", re.compile(r"(maruman|マルマン)", re.IGNORECASE)),
    ("Givenchy", re.compile(r"(givenchy|ジバンシ)", re.IGNORECASE)),
    ("Colibri", re.compile(r"(colibri|コリブリ)", re.IGNORECASE)),
    ("Sarome", re.compile(r"(sarome|サロメ)", re.IGNORECASE)),
]


def extract_actual_lighter_count(title: str, description: str = "") -> tuple[int | None, bool, str]:
    """Bóc tách số lượng cây bật lửa thực tế (tách biệt khỏi năm sản xuất, bản giới hạn, hộp, phụ kiện).
    
    Trả về: (lighter_count, is_multiple_confirmed, reason_note)
    """
    full_text = f"{title} {description}".strip()
    t_clean = full_text

    # 1. Bóc tách số lượng giả:
    # - Phiên bản giới hạn (ví dụ: 1000個限定, 限定1000個, 500本限定)
    t_clean = re.sub(r"(?:限定\s*\d+\s*(?:個|本|点|丁|台|セット)|(?:\d+)\s*(?:個|本|点|丁|台|セット)?\s*限定(?:品|モデル)?)", " ", t_clean)
    # - Năm sản xuất / Replica (1932, 1933, 1935, 1941, 1937, 1980, 1990, 2000...)
    t_clean = re.sub(r"\b(19\d\d|20\d\d)\b", " ", t_clean)
    # - Dòng model Line 1, Line 2
    t_clean = re.sub(r"(?:ライン|line|ligne)\s*[12]", " ", t_clean, flags=re.IGNORECASE)
    # - Số phụ kiện/hộp/gas/đá
    t_clean = re.sub(r"(?:箱|ケース|ボックス|元箱|空箱)\s*\d+\s*(?:個|点|つ)", " ", t_clean)
    t_clean = re.sub(r"(?:ガス|ガスボンベ|オイル|オイル缶)\s*\d+\s*(?:本|缶)", " ", t_clean)
    t_clean = re.sub(r"(?:フリント|石|発火石|替え芯)\s*\d+\s*(?:個|点|粒|個入)", " ", t_clean)

    # 2. Kiểm tra nếu có breakdown chỉ bán 1 cây bật lửa (ví dụ: "3点セット: ライター1点、元箱、オイル缶" hoặc "ライター1本")
    m_single_lighter = re.search(r"(?:ライター|本体|zippo|ジッポ|デュポン|ダンヒル)\s*[:：\-]?\s*1\s*(?:本|個|点|丁|台)", full_text, re.IGNORECASE)
    has_explicit_lot = any(k in title for k in _LOT_POSITIVE_KEYWORDS)
    if m_single_lighter and not has_explicit_lot:
        return 1, False, "Chỉ có 1 cây bật lửa trong phiên bán (kèm phụ kiện/hộp)"

    # Nếu tiêu đề có dạng "X点セット" nhưng kèm phụ kiện và chỉ có 1 bật lửa
    has_set = re.search(r"(\d+)\s*点セット", title)
    has_accessories = re.search(r"(?:元箱|箱|ケース|オイル|ガス|フリント|石|保証書|説明書)", full_text)
    if has_set and has_accessories and not any(k in title for k in ["まとめ", "大量", "詰め合わせ", "本まとめ"]):
        # Nếu có từ 1 cây hoặc không có số lượng cây bật lửa rõ ràng
        m_lighter_cnt = re.search(r"(?:ライター|zippo|ジッポ|デュポン|ダンヒル)\s*[:：\-]?\s*(\d+)\s*(?:本|個|点)", full_text, re.IGNORECASE)
        if m_lighter_cnt and int(m_lighter_cnt.group(1)) == 1:
            return 1, False, "Bộ combo phụ kiện chỉ gồm 1 cây bật lửa"
        elif not m_lighter_cnt:
            # Ví dụ: "ZIPPO 1996 オイルライター フリント オイル缶 3点セット"
            # Chỉ có 1 bật lửa Zippo + 2 phụ kiện (flint + oil)
            acc_matches = len(re.findall(r"(?:箱|ケース|オイル|ガス|フリント|石|説明書|保証書)", full_text))
            set_num = int(has_set.group(1))
            if set_num - acc_matches <= 1:
                return 1, False, "Bộ combo phụ kiện chỉ có 1 cây bật lửa"

    # 3. Tìm số lượng bật lửa rõ ràng
    # Ưu tiên tìm số lượng gắn liền với tên sản phẩm / bật lửa
    m_direct_lighters = re.findall(r"(?:ライター|オイルライター|ガスライター|zippo|ジッポ|デュポン|ダンヒル|cartier|カルティエ|ronson|ロンソン)\s*[:：\-]?\s*(\d+)\s*(?:本|個|点|丁|台)", t_clean, re.IGNORECASE)
    if m_direct_lighters:
        direct_counts = [int(x) for x in m_direct_lighters if 1 <= int(x) <= 500]
        if direct_counts:
            direct_max = max(direct_counts)
            if direct_max == 1:
                return 1, False, "Chỉ có 1 cây bật lửa"
            return direct_max, True, f"Xác nhận {direct_max} cây bật lửa"

    count_patterns = [
        r"(?:計|合計|総数)\s*(\d+)\s*(?:個|本|点|丁|台)",
        r"(\d+)\s*本セット",
        r"(\d+)\s*(?:個|本|点|丁|台)\s*(?:セット|まとめ|まとめて|売り)?",
        r"(\d+)\s*点セット",
        r"(\d+)\s*品\s*(?:お?まとめ|セット)",
        r"(?:lô|set|pack|combo)\s*(\d+)",
        r"(\d+)\s*(?:cây|chiec|chiếc|qua|cái|pcs|items)",
        r"(\d+)\s*個まとめて",
    ]

    detected_counts: list[int] = []
    for p in count_patterns:
        for m in re.finditer(p, t_clean, re.IGNORECASE):
            val = int(m.group(1))
            if 2 <= val <= 500:
                detected_counts.append(val)

    if detected_counts:
        max_count = max(detected_counts)
        return max_count, True, f"Xác nhận số lượng {max_count} cây bật lửa"

    # 4. Nếu không có số lượng cụ thể, kiểm tra dấu hiệu bán sỉ gom nhiều cây rõ ràng
    has_lot_keyword = _has_lot_keyword(full_text) or "複数" in _NOT_LOT_PHRASE_RE.sub(" ", full_text)
    has_no_split = bool(re.search(r"バラ売り(不可|はできません|はいたしません|NG|しません|出来ません)", full_text))

    if has_lot_keyword or has_no_split:
        return None, True, "Bán chung nhiều cây bật lửa (chưa rõ số lượng cụ thể)"

    return None, False, "Không phát hiện số lượng hoặc dấu hiệu bán lô"


def verify_yahoo_lighter_lot(info: dict[str, Any]) -> dict[str, Any]:
    """Kiểm tra và xác minh nghiêm ngặt một phiên đấu Yahoo Auctions có phải là LOT BẬT LỬA hợp lệ hay không.
    
    Quy tắc nghiệp vụ:
    - Bắt buộc bán chung từ 2 cây bật lửa trở lên và giá bid áp dụng cho cả lot.
    - Loại bỏ 100% hàng lẻ (1 cây kể cả fullbox, phụ kiện), chỉ bán hộp/ruột, bán chọn từng cây.
    - Không đủ bằng chứng -> UNCERTAIN (giữ nội bộ, không hiển thị/không gửi).
    """
    title = str(info.get("title") or "").strip()
    description = str(info.get("description") or "").strip()
    condition_raw = str(info.get("conditionName") or "").strip()
    status = str(info.get("status") or "open").lower().strip()
    bids = int(info.get("bids") or 0)
    price_jpy = info.get("current_price_jpy")
    if price_jpy is not None:
        try:
            price_jpy = int(price_jpy)
        except (ValueError, TypeError):
            price_jpy = 0
    else:
        price_jpy = 0

    shipping_fee_jpy = info.get("shipping_fee_jpy")
    if shipping_fee_jpy is not None:
        try:
            shipping_fee_jpy = int(shipping_fee_jpy)
        except (ValueError, TypeError):
            shipping_fee_jpy = 0

    url = str(info.get("url") or "")
    aid = str(info.get("auction_id") or "")
    image_url = str(info.get("image_url") or "")
    end_time = str(info.get("end_time") or "")

    full_text = f"{title} {description} {condition_raw}".strip()

    # Khởi tạo kết quả mặc định
    result: dict[str, Any] = {
        "is_verified_lot": False,
        "decision_code": "UNCERTAIN",
        "lighter_count": None,
        "badge_label": "CHƯA RÕ",
        "condition_label": "Chưa kiểm tra",
        "condition_code": "untested",
        "brands": [],
        "brand_summary": "Bật lửa",
        "evidence_reason": "",
        "title": title,
        "auction_id": aid,
        "current_price_jpy": price_jpy,
        "unit_price_jpy": None,
        "unit_price_vnd": None,
        "shipping_fee_jpy": shipping_fee_jpy,
        "unit_cost_with_ship_jpy": None,
        "unit_cost_with_ship_vnd": None,
        "bids": bids,
        "url": url,
        "image_url": image_url,
        "end_time": end_time,
        "remain_text": info.get("remain_text", ""),
        "remain_mins": info.get("remain_mins", -1),
        "category_id": str(info.get("category_id") or ""),
        "category_path": info.get("category_path") or [],
    }

    # Bóc tách thương hiệu
    detected_brands = []
    for b_name, b_re in _BRAND_PATTERNS:
        if b_re.search(full_text):
            detected_brands.append(b_name)
    result["brands"] = detected_brands
    if len(detected_brands) > 2:
        result["brand_summary"] = f"Hỗn hợp ({', '.join(detected_brands[:3])}...)"
    elif len(detected_brands) == 2:
        result["brand_summary"] = f"Hỗn hợp ({detected_brands[0]} + {detected_brands[1]})"
    elif len(detected_brands) == 1:
        result["brand_summary"] = detected_brands[0]
    else:
        result["brand_summary"] = "Bật lửa tổng hợp"

    # Bóc tách tình trạng
    if any(p in full_text for p in ["ジャンク", "junk", "部品取り", "現状品", "故障", "不動", "難あり", "サビ"]):
        result["condition_code"] = "junk"
        result["condition_label"] = "Junk / Xác / Lấy linh kiện"
    elif any(p in full_text for p in ["着火確認済み", "着火ok", "着火確認", "火花・着火ok", "動作確認済み", "着火良好"]):
        result["condition_code"] = "working"
        result["condition_label"] = "Hoạt động / Đã thử lửa"
    elif any(p in full_text for p in ["火花のみ", "火花ok", "火花確認"]):
        result["condition_code"] = "spark_only"
        result["condition_label"] = "Có tia lửa đá (chưa nạp gas)"
    elif any(p in full_text for p in ["動作未確認", "着火未確認", "未確認", "未チェック", "現状渡し", "動作確認は行っておりません", "保証できません"]):
        result["condition_code"] = "untested"
        result["condition_label"] = "Chưa kiểm tra (Chưa thử lửa)"
    else:
        result["condition_code"] = "untested"
        result["condition_label"] = "Chưa kiểm tra (Bán hiện trạng)"

    # 1. Kiểm tra trạng thái phiên
    if status == "closed" or any(c in full_text for c in ["オークションは終了しました", "落札者"]):
        result["decision_code"] = "CLOSED_AUCTION"
        result["evidence_reason"] = "Phiên đấu giá đã kết thúc hoặc đã tàn phiên"
        return result

    # 2. Kiểm tra nếu chưa tải được thông tin chi tiết hoặc bị lỗi mạng/chặn truy cập
    if info.get("is_fetched") is False:
        result["decision_code"] = "UNCERTAIN"
        result["evidence_reason"] = "Không tải được mô tả chi tiết hoặc bị chặn truy cập Yahoo"
        return result

    if not title:
        result["decision_code"] = "UNCERTAIN"
        result["evidence_reason"] = "Không có tiêu đề sản phẩm"
        return result

    # 2.5. Kiểm tra danh mục ngành hàng Yahoo Auctions (bắt buộc thuộc danh mục Bật lửa 26138 trong Đồ sưu tầm/cổ)
    cat_path = info.get("category_path")
    if cat_path and isinstance(cat_path, list):
        cat_ids = {str(c.get("id")) for c in cat_path if isinstance(c, dict) and c.get("id")}
        cat_names = [str(c.get("name") or "") for c in cat_path if isinstance(c, dict)]
        full_cat_str = " > ".join(cat_names)

        # Các ID danh mục bật lửa hợp lệ trên Yahoo Auctions:
        # 26138 (ライター - Root), 42530 (Zippo), 42531 (一般), 2084037475 (デュポン),
        # 2084037477 (ダンヒル), 2084037485 (カルティエ), 2084037487 (ロンソン)
        valid_lighter_cat_ids = {"26138", "42530", "42531", "2084037475", "2084037477", "2084037485", "2084037487"}
        is_in_lighter_cat = bool(cat_ids & valid_lighter_cat_ids) or ("ライター" in full_cat_str and "喫煙グッズ" in full_cat_str)

        if not is_in_lighter_cat:
            result["decision_code"] = "NON_LIGHTER"
            result["evidence_reason"] = f"Sản phẩm thuộc danh mục khác ({full_cat_str or ', '.join(cat_ids)}), không phải danh mục bật lửa Yahoo 26138"
            return result

    # 3. Loại trừ sản phẩm không phải bật lửa (hàng thời trang, đồng hồ, bút viết, rượu, v.v.)
    explicit_lighter = bool(re.search(r"(?:ライター|オイルライター|ガスライター|zippo|ジッポ|喫煙具|着火)", title, re.IGNORECASE))
    if _NON_LIGHTER_EXCLUDE_RE.search(title) and not explicit_lighter:
        result["decision_code"] = "NON_LIGHTER"
        result["evidence_reason"] = "Không phải sản phẩm bật lửa (hàng thời trang/đồng hồ/rượu/bút viết/linh kiện khác)"
        return result

    if not _LIGHTER_INDICATOR_RE.search(title) and not _LIGHTER_INDICATOR_RE.search(description):
        result["decision_code"] = "NON_LIGHTER"
        result["evidence_reason"] = "Không tìm thấy dấu hiệu sản phẩm bật lửa trong tiêu đề hoặc mô tả"
        return result

    # 4. Loại trừ chỉ bán phụ kiện / hộp rỗng / ruột rời
    is_acc_title = bool(_ACCESSORY_ONLY_RE.search(title)) and not any(k in title for k in ["ライター本体", "オイルライター", "ガスライター"])
    is_box_or_unit = bool(re.search(r"(?:空箱|箱のみ|ケースのみ|元箱のみ|木箱のみ|インサイドユニット|インナーユニット|ユニットのみ|部品のみ|パーツのみ|ガスボンベ|発火石|フリント|替え芯|ウィック)", title))
    if is_acc_title or is_box_or_unit or ("空箱" in full_text and not any(k in full_text for k in ["ライター本体", "本ライター", "個ライター"])):
        m_lighter_attached = re.search(r"(?:ライター\s*(?:本体\s*)?\d+\s*(?:本|個|点)|本体\s*\d+\s*(?:本|個|点))", full_text)
        if not m_lighter_attached:
            # Lô nhiều cây bật lửa kèm đồ tiêu hao (gas, đá lửa, bấc) vẫn là lô hợp lệ khi: đếm được >= 2 cây
            # (không tính số lượng gas/đá/bấc), tiêu đề có chữ ライター thật (không phải 'ライター用'),
            # và không ghi chỉ bán hộp / ruột / linh kiện.
            mixed_cnt, _, _ = extract_actual_lighter_count(_CONSUMABLE_QTY_RE.sub(" ", title), "")
            if (
                mixed_cnt is not None
                and mixed_cnt >= 2
                and re.search(r"ライター(?!用)", title)
                and not _BOX_UNIT_ONLY_RE.search(full_text)
            ):
                m_lighter_attached = True
        if not m_lighter_attached:
            result["decision_code"] = "ACCESSORY_ONLY"
            result["evidence_reason"] = "Chỉ bán hộp rỗng, vỏ hộp, ruột hoặc linh kiện rời; không có bật lửa hoàn chỉnh"
            return result

    # 5. Loại trừ bán chọn 1 món từ ảnh hoặc giá tính theo từng cây
    if _PER_PIECE_CHOICE_RE.search(full_text):
        result["decision_code"] = "PER_PIECE_CHOICE"
        result["evidence_reason"] = "Có nhiều cây để lựa chọn hoặc giá tính riêng theo từng cây, không bán chung cả lot"
        return result

    # Kiểm tra bán tách lẻ (バラ売り)
    has_no_split = bool(re.search(r"バラ売り(不可|はできません|はいたしません|NG|しません|出来ません)", full_text))
    has_split = bool(re.search(r"バラ売り", full_text))
    if has_split and not has_no_split:
        result["decision_code"] = "PER_PIECE_CHOICE"
        result["evidence_reason"] = "Người bán cho phép bán tách lẻ (バラ売り), không bảo đảm bán trọn vẹn cả lot"
        return result

    # 6. Loại trừ trường hợp ảnh chụp nhiều cây nhưng mô tả nói chỉ bán 1 cây chỉ định
    if _SINGLE_CHOICE_FROM_PHOTO_RE.search(description) and not any(k in description for k in _LOT_POSITIVE_KEYWORDS):
        result["decision_code"] = "SINGLE_ITEM"
        result["evidence_reason"] = "Ảnh chụp nhiều cây nhưng mô tả chỉ bán 1 cây chỉ định"
        return result

    # 7. Bóc tách số lượng cây bật lửa thực tế
    count, is_multiple_confirmed, count_note = extract_actual_lighter_count(title, description)

    # 8. Xử lý trường hợp hàng lẻ 1 cây
    if count == 1:
        result["decision_code"] = "SINGLE_ITEM"
        result["evidence_reason"] = "Phiên bán 1 cây bật lửa đơn lẻ (kể cả có kèm hộp, giấy tờ, phụ kiện)"
        return result

    # Nếu không có số lượng và cũng không có bất kỳ từ khóa lot nào -> Hàng lẻ
    has_lot_kw = _has_lot_keyword(full_text)
    if count is None and not is_multiple_confirmed and not has_lot_kw:
        result["decision_code"] = "SINGLE_ITEM"
        result["evidence_reason"] = "Không phát hiện dấu hiệu bán chung từ 2 cây bật lửa trở lên"
        return result

    # 9. Xử lý trường hợp xác nhận LOT hợp lệ
    rate = 165
    if count and count >= 2:
        result["is_verified_lot"] = True
        result["decision_code"] = "VERIFIED_LOT"
        result["lighter_count"] = count
        result["badge_label"] = f"LOT · {count} cây"
        result["evidence_reason"] = f"Mô tả xác nhận bán chung {count} bật lửa (giá bid cho cả lot)"

        if price_jpy and price_jpy > 0:
            result["unit_price_jpy"] = round(price_jpy / count)
            result["unit_price_vnd"] = round((price_jpy * rate) / count)
            tot_jpy = price_jpy + (shipping_fee_jpy or 0)
            result["unit_cost_with_ship_jpy"] = round(tot_jpy / count)
            result["unit_cost_with_ship_vnd"] = round((tot_jpy * rate) / count)
        return result

    if count is None and is_multiple_confirmed:
        # Xác nhận rõ bán nhiều cây nhưng chưa đếm được số cây cụ thể
        result["is_verified_lot"] = True
        result["decision_code"] = "VERIFIED_LOT"
        result["lighter_count"] = None
        result["badge_label"] = "LOT · Nhiều cây (Chưa rõ số lượng)"
        result["evidence_reason"] = "Mô tả xác nhận bán chung nhiều bật lửa (chưa rõ số lượng cụ thể)"
        return result

    # 10. Mọi trường hợp mơ hồ còn lại
    result["decision_code"] = "UNCERTAIN"
    result["evidence_reason"] = "Chưa đủ bằng chứng xác thực bán chung từ 2 cây bật lửa trở lên"
    return result


def analyze_lot_quantity(title: str, description: str = "", price_jpy: int | None = None, shipping_fee_jpy: int | None = None) -> dict[str, Any]:
    """Phân tích số lượng cây quẹt trong Lô (Lot / Bulk / Set) và tính đơn giá bình quân."""
    ver = verify_yahoo_lighter_lot({
        "title": title,
        "description": description,
        "current_price_jpy": price_jpy,
        "shipping_fee_jpy": shipping_fee_jpy,
        "status": "open",
        "bids": 1,
    })
    return {
        "is_lot": ver["is_verified_lot"],
        "count": ver["lighter_count"],
        "unit_price_jpy": ver["unit_price_jpy"],
        "unit_price_vnd": ver["unit_price_vnd"],
        "unit_cost_with_ship_jpy": ver["unit_cost_with_ship_jpy"],
        "unit_cost_with_ship_vnd": ver["unit_cost_with_ship_vnd"],
        "decision_code": ver["decision_code"],
        "evidence_reason": ver["evidence_reason"],
        "badge_label": ver["badge_label"],
    }



def deep_analyze_yahoo_auction(info: dict[str, Any]) -> dict[str, Any]:
    """Phân tích kỹ thuật chuyên sâu về tình trạng, chức năng đánh lửa, phụ kiện và tư vấn chiến thuật."""
    title = info.get("title", "")
    desc = info.get("description", "")
    condition_raw = info.get("conditionName", "")
    full_text = f"{title} {desc} {condition_raw}".lower()

    # 1. Tình trạng đánh lửa & hoạt động
    untested_pats = ["動作未確認", "着火未確認", "未確認", "保証できません", "動作未チェック", "現状渡し", "動作確認は行っておりません"]
    working_pats = ["着火確認済み", "着火ok", "着火確認", "着火良好", "火花・着火ok"]
    spark_only_pats = ["火花のみ", "火花ok", "火花確認"]
    junk_pats = ["ジャンク", "junk", "部品取り", "現状品", "故障"]

    if any(p in full_text for p in untested_pats):
        ignition_status = "⚠️ CHƯA THỬ LỬA / KHÔNG BẢO ĐẢM (Hàng lưu kho, bán hiện trạng)"
        tech_grade = "untested"
    elif any(p in full_text for p in working_pats):
        ignition_status = "🔥 ĐÃ THỬ LỬA (Hoạt động tốt / Đánh lửa chuẩn)"
        tech_grade = "working"
    elif any(p in full_text for p in spark_only_pats):
        ignition_status = "⚡ CÓ TIA LỬA ĐÁ (Chưa nạp gas / Hết gas)"
        tech_grade = "spark_only"
    elif any(p in full_text for p in junk_pats):
        ignition_status = "🔧 HÀNG XÁC / JUNK / LẤY LINH KIỆN (Bán hiện trạng, cần thợ dọn)"
        tech_grade = "junk"
    else:
        ignition_status = "Chưa rõ tình trạng lửa (Người bán không ghi cụ thể)"
        tech_grade = "unknown"

    # 2. Ngoại hình
    cond_map = {
        "未使用": "Mới 100% chưa qua sử dụng",
        "未使用に近い": "Như mới / Like new",
        "目立った傷や汚れなし": "Rất đẹp, ít vết xước",
        "やや傷や汚れあり": "Xước nhẹ theo thời gian, có bụi bẩn",
        "傷や汚れあり": "Trầy xước cấn móp nhiều",
        "全体的に状態が悪い": "Xấu, rỉ sét, trầy xước nặng",
    }
    condition_vn = cond_map.get(condition_raw, condition_raw or "Chưa rõ")

    # 3. Phụ kiện
    if any(p in full_text for p in ["画像に写っているものが全て", "本体のみ", "箱なし", "箱無"]):
        accessories = "Chỉ có quẹt trần như ảnh chụp (Không hộp sổ)"
    elif any(p in full_text for p in ["箱あり", "箱付", "ケース付", "フルセット"]):
        accessories = "Có hộp / phụ kiện kèm theo"
    else:
        accessories = "Theo hình ảnh thực tế trên sàn"

    # 4. Phân tích Lô & Đếm số cây
    price_jpy = info.get("current_price_jpy")
    ship_jpy = info.get("shipping_fee_jpy")
    lot_info = analyze_lot_quantity(title, desc, price_jpy, ship_jpy)

    # 5. Đánh giá chuyên gia (Expert Commentary)
    expert_notes = []
    if lot_info["is_lot"] and lot_info["count"]:
        cnt = lot_info["count"]
        u_jpy = lot_info["unit_price_jpy"]
        u_vnd = lot_info["unit_price_vnd"]
        u_ship_vnd = lot_info["unit_cost_with_ship_vnd"]

        u_vnd_fmt = f"{u_vnd:,}".replace(",", ".") if u_vnd else ""
        u_ship_fmt = f"{u_ship_vnd:,}".replace(",", ".") if u_ship_vnd else ""

        if u_jpy and u_jpy <= 1000:
            expert_notes.append(f"• <b>Về mức giá:</b> Đơn giá ~{u_vnd_fmt} đ/cây (gồm ship Nhật ~{u_ship_fmt} đ/cây) là <b>vùng gom xác rất hời</b> cho thợ dọn quẹt Nhật bãi.")
            expert_notes.append("• <b>Biên lợi nhuận:</b> Quẹt gas Nhật dọn lên lửa bán lẻ tại VN dao động 150k - 300k/cây ➔ Tiềm năng <b>lời x2 - x2.5 lần vốn</b>!")
        elif u_jpy and u_jpy <= 2500:
            expert_notes.append(f"• <b>Về mức giá:</b> Đơn giá ~{u_vnd_fmt} đ/cây ở mức hợp lý nếu trong lô có các thương hiệu tên tuổi (Ronson, Dunhill, Zippo).")

        if tech_grade in ["untested", "junk"]:
            expert_notes.append("• <b>Rủi ro kỹ thuật:</b> Hàng chưa kiểm tra (未確認), ước tính tỷ lệ sống ~30-50%, số còn lại rã van, đá, ron làm phụ tùng cứu cây khác.")
            max_bid_lot = round(cnt * 700)
            max_bid_fmt = f"{max_bid_lot:,}".replace(",", ".")
            expert_notes.append(f"• 🎯 <b>Khuyến nghị mốc trần:</b> Với lô {cnt} cây này, trần bid hợp lý nên dưới <b>{max_bid_fmt} yên</b> để bảo toàn lãi thợ.")
    elif tech_grade in ["untested", "junk"]:
        expert_notes.append("• 💡 Cây này bán dạng xác / chưa thử lửa, nếu mua chỉ nên bid ở mức giá Junk (trừ bớt 50% - 60% so với hàng đẹp).")

    return {
        "ignition_status": ignition_status,
        "tech_grade": tech_grade,
        "condition_vn": condition_vn,
        "accessories": accessories,
        "lot_info": lot_info,
        "expert_notes": expert_notes,
    }


def parse_reverse_profit_input(text: str) -> dict[str, Any] | None:
    """Nhận diện câu lệnh tính ngược giá bid theo lợi nhuận kỳ vọng.
    
    Ví dụ:
    - 'dupont sơn mài bán 4tr5 lời 30%'
    - 'zippo bán 1tr5 lời 400k'
    - 'calc ronson bán 2tr lãi 500k'
    """
    norm = strip_vietnamese_accents(text).lower()
    if "ban " not in norm or not any(k in norm for k in ["loi ", "lai ", "loi", "lai"]):
        return None

    # Regex bắt: <item_name> ban <sale_price> (loi|lai) <profit>
    m = re.search(r"^(?:calc\s+)?(.*?)\s+ban\s+([^\s]+)\s+(?:loi|lai)\s+(.*)$", norm)
    if not m:
        return None

    item_desc = m.group(1).strip()
    sale_raw = m.group(2).strip()
    profit_raw = m.group(3).strip()

    # Parse giá bán
    from parser import parse_multi_currency_price
    sale_val, sale_curr, _, _ = parse_multi_currency_price(sale_raw)
    if not sale_val or sale_val <= 0:
        return None
    if sale_curr == "JPY":
        target_sale_vnd = sale_val * 165
    else:
        target_sale_vnd = sale_val

    # Parse lợi nhuận
    profit_pct = None
    profit_vnd = None
    if "%" in profit_raw:
        p_pct_str = profit_raw.replace("%", "").strip()
        try:
            profit_pct = float(p_pct_str)
        except ValueError:
            profit_pct = 25.0
    else:
        p_val, p_curr, _, sugg = parse_multi_currency_price(profit_raw)
        if p_val and p_val > 0:
            profit_vnd = p_val if p_curr != "JPY" else (p_val * 165)
        elif sugg:
            for s in sugg:
                if s["currency"] == "VND":
                    profit_vnd = s["amount"]
                    break

    return {
        "item_desc": item_desc or "Cây quẹt",
        "target_sale_vnd": target_sale_vnd,
        "profit_pct": profit_pct,
        "profit_vnd": profit_vnd,
    }


def parse_sniper_timer_input(text: str) -> dict[str, Any] | None:
    """Nhận diện lệnh hẹn giờ canh bid (Sniper Timer).
    
    Ví dụ:
    - 'canh dupont 21:30'
    - 'canh zippo 15p'
    - 'remind ronson 10 phut'
    """
    norm = strip_vietnamese_accents(text).lower()
    if not norm.startswith("canh ") and not norm.startswith("remind "):
        return None

    tokens = norm.split()
    if len(tokens) < 3:
        return None

    time_token = tokens[-1]
    unit_token = tokens[-2] if len(tokens) >= 4 and tokens[-1] in ["phut", "p", "m", "phút"] else ""
    
    # 1. Dạng giờ:phút (ví dụ 21:30)
    m_time = re.match(r"^(\d{1,2}):(\d{2})$", time_token)
    if m_time:
        hr = int(m_time.group(1))
        mn = int(m_time.group(2))
        item_desc = " ".join(tokens[1:-1])
        return {
            "type": "exact_time",
            "hour": hr,
            "minute": mn,
            "item_desc": item_desc or "Quẹt đang canh",
        }

    # 2. Dạng số phút đếm ngược (ví dụ 15p, 10 phut)
    m_min = re.match(r"^(\d+)\s*(?:p|phut|phút|m)?$", time_token)
    if m_min:
        mins = int(m_min.group(1))
        item_desc = " ".join(tokens[1:-1])
        return {
            "type": "countdown",
            "minutes": mins,
            "item_desc": item_desc or "Quẹt đang canh",
        }

    return None


def match_brand_and_model_from_title(title: str) -> dict[str, str]:
    """Nhận diện thương hiệu và phân khúc từ tiêu đề tiếng Nhật hoặc tiếng Anh/Việt."""
    t = title.lower()
    res = {"brand": "unknown", "line": "unknown", "vn_name": title}

    if any(k in t for k in ["dupont", "デュポン", "s.t.dupont"]):
        res["brand"] = "dupont"
        if any(k in t for k in ["ライン2", "line 2", "line2", "l2"]):
            res["line"] = "line_2"
            res["vn_name"] = "Dupont Line 2"
        elif any(k in t for k in ["ライン1", "line 1", "line1", "1s", "1l"]):
            res["line"] = "line_1"
            res["vn_name"] = "Dupont Line 1"
        elif any(k in t for k in ["ギャッツビー", "gatsby"]):
            res["line"] = "gatsby"
            res["vn_name"] = "Dupont Gatsby"
        else:
            res["vn_name"] = "Bật lửa Dupont"

    elif any(k in t for k in ["dunhill", "ダンヒル"]):
        res["brand"] = "dunhill"
        if any(k in t for k in ["ローラガス", "rollagas", "rolla"]):
            res["line"] = "rollagas"
            res["vn_name"] = "Dunhill Rollagas"
        elif any(k in t for k in ["ユニーク", "unique"]):
            res["line"] = "unique"
            res["vn_name"] = "Dunhill Unique"
        else:
            res["vn_name"] = "Bật lửa Dunhill"

    elif any(k in t for k in ["zippo", "ジッポー"]):
        res["brand"] = "zippo"
        if any(k in t for k in ["スターリング", "sterling", "925", "純銀"]):
            res["line"] = "sterling"
            res["vn_name"] = "Zippo Bạc Khối (Sterling 925)"
        elif any(k in t for k in ["アーマー", "armor"]):
            res["line"] = "armor"
            res["vn_name"] = "Zippo Armor"
        elif any(k in t for k in ["レプリカ", "replica", "1935", "1941"]):
            res["line"] = "replica"
            res["vn_name"] = "Zippo Replica"
        elif any(k in t for k in ["スリム", "slim"]):
            res["line"] = "slim"
            res["vn_name"] = "Zippo Slim"
        else:
            res["vn_name"] = "Bật lửa Zippo"

    elif any(k in t for k in ["ronson", "ロンソン"]):
        res["brand"] = "ronson"
        if any(k in t for k in ["バンジョー", "banjo"]):
            res["line"] = "banjo"
            res["vn_name"] = "Ronson Banjo"
        elif any(k in t for k in ["ヴァラフレーム", "varaflame"]):
            res["line"] = "varaflame"
            res["vn_name"] = "Ronson Varaflame"
        elif any(k in t for k in ["スタンダード", "standard"]):
            res["line"] = "standard"
            res["vn_name"] = "Ronson Standard"
        else:
            res["vn_name"] = "Bật lửa Ronson"

    elif any(k in t for k in ["cartier", "カルティエ"]):
        res["brand"] = "cartier"
        res["vn_name"] = "Bật lửa Cartier"

    return res


def decode_lighter_stamp(text: str) -> dict[str, Any] | None:
    """Giải mã mộc đáy Zippo và các dòng bật lửa vintage.
    Ví dụ: 'zippo 1994', 'zippo X', 'mộc đáy X', 'zippo 1974', 'mộc đáy dunhill'.
    """
    raw = strip_vietnamese_accents(text).lower().strip()
    if not any(k in raw for k in ["zippo", "moc day", "day zippo", "dunhill", "dupont"]):
        return None

    # 1. Zippo La Mã (1986 - 2000): II đến XVI
    roman_map = {
        "xvi": 2000, "xv": 1999, "xiv": 1998, "xiii": 1997, "xii": 1996,
        "xi": 1995, "x": 1994, "ix": 1993, "viii": 1992, "vii": 1991,
        "vi": 1990, "v": 1989, "iv": 1988, "iii": 1987, "ii": 1986,
    }

    # Thử tìm theo số La Mã
    for r_code, yr in roman_map.items():
        # Kiểm tra token nguyên vẹn
        pattern = rf"\b(?:moc day\s*)?(?:zippo\s*)?{r_code}\b"
        if re.search(pattern, raw):
            return {
                "brand": "Zippo",
                "model": "Zippo La Mã (Giai đoạn Vintage 1986 - 2000)",
                "year": yr,
                "stamp_code": r_code.upper(),
                "stamp_desc": f"Mộc đáy ký hiệu La Mã: {r_code.upper()} (Bradford, PA. MADE IN U.S.A.)",
                "insert_features": f"Ruột (Insert) mộc đáy chữ số {r_code.upper()} (lệch +-1 năm vẫn là zin hãng), bánh xe xéo, chốt cam thép không gỉ.",
                "market_price_vnd": "800.000 - 1.600.000 đ (Tùy độ keng, hoa văn và có hộp)",
                "collector_note": "Dòng La Mã vỏ đồng thau dày dặn, bản lề 5 chấu rất khít, tiếng mở nắp thanh vang được dân chơi săn lùng nhiều nhất.",
            }

    # Thử tìm theo năm 1986 - 2000
    m_yr = re.search(r"\b(198[6-9]|199\d|2000)\b", raw)
    if m_yr:
        yr = int(m_yr.group(1))
        inv_map = {v: k.upper() for k, v in roman_map.items()}
        r_code = inv_map.get(yr, "")
        return {
            "brand": "Zippo",
            "model": f"Zippo La Mã năm {yr}",
            "year": yr,
            "stamp_code": r_code,
            "stamp_desc": f"Mộc đáy ký hiệu La Mã: {r_code} (Bradford, PA. MADE IN U.S.A.)",
            "insert_features": f"Ruột (Insert) dập chữ số La Mã {r_code}, bánh xe xéo, bấc bện dây đồng.",
            "market_price_vnd": "850.000 - 1.800.000 đ",
            "collector_note": f"Zippo năm {yr} (Mã {r_code}) là một trong những năm hoàng kim của Zippo cổ, bản lề chắc chắn, giữ xăng cực tốt.",
        }

    # 2. Zippo gạch cổ (1974 - 1982)
    slash_map = {
        1974: ("/// /// (3 gạch chéo mỗi bên)", "6 gạch chéo"),
        1975: ("/// // (3 gạch trái, 2 gạch phải)", "5 gạch chéo"),
        1976: ("// // (2 gạch mỗi bên)", "4 gạch chéo"),
        1977: ("// / (2 gạch trái, 1 gạch phải)", "3 gạch chéo"),
        1978: ("/ / (1 gạch mỗi bên)", "2 gạch chéo"),
        1979: ("/ | (gạch chéo trái, gạch đứng phải)", "chuyển giao gạch đứng"),
        1980: ("| | | | (4 gạch đứng)", "4 gạch đứng"),
        1981: ("| | | (3 gạch đứng)", "3 gạch đứng"),
        1982: ("| | (2 gạch đứng)", "2 gạch đứng"),
    }
    m_slash_yr = re.search(r"\b(197[4-9]|198[0-2])\b", raw)
    if m_slash_yr:
        s_yr = int(m_slash_yr.group(1))
        desc_pair = slash_map.get(s_yr)
        if desc_pair:
            return {
                "brand": "Zippo",
                "model": f"Zippo Gạch Cổ năm {s_yr}",
                "year": s_yr,
                "stamp_code": desc_pair[1],
                "stamp_desc": f"Mộc đáy ký hiệu: {desc_pair[0]} (BRADFORD, PA.)",
                "insert_features": "Ruột mộc đáy dập ngang, bánh xe chéo sắc nét, lưỡi gà tán ri-vê đặc, bấc bột không dây đồng (hoặc dây đồng đời cuối).",
                "market_price_vnd": "1.500.000 - 3.200.000 đ (Hàng sưu tầm giá trị cao)",
                "collector_note": "Zippo thời kỳ gạch cổ thập niên 70 rất hiếm và có giá trị sưu tầm vượt trội so với Zippo hiện đại.",
            }

    # 3. Zippo đời số hiện đại (2001 - 2026)
    m_mod = re.search(r"\b(200[1-9]|201\d|202[0-6])\b", raw)
    if m_mod:
        m_yr_val = int(m_mod.group(1))
        two_digit = f"{m_yr_val % 100:02d}"
        return {
            "brand": "Zippo",
            "model": f"Zippo Đời Số năm {m_yr_val}",
            "year": m_yr_val,
            "stamp_code": two_digit,
            "stamp_desc": f"Mộc đáy góc phải dập số: {two_digit} (Góc trái là chữ cái A-L chỉ tháng 1-12)",
            "insert_features": f"Ruột dập số {two_digit}, bánh xe xéo, bấc bện dây đồng, đệm bông chặn đáy có lỗ châm xăng dự phòng.",
            "market_price_vnd": "450.000 - 900.000 đ (Dòng phổ thông, thanh khoản cao)",
            "collector_note": "Dòng dùng thường ngày rất bền, phụ tùng đá bấc dễ kiếm, bảo dưỡng đơn giản.",
        }

    # 4. Mộc đáy Dunhill Rollagas
    if "dunhill" in raw and ("moc day" in raw or "rollagas" in raw):
        return {
            "brand": "Dunhill",
            "model": "Dunhill Rollagas (Thụy Sĩ)",
            "year": "1960 - 2010",
            "stamp_code": "SWISS MADE",
            "stamp_desc": "Mộc đáy khắc chìm: 'DUNHILL' - 'SWISS MADE' kèm mã bằng sáng chế 'US.RE 24163'",
            "insert_features": "Núm điều chỉnh gas 2 tầng, bản lề nắp gập kín khí, bánh xe lăn ngang cạnh hông đặc trưng.",
            "market_price_vnd": "1.800.000 - 3.500.000 đ (Hàng dọn sống lên lửa đẹp)",
            "collector_note": "Dòng quý tộc của Anh sản xuất tại Thụy Sĩ. Tuyệt đối dùng đá mềm Dunhill, tránh dùng đá Zippo làm cùn bánh xe.",
        }

    # 5. Mộc đáy Dupont
    if "dupont" in raw and "moc day" in raw:
        return {
            "brand": "S.T. Dupont",
            "model": "Dupont Line 1 / Line 2 / Gatsby (Pháp)",
            "year": "1970 - nay",
            "stamp_code": "MADE IN FRANCE",
            "stamp_desc": "Mộc đáy khắc: 'S.T. DUPONT DE PARIS' - 'MADE IN FRANCE'. Dãy số seri 6-7 ký tự khắc thủ công nông sâu tự nhiên.",
            "insert_features": "Hàng xịn số seri khắc tay không thẳng tắp tăm tắp như hàng nhái dập máy laser. Màu sơn bên trong nắp van nạp tương ứng gas: Vàng (Line 1 nhỏ, Line 2), Đỏ (Line 1 lớn), Xanh lá (Gatsby).",
            "market_price_vnd": "2.500.000 - 7.500.000 đ",
            "collector_note": "Soi kỹ chân ren nạp gas và tiếng chuông (clink) khi mở nắp đối với Line 2.",
        }

    # 6. Zippo Solid Brass (Đồng thau nguyên khối)
    if "solid brass" in raw or ("zippo" in raw and ("dong thau" in raw or "brass" in raw) and "moc day" in raw):
        return {
            "brand": "Zippo",
            "model": "Zippo Solid Brass (Đồng thau nguyên khối)",
            "year": "1982 - nay",
            "stamp_code": "SOLID BRASS",
            "stamp_desc": "Mộc đáy dập chìm dòng chữ hoa nổi bật: 'SOLID BRASS' (Thường đi kèm logo Zippo và mã năm)",
            "insert_features": "Ruột mộc dập xi mạ vàng đồng bộ với vỏ, bánh xe xéo, bấc bện dây đồng.",
            "market_price_vnd": "650.000 - 1.400.000 đ",
            "collector_note": "Dòng vỏ đồng nguyên khối không xi mạ, càng dùng càng lên nước đồng (patina) bóng đẹp cổ kính.",
        }

    # 7. Zippo Sterling Silver 925 (Bạc khối)
    if "sterling" in raw or ("zippo" in raw and ("bac khoi" in raw or "925" in raw)):
        return {
            "brand": "Zippo",
            "model": "Zippo Sterling Silver (Bạc khối 925)",
            "year": "Mọi thời kỳ",
            "stamp_code": "STERLING",
            "stamp_desc": "Mộc đáy dập chìm chữ in hoa: 'STERLING' (Bạc 92.5% nguyên chất)",
            "insert_features": "Ruột thép không gỉ sáng bóng, bánh xe chéo.",
            "market_price_vnd": "3.500.000 - 8.000.000 đ (Tùy độ mới và năm La Mã hay đời số)",
            "collector_note": "Vua âm thanh trong các dòng Zippo, vỏ bạc khối tiếng mở nắp thanh ngân vang ngân dài nhất.",
        }

    # 8. Zippo Copper (Đồng đỏ)
    if "copper" in raw or ("zippo" in raw and "dong do" in raw):
        return {
            "brand": "Zippo",
            "model": "Zippo Copper (Đồng đỏ nguyên chất)",
            "year": "2003 & 2022",
            "stamp_code": "COPPER",
            "stamp_desc": "Mộc đáy dập chìm chữ: 'COPPER' (Vỏ đồng đỏ 100% không pha kẽm)",
            "insert_features": "Đời 2003 ruột inox; đời 2022 ruột mạ đen (black coated insert) độc quyền.",
            "market_price_vnd": "2.800.000 - 5.500.000 đ (Dòng hiếm được săn lùng gắt gao)",
            "collector_note": "Chất đồng đỏ màu ánh đỏ cam ấm áp, tạo lớp oxy hóa tự nhiên cực kỳ cuốn hút.",
        }

    # 9. Zippo Titanium
    if "titan" in raw or "titanium" in raw:
        return {
            "brand": "Zippo",
            "model": "Zippo Solid Titanium (Titan nguyên khối)",
            "year": "2001 - 2003",
            "stamp_code": "TITANIUM",
            "stamp_desc": "Mộc đáy dập chữ: 'SOLID TITANIUM' (Kim loại siêu nhẹ, siêu cứng)",
            "insert_features": "Ruột dập mã năm 2001 - 2003.",
            "market_price_vnd": "8.000.000 - 15.000.000 đ (Siêu phẩm sưu tầm chén thánh)",
            "collector_note": "Zippo chỉ sản xuất trong 3 năm ngắn ngủi vì gia công titan quá tốn kém mòn dao cắt. Cực hiếm trên thị trường!",
        }

    return None


def get_lighter_repair_guide(text: str) -> dict[str, Any] | None:
    """Cẩm nang bắt bệnh, thay ron (O-ring) và phục chế bật lửa cổ bỏ túi."""
    raw = strip_vietnamese_accents(text).lower().strip()
    if not any(k in raw for k in ["benh", "sua", "thay ron", "xi gas", "ket da", "ron "]):
        return None

    # Dunhill Rollagas
    if any(k in raw for k in ["dunhill", "rollagas"]):
        return {
            "brand": "Dunhill",
            "title": "Cẩm Nang Bắt Bệnh & Thay Ron Dunhill Rollagas",
            "symptoms": "Bị xì gas ở chân nạp đáy, xì ở cổ phun khi đóng nắp, hoặc lửa không tắt liu riu.",
            "oring_specs": [
                "• Ron kim điều tốc (chỉnh to nhỏ): 2.5 x 1.0 mm (Cao su Viton/FKM chịu gas)",
                "• Ron cổ van xả: 3.0 x 1.0 mm",
                "• Ron ren nắp nạp đáy: 4.0 x 1.2 mm",
            ],
            "fix_steps": [
                "1. Tháo nắp đáy bằng vít dẹt chuẩn (tránh làm loét ren đồng).",
                "2. Rút cụm kim van xả ra nhẹ nhàng, tránh làm gãy ti kim mỏng.",
                "3. Dùng tăm nhọn gắp ron cũ bị chai mục, vệ sinh sạch muội bẩn buồng chứa.",
                "4. Quét 1 lớp mỡ silicone mỏng lên ron mới trước khi lắp để chống rách ron.",
            ],
            "warning": "⚠️ TUYỆT ĐỐI KHÔNG dùng đá lửa Zippo cứng vì sẽ làm mòn bánh xe lăn ngang của Dunhill. Chỉ dùng đá mềm Dunhill / Ronson đỏ.",
        }

    # Dupont
    if any(k in raw for k in ["dupont", "line 1", "line 2", "gatsby"]):
        return {
            "brand": "S.T. Dupont",
            "title": "Cẩm Nang Bắt Bệnh & Thay Ron S.T. Dupont (Line 1 & Line 2)",
            "symptoms": "Bơm gas bị xì ngược, quẹt không ra gas (nghẹt kim), hoặc xì gas cổ nắp.",
            "oring_specs": [
                "• Ron chân van nạp gas đáy: 4.5 x 1.0 mm (Line 2) / 5.0 x 1.0 mm (Line 1)",
                "• Ron chặn buồng xả: 3.0 x 0.8 mm",
                "• Ron đầu ti kim điều áp: 2.0 x 0.8 mm",
            ],
            "fix_steps": [
                "1. Cần đồ nghề tháo van chuyên dụng 2 chấu hoặc vít chuyên dụng Dupont.",
                "2. Ngâm cụm van nghẹt trong dung dịch rửa xăng thơm hoặc dung dịch rửa chế hòa khí 10 phút.",
                "3. Thay bộ ron cao su chịu áp suất cao.",
                "4. Thử độ kín bằng cách nạp một lượng gas nhỏ và ngửi quanh thân máy sau 5 phút.",
            ],
            "warning": "⚠️ Cẩn thận lò xo nắp và thanh gõ chuông (clink), không bẻ cong làm mất tiếng chuông mở nắp trứ danh của Line 2!",
        }

    # Zippo
    if any(k in raw for k in ["zippo", "xang zippo", "ket da"]):
        return {
            "brand": "Zippo",
            "title": "Cẩm Nang Bắt Bệnh Zippo: Kẹt Đá, Bay Xăng & Lỏng Ruột",
            "symptoms": "Bánh xe bị kẹt cứng không xoay được, xăng bay hơi quá nhanh (1-2 ngày hết), ruột lỏng trồi lên khi mở nắp.",
            "oring_specs": [
                "• Zippo dùng xăng bông bấc, không dùng gioăng cao su.",
                "• Bông chèn ruột: Bông gòn y tế hoặc bông Zippo rayon.",
                "• Bấc (tim): Bấc bện dây đồng tản nhiệt tốt, chống cháy lụi.",
            ],
            "fix_steps": [
                "1. Bánh xe kẹt: Tháo lò xo đá dưới đáy ruột, dùng kim nhọn hoặc mũi khoan mini 1.5mm thông bột đá cũ bị oxy hóa dính chặt trong ống đá.",
                "2. Bay xăng nhanh: Lót thêm miếng đệm cao su chặn đáy felt pad chống bay hơi, luồn bấc hình zíc-zắc qua 3 lớp bông.",
                "3. Lỏng ruột: Dùng kìm bấm bóp nhẹ 2 mép cạnh hông của vỏ, hoặc dán 1 lớp băng keo giấy mỏng quanh thân ruột.",
            ],
            "warning": "⚠️ Không dùng xăng tạp / dầu hỏa làm muội đen buồng đốt và chai tim bấc. Chỉ dùng xăng Zippo chính hãng.",
        }

    # Ronson
    if any(k in raw for k in ["ronson", "banjo", "varaflame"]):
        return {
            "brand": "Ronson",
            "title": "Cẩm Nang Phục Chế Bật Lửa Ronson Varaflame & Banjo",
            "symptoms": "Xì van nạp đáy hoặc kẹt cần gạt bánh xe.",
            "oring_specs": [
                "• Ron van nạp đáy Ronson: 4.0 x 1.0 mm",
                "• Ron ti xả: 2.5 x 1.0 mm",
            ],
            "fix_steps": [
                "1. Tháo nắp van nạp dưới đáy, thay ron cao su chịu dầu.",
                "2. Canh chỉnh kim điều tiết gas vừa tầm, không vặn quá chặt làm gãy ti kim.",
                "3. Tra một giọt dầu máy may vào trục cần gạt để bấm êm ái.",
            ],
            "warning": "⚠️ Cần gạt Ronson bằng hợp kim đúc, không dùng lực đè bẻ cong sẽ gãy ngàm lẫy đá.",
        }

    return None


