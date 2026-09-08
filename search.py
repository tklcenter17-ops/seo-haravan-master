"""Bộ tìm kiếm toàn văn, xếp hạng, phân nhóm so sánh và phân trang."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Sequence

from models import BidCap, Record
from normalizer import clean_search_text, strip_vietnamese_accents
from parser import parse_attributes
from pricing import PricingResult, calculate_reference_pricing
from repository import get_bid_cap


@dataclass
class SearchGroup:
    scope_key: str
    display_title: str
    brand: str
    line: str
    material: str
    color: str
    box: str
    condition: str
    records: list[Record]
    pricing: PricingResult


@dataclass
class SearchResult:
    query: str
    cleaned_query: str
    is_ambiguous: bool = False
    ambiguous_options: list[str] = None  # type: ignore
    ambiguous_prompt: str = ""
    groups: list[SearchGroup] = None  # type: ignore
    similar_groups: list[SearchGroup] = None  # type: ignore
    total_groups: int = 0
    page: int = 1
    page_size: int = 5


# Các từ đệm câu hỏi tự nhiên cần lọc bỏ
_FILLER_PHRASES = [
    "gia bao nhieu", "gia bn", "bid nhieu", "bid bao nhieu",
    "cho hoi", "hoi gia", "gia sao", "co gia bao nhieu",
    "cay quet", "cay", "chiec", "tim", "xem", "co khong", "co ko",
]


def strip_filler_words(query: str) -> str:
    """Loại bỏ từ đệm câu hỏi tiếng Việt để trích xuất thuộc tính cốt lõi."""
    text = strip_vietnamese_accents(query)
    for p in _FILLER_PHRASES:
        text = text.replace(p, " ")
    # Bỏ khoảng trắng dư thừa
    return re.sub(r"\s+", " ", text).strip()


_COLOR_VN = {
    "green": "xanh la xanh luc green 緑",
    "blue": "xanh duong xanh bien blue navy 青",
    "red": "do red 赤",
    "black": "den black 黒",
    "yellow": "vang yellow 黄",
    "brown": "nau brown 茶",
}

_BRAND_VN = {
    "ronson": "ronson ron son ロンソン",
    "dupont": "dupont s.t. dupont st dupont デュポン",
    "zippo": "zippo ジッポー ジッポ",
    "dunhill": "dunhill ダンヒル",
    "cartier": "cartier カルティエ",
    "colibri": "colibri コリブリ",
    "maruman": "maruman マルマン",
    "sarome": "sarome サロメ",
    "penguin": "penguin ペンギン",
    "givenchy": "givenchy ジバンシィ ジバンシー",
}

_LINE_VN = {
    "line_1": "1 line line 1 ligne 1 l1 ライン1 ライン 1",
    "line_2": "2 line line 2 ligne 2 l2 ライン2 ライン 2",
    "la_ma": "la ma lama la-ma số la mã la mã",
    "rollagas": "rollagas ro la rola ローラガス ロールガス",
    "replica": "replica 1941 1935 1932 1933 レプリカ",
    "armor": "armor vo day vỏ dày アーマー",
    "slim": "slim スリム",
    "unique": "unique",
    "v_mark": "v mark v-mark vmark",
    "standard": "standard スタンダード",
    "varaflame": "varaflame ヴァラフレーム バラフレーム",
    "banjo": "banjo バンジョー",
    "whirlwind": "whirlwind",
    "premier": "premier",
    "gatsby": "gatsby ギャッツビー",
    "windproof": "windproof",
    "d_light": "d light d-light",
    "soubreny": "soubreny",
    "urban": "urban",
}

_MATERIAL_VN = {
    "son_mai": "son mai urushi lacquer 漆 本漆",
    "silver": "bac silver sp ma bac 銀 シルバー 銀製",
    "sterling_silver": "bac khoi sterling silver 925 純銀 スターリング",
    "gold": "vang gold gp ma vang boc vang 金 ゴールド 金製",
    "solid_gold": "vang khoi solid gold 18k 14k 金無垢 18金",
    "brass": "brass barass dong thau dong đồng thau đồng 真鍮 ブラス",
}

_BOX_VN = {
    "yes": "co hop co box box hop full box full set 箱付き 元箱 共箱 ケース付き",
    "no": "khong hop khong box no box mat hop 箱なし 本体のみ",
}


def get_record_search_corpus(rec: Record) -> str:
    """Tập hợp toàn bộ văn bản và từ khóa thuộc tính của bản ghi để tìm kiếm."""
    parts = [
        rec.normalized_search_text,
        strip_vietnamese_accents(rec.display_name),
        _BRAND_VN.get(rec.brand, rec.brand),
        _LINE_VN.get(rec.line, rec.line),
        _MATERIAL_VN.get(rec.material, rec.material),
        _COLOR_VN.get(rec.color, rec.color),
        _BOX_VN.get(rec.box, ""),
        rec.finish,
        rec.edition,
        strip_vietnamese_accents(rec.accessories_note),
        strip_vietnamese_accents(rec.cosmetic_condition),
    ]
    return " ".join(p for p in parts if p)


_PRETTY_LINE = {
    "line_1": "Line 1",
    "line_2": "Line 2",
    "la_ma": "La Mã",
    "rollagas": "Rollagas",
    "v_mark": "V-Mark",
    "standard": "Standard",
    "varaflame": "Varaflame",
    "replica": "Replica",
    "armor": "Armor",
    "slim": "Slim",
    "gatsby": "Gatsby",
    "banjo": "Banjo",
    "unique": "Unique",
}

_PRETTY_MATERIAL = {
    "son_mai": "Sơn Mài",
    "silver": "Mạ Bạc",
    "sterling_silver": "Bạc Khối (Sterling)",
    "gold": "Mạ Vàng",
    "solid_gold": "Vàng Khối",
    "brass": "Đồng Thau (Brass)",
}

_PRETTY_COLOR = {
    "green": "Xanh Lá",
    "blue": "Xanh Dương",
    "red": "Đỏ",
    "black": "Đen",
    "brown": "Nâu",
    "yellow": "Vàng",
}


def format_scope_title(r: Record) -> str:
    """Tạo tiêu đề hiển thị thân thiện, chuẩn tiếng Việt cho một nhóm so sánh."""
    parts = []
    if r.brand != "unknown":
        parts.append(r.brand.capitalize())
    if r.line != "unknown":
        parts.append(_PRETTY_LINE.get(r.line, r.line.replace("_", " ").title()))
    if r.material != "unknown":
        parts.append(_PRETTY_MATERIAL.get(r.material, r.material.replace("_", " ").title()))
    if r.finish != "unknown":
        parts.append(r.finish.replace("_", " ").title())
    if r.color != "unknown":
        parts.append(_PRETTY_COLOR.get(r.color, r.color.capitalize()))
    if r.edition != "unknown":
        parts.append(r.edition.title())
    if r.box == "yes":
        parts.append("Có hộp")
    elif r.box == "no":
        parts.append("Không hộp")
    else:
        parts.append("Hộp chưa rõ")

    if r.cosmetic_condition != "unknown":
        parts.append(f"Tình trạng: {r.cosmetic_condition}")
    else:
        parts.append("Tình trạng: Chưa rõ")

    return " · ".join(parts)


def escape_fts5_query(text: str) -> str:
    """Escape các ký tự đặc biệt trong SQLite FTS5 để chống syntax error / injection."""
    sanitized = re.sub(r'[^\w\s]', ' ', text)
    tokens = [t for t in sanitized.split() if t.upper() not in ("AND", "OR", "NOT")]
    if not tokens:
        return ""
    return " ".join(f'"{t}"*' for t in tokens)


def search_records(
    conn: sqlite3.Connection,
    raw_query: str,
    page: int = 1,
    page_size: int = 5,
) -> SearchResult:
    """Tìm kiếm, phân tách nhóm so sánh và phân trang."""
    cleaned = strip_filler_words(raw_query)
    query_attrs = parse_attributes(raw_query)

    # 1. Kiểm tra màu sắc mơ hồ (ví dụ: 'xanh' trong khi DB có cả xanh lá và xanh dương)
    norm_query = strip_vietnamese_accents(raw_query)
    is_vague_xanh = (
        re.search(r"\bxanh\b", norm_query) is not None
        and "xanh la" not in norm_query
        and "xanh luc" not in norm_query
        and "xanh duong" not in norm_query
        and "xanh bien" not in norm_query
    )

    if is_vague_xanh:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT color FROM records WHERE deleted_at IS NULL AND color IN ('green', 'blue');")
        colors = [r["color"] for r in cur.fetchall()]
        if len(colors) >= 2:
            return SearchResult(
                query=raw_query,
                cleaned_query=cleaned,
                is_ambiguous=True,
                ambiguous_prompt="Anh đang muốn tìm quẹt màu Xanh lá hay Xanh dương?",
                ambiguous_options=["Xanh lá", "Xanh dương"],
                groups=[],
                similar_groups=[],
                total_groups=0,
                page=1,
            )

    # 2. Lấy tất cả bản ghi chưa xóa trong DB
    cur = conn.cursor()
    cur.execute("SELECT * FROM records WHERE deleted_at IS NULL ORDER BY created_at DESC;")
    all_rows = cur.fetchall()
    all_records = [Record.from_dict(dict(r)) for r in all_rows]

    matched_records: list[Record] = []
    similar_records: list[Record] = []

    search_tokens = clean_search_text(cleaned).split()

    for rec in all_records:
        rec_corpus = get_record_search_corpus(rec)
        
        # Kiểm tra mâu thuẫn trực tiếp (Explicit conflict)
        has_conflict = False
        if query_attrs["line"] != "unknown" and rec.line != "unknown":
            if query_attrs["line"] != rec.line:
                has_conflict = True

        if query_attrs["box"] != "unknown" and rec.box != "unknown":
            if query_attrs["box"] != rec.box:
                has_conflict = True

        if query_attrs["color"] != "unknown" and rec.color != "unknown":
            if query_attrs["color"] != rec.color:
                has_conflict = True

        if query_attrs["material"] != "unknown" and rec.material != "unknown":
            if query_attrs["material"] != rec.material:
                has_conflict = True

        # Kiểm tra độ khớp từ khóa
        all_tokens_match = True
        if search_tokens:
            all_tokens_match = all(t in rec_corpus for t in search_tokens)

        # Kiểm tra độ khớp thuộc tính
        attrs_match = True
        for attr_key in ["brand", "line", "color", "material", "box"]:
            q_val = query_attrs[attr_key]
            if q_val != "unknown":
                rec_val = getattr(rec, attr_key)
                if rec_val != q_val:
                    attrs_match = False
                    break

        if has_conflict:
            # Nếu mâu thuẫn nhưng cùng brand -> Mẫu gần giống
            if query_attrs["brand"] != "unknown" and query_attrs["brand"] == rec.brand:
                similar_records.append(rec)
        elif all_tokens_match or (attrs_match and query_attrs["brand"] != "unknown"):
            matched_records.append(rec)
        elif query_attrs["brand"] != "unknown" and query_attrs["brand"] == rec.brand:
            similar_records.append(rec)

    # 3. Gom nhóm so sánh (Grouping)
    def group_records(records_list: list[Record]) -> list[SearchGroup]:
        groups_dict: dict[str, list[Record]] = {}
        for r in records_list:
            sk = r.scope_key()
            if sk not in groups_dict:
                groups_dict[sk] = []
            groups_dict[sk].append(r)

        result_groups: list[SearchGroup] = []
        for sk, recs in groups_dict.items():
            first = recs[0]
            cap = get_bid_cap(conn, sk)
            pricing = calculate_reference_pricing(recs, cap)
            title = format_scope_title(first)
            result_groups.append(
                SearchGroup(
                    scope_key=sk,
                    display_title=title,
                    brand=first.brand,
                    line=first.line,
                    material=first.material,
                    color=first.color,
                    box=first.box,
                    condition=first.cosmetic_condition,
                    records=recs,
                    pricing=pricing,
                )
            )
        return result_groups

    matched_groups = group_records(matched_records)
    similar_groups = group_records(similar_records)

    total_groups = len(matched_groups)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_groups = matched_groups[start_idx:end_idx]

    return SearchResult(
        query=raw_query,
        cleaned_query=cleaned,
        is_ambiguous=False,
        groups=paginated_groups,
        similar_groups=similar_groups[:3],
        total_groups=total_groups,
        page=page,
        page_size=page_size,
    )
