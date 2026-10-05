# PLAN TRIỂN KHAI WEBSITE HAMACO — HTML / CSS / JS

**Phiên bản:** 1.0  
**Ngày lập:** 05/10/2026  
**Phạm vi:** Lập kế hoạch triển khai giao diện HTML/CSS/JS theo brief thương hiệu HAMACO, ưu tiên mobile-first, tốc độ tải và dữ liệu có nguồn kiểm chứng.

---

## 1. Mục tiêu triển khai

Xây dựng một hệ giao diện corporate website cho HAMACO theo tinh thần điềm đạm, ấm áp, sâu lắng và chân thực. Sự bề thế được thể hiện bằng cấu trúc thông tin rõ ràng, hình ảnh thực địa, dữ liệu minh bạch và trải nghiệm đọc thoải mái; không dùng copy phô trương hoặc hiệu ứng gây chú ý quá mức.

Website phải đáp ứng các mục tiêu sau:

- Giới thiệu HAMACO từ nền tảng miền Tây, lịch sử hình thành, hệ sinh thái Thương mại – Sản xuất – Dịch vụ và mạng lưới đơn vị.
- Hỗ trợ nhà thầu/đối tác tra cứu sản phẩm, quy cách, tiêu chuẩn, catalogue và gửi yêu cầu báo giá nhanh.
- Tổ chức nội dung doanh nghiệp, tuyển dụng, tin tức, thư viện hình ảnh/video và quan hệ cổ đông.
- Dùng chung một Design System cho toàn bộ màn hình, có thể mở rộng danh mục và dữ liệu mà không phá cấu trúc.
- Chạy tốt trên điện thoại 320px trở lên, máy tính bảng, laptop và màn hình lớn; không để bảng kỹ thuật, bản đồ hoặc modal làm vỡ layout.
- HTML semantic, CSS có token, JS module hóa, dễ tích hợp sang CMS/Haravan/API về sau.

> **Lưu ý đếm trang:** Brief ghi “17 trang” nhưng mã màn hình đang có 18 trạng thái: 1, 2, 3A, 3B, 4, 5, 6A, 6B, 7, 8, 9, 10A, 10B, 11, 12, 13, 14, 15. Plan này bao phủ đủ 18 trạng thái được liệt kê. Khi chốt Figma cần xác nhận có gộp 3A/3B, 6A/6B hoặc 10A/10B thành một template dữ liệu hay không.

---

## 2. Nguyên tắc thương hiệu và nội dung

### 2.1. Tinh thần hình ảnh

- Hình ảnh ưu tiên người lao động, bến sông, sà lan, kho, trạm trộn, xe bồn, nhà máy, công trình và không gian thật của HAMACO.
- Hạn chế ảnh stock quá bóng bẩy, ảnh dựng 3D giả lập hoặc bố cục hình học cắt ghép dày đặc.
- Ảnh phải có chú thích, nguồn, ngày chụp hoặc đơn vị liên quan khi đưa vào thư viện.
- Hero dùng một ảnh chủ đạo có lớp phủ navy nhẹ để bảo đảm chữ đọc được; không phủ cam toàn màn hình.

### 2.2. Quy tắc copy

Dùng các động từ và mô tả cụ thể: “cung ứng”, “phân phối”, “sản xuất”, “vận hành”, “đồng hành”, “đáp ứng”, “tra cứu”, “tải tài liệu”.

Không dùng các placeholder hoặc khẩu hiệu mang tính phô trương như: “tự hào”, “đứng đầu”, “số 1”, “vượt trội”, “dẫn đầu tuyệt đối”. Nếu nội dung nguồn bắt buộc có các từ này, phải đưa vào hàng chờ biên tập và xin duyệt trước khi hiển thị.

Copy mẫu phù hợp:

- “Từ Hậu Giang – Cần Thơ, HAMACO bền bỉ đồng hành cùng những công trình và hoạt động sản xuất tại Đồng bằng sông Cửu Long.”
- “Ba trụ cột Thương mại – Sản xuất – Dịch vụ được kết nối bằng hệ thống đơn vị, kho, nhà máy và mạng lưới phân phối.”
- “Tra cứu quy cách, tiêu chuẩn và tài liệu sản phẩm trước khi gửi yêu cầu.”

### 2.3. Phân biệt dữ liệu tĩnh và dữ liệu động

- **Tĩnh theo Design System:** màu, typography, spacing, component, icon, layout.
- **CMS:** sản phẩm, thương hiệu, bài viết, tuyển dụng, catalogue, thư viện, chi nhánh, đơn vị thành viên.
- **API/dịch vụ bên ngoài:** giá cổ phiếu, thời gian giao dịch, bản đồ, email gửi form.
- **Cần duyệt trước khi công bố:** số liệu quy mô, mốc lịch sử, nhân sự lãnh đạo, địa chỉ chi nhánh, chứng nhận và thông tin tài chính.

---

## 3. Dữ liệu HAMACO đã dò và cách dùng

### 3.1. Nguồn chính thức cần làm nguồn chuẩn

1. **Website chính thức:** `https://hamaco.vn/` — tên doanh nghiệp, lịch sử 1976, chuyển đổi thành công ty cổ phần năm 2003, nhóm ngành, thông tin liên hệ và menu nội dung.
2. **Về chúng tôi:** `https://hamaco.vn/ve-chung-toi` — phần giới thiệu và quá trình hình thành.
3. **Lịch sử phát triển:** `https://hamaco.vn/lich-su-phat-trien` — hiện có danh sách HĐQT và Ban Tổng giám đốc; cần bổ sung/duyệt timeline 1976–2026.
4. **Đơn vị thành viên:** `https://hamaco.vn/don-vi-truc-thuoc` — địa chỉ trụ sở, kho, chi nhánh và công ty con.
5. **Danh mục sản phẩm/dịch vụ:** các trang `/thep`, `/xi-mang`, `/lpg`, `/dau-nhon`, `/son`, `/thiet-bi-ve-sinh`, `/be-tong-thuong-pham`, `/bot-da-voi-caco3`, `/be-tong-tron-san`, `/sx-xi-mang`, `/van-tai` và trang cho thuê kho bãi.
6. **Tuyển dụng:** `https://hamaco.vn/tuyen-dung` — vị trí, khu vực, ngành hàng và cách nộp hồ sơ.
7. **Công bố thông tin:** `https://hamaco.vn/cong-bo-thong-tin` — tài liệu cổ đông; cần kiểm tra các iframe/PDF hiện tại trước khi tích hợp.
8. **Tài liệu Đại hội đồng cổ đông 2026:** đường dẫn được website chính thức liên kết là `/tai-lieu-dai-hoi-dong-co-dong-2026`.
9. **Chính sách quyền riêng tư:** `https://hamaco.vn/chinh-sach-quyen-rieng-tu-1120` — dùng làm cơ sở cho checkbox đồng ý trên form.

### 3.2. Dữ liệu đã xác nhận ở mức định hướng

- HAMACO có nguồn gốc từ năm 1976; chuyển đổi thành công ty cổ phần năm 2003.
- Nhóm hoạt động chính trên website hiện tại: **Thương mại** (thép, xi măng, LPG, dầu nhờn, sơn, thiết bị vệ sinh, sản phẩm gia công), **Sản xuất** (bê tông thương phẩm, bê tông trộn sẵn, xi măng, bột đá vôi CaCO₃) và **Dịch vụ** (cho thuê văn phòng/kho bãi, vận tải thủy – bộ).
- Đơn vị/công ty con được website liệt kê gồm HAMACO Petro, HAMACO Vị Thanh, Bê tông HAMACO và Vật liệu xây dựng Xanh HAMACO, cùng các điểm/kho/chi nhánh.
- Trang lịch sử phát triển hiện liệt kê HĐQT gồm ông Lê Hoàng Nam, ông Phạm Ngọc Minh, ông Mai Bảo Ngọc, bà Lâm Thị Trúc Hà, ông Đào Đức Đại; Ban Tổng giám đốc có ông Mai Bảo Ngọc, ông Phạm Văn Hùng và bà Lâm Thị Trúc Hà. Các chức danh phải được xác nhận lại tại thời điểm bàn giao.
- Mã chứng khoán được nguồn VSD ghi nhận là **HAM**, thị trường **UPCoM**, ISIN `VN000000HAM4`, mệnh giá 10.000 đồng/cổ phiếu. Đây là dữ liệu tham chiếu cho IR Hub, không tự xem là dữ liệu giá thời gian thực.

### 3.3. Dữ liệu có mâu thuẫn cần khóa trước khi code nội dung

- Các trang HAMACO hiển thị nhiều bộ số liệu khác nhau về “đơn vị trực thuộc/nhân viên/đại lý” (ví dụ 17+/600+/1000+, 10+/495+/790+, hoặc bộ số nhỏ hơn trên trang tuyển dụng). Không hard-code số liệu vào HTML. Tạo CMS fields `value`, `label`, `as_of`, `source_url`, `status` và chỉ hiển thị bộ được HAMACO duyệt.
- Danh sách đơn vị thành viên có số thứ tự thiếu và một số địa danh/địa chỉ cần đối soát theo địa giới hành chính mới. Không tự sửa địa chỉ từ nguồn tìm kiếm.
- Các trang “Bê tông thương phẩm” và “Vận tải hàng hóa Thủy - Bộ” hiện ghi “Nội dung đang được cập nhật”. Không viết thêm năng lực, công suất, chứng nhận hoặc đội xe nếu chưa nhận tài liệu từ HAMACO.
- Timeline 1976–2026 trong brief là yêu cầu thiết kế; nguồn hiện có chưa cung cấp đủ các mốc trung gian. Cần bảng mốc có năm, sự kiện, địa danh, ảnh, nguồn và người duyệt.
- Chứng nhận CQ, tiêu chuẩn xuất xưởng, quy cách thép/xi măng/bê tông và thông số sản phẩm phải lấy từ catalogue/CQ chính thức theo từng SKU.

### 3.4. Nguồn dữ liệu ngoài cho IR

- Dùng VSD/HOSE/HNX hoặc nguồn cung cấp dữ liệu được HAMACO chỉ định để xác nhận thông báo cổ đông.
- Nếu hiển thị giá HAM, phải ghi thời gian cập nhật, đơn vị dữ liệu, trạng thái “trễ dữ liệu” nếu có và liên kết nguồn. Không tự gọi scraping không được cấp phép.
- Nếu chưa có API chính thức, dùng widget tĩnh với nút “Xem dữ liệu thị trường” và thông báo rõ dữ liệu không phải khuyến nghị đầu tư.

---

## 4. Kiến trúc thông tin và danh sách màn hình

### 4.1. Điều hướng chính

- Trang chủ
- Về HAMACO
  - Về chúng tôi
  - Lịch sử phát triển
  - Tầm nhìn – sứ mệnh
  - Đơn vị thành viên
- Lĩnh vực hoạt động
  - Thương mại
  - Sản xuất
  - Dịch vụ
- Sản phẩm
- Nhà máy & dịch vụ
- Catalogue & tài liệu
- Truyền thông
  - Tin tức
  - Hoạt động doanh nghiệp
  - Hình ảnh
  - Phim tư liệu
  - Nhà cung cấp/VAS
- Quan hệ cổ đông
  - Công bố thông tin
  - Tài liệu ĐHĐCĐ
  - Báo cáo tài chính
  - Báo cáo thường niên
  - Nghị quyết
- Tuyển dụng
- Liên hệ / Gửi yêu cầu báo giá

### 4.2. Mapping các màn hình trong brief

| Mã | Màn hình đề xuất | Nội dung chính | Tương tác HTML/CSS/JS |
|---|---|---|---|
| 1 | Trang chủ | Hero thực địa, 3 trụ cột, số liệu đã duyệt, hoạt động, đơn vị, tin mới, CTA | Header sticky, slider nhẹ, reveal, counter có fallback |
| 2 | Về HAMACO | Giới thiệu, lịch sử, timeline 1976–2026, giá trị, sơ đồ tổ chức | Timeline ngang/dọc, tabs, cây tổ chức responsive |
| 3A | Tuyển dụng listing | Vị trí, khu vực, ngành hàng, trạng thái tuyển | Search/filter, accordion mobile, pagination |
| 3B | Chi tiết tuyển dụng | Mô tả, yêu cầu, quyền lợi, hồ sơ, form ứng tuyển | Accordion, upload CV, validation, trạng thái gửi |
| 4 | Danh mục sản phẩm | Bộ lọc ngành hàng, thương hiệu, quy cách, ứng dụng | Filter không reload, URL query, empty state |
| 5 | Chi tiết sản phẩm | Gallery, thông số, tiêu chuẩn/CQ, ứng dụng, catalogue, hỏi giá | Tabs, bảng kỹ thuật, lightbox, tải 1 chạm |
| 6A | Nhà máy & năng lực sản xuất | Bê tông, xi măng, bột đá vôi, cọc/cấu kiện nếu được duyệt | Card theo cơ sở, sơ đồ quy trình, gallery |
| 6B | Dịch vụ vận tải/kho bãi | Vận tải thủy – bộ, kho, địa điểm, quy trình yêu cầu | Map/list, CTA báo giá, bảng năng lực có nguồn |
| 7 | Catalogue & thư viện tài liệu | Catalogue, CQ mẫu, hồ sơ năng lực, biểu mẫu | Filter loại/năm, download 1 chạm, file metadata |
| 8 | Liên hệ & mạng lưới | Trụ sở, chi nhánh, kho, nhà máy, bản đồ khu vực | Map markers, list đồng bộ, copy địa chỉ, gọi điện |
| 9 | Báo giá / yêu cầu tư vấn | Chọn nhóm sản phẩm, quy cách, khối lượng, địa điểm, thời gian | Multi-step form, validation, privacy consent, success state |
| 10A | Tin tức / hoạt động listing | Danh sách bài, nhóm nội dung, tìm kiếm | Filter/tag, pagination, lazy images |
| 10B | Bài viết chi tiết | Editorial article, ảnh, trích dẫn, tài liệu liên quan | TOC, share, lightbox, related content |
| 11 | Thư viện hình ảnh | Album theo dự án/đơn vị/năm | Masonry có fallback grid, lightbox, keyboard |
| 12 | Phim tư liệu / video | Video nhà máy, lịch sử, con người | Poster, modal, transcript/caption, reduced-motion |
| 13 | Nhà cung cấp / đối tác | VAS và các nhà cung cấp theo ngành hàng | Logo grid, hồ sơ, bộ lọc; chỉ dùng logo được phép |
| 14 | IR Hub tổng quan | Mã HAM, thông tin cổ đông, giá tham chiếu, chỉ số tóm tắt | Widget gọn, timestamp, trạng thái nguồn |
| 15 | Công bố thông tin & tài chính | BCTC, báo cáo thường niên, nghị quyết, ĐHĐCĐ | Table/filter theo năm, tải PDF, phân nhóm rõ ràng |

---

## 5. Design System đề xuất

### 5.1. Color tokens

```css
:root {
  --hamaco-navy: #1B3A6B;
  --hamaco-deep-navy: #102A4C;
  --hamaco-orange: #F5A623;
  --hamaco-orange-dark: #C77B00;
  --hamaco-cream: #FAF9F6;
  --hamaco-warm-gray: #F1F0EC;
  --hamaco-border: #D9D8D2;
  --hamaco-text: #1D2733;
  --hamaco-muted: #667085;
  --hamaco-success: #2F7D5B;
  --hamaco-danger: #B54747;
  --hamaco-white: #FFFFFF;
}
```

Quy tắc sử dụng:

- Navy cho header, heading chính, footer, IR và nền khối dữ liệu.
- Cam chỉ dùng cho CTA chính, focus/active state, icon, số nhấn và line dẫn hướng; không dùng làm nền lớn liên tục.
- Cream/warm gray làm nền section để giảm cảm giác “xi măng” và tạo khoảng thở.
- Text phải đạt tương phản WCAG AA. Kiểm tra riêng chữ trắng trên cam và chữ muted trên cream.

### 5.2. Typography

- Font ưu tiên: `Inter` hoặc `Be Vietnam Pro`; tải bằng `font-display: swap`, chỉ dùng weight cần thiết 400/500/600/700.
- Body desktop 16–18px, line-height 1.6–1.75; mobile 15–16px.
- H1 dùng 40–64px tùy breakpoint, weight 600–700; không viết hoa toàn bộ đoạn dài.
- H2/H3 dùng 28–40px và 20–28px; bảng kỹ thuật 14–15px với line-height đủ thoáng.
- Số liệu lớn dùng weight 600, tracking vừa phải; không làm số quá dày hoặc hiệu ứng đếm gây giật.

### 5.3. Grid và khoảng cách

- Container max-width 1200–1280px; mobile padding 20px, tablet 32px, desktop 48px.
- Grid 4/8/12 cột tùy breakpoint; không ép mọi section vào card dày.
- Spacing token theo bội số 4: 4, 8, 12, 16, 24, 32, 48, 64, 80, 120px.
- Section desktop 96–144px; mobile 56–80px.
- Card có border mảnh và nền trong/cream; box-shadow rất nhẹ hoặc bỏ hẳn.

### 5.4. Component bắt buộc

Header, mobile drawer, breadcrumb, hero, section heading, CTA button, link arrow, stat card, product card, filter bar, chips, data table, tabs, accordion, timeline, org chart, branch list, map panel, document row, article card, gallery tile, video modal, form field, stepper, toast, empty state, loading skeleton, footer.

Mỗi component phải có:

- trạng thái default/hover/focus/active/disabled/loading/error;
- phiên bản mobile;
- `aria-label`, `aria-expanded`, `aria-controls` khi có tương tác;
- focus ring dễ nhìn;
- không phụ thuộc màu sắc duy nhất để truyền đạt trạng thái.

---

## 6. Chuẩn HTML/CSS/JS

### 6.1. Cấu trúc thư mục đề xuất

```text
hamaco-web/
├── index.html
├── pages/
│   ├── about.html
│   ├── products.html
│   ├── product-detail.html
│   ├── careers.html
│   ├── news.html
│   ├── article.html
│   ├── gallery.html
│   ├── videos.html
│   ├── ir.html
│   ├── disclosures.html
│   └── contact.html
├── assets/
│   ├── images/
│   ├── icons/
│   ├── documents/
│   └── fonts/
├── css/
│   ├── tokens.css
│   ├── reset.css
│   ├── base.css
│   ├── layout.css
│   ├── components.css
│   ├── pages.css
│   └── utilities.css
├── js/
│   ├── app.js
│   ├── components/
│   ├── modules/
│   ├── data/
│   └── utils/
└── data/
    ├── products.json
    ├── branches.json
    ├── documents.json
    ├── jobs.json
    └── timeline.json
```

Nếu tích hợp Haravan/CMS, giữ nguyên mô hình component và chuyển các file JSON thành nguồn Liquid/API; không đưa dữ liệu quản trị vào JS hard-code.

### 6.2. JavaScript modules

- `header.js`: sticky header, drawer, escape, focus trap.
- `filter.js`: lọc sản phẩm/tài liệu/tin/tuyển dụng, đồng bộ query string.
- `tabs.js`, `accordion.js`: keyboard support và `aria`.
- `timeline.js`: chuyển trạng thái mốc, hỗ trợ swipe mobile.
- `org-chart.js`: mở/đóng nhánh, không phụ thuộc hover trên mobile.
- `gallery.js`, `video-modal.js`: lightbox, focus trap, preload poster.
- `map.js`: marker/list sync; lazy load bản đồ chỉ khi section vào viewport.
- `form.js`: validate, chống submit lặp, trạng thái sending/success/error.
- `ir-widget.js`: render timestamp, giá/khối lượng từ API được cấp phép, fallback tĩnh.
- `performance.js`: lazy image observer, resource hints và đo lỗi runtime.

### 6.3. Không dùng

- Không dùng jQuery hoặc thư viện slider nặng nếu native CSS/JS đủ đáp ứng.
- Không autoplay video có âm thanh.
- Không dùng hiệu ứng parallax nặng, particle, scroll-jacking, zoom card quá mức.
- Không chèn inline script lặp lại trên từng trang.

---

## 7. Chi tiết UX theo nhóm trang

### 7.1. Trang chủ và Về HAMACO

- Hero có headline ngắn, một CTA “Khám phá HAMACO” và một CTA “Gửi yêu cầu”.
- Section 3 trụ cột hiển thị bằng số thứ tự/line mảnh, mỗi trụ có ảnh và nội dung 2–3 dòng.
- Timeline dùng một đường navy mảnh, điểm mốc cam; desktop có thể chạy ngang, mobile chuyển dọc.
- Sơ đồ tổ chức dùng cây top-down: HĐQT → Ban Tổng giám đốc → các đơn vị cốt lõi. Mobile hiển thị từng nhánh dạng accordion.
- Số liệu có nhãn “Cập nhật đến [thời điểm]” và nguồn nội bộ/CMS.

### 7.2. Sản phẩm, nhà máy và dịch vụ

- Bộ lọc nằm trên đầu danh sách, mobile mở thành bottom sheet hoặc accordion.
- Lọc theo ngành hàng, thương hiệu, quy cách, tiêu chuẩn, địa bàn; có nút xóa toàn bộ.
- Không reload toàn trang khi lọc; cập nhật URL để chia sẻ được.
- Bảng kỹ thuật desktop có cột cố định; mobile chuyển thành key-value rows hoặc bảng cuộn ngang có chỉ báo “Vuốt để xem thêm”.
- CQ/catalogue hiển thị loại file, dung lượng, ngày cập nhật, ngôn ngữ và nút tải.
- Nội dung năng lực nhà máy chỉ hiển thị khi có tài liệu nguồn; phần thiếu dữ liệu dùng trạng thái “Đang cập nhật” có chủ đích.

### 7.3. IR Hub

- Header IR có màu navy sâu và breadcrumb rõ.
- Widget giá chỉ hiển thị các trường cần thiết: mã HAM, giá gần nhất, thay đổi, thời gian cập nhật, nguồn.
- Tài liệu chia tab hoặc filter: BCTC, thường niên, nghị quyết, ĐHĐCĐ, quản trị.
- Table có header sticky, sort/filter; mobile chuyển thành danh sách tài liệu hoặc bảng cuộn ngang.
- Luôn có chú thích dữ liệu thị trường và liên kết nguồn; không đưa biểu đồ rối nếu không có nhu cầu phân tích.

### 7.4. Truyền thông và thư viện

- Editorial width 720–780px cho bài đọc; ảnh rộng có caption.
- Blockquote dùng line cam mảnh và nền cream, không dùng chữ in hoa dày.
- Gallery có filter album và lightbox hỗ trợ phím mũi tên/Escape.
- Video có poster tối ưu, transcript/caption nếu có; tôn trọng `prefers-reduced-motion`.

### 7.5. Tuyển dụng, liên hệ và báo giá

- Job listing hiển thị rõ địa bàn, ngành hàng, loại công việc và hạn nhận hồ sơ.
- Form báo giá chia 2–3 bước: nhu cầu → thông tin liên hệ → xác nhận. Không bắt nhập lại thông tin.
- Trường bắt buộc có nhãn rõ, lỗi hiển thị cạnh trường, không chỉ dùng màu đỏ.
- Checkbox đồng ý chính sách liên kết tới Privacy Policy hiện hành của HAMACO.
- Branch map có list thay thế khi bản đồ không tải; nút gọi điện/email trên mobile.

---

## 8. Mobile-first, responsive và hiệu năng

### 8.1. Breakpoint

- 320–479px: mobile nhỏ.
- 480–767px: mobile lớn.
- 768–1023px: tablet.
- 1024–1279px: laptop.
- 1280px trở lên: desktop rộng.

Thiết kế từ mobile trước: nội dung một cột, CTA full-width vừa phải, bảng chuyển dạng đọc nhanh, drawer thay mega menu, bản đồ có list fallback. Sau đó mở rộng sang grid desktop.

### 8.2. Ảnh và tài nguyên

- Dùng AVIF/WebP, `srcset`, `sizes`, `width/height` cố định để chống CLS.
- Hero dùng preload một ảnh duy nhất; các ảnh dưới fold lazy-load.
- Ảnh card mục tiêu dưới 150–250KB; ảnh hero tối ưu theo viewport.
- SVG icon inline hoặc sprite nhẹ; tránh tải bộ icon font lớn.
- Font chỉ tải weight cần thiết, có fallback system.
- CSS critical cho header/hero; defer JS không cần cho first paint.
- Không load bản đồ, video player hoặc widget IR trước khi người dùng tới section.

### 8.3. Chỉ tiêu QA hiệu năng

- LCP mục tiêu mobile ≤ 2.5s trên trang chủ với ảnh đã tối ưu.
- CLS < 0.1; mọi ảnh/video/iframe có kích thước giữ chỗ.
- INP mục tiêu < 200ms ở thao tác lọc, accordion, modal.
- JavaScript initial payload nhỏ, không bundle thư viện không dùng.
- Kiểm tra Lighthouse mobile/desktop, WebPageTest hoặc PSI trên trang đại diện.

---

## 9. SEO, accessibility và bảo mật form

- Mỗi trang có `title`, meta description, canonical, Open Graph, breadcrumb và heading duy nhất.
- Product dùng Product/Organization/Breadcrumb schema khi dữ liệu đủ; Article dùng Article schema; tuyển dụng dùng JobPosting khi có trường hợp lệ.
- Không tạo schema từ số liệu placeholder hoặc thông tin chưa duyệt.
- Ảnh có alt theo ngữ cảnh; ảnh trang trí dùng alt rỗng.
- Tab/accordion/modal thao tác được bằng bàn phím; focus không bị mất sau khi đóng modal.
- Đảm bảo trạng thái loading/error/empty có nội dung văn bản.
- Form có CSRF/rate limit ở backend, honeypot hoặc captcha theo yêu cầu; không lưu CV/thông tin nhạy cảm ở localStorage.
- Escape HTML của dữ liệu CMS/API; kiểm soát MIME và kích thước file upload.
- Chính sách quyền riêng tư, thời hạn lưu dữ liệu và người nhận form phải được HAMACO xác nhận.

---

## 10. Kế hoạch triển khai theo phase

### Phase 0 — Chốt dữ liệu và phạm vi

- Xác nhận 17 hay 18 màn hình; xác nhận template gộp.
- Nhận logo vector, brand guideline, ảnh/video gốc, catalogue, CQ, tài liệu cổ đông, danh sách chi nhánh và timeline.
- Lập data dictionary: tên trường, kiểu dữ liệu, bắt buộc/không bắt buộc, nguồn, ngày cập nhật, người duyệt.
- Chốt số liệu thống kê và mốc nhân sự/lịch sử.

**Đầu ra:** sitemap đã duyệt, content matrix, asset checklist, danh sách rủi ro dữ liệu.

### Phase 1 — Design System và khung HTML

- Tạo token màu, type scale, spacing, grid, container.
- Dựng header/footer, breadcrumb, button, form, table, card, modal, accordion.
- Tạo page shell cho mobile/tablet/desktop.
- Kiểm tra typography tiếng Việt, logo và contrast.

**Đầu ra:** bộ component HTML/CSS có trạng thái và trang style guide nội bộ.

### Phase 2 — Nhóm trang nền tảng

- Trang chủ, Về HAMACO, timeline, sơ đồ tổ chức.
- Header responsive, menu drawer, footer, các CTA dùng chung.
- Dữ liệu mẫu phải có cờ `demo` để không nhầm là số liệu thật.

### Phase 3 — Sản phẩm, sản xuất và dịch vụ

- Listing/filter sản phẩm.
- Chi tiết sản phẩm, bảng thông số, CQ/catalogue.
- Nhà máy, dịch vụ, kho bãi, vận tải.
- Test bảng kỹ thuật trên mobile và các trạng thái không có dữ liệu.

### Phase 4 — Tài liệu, truyền thông, thư viện

- Catalogue/document list tải 1 chạm.
- Tin tức listing/detail, editorial layout.
- Gallery/lightbox, video modal/transcript.
- Nhà cung cấp/đối tác và quyền sử dụng logo.

### Phase 5 — Tuyển dụng, liên hệ, báo giá và IR

- Listing/detail tuyển dụng, nộp hồ sơ.
- Branch map/list, contact form, quote wizard.
- IR Hub, bảng công bố thông tin, PDF filters, stock widget fallback/API.

### Phase 6 — Tích hợp CMS/API và nội dung thật

- Thay JSON demo bằng nguồn CMS/Liquid/API.
- Mapping sản phẩm, chi nhánh, tài liệu, bài viết, job, cổ đông.
- Kiểm soát cache, lỗi API, empty state, retry và timestamp.
- Nhập nội dung đã duyệt, rà soát bản quyền ảnh/tài liệu.

### Phase 7 — Tối ưu, kiểm thử và bàn giao

- Tối ưu ảnh/font/JS/CSS, đo Lighthouse/PSI.
- Accessibility keyboard/screen reader cơ bản.
- Cross-browser Chrome, Safari, Firefox, Edge; iOS Safari và Android Chrome.
- Bàn giao source, data schema, component guide, content guide và checklist vận hành.

---

## 11. QA checklist bắt buộc

### 11.1. Visual/UI

- So khớp Figma ở mobile 320/360/390/414px, tablet 768/834px, desktop 1280/1440px.
- Không tràn chữ tiếng Việt, không vỡ logo, không cắt mất ảnh chủ thể.
- Kiểm tra nền cream/navy, cam CTA, border, focus, hover và active.
- Không có section quá dày; spacing giữa heading, body, card và CTA nhất quán.

### 11.2. Chức năng

- Menu desktop/mobile, breadcrumb, filter, query string, pagination.
- Tabs/accordion/modal/lightbox/video/map.
- Tải tài liệu 1 chạm; link hỏng, file thiếu và file lớn phải có trạng thái rõ.
- Form validation, gửi thành công/thất bại, chống submit nhiều lần, upload CV.
- Bảng kỹ thuật và bảng IR xem được trên mobile.

### 11.3. Dữ liệu

- Mỗi số liệu có `as_of` và nguồn.
- Kiểm tra tên công ty, chức danh, địa chỉ, số điện thoại, email, tên sản phẩm, thương hiệu.
- Không hiển thị số liệu mâu thuẫn cùng lúc.
- Kiểm tra PDF/CQ/catalogue đúng sản phẩm, đúng phiên bản.

### 11.4. SEO/accessibility

- Heading hierarchy, title/meta/canonical, sitemap/link nội bộ.
- Alt ảnh, label form, keyboard, focus trap, reduced motion.
- Schema không lỗi và không chứa placeholder.
- Không có console error, broken image, mixed content hoặc link `#` không xử lý.

### 11.5. Performance

- Lighthouse/PSI mobile và desktop trên: home, product listing, product detail, article list/detail, IR, contact.
- LCP/CLS/INP; dung lượng ảnh; số request; JS/CSS blocking.
- Kiểm tra trên 4G throttling và thiết bị iPhone Safari.

### 11.6. Nội dung và pháp lý

- Copy không chứa khẩu hiệu bị loại trừ.
- Ảnh/video/logo có quyền sử dụng và caption/credit khi cần.
- Form có privacy consent; IR có disclaimer dữ liệu thị trường.
- Tài liệu cổ đông và báo cáo có ngày công bố rõ.

---

## 12. Tiêu chí nghiệm thu

1. Đủ các template/màn hình đã chốt trong sitemap; các trạng thái gộp phải được ghi rõ.
2. Responsive hoàn chỉnh từ 320px tới desktop rộng, không vỡ bảng, modal, map, menu hoặc form.
3. Design System dùng chung, không phát sinh màu/font/spacing tùy tiện ở từng trang.
4. Dữ liệu thật chỉ được hiển thị sau khi có nguồn và người duyệt; dữ liệu thiếu phải có trạng thái minh bạch.
5. Filter, tabs, accordion, lightbox, video, download, map, form và IR fallback hoạt động đúng.
6. Không có lỗi console nghiêm trọng, lỗi encoding UTF-8, link hỏng hoặc ảnh không có kích thước giữ chỗ.
7. Đạt checklist hiệu năng, accessibility, SEO và bảo mật form trong mục QA.
8. Bàn giao gồm source HTML/CSS/JS, asset đã tối ưu, data dictionary, component guide, content mapping, hướng dẫn cập nhật và báo cáo QA.

---

## 13. Việc HAMACO cần cung cấp trước khi bắt đầu code

- Logo SVG/PNG chuẩn, quy định sử dụng logo và logo các công ty thành viên.
- Bộ ảnh/video gốc có quyền sử dụng; thông tin ảnh, địa điểm, ngày chụp, nhân vật.
- Timeline 1976–2026 đã duyệt, ảnh/mốc tương ứng.
- Sơ đồ tổ chức hiện hành và danh sách chức danh cần công bố.
- Danh mục SKU, quy cách, bảng thông số, CQ, catalogue và tiêu chuẩn từng nhóm.
- Danh sách nhà máy/kho/chi nhánh, địa chỉ, tọa độ, hotline, giờ làm việc, người liên hệ.
- Hồ sơ cổ đông, BCTC, báo cáo thường niên, nghị quyết, tài liệu ĐHĐCĐ và quy tắc cập nhật.
- API hoặc nguồn dữ liệu giá HAM nếu muốn hiển thị giá gần thời gian thực.
- Quy trình nhận báo giá, email nhận form, SLA phản hồi, chính sách bảo mật và thời hạn lưu dữ liệu.
- Tài khoản/quyền truy cập CMS, hosting, analytics và công cụ đo hiệu năng.

---

## 14. Kết luận triển khai

Trình tự đúng là **khóa dữ liệu và sitemap → dựng Design System → làm component dùng chung → triển khai từng cụm trang → tích hợp dữ liệu thật → QA responsive, nội dung, hiệu năng và accessibility → bàn giao**. Không nên bắt đầu bằng việc nhồi toàn bộ danh mục kỹ thuật vào HTML trước khi có data dictionary và người duyệt, vì đó là nguyên nhân dễ tạo nội dung sai, bảng vỡ và phải sửa lặp lại.
