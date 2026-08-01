# 07. Giai Đoạn 6 — Structured Data (Schema)

> Schema giúp Google **hiểu thực thể** trong nội dung của bạn — không phải "vé vào AI Overview".  
> Schema phải **khớp với nội dung hiển thị** — không được khai báo thứ người dùng không thấy.

---

## Nguyên tắc quan trọng trước khi làm schema

```
✅ Schema phải khớp nội dung thực trên trang (Google kiểm tra)
✅ Schema hỗ trợ hiểu thực thể, không tạo ra ranking trực tiếp
✅ Dùng đúng @type cho đúng loại trang
✅ Validate sau khi triển khai

❌ Đừng lạm dụng — không schema mọi thứ
❌ Đừng khai báo Review/Rating giả
❌ Đừng đặt schema không liên quan tới nội dung trang
```

---

## Bảng schema theo loại trang

| Loại trang | Schema nên dùng | Ghi chú |
|-----------|----------------|---------|
| Trang chủ | `Organization` + `WebSite` + `SiteLinksSearchBox` | |
| Trang sản phẩm | `Product` + `Offer` + `AggregateRating` | Offer cần giá thật, không fallback |
| Trang blog/bài viết | `Article` hoặc `BlogPosting` + `BreadcrumbList` | |
| FAQ trang | `FAQPage` | Câu hỏi phải có trong nội dung |
| Trang hướng dẫn | `HowTo` | Các bước phải hiển thị trên trang |
| Trang tác giả | `Person` + `sameAs` | |
| Trang danh mục | `BreadcrumbList` | |
| Trang liên hệ / địa điểm | `LocalBusiness` hoặc `Store` | Xem Giai đoạn 7 |
| Trang review/đánh giá | `Review` + `AggregateRating` | |

---

## Snippets thường gặp trong Schema

### Product Schema (quan trọng nhất cho ecommerce)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Tên sản phẩm",
  "image": ["https://example.com/image1.jpg"],
  "description": "Mô tả sản phẩm",
  "sku": "SKU-001",
  "brand": {
    "@type": "Brand",
    "name": "Tên thương hiệu"
  },
  "offers": {
    "@type": "Offer",
    "url": "https://example.com/product",
    "priceCurrency": "VND",
    "price": "299000",
    "priceValidUntil": "2025-12-31",
    "itemCondition": "https://schema.org/NewCondition",
    "availability": "https://schema.org/InStock",
    "seller": {
      "@type": "Organization",
      "name": "Tên Shop"
    }
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "89"
  }
}
```

### FAQPage Schema

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Câu hỏi thứ nhất?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Câu trả lời đầy đủ, tự chứa ngữ cảnh."
      }
    },
    {
      "@type": "Question", 
      "name": "Câu hỏi thứ hai?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Câu trả lời đầy đủ."
      }
    }
  ]
}
```

### Article Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Tiêu đề bài viết",
  "datePublished": "2025-01-15",
  "dateModified": "2025-06-20",
  "author": {
    "@type": "Person",
    "name": "Tên tác giả",
    "url": "https://example.com/author/ten-tac-gia"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Tên tổ chức",
    "logo": {
      "@type": "ImageObject",
      "url": "https://example.com/logo.png"
    }
  },
  "image": "https://example.com/article-image.jpg",
  "description": "Mô tả ngắn bài viết"
}
```

---

## Validation và kiểm tra

### Công cụ validate
1. **Google Rich Results Test**: https://search.google.com/test/rich-results
   - Test từng URL sau khi deploy
   - Xem lỗi và cảnh báo
   
2. **Schema.org Validator**: https://validator.schema.org/
   - Validate syntax JSON-LD

3. **Search Console → Enhancements**
   - Xem lỗi schema trên toàn site
   - Theo dõi sau 1–2 tuần deploy

### Quy trình sau khi thêm schema
```
1. Validate trên Rich Results Test
2. Submit URL qua URL Inspection → Request Indexing
3. Kiểm tra Search Console Enhancements sau 2 tuần
4. Nếu có lỗi → fix theo hướng dẫn cụ thể của Google
```

---

## Triển khai trên Haravan

### Vị trí đặt schema
```liquid
{% comment %} Trong theme.liquid, trước </body> {% endcomment %}
<script type="application/ld+json">
  {{ product | json_for_schema }}  {# Nếu theme hỗ trợ #}
</script>
```

### Hoặc dùng snippets
```
Layout: theme.liquid → trước thẻ đóng </body>
Product: product.liquid → thêm block JSON-LD
Blog: article.liquid → thêm Article schema
```

> **Lưu ý Haravan:** Một số theme Haravan đã có schema tích hợp sẵn. Kiểm tra trước khi thêm để tránh duplicate schema.

---

## Checklist Schema

- [ ] `Organization` + `sameAs` trên trang chủ
- [ ] `Product` schema trên tất cả trang sản phẩm
- [ ] `BreadcrumbList` trên danh mục và trang con
- [ ] `Article` / `BlogPosting` trên tất cả bài blog
- [ ] `FAQPage` trên trang FAQ / section FAQ
- [ ] `Person` schema cho tác giả
- [ ] Validate tất cả schema bằng Rich Results Test
- [ ] Kiểm tra Search Console Enhancements sau 2 tuần
