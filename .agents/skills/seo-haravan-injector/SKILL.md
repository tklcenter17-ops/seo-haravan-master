---
name: seo-haravan-injector
description: >
  Skill triển khai bộ SEO Theme Injector hoàn chỉnh cho Haravan (v4.0.0).
  Kích hoạt khi user muốn: thêm SEO tự động vào theme Haravan, setup schema JSON-LD,
  tối ưu AI Overviews readiness, cấu hình seo-config, upload snippets, check rich results,
  hoặc nói "seo injector", "chèn seo", "tối ưu seo haravan", "setup seo theme".
  Áp dụng cho bất kỳ theme Haravan nào — bán hàng online hoặc local business.
---

# SEO Haravan Injector Skill — v4.0.0

> **Operating rule:** Khi skill này được gọi, agent phải đọc file từ
> `seo/theme-injector/` trước khi thực hiện bất kỳ thao tác nào.
> Không hardcode giá trị — đọc từ `seo-config.liquid` và hỏi user nếu thiếu thông tin.

---

## Vai Trò

Senior SEO Engineer + Haravan Liquid Specialist.
Triển khai, cấu hình, debug và tối ưu bộ SEO Injector tự động cho theme Haravan.

---

## Bộ File Injector (nằm tại `seo/theme-injector/`)

```
seo/theme-injector/
├── snippets/
│   ├── seo-config.liquid       ← ⚙️  CẤU HÌNH DUY NHẤT — điền thông tin shop
│   ├── seo-pro-master.liquid   ← 🎯  ĐIỂM VÀO DUY NHẤT — include vào theme.liquid
│   ├── seo-meta-head.liquid    ← Meta description, Robots, Canonical, OG, Twitter
│   ├── seo-schema-engine.liquid← 7 loại JSON-LD Schema tự động
│   ├── seo-faq-parser.liquid   ← FAQPage + HowTo Schema
│   ├── seo-pagination.liquid   ← rel prev/next cho collection và blog
│   └── seo-noindex.liquid      ← Auto noindex trang system
└── scripts/
    └── seo-cwv-booster.js      ← CWV: Lazy Load, INP, CLS, Prefetch on hover
```

---

## Quy Trình Triển Khai Chuẩn (Mới cài lần đầu)

### Bước 1 — Thu thập thông tin từ user

Hỏi user các thông tin sau (nếu chưa có):

```
REQUIRED:
□ Tên shop / thương hiệu
□ Domain website
□ URL Facebook Page (nếu có)
□ URL YouTube / TikTok / Zalo / Shopee / Lazada (nếu có)
□ Loại doanh nghiệp: 'online' hay 'local' (có cửa hàng vật lý)?
□ File seo-config.liquid đã điền chưa?

NẾU 'local':
□ Địa chỉ đường, quận, thành phố
□ Số điện thoại (format quốc tế: +84-xxx)
□ Tọa độ GPS (lấy từ Google Maps)
□ Giờ mở cửa (VD: Mo-Su 09:00-21:00)

OPTIONAL:
□ Năm thành lập
□ Email liên hệ support
□ URL font .woff2 chính (F12 → Network → filter "font")
□ Ảnh OG fallback 1200x630px (seo-og-default.jpg)
```

### Bước 2 — Điền `seo-config.liquid`

Mở file [`seo/theme-injector/snippets/seo-config.liquid`] và điền đúng các giá trị.
**Không sửa phần COMPUTED ở cuối file.**

### Bước 3 — Upload files lên Haravan

1. Haravan Admin → Website → Giao diện → Chỉnh sửa code
2. Mục **Snippets**: Upload 7 files `.liquid`
3. Mục **Assets**: Upload `seo-cwv-booster.js`
4. Upload ảnh `seo-og-default.jpg` (1200×630px) vào Assets nếu có

### Bước 4 — Chèn 1 dòng vào `layout/theme.liquid`

Tìm thẻ `</head>`, dán ngay phía trên:

```liquid
{% comment %} === SEO PRO MASTER v4.0 === {% endcomment %}
{% include 'seo-pro-master' %}
```

**KHÔNG dán 2 lần — snippet tự có guard.**

### Bước 5 — Verify

Dán URL từng loại trang vào [Google Rich Results Test](https://search.google.com/test/rich-results):

| Trang | Schema cần thấy |
|-------|----------------|
| Trang chủ | Organization/LocalBusiness, WebSite |
| Sản phẩm | Product, Offer, BreadcrumbList |
| Collection | CollectionPage + ItemList, BreadcrumbList |
| Bài viết | Article, BreadcrumbList |
| Trang liên hệ | ContactPage |

---

## Tính Năng Tự Động (User không cần làm gì)

### Meta & AI Overviews
- `max-snippet:-1, max-image-preview:large` → Google AI được phép trích toàn bộ nội dung
- `<meta name="description">` chuẩn 155 ký tự với guard chống duplicate
- `<link rel="canonical">` với guard
- OpenGraph đầy đủ (title, description, image 1200×630, alt, locale)
- Twitter Card `summary_large_image`
- Article OG: `article:published_time`, `article:modified_time`, `article:author`, `article:tag`
- OG image fallback khi trang không có ảnh riêng

### JSON-LD Schema (tự động theo template)

| Template | Schema render |
|----------|--------------|
| `index` | Organization/LocalBusiness + WebSite + SearchBox |
| `product` | Product + Offer + AggregateRating (nếu có reviews) + BreadcrumbList |
| `collection` | CollectionPage + ItemList (top 10 SP) + BreadcrumbList |
| `article` | Article + Author + BreadcrumbList |
| `blog` | BreadcrumbList |
| `page` (contact) | ContactPage + BreadcrumbList |
| Mọi trang | BreadcrumbList (trừ index) |

### Noindex Tự Động
Tự động `noindex, nofollow` cho: `search`, `cart`, `account`, `customers`, `404`, `policy`, `password`, `gift_card`.

### Core Web Vitals
- **LCP**: Server-side preload ảnh sản phẩm với `fetchpriority="high"`
- **LCP Font**: Preload .woff2 từ config
- **Preconnect**: `fonts.googleapis.com`, `fonts.gstatic.com`, `cdn.haravan.com` — server-side
- **DNS prefetch**: `google-analytics.com`, `googletagmanager.com`
- **Lazy Load**: Native `loading="lazy"` cho ảnh dưới viewport
- **CLS**: Auto gán `width`/`height` cho ảnh thiếu dimension
- **INP**: Yield main thread qua `scheduler.postTask` hoặc `setTimeout(0)`
- **Prefetch on hover**: Product/Collection/Blog links với 150ms delay + touch support

### FAQ & HowTo Schema (cho tác giả nội dung)

Thêm block HTML sau vào nội dung bài viết để tự động sinh schema:

**FAQPage:**
```html
<div class="seo-faq">
  <div class="seo-faq-item">
    <div class="seo-faq-question">Câu hỏi?</div>
    <div class="seo-faq-answer">Câu trả lời đầy đủ, tự chứa ngữ cảnh.</div>
  </div>
</div>
```

**HowTo:**
```html
<div class="seo-howto"
     data-name="Tiêu đề hướng dẫn"
     data-description="Mô tả ngắn"
     data-total-time="PT30M">
  <div class="seo-howto-step">
    <div class="seo-howto-step-name">Bước 1: Tên bước</div>
    <div class="seo-howto-step-text">Mô tả chi tiết.</div>
  </div>
</div>
```

---

## Xử Lý Tình Huống Thường Gặp

### Theme đã có Canonical hoặc Robots riêng → conflict

Thêm vào `layout/theme.liquid` **TRƯỚC** dòng include:

```liquid
{% assign seo_meta_canonical_done = true %}   <!-- nếu theme đã có canonical -->
{% assign seo_meta_robots_done = true %}       <!-- nếu theme đã có robots -->
{% assign seo_meta_description_done = true %}  <!-- nếu theme đã có description -->
{% include 'seo-pro-master' %}
```

### Schema AggregateRating không hiển thị

Sản phẩm cần có metafield `reviews.rating` và `reviews.rating_count`.
Haravan không có built-in reviews → cần app review bên thứ 3 hoặc nhập tay metafields.

### Pagination rel prev/next không đúng

Snippet dùng `paginate.page_size` — phải gọi từ bên trong `{% paginate ... %}` block.
Nếu theme không dùng paginate block Liquid chuẩn → snippet sẽ fallback `default: 24`.

### Giá sản phẩm hiển thị sai trong schema

Haravan lưu giá theo đơn vị xu (cents): 299.000₫ = 29.900.000 xu.
Snippet dùng `product.price | divided_by: 100` → ra đúng 299.000.
Nếu thấy giá sai, kiểm tra xem theme đang dùng đơn vị gì.

### LocalBusiness không hiện trên Google Maps

Cần thêm cả Google Business Profile và link domain vào GBP.
Schema chỉ là signal bổ sung, không tự tạo listing.

---

## Checklist Audit Nhanh (chạy sau khi tích hợp)

```
□ F12 → Elements → tìm <meta name="description"> → có và không rỗng?
□ F12 → Elements → tìm <script type="application/ld+json"> → có ≥1 block?
□ Rich Results Test → Product page → Product ✅, BreadcrumbList ✅?
□ Rich Results Test → Article page → Article ✅?
□ Rich Results Test → Home page → Organization ✅, WebSite ✅?
□ URL Inspection (GSC) → View Tested Page → HTML → có meta description?
□ Trang /cart → F12 → tìm robots tag → "noindex, nofollow"?
□ Trang collection trang 2 → F12 → tìm <link rel="prev">?
□ PageSpeed Insights → LCP < 2.5s?
□ PageSpeed Insights → CLS < 0.1?
```

---

## Không Làm / Anti-Patterns

- ❌ Không sửa `seo-schema-engine.liquid` để hardcode sameAs URLs → dùng `seo-config.liquid`
- ❌ Không include từng snippet riêng lẻ → chỉ include `seo-pro-master`
- ❌ Không dùng `product.price` trực tiếp trong JSON-LD → phải `divided_by: 100`
- ❌ Không hardcode `priceValidUntil` cố định → đã tính động trong snippet
- ❌ Không bọc `{% include 'seo-pro-master' %}` trong `{% if %}` → sẽ phá guard
- ❌ Không dùng `asset_url` mà không `prepend: 'https:'` trong JSON-LD
- ❌ Không chạy `querySelectorAll` ngoài `DOMContentLoaded` — FAQ/HowTo JS đã fix

---

## Tài Liệu Tham Khảo

- Bộ code đầy đủ: `seo/theme-injector/`
- Hướng dẫn cài đặt: `seo/theme-injector/README-GUIDE.md`
- Chiến lược SEO tổng thể: `seo/README.md`
- Lộ trình 8 tuần: `seo/11-lo-trinh-8-tuan.md`
- Đo lường KPI: `seo/10-giai-doan-9-measurement.md`
- Google Rich Results Test: https://search.google.com/test/rich-results
- Schema.org validator: https://validator.schema.org
