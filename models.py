"""Định nghĩa cấu trúc dữ liệu chuẩn cho Telegram Bot Ghi Nhớ Giá Đấu Quẹt."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Record:
    id: str  # Q0001, Q0002...
    owner_user_id: int
    raw_text: str
    display_name: str
    normalized_search_text: str
    amount_jpy: int
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
    currency: str = "JPY"
    record_type: str = "win"
    price_basis: str = "pure"  # pure | all_in
    fee_jpy: int = 0
    fee_vnd: int = 0
    is_lot: bool = False
    note: str = ""
    auction_date: str | None = None  # YYYY-MM-DD
    auction_id: str | None = None
    source_url: str | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    deleted_at: str | None = None
    version: int = 1
    duplicate_of: str | None = None
    parser_version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Record:
        # Convert types safely if needed
        return cls(
            id=str(data["id"]),
            owner_user_id=int(data["owner_user_id"]),
            raw_text=str(data["raw_text"]),
            display_name=str(data["display_name"]),
            normalized_search_text=str(data["normalized_search_text"]),
            amount_jpy=int(data["amount_jpy"]),
            brand=str(data.get("brand", "unknown")),
            line=str(data.get("line", "unknown")),
            size_submodel=str(data.get("size_submodel", "unknown")),
            material=str(data.get("material", "unknown")),
            finish=str(data.get("finish", "unknown")),
            color=str(data.get("color", "unknown")),
            edition=str(data.get("edition", "unknown")),
            box=str(data.get("box", "unknown")),
            papers=str(data.get("papers", "unknown")),
            accessories_note=str(data.get("accessories_note", "")),
            cosmetic_condition=str(data.get("cosmetic_condition", "unknown")),
            functional_state=str(data.get("functional_state", "unknown")),
            authenticity_note=str(data.get("authenticity_note", "unknown")),
            currency=str(data.get("currency", "JPY")),
            record_type=str(data.get("record_type", "win")),
            price_basis=str(data.get("price_basis", "pure")),
            fee_jpy=int(data.get("fee_jpy", 0)),
            fee_vnd=int(data.get("fee_vnd", 0)),
            is_lot=bool(data.get("is_lot", False)),
            note=str(data.get("note", "")),
            auction_date=data.get("auction_date"),
            auction_id=data.get("auction_id"),
            source_url=data.get("source_url"),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
            deleted_at=data.get("deleted_at"),
            version=int(data.get("version", 1)),
            duplicate_of=data.get("duplicate_of"),
            parser_version=str(data.get("parser_version", "v1")),
        )

    def scope_key(self) -> str:
        """Sinh khóa nhóm so sánh theo đặc tả:
        brand + line + size/submodel + material/finish + color/edition + box + cosmetic_condition.
        """
        parts = [
            self.brand or "unknown",
            self.line or "unknown",
            self.size_submodel or "unknown",
            self.material or "unknown",
            self.finish or "unknown",
            self.color or "unknown",
            self.edition or "unknown",
            self.box or "unknown",
            self.cosmetic_condition or "unknown",
        ]
        return ":".join(parts).lower()


@dataclass
class BidCap:
    id: int | None
    scope_key: str
    brand: str
    line: str
    material: str
    color: str
    box: str
    condition: str
    cap_amount_jpy: int
    source_record_id: str
    is_active: bool = True
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BidCap:
        return cls(
            id=data.get("id"),
            scope_key=str(data["scope_key"]),
            brand=str(data.get("brand", "unknown")),
            line=str(data.get("line", "unknown")),
            material=str(data.get("material", "unknown")),
            color=str(data.get("color", "unknown")),
            box=str(data.get("box", "unknown")),
            condition=str(data.get("condition", "unknown")),
            cap_amount_jpy=int(data["cap_amount_jpy"]),
            source_record_id=str(data.get("source_record_id", "")),
            is_active=bool(data.get("is_active", True)),
            created_at=str(data.get("created_at", utc_now_iso())),
            updated_at=str(data.get("updated_at", utc_now_iso())),
        )


@dataclass
class RecordRevision:
    id: int | None
    record_id: str
    action: str  # create | update | delete | restore
    previous_data: str | None
    new_data: str | None
    created_at: str = field(default_factory=utc_now_iso)


@dataclass
class Draft:
    draft_id: str
    user_id: int
    draft_type: str  # ambiguous_box | missing_price | missing_desc | edit_field
    payload: dict[str, Any]
    created_at: str = field(default_factory=utc_now_iso)
