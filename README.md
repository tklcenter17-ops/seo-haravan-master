# SEO Haravan Injector — v4.0.0

> Bộ snippet tự động chèn Full SEO & Google AI Overviews Readiness vào bất kỳ Theme Haravan nào.
> Chỉ cần **1 dòng code** dán vào `layout/theme.liquid`.

---

## 🚀 Cài đặt nhanh

### Bước 1 — Cấu hình shop

Mở `seo/theme-injector/snippets/seo-config.liquid` và điền thông tin:

```liquid
{% assign seo_facebook_url  = 'https://www.facebook.com/tenpage' %}
{% assign seo_business_type = 'online' %}  {# hoặc 'local' nếu có cửa hàng #}
```

### Bước 2 — Upload lên Haravan

1. Haravan Admin → Website → Giao diện → Chỉnh sửa code
2. **Snippets**: Upload 7 files `.liquid` từ `seo/theme-injector/snippets/`
3. **Assets**: Upload `seo-cwv-booster.js` từ `seo/theme-injector/scripts/`

### Bước 3 — Dán 1 dòng vào `layout/theme.liquid`

Tìm thẻ `</head>`, dán ngay phía trên:

```liquid
{% include 'seo-pro-master' %}
```

---

## 📁 Cấu trúc

```
seo/theme-injector/
├── snippets/
│   ├── seo-config.liquid        ← ⚙️  Điền thông tin shop tại đây
│   ├── seo-pro-master.liquid    ← 🎯  Dán vào theme.liquid
│   ├── seo-meta-head.liquid     ← Meta, AI Overviews, OG, Twitter Card
│   ├── seo-schema-engine.liquid ← JSON-LD: Product, Article, Org, Breadcrumb...
│   ├── seo-faq-parser.liquid    ← FAQPage + HowTo Schema
│   ├── seo-pagination.liquid    ← rel prev/next chống duplicate content
│   └── seo-noindex.liquid       ← Auto noindex cart, search, account, 404
└── scripts/
    └── seo-cwv-booster.js       ← LCP, CLS, INP, Lazy Load, Prefetch
```

---

## ✅ Tính năng

| Hạng mục | Tính năng |
|----------|----------|
| **AI Overviews** | `max-snippet:-1`, `max-image-preview:large` |
| **Meta** | `description` 155 ký tự, `canonical`, guard chống duplicate |
| **OpenGraph** | type, title, description, image 1200×630, alt, locale, fallback |
| **Twitter Card** | `summary_large_image` với image:alt |
| **Schema** | Organization/LocalBusiness, WebSite + SearchBox, Product + Offer + AggregateRating |
| | Article + Author + Keywords, CollectionPage + ItemList top 10, BreadcrumbList |
| | FAQPage, HowTo, ContactPage |
| **Pagination** | `rel="prev"` / `rel="next"` cho collection và blog |
| **Noindex** | Tự động cho: search, cart, account, 404, password, policy, gift_card |
| **CWV** | Preload LCP image, font preload, preconnect server-side, lazy load, CLS fix, INP yield, prefetch on hover |

---

## 🤖 AI Skill

Bộ này đi kèm skill Antigravity AI tại `.agents/skills/seo-haravan-injector/SKILL.md`.
Khi bạn nói **"setup seo haravan"** hoặc **"seo injector"** với Antigravity, skill sẽ tự động hướng dẫn triển khai từng bước.

---

## 📖 Tài liệu đầy đủ

- Hướng dẫn cài đặt: [`seo/theme-injector/README-GUIDE.md`](seo/theme-injector/README-GUIDE.md)
- Chiến lược SEO tổng thể: [`seo/README.md`](seo/README.md)
- Lộ trình 8 tuần: [`seo/11-lo-trinh-8-tuan.md`](seo/11-lo-trinh-8-tuan.md)

---

## 🔍 Verify sau khi cài

Dán URL vào [Google Rich Results Test](https://search.google.com/test/rich-results):

| Loại trang | Schema cần thấy |
|-----------|----------------|
| Trang chủ | Organization, WebSite ✅ |
| Sản phẩm | Product, Offer, BreadcrumbList ✅ |
| Collection | CollectionPage + ItemList ✅ |
| Bài viết | Article, BreadcrumbList ✅ |

---

> **Version**: 4.0.0 | **Target**: Haravan v1.0 | **Market**: vi-VN
