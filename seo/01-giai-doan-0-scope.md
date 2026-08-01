# 01. Giai Đoạn 0 — Xác Định Phạm Vi & Chốt Baseline

> Plan gốc để phần này ở kết luận. Nó phải nằm đầu tiên vì **mọi giai đoạn sau đều phụ thuộc vào đây**.

---

## 1. Domain & thị trường mục tiêu

```
Domain:          [điền domain chính thức]
Ngôn ngữ:        vi-VN
Khu vực:         Việt Nam
Ngành:           [điền ngành]
Segment:         [B2C / B2B / Local Business]
```

> **Lưu ý:** AI Overviews tại VN triển khai chậm hơn thị trường tiếng Anh.  
> Nếu chưa thấy AI Overview xuất hiện khi tìm kiếm → có thể do rollout chứ không phải lỗi site.  
> Tự kiểm tra: mở Google.com.vn, bật VPN nếu cần, tìm câu hỏi ngành xem AI Overview có hiện không.

---

## 2. Danh sách đối thủ (3–5 đơn vị)

| # | Đối thủ | Domain | Ghi chú |
|---|---------|--------|---------|
| 1 | | | Đối thủ trực tiếp |
| 2 | | | Đối thủ trực tiếp |
| 3 | | | Đối thủ trực tiếp |
| 4 | | | **Đang được AI trích dẫn** (có thể khác đối thủ trực tiếp) |
| 5 | | | **Đang được AI trích dẫn** |

> **Cách tìm đối thủ AI:** Tìm 10–15 câu hỏi ngành trên Google → xem AI Overview đang dẫn URL nào → đó là đối thủ AI thực sự (không nhất thiết là đối thủ kinh doanh).

---

## 3. Baseline Search Console (xuất trước ngày bắt đầu)

### Cách xuất
1. Vào [Google Search Console](https://search.google.com/search-console)
2. **Performance** → **Search results**
3. Đặt khoảng thời gian: **12 tháng**
4. Export ra Google Sheets / CSV

### Các cột cần giữ

| Cột | Mục đích |
|-----|---------|
| Query | Xem người dùng đang hỏi gì |
| Page | Trang nào đang được hiển thị |
| Clicks | Lưu lượng thực |
| Impressions | Độ phủ |
| CTR | Click-through rate — nếu thấp mà impression cao → cần cải thiện title/meta |
| Position | Vị trí trung bình |

### Lọc để tìm cơ hội nhanh

```
Filter: Query chứa từ hỏi (cách, là gì, nên, có không, tại sao, bao nhiêu, ở đâu)
→ Đây là câu hỏi — ứng viên cho AI Overview content

Filter: Impressions cao + Position > 10 + CTR thấp
→ Trang tiềm năng cần cải thiện
```

### File baseline cần lưu

- [ ] `seo/data/baseline-search-console-YYYYMM.csv`
- [ ] `seo/data/baseline-analytics-YYYYMM.csv` (organic traffic, branded vs non-branded)
- [ ] Screenshot: branded search volume hiện tại (Google Trends hoặc Keyword Planner)

---

## 4. Phân công Owner (bắt buộc)

> "Ai cũng làm hóa ra không ai làm." — Mỗi mảng phải có **đúng 1 người chịu trách nhiệm**.

| Mảng | Owner | Liên hệ | Ghi chú |
|------|-------|---------|---------|
| **Technical SEO** (crawl, index, speed, schema) | | | |
| **Nội dung** (viết, cập nhật, review) | | | |
| **Entity / Brand** (tác giả, schema org, Wikipedia) | | | |
| **Off-site** (PR, forum, UGC, link building) | | | |
| **Đo lường** (báo cáo, test AI, tracking) | | | |

---

## 5. Định nghĩa "thành công" bằng số cụ thể

> Phải chốt **trước khi bắt đầu** — không chốt sau khi xem kết quả.

### Ví dụ mẫu (điều chỉnh theo mục tiêu thực tế):

| KPI | Baseline hiện tại | Mục tiêu 3 tháng | Mục tiêu 6 tháng |
|-----|------------------|-----------------|-----------------|
| Brand xuất hiện trong AI (/ 50 câu test) | ___ / 50 | 15 / 50 | 25 / 50 |
| Branded search volume | ___ / tháng | +20% | +40% |
| Organic impressions | ___ / tháng | +30% | +60% |
| Conversion từ organic | ___ / tháng | +15% | +30% |
| Số trang được index | ___ | ___ | ___ |

> **Quy tắc KPI:** Nếu chỉ đo traffic → sẽ bị đánh giá sai. Phải có ít nhất 1 KPI brand và 1 KPI conversion trong bộ đo.

---

## Checklist Giai đoạn 0

- [ ] Chốt domain + ngôn ngữ + thị trường
- [ ] Xác nhận AI Overviews đã rollout cho vi-VN chưa
- [ ] Liệt kê 3–5 đối thủ trực tiếp
- [ ] Test 10–15 câu hỏi ngành → xác định đối thủ AI
- [ ] Xuất Search Console 12 tháng → lưu file baseline
- [ ] Xuất Google Analytics baseline (branded vs organic)
- [ ] Điền bảng Owner đầy đủ
- [ ] Chốt bảng KPI với số cụ thể
- [ ] Gửi/đồng thuận KPI với team/client trước khi bắt đầu
