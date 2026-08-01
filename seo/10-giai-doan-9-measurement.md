# 10. Giai Đoạn 9 — Đo Lường

> Đo đúng → biết đang thắng hay thua thật. Đo sai → tự thấy thất bại dù đang thắng.

---

## Giới hạn thực tế cần biết trước

> Biết giới hạn để không hứa hẹn sai với team/client.

```
❌ Search Console KHÔNG tách click riêng cho AI Overview
   → Impression và click AI gộp vào tổng — không thể báo "X click từ AI Overview"

❌ Không có công cụ Google chính thức đo "được trích dẫn trong AI hay không"
   → Phải test thủ công + dùng tracker bên thứ 3

✅ Có thể đo: 
   → AI Overview có xuất hiện với query X không?
   → Brand có được nhắc trong câu trả lời AI không?
   → URL nào được dẫn?
   → So với đối thủ, share of voice thế nào?
```

---

## Bộ test thủ công (30–50 câu)

### Quy trình test

**Điều kiện test phải cố định:**

```
- Quốc gia: Việt Nam (dùng VPN nếu cần)
- Ngôn ngữ: Tiếng Việt
- Thiết bị: Desktop Chrome (test riêng mobile nếu cần)
- Trạng thái: Ẩn danh / không đăng nhập
- Thời điểm: Cùng giờ mỗi tháng (VD: 9AM ngày 1 mỗi tháng)
```

> **Lý do cố định điều kiện:** Kết quả AI thay đổi theo người dùng, vị trí, lịch sử. Không cố định → so sánh tháng này với tháng kia không có giá trị.

### Bảng ghi kết quả test

| # | Câu hỏi | AI Overview xuất hiện? | Brand được nhắc? | URL được dẫn | Đối thủ được dẫn | Ghi chú |
|---|---------|----------------------|-----------------|-------------|-----------------|---------|
| 1 | | Y / N | Y / N | | | |
| 2 | | Y / N | Y / N | | | |

**Tần suất:** Hàng tháng, cùng điều kiện.

### Cách test nhanh hơn
```
Dùng Incognito mode → tìm từng câu → screenshot → ghi kết quả
Có thể dùng extension ghi màn hình để review lại
Công cụ bên thứ 3: Authoritas, SE Ranking AI tracker (trả phí)
```

---

## KPI 2 tầng (bắt buộc đo đủ cả 2)

### Tầng 1 — Hiện diện AI (AI Presence)

> Đây là KPI đặc thù, không thay thế được bằng KPI traffic.

| KPI | Cách đo | Tần suất |
|-----|---------|---------|
| Số câu test có brand xuất hiện / tổng câu test | Bộ test thủ công 30–50 câu | Hàng tháng |
| Tỷ lệ trích dẫn vs đối thủ (share of voice AI) | Bộ test + đếm lần đối thủ được dẫn | Hàng tháng |
| Số trang có AI impression | Search Console (gộp, không tách được) | Hàng tháng |
| Tổng AI impression | Search Console | Hàng tháng |

### Tầng 2 — Kinh doanh (Business Outcome)

> Đây là KPI cuối — vì click hữu cơ có thể giảm mà kinh doanh vẫn tăng.

| KPI | Cách đo | Tần suất |
|-----|---------|---------|
| Branded search volume | Google Search Console (query "brand") / Google Trends | Hàng tháng |
| Direct traffic | Google Analytics 4 | Hàng tháng |
| Organic conversion (form/gọi/đơn) | GA4 → Goals/Conversions | Hàng tháng |
| Assisted conversion | GA4 → Conversion paths | Hàng quý |
| Doanh thu từ organic | GA4 → Ecommerce | Hàng tháng |

### Cách đọc kết quả

```
Scenario A: Traffic giảm + Brand search tăng + Conversion tăng
→ Đang thắng (zero-click effect, AI đang giới thiệu brand)

Scenario B: Traffic giảm + Brand search giảm + Conversion giảm
→ Đang thua thật sự → cần review lại chiến lược

Scenario C: Traffic tăng + Brand không đổi + Conversion không đổi
→ Traffic tốt nhưng chưa tác động brand (cần cải thiện extractability)
```

---

## Dashboard báo cáo hàng tháng

### Cấu trúc báo cáo (xem template tại `templates/monthly-report.md`)

```
1. Executive Summary (3–5 bullet points)
2. Tầng 1 — Hiện diện AI
   - Kết quả bộ test 30–50 câu (tháng này vs tháng trước)
   - Ví dụ câu AI đang trích brand (chụp màn hình)
   - Ví dụ câu AI đang trích đối thủ (chụp màn hình)
3. Tầng 2 — Kinh doanh
   - Branded search volume
   - Organic traffic + conversion
   - Doanh thu organic
4. Technical health
   - Index status
   - Core Web Vitals
   - Schema errors
5. Actions taken tháng này
6. Actions planned tháng tới
7. Open issues
```

---

## Công cụ đo lường

| Công cụ | Miễn phí | Dùng cho |
|---------|---------|---------|
| Google Search Console | ✅ | Index, impressions, clicks, queries |
| Google Analytics 4 | ✅ | Traffic, conversions, revenue |
| Google Trends | ✅ | Branded search trends |
| PageSpeed Insights | ✅ | Core Web Vitals |
| Rich Results Test | ✅ | Schema validation |
| Google Alerts | ✅ | Brand mentions |
| Screaming Frog (free up to 500 URLs) | Freemium | Technical audit |
| SE Ranking / Ahrefs / Semrush | 💰 | Rank tracking, AI tracking, backlinks |
| Authoritas | 💰 | AI Overview tracking chuyên biệt |

---

## Checklist Đo lường

- [ ] Bộ test 30–50 câu đã thiết lập
- [ ] Quy trình test tháng đầu đã chạy (baseline)
- [ ] GA4 đã setup goals/conversions
- [ ] Search Console connected + verified
- [ ] Branded query filter đã tạo trong Search Console
- [ ] Template báo cáo hàng tháng đã dùng
- [ ] KPI 2 tầng đã chia sẻ với team/client + được đồng thuận
- [ ] Lịch báo cáo tháng đã gắn vào calendar
