# 08. Giai Đoạn 7 — Bán Hàng / Doanh Nghiệp Địa Phương

> Áp dụng khi có địa điểm vật lý (cửa hàng, showroom, văn phòng) và/hoặc bán sản phẩm cần xuất hiện trong Google Shopping.

---

## 7.1. Google Business Profile (GBP)

> GBP là nguồn dữ liệu chính cho local search và AI Overviews khi có query địa lý.

### Tạo / tối ưu GBP

- [ ] Xác nhận ownership (qua postcard, phone, email, hoặc video)
- [ ] Tên doanh nghiệp đúng pháp nhân (không thêm keyword vào tên)
- [ ] Danh mục chính: chọn đúng nhất (primary category ảnh hưởng nhiều nhất)
- [ ] Danh mục phụ: thêm tối đa 10 danh mục liên quan
- [ ] Địa chỉ đầy đủ, khớp website
- [ ] Số điện thoại chính xác, khớp website
- [ ] Website URL trỏ đúng trang chủ hoặc landing page
- [ ] Giờ mở cửa đầy đủ (kể cả ngày lễ)
- [ ] Mô tả doanh nghiệp: 750 ký tự, tự nhiên, không nhồi keyword

### Tối ưu GBP liên tục

| Hành động | Tần suất | Ghi chú |
|-----------|---------|---------|
| Đăng Google Posts | Hàng tuần | Sản phẩm mới, ưu đãi, sự kiện |
| Cập nhật ảnh | 2 tuần/lần | Ảnh thật: sản phẩm, cửa hàng, đội ngũ |
| Trả lời reviews | Trong 24h | Cả review tích cực lẫn tiêu cực |
| Cập nhật Q&A | Khi có câu hỏi | Trả lời đầy đủ, add câu hỏi phổ biến |
| Cập nhật sản phẩm/dịch vụ | Khi có thay đổi | |

### Xin review đúng cách

```
✅ Được phép: Yêu cầu review từ khách hàng thật sau khi mua
✅ Được phép: Gửi link review qua email/SMS sau giao hàng
✅ Được phép: Đặt QR code tại cửa hàng dẫn tới trang review

❌ Không được: Mua review
❌ Không được: Ép khách review để đổi ưu đãi
❌ Không được: Review từ nhân viên dùng tài khoản riêng
```

**Công thức xin review tỷ lệ cao:**
```
"Cảm ơn [tên khách] đã mua hàng! Bạn có 2 phút 
để chia sẻ trải nghiệm không? Đánh giá của bạn 
giúp chúng tôi cải thiện và giúp khách hàng khác 
tìm được sản phẩm phù hợp. [Link review]"
```

---

## 7.2. LocalBusiness Schema

> Đặt trên trang chủ hoặc trang liên hệ, sau Organization schema.

```json
{
  "@context": "https://schema.org",
  "@type": "Store",
  "name": "Tên Cửa Hàng",
  "image": "https://example.com/storefront.jpg",
  "description": "Mô tả cửa hàng",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Đường ABC, Phường XYZ",
    "addressLocality": "Quận 1",
    "addressRegion": "TP. Hồ Chí Minh",
    "postalCode": "70000",
    "addressCountry": "VN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 10.7769,
    "longitude": 106.7009
  },
  "url": "https://example.com",
  "telephone": "+84-xxx-xxx-xxxx",
  "openingHoursSpecification": [
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      "opens": "09:00",
      "closes": "21:00"
    },
    {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Saturday", "Sunday"],
      "opens": "09:00",
      "closes": "22:00"
    }
  ],
  "priceRange": "₫₫"
}
```

---

## 7.3. Google Merchant Center & Product Schema

> Dành cho site có sản phẩm muốn xuất hiện trong Google Shopping và AI Shopping results.

### Setup Merchant Center

1. Tạo tài khoản tại [Merchant Center](https://merchants.google.com)
2. Xác nhận domain (thêm tag hoặc file xác minh)
3. Kết nối với Google Ads (nếu có)
4. Upload product feed

### Product Feed (cách đơn giản nhất cho Haravan)

```
Option 1: Dùng app Haravan tích hợp Merchant Center
Option 2: Export CSV từ Haravan → import lên Merchant Center
Option 3: Dùng Google Shopping app trên Haravan App Store
```

### Các trường quan trọng trong feed

| Trường | Bắt buộc | Ghi chú |
|--------|---------|---------|
| `id` | ✅ | SKU hoặc product ID |
| `title` | ✅ | Tên sản phẩm (không viết hoa toàn bộ) |
| `description` | ✅ | Mô tả đầy đủ, không nhồi keyword |
| `link` | ✅ | URL trang sản phẩm |
| `image_link` | ✅ | URL ảnh chính (tối thiểu 100x100px) |
| `availability` | ✅ | `in_stock` / `out_of_stock` / `preorder` |
| `price` | ✅ | Giá kèm đơn vị tiền tệ (VND) |
| `brand` | ✅ cho hầu hết | Tên thương hiệu |
| `gtin` / `mpn` | Khuyến nghị | Mã sản phẩm tiêu chuẩn |
| `product_type` | Khuyến nghị | Danh mục sản phẩm |

### Product Schema trên trang sản phẩm

> Xem template tại `07-giai-doan-6-schema.md` — phần Product Schema.

---

## 7.4. Chiến lược review cho ecommerce

### Nền tảng cần có review

| Nền tảng | Ưu tiên | Ghi chú |
|---------|---------|---------|
| Google Maps (qua GBP) | ⭐⭐⭐ | Ảnh hưởng local pack + AI |
| Facebook Page | ⭐⭐⭐ | Dễ xin từ khách VN |
| Shopee / Lazada | ⭐⭐ | Nếu bán trên marketplace |
| Trustpilot | ⭐ | Thường dùng cho B2B |

### Quy trình xin review tự động

```
Sau giao hàng 3 ngày:
  → Email/SMS "Bạn có hài lòng không?"
  → Nếu hài lòng → dẫn tới trang review Google/Facebook
  → Nếu không hài lòng → form nội bộ để team CSKH xử lý
```

---

## Checklist Giai đoạn 7

- [ ] GBP đã xác nhận ownership
- [ ] GBP thông tin đầy đủ (tên, địa chỉ, giờ mở cửa, ảnh, mô tả)
- [ ] LocalBusiness schema trên trang liên hệ/chủ
- [ ] Product schema trên tất cả trang sản phẩm
- [ ] Merchant Center account tạo + domain xác nhận
- [ ] Product feed upload lần đầu (không có lỗi)
- [ ] Quy trình xin review sau mua hàng đã thiết lập
- [ ] Đang trả lời review mới trong 24h
