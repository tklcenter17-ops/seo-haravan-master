# 📖 Hướng Dẫn Tích Hợp SEO Pro Master — v2.0.0

> **Cải tiến v2:** Fix 10 lỗi nghiêm trọng, thêm `seo-config.liquid` để cấu hình 1 lần.

---

## 📁 Danh Sách File (Upload lên Snippets của Haravan)

| File | Mô tả |
| :--- | :--- |
| `seo-config.liquid` | ⚙️ **Điền thông tin shop tại đây** (sameAs, logo, author) |
| `seo-pro-master.liquid` | 🎯 File Master — dán vào `theme.liquid` |
| `seo-meta-head.liquid` | 🤖 Meta Tags + AI Overviews Directives + OG + Twitter Card |
| `seo-schema-engine.liquid` | 📊 JSON-LD Schema tự động (Product, Article, Organization, Breadcrumb, Collection) |
| `seo-faq-parser.liquid` | ❓ FAQ Schema tự động từ nội dung |

**Upload vào thư mục `assets/` của Theme:**

| File | Mô tả |
| :--- | :--- |
| `seo-cwv-booster.js` | ⚡ Core Web Vitals: Lazy Load + INP + CLS + Preconnect |

---

## ⚡ 3 Bước Tích Hợp

### Bước 1 — Cấu hình shop (làm 1 lần duy nhất)

Mở file `seo-config.liquid` và điền thông tin thật của shop:

```liquid
{% assign seo_facebook_url   = 'https://www.facebook.com/tenpage' %}
{% assign seo_youtube_url    = 'https://www.youtube.com/@tenchannel' %}
{% assign seo_linkedin_url   = '' %}  {# để trống nếu không có #}
```

### Bước 2 — Upload Files

1. Haravan Admin → **Website** → **Giao diện** → **Chỉnh sửa code**
2. Trong mục **Snippets**: Upload 5 file `.liquid`
3. Trong mục **Assets**: Upload `seo-cwv-booster.js`

### Bước 3 — Chèn 1 dòng vào theme.liquid

Mở `layout/theme.liquid`, tìm thẻ `</head>`, dán ngay phía trên:

```liquid
{% comment %} === SEO PRO MASTER v2.0 === {% endcomment %}
{% include 'seo-pro-master' %}
```

> ⚠️ **Lưu ý:** Chỉ dán **1 lần duy nhất**. Snippet đã có guard tự chống chạy 2 lần.

---

## ✅ Kiểm Tra Sau Khi Tích Hợp

### Test Schema (bắt buộc)

| Loại trang | URL để test | Mong đợi thấy |
| :--- | :--- | :--- |
| Trang sản phẩm | `/products/[slug]` | `Product`, `BreadcrumbList`, `Organization` |
| Trang blog | `/blogs/[blog]/[article]` | `Article`, `BreadcrumbList` |
| Trang danh mục | `/collections/[slug]` | `CollectionPage`, `BreadcrumbList` |
| Trang chủ | `/` | `WebSite`, `Organization` |

Dán URL vào: **[Google Rich Results Test](https://search.google.com/test/rich-results)**

### Test Meta Tags

Mở DevTools (F12) → Sources → Tìm `application/ld+json` để xem JSON-LD render đúng chưa.

---

## 🔧 Tùy chỉnh nâng cao

### Nếu theme đã có Canonical / Robots riêng

Thêm dòng này vào `layout/theme.liquid` **trước** dòng `{% include 'seo-pro-master' %}` để tắt phần đó:

```liquid
{% assign seo_meta_canonical_done = true %}
{% assign seo_meta_robots_done = true %}
{% include 'seo-pro-master' %}
```

### Thêm FAQ Schema vào bài viết

Trong nội dung bài viết, dùng cấu trúc HTML này:

```html
<div class="seo-faq">
  <div class="seo-faq-item">
    <div class="seo-faq-question">Câu hỏi của khách hàng?</div>
    <div class="seo-faq-answer">Câu trả lời đầy đủ, tự chứa ngữ cảnh.</div>
  </div>
</div>
```

Snippet sẽ tự động tạo `FAQPage` JSON-LD schema từ các block trên.

---

## 🗂️ Changelog

| Version | Thay đổi |
| :--- | :--- |
| v2.0.0 | Fix 10 lỗi critical/important: price format, logo dynamic, dateModified thật, priceValidUntil động, sameAs từ config, duplicate guard, Twitter Card, OG image size, LCP preload server-side, FAQ server-side detect |
| v1.0.0 | Release đầu tiên |
