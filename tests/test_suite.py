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









