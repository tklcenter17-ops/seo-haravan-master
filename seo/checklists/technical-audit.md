# Checklist: Technical Audit

> Chạy checklist này ở Tuần 1 và sau đó mỗi quý 1 lần.  
> Đánh dấu: ✅ OK | ❌ Lỗi cần fix | ⚠️ Cần xem xét | N/A không áp dụng

---

## A. Crawlability

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| A1 | robots.txt không block Googlebot (kiểm tra /robots.txt) | | |
| A2 | robots.txt không block CSS/JS quan trọng | | |
| A3 | Không có meta robots noindex trên trang quan trọng | | |
| A4 | Sitemap XML tồn tại tại /sitemap.xml | | |
| A5 | Sitemap được submit lên Search Console | | |
| A6 | Sitemap không có lỗi (Search Console → Sitemaps) | | |
| A7 | Sitemap chỉ chứa URL muốn index (không có 4xx, noindex) | | |

---

## B. Indexability

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| B1 | 10 trang quan trọng nhất đã được index (URL Inspection) | | |
| B2 | Không có trang quan trọng bị lỗi "Crawled - currently not indexed" | | |
| B3 | Redirect chain ≤ 2 hop | | |
| B4 | Không có redirect loop | | |
| B5 | Canonical tự trỏ về chính nó trên trang chính | | |
| B6 | Canonical không trỏ sai (VD: trang A canonical về trang B vô lý) | | |
| B7 | Không có trang 404 quan trọng bị link tới | | |

---

## C. Rendering (Điểm dễ hỏng nhất)

> **Cách kiểm tra:** URL Inspection → Test Live URL → View Tested Page → Tab HTML

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| C1 | H1 có trong HTML Googlebot nhận | | |
| C2 | H2, H3 quan trọng có trong HTML | | |
| C3 | Mô tả sản phẩm đầy đủ có trong HTML (không chỉ có sau JS) | | |
| C4 | Giá sản phẩm có trong HTML | | |
| C5 | Đoạn answer-first có trong HTML | | |
| C6 | Nội dung không chỉ hiện sau click/scroll/tab | | |
| C7 | Googlebot render đủ JavaScript cần thiết | | |

---

## D. Core Web Vitals

> **Công cụ:** PageSpeed Insights (pageSpeed.web.dev) → Mobile + Desktop

| # | Metric | Điểm hiện tại | Mục tiêu | Ghi chú |
|---|--------|--------------|---------|---------|
| D1 | LCP (desktop) | | ≤ 2.5s | |
| D2 | LCP (mobile) | | ≤ 2.5s | |
| D3 | INP (desktop) | | ≤ 200ms | |
| D4 | INP (mobile) | | ≤ 200ms | |
| D5 | CLS (desktop) | | ≤ 0.1 | |
| D6 | CLS (mobile) | | ≤ 0.1 | |
| D7 | PageSpeed Score (desktop) | | ≥ 80 | |
| D8 | PageSpeed Score (mobile) | | ≥ 70 | |

---

## E. Snippet Control

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| E1 | Không có nosnippet trên trang muốn được trích | | |
| E2 | max-snippet không đặt quá thấp (< 50) | | |
| E3 | Trang nội dung chính có max-snippet:-1 hoặc giá trị cao | | |
| E4 | data-nosnippet dùng đúng chỗ (giá nội bộ, ghi chú riêng) | | |

---

## F. Language & Geo

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| F1 | `<html lang="vi">` hoặc `lang="vi-VN"` đặt đúng | | |
| F2 | hreflang đúng nếu có đa ngôn ngữ | | |
| F3 | Canonical không trỏ nhầm bản ngôn ngữ khác | | |
| F4 | AI Overviews đã rollout cho vi-VN (test thủ công) | | |

---

## G. Haravan-specific

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| G1 | Trang phân trang (`/page/2`) có canonical về trang gốc | | |
| G2 | Trang lọc sản phẩm (facets) có noindex hoặc bị block | | |
| G3 | Product variant URLs (`?variant=xxx`) có canonical về URL gốc | | |
| G4 | Blog Haravan: title, description, OG tags render đúng | | |
| G5 | Sitemap Haravan (`/sitemap.xml`) đầy đủ và submit | | |
| G6 | JS third-party (chat, tracking) không ảnh hưởng LCP | | |
| G7 | Không có schema duplicate (theme tự tạo + bạn thêm = trùng) | | |

---

## H. Cannibalization

| # | Mục | Trạng thái | Ghi chú / Fix |
|---|-----|-----------|--------------|
| H1 | Không có 2+ URL cùng rank top 10 cho cùng query | | |
| H2 | Trang collection và trang tag không trùng nội dung | | |
| H3 | Trang blog và trang sản phẩm nhắm intent khác nhau | | |

---

## Tóm lược lỗi cần fix

| # | Lỗi | Mức độ | Owner | Deadline |
|---|-----|--------|-------|---------|
| 1 | | 🔴 Critical / 🟡 Important / 🟢 Nice-to-have | | |
| 2 | | | | |
| 3 | | | | |

---

## Ngày audit

| Lần | Ngày | Người audit | Ghi chú |
|-----|------|------------|---------|
| 1 (baseline) | | | |
| 2 (quý 2) | | | |
| 3 (quý 3) | | | |
