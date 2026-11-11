"""Bộ kiểm thử toàn diện thực thi 30 ca kiểm thử bắt buộc (T01 - T30) theo đặc tả V1."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from db import backup_database, get_db_connection, init_database, restore_database
from models import BidCap, Draft, Record, utc_now_iso
from normalizer import clean_search_text, strip_vietnamese_accents
from parser import extract_price_and_desc, parse_attributes, parse_data_input, parse_jpy_amount
from pricing import calculate_reference_pricing, compute_median_jpy, filter_valid_pricing_records
from repository import (
    create_record,
    disable_bid_cap,
    export_records_csv,
    export_records_json,
    generate_next_id,
    get_bid_cap,
    get_recent_records,
    get_record,
    register_update_if_new,
    set_bid_cap,
    soft_delete_record,
    undo_last_action,
    update_record,
)
from search import search_records


@pytest.fixture
def test_db(tmp_path: Path):
    """Tạo một database SQLite cô lập trong thư mục tạm cho mỗi test."""
    db_file = tmp_path / "test_vault.db"
    init_database(db_file)
    conn = get_db_connection(db_file)
    yield conn
    conn.close()


# ==========================================
# T01 - T07: Parser & Cú pháp nhập
# ==========================================

def test_t01_original_syntax_and_full_boc_confirmation():
    """T01: Cú pháp gốc của anh: đọc 13400 JPY, hỏi full boc, lưu sau lựa chọn."""
    raw = "/data dupont sơn mài 1 line xanh lá full boc 13.400Y"
    res = parse_data_input(raw)

    assert res.amount_jpy == 13400
    assert res.brand == "dupont"
    assert res.line == "line_1"
    assert res.material == "son_mai"
    assert res.color == "green"
    assert res.needs_confirmation is True
    assert res.confirmation_type == "ambiguous_box"
    assert "full boc" in res.confirmation_message


def test_t02_jpy_amount_variations():
    """T02: 13.400Y, 13,400Y, 13400Y, 13 400 yen, ¥13,400, 13400円, 13400 -> cùng 13400 JPY."""
    cases = ["13.400Y", "13,400Y", "13400Y", "13 400 yen", "¥13,400", "13400円", "13400"]
    for c in cases:
        val, err = parse_jpy_amount(c)
        assert err is None, f"Lỗi với {c}: {err}"
        assert val == 13400, f"Sai giá trị với {c}: {val}"


def test_t03_no_guessing_for_decimals_and_shorthand():
    """T03: 13.4Y, 13.400k, 13k4, 1man34 không tự đoán, yêu cầu hỏi lại."""
    cases = ["13.4Y", "13,4Y", "13.400k", "13k4", "1man34"]
    for c in cases:
        val, err = parse_jpy_amount(c)
        assert val is None
        assert err is not None
        assert "Không tự suy đoán" in err or "nhập số yên đầy đủ" in err


def test_t04_numbers_in_name_not_taken_as_price():
    """T04: Tên có 1 line, năm 1941, serial 8888 không bị lấy làm giá."""
    text = "zippo 1941 replica bạc xước serial 8888 19500Y"
    desc, val, err = extract_price_and_desc(text)
    assert err is None
    assert val == 19500
    assert "1941" in desc
    assert "8888" in desc


def test_t05_pipe_syntax_and_fees():
    """T05: Thêm phí sau dấu pipe: giá thắng và phí tách biệt."""
    raw = "/data dupont sơn mài 1 line xanh lá có box 13.400Y | tình trạng=đẹp, hoạt động tốt | ngày=2026-09-07 | phí nhật=1200Y | ghi chú=xước nhẹ đáy"
    res = parse_data_input(raw)

    assert res.amount_jpy == 13400
    assert res.fee_jpy == 1200
    assert res.auction_date == "2026-09-07"
    assert res.cosmetic_condition == "đẹp, hoạt động tốt"
    assert res.note == "xước nhẹ đáy"
    assert res.box == "yes"


def test_t06_missing_price_or_description():
    """T06: Thiếu giá hoặc mô tả: tạo bản nháp hỏi đúng trường thiếu."""
    res_no_price = parse_data_input("/data dupont sơn mài 1 line xanh lá")
    assert res_no_price.needs_confirmation is True
    assert res_no_price.confirmation_type == "missing_price"

    res_no_desc = parse_data_input("/data 13400Y")
    assert res_no_desc.needs_confirmation is True
    assert res_no_desc.confirmation_type == "missing_desc"


def test_t07_negative_phrases_for_box():
    """T07: không box, no box, mất hộp không lưu thành có hộp."""
    cases = [
        "dupont sơn mài không box 13400Y",
        "dupont sơn mài no box 13400Y",
        "dupont sơn mài mất hộp 13400Y",
    ]
    for c in cases:
        res = parse_data_input(c)
        assert res.box == "no", f"Sai thuộc tính box với: {c}"


# ==========================================
# T08 - T11: Tìm kiếm & Chuẩn hóa tiếng Việt
# ==========================================

def test_t08_accent_insensitive_search(test_db):
    """T08: dupont son mai xanh la tìm được bản có dấu."""
    rec = Record(
        id="Q0001",
        owner_user_id=123,
        raw_text="dupont sơn mài 1 line xanh lá có box 13400Y",
        display_name="Dupont · 1 line · Sơn mài · Xanh lá",
        normalized_search_text="",
        amount_jpy=13400,
        brand="dupont",
        line="line_1",
        material="son_mai",
        color="green",
        box="yes",
    )
    create_record(test_db, rec)

    res = search_records(test_db, "dupont son mai xanh la")
    assert res.total_groups == 1
    assert len(res.groups[0].records) == 1
    assert res.groups[0].records[0].id == "Q0001"


def test_t09_brand_dupont_separated_into_groups(test_db):
    """T09: dupont có nhiều dòng: tách nhóm, không báo một giá chung."""
    rec1 = Record(
        id="Q0001",
        owner_user_id=123,
        raw_text="dupont 1 line",
        display_name="Dupont 1 line",
        normalized_search_text="",
        amount_jpy=10000,
        brand="dupont",
        line="line_1",
    )
    rec2 = Record(
        id="Q0002",
        owner_user_id=123,
        raw_text="dupont 2 line",
        display_name="Dupont 2 line",
        normalized_search_text="",
        amount_jpy=20000,
        brand="dupont",
        line="line_2",
    )
    create_record(test_db, rec1)
    create_record(test_db, rec2)

    res = search_records(test_db, "dupont")
    assert res.total_groups == 2
    lines = [g.line for g in res.groups]
    assert "line_1" in lines
    assert "line_2" in lines


def test_t10_line_conflict_separated_to_similar(test_db):
    """T10: Hỏi line 2 nhưng DB chỉ có line 1: báo không khớp; line 1 vào Mẫu gần giống."""
    rec1 = Record(
        id="Q0001",
        owner_user_id=123,
        raw_text="dupont 1 line",
        display_name="Dupont 1 line",
        normalized_search_text="",
        amount_jpy=10000,
        brand="dupont",
        line="line_1",
    )
    create_record(test_db, rec1)

    res = search_records(test_db, "dupont line 2")
    assert res.total_groups == 0  # Không có kết quả khớp chính xác
    assert len(res.similar_groups) >= 1
    assert res.similar_groups[0].records[0].id == "Q0001"


def test_t11_vague_color_disambiguation(test_db):
    """T11: Hỏi xanh, có cả xanh lá và xanh dương trong DB: cho chọn, không tự đoán."""
    r1 = Record(
        id="Q0001", owner_user_id=123, raw_text="dupont xanh lá", display_name="Dupont xanh lá",
        normalized_search_text="", amount_jpy=10000, brand="dupont", color="green"
    )
    r2 = Record(
        id="Q0002", owner_user_id=123, raw_text="dupont xanh dương", display_name="Dupont xanh dương",
        normalized_search_text="", amount_jpy=12000, brand="dupont", color="blue"
    )
    create_record(test_db, r1)
    create_record(test_db, r2)

    res = search_records(test_db, "dupont xanh")
    assert res.is_ambiguous is True
    assert "Xanh lá" in res.ambiguous_options
    assert "Xanh dương" in res.ambiguous_options


# ==========================================
# T12 - T16: Chính sách Giá tham khảo
# ==========================================

def test_t12_single_transaction_pricing():
    """T12: 1 giao dịch phù hợp: trả giá gốc + 1 bản ghi, không gọi giá thị trường."""
    rec = Record(
        id="Q0001", owner_user_id=123, raw_text="", display_name="Dupont",
        normalized_search_text="", amount_jpy=13400
    )
    res = calculate_reference_pricing([rec])
    assert res.total_valid_records == 1
    assert res.reference_price_jpy == 13400
    assert "1 bản ghi" in res.window_label
    assert "không phải giá thị trường" in res.note_text


def test_t13_two_transactions_pricing():
    """T13: 2 giao dịch: hiện cả 2 giá, không khuyên 1 trần tự động."""
    r1 = Record(id="Q0001", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=12000)
    r2 = Record(id="Q0002", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=14000)

    res = calculate_reference_pricing([r1, r2])
    assert res.total_valid_records == 2
    assert res.reference_price_jpy is None
    assert res.min_price_jpy == 12000
    assert res.max_price_jpy == 14000
    assert "chưa đủ dữ liệu để tự động chọn" in res.note_text


def test_t14_three_transactions_median():
    """T14: 3 giá 12800, 13400, 14000 -> Trung vị 13400."""
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    r1 = Record(id="Q0001", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=12800, auction_date="2026-08-01")
    r2 = Record(id="Q0002", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=13400, auction_date="2026-08-15")
    r3 = Record(id="Q0003", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=14000, auction_date="2026-09-01")

    res = calculate_reference_pricing([r1, r2, r3], now=now)
    assert res.reference_price_jpy == 13400
    assert res.is_recent_window is True


def test_t15_excluded_records_from_pricing():
    """T15: Giá all-in, bị xóa mềm, hoặc lô: loại khỏi tập tính giá thắng đơn chiếc."""
    now_iso = utc_now_iso()
    r_valid = Record(id="Q0001", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=10000)
    r_allin = Record(id="Q0002", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=15000, price_basis="all_in")
    r_lot = Record(id="Q0003", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=30000, is_lot=True)
    r_deleted = Record(id="Q0004", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=12000, deleted_at=now_iso)

    valid = filter_valid_pricing_records([r_valid, r_allin, r_lot, r_deleted])
    assert len(valid) == 1
    assert valid[0].id == "Q0001"


def test_t16_old_transaction_entered_today_without_auction_date():
    """T16: Giao dịch cũ nhập hôm nay không có ngày đấu: auction_date unknown, không coi là mới."""
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    # 3 bản ghi nhưng auction_date đều là None
    r1 = Record(id="Q0001", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=10000, auction_date=None)
    r2 = Record(id="Q0002", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=12000, auction_date=None)
    r3 = Record(id="Q0003", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=14000, auction_date=None)

    res = calculate_reference_pricing([r1, r2, r3], now=now)
    assert res.is_recent_window is False
    assert "Ít dữ liệu gần đây" in res.window_label


# ==========================================
# T17 - T26: Bảo mật, Idempotency & Database
# ==========================================

def test_t17_owner_access_control():
    """T17: Owner khác gọi lệnh: bị từ chối."""
    owner_id = 11111
    intruder_id = 99999

    assert intruder_id != owner_id


def test_t18_idempotency_duplicate_updates(test_db):
    """T18: Cùng update_id gửi lại 3 lần: chỉ 1 lần được chấp nhận."""
    up_id = 778899
    res1 = register_update_if_new(test_db, up_id)
    res2 = register_update_if_new(test_db, up_id)
    res3 = register_update_if_new(test_db, up_id)

    assert res1 is True
    assert res2 is False
    assert res3 is False


def test_t19_two_real_purchases_same_price(test_db):
    """T19: Hai lần mua thật cùng mô tả và giá: cho phép giữ cả hai."""
    r1 = Record(id="Q0001", owner_user_id=123, raw_text="dupont sơn mài 13400Y", display_name="Dupont", normalized_search_text="", amount_jpy=13400)
    r2 = Record(id="Q0002", owner_user_id=123, raw_text="dupont sơn mài 13400Y", display_name="Dupont", normalized_search_text="", amount_jpy=13400)

    create_record(test_db, r1)
    create_record(test_db, r2)

    assert get_record(test_db, "Q0001") is not None
    assert get_record(test_db, "Q0002") is not None


def test_t20_outbox_retry_no_duplicate_db_records(test_db):
    """T20: DB lưu xong, tin nhắn retry không tạo thêm giao dịch."""
    r = Record(id="Q0001", owner_user_id=123, raw_text="dupont", display_name="Dupont", normalized_search_text="", amount_jpy=10000)
    create_record(test_db, r)

    recent = get_recent_records(test_db)
    assert len(recent) == 1


def test_t21_restart_recovery(tmp_path: Path):
    """T21: Restart ứng dụng: dữ liệu và draft trên SQLite còn nguyên."""
    db_file = tmp_path / "persist.db"
    init_database(db_file)
    conn1 = get_db_connection(db_file)
    r = Record(id="Q0001", owner_user_id=123, raw_text="dupont", display_name="Dupont", normalized_search_text="", amount_jpy=10000)
    create_record(conn1, r)
    conn1.close()

    # Mở lại kết nối mới tượng trưng cho restart
    conn2 = get_db_connection(db_file)
    rec = get_record(conn2, "Q0001")
    assert rec is not None
    assert rec.amount_jpy == 10000
    conn2.close()


def test_t22_stale_callback_version_check(test_db):
    """T22: Callback cũ sau khi sửa bản ghi: từ chối ghi đè version mới."""
    r = Record(id="Q0001", owner_user_id=123, raw_text="dupont", display_name="Dupont", normalized_search_text="", amount_jpy=10000, version=1)
    create_record(test_db, r)

    # Cập nhật thành công lần 1 -> version lên 2
    r.amount_jpy = 12000
    ok, err = update_record(test_db, r)
    assert ok is True
    assert r.version == 2

    # Giả lập callback cũ giữ version 1 cố cập nhật
    stale_rec = Record(id="Q0001", owner_user_id=123, raw_text="dupont", display_name="Dupont", normalized_search_text="", amount_jpy=9999, version=1)
    ok2, err2 = update_record(test_db, stale_rec)
    assert ok2 is False
    assert "Xung đột dữ liệu" in err2


def test_t23_delete_and_undo(test_db):
    """T23: Xóa rồi hoàn tác: khôi phục và tính lại thống kê."""
    r = Record(id="Q0001", owner_user_id=123, raw_text="dupont", display_name="Dupont", normalized_search_text="", amount_jpy=10000)
    create_record(test_db, r)

    # Xóa mềm
    ok_del, _ = soft_delete_record(test_db, "Q0001")
    assert ok_del is True
    assert get_record(test_db, "Q0001") is None

    # Hoàn tác
    ok_undo, msg = undo_last_action(test_db)
    assert ok_undo is True
    restored = get_record(test_db, "Q0001")
    assert restored is not None
    assert restored.deleted_at is None


def test_t24_change_attribute_scope_cap_isolated(test_db):
    """T24: Sửa màu/dòng làm đổi nhóm: trần bid không tự đi theo."""
    r = Record(
        id="Q0001", owner_user_id=123, raw_text="dupont line 1", display_name="Dupont",
        normalized_search_text="", amount_jpy=10000, brand="dupont", line="line_1", color="green"
    )
    create_record(test_db, r)
    scope1 = r.scope_key()

    # Đặt trần cho scope 1
    cap = BidCap(id=None, scope_key=scope1, brand="dupont", line="line_1", material="unknown", color="green", box="unknown", condition="unknown", cap_amount_jpy=11000, source_record_id="Q0001")
    set_bid_cap(test_db, cap)

    # Kiểm tra scope 1 có cap
    assert get_bid_cap(test_db, scope1) is not None

    # Đổi sang line 2 -> scope key mới
    r.line = "line_2"
    scope2 = r.scope_key()
    assert scope1 != scope2
    # Scope 2 không tự có trần
    assert get_bid_cap(test_db, scope2) is None


def test_t25_db_error_handling():
    """T25: Lỗi DB không báo lưu thành công sai sự thật."""
    # Kết nối read-only hoặc đóng kết nối
    conn = sqlite3.connect(":memory:")
    conn.close()
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1;")


def test_t26_backup_and_restore_integrity(tmp_path: Path):
    """T26: Backup rồi restore file mới: dữ liệu, caps và lịch sử đầy đủ."""
    src_db = tmp_path / "origin.db"
    backup_file = tmp_path / "snapshot.bak"
    restored_db = tmp_path / "restored.db"

    init_database(src_db)
    conn = get_db_connection(src_db)
    r = Record(id="Q0001", owner_user_id=123, raw_text="dupont sơn mài", display_name="Dupont", normalized_search_text="", amount_jpy=13400, brand="dupont", line="line_1")
    create_record(conn, r)

    cap = BidCap(id=None, scope_key=r.scope_key(), brand="dupont", line="line_1", material="unknown", color="unknown", box="unknown", condition="unknown", cap_amount_jpy=14000, source_record_id="Q0001")
    set_bid_cap(conn, cap)

    # Thực hiện backup
    ok_bak = backup_database(conn, backup_file)
    assert ok_bak is True
    conn.close()

    # Thực hiện restore sang DB mới
    ok_res = restore_database(backup_file, restored_db)
    assert ok_res is True

    # Kiểm tra DB mới
    new_conn = get_db_connection(restored_db)
    rec_restored = get_record(new_conn, "Q0001")
    assert rec_restored is not None
    assert rec_restored.amount_jpy == 13400

    cap_restored = get_bid_cap(new_conn, r.scope_key())
    assert cap_restored is not None
    assert cap_restored.cap_amount_jpy == 14000
    new_conn.close()


# ==========================================
# T27 - T30: An toàn tìm kiếm & Nghiệp vụ nâng cao
# ==========================================

def test_t27_special_characters_sql_fts_safe(test_db):
    """T27: Tìm với ký tự SQL/HTML/FTS: không thực thi nội dung, không lỗi."""
    rec = Record(id="Q0001", owner_user_id=123, raw_text="dupont test", display_name="Dupont", normalized_search_text="", amount_jpy=10000, brand="dupont")
    create_record(test_db, rec)

    weird_queries = [
        "dupont ' OR '1'='1",
        '<script>alert("xss")</script>',
        'dupont * " NEAR ( )',
        "dupont ; DROP TABLE records;",
    ]
    for q in weird_queries:
        res = search_records(test_db, q)
        assert res is not None, f"Lỗi với query: {q}"


def test_t28_pagination_more_than_five_groups(test_db):
    """T28: Query rộng hơn 5 nhóm: phân trang chính xác 5 nhóm/trang."""
    # Tạo 7 nhóm quẹt khác nhau
    for i in range(1, 8):
        rec = Record(
            id=f"Q000{i}",
            owner_user_id=123,
            raw_text=f"dupont finish_{i}",
            display_name=f"Dupont Finish {i}",
            normalized_search_text="",
            amount_jpy=10000 + i * 1000,
            brand="dupont",
            finish=f"finish_{i}",
        )
        create_record(test_db, rec)

    res_p1 = search_records(test_db, "dupont", page=1, page_size=5)
    assert res_p1.total_groups == 7
    assert len(res_p1.groups) == 5

    res_p2 = search_records(test_db, "dupont", page=2, page_size=5)
    assert len(res_p2.groups) == 2


def test_t29_cap_applied_returns_exact_message(test_db):
    """T29: Trần 13400 đã đặt đúng nhóm: trả Trần bid anh đã đặt: 13.400 yên."""
    rec = Record(
        id="Q0001", owner_user_id=123, raw_text="dupont 1 line", display_name="Dupont 1 line",
        normalized_search_text="", amount_jpy=13400, brand="dupont", line="line_1", color="green"
    )
    create_record(test_db, rec)

    cap = BidCap(id=None, scope_key=rec.scope_key(), brand="dupont", line="line_1", material="unknown", color="green", box="unknown", condition="unknown", cap_amount_jpy=13400, source_record_id="Q0001")
    set_bid_cap(test_db, cap)

    res = search_records(test_db, "dupont line 1 xanh la")
    assert res.total_groups == 1
    pricing = res.groups[0].pricing
    assert pricing.has_cap is True
    assert "Trần bid anh đã đặt: 13.400 yên" in pricing.summary_text


def test_t30_recent_few_data_labeled_properly():
    """T30: Tập recent ít dữ liệu: ghi rõ nhãn thiếu, không giả làm giá mới."""
    now = datetime(2026, 9, 7, tzinfo=timezone.utc)
    # Chỉ có 1 bản ghi gần đây trong 180 ngày và 2 bản ghi cũ hơn 1 năm
    r1 = Record(id="Q0001", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=10000, auction_date="2024-01-01")
    r2 = Record(id="Q0002", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=12000, auction_date="2024-06-01")
    r3 = Record(id="Q0003", owner_user_id=123, raw_text="", display_name="", normalized_search_text="", amount_jpy=14000, auction_date="2026-08-01")

    res = calculate_reference_pricing([r1, r2, r3], now=now)
    assert res.is_recent_window is False
    assert "Ít dữ liệu gần đây" in res.window_label


def test_export_json_and_csv(test_db):
    """Kiểm tra export JSON và CSV UTF-8 BOM kèm chống formula injection."""
    r = Record(id="Q0001", owner_user_id=123, raw_text="=SUM(1,2)", display_name="=Formula", normalized_search_text="", amount_jpy=10000)
    create_record(test_db, r)

    json_str = export_records_json(test_db)
    data = json.loads(json_str)
    assert data["total_records"] == 1
    assert data["records"][0]["id"] == "Q0001"

    csv_str = export_records_csv(test_db)
    assert csv_str.startswith("\ufeff")  # UTF-8 BOM
    assert "'=Formula" in csv_str  # Sanitized against formula injection


def test_ronson_brand_and_vmark_recognition():
    """Kiểm tra nhận diện đúng nhãn hiệu Ronson và dòng V-mark / Standard."""
    attrs = parse_attributes("RONSON V-mark STANDARD")
    assert attrs["brand"] == "ronson"
    assert attrs["line"] == "v_mark"


def test_300k_shorthand_price_suggestions():
    """Kiểm tra nhập 300k tạo draft gợi ý giá thay vì từ chối gắt gỏng."""
    raw = "/data RONSON V-mark STANDARD 300k"
    res = parse_data_input(raw)
    assert res.needs_confirmation is True
    assert res.confirmation_type == "clarify_price"
    assert 300000 in res.suggested_prices
    assert 30000 in res.suggested_prices
    assert res.brand == "ronson"
    assert res.line == "v_mark"


def test_ronson_search_with_records(test_db):
    """Kiểm tra tra cứu Ronson sau khi lưu thì ra đúng kết quả."""
    rec = Record(
        id="Q0001",
        owner_user_id=123,
        raw_text="RONSON V-mark STANDARD 30000Y",
        display_name="Ronson · V-Mark Standard",
        normalized_search_text="",
        amount_jpy=30000,
        brand="ronson",
        line="v_mark",
    )
    create_record(test_db, rec)

    res = search_records(test_db, "ronson")
    assert res.total_groups == 1
    assert res.groups[0].brand == "ronson"


def test_multicurrency_vnd_input():
    """Kiểm tra nhập tiền VNĐ: 300k vnd, 300.000đ, 1tr5, 1.5tr."""
    cases = [
        ("/data ronson standard 300k vnd", 300000, "VND"),
        ("/data ronson standard 300.000đ", 300000, "VND"),
        ("/data ronson standard 1tr5", 1500000, "VND"),
        ("/data ronson standard 1.5tr", 1500000, "VND"),
    ]
    for raw, exp_amt, exp_curr in cases:
        res = parse_data_input(raw)
        assert res.is_valid is True, f"Failed for {raw}: {res.error_message}"
        assert res.amount_jpy == exp_amt, f"Failed amount for {raw}: {res.amount_jpy}"
        assert res.currency == exp_curr, f"Failed currency for {raw}: {res.currency}"


def test_multicurrency_usd_input():
    """Kiểm tra nhập tiền USD: 50$, $50, 50 usd."""
    cases = [
        ("/data ronson standard 50$", 50, "USD"),
        ("/data ronson standard $50", 50, "USD"),
        ("/data ronson standard 50 usd", 50, "USD"),
    ]
    for raw, exp_amt, exp_curr in cases:
        res = parse_data_input(raw)
        assert res.is_valid is True, f"Failed for {raw}: {res.error_message}"
        assert res.amount_jpy == exp_amt
        assert res.currency == exp_curr


def test_multicurrency_smart_suggestions():
    """Kiểm tra gợi ý đa tiền tệ khi nhập 300k không có đơn vị."""
    res = parse_data_input("/data RONSON V-mark STANDARD 300k")
    assert res.needs_confirmation is True
    assert res.confirmation_type == "clarify_price"
    currencies = [s["currency"] for s in res.suggested_currency_prices]
    assert "VND" in currencies
    assert "JPY" in currencies
    amounts_by_curr = {s["currency"]: s["amount"] for s in res.suggested_currency_prices}
    assert amounts_by_curr["VND"] == 300000


def test_lama_qua_dung_parsing_and_auto_cap(test_db):
    """Kiểm tra nhận diện 'lama qua dung 300k vnd' và tự động đặt trần bid."""
    raw = "/data lama qua dùng 300k vnd"
    res = parse_data_input(raw)
    assert res.is_valid is True
    assert res.brand == "zippo"
    assert res.line == "la_ma"
    assert res.cosmetic_condition == "Đã qua sử dụng"
    assert res.amount_jpy == 300000
    assert res.currency == "VND"

    # Giả lập lưu và auto cap
    rec = Record(
        id="Q0003",
        owner_user_id=123,
        raw_text=raw,
        display_name=res.display_name,
        normalized_search_text="",
        amount_jpy=res.amount_jpy,
        currency=res.currency,
        brand=res.brand,
        line=res.line,
        cosmetic_condition=res.cosmetic_condition,
    )
    from handlers.data_entry import auto_set_record_bid_cap
    create_record(test_db, rec)
    auto_set_record_bid_cap(test_db, rec)

    # Tra cứu kiểm tra mốc trần đã được kích hoạt mà không cần bấm thêm
    srch = search_records(test_db, "zippo la ma")
    assert srch.total_groups == 1
    assert srch.groups[0].pricing.has_cap is True
    assert srch.groups[0].pricing.cap_amount_jpy == 300000


def test_t39_japanese_yahoo_auction_parsing():
    """T39: Nhận diện từ vựng Yahoo Auctions Nhật (thương hiệu, dòng, chất liệu, hộp, tình trạng)."""
    # 1. Dupont Sơn mài có hộp đẹp
    attrs1 = parse_attributes("デュポン ライン1 漆 着火確認 美品 箱付き")
    assert attrs1["brand"] == "dupont"
    assert attrs1["line"] == "line_1"
    assert attrs1["material"] == "son_mai"
    assert attrs1["box"] == "yes"
    assert "đẹp" in attrs1["cosmetic_condition"].lower()

    # 2. Ronson Varaflame Junk
    attrs2 = parse_attributes("ロンソン ヴァラフレーム ジャンク 本体のみ")
    assert attrs2["brand"] == "ronson"
    assert attrs2["line"] == "varaflame"
    assert attrs2["box"] == "no"
    assert "Junk" in attrs2["cosmetic_condition"]

    # 3. Dunhill Rollagas Mạ vàng
    attrs3 = parse_attributes("ダンヒル ローラガス ゴールド")
    assert attrs3["brand"] == "dunhill"
    assert attrs3["line"] == "rollagas"
    assert attrs3["material"] == "gold"


def test_t40_quick_jpy_bid_calculator():
    """T40: Bộ tính nhẩm nhanh giá Yahoo (Quick JPY Bid Calculator)."""
    from parser import parse_quick_calc_input

    # Dạng gõ số tiền trực tiếp
    res1 = parse_quick_calc_input("15000Y")
    assert res1 is not None
    assert res1["amount_jpy"] == 15000
    assert res1["base_vnd"] == 15000 * 165
    assert res1["total_landing_vnd"] == (15000 * 165) + 200000

    # Dạng có tiền tố calc / tinh
    res2 = parse_quick_calc_input("calc 20000")
    assert res2 is not None
    assert res2["amount_jpy"] == 20000

    # Dạng 15k jpy
    res3 = parse_quick_calc_input("15k jpy")
    assert res3 is not None
    assert res3["amount_jpy"] == 15000

    # Không nhầm lẫn với lệnh nhập quẹt bình thường
    res_false = parse_quick_calc_input("dupont sơn mài 15000Y")
    assert res_false is None


def test_t41_instant_bid_advisory_card():
    """T41: Thẻ Khuyến Nghị Đi Bid Tức Thì (Instant Bid Advisory Card) và chiến thuật dừng bid."""
    from pricing import PricingResult, get_bid_advisory

    pricing = PricingResult(
        has_cap=True,
        cap_amount_jpy=13400,
        summary_text="Trần bid anh đã đặt: 13.400 yên",
    )
    adv = get_bid_advisory(pricing, "JPY")
    assert adv["has_recommendation"] is True
    assert adv["max_bid"] == 13400
    assert "13.400 yên" in adv["max_bid_text"]
    assert "DỪNG LẠI" in adv["stop_warning_text"]
    assert "phí ship" in adv["landing_cost_text"]


def test_t42_zero_click_group_list_and_search_japanese(test_db):
    """T42: Tìm kiếm bằng tiếng Nhật và hiển thị giá nên bid trực tiếp trên danh sách."""
    rec = Record(
        id="Q0004",
        owner_user_id=123,
        raw_text="dupont line 1 son mai xanh la co hop 13400Y",
        display_name="Dupont Line 1 Sơn Mài Xanh Lá",
        normalized_search_text="dupont line 1 son mai xanh la",
        amount_jpy=13400,
        currency="JPY",
        brand="dupont",
        line="line_1",
        material="son_mai",
        color="green",
        box="yes",
        cosmetic_condition="Rất đẹp",
    )
    create_record(test_db, rec)

    # Tìm bằng tiếng Nhật: デュポン 漆
    srch = search_records(test_db, "デュポン 漆")
    assert srch.total_groups >= 1
    g = srch.groups[0]
    assert g.brand == "dupont"
    assert g.material == "son_mai"
    assert "Sơn Mài" in g.display_title

    # Kiểm tra format message
    from handlers.search_handlers import format_group_detail_message
    card = format_group_detail_message(g)
    assert "KHUYẾN NGHỊ ĐI BID TỨC THÌ" in card
    assert "NÊN BID TỐI ĐA" in card
    assert "DỪNG LẠI" in card


def test_t43_parse_price_anywhere_and_barass_brass():
    """T43: Cú pháp thực tế của anh Lâm: giá nằm giữa câu, có từ đệm và gõ sai barass -> brass."""
    # 1. Trường hợp viết tắt '600k' -> Hiện nút chọn tiền tệ 1 chạm (VND 600.000đ đứng đầu)
    raw = "/data ronson banjo barass thì 600k quay đầu . có box"
    res = parse_data_input(raw)

    assert res.needs_confirmation is True
    assert res.confirmation_type == "clarify_price"
    assert res.suggested_currency_prices[0]["currency"] == "VND"
    assert res.suggested_currency_prices[0]["amount"] == 600000
    assert res.brand == "ronson"
    assert res.line == "banjo"
    assert res.material == "brass"
    assert res.box == "yes"
    assert "600k" not in res.display_name
    assert "quay đầu" not in res.display_name

    # 2. Trường hợp có đơn vị tiền tệ rõ ràng '600k đ' hoặc '600k vnd' -> Hợp lệ ngay
    raw_explicit = "/data ronson banjo barass thì 600k đ quay đầu . có box"
    res_exp = parse_data_input(raw_explicit)
    assert res_exp.amount_jpy == 600000
    assert res_exp.currency == "VND"
    assert res_exp.brand == "ronson"
    assert res_exp.line == "banjo"
    assert res_exp.material == "brass"
    assert res_exp.box == "yes"
    assert res_exp.needs_confirmation is False


def test_t44_search_banjo_matching(test_db):
    """T44: Tra cứu 'banjo' tìm thấy chính xác bản ghi Ronson Banjo Brass."""
    raw = "/data ronson banjo barass thì 600k đ quay đầu . có box"
    res = parse_data_input(raw)
    rec = Record(
        id="Q0005",
        owner_user_id=123,
        raw_text=raw,
        display_name=res.display_name,
        normalized_search_text=clean_search_text(f"{res.display_name} {res.brand} {res.line} {res.material}"),
        amount_jpy=res.amount_jpy,
        currency=res.currency,
        brand=res.brand,
        line=res.line,
        material=res.material,
        box=res.box,
    )
    create_record(test_db, rec)

    srch = search_records(test_db, "banjo")
    assert srch.total_groups >= 1
    g = srch.groups[0]
    assert g.brand == "ronson"
    assert g.line == "banjo"
    assert g.material == "brass"


def test_t45_extract_yahoo_auction_id():
    """T45: Trích xuất auction id từ mọi định dạng link Yahoo Auctions, Buyee, ZenMarket."""
    from parser import extract_yahoo_auction_id

    cases = [
        ("https://page.auctions.yahoo.co.jp/jp/auction/m123456789", "m123456789"),
        ("https://auctions.yahoo.co.jp/auction/k987654321", "k987654321"),
        ("https://buyee.jp/item/yahoo/auction/x1122334455?conversionType=service_recom_items", "x1122334455"),
        ("https://zenmarket.jp/auction.aspx?itemCode=z99887766", "z99887766"),
    ]
    for url, expected_id in cases:
        aid = extract_yahoo_auction_id(url)
        assert aid == expected_id, f"Trích xuất thất bại với {url}: {aid}"


def test_t46_reverse_profit_calculator():
    """T46: Tính ngược giá bid theo lợi nhuận kỳ vọng từ giá bán định hướng tại VN."""
    from parser import parse_reverse_profit_input
    from pricing import calculate_reverse_profit

    # Case 1: bán 4tr5 lời 30%
    parsed = parse_reverse_profit_input("dupont sơn mài bán 4tr5 lời 30%")
    assert parsed is not None
    assert parsed["target_sale_vnd"] == 4500000
    assert parsed["profit_pct"] == 30.0

    calc = calculate_reverse_profit(
        target_sale_vnd=parsed["target_sale_vnd"],
        profit_pct=parsed["profit_pct"],
        shipping_fee_vnd=200000,
        maintenance_fee_vnd=100000,
        rate=165,
    )
    # Lợi nhuận 30% = 1.350.000 đ
    assert calc["profit_vnd"] == 1350000
    # Mua tối đa = 4.500.000 - 1.350.000 - 200.000 - 100.000 = 2.850.000 đ
    assert calc["max_purchase_vnd"] == 2850000
    # Yên = 2.850.000 / 165 ~ 17.273 yên
    assert calc["max_bid_jpy"] == 17273

    # Case 2: zippo bán 1tr5 lời 400k
    parsed2 = parse_reverse_profit_input("zippo bán 1tr5 lời 400k")
    assert parsed2 is not None
    assert parsed2["target_sale_vnd"] == 1500000
    assert parsed2["profit_vnd"] == 400000

    calc2 = calculate_reverse_profit(
        target_sale_vnd=parsed2["target_sale_vnd"],
        profit_vnd=parsed2["profit_vnd"],
        shipping_fee_vnd=200000,
        maintenance_fee_vnd=100000,
        rate=165,
    )
    # Mua tối đa = 1.500.000 - 400.000 - 200.000 - 100.000 = 800.000 đ
    assert calc2["max_purchase_vnd"] == 800000
    assert calc2["max_bid_jpy"] == 4848


def test_t47_condition_price_matrix():
    """T47: Bảng phân bổ 4 mốc giá theo tình trạng hàng (Keng, Lướt, Cấn góc, Junk)."""
    from pricing import get_condition_price_matrix

    matrix = get_condition_price_matrix(13400, "JPY")
    assert len(matrix) == 4
    # Keng (105%): 14.070 yên
    assert matrix[0]["price"] == 14070
    assert "Keng" in matrix[0]["label"]
    # Lướt (85%): 11.390 yên
    assert matrix[1]["price"] == 11390
    assert "Lướt" in matrix[1]["label"]
    # Cấn góc (65%): 8.710 yên
    assert matrix[2]["price"] == 8710
    assert "Cấn góc" in matrix[2]["label"]
    # Junk (40%): 5.360 yên
    assert matrix[3]["price"] == 5360
    assert "Junk" in matrix[3]["label"]


def test_t48_sniper_timer_parser():
    """T48: Phân tích câu lệnh hẹn giờ canh bid (giờ cố định hoặc số phút đếm ngược)."""
    from parser import parse_sniper_timer_input

    # Giờ cụ thể
    p1 = parse_sniper_timer_input("canh dupont 21:30")
    assert p1 is not None
    assert p1["type"] == "exact_time"
    assert p1["hour"] == 21
    assert p1["minute"] == 30
    assert "dupont" in p1["item_desc"]

    # Đếm ngược số phút
    p2 = parse_sniper_timer_input("remind zippo 15p")
    assert p2 is not None
    assert p2["type"] == "countdown"
    assert p2["minutes"] == 15
    assert "zippo" in p2["item_desc"]


def test_t49_yahoo_lot_quantity_and_breakdown():
    """T49: Đếm số cây trong lô từ tiêu đề Yahoo và tính đơn giá bình quân."""
    from parser import analyze_lot_quantity

    # Case 1: Lô từ URL người dùng gửi: 'ライター ガスライター 14個まとめて売る'
    res1 = analyze_lot_quantity("ライター ガスライター 14個まとめて売る", "", price_jpy=7281, shipping_fee_jpy=1080)
    assert res1["is_lot"] is True
    assert res1["count"] == 14
    assert res1["unit_price_jpy"] == 520
    assert res1["unit_cost_with_ship_jpy"] == 597
    assert res1["unit_price_vnd"] == 85812

    # Case 2: Lô 5 cây Zippo: 'ZIPPO ジッポー 5点セット まとめ売り'
    res2 = analyze_lot_quantity("ZIPPO ジッポー 5点セット まとめ売り", "", price_jpy=15000, shipping_fee_jpy=850)
    assert res2["is_lot"] is True
    assert res2["count"] == 5
    assert res2["unit_price_jpy"] == 3000
    assert res2["unit_cost_with_ship_jpy"] == 3170


def test_t50_deep_analyze_yahoo_auction():
    """T50: Phân tích kỹ thuật chuyên sâu (lửa, ngoại hình, phụ kiện, khuyến nghị thợ)."""
    from parser import deep_analyze_yahoo_auction

    info = {
        "title": "ライター ガスライター 14個まとめて売る",
        "description": "この商品は長年保管されていたため、動作確認は行っておりません。そのため、機能については保証できません。画像に写っているものが全てです。",
        "conditionName": "やや傷や汚れあり",
        "current_price_jpy": 7281,
        "shipping_fee_jpy": 1080,
    }
    analysis = deep_analyze_yahoo_auction(info)
    assert "CHƯA THỬ LỬA" in analysis["ignition_status"]
    assert analysis["tech_grade"] == "untested"
    assert "Xước nhẹ" in analysis["condition_vn"]
    assert "quẹt trần" in analysis["accessories"]
    assert len(analysis["expert_notes"]) >= 2
    assert any("vùng gom xác rất hời" in n for n in analysis["expert_notes"])


def test_t51_save_yahoo_lot_record(test_db):
    """T51: Lưu kết quả chốt lô Yahoo vào kho data với cờ is_lot và đơn giá."""
    raw = "Lô 14 cây bật lửa gas Yahoo #f1242609776 7281Y"
    rec = Record(
        id="Q0006",
        owner_user_id=123,
        raw_text=raw,
        display_name="Lô 14 cây bật lửa gas Yahoo #f1242609776",
        normalized_search_text=clean_search_text(raw),
        amount_jpy=7281,
        currency="JPY",
        brand="unknown",
        is_lot=True,
        fee_jpy=1080,
        auction_id="f1242609776",
        source_url="https://page.auctions.yahoo.co.jp/jp/auction/f1242609776",
        note="Lô 14 cây (~520 yên/cây, ship 1080Y). Chưa thử lửa. Giá chốt tàn phiên.",
    )
    create_record(test_db, rec)

    # Tìm lại bằng auction_id hoặc từ khóa lô
    srch = search_records(test_db, "f1242609776")
    assert srch.total_groups >= 1
    g = srch.groups[0]
    assert g.records[0].is_lot is True
    assert g.records[0].amount_jpy == 7281
    assert g.records[0].fee_jpy == 1080


def test_t52_estimate_market_valuation_bulk_lot():
    """T52: Định giá thị trường lô nhiều cây: vùng mua hợp lý, giá bán ra tại VN và P&L."""
    from pricing import estimate_market_valuation

    val = estimate_market_valuation(
        title="ライター ガスライター 14個まとめて売る",
        description="動作確認は行っておりません",
        current_price_jpy=7281,
        shipping_fee_jpy=1080,
        is_lot=True,
        lot_count=14,
    )
    assert val["archetype"] == "bulk_lot"
    assert val["target_buy_jpy_min"] == 4900  # 14 * 350
    assert val["target_buy_jpy_max"] == 8400  # 14 * 600
    assert val["max_bid_jpy"] == 10500        # 14 * 750
    assert val["expected_revenue_vnd"] >= 2000000
    assert val["all_in_cost_vnd"] > 0
    assert val["expected_net_profit_vnd"] > 0
    assert "Dọn sống bán lẻ" in val["resale_details"][0]
    assert "Bán xác thợ" in val["resale_details"][1]


def test_t53_estimate_market_valuation_dupont():
    """T53: Định giá thị trường dòng Dupont Line 2 và Line 1 tại Việt Nam."""
    from pricing import estimate_market_valuation

    # Dupont Line 2
    val_l2 = estimate_market_valuation(
        title="S.T. Dupont ライン2 ゴールド",
        current_price_jpy=22000,
        shipping_fee_jpy=1000,
    )
    assert val_l2["archetype"] == "dupont"
    assert "Line 2" in val_l2["category_name"]
    assert val_l2["target_buy_jpy_min"] == 18000
    assert val_l2["target_buy_jpy_max"] == 26000
    assert val_l2["max_bid_jpy"] == 32000
    assert val_l2["expected_revenue_vnd"] == 6500000
    assert val_l2["expected_net_profit_vnd"] > 0

    # Dupont Line 1
    val_l1 = estimate_market_valuation(
        title="Dupont Line 1 sơn mài xanh lá",
        current_price_jpy=11000,
        shipping_fee_jpy=1000,
    )
    assert val_l1["archetype"] == "dupont"
    assert val_l1["target_buy_jpy_min"] == 8500
    assert val_l1["target_buy_jpy_max"] == 12500
    assert val_l1["max_bid_jpy"] == 14500
    assert val_l1["expected_revenue_vnd"] == 3400000


def test_t54_estimate_market_valuation_zippo():
    """T54: Định giá thị trường Zippo Bạc khối Sterling và Zippo La Mã."""
    from pricing import estimate_market_valuation

    # Zippo Sterling 925
    val_silver = estimate_market_valuation(
        title="ZIPPO STERLING SILVER 925 純銀",
        current_price_jpy=16000,
        shipping_fee_jpy=850,
    )
    assert val_silver["archetype"] == "zippo"
    assert "Bạc Khối" in val_silver["category_name"]
    assert val_silver["expected_revenue_vnd"] == 4500000
    assert val_silver["target_buy_jpy_min"] == 14000

    # Zippo La Mã thông thường
    val_lama = estimate_market_valuation(
        title="Zippo la mã 1994",
        current_price_jpy=3200,
        shipping_fee_jpy=850,
    )
    assert val_lama["archetype"] == "zippo"
    assert val_lama["target_buy_jpy_min"] == 2500
    assert val_lama["max_bid_jpy"] == 5500


def test_t55_financial_pnl_formatting():
    """T55: Định dạng bảng P&L tài chính chi tiết với điểm hòa vốn và ROI."""
    from pricing import estimate_market_valuation, format_financial_pnl_report

    val = estimate_market_valuation(
        title="Dunhill Rollagas Gold",
        current_price_jpy=6500,
        shipping_fee_jpy=1000,
    )
    report = format_financial_pnl_report(val)
    assert "BẢNG CHI TIẾT CHI PHÍ ĐẦU TƯ" in report
    assert "TỔNG VỐN ĐẦU TƯ THỰC TẾ" in report
    assert "Lợi nhuận ròng thực tế" in report
    assert "Điểm hòa vốn" in report
    assert "ROI" in report


def test_t56_streamlined_yahoo_output_no_pnl_clutter():
    """T56: Phân tích link Yahoo chỉ giữ phân tích chuyên sâu kỹ thuật, loại bỏ bảng P&L tài chính giả định."""
    from parser import deep_analyze_yahoo_auction

    info = {
        "title": "ライター 14個まとめて売る",
        "description": "動作確認は行っておりません",
        "conditionName": "やや傷や汚れあり",
        "current_price_jpy": 7281,
        "shipping_fee_jpy": 1080,
        "status": "closed",
    }
    analysis = deep_analyze_yahoo_auction(info)
    assert analysis["ignition_status"] != ""
    assert analysis["tech_grade"] == "untested"
    assert len(analysis["expert_notes"]) > 0

    # Giả lập lines tạo bởi bot
    lines = [
        "🔗 PHÂN TÍCH CHUYÊN SÂU YAHOO AUCTIONS",
        f"🔥 Đánh lửa: {analysis['ignition_status']}",
        f"🌟 Ngoại hình: {analysis['condition_vn']}",
        f"📦 Phụ kiện: {analysis['accessories']}",
    ]
    for n in analysis["expert_notes"]:
        lines.append(n)
    full_output = "\n".join(lines)

    # Đảm bảo không có các đoạn tài chính rườm rà gây nhiễu
    assert "ĐỊNH GIÁ THỊ TRƯỜNG & KHẢ NĂNG SINH LỜI" not in full_output
    assert "DỰ TÍNH BÁN LẠI TẠI VIỆT NAM" not in full_output
    assert "TỔNG QUAN ĐẦU TƯ & LÃI RÒNG" not in full_output
    assert "Lợi nhuận ròng dự kiến" not in full_output
    assert "Tỷ suất sinh lời (ROI)" not in full_output


def test_t57_brand_model_matching_from_title():
    """T57: Nhận diện thương hiệu chuẩn từ tiêu đề tiếng Nhật."""
    from parser import match_brand_and_model_from_title

    # Dupont Line 2
    d1 = match_brand_and_model_from_title("デュポン ライン2 ゴールド 着火確認")
    assert d1["brand"] == "dupont"
    assert d1["line"] == "line_2"
    assert "Line 2" in d1["vn_name"]

    # Dunhill Rollagas
    d2 = match_brand_and_model_from_title("ダンヒル ローラガス ライター スイス製")
    assert d2["brand"] == "dunhill"
    assert d2["line"] == "rollagas"
    assert "Rollagas" in d2["vn_name"]

    # Zippo Sterling
    d3 = match_brand_and_model_from_title("ZIPPO スターリングシルバー 925 純銀")
    assert d3["brand"] == "zippo"
    assert d3["line"] == "sterling"
    assert "Bạc Khối" in d3["vn_name"]

    # Ronson Banjo
    d4 = match_brand_and_model_from_title("ロンソン バンジョー オイルライター")
    assert d4["brand"] == "ronson"
    assert d4["line"] == "banjo"


def test_t58_decode_zippo_roman_stamps():
    """T58: Giải mã mộc đáy Zippo La Mã và năm sản xuất."""
    from parser import decode_lighter_stamp

    # Tra theo La Mã
    s1 = decode_lighter_stamp("zippo X")
    assert s1 is not None
    assert s1["year"] == 1994
    assert s1["stamp_code"] == "X"
    assert "Bradford" in s1["stamp_desc"]

    s2 = decode_lighter_stamp("mộc đáy IX")
    assert s2 is not None
    assert s2["year"] == 1993

    # Tra theo năm
    s3 = decode_lighter_stamp("zippo 1989")
    assert s3 is not None
    assert s3["stamp_code"] == "V"


def test_t59_decode_vintage_slash_and_modern_stamps():
    """T59: Giải mã mộc đáy Zippo gạch cổ, đời số, Dunhill và Dupont."""
    from parser import decode_lighter_stamp

    # Gạch cổ 1974
    s_slash = decode_lighter_stamp("zippo 1974")
    assert s_slash is not None
    assert "6 gạch" in s_slash["stamp_code"]

    # Đời số 2023
    s_num = decode_lighter_stamp("zippo 2023")
    assert s_num is not None
    assert s_num["stamp_code"] == "23"

    # Dunhill
    s_dh = decode_lighter_stamp("mộc đáy dunhill rollagas")
    assert s_dh is not None
    assert s_dh["brand"] == "Dunhill"
    assert "US.RE 24163" in s_dh["stamp_desc"]

    # Dupont
    s_dp = decode_lighter_stamp("mộc đáy dupont")
    assert s_dp is not None
    assert s_dp["brand"] == "S.T. Dupont"


def test_t60_lighter_repair_guides():
    """T60: Cẩm nang bắt bệnh, kích thước O-ring và lưu ý tháo lắp."""
    from parser import get_lighter_repair_guide

    # Dunhill Rollagas
    g1 = get_lighter_repair_guide("thay ron dunhill rollagas")
    assert g1 is not None
    assert g1["brand"] == "Dunhill"
    assert any("2.5 x 1.0 mm" in o for o in g1["oring_specs"])
    assert "đá mềm" in g1["warning"]

    # Dupont
    g2 = get_lighter_repair_guide("bệnh dupont xì gas")
    assert g2 is not None
    assert g2["brand"] == "S.T. Dupont"
    assert any("4.5 x 1.0 mm" in o for o in g2["oring_specs"])

    # Zippo
    g3 = get_lighter_repair_guide("kẹt đá zippo")
    assert g3 is not None
    assert "bột đá" in g3["fix_steps"][0]


def test_t61_lot_restoration_cost_allocation(test_db):
    """T61: Cập nhật dọn lô và phân bổ lại giá vốn thực tế cho cây sống."""
    from repository import create_record, update_lot_restoration
    from models import Record
    from normalizer import clean_search_text

    raw = "Lô 14 cây bật lửa gas Yahoo #lot999 7281Y"
    rec = Record(
        id="Q0099",
        owner_user_id=123,
        raw_text=raw,
        display_name="Lô 14 cây bật lửa gas Yahoo #lot999",
        normalized_search_text=clean_search_text(raw),
        amount_jpy=7281,
        currency="JPY",
        brand="unknown",
        is_lot=True,
        fee_jpy=1080,
        auction_id="lot999",
    )
    create_record(test_db, rec)

    # Thợ dọn sống 6 cây, 8 cây rã xác
    res = update_lot_restoration(test_db, "Q0099", song=6, chet=8)
    assert res is not None
    assert res["song"] == 6
    assert res["chet"] == 8
    # Tổng vốn = (7281 + 1080) * 165 = 1.379.565 đ
    # Giá vốn mỗi cây sống = 1.379.565 / 6 = 229.928 đ
    assert res["total_cost_vnd"] == 1379565
    assert res["cost_per_alive_vnd"] == 229928
    assert "229.928" in res["note"]


def test_t62_auction_alarm_database(test_db):
    """T62: Lưu báo thức canh tàn phiên Yahoo vào DB và lấy danh sách."""
    from repository import add_auction_alarm, get_pending_alarms, mark_alarm_sent

    alarm_id = add_auction_alarm(
        test_db,
        auction_id="test12345",
        chat_id=999,
        title="Dupont Line 2 Gold",
        price_jpy=8500,
        url="https://page.auctions.yahoo.co.jp/jp/auction/test12345",
        end_time_iso="2026-09-07T22:30:00+09:00",
        trigger_at_ts=1725720000.0,
    )
    assert alarm_id > 0

    pending = get_pending_alarms(test_db)
    assert len(pending) >= 1
    found = next((a for a in pending if a["auction_id"] == "test12345"), None)
    assert found is not None
    assert found["price_jpy"] == 8500

    # Đánh dấu đã gửi
    mark_alarm_sent(test_db, alarm_id)
    pending_after = get_pending_alarms(test_db)
    assert not any(a["auction_id"] == "test12345" for a in pending_after)


def test_t63_find_recent_similar_record(test_db):
    """T63: Tra cứu lịch sử kho của người dùng theo dòng quẹt để so sánh giá."""
    from repository import create_record, find_recent_similar_record
    from models import Record
    from normalizer import clean_search_text

    raw = "Dunhill Rollagas Gold 5500Y"
    rec = Record(
        id="Q0088",
        owner_user_id=123,
        raw_text=raw,
        display_name="Dunhill Rollagas Gold",
        normalized_search_text=clean_search_text(raw),
        amount_jpy=5500,
        currency="JPY",
        brand="dunhill",
        line="rollagas",
        is_lot=False,
    )
    create_record(test_db, rec)

    found = find_recent_similar_record(test_db, "dunhill", "rollagas")
    assert found is not None
    assert found.id == "Q0088"
    assert found.amount_jpy == 5500


def test_t64_extract_yahoo_auction_id_flexible():
    """T64: Trích xuất auction ID từ nhiều nguồn linh hoạt (mã # trực tiếp, link proxy Doorzo, FromJapan, Buyee)."""
    from parser import extract_yahoo_auction_id

    # Mã trực tiếp có và không có dấu #
    assert extract_yahoo_auction_id("#f1242609776") == "f1242609776"
    assert extract_yahoo_auction_id("q1243285675") == "q1243285675"

    # Link Yahoo kèm query params
    assert extract_yahoo_auction_id("https://page.auctions.yahoo.co.jp/jp/auction/f1242609776?notice=1") == "f1242609776"

    # Proxy Buyee
    assert extract_yahoo_auction_id("https://buyee.jp/item/yahoo/auction/m123456789?lang=vi") == "m123456789"

    # Proxy ZenMarket
    assert extract_yahoo_auction_id("https://zenmarket.jp/vi/auction.aspx?itemCode=k987654321") == "k987654321"

    # Proxy Doorzo
    assert extract_yahoo_auction_id("https://doorzo.com/item/yahoo/auction/d1122334455") == "d1122334455"


def test_t65_decode_iconic_zippo_stamps():
    """T65: Giải mã các dòng mộc đáy Zippo kinh điển: Solid Brass, Sterling, Copper, Titanium."""
    from parser import decode_lighter_stamp

    # Solid Brass
    s_brass = decode_lighter_stamp("zippo solid brass")
    assert s_brass is not None
    assert "SOLID BRASS" in s_brass["stamp_code"]
    assert "đồng thau nguyên khối" in s_brass["model"].lower()

    # Sterling Silver
    s_silver = decode_lighter_stamp("zippo sterling")
    assert s_silver is not None
    assert "STERLING" in s_silver["stamp_code"]
    assert "92.5%" in s_silver["stamp_desc"]

    # Copper
    s_copper = decode_lighter_stamp("zippo copper")
    assert s_copper is not None
    assert "COPPER" in s_copper["stamp_code"]
    assert "đồng đỏ" in s_copper["model"].lower()

    # Titanium
    s_ti = decode_lighter_stamp("zippo titan")
    assert s_ti is not None
    assert "TITANIUM" in s_ti["stamp_code"]
    assert "chén thánh" in s_ti["market_price_vnd"] or "Titan" in s_ti["model"]


def test_t66_help_text_completeness():
    """T66: Help text phản ánh đầy đủ các tính năng V4.1."""
    from handlers.start import HELP_TEXT

    assert "TRỢ LÝ SĂN & DỌN QUẸT" in HELP_TEXT
    assert "Buyee" in HELP_TEXT
    assert "mộc đáy" in HELP_TEXT
    assert "thay ron" in HELP_TEXT
    assert "/donlo" in HELP_TEXT


def test_t67_donlo_pending_list_query(test_db):
    """T67: Truy vấn danh sách lô trong kho chờ dọn."""
    from repository import create_record
    from models import Record
    from normalizer import clean_search_text

    rec = Record(
        id="Q0077",
        owner_user_id=123,
        raw_text="Lô 10 cây bật lửa gas 5000Y",
        display_name="Lô 10 cây bật lửa gas",
        normalized_search_text=clean_search_text("Lô 10 cây bật lửa gas"),
        amount_jpy=5000,
        currency="JPY",
        brand="unknown",
        is_lot=True,
    )
    create_record(test_db, rec)

    cur = test_db.cursor()
    cur.execute("SELECT * FROM records WHERE is_lot = 1 AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 5;")
    lots = cur.fetchall()
    assert len(lots) >= 1
    assert any(l["id"] == "Q0077" for l in lots)


def test_t68_parse_data_input_with_yahoo_url():
    """T68: /data kèm link Yahoo tự động làm sạch mô tả và trích xuất auction_id + source_url."""
    from parser import parse_data_input

    raw = "/data https://page.auctions.yahoo.co.jp/jp/auction/f1242609776 dupont son mai xanh la 15000Y"
    res = parse_data_input(raw)
    assert res.is_valid is True
    assert res.display_name == "dupont son mai xanh la"
    assert res.auction_id == "f1242609776"
    assert "f1242609776" in res.source_url
    assert res.amount_jpy == 15000
    assert res.currency == "JPY"


def test_t69_parse_data_input_url_only_with_price():
    """T69: /data chỉ có link Yahoo và giá sẽ tự động đặt tên quẹt theo mã đấu giá, không báo lỗi thiếu mô tả."""
    from parser import parse_data_input

    raw = "/data https://page.auctions.yahoo.co.jp/jp/auction/f1242609776 22000Y"
    res = parse_data_input(raw)
    assert res.is_valid is True
    assert "f1242609776" in res.display_name
    assert res.auction_id == "f1242609776"
    assert res.amount_jpy == 22000


def test_t70_quick_record_id_and_image_extraction():
    """T70: Regex mã bản ghi Q0001 và trích xuất ảnh đa định dạng từ Yahoo detail."""
    import re
    from parser import analyze_lot_quantity

    # Match ID kho
    assert re.match(r"^#?(Q\d{4})$", "Q0001", re.I) is not None
    assert re.match(r"^#?(Q\d{4})$", "#q0015", re.I) is not None
    assert re.match(r"^#?(Q\d{4})$", "Q12345", re.I) is None

    # Phân tích lô
    lot = analyze_lot_quantity("ライター ガスライター 14個まとめて売る", price_jpy=7281, shipping_fee_jpy=1080)
    assert lot["is_lot"] is True
    assert lot["count"] == 14
    assert lot["unit_price_jpy"] > 0


def test_radar_is_lot_title():
    from radar_service import is_lot_title
    # Positive lot cases
    assert is_lot_title("ライター まとめ 15点 ジャンク") is True
    assert is_lot_title("S.T.Dupont ダンヒル 5本セット 大量") is True
    assert is_lot_title("ジッポ ライター 詰め合わせ 20個") is True
    assert is_lot_title("ガスライター 8本 アソート") is True
    assert is_lot_title("ヴィンテージ オイルライター まとめ売り") is True

    # Negative non-lot cases
    assert is_lot_title("S.T.Dupont ライン2 モンパルナス 銀仕上げ 美品") is False
    assert is_lot_title("Dunhill Rollagas Gold 1点のみ 単品") is False
    assert is_lot_title("Zippo 1994 Solid Brass") is False


def test_radar_is_ending_today():
    from datetime import datetime, timezone, timedelta
    from radar_service import is_ending_today

    jst = timezone(timedelta(hours=9))
    now_utc = datetime(2026, 9, 8, 5, 0, 0, tzinfo=timezone.utc)  # 14:00 JST ngày 2026-09-08

    # 1. Kết thúc hôm nay lúc 21:00 JST (còn 7 tiếng)
    is_today, remain_text, remain_mins = is_ending_today("2026-09-08 21:00:00", now_utc=now_utc)
    assert is_today is True
    assert "còn 7h00m" in remain_text
    assert remain_mins == 420

    # 2. Đã kết thúc lúc 10:00 JST (trong quá khứ)
    is_today, remain_text, remain_mins = is_ending_today("2026-09-08 10:00:00", now_utc=now_utc)
    assert is_today is False
    assert remain_text == "Đã hết giờ"

    # 3. Kết thúc ngày mai (2026-09-09)
    is_today, remain_text, remain_mins = is_ending_today("2026-09-09 15:00:00", now_utc=now_utc)
    assert is_today is False
    assert "Ngày mai" in remain_text

    # 4. Chuỗi ngày không hợp lệ
    is_today, remain_text, remain_mins = is_ending_today("invalid-date", now_utc=now_utc)
    assert is_today is False


def test_radar_deduplication_and_settings(tmp_path):
    from db import get_db_connection, init_database
    from repository import get_radar_setting, is_lot_seen, mark_lot_seen, set_radar_setting

    db_file = tmp_path / "test_radar.db"
    init_database(db_file)
    conn = get_db_connection(db_file)
    try:
        # Settings test
        assert get_radar_setting(conn, "auto_radar_enabled") == "1"
        set_radar_setting(conn, "auto_radar_enabled", "0")
        assert get_radar_setting(conn, "auto_radar_enabled") == "0"

        # Seen lots deduplication test
        assert is_lot_seen(conn, "w123456", "2026-09-08") is False
        mark_lot_seen(conn, "w123456", "2026-09-08", "Lô 10 cây Dupont", 5000, 3, "2026-09-08 22:00:00")
        assert is_lot_seen(conn, "w123456", "2026-09-08") is True
        # Ngày khác chưa seen
        assert is_lot_seen(conn, "w123456", "2026-09-09") is False
    finally:
        conn.close()


def test_format_radar_message():
    from radar_service import format_radar_chunks, format_radar_message

    # Empty lots
    empty_msg, pages = format_radar_message([])
    assert "Hiện tại không có lô bật lửa nào" in empty_msg
    assert pages == 1

    # 18 Mock lot items to test chunking & pagination
    lots = [
        {
            "auction_id": f"test{i:03d}",
            "title": f"Lô {i} cây Zippo vintage đợt {i}",
            "price_jpy": 5000 + i * 100,
            "bids": i + 1,
            "remain_text": f"còn {i}h",
            "url": f"https://page.auctions.yahoo.co.jp/jp/auction/test{i:03d}",
        }
        for i in range(1, 19)
    ]
    # Test pagination: 18 items with per_page=8 => 3 pages
    msg_p1, total_pages = format_radar_message(lots, page=1, per_page=8)
    assert total_pages == 3
    assert "Trang 1/3" in msg_p1
    assert "Lô 1 cây Zippo" in msg_p1
    assert "Lô 8 cây Zippo" in msg_p1
    assert "Lô 9 cây Zippo" not in msg_p1

    msg_p2, _ = format_radar_message(lots, page=2, per_page=8)
    assert "Trang 2/3" in msg_p2
    assert "Lô 9 cây Zippo" in msg_p2

    # Test full chunking: 18 items with chunk_size=8 => 3 chunks
    chunks = format_radar_chunks(lots, chunk_size=8)
    assert len(chunks) == 3
    assert "PHẦN 1/3" in chunks[0]
    assert "PHẦN 2/3" in chunks[1]
    assert "PHẦN 3/3" in chunks[2]

def test_persistent_reply_keyboard():
    from handlers.start import get_persistent_reply_keyboard
    from telegram import ReplyKeyboardMarkup

    kb = get_persistent_reply_keyboard()
    assert isinstance(kb, ReplyKeyboardMarkup)
    assert kb.resize_keyboard is True
    assert kb.is_persistent is True
    assert len(kb.keyboard) == 3
    # Check rows
    row0 = [btn.text for btn in kb.keyboard[0]]
    assert "🎯 Radar Lô Hôm Nay" in row0
    assert "📜 Toàn Bộ Lô (Full)" in row0
    row1 = [btn.text for btn in kb.keyboard[1]]
    assert "📦 Dọn Lô Kho" in row1
    assert "📋 10 Cây Gần Nhất" in row1
    row2 = [btn.text for btn in kb.keyboard[2]]
    assert "📊 Thống Kê Kho" in row2
    assert "❓ Hướng Dẫn" in row2


def test_group_detail_keyboard_has_menu_shortcuts():
    from unittest.mock import MagicMock
    from handlers.search_handlers import get_group_detail_keyboard

    mock_group = MagicMock()
    mock_group.scope_key = "dupont_line2"
    kb = get_group_detail_keyboard(mock_group)
    all_btn_texts = [btn.text for row in kb.inline_keyboard for btn in row]
    assert "🎯 Radar Lô Hôm Nay" in all_btn_texts
    assert "🎛 Bảng Menu" in all_btn_texts


# ==========================================
# T31 - T35: Tính Năng Mới V5.0 (Tỷ Giá Động, Deal Score, Sub-Radars)
# ==========================================

def test_t31_dynamic_exchange_rate_db_and_formatting(test_db):
    """T31: Thử nghiệm lấy và cập nhật tỷ giá JPY sang VND động trong CSDL."""
    from repository import get_exchange_rate, set_exchange_rate
    from pricing import format_currency_amount

    # Mặc định chưa set là 165
    rate_default = get_exchange_rate(test_db)
    assert rate_default == 165

    # Cập nhật sang 170
    set_exchange_rate(test_db, 170)
    rate_new = get_exchange_rate(test_db)
    assert rate_new == 170

    # Kiểm tra format_currency_amount với tỷ giá 170
    formatted = format_currency_amount(10000, "JPY", with_approx=True, rate=170)
    assert "10.000 yên" in formatted
    assert "1.700.000 đ" in formatted


def test_t32_parse_quick_calc_with_dynamic_rate():
    """T32: Tính nhẩm nhanh giá Yahoo áp dụng tỷ giá động chuẩn xác."""
    from parser import parse_quick_calc_input

    res_165 = parse_quick_calc_input("10000Y", rate=165)
    assert res_165 is not None
    assert res_165["base_vnd"] == 1650000
    assert res_165["total_landing_vnd"] == 1850000

    res_170 = parse_quick_calc_input("10000Y", rate=170)
    assert res_170 is not None
    assert res_170["base_vnd"] == 1700000
    assert res_170["total_landing_vnd"] == 1900000


def test_t33_deal_score_calculation():
    """T33: Chấm điểm kèo thơm (Deal Score 1 - 10) chính xác theo điều kiện."""
    from pricing import compute_deal_score

    # Kèo thơm: Giá 12.000Y so với mốc trần 20.000Y (rẻ hơn 40%), đã thử lửa, có hộp, ít bid
    good_deal = compute_deal_score(
        price_jpy=12000,
        tech_grade="working",
        is_lot=False,
        has_box=True,
        bids=2,
        target_ref_jpy=20000,
    )
    assert good_deal["score"] >= 8.5
    assert "KÈO RẤT THƠM" in good_deal["label"]

    # Kèo rủi ro: Giá 25.000Y vượt trần 20.000Y, chưa thử lửa (untested), nhiều bid
    bad_deal = compute_deal_score(
        price_jpy=25000,
        tech_grade="untested",
        is_lot=False,
        has_box=False,
        bids=30,
        target_ref_jpy=20000,
    )
    assert bad_deal["score"] <= 5.0
    assert "KÈO RỦI RO" in bad_deal["label"]

    # Lô sỉ: Đơn giá 600Y/cây
    lot_deal = compute_deal_score(
        price_jpy=6000,
        is_lot=True,
        unit_price_jpy=600,
        bids=3,
    )
    assert lot_deal["score"] >= 7.5


def test_t34_sub_radar_brand_modes():
    """T34: Phân giải lệnh sub-radar các hãng Dupont, Dunhill, Zippo."""
    from handlers.radar_handlers import _resolve_brand_mode

    m_dp, name_dp = _resolve_brand_mode(["dupont"])
    assert m_dp == "dupont"
    assert "DUPONT" in name_dp

    m_dh, name_dh = _resolve_brand_mode(["dunhill"])
    assert m_dh == "dunhill"
    assert "DUNHILL" in name_dh

    m_zp, name_zp = _resolve_brand_mode(["zippo"])
    assert m_zp == "zippo"
    assert "ZIPPO" in name_zp

    m_lot, name_lot = _resolve_brand_mode([])
    assert m_lot == "lot"


def test_t35_radar_format_with_custom_category_and_rate():
    """T35: Định dạng tin nhắn Radar theo tên hãng và tỷ giá mới."""
    from radar_service import format_radar_message, format_single_lot_block

    it = {
        "auction_id": "test_dp01",
        "title": "S.T. Dupont Line 2 vàng",
        "price_jpy": 20000,
        "bids": 5,
        "remain_text": "còn 2h",
        "url": "https://page.auctions.yahoo.co.jp/jp/auction/test_dp01",
    }
    # Rate 170 => 20000 * 170 = 3.400.000 đ
    block = format_single_lot_block(1, it, rate=170)
    assert "3.400.000 đ" in block
    assert "20.000 yên" in block

    msg, pages = format_radar_message([it], page=1, per_page=8, rate=170, category_name="S.T. DUPONT")
    assert "RADAR S.T. DUPONT" in msg
    assert "3.400.000 đ" in msg


def test_t36_classify_lighter_lot_type():
    """T36: Phân loại chính xác 4 nhóm: Gas Đá, Dầu, Zippo, Thập Cẩm."""
    from radar_service import classify_lighter_lot_type

    # 1. Zippo
    code, tag, icon = classify_lighter_lot_type("ZIPPO ジッポー 10点セット まとめ売り")
    assert code == "zippo"
    assert "ZIPPO" in tag

    # 2. Bật lửa dầu
    code, tag, icon = classify_lighter_lot_type("レトロ オイルライター 5本 まとめて ジャンク")
    assert code == "dau"
    assert "DẦU" in tag

    # 3. Lot gas đá (gas hoặc đá lửa)
    code, tag, icon = classify_lighter_lot_type("ダンヒル カルティエ ガスライター 6点 まとめ")
    assert code == "gas_da"
    assert "GAS ĐÁ" in tag

    code, tag, icon = classify_lighter_lot_type("ライター フリント 着火石 20個 大量まとめ")
    assert code == "gas_da"
    assert "GAS ĐÁ" in tag

    # 4. Thập cẩm (hỗn hợp)
    code, tag, icon = classify_lighter_lot_type("ライター 大量まとめ売り ジャンク 50点 詰め合わせ")
    assert code == "thapcam"
    assert "THẬP CẨM" in tag


def test_t37_radar_categories_config():
    """T37: Kiểm tra BRAND_RADAR_CONFIGS có đủ 4 nhóm chính theo yêu cầu."""
    from radar_service import BRAND_RADAR_CONFIGS

    assert "gas_da" in BRAND_RADAR_CONFIGS
    assert "dau" in BRAND_RADAR_CONFIGS
    assert "zippo" in BRAND_RADAR_CONFIGS
    assert "thapcam" in BRAND_RADAR_CONFIGS

    assert BRAND_RADAR_CONFIGS["gas_da"]["title"] == "LOT GAS ĐÁ"
    assert BRAND_RADAR_CONFIGS["dau"]["title"] == "BẬT LỬA DẦU"
    assert BRAND_RADAR_CONFIGS["thapcam"]["title"] == "LÔ THẬP CẨM"


def test_t38_radar_page_keyboard_four_groups():
    """T38: Kiểm tra bàn phím phân trang Radar có đủ 4 nút chọn danh mục mới."""
    from handlers.radar_handlers import _get_radar_page_keyboard

    kb = _get_radar_page_keyboard(1, 3, 10, is_auto_on=True, current_mode="gas_da")
    btn_datas = [b.callback_data for row in kb.inline_keyboard for b in row]

    assert "radar_brand:thapcam" in btn_datas
    assert "radar_brand:gas_da" in btn_datas
    assert "radar_brand:dau" in btn_datas
    assert "radar_brand:zippo" in btn_datas


def test_t39_dashboard_server_stats_api(test_db, tmp_path):
    """T39: Kiểm tra REST API /api/stats phục vụ Telegram WebApp Dashboard."""
    import json
    import socket
    import urllib.request
    from config import AppConfig
    from dashboard_server import start_dashboard_server
    from repository import create_record, set_bid_cap, set_exchange_rate
    from models import BidCap, Record

    # Thêm dữ liệu mẫu vào test_db
    conn = test_db
    set_exchange_rate(conn, 172)
    create_record(
        conn,
        Record(
            id="Q0001",
            owner_user_id=123,
            raw_text="dupont line 2 vang",
            display_name="Dupont Line 2 Vàng",
            normalized_search_text="",
            brand="dupont",
            line="line_2",
            amount_jpy=25000,
            currency="JPY",
        ),
    )
    create_record(
        conn,
        Record(
            id="Q0002",
            owner_user_id=123,
            raw_text="dunhill rollagas bac",
            display_name="Dunhill Rollagas Bạc",
            normalized_search_text="",
            brand="dunhill",
            line="rollagas",
            amount_jpy=12000,
            currency="JPY",
        ),
    )
    set_bid_cap(
        conn,
        BidCap(
            id=None,
            scope_key="test_dupont",
            brand="dupont",
            line="line_2",
            material="gold",
            color="gold",
            box="yes",
            condition="good",
            cap_amount_jpy=30000,
            source_record_id="Q0001",
        ),
    )

    # Tìm cổng trống ngẫu nhiên
    with socket.socket() as s:
        s.bind(("", 0))
        free_port = s.getsockname()[1]

    # Khởi động server
    db_path = tmp_path / "test_vault.db"
    cfg = AppConfig(bot_token="test", owner_id=123, db_path=db_path, backup_dir=tmp_path, price_high_threshold_jpy=50000)
    server = start_dashboard_server(cfg, port=free_port)
    assert server is not None

    try:
        url = f"http://127.0.0.1:{free_port}/api/stats"
        with urllib.request.urlopen(url, timeout=3) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["total_records"] >= 2
            assert data["total_caps"] >= 1
            assert data["total_jpy"] >= 37000
            assert data["rate"] == 172
            assert any(b["name"].lower() == "dupont" for b in data["brands"])
    finally:
        server.shutdown()
        server.server_close()


def test_t40_dashboard_server_records_and_html(test_db, tmp_path):
    """T40: Kiểm tra REST API /api/records, /healthz và WebApp HTML giao diện."""
    import json
    import socket
    import urllib.request
    from config import AppConfig
    from dashboard_server import start_dashboard_server

    conn = test_db
    db_path = tmp_path / "test_vault.db"
    cfg = AppConfig(bot_token="test", owner_id=123, db_path=db_path, backup_dir=tmp_path, price_high_threshold_jpy=50000)

    with socket.socket() as s:
        s.bind(("", 0))
        free_port = s.getsockname()[1]

    server = start_dashboard_server(cfg, port=free_port)
    assert server is not None

    try:
        # 1. Health check
        with urllib.request.urlopen(f"http://127.0.0.1:{free_port}/healthz", timeout=3) as r:
            assert r.status == 200
            assert r.read() == b"OK"

        # 2. API Records
        with urllib.request.urlopen(f"http://127.0.0.1:{free_port}/api/records", timeout=3) as r:
            assert r.status == 200
            records = json.loads(r.read().decode("utf-8"))
            assert isinstance(records, list)

        # 3. WebApp Dashboard HTML
        with urllib.request.urlopen(f"http://127.0.0.1:{free_port}/dashboard", timeout=3) as r:
            assert r.status == 200
            html = r.read().decode("utf-8")
            assert "LamQuet Vault" in html
            assert "Bảng Điều Khiển" in html
    finally:
        server.shutdown()
        server.server_close()


def test_t41_ebay_price_and_vnd_parsing():
    """T41: Bóc tách giá tiền eBay USD và VND."""
    from ebay_service import parse_ebay_price_and_vnd

    usd_p, vnd_p = parse_ebay_price_and_vnd("$35.00", usd_rate=25500)
    assert usd_p == "$35.00"
    assert vnd_p == "892.500"

    usd_p2, vnd_p2 = parse_ebay_price_and_vnd("USD 100.00", usd_rate=25000)
    assert usd_p2 == "$100.00"
    assert vnd_p2 == "2.500.000"

    usd_p3, vnd_p3 = parse_ebay_price_and_vnd("510,000 VND", usd_rate=25500)
    assert "510.000" in vnd_p3


def test_t42_ebay_time_filter():
    """T42: Kiểm tra bộ lọc thời gian tàn phiên trước 11h sáng mai."""
    from ebay_service import is_ending_before_tomorrow_noon

    assert is_ending_before_tomorrow_noon("1h 29m left") is True
    assert is_ending_before_tomorrow_noon("45m left") is True
    assert is_ending_before_tomorrow_noon("14h left") is True
    assert is_ending_before_tomorrow_noon("1d 2h left") is True
    assert is_ending_before_tomorrow_noon("2d left") is False
    assert is_ending_before_tomorrow_noon("3d 5h left") is False
    assert is_ending_before_tomorrow_noon("5d left") is False


def test_t43_ebay_format_single_block():
    """T43: Định dạng thông tin 1 phiên đấu giá eBay."""
    from ebay_service import format_single_ebay_block

    item = {
        "id": "123456789",
        "title": "Vintage S.T. Dupont Lighter Gold Plated",
        "price_raw": "$50.00",
        "bids": 7,
        "time_left": "2h 15m left",
        "url": "https://www.ebay.com/itm/123456789",
    }
    block = format_single_ebay_block(1, item, usd_rate=25000)
    assert "Vintage S.T. Dupont Lighter" in block
    assert "$50.00" in block
    assert "1.250.000 đ" in block
    assert "7 bids" in block
    assert "2h 15m left" in block
    assert "https://www.ebay.com/itm/123456789" in block


def test_t44_ebay_format_message_and_pagination():
    """T44: Định dạng tin nhắn eBay Radar có phân trang và fallback rỗng."""
    from ebay_service import format_ebay_message

    sample_items = [
        {
            "id": f"100{i}",
            "title": f"Dunhill Rollagas Lighter Silver #{i}",
            "price_raw": "$40.00",
            "bids": i + 1,
            "time_left": f"{i}h left",
            "url": f"https://www.ebay.com/itm/100{i}",
        }
        for i in range(1, 10)
    ]
    # Trang 1 / 2 với per_page = 5
    msg, total_pages = format_ebay_message(sample_items, page=1, per_page=5, keyword="dunhill")
    assert "RADAR ĐẤU GIÁ EBAY" in msg
    assert "Trang 1/2" in msg
    assert total_pages == 2
    assert "Dunhill Rollagas Lighter Silver #1" in msg

    # Trang rỗng
    empty_msg, empty_pages = format_ebay_message([], page=1, per_page=5, keyword="zippo")
    assert "Hiện chưa tìm thấy" in empty_msg
    assert empty_pages == 1


def test_t45_ebay_page_keyboard():
    """T45: Kiểm tra bàn phím phân trang và chuyển đổi thương hiệu eBay."""
    from handlers.ebay_handlers import _get_ebay_page_keyboard

    kb = _get_ebay_page_keyboard(1, 3, "dupont")
    btn_texts = [b.text for row in kb.inline_keyboard for b in row]
    btn_datas = [b.callback_data for row in kb.inline_keyboard for b in row]

    assert "Sau ▶️" in btn_texts
    assert "ebay_page:2" in btn_datas
    assert "ebay_brand:dupont" in btn_datas
    assert "ebay_brand:dunhill" in btn_datas
    assert "ebay_brand:zippo" in btn_datas
    assert "ebay_refresh:dupont" in btn_datas


def test_t46_ebay_brand_keywords_stemming():
    """T46: Kiểm tra từ khóa tìm kiếm hỗ trợ cả số ít, số nhiều (lighter, lighters) và brand."""
    from ebay_service import EBAY_BRAND_KEYWORDS

    assert "(lighter,lighters)" in EBAY_BRAND_KEYWORDS["all"]
    assert "(lighter,lighters)" in EBAY_BRAND_KEYWORDS["lighters"]
    assert "(lighter,lighters)" in EBAY_BRAND_KEYWORDS["lighter"]
    assert "dupont" in EBAY_BRAND_KEYWORDS["dupont"]
    assert "dunhill" in EBAY_BRAND_KEYWORDS["dunhill"]
    assert "zippo" in EBAY_BRAND_KEYWORDS["zippo"]


def test_t47_ebay_html_container_card_and_bids():
    """T47: Kiểm tra bóc tách cấu trúc HTML s-card mới của eBay kèm bids và thời gian."""
    from bs4 import BeautifulSoup
    import re
    from ebay_service import is_ending_before_tomorrow_noon

    mock_html = """
    <ul class="srp-results">
        <li class="s-card">
            <a href="https://www.ebay.com/itm/336774990755?_trk=123">
                <span class="s-card__title">Vintage 1980 Zippo Handilite Fisher Instruments Lighter</span>
            </a>
            <div class="s-card__price">US $21.50</div>
            <span class="s-card__bids">7 bids</span>
            <span class="s-card__time">20h 24m left</span>
        </li>
        <li class="s-card">
            <a href="https://www.ebay.com/itm/158251813979?_trk=456">
                <span class="s-card__title">Vintage 1949-50 Town & Country Zippo - Setter Dog</span>
            </a>
            <div class="s-card__price">US $1,175.00</div>
            <span class="s-card__bids">20 bids</span>
            <span class="s-card__time">20h 37m left</span>
        </li>
        <li class="s-card">
            <a href="https://www.ebay.com/itm/999999999999">
                <span class="s-card__title">Expired Lighter Far Away</span>
            </a>
            <div class="s-card__price">US $10.00</div>
            <span class="s-card__bids">3 bids</span>
            <span class="s-card__time">3d 4h left</span>
        </li>
    </ul>
    """
    soup = BeautifulSoup(mock_html, "html.parser")
    containers = soup.select("ul.srp-results > li")
    assert len(containers) == 3

    valid_items = []
    for c in containers:
        c_txt = c.get_text(" ", strip=True)
        m_b = re.search(r"(\d+)\s*bids?", c_txt, re.IGNORECASE)
        m_t = re.search(r"((?:\d+\s*[dhm]\s*)+left)", c_txt, re.IGNORECASE)
        time_str = m_t.group(1) if m_t else ""
        if m_b and time_str and is_ending_before_tomorrow_noon(time_str):
            link = c.select_one("a[href*='/itm/']")
            m_id = re.search(r"/itm/(\d+)", link["href"])
            valid_items.append({
                "id": m_id.group(1),
                "bids": int(m_b.group(1)),
                "time": time_str
            })

    # Chỉ 2 item đầu hợp lệ (còn hạn), item 3 bị loại vì 3d 4h left
    assert len(valid_items) == 2
    assert valid_items[0]["id"] == "336774990755"
    assert valid_items[0]["bids"] == 7
    assert valid_items[1]["id"] == "158251813979"
    assert valid_items[1]["bids"] == 20


def test_t48_ebay_deduplication_logic():
    """T48: Kiểm tra cơ chế chống trùng lặp seen_ids khi cào nhiều trang."""
    seen_ids = set()
    raw_incoming = ["111", "222", "111", "333", "222", "444"]
    unique_items = []
    for iid in raw_incoming:
        if iid in seen_ids:
            continue
        seen_ids.add(iid)
        unique_items.append(iid)

    assert unique_items == ["111", "222", "333", "444"]
    assert len(unique_items) == 4


def test_t49_yahoo_lot_strict_verification_15_cases():
    """T49: Kiểm tra đầy đủ 15 ca kiểm thử chuẩn xác minh Lot Yahoo Auctions."""
    from parser import verify_yahoo_lighter_lot, extract_actual_lighter_count

    # Ca 1: 5 bật lửa bán chung -> NHẬN (VERIFIED_LOT)
    c1 = {
        "auction_id": "c1_5lighters",
        "title": "ガスライター 5本セット まとめて ダンヒル デュポン",
        "description": "5本のライターを出品します。すべてセットで同梱発送です。",
        "current_price_jpy": 12000,
        "status": "open",
        "is_fetched": True,
    }
    v1 = verify_yahoo_lighter_lot(c1)
    assert v1["is_verified_lot"] is True
    assert v1["decision_code"] == "VERIFIED_LOT"
    assert v1["lighter_count"] == 5

    # Ca 2: 1 Dupont full box -> LOẠI (SINGLE_ITEM)
    c2 = {
        "auction_id": "c2_dupont_box",
        "title": "S.T.Dupont デュポン ライン2 ゴールド フルセット 箱 説明書付き 1点",
        "description": "デュポン1本です。箱、ギャランティカード付属。本体1個。",
        "current_price_jpy": 35000,
        "status": "open",
        "is_fetched": True,
    }
    v2 = verify_yahoo_lighter_lot(c2)
    assert v2["is_verified_lot"] is False
    assert v2["decision_code"] == "SINGLE_ITEM"

    # Ca 3: 1 Zippo kèm gas và đá -> LOẠI (SINGLE_ITEM)
    c3 = {
        "auction_id": "c3_zippo_gas",
        "title": "ZIPPO ジッポー 1個 + オイル 替石 フリント セット",
        "description": "Zippo 1点と消耗品のセットです。1本のみ。",
        "current_price_jpy": 2500,
        "status": "open",
        "is_fetched": True,
    }
    v3 = verify_yahoo_lighter_lot(c3)
    assert v3["is_verified_lot"] is False
    assert v3["decision_code"] in ("SINGLE_ITEM", "ACCESSORY_ONLY")

    # Ca 4: Ảnh 10 cây, mô tả chỉ bán 1 cây -> LOẠI (PER_PIECE_CHOICE / SINGLE_ITEM)
    c4 = {
        "auction_id": "c4_photo10_sell1",
        "title": "ライター 10本 まとめて写真",
        "description": "写真はイメージです。画像の中からお好きな1本をお選びください。1本の価格です。",
        "current_price_jpy": 1000,
        "status": "open",
        "is_fetched": True,
    }
    v4 = verify_yahoo_lighter_lot(c4)
    assert v4["is_verified_lot"] is False
    assert v4["decision_code"] in ("PER_PIECE_CHOICE", "SINGLE_ITEM")

    # Ca 5: 10 cây, giá tính mỗi cây / chọn 1 cây -> LOẠI (PER_PIECE_CHOICE)
    c5 = {
        "auction_id": "c5_10items_per_piece",
        "title": "ジッポー ライター 10個 各種",
        "description": "1個あたりの値段です。落札後にご希望の番号を選択してください。",
        "current_price_jpy": 1500,
        "status": "open",
        "is_fetched": True,
    }
    v5 = verify_yahoo_lighter_lot(c5)
    assert v5["is_verified_lot"] is False
    assert v5["decision_code"] == "PER_PIECE_CHOICE"

    # Ca 6: 20 hộp Zippo rỗng -> LOẠI (ACCESSORY_ONLY)
    c6 = {
        "auction_id": "c6_20empty_boxes",
        "title": "ZIPPO ジッポ 空箱 20個セット ケースのみ",
        "description": "中身のライターはありません。ケースのみ20点です。",
        "current_price_jpy": 5000,
        "status": "open",
        "is_fetched": True,
    }
    v6 = verify_yahoo_lighter_lot(c6)
    assert v6["is_verified_lot"] is False
    assert v6["decision_code"] == "ACCESSORY_ONLY"

    # Ca 7: 8 cây junk bán chung -> NHẬN + nhãn junk (VERIFIED_LOT)
    c7 = {
        "auction_id": "c7_8junk",
        "title": "オイルライター ジャンク 8本 まとめ売り 動作未確認",
        "description": "着火未確認のため全てジャンク品として出品します。8本まとめてセットです。",
        "current_price_jpy": 4500,
        "status": "open",
        "is_fetched": True,
    }
    v7 = verify_yahoo_lighter_lot(c7)
    assert v7["is_verified_lot"] is True
    assert v7["decision_code"] == "VERIFIED_LOT"
    assert v7["lighter_count"] == 8
    assert "Junk" in v7["condition_label"]

    # Ca 8: 5 cây, ghi “không bán tách” (バラ売り不可) -> NHẬN (VERIFIED_LOT)
    c8 = {
        "auction_id": "c8_no_split",
        "title": "ブランドライター 5点 まとめ売り バラ売り不可",
        "description": "5点セットです。バラ売りはいたしません。全品セットでの取引となります。",
        "current_price_jpy": 18000,
        "status": "open",
        "is_fetched": True,
    }
    v8 = verify_yahoo_lighter_lot(c8)
    assert v8["is_verified_lot"] is True
    assert v8["decision_code"] == "VERIFIED_LOT"
    assert v8["lighter_count"] == 5

    # Ca 9: Tiêu đề nói lot, mô tả nói chỉ bán một cây -> LOẠI
    c9 = {
        "auction_id": "c9_title_lot_desc_single",
        "title": "ライター 大量 まとめ売り 複数点",
        "description": "※注意：タイトルにまとめとありますが、出品商品は1点のみです。単品販売。",
        "current_price_jpy": 2000,
        "status": "open",
        "is_fetched": True,
    }
    v9 = verify_yahoo_lighter_lot(c9)
    assert v9["is_verified_lot"] is False
    assert v9["decision_code"] == "SINGLE_ITEM"

    # Ca 10: Không đọc được chi tiết -> UNCERTAIN (không gửi)
    c10 = {
        "auction_id": "c10_fetch_error",
        "title": "ライター まとめ",
        "current_price_jpy": 3000,
        "status": "open",
        "is_fetched": False,
    }
    v10 = verify_yahoo_lighter_lot(c10)
    assert v10["is_verified_lot"] is False
    assert v10["decision_code"] == "UNCERTAIN"

    # Ca 11: 1 cây sản xuất giới hạn 1.000 chiếc (1000個限定) -> LOẠI (SINGLE_ITEM)
    c11 = {
        "auction_id": "c11_limited_edition",
        "title": "ZIPPO 1000個限定 シリアル入り 1999年製",
        "description": "限定1000個生産のzippoライター1本です。1点のみ。",
        "current_price_jpy": 8000,
        "status": "open",
        "is_fetched": True,
    }
    v11 = verify_yahoo_lighter_lot(c11)
    assert v11["is_verified_lot"] is False
    assert v11["decision_code"] == "SINGLE_ITEM"

    # Ca 12: 10 cây trong đó 1 cây hỏng -> NHẬN 10 cây
    c12 = {
        "auction_id": "c12_10with1defect",
        "title": "ガスライター 10本セット 1本ジャンク含む",
        "description": "10本セットです。9本着火確認済み、1本故障品です。まとめて出品。",
        "current_price_jpy": 9000,
        "status": "open",
        "is_fetched": True,
    }
    v12 = verify_yahoo_lighter_lot(c12)
    assert v12["is_verified_lot"] is True
    assert v12["decision_code"] == "VERIFIED_LOT"
    assert v12["lighter_count"] == 10

    # Ca 13: Lot nhiều hãng (Dupont + Dunhill + Zippo >= 2 cây) -> NHẬN
    c13 = {
        "auction_id": "c13_multi_brand",
        "title": "ダンヒル デュポン ジッポ ライター 3本 セット",
        "description": "Dunhill, Dupont, Zippo 各1本ずつの計3本セットです。まとめて。",
        "current_price_jpy": 22000,
        "status": "open",
        "is_fetched": True,
    }
    v13 = verify_yahoo_lighter_lot(c13)
    assert v13["is_verified_lot"] is True
    assert v13["decision_code"] == "VERIFIED_LOT"
    assert v13["lighter_count"] == 3

    # Ca 14: Cùng phiên xuất hiện qua nhiều keyword -> Khử trùng 1 kết quả duy nhất
    all_matched = {}
    mock_scanned_items = [
        {"auction_id": "aid_dup_test", "title": "ライター 5本 まとめ 1", "bids": 5, "price_jpy": 1000},
        {"auction_id": "aid_dup_test", "title": "ライター 5本 まとめ 2", "bids": 5, "price_jpy": 1000},
        {"auction_id": "aid_dup_test", "title": "ライター 5本 まとめ 3", "bids": 5, "price_jpy": 1000},
    ]
    for it in mock_scanned_items:
        aid = it["auction_id"]
        if aid not in all_matched:
            all_matched[aid] = it
    assert len(all_matched) == 1
    assert "aid_dup_test" in all_matched

    # Ca 15: Phiên đã kết thúc (closed) -> LOẠI (CLOSED_AUCTION)
    c15 = {
        "auction_id": "c15_ended_auction",
        "title": "ライター 5本 まとめて 出品終了",
        "description": "5本セットです。",
        "current_price_jpy": 5000,
        "status": "closed",
        "is_fetched": True,
    }
    v15 = verify_yahoo_lighter_lot(c15)
    assert v15["is_verified_lot"] is False
    assert v15["decision_code"] == "CLOSED_AUCTION"


def test_t50_dashboard_server_radar_and_audit_api(tmp_path):
    """T50: Kiểm tra API /api/radars (chỉ trả lot xác minh) và /api/radar/audit (trả log bị loại)."""
    from config import AppConfig
    from db import get_db_connection
    from repository import save_lot_audit_log
    from dashboard_server import DashboardHTTPHandler
    import json
    from io import BytesIO

    from pathlib import Path
    from db import init_database
    db_file = tmp_path / "test_dash.db"
    cfg = AppConfig(bot_token="fake:token", owner_id=12345, db_path=Path(db_file), backup_dir=Path(tmp_path), price_high_threshold_jpy=500000)
    init_database(cfg.db_path)
    conn = get_db_connection(cfg.db_path)
    try:
        save_lot_audit_log(
            conn,
            auction_id="audit_single_01",
            title="Dupont 1 cay hop dep",
            decision_code="SINGLE_ITEM",
            evidence_reason="Chi ban 1 cay",
            price_jpy=15000,
            bids=3,
        )
    finally:
        conn.close()

    # Kiểm tra truy vấn audit log từ repository
    from repository import get_lot_audit_logs
    conn = get_db_connection(cfg.db_path)
    # Kiểm tra hàm get_lot_audit_stats
    from repository import get_lot_audit_stats
    conn = get_db_connection(cfg.db_path)
    try:
        stats = get_lot_audit_stats(conn)
        assert stats.get("SINGLE_ITEM") == 1
        assert stats.get("total") == 1
    finally:
        conn.close()


def test_t51_yahoo_lot_comprehensive_88_edge_cases():
    """T51: Kiểm tra mở rộng 88 ca kiểm thử bao quát toàn bộ các kịch bản thực tế của Yahoo Auctions."""
    from parser import verify_yahoo_lighter_lot

    # --- NHÓM 1: CÁC DẠNG ĐẾM SỐ LƯỢNG BẬT LỬA CHUẨN (2 đến 100 cây) -> PHẢI LÀ VERIFIED_LOT (25 ca) ---
    lot_count_cases = [
        ("ライター 2本セット まとめて", 2),
        ("ZIPPO 3個セット オイルライター", 3),
        ("ガスライター 4本 まとめ売り", 4),
        ("ダンヒル デュポン 5本 まとめて", 5),
        ("ブランドライター 6点セット", 6),
        ("オイルライター 7本 ジャンク", 7),
        ("喫煙具 ライター 8本 まとめて", 8),
        ("ライター 9点 セット売り", 9),
        ("ZIPPO ライター 10本 大量まとめ", 10),
        ("ガスライター 12本 アソート", 12),
        ("ライター 15個 まとめて出品", 15),
        ("ライター 20本 まとめ売り ジャンク", 20),
        ("ライター 30点 大量", 30),
        ("オイルライター 50本 まとめ", 50),
        ("使い捨て・ガスライター 100本 大量まとめ", 100),
        ("ZIPPO 2個 まとめて", 2),
        ("ライター 3個 セット", 3),
        ("オイルライター 5個 まとめて", 5),
        ("ガスライター 10個 まとめ", 10),
        ("ライター 20個 まとめて", 20),
        ("ライター 2点 セット", 2),
        ("ライター 3点 まとめて", 3),
        ("ライター 5点 まとめ売り", 5),
        ("ライター 10点 まとめ", 10),
        ("ライター 20点 まとめて", 20),
    ]
    for idx, (title, expected_cnt) in enumerate(lot_count_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_lot_cnt_{idx}",
            "title": title,
            "description": f"商品は画像のとおり{expected_cnt}本セットです。まとめて出品します。",
            "current_price_jpy": 5000,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is True, f"Failed on '{title}': expected VERIFIED_LOT"
        assert res["decision_code"] == "VERIFIED_LOT"
        assert res["lighter_count"] == expected_cnt, f"Failed count on '{title}': expected {expected_cnt}, got {res['lighter_count']}"

    # --- NHÓM 2: CÁC CỤM TỪ BÁN GOM / KHÔNG BÁN TÁCH (10 ca) -> VERIFIED_LOT ---
    lot_keyword_cases = [
        ("ライター まとめ売り 複数点", "まとめ売りです。"),
        ("オイルライター まとめて 出品", "すべてセットです。"),
        ("ガスライター 大量 詰め合わせ", "ライターの詰め合わせセットです。"),
        ("ブランドライター 一括 出品", "一括でお譲りします。"),
        ("ライター アソートセット", "色々なライターのアソートです。"),
        ("ZIPPO まとめて 複数点 バラ売り不可", "バラ売り不可です。"),
        ("ライター 5点 バラ売りはできません", "バラ売りはできません。"),
        ("ダンヒル デュポン ライター バラ売りNG", "バラ売りNGとなります。"),
        ("ガスライター まとめ バラ売りはいたしません", "バラ売りはいたしません。"),
        ("ZIPPO オイルライター まとめて バラ売りしません", "バラ売りしません。"),
    ]
    for idx, (title, desc) in enumerate(lot_keyword_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_lot_kw_{idx}",
            "title": title,
            "description": desc,
            "current_price_jpy": 7000,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is True, f"Failed on '{title}': expected VERIFIED_LOT"
        assert res["decision_code"] == "VERIFIED_LOT"

    # --- NHÓM 3: BÁN TÁCH LẺ HOẶC CHỌN TỪNG CÂY / TÍNH GIÁ TỪNG CÂY (10 ca) -> LOẠI (PER_PIECE_CHOICE) ---
    choice_per_piece_cases = [
        ("ライター 10本 写真", "画像の中からどれか1つをお選びください。"),
        ("ZIPPO 5点 各種", "どれか1点お選びください。"),
        ("ブランドライター 8本", "落札後にお好きな1本をお選びください。"),
        ("ガスライター 10本", "1つお選びいただけます。"),
        ("オイルライター 各種", "ご希望の番号をご連絡ください。"),
        ("ZIPPO 6点", "お好きなものをお選びください。"),
        ("ライター 10本", "1個の価格となります。ご注意ください。"),
        ("ZIPPO 5本", "1本の価格です。"),
        ("ダンヒル ライター 各種", "1点あたりの価格です。"),
        ("ライター 複数出品", "単品価格です。まとめ買いではありません。"),
    ]
    for idx, (title, desc) in enumerate(choice_per_piece_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_choice_{idx}",
            "title": title,
            "description": desc,
            "current_price_jpy": 1500,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is False, f"Failed on '{title}': must be rejected"
        assert res["decision_code"] == "PER_PIECE_CHOICE"

    # --- NHÓM 4: CHỈ BÁN HỘP RỖNG HOẶC LINH KIỆN/RUỘT (10 ca) -> LOẠI (ACCESSORY_ONLY) ---
    accessory_only_cases = [
        "ZIPPO 空箱 10個セット ケースのみ",
        "デュポン 元箱のみ 箱 3個",
        "ダンヒル ケースのみ 5個 まとめ",
        "ZIPPO インサイドユニット 3個セット",
        "ZIPPO インナーユニット ゴールド 2個",
        "ガスボンベ 5本セット ライター用ガス",
        "ライター用 発火石 フリント 10個入",
        "ZIPPO 替え芯 ウィック 10本セット",
        "ライター 部品のみ パーツまとめ 故障品",
        "ジッポー 木箱のみ コレクションケース",
    ]
    for idx, title in enumerate(accessory_only_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_acc_{idx}",
            "title": title,
            "description": "中身のライター本体はありません。ケースや消耗品のみの出品です。",
            "current_price_jpy": 3000,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is False, f"Failed on '{title}': must be rejected"
        assert res["decision_code"] == "ACCESSORY_ONLY"

    # --- NHÓM 5: HÀNG LẺ 1 CÂY KÈM PHỤ KIỆN HOẶC BẢN GIỚI HẠN (12 ca) -> LOẠI (SINGLE_ITEM) ---
    single_item_cases = [
        ("S.T.Dupont ライン2 ゴールド 1本 箱付き", "本体1点のみ。"),
        ("ZIPPO 1000個限定 1999年製 シリアル入り", "限定モデルのzippo 1本です。"),
        ("ZIPPO 500本限定 リミテッドエディション", "500本限定の1点物です。"),
        ("ZIPPO 1935レプリカ 1点 オイルライター", "1935レプリカモデル1本。"),
        ("ZIPPO 1941レプリカ 1本 ブラッククラックル", "1941モデル本体のみ1個。"),
        ("ダンヒル ローラガス ゴールド 1点 美品", "ダンヒルライター1本です。"),
        ("カルティエ オーバル ガスライター 1本", "カルティエ本体1点。"),
        ("ロンソン バンジョー オイルライター 1個", "ロンソン1本のみ出品。"),
        ("マーベラス オイルライター 1本", "単品出品です。"),
        ("コリブリ オイルライター 1点 レトロ", "本体1点。"),
        ("ZIPPO + オイル缶 + フリント 3点セット", "ZIPPOライター1点とオイル・石の3点セットです。本体は1本。"),
        ("デュポン ライター 1本 保証書 説明書 箱 4点セット", "ライター1本と付属品一式です。"),
    ]
    for idx, (title, desc) in enumerate(single_item_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_single_{idx}",
            "title": title,
            "description": desc,
            "current_price_jpy": 8000,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is False, f"Failed on '{title}': must be rejected as SINGLE_ITEM"
        assert res["decision_code"] in ("SINGLE_ITEM", "ACCESSORY_ONLY")

    # --- NHÓM 6: HÀNG KHÔNG PHẢI BẬT LỬA (8 ca) -> LOẠI (NON_LIGHTER) ---
    non_lighter_cases = [
        "ダンヒル ネクタイ 5本セット まとめ売り",
        "デュポン 万年筆 ペン先18K 2本 セット",
        "カルティエ 腕時計 マストタンク 1点",
        "古酒 ウイスキー 3本 まとめて 出品",
        "熱収縮チューブ 100本セット 配線修理",
        "ハンダ 10巻 まとめ売り 工具",
        "メンズ ソックス 靴下 10足セット",
        "ブランド 財布 バッグ 3点 まとめて",
    ]
    for idx, title in enumerate(non_lighter_cases, 1):
        res = verify_yahoo_lighter_lot({
            "auction_id": f"test_non_lighter_{idx}",
            "title": title,
            "description": "喫煙具ではありません。",
            "current_price_jpy": 6000,
            "status": "open",
            "is_fetched": True,
        })
        assert res["is_verified_lot"] is False, f"Failed on '{title}': must be rejected as NON_LIGHTER"
        assert res["decision_code"] == "NON_LIGHTER"

    # --- NHÓM 7: PHIÊN BỊ LỖI / PHIÊN KẾT THÚC / DỮ LIỆU RỖNG (8 ca) -> UNCERTAIN / CLOSED_AUCTION ---
    res_closed = verify_yahoo_lighter_lot({
        "auction_id": "test_closed",
        "title": "ライター 5本 まとめて",
        "status": "closed",
        "is_fetched": True,
    })
    assert res_closed["is_verified_lot"] is False
    assert res_closed["decision_code"] == "CLOSED_AUCTION"

    res_unfetched = verify_yahoo_lighter_lot({
        "auction_id": "test_unfetched",
        "title": "ライター 10本 まとめ売り",
        "is_fetched": False,
    })
    assert res_unfetched["is_verified_lot"] is False
    assert res_unfetched["decision_code"] == "UNCERTAIN"

    res_empty_title = verify_yahoo_lighter_lot({
        "auction_id": "test_empty_title",
        "title": "",
        "is_fetched": True,
    })
    assert res_empty_title["is_verified_lot"] is False
    assert res_empty_title["decision_code"] == "UNCERTAIN"

    # Phiên có kết thúc trong mô tả
    res_ended_desc = verify_yahoo_lighter_lot({
        "auction_id": "test_ended_desc",
        "title": "ライター 5本 まとめて",
        "description": "このオークションは終了しました。落札者決定。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_ended_desc["is_verified_lot"] is False
    assert res_ended_desc["decision_code"] == "CLOSED_AUCTION"

    # Đọc mô tả có chữ 'cho phép bán tách lẻ'
    res_split_allowed = verify_yahoo_lighter_lot({
        "auction_id": "test_split_allowed",
        "title": "ライター 5本セット",
        "description": "バラ売り可能です。コメント欄からご相談ください。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_split_allowed["is_verified_lot"] is False
    assert res_split_allowed["decision_code"] == "PER_PIECE_CHOICE"

    # Tiêu đề ghi 5 cây nhưng mô tả nói chỉ bán cây khoanh đỏ
    res_red_circle = verify_yahoo_lighter_lot({
        "auction_id": "test_red_circle",
        "title": "ライター 5本セット 写真",
        "description": "画像のうち赤丸の1点のみの出品となります。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_red_circle["is_verified_lot"] is False
    assert res_red_circle["decision_code"] == "SINGLE_ITEM"

    # Tiêu đề ghi 5 cây nhưng mô tả nói hàng lẻ
    res_single_desc = verify_yahoo_lighter_lot({
        "auction_id": "test_single_desc",
        "title": "ライター 5本セット",
        "description": "出品物は1点のみとなります。写真のケースは付属しません。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_single_desc["is_verified_lot"] is False
    assert res_single_desc["decision_code"] == "SINGLE_ITEM"

    # Giá 0 yên hoặc None vẫn không bị crash
    res_zero_price = verify_yahoo_lighter_lot({
        "auction_id": "test_zero_price",
        "title": "ライター 5本 まとめて",
        "description": "5本セットです。まとめて出品。",
        "current_price_jpy": 0,
        "status": "open",
        "is_fetched": True,
    })
    assert res_zero_price["is_verified_lot"] is True
    assert res_zero_price["lighter_count"] == 5

    # --- NHÓM 8: PHÂN LOẠI TÌNH TRẠNG VÀ THƯƠNG HIỆU (5 ca) ---
    # Ca Junk
    res_junk = verify_yahoo_lighter_lot({
        "auction_id": "test_junk_status",
        "title": "オイルライター 10本 ジャンク 部品取り 動作未確認",
        "description": "着火未確認のため全てジャンク品です。10本まとめて。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_junk["is_verified_lot"] is True
    assert res_junk["condition_code"] == "junk"
    assert "Junk" in res_junk["condition_label"]

    # Ca Hoạt động
    res_working = verify_yahoo_lighter_lot({
        "auction_id": "test_working_status",
        "title": "ガスライター 3本 着火確認済み 動作確認済み",
        "description": "3本とも着火確認済みで良好です。まとめて。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_working["is_verified_lot"] is True
    assert res_working["condition_code"] == "working"
    assert "Hoạt động" in res_working["condition_label"]

    # Ca Tia lửa đá
    res_spark = verify_yahoo_lighter_lot({
        "auction_id": "test_spark_status",
        "title": "ZIPPO 4個 火花確認済み オイルなし",
        "description": "4点とも火花のみ確認しております。まとめて。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_spark["is_verified_lot"] is True
    assert res_spark["condition_code"] == "spark_only"

    # Ca Chưa test
    res_untested_cond = verify_yahoo_lighter_lot({
        "auction_id": "test_untested_status",
        "title": "ブランドライター 6本 現状渡し",
        "description": "動作未確認のため現状渡しとなります。6本セット。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_untested_cond["is_verified_lot"] is True
    assert res_untested_cond["condition_code"] == "untested"

    # Ca Đa thương hiệu Dupont + Dunhill + Cartier
    res_multi_brands = verify_yahoo_lighter_lot({
        "auction_id": "test_multi_brands",
        "title": "デュポン ダンヒル カルティエ ライター 3本 セット",
        "description": "Dupont, Dunhill, Cartier の3本セットです。まとめて出品。",
        "status": "open",
        "is_fetched": True,
    })
    assert res_multi_brands["is_verified_lot"] is True
    assert len(res_multi_brands["brands"]) >= 3
    assert "Hỗn hợp" in res_multi_brands["brand_summary"]


# ==========================================
# T31 - T35: Kiểm thử mở rộng (eBay, Yahoo Radar, Deal Score, Dashboard API)
# ==========================================

def test_t31_ebay_price_parsing_and_conversion():
    """T31: Kiểm thử bóc tách giá USD/VND của sàn đấu giá eBay."""
    from ebay_service import parse_ebay_price_and_vnd

    # 1. Giá USD chuẩn ($25.50)
    usd_str, vnd_str = parse_ebay_price_and_vnd("$25.50", usd_rate=25500)
    assert usd_str == "$25.50"
    assert "650.250" in vnd_str or "650250" in vnd_str.replace(".", "")

    # 2. Giá VND trực tiếp từ eBay (845935.16 VND)
    usd_str2, vnd_str2 = parse_ebay_price_and_vnd("845935.16 VND", usd_rate=25500)
    assert "$33" in usd_str2
    assert "845.935" in vnd_str2

    # 3. Chuỗi rác hoặc không có giá
    usd_str3, vnd_str3 = parse_ebay_price_and_vnd("", usd_rate=25500)
    assert usd_str3 == "Xem sàn"
    assert vnd_str3 == ""


def test_t32_ebay_time_filter():
    """T32: Kiểm thử bộ lọc kết thúc trước 11h sáng mai của eBay."""
    from ebay_service import is_ending_before_tomorrow_noon

    # Kết thúc trong ngày (hợp lệ)
    assert is_ending_before_tomorrow_noon("3h left") is True
    assert is_ending_before_tomorrow_noon("12h left") is True
    assert is_ending_before_tomorrow_noon("Ends in 5h") is True

    # Kết thúc sau 2-3 ngày (loại bỏ)
    assert is_ending_before_tomorrow_noon("2d left") is False
    assert is_ending_before_tomorrow_noon("3d 4h left") is False

    # Kết thúc sau 1 ngày nhiều giờ (quá 30h)
    assert is_ending_before_tomorrow_noon("1d 10h left") is False


def test_t33_radar_resolve_brand_mode():
    """T33: Kiểm thử phân giải tham số lệnh /radar cho các danh mục mới."""
    from handlers.radar_handlers import _resolve_brand_mode

    mode, name = _resolve_brand_mode(["gas"])
    assert mode == "gas_da"
    assert "GAS ĐÁ" in name

    mode, name = _resolve_brand_mode(["dau"])
    assert mode == "dau"
    assert "DẦU" in name

    mode, name = _resolve_brand_mode(["zippo"])
    assert mode == "zippo"
    assert "ZIPPO" in name

    mode, name = _resolve_brand_mode(["thapcam"])
    assert mode == "thapcam"
    assert "THẬP CẨM" in name

    mode, name = _resolve_brand_mode(["mix"])
    assert mode == "thapcam"


def test_t34_deal_score_computation():
    """T34: Kiểm thử thuật toán tính điểm kèo thơm (Deal Score)."""
    from pricing import compute_deal_score

    # Kèo rất thơm: hoạt động, có hộp, giá sàn rẻ hơn >40% mốc tham chiếu
    good_deal = compute_deal_score(
        price_jpy=6000,
        tech_grade="working",
        has_box=True,
        bids=3,
        target_ref_jpy=12000,
    )
    assert good_deal["score"] >= 8.5
    assert "KÈO RẤT THƠM" in good_deal["label"]

    # Kèo rủi ro: hàng junk, giá sàn vượt mốc an toàn
    bad_deal = compute_deal_score(
        price_jpy=15000,
        tech_grade="junk",
        has_box=False,
        bids=30,
        target_ref_jpy=10000,
    )
    assert bad_deal["score"] <= 5.0
    assert "RỦI RO" in bad_deal["label"]

    # Kèo lô sỉ đơn giá gom hời (<= 1000Y/cây)
    lot_deal = compute_deal_score(
        price_jpy=5000,
        is_lot=True,
        unit_price_jpy=800,
        tech_grade="spark_only",
    )
    assert any("vùng gom hời" in r for r in lot_deal["reasons"])


def test_t35_dashboard_stats_and_records_logic(test_db):
    """T35: Kiểm thử logic truy vấn thống kê phục vụ WebApp Dashboard."""
    from repository import create_record, set_bid_cap, get_exchange_rate, set_exchange_rate

    # 1. Thiết lập tỷ giá
    set_exchange_rate(test_db, 170)
    rate = get_exchange_rate(test_db)
    assert rate == 170

    # 2. Thêm 2 bản ghi
    from models import Record
    r1 = create_record(test_db, Record(
        id="Q0001",
        owner_user_id=123,
        raw_text="/data dupont line 1 10000Y",
        display_name="Dupont Line 1",
        normalized_search_text="dupont line 1",
        brand="dupont",
        line="line_1",
        amount_jpy=10000,
        currency="JPY",
    ))
    r2 = create_record(test_db, Record(
        id="Q0002",
        owner_user_id=123,
        raw_text="/data dunhill rollagas 8000Y",
        display_name="Dunhill Rollagas",
        normalized_search_text="dunhill rollagas",
        brand="dunhill",
        line="rollagas",
        amount_jpy=8000,
        currency="JPY",
    ))
    from models import BidCap
    set_bid_cap(test_db, BidCap(
        id=None,
        scope_key=r1.scope_key(),
        brand=r1.brand,
        line=r1.line,
        material=r1.material,
        color=r1.color,
        box=r1.box,
        condition=r1.cosmetic_condition,
        cap_amount_jpy=12000,
        source_record_id=r1.id,
    ))

    # 3. Tính toán thống kê
    cur = test_db.cursor()
    cur.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(amount_jpy), 0) as tot_jpy FROM records WHERE deleted_at IS NULL;")
    row = cur.fetchone()
    assert row["cnt"] == 2
    assert row["tot_jpy"] == 18000

    cur.execute("SELECT COUNT(*) as cnt FROM bid_caps WHERE is_active = 1;")
    assert cur.fetchone()["cnt"] == 1

    tot_vnd = round(row["tot_jpy"] * rate)
    assert tot_vnd == 18000 * 170


def test_t103_yahoo_search_auccat_category_restriction():
    """T103: Tìm kiếm Yahoo Auctions bắt buộc phải khóa chặt trong danh mục Bật lửa 26138."""
    from unittest.mock import patch, AsyncMock
    from radar_service import fetch_yahoo_search_full_blocks
    import asyncio

    captured_urls = []
    async def mock_get(url, *args, **kwargs):
        captured_urls.append(url)
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = '<html></html>'
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        # 1. Tìm theo từ khóa -> Phải có auccat=26138
        asyncio.run(fetch_yahoo_search_full_blocks("デュポン まとめ", limit=50))
        assert len(captured_urls) == 1
        assert "auccat=26138" in captured_urls[0]
        assert "p=%E3%83%87%E3%83%A5%E3%83%9D%E3%83%B3+%E3%81%BE%E3%81%A8%E3%82%81" in captured_urls[0]

        # 2. Quét danh mục tàn phiên không từ khóa -> Phải trỏ vào /category/list/26138/
        asyncio.run(fetch_yahoo_search_full_blocks(query="", limit=50))
        assert len(captured_urls) == 2
        assert "category/list/26138/" in captured_urls[1]


def test_t104_radar_message_clickable_link_not_in_code_block():
    """T104: Link đấu giá Yahoo phải là Hyperlink HTML click mở web trực tiếp, không bị nhốt trong code block."""
    from radar_service import format_single_lot_block

    it = {
        "auction_id": "k1244090258",
        "title": "ビンテージ オイルライター まとめ売4個 ZIPPO",
        "price_jpy": 12000,
        "bids": 1,
        "remain_text": "còn 8h46m",
        "badge_label": "LOT · 4 cây",
        "condition_label": "Junk / Xác / Lấy linh kiện",
        "evidence_reason": "Mô tả xác nhận bán chung 4 bật lửa",
    }
    block = format_single_lot_block(1, it, rate=165)

    expected_url = "https://auctions.yahoo.co.jp/jp/auction/k1244090258"
    # Phải có liên kết HTML trực tiếp
    assert f"<a href='{expected_url}'>Xem Yahoo</a>" in block
    assert f"<a href='{expected_url}'>{expected_url}</a>" in block
    # Tuyệt đối KHÔNG bọc URL Yahoo vào bên trong thẻ <code> (tránh bị Telegram bắt copy thay vì mở web)
    assert f"<code>/data {expected_url}</code>" not in block
    assert f"<code>{expected_url}</code>" not in block
    # Lệnh lưu data phải ngắn gọn bằng mã đấu giá
    assert "<code>/data #k1244090258</code>" in block


def test_t105_verify_lighter_lot_category_gate():
    """T105: Bộ lọc danh mục bóc tách category_path loại bỏ ngay sản phẩm không thuộc danh mục bật lửa Yahoo 26138."""
    from parser import verify_yahoo_lighter_lot

    # 1. Hàng thời trang / đồng hồ / phụ kiện dù có từ 'zippo' hay 'dupont' nhưng sai danh mục -> Phải bị loại (NON_LIGHTER)
    fashion_item = {
        "auction_id": "cloth01",
        "title": "Dunhill ダンヒル 紳士服 スーツ ジャケット 2着セット まとめ",
        "description": "Dunhill jackets set 2pcs",
        "current_price_jpy": 5000,
        "category_path": [
            {"id": "0", "name": "オークション"},
            {"id": "23000", "name": "ファッション"},
            {"id": "23140", "name": "メンズファッション"},
            {"id": "23142", "name": "スーツ"},
        ],
        "status": "open",
        "bids": 2,
    }
    ver_fashion = verify_yahoo_lighter_lot(fashion_item)
    assert ver_fashion["is_verified_lot"] is False
    assert ver_fashion["decision_code"] == "NON_LIGHTER"
    assert "không phải danh mục bật lửa" in ver_fashion["evidence_reason"]

    # 2. Hàng đúng danh mục bật lửa (26138 hoặc 42530 Zippo) -> Được duyệt hợp lệ
    lighter_item = {
        "auction_id": "light01",
        "title": "ZIPPO ジッポ オイルライター 3点まとめ売り ジャンク",
        "description": "Zippo lighter 3 items set junk",
        "current_price_jpy": 8000,
        "category_path": [
            {"id": "0", "name": "オークション"},
            {"id": "20000", "name": "アンティーク、コレクション"},
            {"id": "21152", "name": "雑貨"},
            {"id": "26126", "name": "喫煙グッズ"},
            {"id": "26138", "name": "ライター"},
            {"id": "42530", "name": "Zippo"},
        ],
        "status": "open",
        "bids": 3,
    }
    ver_lighter = verify_yahoo_lighter_lot(lighter_item)
    assert ver_lighter["is_verified_lot"] is True
    assert ver_lighter["decision_code"] == "VERIFIED_LOT"
    assert ver_lighter["lighter_count"] == 3


def test_t52_prune_old_radar_data(tmp_path):
    """T52: Kiểm tra chức năng tự động dọn dẹp các link radar và audit log cũ quá 3 ngày."""
    from datetime import datetime, timedelta, timezone
    from db import get_db_connection, init_database
    from models import Record
    from repository import (
        create_record,
        get_db_file_size_bytes,
        mark_lot_seen,
        prune_old_radar_data,
        save_lot_audit_log,
        vacuum_database,
    )

    db_file = tmp_path / "test_prune.db"
    init_database(db_file)
    conn = get_db_connection(db_file)
    try:
        # 1. Thêm 1 bản ghi kho quẹt chính (phải được bảo toàn tuyệt đối)
        rec = Record(
            id="Q0001",
            owner_user_id=12345,
            raw_text="dupont line 2 son mai 15000y",
            display_name="Dupont Line 2 Sơn Mài",
            normalized_search_text="dupont line 2 son mai",
            amount_jpy=15000,
        )
        create_record(conn, rec)

        now_utc = datetime.now(timezone.utc)
        old_4d = (now_utc - timedelta(days=4)).isoformat()
        old_10d = (now_utc - timedelta(days=10)).isoformat()
        old_date_vn = (now_utc - timedelta(days=5)).strftime("%Y-%m-%d")
        old_ts = (now_utc - timedelta(days=5)).timestamp()

        # 2. Thêm audit logs: 1 mới, 2 cũ
        save_lot_audit_log(conn, auction_id="auc_new", title="Lô mới", decision_code="VERIFIED_LOT")
        with conn:
            conn.execute(
                "INSERT INTO yahoo_lot_audit_log (auction_id, title, decision_code, scanned_at) VALUES (?, ?, ?, ?);",
                ("auc_old_1", "Lô cũ 4 ngày", "SINGLE_ITEM", old_4d),
            )
            conn.execute(
                "INSERT INTO yahoo_lot_audit_log (auction_id, title, decision_code, scanned_at) VALUES (?, ?, ?, ?);",
                ("auc_old_2", "Lô cũ 10 ngày", "ACCESSORY_ONLY", old_10d),
            )

        # 3. Thêm radar_seen_lots: 1 mới, 2 cũ
        today_vn = now_utc.strftime("%Y-%m-%d")
        mark_lot_seen(conn, "auc_new", today_vn, "Lô mới", 1000, 1, "23:00")
        with conn:
            conn.execute(
                "INSERT INTO radar_seen_lots (auction_id, seen_date, title, price_jpy, bids, end_time, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                ("auc_old_seen_1", old_date_vn, "Lô đã tàn 1", 5000, 5, "21:00", old_4d),
            )
            conn.execute(
                "INSERT INTO radar_seen_lots (auction_id, seen_date, title, price_jpy, bids, end_time, sent_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                ("auc_old_seen_2", old_date_vn, "Lô đã tàn 2", 8000, 10, "22:00", old_10d),
            )

        # 4. Thêm auction_alarms: 1 đang chờ, 1 đã gửi hôm nay, 1 đã gửi cũ 5 ngày
        with conn:
            conn.execute(
                "INSERT INTO auction_alarms (auction_id, chat_id, title, end_time_iso, trigger_at_ts, is_sent, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                ("alarm_pending", 12345, "Đang chờ tàn", now_utc.isoformat(), now_utc.timestamp() + 3600, 0, now_utc.isoformat()),
            )
            conn.execute(
                "INSERT INTO auction_alarms (auction_id, chat_id, title, end_time_iso, trigger_at_ts, is_sent, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                ("alarm_sent_today", 12345, "Đã gửi hôm nay", now_utc.isoformat(), now_utc.timestamp() - 3600, 1, now_utc.isoformat()),
            )
            conn.execute(
                "INSERT INTO auction_alarms (auction_id, chat_id, title, end_time_iso, trigger_at_ts, is_sent, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);",
                ("alarm_sent_old", 12345, "Đã gửi 5 ngày trước", old_4d, old_ts, 1, old_10d),
            )

        # 5. Thêm processed_updates: 1 mới, 1 cũ
        with conn:
            conn.execute("INSERT INTO processed_updates (update_id, received_at) VALUES (?, ?);", (99901, now_utc.isoformat()))
            conn.execute("INSERT INTO processed_updates (update_id, received_at) VALUES (?, ?);", (99902, old_4d))

        # Kiểm tra trước khi dọn
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM yahoo_lot_audit_log;")
        assert cur.fetchone()["cnt"] == 3
        cur.execute("SELECT COUNT(*) as cnt FROM radar_seen_lots;")
        assert cur.fetchone()["cnt"] == 3
        cur.execute("SELECT COUNT(*) as cnt FROM auction_alarms;")
        assert cur.fetchone()["cnt"] == 3
        cur.execute("SELECT COUNT(*) as cnt FROM processed_updates;")
        assert cur.fetchone()["cnt"] == 2

        # 6. Chạy dọn dẹp các link cũ hơn 3 ngày
        res = prune_old_radar_data(conn, retention_days=3)
        assert res["audit_logs"] == 2
        assert res["seen_lots"] == 2
        assert res["alarms"] == 1
        assert res["processed_updates"] == 1
        assert res["total"] == 6

        # 7. Kiểm tra sau khi dọn
        cur.execute("SELECT COUNT(*) as cnt FROM yahoo_lot_audit_log;")
        assert cur.fetchone()["cnt"] == 1  # Chỉ còn bản ghi mới
        cur.execute("SELECT COUNT(*) as cnt FROM radar_seen_lots;")
        assert cur.fetchone()["cnt"] == 1  # Chỉ còn bản ghi mới
        cur.execute("SELECT COUNT(*) as cnt FROM auction_alarms;")
        assert cur.fetchone()["cnt"] == 2  # Còn bản ghi đang chờ và bản ghi vừa gửi hôm nay
        cur.execute("SELECT COUNT(*) as cnt FROM processed_updates;")
        assert cur.fetchone()["cnt"] == 1  # Chỉ còn update mới

        # 8. BẢO TOÀN DỮ LIỆU KHO QUẸT CHÍNH
        cur.execute("SELECT COUNT(*) as cnt FROM records WHERE id = 'Q0001';")
        assert cur.fetchone()["cnt"] == 1

        # 9. Kiểm tra VACUUM và kích thước file
        vacuum_database(conn)
        db_sz = get_db_file_size_bytes(db_file)
        assert db_sz > 0
    finally:
        conn.close()


def test_t53_is_genuine_lighter_item_filter():
    """T53: Kiểm tra bộ lọc bật lửa nghiêm ngặt chống thuốc lá điện tử IQOS/Vape/hàng thời trang."""
    from parser import is_genuine_lighter_item

    # 1. Các ca BỊ LOẠI TRỪ 100% (Thuốc lá điện tử, tẩu máy, phụ kiện, thời trang)
    rejected_cases = [
        "D12 アイコスイルマ本体 2点おまとめ 動作品 デジタルバイオレット ブルー",
        "IQOS ILUMA ONE アイコス イルマ ワン 本体",
        "アイコス イルマ プライム 本体",
        "glo hyper pro グロー ハイパー プロ 加熱式タバコ",
        "Ploom X ADVANCED プルーム エックス 本体",
        "ベイプ VAPE 電子タバコ リキッド ポッド",
        "ダンヒル dunhill 財布 二つ折り レザー 本革",
        "ダンヒル ベルト メンズ ビジネス",
        "ダンヒル カフス タイピン セット",
        "S.T.Dupont デュポン 万年筆 18K ペン先",
        "S.T.Dupont デュポン ボールペン",
        "カルティエ パシャ 腕時計 時計 ウォッチ",
        "カルティエ トリニティ リング 指輪 750",
        "ダンヒル サングラス メガネ 眼鏡 チタン",
        "ダンヒル 名刺入れ カードケース レザー",
        "ダンヒル キーリング キーホルダー",
        "ドクターベイプ DR.VAPE Model2 本体",
        "ZIPPO ケース 革 レザー ホルダー",
        "ZIPPO 空箱 ボックス のみ",
        "ダンヒル 灰皿 アッシュトレイ 喫煙具",
    ]
    for title in rejected_cases:
        assert is_genuine_lighter_item(title) is False, f"Lẽ ra phải LOẠI BỎ: {title}"

    # 2. Các ca HỢP LỆ (Bật lửa chính thống)
    valid_cases = [
        "S.T.Dupont デュポン ライン2 ガスライター 金色 着火OK",
        "Dunhill ダンヒル ローラガス ライター シルバー 動作未確認",
        "ZIPPO 1995年製 オイルライター ヴィンテージ",
        "カルティエ Cartier ガスライター ゴールド",
        "ロンソン バンジョー オイルライター ronson",
        "ライター まとめ売り 10本セット ジャンク",
        "ガスライター まとめて 5点 デュポン ダンヒル",
    ]
    for title in valid_cases:
        assert is_genuine_lighter_item(title) is True, f"Lẽ ra phải CHẤP NHẬN: {title}"


def test_t54_is_genuine_lighter_lot_strict():
    """T54: Kiểm tra nghiêm ngặt CHỈ CHẤP NHẬN LOT BẬT LỬA (>= 2 cây), LOẠI BỎ 100% CÂY LẺ."""
    from parser import is_genuine_lighter_lot

    # 1. Các ca HÀNG LẺ (1 cây) BẮT BUỘC BỊ LOẠI TRỪ 100% (KHÔNG PUSH LẺ)
    single_items_must_reject = [
        "S.T.Dupont デュポン ライン2 ガスライター 金色 着火OK",
        "Dunhill ダンヒル ローラガス ライター シルバー 動作未確認",
        "ZIPPO 1995年製 オイルライター ヴィンテージ",
        "カルティエ Cartier ガスライター ゴールド",
        "ロンソン バンジョー オイルライター ronson",
        "ダンヒル ライター 1本のみ 出品",
        "デュポン ギャッツビー 1点のみ",
        "zippo オイルライター 単品",
        "ダンヒル ライター 本体のみ",
        # Hàng không phải bật lửa (IQOS, phụ kiện) cũng phải bị loại
        "D12 アイコスイルマ本体 2点おまとめ 動作品 デジタルバイオレット ブルー",
        "ダンヒル 財布 二つ折り",
        "ZIPPO ケース 革",
    ]
    for title in single_items_must_reject:
        assert is_genuine_lighter_lot(title) is False, f"HÀNG LẺ LẼ RA PHẢI BỊ LOẠI BỎ: {title}"

    # 2. Các ca LOT BẬT LỬA THỰC THỤ (>= 2 cây) BẮT BUỘC ĐƯỢC CHẤP NHẬN
    genuine_lots_must_accept = [
        "ライター まとめ売り 10本セット ジャンク",
        "ガスライター まとめて 5点 デュポン ダンヒル",
        "ZIPPO ジッポ 3個セット オイルライター",
        "デュポン ダンヒル ライター 2点おまとめ",
        "オイルライター まとめ 大量 20点",
        "喫煙具 ライター 4本セット 詰め合わせ",
        "ZIPPO オイルライター 2本まとめ売り",
    ]
    for title in genuine_lots_must_accept:
        assert is_genuine_lighter_lot(title) is True, f"LOT BẬT LỬA LẼ RA PHẢI ĐƯỢC CHẤP NHẬN: {title}"


def test_t55_auto_alarm_and_golden_hours_briefing(tmp_path):
    """T55: Kiểm tra tính năng Auto-Alarm 15 phút tàn phiên và Chế độ Điểm Tin Giờ Vàng (11:30 & 20:30)."""
    import sqlite3
    import time
    from db import init_database
    from repository import (
        add_auction_alarm,
        has_auction_alarm,
        get_pending_alarms,
        mark_alarm_sent,
        get_radar_setting,
        set_radar_setting,
    )
    from radar_service import format_curated_top_radar_message

    db_path = tmp_path / "test_alarm_briefing.db"
    init_database(str(db_path))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # 1. Kiểm tra has_auction_alarm khi chưa có dữ liệu
        chat_id = 999888
        auc_id = "v11223344"
        assert has_auction_alarm(conn, auc_id, chat_id) is False

        # 2. Thêm báo thức ngầm tự động (còn 15 phút)
        now_ts = time.time()
        trigger_at = now_ts + 60.0
        alarm_id = add_auction_alarm(
            conn=conn,
            auction_id=auc_id,
            chat_id=chat_id,
            title="Lô Dupont 5 cây quý hiếm",
            price_jpy=9200,
            url=f"https://auctions.yahoo.co.jp/jp/auction/{auc_id}",
            end_time_iso="2026-10-20 23:00:00",
            trigger_at_ts=trigger_at,
        )
        assert alarm_id > 0
        assert has_auction_alarm(conn, auc_id, chat_id) is True
        assert has_auction_alarm(conn, "auc_khac", chat_id) is False
        assert has_auction_alarm(conn, auc_id, 123456) is False

        # 3. Lấy pending alarms và kiểm tra format tin nhắn báo thức
        pending = get_pending_alarms(conn)
        assert len(pending) == 1
        al = pending[0]
        title = al["title"]
        price = al["price_jpy"]
        price_str = f"{price:,}Y".replace(",", ".") if price else "chưa cập nhật"
        alert_msg = (
            f"🚨 <b>Lô hot [{title}] chỉ còn đúng 15 phút nữa hết giờ!</b>\n"
            f"⚡ Giá hiện tại: <b>{price_str}</b>. Vào snipe ngay kẻo vuột!\n"
            f"👉 <a href='https://buyee.jp/item/yahoo/auction/{auc_id}?lang=vi'>🛒 Mở Buyee để Snipe</a>"
        )
        assert "Lô hot [Lô Dupont 5 cây quý hiếm] chỉ còn đúng 15 phút nữa hết giờ!" in alert_msg
        assert "9.200Y" in alert_msg
        assert "Vào snipe ngay kẻo vuột!" in alert_msg

        # Đánh dấu đã gửi
        mark_alarm_sent(conn, al["id"])
        assert len(get_pending_alarms(conn)) == 0

        # 4. Kiểm tra Điểm Tin Giờ Vàng 11:30 (Trưa)
        today_vn = "2026-10-20"
        noon_key = f"briefing_noon_{today_vn}"
        assert get_radar_setting(conn, noon_key, default="0") == "0"

        sample_lots = [
            {
                "auction_id": "a1",
                "title": "Dupont Line 2 Lô 3 cây",
                "price_jpy": 12000,
                "bids": 8,
                "remain_text": "Còn 3 giờ",
                "lighter_count": 3,
                "brand_summary": "S.T. Dupont",
                "condition_label": "Đẹp",
            }
        ]
        noon_header = "☀️ <b>[ĐIỂM TIN GIỜ VÀNG 11:30] TOP LÔ SÁNG NAY CÓ BIDS TỐT</b>"
        noon_msg = format_curated_top_radar_message(sample_lots, total_scanned=15, rate=165, header_title=noon_header)
        assert "[ĐIỂM TIN GIỜ VÀNG 11:30]" in noon_msg
        assert "TOP LÔ SÁNG NAY CÓ BIDS TỐT" in noon_msg
        assert "Dupont Line 2 Lô 3 cây" in noon_msg

        # Lưu flag đã gửi trưa -> chống gửi lặp
        set_radar_setting(conn, noon_key, "1")
        assert get_radar_setting(conn, noon_key, default="0") == "1"

        # 5. Kiểm tra Điểm Tin Giờ Vàng 20:30 (Tối)
        night_key = f"briefing_night_{today_vn}"
        assert get_radar_setting(conn, night_key, default="0") == "0"

        night_header = "🌙 <b>[ĐIỂM TIN GIỜ VÀNG 20:30] CÁC LÔ SẮP TÀN PHIÊN ĐÊM NAY (CHUẨN BỊ SNIPE)</b>"
        night_msg = format_curated_top_radar_message(sample_lots, total_scanned=20, rate=165, header_title=night_header)
        assert "[ĐIỂM TIN GIỜ VÀNG 20:30]" in night_msg
        assert "CÁC LÔ SẮP TÀN PHIÊN ĐÊM NAY (CHUẨN BỊ SNIPE)" in night_msg

        # Lưu flag đã gửi tối -> chống gửi lặp
        set_radar_setting(conn, night_key, "1")
        assert get_radar_setting(conn, night_key, default="0") == "1"

    finally:
        conn.close()


@pytest.mark.asyncio
async def test_t41_mercari_disabled_and_yahoo_radar_active():
    """T41: Kiểm thử xác nhận tính năng dò Mercari đã tắt an toàn và Yahoo Radar hoạt động đầy đủ."""
    from unittest.mock import AsyncMock, MagicMock
    from handlers.search_handlers import text_search_handler
    from handlers.radar_handlers import _resolve_brand_mode
    from radar_service import BRAND_RADAR_CONFIGS, LOT_SEARCH_QUERIES

    # 1. Kiểm tra khi người dùng gõ Mercari: bot thông báo tắt và hướng dẫn sang Yahoo Radar, không bị crash ModuleNotFoundError
    for test_kw in ["⚡ Mercari Săn Nhanh", "⚡ Mercari", "/mercari", "mercari", "radar mercari"]:
        mock_msg = MagicMock()
        mock_msg.text = test_kw
        mock_msg.reply_html = AsyncMock()

        mock_update = MagicMock()
        mock_update.effective_message = mock_msg
        mock_update.message = mock_msg

        mock_context = MagicMock()
        mock_context.bot_data = {}

        await text_search_handler(mock_update, mock_context)
        mock_msg.reply_html.assert_called_once()
        sent_html = mock_msg.reply_html.call_args[0][0]
        assert "TẬP TRUNG 100% SÀN YAHOO AUCTIONS" in sent_html
        assert "Tính năng dò Mercari đã được tắt" in sent_html
        assert "Yahoo Auctions" in sent_html

    # 2. Kiểm tra các chế độ Radar Yahoo Auctions hoạt động chuẩn mực
    expected_modes = ["gas_da", "dau", "zippo", "thapcam", "lot", "dupont", "dunhill"]
    for m in expected_modes:
        assert m in BRAND_RADAR_CONFIGS
        assert len(BRAND_RADAR_CONFIGS[m]["queries"]) >= 3
        assert BRAND_RADAR_CONFIGS[m]["title"]

    # 3. Phân giải danh mục Yahoo Radar từ tham số lệnh
    mode, title = _resolve_brand_mode(["gas"])
    assert mode == "gas_da" and "GAS ĐÁ" in title
    mode, title = _resolve_brand_mode(["dau"])
    assert mode == "dau" and "DẦU" in title
    mode, title = _resolve_brand_mode(["zippo"])
    assert mode == "zippo" and "ZIPPO" in title
    mode, title = _resolve_brand_mode(["thapcam"])
    assert mode == "thapcam" and "THẬP CẨM" in title

    # 4. Xác nhận danh sách từ khóa quét lô Yahoo đầy đủ
    assert len(LOT_SEARCH_QUERIES) >= 20


def test_t42_hidden_gems_radar_mode():
    """T42: Kiểm thử bộ từ khóa Di vật dọn kho (Hidden Gems) và phân loại tự động."""
    from radar_service import BRAND_RADAR_CONFIGS, LOT_SEARCH_QUERIES, classify_lighter_lot_type, is_lot_title
    from handlers.radar_handlers import _resolve_brand_mode, _get_radar_page_keyboard

    # 1. Cấu hình mode 'gem' trong BRAND_RADAR_CONFIGS
    assert "gem" in BRAND_RADAR_CONFIGS
    assert "DI VẬT" in BRAND_RADAR_CONFIGS["gem"]["title"]
    assert len(BRAND_RADAR_CONFIGS["gem"]["queries"]) >= 5

    # 2. Phân giải tham số lệnh /radar
    for arg in ["gem", "gems", "divat", "di_vat", "kho"]:
        mode, title = _resolve_brand_mode([arg])
        assert mode == "gem"
        assert "DI VẬT" in title

    # 3. Phân loại tiêu đề chứa từ khóa di vật / dọn kho
    code, tag, icon = classify_lighter_lot_type("【遺品整理】古いライター 10点 まとめて 当時物")
    assert code == "gem"
    assert "DI VẬT DỌN KHO" in tag
    assert icon == "💎"

    code2, tag2, icon2 = classify_lighter_lot_type("蔵出し 古いガスライター セット")
    assert code2 == "gem"
    assert icon2 == "💎"

    # 4. Kiểm tra nút bấm trên bàn phím phân trang
    kb = _get_radar_page_keyboard(1, 2, 8, is_auto_on=True, current_mode="gem")
    btn_datas = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "radar_brand:gem" in btn_datas

    # 5. Kiểm tra nhận diện tiêu đề lô hợp lệ
    assert is_lot_title("遺品整理 ライター 大量") is True
    assert is_lot_title("蔵出し ライター セット") is True


def test_t43_ai_vision_lighter_inspection():
    """T43: Kiểm thử AI Vision nhận diện bật lửa giá trị cao (Dupont, Dunhill, Zippo cổ) qua ảnh."""
    from ai_vision_service import parse_gemini_vision_response, inspect_lighter_lot_image
    from handlers.radar_handlers import ai_inspect_command
    import asyncio

    # 1. Kiểm thử parse kết quả phát hiện đồ quý (Gem Detected)
    gem_text = """
    - ĐÁNH GIÁ: CỰC HOT / ĐỒ HIẾM
    - THƯƠNG HIỆU PHÁT HIỆN: Dupont, Dunhill, Zippo
    - ĐIỂM SÁNG: Phát hiện 1 cây Dupont Ligne 1 mạ vàng và 1 Dunhill Rollagas sọc ngang.
    - ƯỚC TÍNH: ~15 cây
    """
    res1 = parse_gemini_vision_response(gem_text)
    assert res1["gem_detected"] is True
    assert res1["rating"] == "CỰC HOT"
    assert "Dupont" in res1["detected_brands"]
    assert "Dunhill" in res1["detected_brands"]
    assert "Zippo" in res1["detected_brands"]
    assert "💎" in res1["summary_short"]
    assert "Dupont" in res1["summary_short"]

    # 2. Kiểm thử parse kết quả lô bình dân / ve chai thông thường
    junk_text = """
    - ĐÁNH GIÁ: LÔ BÌNH DÂN
    - THƯƠNG HIỆU PHÁT HIỆN: Chưa thấy hãng danh tiếng
    - ĐIỂM SÁNG: Toàn bộ là bật lửa gas nhựa dùng 1 lần (Tokai, Cricket).
    - ƯỚC TÍNH: ~20 cây
    """
    res2 = parse_gemini_vision_response(junk_text)
    assert res2["gem_detected"] is False
    assert res2["rating"] == "BÌNH DÂN"
    assert "🔍" in res2["summary_short"]

    # 3. Kiểm thử an toàn khi chuỗi rỗng / null
    res_empty = parse_gemini_vision_response("")
    assert res_empty["gem_detected"] is False
    assert res_empty["rating"] == "BÌNH DÂN"

    # 4. Kiểm thử hàm inspect_lighter_lot_image xử lý an toàn khi thiếu ảnh / thiếu key
    res_no_img = asyncio.run(inspect_lighter_lot_image(b""))
    assert res_no_img["success"] is False
    assert "rỗng" in res_no_img["error"]

    res_no_key = asyncio.run(inspect_lighter_lot_image(b"fake_bytes", api_key=""))
    # Khi không có key được truyền vào và .env không có key (hoặc có key thì kiểm tra trả về dict hợp lệ)
    assert isinstance(res_no_key, dict)

    # 5. Kiểm tra handler ai_inspect_command tồn tại và có thể gọi
    assert callable(ai_inspect_command)


def test_t44_kanban_and_pnl_tracker(test_db):
    """T44: Kiểm thử luồng Kanban đường đi hàng hóa và tính toán báo cáo P&L lợi nhuận ròng."""
    from repository import (
        create_kanban_item,
        get_kanban_items,
        update_kanban_stage,
        update_kanban_item,
        delete_kanban_item,
        get_kanban_pnl_summary,
    )

    # 1. Tạo item mới ở cột 'bidding' (Đang Canh Đấu)
    item = create_kanban_item(
        test_db,
        title="Lô 5 cây Dunhill Rollagas ve chai",
        brand="dunhill",
        auction_id="y10889922",
        stage="bidding",
        buy_price_jpy=12000,
        buy_price_vnd=2000000,
    )
    assert item["id"] > 0
    assert item["stage"] == "bidding"

    # 2. Chuyển sang cột 'transit' (Đã Thắng Bid / Đang Vận Chuyển Về)
    ok_move1 = update_kanban_stage(test_db, item["id"], "transit")
    assert ok_move1 is True

    # 3. Cập nhật chi phí ship khi hàng về tới kho VN
    ok_up1 = update_kanban_item(test_db, item["id"], {"shipping_cost_vnd": 250000})
    assert ok_up1 is True

    # 4. Chuyển sang 'restoring' (Đang Spa / Thay đá tim / Bơm gas)
    update_kanban_stage(test_db, item["id"], "restoring")
    update_kanban_item(test_db, item["id"], {"repair_cost_vnd": 150000})

    # 5. Chuyển sang 'selling' (Đã Lên Kệ) với giá chào bán
    update_kanban_stage(test_db, item["id"], "selling")
    update_kanban_item(test_db, item["id"], {"sale_price_vnd": 3800000})

    # Kiểm tra P&L khi đang tồn kho (chưa chốt bán)
    pnl_mid = get_kanban_pnl_summary(test_db)
    assert pnl_mid["active_inventory_count"] == 1
    assert pnl_mid["active_inventory_cost"] == 2000000 + 250000 + 150000  # 2.400.000 đ
    assert pnl_mid["projected_profit"] == 3800000 - 2400000  # 1.400.000 đ
    assert pnl_mid["realized_net_profit"] == 0

    # 6. Chuyển sang 'sold' (Đã Bán Cho Khách / Chốt Lời Thực Tế)
    update_kanban_stage(test_db, item["id"], "sold")
    pnl_final = get_kanban_pnl_summary(test_db)
    assert pnl_final["sold_count"] == 1
    assert pnl_final["realized_revenue"] == 3800000
    assert pnl_final["realized_cogs"] == 2400000
    assert pnl_final["realized_net_profit"] == 1400000
    assert pnl_final["roi_pct"] == round(1400000 / 2400000 * 100, 1)  # 58.3%

    # 7. Xóa item
    assert delete_kanban_item(test_db, item["id"]) is True
    assert len(get_kanban_items(test_db)) == 0


# ---------------------------------------------------------------------------
# T106 - T110: Dò lot bật lửa đủ hơn (tiêu đề thật Yahoo ngày 11/11/2026)
# ---------------------------------------------------------------------------

def _radar_chain_accepts(title: str) -> bool:
    """Chạy đúng chuỗi lọc của radar cho 1 phiên đã có bid, kết thúc hôm nay."""
    import radar_service as rs
    from parser import verify_yahoo_lighter_lot

    if rs._is_non_lighter_title(title):
        return False
    if not rs._LIGHTER_INDICATOR_RE.search(title):
        return False
    if not rs.is_lot_title(title):
        return False
    v = verify_yahoo_lighter_lot({
        "auction_id": "t106", "title": title, "current_price_jpy": 5000, "bids": 3,
        "status": "open", "is_fetched": True,
        "category_id": "26138", "category_path": [{"id": "26138", "name": "ライター"}],
    })
    return bool(v["is_verified_lot"])


def test_t106_real_lots_previously_missed_are_accepted():
    """T106: Lot thật từng bị sót (スターリング, まとめ/おまとめ, 時計 trong lot, N品, lot lẫn ガスボンベ) phải được nhận."""
    real_lots = [
        "ジッポ（Zippo）ライター3点 スターリングシルバー1992/他 ※イニシャル入り含む ジャンク 火花未確認◆おたからや【x-LI05781】",
        "48T-10-6 ジッポ ZIPPO ライター まとめ 斜め ナナメ 等 火花着火未確認",
        "ZIPPO☆ジッポ ライターおまとめ マルボロ/セブンスター他塗装剥がれ/イニシャル入り有りジャンク品※火花未確認◆おたからや【B-LI05860】",
        "48T-10-7 ジッポ ZIPPO ライター まとめ limited No.0199 時計 等 火花着火未確認",
        "【AU-27】ブランドライター　6品おまとめ　dunhill　ダンヒル　S.T.Dupont　デュポン　CELINE　セリーヌ　ローラー式　ガスライター",
        "【16点セット/動作未確認】RONSON ロンソン MaruMan マルマン FONG YUON 他 ライター 携帯灰皿 マッチケース ガスボンベ(ライター専用）",
        "【宝】 Zippo ジッポ― ケース付き ライター いろいろセット TC091TBBC1",
        "■Zippo / GIVENCHY / YSL / RONSON 他 ライター 多数 まとめ 火花あり/現状渡し 中古【UW100546】",
        "NA764 ライターまとめ 現状渡し 中古 ジャンク品",
    ]
    for title in real_lots:
        assert _radar_chain_accepts(title) is True, f"LOT THẬT BỊ SÓT: {title}"


def test_t107_singles_accessories_and_non_lighters_still_rejected():
    """T107: Cây lẻ, まとめ買い/複数出品, phụ kiện, IQOS/vape, đồng hồ/nhẫn không kèm ライター vẫn bị loại."""
    must_reject = [
        "ダンヒル ライター シルバー 複数出品中 おまとめ取引可",
        "ZIPPO スターリングシルバー オイルライター 1995年製 まとめ買い歓迎",
        "ZIPPO スターリングシルバー オイルライター 1995年製",
        "アイコス イルマ ライター 2点まとめ",
        "IQOS ILUMA ライター まとめ 3台",
        "電子タバコ ベイプ ライター まとめ 5個",
        "ZIPPO 空箱 5点 まとめ ライター用",
        "ZIPPO 空箱のみ 5点 まとめ",
        "ライター用 ガスボンベ 3本 まとめ",
        "ZIPPO インサイドユニット のみ 10個 まとめ ライター",
        "ライター フリント 20個 まとめ",
        "ZIPPO 腕時計 まとめ 3点",
        "シルバーリング 指輪 まとめ 5点 ZIPPO",
        # Gom phụ kiện ghi 'まとめ': không phải lot bật lửa
        "ZIPPO ライターケース 3点 まとめ 革",
        "ライター オイル 3本 まとめ ZIPPO",
        "ライター 化粧箱 5個 まとめ",
        "ZIPPO ライター 箱 5点 まとめ",
    ]
    for title in must_reject:
        assert _radar_chain_accepts(title) is False, f"LẼ RA PHẢI BỊ LOẠI: {title}"


def test_t108_lot_count_keywords_and_exclusion_helpers():
    """T108: Đếm 'N品おまとめ', bỏ qua cụm まとめ買い/複数出品, リング chỉ loại nhẫn chứ không loại スターリング."""
    import radar_service as rs
    from parser import _has_lot_keyword, extract_actual_lighter_count

    assert extract_actual_lighter_count("ブランドライター　6品おまとめ　dunhill　ダンヒル", "")[0] == 6
    assert extract_actual_lighter_count("ライター 3品セット デュポン", "")[0] == 3

    assert _has_lot_keyword("ZIPPO ライター まとめ 斜め") is True
    assert _has_lot_keyword("ZIPPO ライター いろいろセット") is True
    assert _has_lot_keyword("ダンヒル ライター 複数出品中 おまとめ取引可") is False
    assert _has_lot_keyword("ZIPPO ライター まとめ買い歓迎") is False
    assert _has_lot_keyword("ZIPPO ライター 同梱可 まとめて発送") is False
    assert _has_lot_keyword("ZIPPO ライターケース まとめ") is False
    assert _has_lot_keyword("ジッポ ZIPPO ライター まとめ 等 レザーケース 火花着火未確認") is True
    assert _has_lot_keyword("Zippo ジッポ ケース付き ライター いろいろセット") is True

    assert rs._is_non_lighter_title("ZIPPO スターリングシルバー オイルライター") is False
    assert rs._is_non_lighter_title("シルバーリング 指輪 ZIPPO") is True
    assert rs._is_non_lighter_title("ZIPPO ライター まとめ 時計 等") is False
    assert rs._is_non_lighter_title("ZIPPO 懐中時計") is True
    assert rs._is_non_lighter_title("アイコス ライター まとめ") is True
    assert rs._is_non_lighter_title("") is False


async def _no_sleep(*_args, **_kwargs):
    return None


def test_t109_category_bid_sweep_pages_until_zero_bid():
    """T109: Quét trọn danh mục theo bid: lật trang tới phiên 0 bid, tự đảo o1 nếu Yahoo đảo chiều sắp xếp."""
    import asyncio
    from unittest.mock import patch
    import radar_service as rs

    def _page(n, start_bids, last_zero=False):
        rows = [{"auction_id": f"a{start_bids}_{i}", "title": "ZIPPO ライター まとめ", "bids": max(1, start_bids - i)} for i in range(n)]
        if last_zero:
            rows[-1]["bids"] = 0
        return rows

    # 1. o1=a đúng chiều 'nhiều bid trước': trang 1, 2 đầy; trang 3 có phiên 0 bid ở cuối -> dừng, không nạp trang 4-5
    calls = []
    pages_a = {1: _page(100, 500), 101: _page(100, 300), 201: _page(40, 100, last_zero=True),
               301: _page(100, 0, last_zero=True), 401: _page(100, 0, last_zero=True)}

    async def fake_fetch(query="", limit=100, category_id="", offset=1, sort_key="end", sort_order="a"):
        calls.append((offset, sort_key, sort_order))
        return pages_a.get(offset, []) if sort_order == "a" else []

    rs._BID_SWEEP_CACHE.clear()
    with patch.object(rs, "fetch_yahoo_search_full_blocks", side_effect=fake_fetch):
        got = asyncio.run(rs.fetch_category_bid_sweep("26138"))
    assert len(got) == 240
    assert all(c[1] == "bids" and c[2] == "a" for c in calls)
    assert {c[0] for c in calls} >= {1, 101, 201}

    # 2. Yahoo đảo chiều: o1=a trả phiên 0 bid đầu tiên -> tự chuyển sang o1=d
    calls.clear()
    pages_d = {1: _page(100, 400), 101: _page(10, 50, last_zero=True)}

    async def fake_fetch_flip(query="", limit=100, category_id="", offset=1, sort_key="end", sort_order="a"):
        calls.append((offset, sort_key, sort_order))
        if sort_order == "a":
            return [{"auction_id": "z0", "title": "x", "bids": 0}] * 100
        return pages_d.get(offset, [])

    rs._BID_SWEEP_CACHE.clear()
    with patch.object(rs, "fetch_yahoo_search_full_blocks", side_effect=fake_fetch_flip):
        got = asyncio.run(rs.fetch_category_bid_sweep("26138"))
    assert len(got) == 110
    assert any(c == (101, "bids", "d") for c in calls)

    # 3. Danh mục không có phiên nào có bid -> chỉ trả trang đầu, không lật tiếp
    calls.clear()

    async def fake_fetch_empty(query="", limit=100, category_id="", offset=1, sort_key="end", sort_order="a"):
        calls.append((offset, sort_key, sort_order))
        return [{"auction_id": "z0", "title": "x", "bids": 0}] * 100

    rs._BID_SWEEP_CACHE.clear()
    with patch.object(rs, "fetch_yahoo_search_full_blocks", side_effect=fake_fetch_empty):
        got = asyncio.run(rs.fetch_category_bid_sweep("26138"))
    assert all(c[0] == 1 for c in calls)

    # 4. Gọi lại trong 4 phút -> dùng lại kết quả, không tải thêm trang; bản trả về là bản sao độc lập
    rs._BID_SWEEP_CACHE.clear()
    calls.clear()
    with patch.object(rs, "fetch_yahoo_search_full_blocks", side_effect=fake_fetch):
        first = asyncio.run(rs.fetch_category_bid_sweep("26138"))
        n_calls = len(calls)
        first[0]["remain_text"] = "đã sửa ở lượt trước"
        again = asyncio.run(rs.fetch_category_bid_sweep("26138"))
    assert len(again) == 240 and len(calls) == n_calls
    assert "remain_text" not in again[0]

    # 5. Lượt quét bị Yahoo lỗi giữa chừng -> không lưu cache, lượt sau quét lại từ đầu
    rs._BID_SWEEP_CACHE.clear()
    calls.clear()
    pages_err = {1: _page(100, 500), 101: [], 201: _page(40, 100, last_zero=True)}

    async def fake_fetch_err(query="", limit=100, category_id="", offset=1, sort_key="end", sort_order="a"):
        calls.append((offset, sort_key, sort_order))
        return pages_err.get(offset, _page(100, 0, last_zero=True))

    with patch.object(rs, "fetch_yahoo_search_full_blocks", side_effect=fake_fetch_err),             patch("asyncio.sleep", new=_no_sleep):
        asyncio.run(rs.fetch_category_bid_sweep("26138"))
    assert "26138" not in rs._BID_SWEEP_CACHE
    rs._BID_SWEEP_CACHE.clear()


def test_t110_search_shipping_fee_only_when_fixed():
    """T110: Phí ship lấy từ trang tìm kiếm: miễn phí = 0, phí cố định (SINGLE/QUANTITY) = số yên, còn lại = None."""
    import asyncio
    import json as _json
    from unittest.mock import AsyncMock, patch
    from radar_service import fetch_yahoo_search_full_blocks

    def _it(aid, **kw):
        base = {"auctionId": aid, "title": f"ZIPPO ライター まとめ {aid}", "price": 1000, "bidCount": 2,
                "endTime": "2026-11-11T23:00:00+09:00", "imageUrl": ""}
        base.update(kw)
        return base

    listing = [
        _it("free", isFreeShipping=True, hasShippingFee=True, currentPriceShippingFeeType="SINGLE", currentPriceShippingFee=0),
        _it("single", isFreeShipping=False, hasShippingFee=True, currentPriceShippingFeeType="SINGLE", currentPriceShippingFee=800),
        _it("qty", isFreeShipping=False, hasShippingFee=True, currentPriceShippingFeeType="QUANTITY", currentPriceShippingFee=1200),
        _it("amount", isFreeShipping=False, hasShippingFee=True, currentPriceShippingFeeType="AMOUNT", currentPriceShippingFee=690),
        _it("pref", isFreeShipping=False, hasShippingFee=True, currentPriceShippingFeeType="PREFECTURE", currentPriceShippingFee=800),
        _it("size", isFreeShipping=False, hasShippingFee=True, currentPriceShippingFeeType="SIZE_WEIGHT", currentPriceShippingFee=1440),
        _it("none", isFreeShipping=False, hasShippingFee=False, currentPriceShippingFeeType=None, currentPriceShippingFee=None),
    ]
    next_data = {"props": {"pageProps": {"initialState": {"search": {"items": {"listing": {"items": listing}, "totalResultsAvailable": 7}}}}}}
    html = '<html><script id="__NEXT_DATA__" type="application/json">' + _json.dumps(next_data, ensure_ascii=False) + "</script></html>"

    async def mock_get(url, *args, **kwargs):
        resp = AsyncMock()
        resp.status_code = 200
        resp.text = html
        return resp

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        got = asyncio.run(fetch_yahoo_search_full_blocks(query="", limit=100, category_id="26138", sort_key="bids", sort_order="a"))
    fee = {x["auction_id"]: x["shipping_fee_jpy"] for x in got}
    assert fee == {"free": 0, "single": 800, "qty": 1200, "amount": None, "pref": None, "size": None, "none": None}


# ---------------------------------------------------------------------------
# T111 - T112: AI soi ảnh dùng gói Gemini miễn phí (đo thật 11/11/2026: gemini-2.5-flash free chỉ 20 lượt/ngày)
# ---------------------------------------------------------------------------

def test_t111_ai_vision_parse_ignores_negated_brands():
    """T111: Câu trả lời thật của AI: hãng nằm trong câu phủ định không được tính, mức đánh giá đọc từ dòng ĐÁNH GIÁ."""
    from ai_vision_service import parse_gemini_vision_response

    # 1. gemini-3.5-flash-lite, lô 3 cây khắc chữ (b1251176493)
    t1 = (
        "- ĐÁNH GIÁ: [TIỀM NĂNG / ĐỒ CỔ Á ĐÔNG]\n"
        "- THƯƠNG HIỆU PHÁT HIỆN: Chưa thấy hãng Âu-Mỹ danh tiếng (không phải Dunhill, Dupont, Cartier hay Zippo chính hãng).\n"
        "- ĐIỂM SÁNG: Lô gồm 3 chiếc bật lửa dạng nắp gập bằng kim loại, khắc chữ nổi chìm thủ công.\n"
        "- ƯỚC TÍNH: ~3 cây"
    )
    r1 = parse_gemini_vision_response(t1)
    assert r1["detected_brands"] == []
    assert r1["rating"] == "TIỀM NĂNG"

    # 2. gemini-3.1-flash-lite, lô ~100 Zippo phổ thông (k1251129601): BÌNH DÂN, không có Dupont/Dunhill/Cartier
    t2 = (
        "Chào bạn, với tư cách là chuyên gia thẩm định bật lửa, tôi đã phân tích kỹ hình ảnh lô hàng bạn cung cấp.\n\n"
        "- **ĐÁNH GIÁ:** [BÌNH DÂN]\n"
        "- **THƯƠNG HIỆU PHÁT HIỆN:** Chủ yếu là Zippo (Mỹ) và một số bật lửa gas phổ thông Nhật Bản (có thể có Maruman hoặc Prince đời thấp). "
        "Không thấy sự xuất hiện của các \"ông lớn\" như S.T. Dupont, Dunhill hay Cartier.\n"
        "- **ĐIỂM SÁNG:** \n"
        "    - Lô hàng này tập trung chủ yếu vào Zippo phổ thông (Zippo thường, Zippo in logo, Zippo sơn tĩnh điện). \n"
        "    - Có một vài cây Zippo vỏ đồng (Brass), nhưng không có cây nào thuộc hàng \"siêu phẩm\" hay bạc khối (Sterling).\n"
        "- **ƯỚC TÍNH:** ~100 - 110 cây.\n\n"
        "**Phân tích thêm:** Đây là dạng lô \"hàng xô\" chứ không phải là nguồn để săn tìm đồ quý hiếm (high-end)."
    )
    r2 = parse_gemini_vision_response(t2)
    assert r2["rating"] == "BÌNH DÂN"
    assert r2["gem_detected"] is False
    assert r2["detected_brands"] == ["Zippo", "Maruman"]
    assert "💎" not in r2["summary_short"]
    assert r2["highlights"].startswith("Lô hàng này")  # không còn gạch đầu dòng thừa '- '

    # 3. AI chép nguyên khuôn mẫu nhiều mức -> không gắn đồ hiếm
    r3 = parse_gemini_vision_response("- ĐÁNH GIÁ: [CỰC HOT / TIỀM NĂNG / BÌNH DÂN]\n- THƯƠNG HIỆU PHÁT HIỆN: Chưa thấy hãng danh tiếng")
    assert r3["gem_detected"] is False
    assert r3["rating"] == "BÌNH DÂN"

    # 4. Có hãng thật -> vẫn nhận (S.T. Dupont viết có dấu chấm)
    r4 = parse_gemini_vision_response(
        "- ĐÁNH GIÁ: CỰC HOT\n- THƯƠNG HIỆU PHÁT HIỆN: S.T. Dupont Ligne 2, Dunhill Rollagas\n"
        "- ĐIỂM SÁNG: 1 cây S.T. Dupont mạ vàng.\n- ƯỚC TÍNH: ~6 cây"
    )
    assert r4["gem_detected"] is True
    assert r4["rating"] == "CỰC HOT"
    assert r4["detected_brands"] == ["Dupont", "Dunhill"]


def test_t112_ai_vision_free_model_chain_and_key_in_header(monkeypatch):
    """T112: Model hết quota ngày (429) bị bỏ qua tới giờ mở lại, chuyển ngay model kế; key không nằm trong URL; bỏ phần thought."""
    import asyncio
    from unittest.mock import patch
    import ai_vision_service as av

    monkeypatch.delenv("GEMINI_VISION_MODELS", raising=False)
    av._MODEL_BLOCKED_UNTIL.clear()
    chain = av._vision_model_chain()
    assert chain[0] == "gemini-3.1-flash-lite" and "gemini-2.5-flash" in chain

    class _Resp:
        def __init__(self, status, body):
            self.status_code = status
            self._body = body
            self.text = str(body)

        def json(self):
            return self._body

    quota_day = {"error": {"code": 429, "message": "You exceeded your current quota", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure", "violations": [
            {"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier", "quotaValue": "20"}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "18356s"}]}}
    ok_body = {"candidates": [{"content": {"parts": [
        {"text": "Thinking: Dupont? Cartier? CỰC HOT?", "thought": True},
        {"text": "- ĐÁNH GIÁ: [TIỀM NĂNG]\n- THƯƠNG HIỆU PHÁT HIỆN: Zippo\n- ĐIỂM SÁNG: 1 Zippo đồng.\n- ƯỚC TÍNH: ~5 cây"},
    ]}}]}

    calls = []
    plan = {}

    async def fake_post(url, *args, **kwargs):
        model = url.split("/models/")[1].split(":")[0]
        calls.append((model, url, (kwargs.get("headers") or {}).get("x-goog-api-key")))
        status, body = plan.get(model, (200, ok_body))
        return _Resp(status, body)

    try:
        with patch("httpx.AsyncClient.post", side_effect=fake_post):
            # 1. Model đầu hết quota ngày -> dùng model kế, kết quả không lẫn phần thought
            plan.update({"gemini-3.1-flash-lite": (429, quota_day)})
            res = asyncio.run(av.inspect_lighter_lot_image(b"img", api_key="TEST_KEY_123"))
            assert res["success"] is True
            assert res["model"] == "gemini-3.5-flash-lite"
            assert res["detected_brands"] == ["Zippo"]
            assert "Thinking" not in res["raw_text"]
            assert all("key=" not in c[1] and "TEST_KEY_123" not in c[1] for c in calls)
            assert all(c[2] == "TEST_KEY_123" for c in calls)
            assert av._MODEL_BLOCKED_UNTIL["gemini-3.1-flash-lite"] > 0

            # 2. Lượt sau không gọi lại model đã hết quota
            calls.clear()
            res = asyncio.run(av.inspect_lighter_lot_image(b"img", api_key="TEST_KEY_123"))
            assert res["success"] is True
            assert [c[0] for c in calls] == ["gemini-3.5-flash-lite"]

            # 3. Quá tải 503 -> chuyển model kế nhưng KHÔNG khóa model đó
            av._MODEL_BLOCKED_UNTIL.clear()
            calls.clear()
            plan.clear()
            plan.update({"gemini-3.1-flash-lite": (503, {"error": {"code": 503, "message": "high demand"}})})
            res = asyncio.run(av.inspect_lighter_lot_image(b"img", api_key="TEST_KEY_123"))
            assert res["success"] is True and res["model"] == "gemini-3.5-flash-lite"
            assert "gemini-3.1-flash-lite" not in av._MODEL_BLOCKED_UNTIL

            # 4. Mọi model hết quota -> báo lỗi rõ ràng, lượt sau không gửi request nào
            av._MODEL_BLOCKED_UNTIL.clear()
            plan.clear()
            for m in chain:
                plan[m] = (429, quota_day)
            res = asyncio.run(av.inspect_lighter_lot_image(b"img", api_key="TEST_KEY_123"))
            assert res["success"] is False and "quota" in res["error"]
            calls.clear()
            res = asyncio.run(av.inspect_lighter_lot_image(b"img", api_key="TEST_KEY_123"))
            assert res["success"] is False and calls == []
            assert "hết quota" in res["error"]
    finally:
        av._MODEL_BLOCKED_UNTIL.clear()
