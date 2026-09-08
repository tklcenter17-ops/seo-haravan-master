"""Bộ chuẩn hóa văn bản tiếng Việt, Unicode, số full-width và alias."""
from __future__ import annotations

import re
import unicodedata

# Bảng chuyển ký tự full-width sang ASCII
_FULLWIDTH_MAP = {
    ord(c): ord(a)
    for c, a in zip(
        "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ，．：；！？￥",
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz,.:;!?¥",
    )
}

# Bản đồ bỏ dấu tiếng Việt chuẩn xác
_VIETNAMESE_ACCENT_MAP = {
    ord("à"): ord("a"), ord("á"): ord("a"), ord("ả"): ord("a"), ord("ã"): ord("a"), ord("ạ"): ord("a"),
    ord("ă"): ord("a"), ord("ằ"): ord("a"), ord("ắ"): ord("a"), ord("ẳ"): ord("a"), ord("ẵ"): ord("a"), ord("ặ"): ord("a"),
    ord("â"): ord("a"), ord("ầ"): ord("a"), ord("ấ"): ord("a"), ord("ẩ"): ord("a"), ord("ẫ"): ord("a"), ord("ậ"): ord("a"),
    ord("è"): ord("e"), ord("é"): ord("e"), ord("ẻ"): ord("e"), ord("ẽ"): ord("e"), ord("ẹ"): ord("e"),
    ord("ê"): ord("e"), ord("ề"): ord("e"), ord("ế"): ord("e"), ord("ể"): ord("e"), ord("ễ"): ord("e"), ord("ệ"): ord("e"),
    ord("ì"): ord("i"), ord("í"): ord("i"), ord("ỉ"): ord("i"), ord("ĩ"): ord("i"), ord("ị"): ord("i"),
    ord("ò"): ord("o"), ord("ó"): ord("o"), ord("ỏ"): ord("o"), ord("õ"): ord("o"), ord("ọ"): ord("o"),
    ord("ô"): ord("o"), ord("ồ"): ord("o"), ord("ố"): ord("o"), ord("ổ"): ord("o"), ord("ỗ"): ord("o"), ord("ộ"): ord("o"),
    ord("ơ"): ord("o"), ord("ờ"): ord("o"), ord("ớ"): ord("o"), ord("ở"): ord("o"), ord("ỡ"): ord("o"), ord("ợ"): ord("o"),
    ord("ù"): ord("u"), ord("ú"): ord("u"), ord("ủ"): ord("u"), ord("ũ"): ord("u"), ord("ụ"): ord("u"),
    ord("ư"): ord("u"), ord("ừ"): ord("u"), ord("ứ"): ord("u"), ord("ử"): ord("u"), ord("ữ"): ord("u"), ord("ự"): ord("u"),
    ord("ỳ"): ord("y"), ord("ý"): ord("y"), ord("ỷ"): ord("y"), ord("ỹ"): ord("y"), ord("ỵ"): ord("y"),
    ord("đ"): ord("d"),
    ord("À"): ord("a"), ord("Á"): ord("a"), ord("Ả"): ord("a"), ord("Ã"): ord("a"), ord("Ạ"): ord("a"),
    ord("Ă"): ord("a"), ord("Ằ"): ord("a"), ord("Ắ"): ord("a"), ord("Ẳ"): ord("a"), ord("Ẵ"): ord("a"), ord("Ặ"): ord("a"),
    ord("Â"): ord("a"), ord("Ầ"): ord("a"), ord("Ấ"): ord("a"), ord("Ẩ"): ord("a"), ord("Ẫ"): ord("a"), ord("Ậ"): ord("a"),
    ord("È"): ord("e"), ord("É"): ord("e"), ord("Ẻ"): ord("e"), ord("Ẽ"): ord("e"), ord("Ẹ"): ord("e"),
    ord("Ê"): ord("e"), ord("Ề"): ord("e"), ord("Ế"): ord("e"), ord("Ể"): ord("e"), ord("Ễ"): ord("e"), ord("Ệ"): ord("e"),
    ord("Ì"): ord("i"), ord("Í"): ord("i"), ord("Ỉ"): ord("i"), ord("Ĩ"): ord("i"), ord("Ị"): ord("i"),
    ord("Ò"): ord("o"), ord("Ó"): ord("o"), ord("Ỏ"): ord("o"), ord("Õ"): ord("o"), ord("Ọ"): ord("o"),
    ord("Ô"): ord("o"), ord("Ồ"): ord("o"), ord("Ố"): ord("o"), ord("Ổ"): ord("o"), ord("Ỗ"): ord("o"), ord("Ộ"): ord("o"),
    ord("Ơ"): ord("o"), ord("Ờ"): ord("o"), ord("Ớ"): ord("o"), ord("Ở"): ord("o"), ord("Ỡ"): ord("o"), ord("Ợ"): ord("o"),
    ord("Ù"): ord("u"), ord("Ú"): ord("u"), ord("Ủ"): ord("u"), ord("Ũ"): ord("u"), ord("Ụ"): ord("u"),
    ord("Ư"): ord("u"), ord("Ừ"): ord("u"), ord("Ứ"): ord("u"), ord("Ử"): ord("u"), ord("Ữ"): ord("u"), ord("Ự"): ord("u"),
    ord("Ỳ"): ord("y"), ord("Ý"): ord("y"), ord("Ỷ"): ord("y"), ord("Ỹ"): ord("y"), ord("Ỵ"): ord("y"),
    ord("Đ"): ord("d"),
}


def normalize_unicode(text: str) -> str:
    """Chuẩn hóa Unicode về dạng NFC và chuyển đổi full-width sang half-width ASCII."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return text.translate(_FULLWIDTH_MAP)


def strip_vietnamese_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt, chuyển đ/Đ thành d và đưa về chữ thường."""
    if not text:
        return ""
    text = normalize_unicode(text)
    return text.translate(_VIETNAMESE_ACCENT_MAP).lower()


def clean_search_text(text: str) -> str:
    """Loại bỏ ký tự phân cách thừa, chuẩn hóa khoảng trắng phục vụ tìm kiếm."""
    s = strip_vietnamese_accents(text)
    # Thay thế dấu câu bằng khoảng trắng
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()
