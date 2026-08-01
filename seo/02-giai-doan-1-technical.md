# 02. Giai Đoạn 1 — Điều Kiện Kỹ Thuật để Google AI Dùng Được Site

> Đây là nền móng bắt buộc. Nếu kỹ thuật hỏng → AI không trích dù nội dung tốt.  
> Dùng checklist tại `checklists/technical-audit.md` để kiểm tra từng mục.

---

## 1.1. Crawlability & Indexability

### Crawl
- [ ] `robots.txt` không block Googlebot (cả desktop lẫn smartphone)
- [ ] Không có `<meta name="robots" content="noindex">` trên trang muốn index
- [ ] Sitemap XML tồn tại, được submit lên Search Console, không có lỗi
- [ ] Sitemap chỉ chứa URL muốn index (loại bỏ trang trùng, trang lỗi)

### Index
- [ ] URL Inspection trên Search Console → trang quan trọng được index
- [ ] Không có trang 404 quan trọng bị link tới
- [ ] Redirect chain không quá 2 hop
- [ ] Canonical đúng — tự trỏ về chính nó (không trỏ sang URL khác vô lý)

---

## 1.2. Core Web Vitals & Tốc độ

> AI Overviews ưu tiên trích nguồn từ trang có UX tốt. Tốc độ kém → Google không muốn gửi user tới.

| Metric | Mục tiêu Good | Công cụ kiểm tra |
|--------|--------------|-----------------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | PageSpeed Insights, CrUX |
| INP (Interaction to Next Paint) | ≤ 200ms | PageSpeed Insights |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | PageSpeed Insights |

**Haravan-specific:**
- Ảnh sản phẩm: dùng định dạng WebP, có `width` + `height`, lazy load đúng cách
- Không chặn render CSS/JS quan trọng above-the-fold
- Font chữ: dùng `font-display: swap`

---

## 1.3. Audit Haravan (đặc thù nền tảng)

> Haravan có một số điểm cần kiểm tra riêng so với WordPress/custom stack.

- [ ] **Theme liquid**: kiểm tra `{% paginate %}` — trang phân trang có canonical về `/collection/` không
- [ ] **Trang lọc sản phẩm** (facets): block bằng `robots.txt` hoặc `noindex` nếu tạo ra hàng nghìn URL trùng nội dung
- [ ] **Product variant URLs** (ví dụ `?variant=xxx`): canonical về URL gốc
- [ ] **Blog Haravan**: kiểm tra metadata — title, description, OG tags có render đúng không
- [ ] **Sitemap tự động của Haravan**: kiểm tra `/sitemap.xml` có đầy đủ và submit chưa
- [ ] **Tốc độ Haravan**: kiểm tra JS third-party (widget chat, tracking) có ảnh hưởng LCP không

---

## 1.4. Rendering (điểm dễ hỏng nhất với Haravan/JS)

> **Nguyên tắc:** Nội dung mà AI cần phải có trong HTML server-side hoặc render được không cần tương tác.

### Cách kiểm tra chính xác (không đoán)
```
1. Google Search Console → URL Inspection
2. Nhập URL cần kiểm tra → "Test Live URL"
3. Chờ render xong → click "View Tested Page"
4. Tab "HTML" → đây là HTML mà Googlebot thực sự nhận
5. Tìm kiếm nội dung quan trọng trong HTML đó
```

### Nội dung bắt buộc phải có trong HTML server-side
- [ ] Tên sản phẩm / tiêu đề trang
- [ ] Mô tả sản phẩm đầy đủ (không chỉ hiện sau JS)
- [ ] Đoạn "answer-first" (câu trả lời trực tiếp, tóm tắt)
- [ ] Giá sản phẩm
- [ ] Heading H1, H2, H3

### Nội dung chỉ hiện sau click/scroll/JS thay thế
❌ AI khó dùng → cần chuyển sang server-side render

---

## 1.5. Snippet Control

> Cấu hình sai ở đây → chặn cả AI trích xuất lẫn featured snippet.

| Tag | Ý nghĩa | Dùng khi nào |
|-----|---------|-------------|
| `<meta name="robots" content="nosnippet">` | Chặn hoàn toàn snippet | TRÁNH nếu muốn AI trích |
| `<meta name="robots" content="max-snippet:0">` | Chặn hoàn toàn snippet | TRÁNH |
| `<meta name="robots" content="max-snippet:-1">` | Cho phép snippet dài tùy ý | **Dùng cho trang nội dung** |
| `<meta name="robots" content="max-snippet:150">` | Giới hạn ở 150 ký tự | Dùng thận trọng |
| `data-nosnippet` (attribute HTML) | Ẩn vùng cụ thể khỏi snippet | Dùng cho giá nội bộ, ghi chú nhạy cảm |

**Khuyến nghị:** Đặt `max-snippet:-1` cho trang nội dung muốn AI trích. Dùng `data-nosnippet` cho vùng KHÔNG muốn AI lấy (giá wholesale, điều khoản nội bộ).

---

## 1.6. Language / Geo Targeting (cần cho thị trường VN)

- [ ] Nếu có đa ngôn ngữ: `hreflang="vi-VN"` đặt đúng, `hreflang="x-default"` có giá trị
- [ ] Canonical không trỏ nhầm bản tiếng Anh về bản tiếng Việt hoặc ngược lại
- [ ] `<html lang="vi">` hoặc `lang="vi-VN"` đặt đúng
- [ ] `<meta name="geo.region" content="VN">` (optional nhưng hữu ích)

**Kiểm tra rollout AI Overviews:**
```
Mở Chrome → Google.com.vn (hoặc Google.com với ngôn ngữ VN)
Tìm: "cách chọn giày thể thao phù hợp" (hoặc câu hỏi ngành)
→ Nếu thấy hộp AI trả lời → AI Overviews đã rollout
→ Nếu không thấy → có thể rollout chưa đến, thử lại sau 2–4 tuần
```

---

## 1.7. Cannibalization & Trùng Lặp

> Nhiều URL cùng nhắm một intent → AI/Google phân tán tín hiệu, không URL nào "thắng".

### Cách phát hiện
```bash
# Tìm URL trùng intent trong Search Console
Filter: 2+ URL có cùng query trong top 10
→ Đây là dấu hiệu cannibalization
```

### Cách xử lý

| Tình huống | Giải pháp |
|-----------|----------|
| 2 bài blog viết cùng chủ đề | Gộp vào 1 bài mạnh hơn, redirect 301 |
| Trang collection + trang tag trùng nội dung | Canonical từ tag về collection |
| Trang sản phẩm + trang blog cùng rank cho query | Giữ trang sản phẩm, tối ưu blog sang intent khác |
| Phân trang `/page/2` rank thay vì trang gốc | Kiểm tra canonical phân trang |

---

## Thứ tự ưu tiên audit

```
1. Index OK chưa?         → URL Inspection
2. Render OK chưa?        → View Tested Page HTML  
3. Snippet không bị chặn? → Kiểm tra meta robots
4. Core Web Vitals?       → PageSpeed Insights
5. Canonical / Hreflang?  → Screaming Frog / manual
6. Cannibalization?        → Search Console filter
```

→ Xem chi tiết từng bước trong `checklists/technical-audit.md`
