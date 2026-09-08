"""Bộ tính toán giá tham khảo và mốc bid cá nhân theo chính sách nghiệp vụ V1."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence

from models import BidCap, Record


@dataclass
class PricingResult:
    has_cap: bool
    cap_amount_jpy: int | None = None
    cap_source_id: str = ""
    cap_updated_at: str = ""
    
    reference_price_jpy: int | None = None
    min_price_jpy: int | None = None
    max_price_jpy: int | None = None
    total_valid_records: int = 0
    
    is_recent_window: bool = False
    window_label: str = ""  # '1 giao dịch' | '2 giao dịch' | 'gần đây' | 'toàn bộ lịch sử'
    
    summary_text: str = ""
    note_text: str = ""


def filter_valid_pricing_records(records: Sequence[Record]) -> list[Record]:
    """Lọc các bản ghi hợp lệ để tính giá thắng tham khảo đơn chiếc.
    
    Loại trừ:
    - Bản ghi đã xóa mềm (deleted_at is not None)
    - Loại không phải thắng đấu giá (record_type != 'win')
    - Giá all-in đã gồm phí chưa bóc tách (price_basis == 'all_in')
    - Mua theo lô nhiều cây (is_lot == True)
    """
    valid = []
    for r in records:
        if r.deleted_at is not None:
            continue
        if r.record_type != "win":
            continue
        if r.price_basis != "pure":
            continue
        if r.is_lot:
            continue
        if r.amount_jpy <= 0:
            continue
        valid.append(r)
    return valid


def compute_median_jpy(prices: list[int]) -> int:
    """Tính trung vị (median) của danh sách giá JPY.
    
    Nếu số bản ghi chẵn: lấy trung bình 2 số giữa và làm tròn xuống 1 yên.
    """
    s = sorted(prices)
    n = len(s)
    if n == 0:
        return 0
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    else:
        return math.floor((s[mid - 1] + s[mid]) / 2)


def format_jpy(amount: int | None) -> str:
    """Định dạng số tiền JPY có dấu chấm phân cách hàng nghìn theo chuẩn tiếng Việt (ví dụ: 13.400)."""
    if amount is None:
        return "0"
    return f"{amount:,}".replace(",", ".")


def format_currency_amount(amount: int | None, currency: str = "JPY", with_approx: bool = False) -> str:
    """Định dạng số tiền kèm đơn vị tiền tệ chuẩn (VND, USD, JPY)."""
    if amount is None:
        return "0"
    curr = (currency or "JPY").upper()
    val_str = f"{amount:,}".replace(",", ".")
    if curr == "VND":
        res = f"{val_str} đ"
        if with_approx and amount >= 1000:
            approx_jpy = round(amount / 165)
            res += f" (~{approx_jpy:,} yên)".replace(",", ".")
        return res
    elif curr == "USD":
        res = f"${val_str}"
        if with_approx and amount > 0:
            approx_vnd = round(amount * 25500)
            res += f" (~{approx_vnd:,} đ)".replace(",", ".")
        return res
    else:
        res = f"{val_str} yên"
        if with_approx and amount >= 100:
            approx_vnd = round(amount * 165)
            res += f" (~{approx_vnd:,} đ)".replace(",", ".")
        return res


def calculate_reference_pricing(
    records: Sequence[Record],
    active_cap: BidCap | None = None,
    now: datetime | None = None,
) -> PricingResult:
    """Tính toán mốc bid tham khảo theo chính sách 4 cấp độ ưu tiên."""
    if now is None:
        now = datetime.now(timezone.utc)

    # Nếu đã có trần cá nhân active cho đúng nhóm so sánh
    if active_cap and active_cap.is_active:
        cap_fmt = format_jpy(active_cap.cap_amount_jpy)
        return PricingResult(
            has_cap=True,
            cap_amount_jpy=active_cap.cap_amount_jpy,
            cap_source_id=active_cap.source_record_id,
            cap_updated_at=active_cap.updated_at,
            reference_price_jpy=active_cap.cap_amount_jpy,
            window_label="Trần cá nhân đã đặt",
            summary_text=f"Trần bid anh đã đặt: {cap_fmt} yên",
            note_text=f"Nguồn: #{active_cap.source_record_id} · Cập nhật: {active_cap.updated_at[:10]}",
        )

    valid_records = filter_valid_pricing_records(records)
    count = len(valid_records)

    if count == 0:
        return PricingResult(
            has_cap=False,
            total_valid_records=0,
            window_label="Chưa có dữ liệu",
            summary_text="Chưa có dữ liệu giao dịch phù hợp.",
            note_text="Chưa đủ thông tin để đưa ra mốc tham khảo.",
        )

    # Trường hợp 1: Có đúng 1 giao dịch
    if count == 1:
        r = valid_records[0]
        p_fmt = format_jpy(r.amount_jpy)
        return PricingResult(
            has_cap=False,
            reference_price_jpy=r.amount_jpy,
            min_price_jpy=r.amount_jpy,
            max_price_jpy=r.amount_jpy,
            total_valid_records=1,
            window_label="1 bản ghi",
            summary_text=f"Mốc bid tham khảo: {p_fmt} yên\nGiá từng thắng: {p_fmt} yên · 1 bản ghi",
            note_text="1 bản ghi, không phải giá thị trường. Chưa gồm phí; cần đối chiếu tình trạng cây đang đấu.",
        )

    # Trường hợp 2: Có đúng 2 giao dịch
    prices = [r.amount_jpy for r in valid_records]
    min_p, max_p = min(prices), max(prices)
    min_fmt, max_fmt = format_jpy(min_p), format_jpy(max_p)
    if count == 2:
        return PricingResult(
            has_cap=False,
            reference_price_jpy=None,  # Không tự chốt 1 con số
            min_price_jpy=min_p,
            max_price_jpy=max_p,
            total_valid_records=2,
            window_label="2 bản ghi",
            summary_text=f"2 lần thắng: {min_fmt} yên và {max_fmt} yên (khoảng: {min_fmt} - {max_fmt} yên)",
            note_text="Hiện có 2 giao dịch, chưa đủ dữ liệu để tự động chọn 1 mốc nên bid. Anh có thể đặt trần cá nhân.",
        )

    # Trường hợp 3: Có từ 3 giao dịch trở lên -> Xét cửa sổ 180 ngày
    cutoff_180d = now - timedelta(days=180)
    recent_records: list[Record] = []
    for r in valid_records:
        if r.auction_date:
            try:
                dt = datetime.fromisoformat(r.auction_date).replace(tzinfo=timezone.utc)
                if dt >= cutoff_180d:
                    recent_records.append(r)
            except ValueError:
                pass

    # Nếu trong 180 ngày có ít nhất 3 bản ghi
    if len(recent_records) >= 3:
        recent_prices = [r.amount_jpy for r in recent_records]
        median_price = compute_median_jpy(recent_prices)
        med_fmt = format_jpy(median_price)
        r_min, r_max = min(recent_prices), max(recent_prices)
        r_min_fmt, r_max_fmt = format_jpy(r_min), format_jpy(r_max)
        return PricingResult(
            has_cap=False,
            reference_price_jpy=median_price,
            min_price_jpy=r_min,
            max_price_jpy=r_max,
            total_valid_records=len(recent_records),
            is_recent_window=True,
            window_label=f"{len(recent_records)} giao dịch gần đây (180 ngày)",
            summary_text=f"Mốc bid tham khảo (trung vị): {med_fmt} yên\nKhoảng giá gần đây: {r_min_fmt} - {r_max_fmt} yên ({len(recent_records)} bản ghi)",
            note_text="Tính trên các giao dịch trong 180 ngày gần nhất.",
        )
    else:
        # Sử dụng toàn bộ lịch sử
        median_price = compute_median_jpy(prices)
        med_fmt = format_jpy(median_price)
        min_fmt, max_fmt = format_jpy(min_p), format_jpy(max_p)
        return PricingResult(
            has_cap=False,
            reference_price_jpy=median_price,
            min_price_jpy=min_p,
            max_price_jpy=max_p,
            total_valid_records=count,
            is_recent_window=False,
            window_label=f"Ít dữ liệu gần đây ({count} bản ghi lịch sử)",
            summary_text=f"Mốc bid tham khảo (trung vị): {med_fmt} yên\nKhoảng giá lịch sử: {min_fmt} - {max_fmt} yên ({count} bản ghi)",
            note_text="Ít dữ liệu trong 180 ngày qua; mốc này tính trên toàn bộ lịch sử mua.",
        )


def get_bid_advisory(pricing: PricingResult, primary_currency: str = "JPY") -> dict[str, str | int | None]:
    """Tạo thông tin khuyến nghị đi bid tức thì cho người dùng khi tham gia đấu giá."""
    curr = (primary_currency or "JPY").upper()
    rate = 165

    # 1. Xác định mức giá nên bid tối đa
    if pricing.has_cap and pricing.cap_amount_jpy:
        max_bid = pricing.cap_amount_jpy
        basis = "Theo trần bid cá nhân anh đã đặt"
    elif pricing.reference_price_jpy:
        max_bid = pricing.reference_price_jpy
        if pricing.total_valid_records == 1:
            basis = "Theo 1 lần thắng lịch sử trước đây"
        else:
            basis = f"Theo giá trung vị ({pricing.total_valid_records} lần thắng)"
    elif pricing.max_price_jpy:
        max_bid = pricing.max_price_jpy
        basis = f"Theo mức giá cao nhất trong {pricing.total_valid_records} lần thắng"
    else:
        max_bid = None
        basis = "Chưa có dữ liệu giá thắng phù hợp"

    if max_bid is None or max_bid <= 0:
        return {
            "has_recommendation": False,
            "max_bid": None,
            "max_bid_text": "Chưa có mốc tham khảo",
            "landing_cost_text": "",
            "safe_zone_text": "",
            "stop_warning_text": "Chưa có dữ liệu để khuyến nghị mốc dừng.",
            "basis_text": basis,
            "condition_hint": "",
        }

    max_bid_text = format_currency_amount(max_bid, curr, with_approx=True)

    # Ước tính về tay
    if curr == "JPY":
        landing_vnd = round(max_bid * rate) + 200000
        landing_fmt = f"{landing_vnd:,}".replace(",", ".")
        landing_text = f"~{landing_fmt} đ (đã gồm ~200k phí ship quốc tế & phụ phí)"
    elif curr == "USD":
        landing_vnd = round(max_bid * 25500) + 200000
        landing_fmt = f"{landing_vnd:,}".replace(",", ".")
        landing_text = f"~{landing_fmt} đ (đã gồm ~200k phí ship quốc tế)"
    else:
        landing_vnd = max_bid + 30000  # ship nội địa
        landing_fmt = f"{landing_vnd:,}".replace(",", ".")
        landing_text = f"~{landing_fmt} đ (gồm ~30k ship nội địa)"

    # Vùng an toàn & Điểm dừng
    if pricing.min_price_jpy and pricing.min_price_jpy < max_bid:
        min_fmt = format_currency_amount(pricing.min_price_jpy, curr)
        safe_zone_text = f"{min_fmt} → {format_currency_amount(max_bid, curr)}"
    else:
        safe_zone_text = f"Dưới {max_bid_text}"

    stop_warning_text = (
        f"Nếu sàn vượt quá {format_currency_amount(max_bid, curr)} ➔ <b>DỪNG LẠI</b>, "
        f"bỏ phiên không theo để tránh bị mua đắt / ôm hớ!"
    )

    condition_hint = (
        "💡 <i>Mẹo bid: Cây có hộp & đẹp giữ giá tốt. Nếu cây trên sàn trầy xước "
        "hoặc thiếu hộp, anh nên trừ bớt 2.000 - 3.000 yên (~300k - 500k).</i>"
    )

    return {
        "has_recommendation": True,
        "max_bid": max_bid,
        "max_bid_text": max_bid_text,
        "landing_cost_text": landing_text,
        "safe_zone_text": safe_zone_text,
        "stop_warning_text": stop_warning_text,
        "basis_text": basis,
        "condition_hint": condition_hint,
    }


def calculate_reverse_profit(
    target_sale_vnd: int,
    profit_pct: float | None = None,
    profit_vnd: int | None = None,
    shipping_fee_vnd: int = 200000,
    maintenance_fee_vnd: int = 100000,
    rate: int = 165,
) -> dict[str, Any]:
    """Tính ngược giá bid tối đa trên sàn dựa trên giá bán lại kỳ vọng và lợi nhuận mong muốn."""
    if profit_pct is not None and profit_pct > 0:
        calc_profit_vnd = round(target_sale_vnd * (profit_pct / 100.0))
        profit_label = f"{profit_pct:g}% (~{calc_profit_vnd:,} đ)".replace(",", ".")
    elif profit_vnd is not None and profit_vnd > 0:
        calc_profit_vnd = profit_vnd
        calc_pct = round((profit_vnd / target_sale_vnd) * 100, 1)
        profit_label = f"{calc_profit_vnd:,} đ (~{calc_pct}%)".replace(",", ".")
    else:
        calc_profit_vnd = round(target_sale_vnd * 0.25)  # Mặc định kỳ vọng lãi 25%
        profit_label = f"25% (~{calc_profit_vnd:,} đ)".replace(",", ".")

    max_purchase_vnd = target_sale_vnd - calc_profit_vnd - shipping_fee_vnd - maintenance_fee_vnd
    if max_purchase_vnd < 0:
        max_purchase_vnd = 0
        max_bid_jpy = 0
    else:
        max_bid_jpy = round(max_purchase_vnd / rate)

    return {
        "target_sale_vnd": target_sale_vnd,
        "profit_vnd": calc_profit_vnd,
        "profit_label": profit_label,
        "shipping_fee_vnd": shipping_fee_vnd,
        "maintenance_fee_vnd": maintenance_fee_vnd,
        "max_purchase_vnd": max_purchase_vnd,
        "max_bid_jpy": max_bid_jpy,
        "rate": rate,
    }


def get_condition_price_matrix(base_price_jpy: int, primary_currency: str = "JPY") -> list[dict[str, Any]]:
    """Tạo bảng mốc giá bid khuyến nghị theo 4 cấp độ tình trạng quẹt thực tế."""
    curr = (primary_currency or "JPY").upper()

    levels = [
        ("🌟 Hàng Keng / Like new / Full box", 1.05, "Đẹp xuất sắc, có hộp zin, giữ giá tốt nhất"),
        ("👌 Hàng Lướt / Xước nhẹ / Có hộp", 0.85, "Đã qua sử dụng, xước dăm nhẹ, hoạt động tốt"),
        ("⚠️ Cấn góc / Mất hộp / Trầy nhiều", 0.65, "Ngoại hình xấu, trầy xước cấn móp, thiếu phụ kiện"),
        ("🔧 Junk / Xác / Hư van / Lấy vỏ", 0.40, "Xác quẹt, xì gas, kẹt đá, mua về lấy linh kiện/sửa"),
    ]

    matrix = []
    for label, factor, note in levels:
        lvl_price = round(base_price_jpy * factor)
        lvl_text = format_currency_amount(lvl_price, curr, with_approx=True)
        matrix.append({
            "label": label,
            "factor": factor,
            "price": lvl_price,
            "price_text": lvl_text,
            "note": note,
        })
    return matrix


def estimate_market_valuation(
    title: str,
    description: str = "",
    current_price_jpy: int | None = None,
    shipping_fee_jpy: int | None = None,
    is_lot: bool = False,
    lot_count: int | None = None,
    condition_vn: str = "",
    rate: int = 165,
) -> dict[str, Any]:
    """Phân tích chuyên sâu định giá thị trường: mua bao nhiêu hợp lý, bán lại được bao nhiêu tại VN, P&L và chiến lược khai thác."""
    from normalizer import strip_vietnamese_accents
    full_text = strip_vietnamese_accents(f"{title} {description}").lower()

    count = lot_count or 1
    p_jpy = current_price_jpy or (7000 if is_lot else 10000)
    ship_j_jpy = shipping_fee_jpy if shipping_fee_jpy is not None else 1080

    # 1. Nhận diện Archetype & Phân khúc thị trường
    if is_lot and count >= 2:
        archetype = "bulk_lot"
        category_name = f"Lô {count} Cây Bật Lửa Nhật Bãi"
        liquidity = "Cao (Rất dễ bán sỉ hoặc thanh lý thợ lẻ tại VN)"

        target_buy_jpy_min = round(count * 350)
        target_buy_jpy_max = round(count * 600)
        max_bid_jpy = round(count * 750)

        live_count = max(1, round(count * 0.45))
        parts_count = count - live_count

        resale_details = [
            f"• <b>Dọn sống bán lẻ ({live_count} cây):</b> ~180.000 - 300.000 đ/cây ➔ Thu ~{live_count * 240000:,} đ".replace(",", "."),
            f"• <b>Bán xác thợ rã phụ tùng ({parts_count} cây):</b> ~60.000 - 100.000 đ/cây ➔ Thu ~{parts_count * 80000:,} đ".replace(",", "."),
            f"• <i>(Hoặc bán sỉ sang tay cả lô cho thợ khác tại VN: ~{count * 135000:,} đ)</i>".replace(",", "."),
        ]
        expected_revenue_vnd = (live_count * 240000) + (parts_count * 80000)

        ship_intl_vnd = count * 20000
        maint_vnd = live_count * 30000
        action_plan = (
            f"1. Nhận hàng về, chọn ra {live_count} cây đẹp nhất dọn lửa (thay ron/đá) bán lẻ 200k - 300k/cây.\n"
            f"2. {parts_count} cây còn lại bán combo xác cho thợ hoặc rã linh kiện (bánh xe, ty van, ron) trữ kho.\n"
            f"3. Hoặc nếu muốn thu tiền nhanh: sang tay nguyên lô cho thợ với giá ~{count * 135000:,} đ (vẫn có lãi ~20-30%).".replace(",", ".")
        )

    elif any(b in full_text for b in ["dupont", "s.t. dupont", "st dupont", "ligne 1", "ligne 2", "line 1", "line 2", "gatsby"]) or "デュポン" in f"{title} {description}":
        archetype = "dupont"
        is_l2 = any(l in full_text for l in ["line 2", "ligne 2", "l2", "2 line"]) or "ライン2" in f"{title} {description}"
        if is_l2:
            category_name = "Dupont Line 2 (Phân Khúc Cao Cấp / Âm Chuông)"
            liquidity = "Cực cao (Giữ giá số 1 tại VN, săn đón rất mạnh)"
            target_buy_jpy_min = 18000
            target_buy_jpy_max = 26000
            max_bid_jpy = 32000
            resale_details = [
                "• <b>Hàng Keng / Chuông hay:</b> ~7.500.000 - 10.500.000 đ",
                "• <b>Hàng Lướt / Đẹp:</b> ~5.500.000 - 7.000.000 đ",
                "• <b>Hàng xước / bán thợ:</b> ~3.500.000 - 4.500.000 đ",
            ]
            expected_revenue_vnd = 6500000
        else:
            category_name = "Dupont Line 1 / Gatsby (Phân Khúc Sang Trọng Cổ Điển)"
            liquidity = "Rất cao (Thanh khoản nhanh trong 2 - 5 ngày)"
            target_buy_jpy_min = 8500
            target_buy_jpy_max = 12500
            max_bid_jpy = 14500
            resale_details = [
                "• <b>Hàng Keng / Fullbox:</b> ~3.800.000 - 5.200.000 đ",
                "• <b>Hàng Lướt / Sơn mài đẹp:</b> ~2.800.000 - 3.800.000 đ",
                "• <b>Cũ / xì gas / bán thợ:</b> ~1.500.000 - 2.200.000 đ",
            ]
            expected_revenue_vnd = 3400000

        ship_intl_vnd = 200000
        maint_vnd = 200000
        action_plan = (
            "1. Kiểm tra ty van và buồng gas, thay bộ ron chống xì Dupont (~150k).\n"
            "2. Vệ sinh bánh xe, tra đá chính hãng để tia lửa bén ngọt.\n"
            "3. Quay video quẹt lên lửa + test tiếng chuông 'Clink' đăng lên hội nhóm quẹt cổ là chốt đơn rất nhanh."
        )

    elif any(b in full_text for b in ["dunhill", "rollagas"]) or "ダンヒル" in f"{title} {description}":
        archetype = "dunhill"
        category_name = "Dunhill Rollagas (Phân Khúc Doanh Nhân / Tẩu & Xì Gà)"
        liquidity = "Cao (Dòng bán chạy quanh năm tại thị trường VN)"
        target_buy_jpy_min = 5000
        target_buy_jpy_max = 7500
        max_bid_jpy = 9000
        resale_details = [
            "• <b>Đẹp / Giữ gas tốt:</b> ~2.400.000 - 3.200.000 đ",
            "• <b>Lướt / Xước nhẹ vỏ:</b> ~1.800.000 - 2.400.000 đ",
            "• <b>Xì gas / Bán thợ:</b> ~900.000 - 1.300.000 đ",
        ]
        expected_revenue_vnd = 2300000
        ship_intl_vnd = 200000
        maint_vnd = 150000
        action_plan = (
            "1. Thay bộ gioăng đáy và van trên Dunhill Rollagas (~100k) để bảo đảm giữ gas 100%.\n"
            "2. Đánh bóng nhẹ lớp mạ bạc / vàng để nâng vẻ ngoài lên chuẩn công sở.\n"
            "3. Hướng tới đối tượng khách hút xì gà, tẩu hoặc làm quà tặng."
        )

    elif any(b in full_text for b in ["zippo", "sterling", "replica"]) or any(z in f"{title} {description}" for z in ["ジッポー", "ジッポ"]):
        archetype = "zippo"
        is_silver = any(m in full_text for m in ["sterling", "925", "bac khoi"]) or "スターリング" in f"{title} {description}"
        if is_silver:
            category_name = "Zippo Bạc Khối Sterling 925 (Sưu Tầm Cao Cấp)"
            liquidity = "Cực cao (Bạc khối không bao giờ rớt giá, thanh khoản 24h)"
            target_buy_jpy_min = 14000
            target_buy_jpy_max = 19000
            max_bid_jpy = 22000
            resale_details = [
                "• <b>Fullbox / Đẹp:</b> ~4.500.000 - 6.000.000 đ",
                "• <b>Lướt / Trùng ruột vỏ:</b> ~3.600.000 - 4.500.000 đ",
            ]
            expected_revenue_vnd = 4500000
        else:
            category_name = "Zippo La Mã / Replica / Cổ Điển"
            liquidity = "Cực cao (Cộng đồng người chơi đông nhất VN)"
            target_buy_jpy_min = 2500
            target_buy_jpy_max = 4500
            max_bid_jpy = 5500
            resale_details = [
                "• <b>Cây đẹp / Mộc đáy rõ:</b> ~1.200.000 - 1.800.000 đ",
                "• <b>Hàng xài / Xước dăm:</b> ~800.000 - 1.200.000 đ",
            ]
            expected_revenue_vnd = 1300000

        ship_intl_vnd = 150000
        maint_vnd = 50000
        action_plan = (
            "1. Vệ sinh buồng đốt, thay bấc và đá xịn Zippo.\n"
            "2. Chụp rõ mộc đáy, bản lề và ruột zippo để chứng minh độ zin.\n"
            "3. Đăng bán trên các hội Zippo Việt Nam thường chốt rất nhanh trong ngày."
        )

    elif any(b in full_text for b in ["ronson", "banjo", "varaflame"]) or "ロンソン" in f"{title} {description}":
        archetype = "ronson"
        category_name = "Ronson (Banjo / Varaflame Cổ Điển)"
        liquidity = "Khá cao (Được ưa chuộng vì cơ chế độc lạ)"
        target_buy_jpy_min = 2500
        target_buy_jpy_max = 4500
        max_bid_jpy = 5500
        resale_details = [
            "• <b>Đã dọn lửa / Bén:</b> ~1.300.000 - 2.000.000 đ",
            "• <b>Hàng xác / Kẹt cơ:</b> ~600.000 - 900.000 đ",
        ]
        expected_revenue_vnd = 1500000
        ship_intl_vnd = 150000
        maint_vnd = 100000
        action_plan = (
            "1. Dọn sạch bụi buồng búa gõ, bôi trơn bánh răng cơ chế bấm nhả.\n"
            "2. Với dòng Varaflame: chú ý van nạp gas Ronson thường cần thay ron nắp đáy."
        )

    else:
        archetype = "generic_single"
        category_name = "Bật Lửa Nhật Bãi / Thương Hiệu Khác"
        liquidity = "Trung bình (Dành cho người chơi phổ thông)"
        target_buy_jpy_min = 1500
        target_buy_jpy_max = 3000
        max_bid_jpy = 3800
        resale_details = [
            "• <b>Lên lửa tốt / Đẹp:</b> ~600.000 - 1.000.000 đ",
            "• <b>Bán xác / Thợ:</b> ~250.000 - 400.000 đ",
        ]
        expected_revenue_vnd = 750000
        ship_intl_vnd = 150000
        maint_vnd = 80000
        action_plan = "Vệ sinh sạch sẽ, châm gas/xăng thử lửa rồi bán lẻ cho người mới chơi hoặc dùng hàng ngày."

    # 2. Tính toán P&L
    purchase_vnd = round(p_jpy * rate)
    ship_japan_vnd = round(ship_j_jpy * rate)
    all_in_cost_vnd = purchase_vnd + ship_japan_vnd + ship_intl_vnd + maint_vnd

    expected_net_profit_vnd = expected_revenue_vnd - all_in_cost_vnd
    roi_percent = round((expected_net_profit_vnd / all_in_cost_vnd) * 100, 1) if all_in_cost_vnd > 0 else 0

    return {
        "archetype": archetype,
        "category_name": category_name,
        "liquidity": liquidity,
        "target_buy_jpy_min": target_buy_jpy_min,
        "target_buy_jpy_max": target_buy_jpy_max,
        "target_buy_vnd_min": round(target_buy_jpy_min * rate),
        "target_buy_vnd_max": round(target_buy_jpy_max * rate),
        "max_bid_jpy": max_bid_jpy,
        "max_bid_vnd": round(max_bid_jpy * rate),
        "resale_details": resale_details,
        "expected_revenue_vnd": expected_revenue_vnd,
        "current_price_jpy": p_jpy,
        "shipping_fee_jpy": ship_j_jpy,
        "purchase_vnd": purchase_vnd,
        "ship_japan_vnd": ship_japan_vnd,
        "ship_intl_vnd": ship_intl_vnd,
        "maint_vnd": maint_vnd,
        "all_in_cost_vnd": all_in_cost_vnd,
        "expected_net_profit_vnd": expected_net_profit_vnd,
        "roi_percent": roi_percent,
        "action_plan": action_plan,
        "count": count,
    }


def format_market_valuation_report(val: dict[str, Any]) -> str:
    """Định dạng báo cáo phân tích chuyên sâu thị trường, định giá mua/bán và chiến lược."""
    t_min_fmt = f"{val['target_buy_jpy_min']:,}".replace(",", ".")
    t_max_fmt = f"{val['target_buy_jpy_max']:,}".replace(",", ".")
    t_vnd_min = f"{val['target_buy_vnd_min']:,}".replace(",", ".")
    t_vnd_max = f"{val['target_buy_vnd_max']:,}".replace(",", ".")
    max_bid_fmt = f"{val['max_bid_jpy']:,}".replace(",", ".")
    max_bid_vnd = f"{val['max_bid_vnd']:,}".replace(",", ".")

    rev_fmt = f"{val['expected_revenue_vnd']:,}".replace(",", ".")
    cost_fmt = f"{val['all_in_cost_vnd']:,}".replace(",", ".")
    profit_fmt = f"{val['expected_net_profit_vnd']:,}".replace(",", ".")

    profit_icon = "💵" if val["expected_net_profit_vnd"] >= 0 else "⚠️"
    profit_sign = "+" if val["expected_net_profit_vnd"] >= 0 else ""

    lines = [
        "📊 <b>TỔNG QUAN ĐỊNH GIÁ THỊ TRƯỜNG & KHẢ NĂNG SINH LỜI</b>",
        f"🏷️ <b>Phân khúc:</b> {val['category_name']}",
        f"⚡ <b>Thanh khoản tại VN:</b> {val['liquidity']}",
        "━━━━━━━━━━━━━━━━━━━━━",
        "🎯 <b>1. MUA BAO NHIÊU LÀ HỢP LÝ TRÊN SÀN YAHOO?</b>",
        f"• Vùng giá gom hời: <b>{t_min_fmt} - {t_max_fmt} yên</b> (~{t_vnd_min} - {t_vnd_max} đ)",
        f"• Mốc trần tối đa nên dừng: <b>{max_bid_fmt} yên</b> (~{max_bid_vnd} đ)",
        "<i>(Nếu sàn vượt quá mốc này ➔ Dừng lại để bảo toàn lãi!)</i>\n",
        "💰 <b>2. CÓ THỂ BÁN LẠI BAO NHIÊU TẠI VIỆT NAM?</b>",
    ]
    for d in val["resale_details"]:
        lines.append(d)
    lines.append(f"👉 <b>Tổng doanh thu bán ra ước tính:</b> <b>~{rev_fmt} đ</b>\n")

    lines.append("🧮 <b>3. TỔNG QUAN ĐẦU TƯ & DỰ TÍNH LÃI RÒNG:</b>")
    lines.append(f"• Tổng vốn về tay (All-in gồm ship & bảo dưỡng): <b>~{cost_fmt} đ</b>")
    lines.append(f"{profit_icon} <b>Lợi nhuận ròng dự kiến:</b> <b>{profit_sign}{profit_fmt} đ</b>")
    lines.append(f"📈 <b>Tỷ suất sinh lời (ROI):</b> <b>{profit_sign}{val['roi_percent']}%</b>\n")

    lines.append("💡 <b>4. CHIẾN LƯỢC KHAI THÁC TỐI ƯU:</b>")
    lines.append(val["action_plan"])

    return "\n".join(lines)


def format_financial_pnl_report(val: dict[str, Any]) -> str:
    """Bảng chi tiết các khoản chi phí đầu tư và phân tích điểm hòa vốn."""
    pur_fmt = f"{val['purchase_vnd']:,}".replace(",", ".")
    ship_j_fmt = f"{val['ship_japan_vnd']:,}".replace(",", ".")
    ship_vn_fmt = f"{val['ship_intl_vnd']:,}".replace(",", ".")
    maint_fmt = f"{val['maint_vnd']:,}".replace(",", ".")
    all_in_fmt = f"{val['all_in_cost_vnd']:,}".replace(",", ".")
    rev_fmt = f"{val['expected_revenue_vnd']:,}".replace(",", ".")
    profit_fmt = f"{val['expected_net_profit_vnd']:,}".replace(",", ".")

    profit_sign = "+" if val["expected_net_profit_vnd"] >= 0 else ""

    lines = [
        "💰 <b>BẢNG CHI TIẾT CHI PHÍ ĐẦU TƯ & P&L TOÀN DIỆN</b>",
        f"📦 <b>Mục tiêu:</b> {val['category_name']}",
        "━━━━━━━━━━━━━━━━━━━━━",
        "<b>CÁC KHOẢN CHI PHÍ VỐN (ALL-IN COST):</b>",
        f"1. Tiền mua trên sàn Yahoo ({val['current_price_jpy']:,}Y): <b>{pur_fmt} đ</b>".replace(",", "."),
        f"2. Phí ship nội địa Nhật ({val['shipping_fee_jpy']:,}Y): <b>+{ship_j_fmt} đ</b>".replace(",", "."),
        f"3. Cước vận chuyển Nhật - VN & kho: <b>+{ship_vn_fmt} đ</b>",
        f"4. Phí bảo dưỡng, ron, xăng đá dự kiến: <b>+{maint_fmt} đ</b>",
        "─────────────────────",
        f"👉 <b>TỔNG VỐN ĐẦU TƯ THỰC TẾ:</b> <b>~{all_in_fmt} đ</b>\n",
        "<b>DỰ TÍNH DOANH THU & HIỆU QUẢ:</b>",
        f"• Tổng doanh thu kỳ vọng tại VN: <b>~{rev_fmt} đ</b>",
        f"• Lợi nhuận ròng thực tế: <b>{profit_sign}{profit_fmt} đ</b>",
        f"• Tỷ suất lợi nhuận trên vốn (ROI): <b>{profit_sign}{val['roi_percent']}%</b>",
        f"• Điểm hòa vốn: Doanh thu chỉ cần đạt trên <b>{all_in_fmt} đ</b> là bắt đầu có lãi!",
    ]
    return "\n".join(lines)

