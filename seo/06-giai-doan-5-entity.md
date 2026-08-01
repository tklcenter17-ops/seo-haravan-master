# 06. Giai Đoạn 5 — Thực Thể Thương Hiệu

> Google hiểu thế giới qua thực thể (entities), không chỉ qua từ khóa. Thương hiệu của bạn phải là một thực thể được nhận diện rõ ràng — trên site và ngoài site.

---

## 5.1. Thông tin cơ bản trên site

### Trang Giới thiệu (About)
```
Bắt buộc có:
- Tên pháp nhân đầy đủ
- Lĩnh vực hoạt động
- Năm thành lập
- Địa chỉ đầy đủ (nếu có địa điểm vật lý)
- Số điện thoại
- Email liên hệ
- Đội ngũ chủ chốt (tên + chức vụ + ảnh thật)
- Các chứng chỉ / giải thưởng / mốc quan trọng
```

### NAP Consistency (Name, Address, Phone)
```
Quy tắc: Tên / Địa chỉ / SĐT phải GIỐNG HỆT nhau trên:
- Trang web
- Google Business Profile
- Facebook Page
- Các directory, forum có đề cập thương hiệu
```

Sai lầm phổ biến:
```
Website:   "Công ty TNHH ABC"
Facebook:  "ABC Store"  
GBP:       "ABC - Thời trang"
→ Google không nối được 3 thực thể này làm một
```

### Trang tác giả (nếu có blog)
```
Bắt buộc:
- Ảnh thật
- Tên thật
- Chức danh / chuyên môn
- Số năm kinh nghiệm
- Link ra profiles bên ngoài (LinkedIn, v.v.)
- Bài đã viết

Tránh: Trang tác giả trống hoặc chỉ có 2 câu chung chung
```

---

## 5.2. Schema Organization (trên trang chủ)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Tên Thương Hiệu",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "description": "Mô tả ngắn về doanh nghiệp",
  "foundingDate": "2020",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Đường ABC",
    "addressLocality": "TP. Hồ Chí Minh",
    "addressCountry": "VN"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+84-xxx-xxx-xxxx",
    "contactType": "customer service"
  },
  "sameAs": [
    "https://www.facebook.com/[page]",
    "https://www.youtube.com/@[channel]",
    "https://www.linkedin.com/company/[company]",
    "https://g.co/kgs/[business-profile]"
  ]
}
```

> **`sameAs` quan trọng:** Đây là cách Google nối thực thể website với profiles ngoài. Liệt kê tất cả profile chính chủ.

---

## 5.3. Liên kết ngoài site (off-site entity signals)

### Profiles chính chủ cần tạo / cập nhật

| Platform | Độ ưu tiên | Ghi chú |
|---------|------------|---------|
| Google Business Profile | ⭐⭐⭐ | Bắt buộc nếu có địa điểm vật lý |
| Facebook Page | ⭐⭐⭐ | NAP khớp website |
| YouTube Channel | ⭐⭐ | Nếu có video content |
| LinkedIn Company | ⭐⭐ | Quan trọng cho B2B |
| Shopee / Lazada Store | ⭐⭐ | Nếu bán trên marketplace |
| Zalo Official Account | ⭐ | Thị trường VN |

### Wikidata (nếu đủ điều kiện)
```
Điều kiện: Thương hiệu đủ "notable" (có bài báo đề cập, có lịch sử đáng kể)
Lợi ích: Hỗ trợ Knowledge Panel trên Google
Cách làm: Tạo item trên wikidata.org với các thuộc tính cơ bản
Không cần: Không nhất thiết phải có trang Wikipedia
```

---

## 5.4. E-E-A-T thật (không phải trang tác giả trống)

> E-E-A-T = Experience, Expertise, Authoritativeness, Trustworthiness  
> Tín hiệu thật nằm **ngoài site** nhiều hơn trong site.

### Tín hiệu E-E-A-T có giá trị

| Tín hiệu | Mức độ | Cách xây dựng |
|---------|--------|--------------|
| Được nhắc trong báo uy tín | ⭐⭐⭐ | Digital PR, case study shareable |
| Tác giả có LinkedIn profile đầy đủ | ⭐⭐ | Cập nhật LinkedIn, link từ bio |
| Tác giả có bài đăng ở site khác (guest post) | ⭐⭐ | Viết cho blog ngành, báo ngành |
| Review thật trên Google Maps | ⭐⭐ | Xin review từ khách hài lòng |
| Tham gia hội thảo / sự kiện ngành | ⭐ | Có ảnh/bài ghi lại |
| Chứng chỉ ngành liên quan | ⭐ | Đăng lên trang tác giả + LinkedIn |

### Tín hiệu KHÔNG có giá trị
❌ Trang "Chuyên gia của chúng tôi" chỉ có tên + ảnh stock  
❌ Badge "10 năm kinh nghiệm" không có minh chứng nào  
❌ Chứng chỉ tự phong  

---

## 5.5. Checklist Giai đoạn 5

- [ ] Trang Giới thiệu đầy đủ (NAP + đội ngũ thật)
- [ ] NAP đồng nhất trên website / GBP / Facebook
- [ ] Schema Organization với `sameAs` đầy đủ
- [ ] Schema Person cho tác giả chính (nếu có blog)
- [ ] Google Business Profile cập nhật (ảnh thật, mô tả, danh mục đúng)
- [ ] Facebook Page thông tin đầy đủ
- [ ] LinkedIn Company page (nếu B2B)
- [ ] YouTube channel (nếu có video)
- [ ] Review policy: quy trình xin review từ khách hàng
- [ ] (Optional) Wikidata item nếu đủ điều kiện

→ Xem chi tiết tại `checklists/entity-audit.md`
