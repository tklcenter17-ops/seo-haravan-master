# 11. Lộ Trình 8 Tuần

> Timeline điều chỉnh cho khớp thực tế — không ép task cần thời gian thu thập data vào tuần ngắn.  
> **Nguyên tắc quan trọng:** Case study và tín hiệu off-site là việc liên tục nhiều tháng, không phải task tick trong 8 tuần.

---

## Tổng quan 8 tuần

```
Tuần 1  → Foundation: Scope + Kỹ thuật + Rendering
Tuần 2  → Intelligence: Câu hỏi + Fan-out + Đối thủ AI
Tuần 3  → Architecture: Topic cluster + Internal link + Template | Song song: Xin data/quote khách
Tuần 4–6 → Content: Viết 8–15 nội dung (ưu tiên có data sẵn)
Tuần 6  → Entity: Tác giả + Schema + GBP + Merchant Center
Tuần 7–8 → Amplify: Case study + Off-site | Test AI đầu tiên + Lập baseline đo lường
Tuần 8  → Launch: Request index + Baseline chính thức
```

---

## Chi tiết từng tuần

### 📅 Tuần 1 — Foundation
**Giai đoạn 0 + Audit kỹ thuật + Rendering**

**Ưu tiên:**
- [ ] Điền đầy đủ `01-giai-doan-0-scope.md` (domain, owner, KPI)
- [ ] Xuất Search Console 12 tháng → lưu baseline
- [ ] Audit kỹ thuật theo `checklists/technical-audit.md`
- [ ] Đặc biệt: URL Inspection → View Tested Page HTML cho 10 trang quan trọng nhất
- [ ] Fix ngay các lỗi kỹ thuật nghiêm trọng (noindex sai, render hỏng)

**Deliverable:** Báo cáo audit kỹ thuật + danh sách fix theo mức độ ưu tiên

**Owner:** Technical SEO

---

### 📅 Tuần 2 — Intelligence
**Câu hỏi + Fan-out + Phân tích đối thủ AI**

**Ưu tiên:**
- [ ] Khai thác câu hỏi từ: Search Console + Google PAA + Autocomplete + Chat log
- [ ] Test 15–20 câu hỏi ngành trên Google → xem đối thủ AI
- [ ] Điền bảng đối thủ trong `01-giai-doan-0-scope.md`
- [ ] Tạo file câu hỏi theo format `templates/question-matrix.md`
- [ ] Chấm điểm ưu tiên, xác định top 10 câu làm trước

**Deliverable:** File câu hỏi 30–50 câu, top 10 đã ưu tiên

**Owner:** Nội dung + đo lường

---

### 📅 Tuần 3 — Architecture
**Topic cluster + Internal link + Template | Song song: Xin data/quote**

**Ưu tiên:**
- [ ] Vẽ topic cluster map (trang trụ cột → trang con)
- [ ] Lập internal linking plan
- [ ] Điền `templates/content-brief.md` cho top 5 trang
- [ ] **[Song song]** Liên hệ 5–10 khách hàng tốt nhất xin quote/data cho case study
- [ ] **[Song song]** Bắt đầu khai thác data nội bộ (đơn hàng, review, log chat)

**Lý do song song:** Case study cần thời gian xin xác nhận từ khách — bắt đầu ngay tuần 3, không đợi.

**Deliverable:** Topic cluster map, content briefs, danh sách khách đã liên hệ

**Owner:** Nội dung

---

### 📅 Tuần 4–6 — Content
**Viết 8–15 nội dung (kéo 3 tuần thay vì 2)**

**Thứ tự ưu tiên:**
1. Trang đã rank gần top 10 nhưng chưa tối ưu extractability → tối ưu trước
2. Trang câu hỏi cao điểm "giá trị cao + dễ thắng"
3. Trang trụ cột cho cụm topic chính
4. Bài có data sẵn (không đợi data chưa có)

**Tiêu chí mỗi bài:**
- [ ] Answer-first trong 3 câu đầu tiên
- [ ] Đoạn tự chứa ngữ cảnh
- [ ] Heading dạng câu hỏi đúng như khách hỏi
- [ ] Internal links đúng theo plan
- [ ] Schema phù hợp (Article / FAQPage / HowTo)
- [ ] Tên tác giả thật + bio ngắn

**Deliverable:** 8–15 bài publish hoặc cập nhật

**Owner:** Nội dung

---

### 📅 Tuần 6 — Entity & Schema
**[Song song với cuối giai đoạn nội dung]**

**Ưu tiên:**
- [ ] Trang Giới thiệu đầy đủ (NAP + đội ngũ)
- [ ] Trang tác giả hoàn chỉnh (ảnh thật, bio, link ngoài)
- [ ] Organization schema + sameAs trên trang chủ
- [ ] Person schema cho tác giả chính
- [ ] LocalBusiness schema (nếu có địa điểm)
- [ ] Google Business Profile update
- [ ] Merchant Center setup (nếu ecommerce)
- [ ] Validate toàn bộ schema mới qua Rich Results Test

**Deliverable:** Entity audit hoàn tất theo `checklists/entity-audit.md`

**Owner:** Entity/Brand + Technical

---

### 📅 Tuần 7–8 — Amplify & Baseline
**Case study + Off-site + Test AI lần đầu + Baseline chính thức**

**Ưu tiên:**
- [ ] Publish case study đầu tiên (nếu đã có data + quote từ tuần 3)
- [ ] Request Index cho tất cả trang mới/cập nhật qua Search Console
- [ ] Chạy bộ test 30–50 câu lần đầu → ghi kết quả → đây là baseline AI
- [ ] Lập baseline chính thức: Search Console + GA4 + bộ test AI
- [ ] Tham gia 2–3 forum/group ngành với nội dung hữu ích
- [ ] Setup Google Alerts brand monitoring
- [ ] Lập lịch hàng tháng cho vòng lặp bảo trì

**Lưu ý:** Case study và off-site là bắt đầu, không phải hoàn tất. Tiếp tục ở vòng lặp hàng tháng.

**Deliverable:** Baseline report đầy đủ, lịch hàng tháng

**Owner:** Tất cả owners

---

## Bảng tóm lược

| Thời gian | Công việc chính | Owner | Điều chỉnh vs plan gốc |
|-----------|----------------|-------|----------------------|
| Tuần 1 | Scope + kỹ thuật + rendering | Technical | Chốt owner, baseline trước |
| Tuần 2 | 30–50 câu, fan-out, đối thủ AI | Nội dung + đo lường | |
| Tuần 3 | Topic cluster, internal link, template | Nội dung | **Song song xin data/quote khách ngay** |
| Tuần 4–6 | Viết 8–15 nội dung | Nội dung | **Kéo 3 tuần thay vì 2** |
| Tuần 6 | Entity, tác giả, schema, GBP | Entity + Technical | |
| Tuần 7–8 | Case study + video + off-site | Tất cả | **Coi là bắt đầu, không phải hoàn tất** |
| Tuần 8 | Request index + test AI + baseline | Đo lường | |

---

## Sau tuần 8 → Vòng lặp hàng tháng

Xem `12-vong-lap-hang-thang.md`

---

## ⚠️ Cảnh báo kỳ vọng

```
❌ Không kỳ vọng: "8 tuần xong là thấy kết quả ngay"
✅ Thực tế: Google index và xử lý tín hiệu cần 2–4 tuần sau khi publish
✅ Thực tế: AI citation thường thấy sau khi trang đã rank tốt (thêm 4–8 tuần)
✅ Thực tế: Case study thật + off-site cần nhiều tháng để tích lũy

→ Kết quả rõ rệt: tháng 3–4 sau khi bắt đầu
→ Kết quả bền vững: tháng 6+
```
