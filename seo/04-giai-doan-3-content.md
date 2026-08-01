# 04. Giai Đoạn 3 — Cấu Trúc Nội Dung cho AI + Người Đọc

> Nội dung tốt = người đọc hiểu + AI trích được. Hai yêu cầu này **không mâu thuẫn** — cùng nguyên tắc viết rõ ràng.

---

## Khung nội dung: Trụ cột + Trang chuyên sâu

### Cấu trúc Topic Cluster

```
Trang trụ cột (Pillar Page)
├── Phủ rộng toàn bộ chủ đề
├── Link tới các trang con
├── ~2000-4000 từ
└── Trả lời được nhiều nhánh fan-out của câu hỏi chính

    Trang con chuyên sâu (Supporting Page)
    ├── Đi sâu vào 1 khía cạnh cụ thể
    ├── Link ngược lại trang trụ cột
    └── 800-1500 từ
```

### Nguyên tắc internal linking (tín hiệu topical authority)
- Trang trụ cột ↔ trang con: **link 2 chiều**
- Anchor text mô tả đúng chủ đề (không dùng "click here", "xem thêm")
- Mỗi trang con trong cụm phải link về trụ cột
- Google dùng internal link pattern để hiểu bạn phủ trọn một chủ đề

---

## 5 Nguyên tắc "Trích xuất được" (Extractability)

> Đây là điều AI thực sự cần để trích nội dung của bạn.

### 1. Answer-First
```
❌ Sai:
H1: Hướng dẫn chọn giày chạy bộ
[3 đoạn giới thiệu lịch sử, tại sao giày quan trọng...]
[Đến đoạn 4 mới nói cách chọn]

✅ Đúng:
H1: Hướng dẫn chọn giày chạy bộ phù hợp
[Ngay dưới H1]: Để chọn giày chạy bộ phù hợp, cần xem xét 3 yếu tố: 
loại vòm bàn chân, bề mặt chạy, và quãng đường trung bình mỗi tuần. 
Sau đây là cách đánh giá từng yếu tố...
```

AI hay lấy nguyên đoạn answer-first này. Viết nó như thể bạn đang trả lời câu hỏi trực tiếp.

### 2. Tự chứa ngữ cảnh
```
❌ Sai: "Như đã nói ở phần trên, điều quan trọng nhất là..."
         "Theo phân tích ban đầu, chúng ta thấy..."

✅ Đúng: Mỗi đoạn đọc độc lập vẫn có đủ ngữ cảnh
          "Khi chọn giày theo loại vòm bàn chân: vòm thấp (flat foot) 
          cần giày hỗ trợ motion control, vòm trung cần giày stability..."
```

AI trích lẻ từng đoạn — đoạn nào tự chứa nghĩa thì được trích, đoạn phụ thuộc ngữ cảnh thì không.

### 3. Một ý — một chỗ
```
❌ Sai: Câu trả lời "giá bao nhiêu" rải rác ở đoạn 2, đoạn 5, và sidebar
✅ Đúng: Thông tin giá tập trung tại 1 section rõ ràng, có heading
```

### 4. Heading dạng câu hỏi → trả lời ngay dưới
```
✅ Đúng:
## Giày chạy bộ nam nên chọn size thế nào?
Giày chạy bộ nên lớn hơn giày thường 0.5–1 size. Lý do: bàn chân phình ra khi chạy.
Cách đo: [hướng dẫn cụ thể]...
```

### 5. Không có "độ dài lý tưởng" — Google xác nhận
```
Viết đủ để trả lời câu hỏi. Không ép dài, không cắt ngắn.
Bài ngắn 500 từ nếu trả lời đầy đủ = tốt hơn bài dài 3000 từ nhưng lan man.
```

---

## Cấu trúc bài viết chuẩn (giữ nguyên từ plan gốc — đã đúng)

```
H1: [Tiêu đề chứa câu hỏi chính / từ khóa chính]
│
├── [Đoạn answer-first: 2-3 câu, trả lời trực tiếp, tự chứa nghĩa]
│
├── H2: [Câu hỏi con thứ nhất]
│   └── Trả lời ngay, đoạn tự chứa
│
├── H2: [Câu hỏi con thứ hai]  
│   └── Trả lời ngay, đoạn tự chứa
│
├── H2: So sánh / Ví dụ thực tế / Case study
│   └── [Dữ liệu gốc nếu có — đây là phần AI khó bịa]
│
├── H2: Câu hỏi thường gặp (FAQ)
│   ├── Q: [câu hỏi viết đúng như khách hỏi]
│   │   A: [trả lời ngắn, tự chứa]
│   └── Q: ...
│
└── [CTA / Bước tiếp theo]
```

---

## Internal linking — thực hiện cụ thể

### Khi viết trang trụ cột
- Liệt kê tất cả trang con trong cụm → link tới từng trang
- Anchor text: dùng từ khóa mô tả đúng (VD: "hướng dẫn chọn size giày chạy bộ", không phải "xem thêm")

### Khi viết trang con
- Bắt buộc có link ngược về trang trụ cột
- Có thể link sang trang con liên quan khác trong cụm

### Công thức kiểm tra
```
Trang trụ cột → link tới N trang con: ✅
Mỗi trang con → link ngược trang trụ cột: ✅
Anchor text mô tả đúng chủ đề: ✅
Không orphan page (không trang nào bị bỏ lại không link): ✅
```

---

## Những gì KHÔNG làm với nội dung

❌ Ép thêm "khối AI" (AI answer box) ngắn nhân tạo — không cần  
❌ Viết bài dài cố tình để "trông authority" — nếu rỗng thì phản tác dụng  
❌ Nhồi từ khóa — AI đọc semantic, không đếm từ khóa  
❌ Mỗi H2 một keyword khác nhau không liên quan — loãng topical authority  

---

## Kết quả bàn giao Giai đoạn 3

- [ ] Topic cluster map (trang trụ cột + danh sách trang con cho mỗi cụm)
- [ ] Brief nội dung cho top 5 trang ưu tiên (xem `templates/content-brief.md`)
- [ ] Internal linking plan (trang nào link tới trang nào, anchor text gì)
