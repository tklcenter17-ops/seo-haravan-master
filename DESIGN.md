# HAMACO Design DNA & Design System (DESIGN.md)

Tài liệu định hình chuẩn thiết kế UI/UX theo kỹ năng `taste-design`, `ui-ux-promax`, `ui-styling` và nguyên tắc tinh gọn `ponytail`.

---

## 1. Triết Lý Thiết Kế Cốt Lõi (Design Philosophy)

* **Phong cách chủ đạo:** *Corporate Solid & Warm Mekong Heritage* (Bề thế, điềm đạm, ấm áp, sâu lắng và chân thực).
* **Đặc trưng thị giác:**
  - Tôn vinh nền tảng sản xuất và phân phối thực tế từ năm 1976 tại miền Tây Nam Bộ (Cần Thơ, Hậu Giang và ĐBSCL).
  - Không lạm dụng hiệu ứng bóng bẩy, không gradient lòe loẹt, không scroll-jacking.
  - Sử dụng đường viền siêu mảnh (`1px solid var(--hamaco-border)`), bóng đổ siêu nhẹ (`0 2px 8px rgba(16, 42, 76, 0.05)`).
  - Hệ thống lưới thoáng đãng (Whitespace), phân cấp thông tin rõ ràng theo chuẩn Bento Grid cho các khối dữ liệu trọng tâm.

---

## 2. Bảng Màu Thiết Kế (Color Tokens)

| Tên Token | Mã Hex / HSL | Mục đích sử dụng | Tiêu chuẩn WCAG AA |
| :--- | :--- | :--- | :--- |
| `--hamaco-navy` | `#1B3A6B` | Màu chủ đạo: Header, tiêu đề lớn H1/H2, card điểm nhấn, footer | Đạt tương phản 8.6:1 trên nền trắng/cream |
| `--hamaco-deep-navy` | `#102A4C` | Nền thanh điều hướng tối, IR Hub header, banner uy tín | Đạt tương phản 11.2:1 |
| `--hamaco-orange` | `#F5A623` | Màu nhấn hành động (CTA chính, active tab, hover link, dot mốc) | Sử dụng có kiểm soát, không làm nền toàn trang |
| `--hamaco-orange-dark`| `#C77B00` | Trạng thái hover/active của CTA màu cam | Đạt tương phản nút bấm |
| `--hamaco-cream` | `#FAF9F6` | Nền phụ, nền section xen kẽ, giảm độ chói của màu trắng tinh | Mang lại cảm giác ấm áp |
| `--hamaco-warm-gray` | `#F1F0EC` | Nền card kỹ thuật, bảng dữ liệu, khối thông số | Giữ nhịp thị giác ổn định |
| `--hamaco-border` | `#D9D8D2` | Đường kẻ phân cách, viền input, viền card | Tinh tế, không gây nhiễu giao diện |
| `--hamaco-text` | `#1D2733` | Màu chữ chính (Body text, nhãn thông tin) | Đạt tương phản 13.5:1 |
| `--hamaco-muted` | `#667085` | Màu chữ phụ, chú thích, ngày tháng, metadata | Đạt tương phản 4.8:1 |
| `--hamaco-white` | `#FFFFFF` | Nền thẻ chính, màu chữ trên nền Navy | Tuyệt đối trong trẻo |
| `--hamaco-success` | `#2F7D5B` | Trạng thái tích cực, tăng trưởng chỉ số, chứng nhận CQ | Chuẩn tin cậy |
| `--hamaco-danger` | `#B54747` | Cảnh báo, thông báo lỗi trường nhập liệu | Rõ ràng, hỗ trợ accessibility |

---

## 3. Hệ Thống Typography & Phân Cấp Văn Bản

* **Font gia đình:** `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif`
* **Quy chuẩn hiển thị:**
  - `Display / H1`: 40px – 56px (Desktop), 32px – 38px (Mobile), Weight: 700, Line-height: 1.2
  - `Section Title / H2`: 28px – 36px (Desktop), 24px – 28px (Mobile), Weight: 600, Line-height: 1.3
  - `Sub-heading / H3`: 20px – 24px, Weight: 600, Line-height: 1.4
  - `Body Regular`: 16px (Desktop) / 15px (Mobile), Weight: 400, Line-height: 1.65
  - `Body Small / Metadata`: 13px – 14px, Weight: 400 - 500, Line-height: 1.5
  - `Stat Number`: 36px – 48px, Weight: 700, Tabular nums (chống nhảy số)

---

## 4. Spacing & Grid System (Hệ số 8px)

* **Spacing Tokens:**
  - `4px` (`--space-1`), `8px` (`--space-2`), `12px` (`--space-3`), `16px` (`--space-4`), `24px` (`--space-6`), `32px` (`--space-8`), `48px` (`--space-12`), `64px` (`--space-16`), `80px` (`--space-20`)
* **Container Width:**
  - Max-width: `1240px` (có padding 24px ở desktop, 16px ở mobile)
* **Breakpoints chuẩn:**
  - Mobile nhỏ: `320px - 479px`
  - Mobile lớn: `480px - 767px`
  - Tablet: `768px - 1023px`
  - Laptop: `1024px - 1279px`
  - Desktop / Wide: `>= 1280px`

---

## 5. Quy Tắc Bo Góc & Hiệu Ứng (Borders & Radius)

* **Border Radius:**
  - Nút bấm, input, badge: `6px - 8px` (gọn gàng, chuyên nghiệp)
  - Card, panel thông tin: `10px - 12px`
  - Modal, drawer lớn: `12px - 16px`
* **Shadows:**
  - Soft Card: `0 2px 8px rgba(16, 42, 76, 0.05)`
  - Hover Card: `0 8px 24px rgba(16, 42, 76, 0.09)`
  - Dropdown / Modal: `0 12px 36px rgba(16, 42, 76, 0.16)`

---

## 6. Tiêu Chuẩn Icon & Tương Tác (Icons & Interactions)

* **Icon:** Tuyệt đối không dùng Emoji làm biểu tượng giao diện. Dùng Inline SVG chuẩn (dựa trên Lucide Icons) với `stroke-width="1.75"` hoặc `"2"`.
* **Touch Target:** Tất cả nút bấm, link điều hướng và ô chọn trên thiết bị cảm ứng tối thiểu `44px x 44px`.
* **Focus States:** Luôn có viền focus ring rõ nét (`outline: 2px solid var(--hamaco-orange); outline-offset: 2px;`) hỗ trợ điều hướng bàn phím (Keyboard Accessibility).
