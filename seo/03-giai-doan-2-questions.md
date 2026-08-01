# 03. Giai Đoạn 2 — Bộ Câu Hỏi & Query Fan-out

> Đây là bước xác định BẠN sẽ tối ưu cho câu hỏi nào. Làm đúng bước này → mọi nội dung sau mới có hướng.

---

## Fan-out là gì — hiểu để làm đúng

**Fan-out** = cơ chế AI Mode phân rã một câu hỏi phức thành **nhiều truy vấn con** chạy song song, rồi tổng hợp câu trả lời.

### Ví dụ thực tế

```
Câu hỏi gốc: "nên thuê đơn vị nào tối ưu PageSpeed Haravan"

AI tự sinh các truy vấn con:
├── Chi phí tối ưu PageSpeed Haravan là bao nhiêu?
├── Tiêu chí chọn đơn vị tối ưu tốc độ website
├── Có bảo hành sau khi tối ưu không?
├── Rủi ro khi thuê ngoài tối ưu theme Haravan
├── Mất bao lâu để tối ưu xong?
├── Review đơn vị X có uy tín không?
└── Tự tối ưu hay thuê ngoài — cái nào tốt hơn?
```

**Trang thắng** = trang trả lời được **nhiều nhánh con** trong cùng một chỗ.

### Chiến lược nội dung từ fan-out

```
❌ Sai: Mỗi nhánh con = 1 bài mỏng riêng biệt
✅ Đúng: 1 trang trụ cột phủ trọn cụm nhánh + trang con chi tiết nếu cần
```

---

## Nguồn khai thác câu hỏi thật (không tự nghĩ)

### 1. Google (miễn phí, chất lượng cao)
```
- Google Autocomplete: gõ từ khóa → xem gợi ý
- People Also Ask (PAA): click mở rộng từng câu → câu tiếp tục xuất hiện
- "Câu hỏi liên quan" ở cuối AI Overview
- "Tìm kiếm liên quan" ở cuối trang kết quả
```

### 2. Search Console (dữ liệu của chính bạn — quý nhất)
```
Filter: Query chứa: cách, là gì, nên, có, tại sao, bao nhiêu, ở đâu, như thế nào
→ Đây là câu hỏi khách thật đang tìm và ĐÃ VÀO site bạn
→ Ưu tiên cao nhất — đang có traffic, chỉ cần cải thiện content
```

### 3. Log chat / tổng đài / inbox sales
```
Câu hỏi trước khi mua = giá trị kinh doanh cao nhất
Ví dụ: "size này có vừa với chân rộng không?" → bài tư vấn chọn size
Cách thu thập: xin export log từ bộ phận sales mỗi tháng
```

### 4. Cộng đồng VN (AI ngày càng trích UGC)
```
- Facebook group ngành: tìm câu hỏi được nhiều bình luận
- Forum: Voz, Otofun, Reddit (r/Vietnam)
- Shopee/Lazada Q&A: câu hỏi mua hàng thật
- Google Maps reviews: "nhưng tôi thắc mắc..."
```

### 5. Hỏi thẳng AI
```
Prompt: "Tôi bán [sản phẩm X]. Khách hàng thường hỏi những câu gì trước khi mua? 
Liệt kê 20 câu hỏi theo từng giai đoạn: nhận biết → cân nhắc → quyết định."

→ AI sẽ tự bung thêm nhiều nhánh bạn chưa nghĩ tới
→ Dùng để brainstorm, không phải làm xong
```

---

## Ma trận ưu tiên câu hỏi

> Chấm mỗi câu theo 2 trục. Làm ô **"giá trị cao + dễ thắng"** trước.

### Trục X: Giá trị kinh doanh
```
Cao  = gần quyết định mua (so sánh, giá, review, tư vấn chọn)
Thấp = xa quyết định mua (định nghĩa, khái niệm chung)
```

### Trục Y: Khả năng thắng
```
Cao  = đã rank / có dữ liệu gốc / đối thủ yếu / có case study thật
Thấp = chưa có trang / đối thủ mạnh / cần nhiều E-E-A-T
```

### Ma trận 2×2

```
                    Dễ thắng    Khó thắng
Giá trị cao    │  ✅ LÀM NGAY  │  📋 Lên kế hoạch  │
Giá trị thấp   │  ⏸ Để sau    │  ❌ Bỏ qua        │
```

**Làm theo thứ tự:** ✅ → 📋 → ⏸ → bỏ qua ❌

---

## Format file câu hỏi (30–50 câu)

> Lưu vào: `seo/data/question-matrix.csv` hoặc Google Sheets

| # | Câu hỏi | Intent | Giai đoạn mua | Nhánh fan-out | Điểm giá trị (1-5) | Điểm dễ thắng (1-5) | Tổng | Trang đích |
|---|---------|--------|--------------|--------------|---------------------|---------------------|------|-----------|
| 1 | | Informational / Commercial / Transactional | Nhận biết / Cân nhắc / Quyết định | [liệt kê 3-5 nhánh] | | | | |
| 2 | | | | | | | | |

→ Xem template đầy đủ tại `templates/question-matrix.md`

---

## Quy tắc chọn câu hỏi

✅ **Nên chọn:**
- Câu hỏi khách hàng thật đang tìm (có trong Search Console)
- Câu hỏi gần quyết định mua
- Câu hỏi bạn có dữ liệu gốc / case study thật để trả lời
- Câu hỏi đối thủ AI đang trả lời kém / bỏ sót

❌ **Không nên:**
- Câu hỏi quá rộng (khó thắng với DA thấp)
- Câu hỏi chỉ có Wikipedia/báo lớn mới trả lời được
- Câu hỏi không liên quan ngành
- Câu hỏi bạn không có gì khác biệt để nói

---

## Kết quả bàn giao của Giai đoạn 2

- [ ] File 30–50 câu hỏi theo format trên
- [ ] Mỗi câu có: intent, nhánh fan-out, điểm ưu tiên, trang đích dự kiến
- [ ] Top 10 câu ưu tiên cao nhất → chuyển sang Giai đoạn 3 để viết nội dung
