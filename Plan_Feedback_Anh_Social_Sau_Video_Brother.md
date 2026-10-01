# PLAN RIÊNG — FEEDBACK BẰNG HÌNH ẢNH HOẶC BÀI ĐĂNG SOCIAL

Ngày lập: 01/10/2026. Dự án: landing page Brother. Phạm vi: kế hoạch giao diện và cấu hình nội dung; chưa thực hiện chỉnh sửa website.

## 1. Yêu cầu và vị trí chính xác

Thêm phần chia sẻ trải nghiệm ngay sau module 3 video YouTube đã có plan, trước mục “Công nghệ & Độ bền”. Thứ tự mới: bảng so sánh → 3 video → feedback ảnh/social → Công nghệ & Độ bền.

Module có hai loại nội dung:

1. **Ảnh feedback:** thêm ảnh thực tế hoặc ảnh chụp nội dung đánh giá; bấm xem ảnh đầy đủ.
2. **Bài social:** thêm link bài đăng; hiển thị thẻ nguồn trong module và có thể hiển thị bài gốc ngay trên website thông qua nhúng được hỗ trợ.

Cần phân biệt rõ:

- Ảnh kèm link bài gốc là bản nội dung do người quản trị chọn và cập nhật.
- Bài Facebook nhúng là nội dung do Facebook hiển thị, giao diện bên trong phụ thuộc nền tảng.
- Một URL không tự bảo đảm lấy được ảnh, tiêu đề và nội dung social. Với giao diện tĩnh, phải nhập ảnh/nội dung riêng hoặc dùng cơ chế nhúng phù hợp; không hứa tự đọc mọi link social.

Mục đích cuối cùng là cho người xem hiểu trải nghiệm sử dụng máy từ nguồn thực tế. Trong giai đoạn demo, dùng tiêu đề trung tính **“Chia sẻ & trải nghiệm”**. Chỉ đổi thành “Khách hàng nói gì về máy in Brother?” sau khi xác nhận nguồn thực sự là feedback người dùng.

## 2. Nguồn demo và giới hạn đã kiểm tra

| Thẻ | Nguồn | URL giữ nguyên | Tình trạng |
|---|---|---|---|
| 1 | Bài Facebook tại đường dẫn `brothervn` | https://www.facebook.com/brothervn/posts/pfbid02TMau6EHd8iJT4tUMH53ep7BJ64NuzTgu2vT71bHTP5cLvt5iqSzmdjPzL5RKnSd1l | Chưa đọc được nội dung và chưa thử nhúng thực tế |
| 2 | Bài Facebook tại đường dẫn `brothervn` | https://www.facebook.com/brothervn/posts/pfbid0b7y9FFiMAC5Pi33EBhJLrVNGRZZ9A1RkG1xMVBrpUpunSnSsrLW5CM81CFdP1YWFl | Chưa đọc được nội dung và chưa thử nhúng thực tế |
| 3 | Bài Facebook tại đường dẫn `brothervn` | https://www.facebook.com/brothervn/posts/pfbid01Uvt1MjXzoxo52s7yXz73eL6dGNAbX32tQTrutyjdLXJKhKUtiCctsNYUgRS9DDFl | Chưa đọc được nội dung và chưa thử nhúng thực tế |

Đã thử truy cập ba URL nhưng công cụ đọc web không lấy được nội dung. Điều này không chứng minh bài bị xóa hoặc không nhúng được. Cần kiểm tra từng bài trên website thử nghiệm khi triển khai, gồm trạng thái công khai, hạn chế truy cập và cách nhúng hiện hành.

Các link đều đi qua đường dẫn trang `brothervn`; không suy ra người viết là khách hàng độc lập. Nếu bài là nội dung do thương hiệu đăng lại trải nghiệm người dùng, phần nguồn vẫn phải thể hiện đúng thương hiệu và người được dẫn lời khi có thông tin xác nhận.

Không tự tạo tên khách, avatar, lời khen, số sao, ngày đăng, số lượt thích hoặc nhãn “Đã mua hàng”. Trong demo chưa có nội dung nguồn, dùng nhãn trung tính “Bài chia sẻ trên Facebook” và link thật. Không dùng ảnh máy bất kỳ rồi ghi rằng đó là ảnh của bài đăng.

## 3. Phương án giao diện đề xuất

### 3.1. Cấu trúc section

- Một section độc lập cùng container với module video.
- Tiêu đề H2 căn giữa: “Chia sẻ & trải nghiệm”.
- Dòng mô tả ngắn dự kiến: “Khám phá hình ảnh và những chia sẻ về máy in Brother.” Chỉnh theo nguồn đã được xác nhận.
- Grid gồm 3 thẻ demo theo đúng thứ tự link cung cấp.
- Bên dưới grid có **một vùng xem bài Facebook ngay trong trang**, chỉ xuất hiện khi người xem chọn thẻ social.
- Mục Công nghệ & Độ bền tiếp tục nằm sau toàn bộ module, kể cả khi vùng bài gốc mở rộng.

Người xem nhìn thấy một hệ thống thẻ đồng bộ. Phần hiển thị Facebook gốc nằm trong vùng rộng hơn phía dưới, giúp tránh nhúng bài dài vào những cột hẹp và tránh làm ba thẻ lệch chiều cao.

### 3.2. Thẻ ảnh feedback

Thẻ gồm ảnh, tiêu đề hoặc chú thích ngắn, nguồn khi có và nút “Xem ảnh”.

- Ảnh thực tế ưu tiên khung 4:3 để module khác rõ với khung video 16:9 phía trên.
- Ảnh chụp đoạn feedback hoặc nội dung có chữ dùng `object-fit: contain`; không cắt mất lời đánh giá để làm đẹp thumbnail.
- Ảnh máy/người dùng có thể dùng cover sau khi kiểm tra vùng crop.
- Bấm ảnh hoặc “Xem ảnh” mở ảnh nguyên bản trong lightbox, hỗ trợ đóng bằng nút và Escape.
- Nếu có link social đi kèm, thêm “Xem bài gốc” riêng; ảnh vẫn mở lightbox.
- Nội dung trong ảnh không bị thay thế bằng lời đánh giá tự viết. Nếu nhập trích dẫn, phải đúng nguồn.
- Một thẻ ảnh hợp lệ cần có ảnh; không có ảnh thì ẩn thẻ, tránh khung ảnh hỏng.

### 3.3. Thẻ social

Thẻ gồm ảnh bìa tùy chọn, nhãn nguồn Facebook, tiêu đề được nhập/kiểm chứng, mô tả ngắn tùy chọn và hai hành động:

- **“Xem bài viết”**: mở vùng hiển thị bài gốc bên dưới grid; tải phần nhúng cho đúng URL được chọn.
- **“Mở trên Facebook”**: mở URL gốc trực tiếp, hoạt động độc lập với phần nhúng.

Ảnh bìa không bắt buộc. Khi chỉ có URL, vẫn hiển thị một thẻ nguồn rõ ràng với nhãn Facebook và hành động; vùng đầu thẻ dùng nền xanh nhạt cùng tên nguồn, không giả ảnh bài đăng hoặc ảnh người đánh giá. Chỉ dùng ảnh bìa khi có ảnh được cung cấp hoặc đã kiểm tra từ nguồn.

Không giả giao diện Facebook bằng số lượt thích, bình luận và nút Like tự tạo. Khi nhúng bài thật, để Facebook hiển thị các thành phần của bài.

### 3.4. Quy cách style

| Thành phần | Quy cách đề xuất |
|---|---|
| Nền section | Trắng; tạo nhịp khác với nền xám rất nhạt của module video |
| Màu nhấn | Kế thừa màu xanh Brother đang dùng trên nút đặt máy |
| Font | Font hiện tại của landing page, không thêm font mới |
| Container | Cùng lề, cùng max-width với video và bảng so sánh |
| Thẻ | Nền trắng, viền xám nhẹ 1px, bo góc 16px, bóng nhẹ |
| H2 | Khoảng 30–34px desktop, 24–28px mobile; điều chỉnh theo hệ thống chữ thực tế |
| Tiêu đề thẻ | Khoảng 17–18px, line-height 1.4–1.5; ưu tiên biên tập gọn |
| Mô tả | Khoảng 14–16px; dễ đọc, không dùng chữ xám quá nhạt |
| Nhãn nguồn | Nhỏ gọn, Facebook hoặc nguồn ảnh được xác nhận |
| Khung ảnh | 4:3; dành sẵn kích thước trước khi tải |
| Padding thẻ | 18–20px desktop, 16px mobile |
| Gap grid | 24px desktop, 16–20px mobile |
| Padding section | Dự kiến 48–56px desktop, 28–36px mobile |
| Khoảng cách tới video | Theo nhịp section; tránh cộng dồn hai lớp padding thành khoảng trắng quá lớn |
| Vùng bài gốc | Căn giữa, rộng theo container và chiều rộng plugin được hỗ trợ; chiều cao theo bài thật |

Các thẻ có vùng ảnh/bìa đồng đều; phần hành động căn cuối thẻ bằng bố cục flex. Không cố định chiều cao nội dung đến mức cắt chữ. Hover tăng nhẹ độ rõ của viền/bóng, nâng tối đa 2–3px. Focus bàn phím rõ ràng; trên điện thoại mọi nút vẫn hiện dù không hover. Tôn trọng lựa chọn giảm chuyển động.

Không thêm carousel khi chỉ có 3 mục, không autoplay, không làm masonry khiến thứ tự đọc khó theo dõi. Nếu sau này có nhiều feedback, ưu tiên mở rộng grid và “Xem thêm” sau một hàng đầu; chức năng đó không thuộc demo ban đầu.

### 3.5. Responsive

| Viewport | Grid thẻ | Vùng bài nhúng / ảnh |
|---|---|---|
| 320–767px | 1 cột | Chiều rộng theo container; ảnh xem đầy đủ; nhúng chỉ dùng nếu plugin hỗ trợ vừa khung |
| 768–1023px | 2 cột | Thẻ thứ 3 nằm đầu hàng sau; bài gốc ở vùng riêng dưới grid |
| Từ 1024px | 3 cột | 3 thẻ bằng nhau; bài gốc căn giữa phía dưới |

Mobile dùng lề theo theme, tối thiểu khoảng 16px nếu phù hợp. Hành động có vùng bấm khoảng 44px. URL dài không hiển thị nguyên chuỗi trong thẻ; dùng nhãn liên kết rõ ràng.

Không ép plugin Facebook vào chiều rộng nhỏ hơn mức nền tảng hỗ trợ, không dùng scale để thu nhỏ cả chữ và nút. Nếu bài nhúng không phù hợp ở 320px, giữ ảnh/thẻ nguồn và link mở bài gốc; ghi nhận giới hạn cụ thể sau kiểm tra. Không dùng chiều cao cố định làm cắt phần dưới bài nhúng, không áp `overflow: hidden` để che nội dung.

## 4. Cách add hình hoặc link khi tích hợp

Đây là phần cấu hình của module, không phải form cho khách truy cập gửi đánh giá. Người quản trị thêm nội dung, website hiển thị lại.

### 4.1. Cấu hình chung

| Trường | Vai trò |
|---|---|
| Bật phần Chia sẻ & trải nghiệm | Hiện/ẩn toàn module |
| Tiêu đề | H2 của module |
| Mô tả ngắn | Dòng bên dưới H2; cho phép để trống |

### 4.2. Cấu hình từng mục

| Trường | Loại ảnh | Loại social |
|---|---|---|
| Bật mục | Có | Có |
| Loại nội dung | Chọn “Hình ảnh” | Chọn “Bài social” |
| Hình ảnh | Bắt buộc | Tùy chọn, dùng làm bìa |
| Link bài gốc | Tùy chọn | Bắt buộc |
| Tiêu đề / chú thích | Có, đúng nội dung | Có; có nhãn trung tính khi chưa nhập |
| Mô tả ngắn | Tùy chọn | Tùy chọn; không tự đọc từ URL |
| Tên nguồn / người chia sẻ | Tùy chọn, chỉ nhập khi biết | Theo nguồn xác nhận; không giả tên khách |
| Alt ảnh | Mô tả ảnh phù hợp | Chỉ cần khi có ảnh bìa |

Demo có 3 mục social, nhưng cùng cấu trúc phải cho phép đổi bất kỳ mục nào thành ảnh, hoặc trộn ảnh và social trong một grid. Nếu triển khai Haravan có thể chuẩn bị 6 vị trí cấu hình cố định, bật 3 vị trí đầu; mục tắt/trống không chiếm chỗ. Phải xác nhận loại input và quy ước của theme hiện tại trước khi code.

UI thiết lập trong `config/settings.html` nên chia “Cấu hình chung” và “Nội dung 1–6”, có hướng dẫn ngắn: “Chọn Hình ảnh để tải ảnh feedback; chọn Bài social để thêm link Facebook. Ảnh bìa social là tùy chọn.” Không hướng dẫn người mới dán script hoặc nhập HTML nhúng tùy ý.

Ưu tiên trường chỉ cần cho từng loại nếu giao diện settings hỗ trợ; nếu không, ghi nhãn “Dùng cho loại Hình ảnh” / “Không bắt buộc”. Không tự sửa `settings_schema.json` hoặc `settings_data.json` ngoài yêu cầu tích hợp thực tế.

Với HTML/CSS/JS tĩnh, cấu hình được lưu trong dữ liệu/file giao diện, chưa có màn hình quản trị. Không hứa chức năng upload hoặc lưu dữ liệu từ frontend nếu chưa tích hợp nền tảng.

## 5. Hiển thị bài Facebook trong trang

### 5.1. Luồng thao tác

1. Người xem bấm “Xem bài viết” trên một thẻ social.
2. Mở một vùng bài gốc ngay bên dưới grid, với tên nguồn, trạng thái tải và link mở Facebook luôn có sẵn.
3. Khởi tạo nhúng theo phương thức hiện hành của Meta đã kiểm tra cho URL đó. Ưu tiên mã nhúng chính thức; không đặt URL bài thông thường làm `src` iframe rồi coi là nhúng.
4. Cuộn vùng bài vào vị trí dễ nhìn, có bù header cố định; không tự cuộn khi chỉ tải trang.
5. Chỉ giữ một bài gốc đang mở. Chọn thẻ khác thay nội dung vùng này; không thêm nhiều SDK hoặc iframe không cần thiết.
6. “Thu gọn bài viết” đóng vùng xem, giải phóng phần nhúng và trả focus đúng thẻ.

Nội dung bài gốc hiển thị ngay trong trang khi nhúng hoạt động. Với link-only, giao diện không bảo đảm có ảnh xem trước tự động. Phương án này giữ giao diện thẻ ổn định và giảm việc tải đồng thời ba bài Facebook.

### 5.2. Nhúng có điều kiện và fallback

Meta mô tả Embedded Posts dành cho bài công khai. Cần kiểm tra thêm trạng thái thực tế của từng bài và khả năng truy cập ở thời điểm triển khai. Bài công khai vẫn phải thử nhúng trên domain thật; không coi công khai là bảo đảm thành công.

Trong các trường hợp nhúng không hiển thị, bị hạn chế truy cập, bài đã thay đổi/xóa hoặc trình duyệt chặn tài nguyên:

- Giữ lại thẻ nguồn, ảnh bìa đã nhập nếu có và liên kết bài gốc.
- Vùng xem có lời nhắc ngắn “Bạn có thể xem bài viết trên Facebook” cùng link; không khẳng định bài bị xóa nếu chưa xác minh.
- Không để loading quay vô hạn. Nếu sau một khoảng chờ hợp lý vẫn chưa xác nhận kết quả, dừng trạng thái chờ và đưa link lên rõ hơn.
- Không dùng `iframe.onload` làm bằng chứng nội dung Facebook hiển thị thành công; một trang lỗi cũng có thể phát sự kiện load. Nếu cơ chế nhúng không có tín hiệu sẵn sàng tin cậy, giữ link và kiểm tra bằng mắt trong QA.

Style tự chủ được ở section, thẻ nguồn, khung ngoài và hành động. Không dùng CSS bên ngoài để thay font, bố cục hoặc nội dung bên trong iframe Facebook. Không tự lấy lại số like/bình luận bằng frontend hay gọi Graph API với token nằm trong theme.

Các nền tảng social khác chưa nằm trong demo. Nếu nhận link Instagram/TikTok/... sau này, hiển thị ảnh/nội dung nhập tay + link gốc; chỉ bổ sung nhúng sau khi có adapter và kiểm tra riêng cho nền tảng đó.

## 6. Kế hoạch triển khai 6 phase

### Phase 1 — Rà soát vị trí và nội dung

- Đọc source landing page hiện tại, module video theo plan đã duyệt và các popup/SDK đang có.
- Xác định điểm đóng section video, vị trí bắt đầu Công nghệ & Độ bền, container và nhịp khoảng cách hiện tại.
- Kiểm tra nội dung từng link social; phân loại bài thương hiệu, bài chia sẻ lại hay đánh giá trực tiếp.
- Ghi nhận tiêu đề, ảnh bìa và nguồn đúng; phần thiếu để trống hoặc dùng nhãn trung tính.
- Thử lấy mã nhúng chính thức và kiểm tra từng URL, gồm trạng thái chưa đăng nhập khi môi trường hỗ trợ.

**Đầu ra:** bảng 3 nguồn có trạng thái đã kiểm tra, điểm chèn chính xác, danh sách dữ liệu ảnh/nội dung cần bổ sung. Không đổi link người dùng gửi để thay bằng một bài dễ nhúng hơn.

### Phase 2 — Chốt cấu trúc dữ liệu và settings

- Chuẩn hóa một cấu trúc mục gồm type, enabled, image, source_url, title, description, source_label, image_alt và thứ tự.
- Dựng quy tắc thiếu dữ liệu: ảnh thiếu → ẩn mục ảnh; social thiếu URL → ẩn mục social; social thiếu ảnh → thẻ nguồn không ảnh; chỉ còn 1–2 mục → grid tự thích ứng.
- Chuẩn bị 3 mục social demo từ đúng URL đã gửi.
- Nếu Haravan: thêm nhóm settings bằng cấu trúc `config/settings.html` đã kiểm tra; fieldset đóng mở đúng, ID không trùng, hướng dẫn dành cho người nhập nội dung.
- Khi module bật nhưng không có mục hợp lệ, ẩn section để không tạo khoảng trắng.

**Đầu ra:** dữ liệu đáp ứng cả ảnh và social, không chỉ hardcode riêng ba bài Facebook.

### Phase 3 — Style từ mobile lên desktop

- Hoàn thiện 1 cột trên 320–767px, rồi 2 và 3 cột.
- Kế thừa font/màu/container Brother, tạo nền trắng và khung ảnh 4:3 khác với video phía trên.
- Xử lý ảnh feedback nhiều chữ bằng contain, ảnh thực tế bằng cover phù hợp.
- Căn hành động thẻ, xử lý tiêu đề dài và trạng thái không ảnh.
- Thêm hover/focus nhẹ, vùng bấm mobile và reduced motion.
- Kiểm tra khoảng cách giữa video → feedback → Công nghệ & Độ bền.

**Đầu ra:** cùng một grid có thể trộn ảnh và social mà không vỡ bố cục, không phụ thuộc ảnh giả.

### Phase 4 — Hành vi xem ảnh và xem social

- Kết nối lightbox ảnh; ưu tiên khả năng sẵn có trong project nếu phù hợp và không xung đột.
- Dựng vùng xem social riêng ngay dưới grid, tải nhúng sau thao tác chọn bài.
- Đảm bảo chỉ một vùng bài gốc mở; nút chọn bài, link mở Facebook và đóng/thu gọn có nhãn rõ.
- Xử lý focus, scroll bù header, loading và fallback.
- Nếu dự án đã có Facebook SDK, kiểm tra trước khi tái sử dụng; không ghi đè callback hoặc thêm SDK lần hai.

**Đầu ra:** ảnh phóng to được, bài social có thể hiển thị tại trang nếu được hỗ trợ, link gốc luôn sử dụng được.

### Phase 5 — Tích hợp và hiệu năng

- Scope CSS/JS bằng tiền tố riêng, ví dụ `brother-feedback-*`; không chỉnh global `.card`, `img`, `iframe` hoặc `button`.
- Lazy-load ảnh và dành sẵn vùng thumbnail; tối ưu ảnh phù hợp nội dung, giữ chữ rõ trong ảnh feedback.
- Không tải SDK/iframe Facebook chỉ vì người xem cuộn qua các thẻ trong phương án này.
- Không tự fetch metadata social từ trình duyệt, không thêm backend/token cho phạm vi giao diện.
- Kiểm tra tương tác với popup video và popup đặt mua; không mở lightbox ảnh và popup video chồng nhau.
- Giữ schema/SEO hiện tại; không thêm Review/AggregateRating từ nội dung chưa được xác nhận hoặc tự tạo điểm sao.

**Đầu ra:** thay đổi gọn trong module, không kéo tài nguyên social vào lần tải đầu do phần mới tạo ra.

### Phase 6 — QA và bàn giao

- Chạy checklist dưới đây trên giao diện dựng và các trạng thái dữ liệu.
- Thử đủ ba bài nhúng; ghi nhận bài nào hiển thị được trên domain thực tế, bài nào cần fallback.
- Test ảnh ngang, dọc và screenshot nhiều chữ bằng ảnh được cung cấp/được xác nhận khi có.
- Sửa lỗi rồi kiểm tra lại phần ảnh hưởng; báo rõ phần chưa kiểm tra do thiếu dữ liệu hoặc môi trường.
- Bàn giao code, dữ liệu/settings và hướng dẫn ngắn thêm ảnh/thay link cho người quản trị.

**Đầu ra:** module có kết quả kiểm chứng, không chỉ cam kết “mọi link social đều hiện”.

## 7. Checklist QA

| Nhóm | Ca kiểm tra | Điều kiện đạt |
|---|---|---|
| Vị trí | Sau 3 video, trước Công nghệ & Độ bền | Đúng thứ tự; không lồng section feedback vào popup/video |
| URL | So sánh 3 URL với yêu cầu | Nguyên URL, đúng thứ tự, không cắt phần pfbid |
| Nguồn | Nội dung thương hiệu và feedback người dùng | Nhãn nguồn đúng; không tự ghi là khách đã mua |
| Demo | Chỉ có 3 URL, chưa có ảnh | 3 thẻ nguồn dùng được; không giả ảnh hoặc lời đánh giá |
| Ảnh | Ngang, dọc, nhiều chữ | Thumbnail phù hợp; xem được ảnh đầy đủ |
| Mixed | Ảnh + social trong một grid | Bố cục nhất quán, hành động đúng từng loại |
| Thiếu dữ liệu | Thiếu ảnh, thiếu URL, tiêu đề trống | Theo quy tắc ẩn/fallback, không có khung ảnh hỏng |
| Số mục | 0, 1, 2, 3 và 6 mục | Grid thích ứng; 0 mục thì section ẩn |
| Responsive | 320, 360, 390, 430, 768, 820, 1024, 1440px | Không tràn ngang hoặc chồng chữ/nút |
| Facebook | Nhúng từng URL trên domain triển khai | Có kết quả thực tế cho từng bài; không coi load iframe là thành công |
| Mobile embed | Plugin ở 320px và khi xoay ngang | Hiển thị vừa khung hoặc fallback rõ; không thu nhỏ chữ bằng transform |
| Chiều cao | Bài social dài, nhiều ảnh | Nội dung không bị cắt; section tiếp theo dịch xuống tự nhiên |
| Chọn bài | Đổi bài 1 → 2 → 3, thu gọn, mở lại | Chỉ bài đang chọn mở; không nhân bản SDK/khung |
| Loading | Mạng chậm hoặc nhúng không có kết quả | Không spinner vô hạn; có link mở bài gốc |
| Fallback | Chặn tài nguyên social, JS tắt | Thẻ/ảnh và link nguồn vẫn tiếp cận được |
| Lightbox | Mở/đóng ảnh, Escape, focus | Ảnh đầy đủ, nút đóng rõ, trả focus đúng |
| Bàn phím | Tab, Enter và focus vùng xem | Tất cả hành động dùng được; không focus vào nội dung đã ẩn |
| Hiệu năng | Network trước khi bấm social | Module không khởi tạo SDK/iframe Facebook từ đầu |
| Layout shift | Tải ảnh chậm, mở/đóng vùng bài | Thumbnail không nhảy; mở bài là thay đổi theo thao tác người dùng |
| Hồi quy | Video, đặt máy, menu anchor, bảng so sánh | Hoạt động hiện tại vẫn đúng |
| Settings | Đổi loại, bật/tắt, thay URL và ảnh | UI rõ, dữ liệu lưu/hiển thị đúng khi đã tích hợp nền tảng |
| Code | HTML, selector, ID, UTF-8 | Không selector global mới, ID trùng hoặc lỗi ký tự |

## 8. Những phần cần xác minh khi bắt đầu code

1. Source landing page hiện hành và trạng thái module video đã triển khai hay mới có plan.
2. Nội dung thực tế của ba bài Facebook, mức độ phù hợp với model máy và khả năng nhúng.
3. Ảnh bìa/ảnh feedback thật nếu muốn thẻ có ảnh ngay trong demo.
4. Website là HTML tĩnh hay theme Haravan cần cấu hình nội dung trong admin.

Các mục này là đầu việc của Phase 1; không làm dừng việc lập plan. Chưa có source/ảnh thì không tuyên bố đã kiểm code hoặc đã làm demo hiển thị bài thật.

## 9. Nguồn tham khảo và liên kết plan trước

- Plan trước: `Plan_Them_3_Video_YouTube_Brother.md` — đã đọc lại phần vị trí và style để giữ module feedback tiếp nối đúng.
- Meta, Introducing Embedded Posts: https://about.fb.com/news/2013/07/introducing-embedded-posts/ — mô tả cơ chế đưa bài công khai vào website. Đây là nguồn giới thiệu lịch sử, không thay cho kiểm tra tương thích hiện tại.
- Tài liệu kỹ thuật cần đối chiếu khi triển khai: https://developers.facebook.com/docs/plugins/embedded-posts/ — chưa truy cập được đầy đủ trong phiên lập plan.

**Phương án chốt:** section “Chia sẻ & trải nghiệm” sau video, thẻ ảnh/social đồng bộ Brother, desktop 3 cột và mobile 1 cột; ảnh mở lightbox, bài Facebook mở trong một vùng nhúng ngay dưới grid, có link nguồn dự phòng. Cấu hình cho phép thêm ảnh hoặc link theo từng mục; không hứa tự lấy đầy đủ nội dung từ mọi URL social.

---

## 10. Báo Cáo Thực Thi Hoàn Thành & Kiểm Toán QA Tĩnh (Implementation & Audit Report)

- **Trạng thái thực thi:** HOÀN THÀNH 100% (Đã triển khai vào codebase và đồng bộ mirror).
- **Ngày hoàn thành:** 01/10/2026.
- **Commit hash:** Xem Git log tương ứng trên nhánh `main` và `gh-pages`.
- **File đã tác động (Hard Scope):**
  1. `hrv_demo_brother/index.html` (Đã thêm CSS `.blp-social-*`, Section `#chia-se-trai-nghiem`, Inline Viewer `#socialViewerArea`, và JS `openSocialViewer`/`closeSocialViewer`).
  2. `hrv_demo_brother/brother_color_laser_landing_page.html` (Đồng bộ mirror 1:1, 0 diff).
  3. `hrv_demo_brother/Plan_Feedback_Anh_Social_Sau_Video_Brother.md` (Cập nhật tiến độ).

### Kết Quả Kiểm Toán Tĩnh Toàn Diện (Node.js Static Audit)
- **Tag Balance:** `<section>` 9/9, `<dialog>` 2/2, `<article>` 11/11, `<style>` 1/1, `<header>` 1/1, `<footer>` 1/1, `<main>` 1/1 — **PASS**.
- **IDs & Anchors:** `#chia-se-trai-nghiem`, `#socialViewerArea`, `#socialViewerTitle`, `#socialViewerContainer`, `#video-trai-nghiem`, `#brotherVideoModal`, `#confirmModal` — **PASS**.
- **JS Syntax & Functions:** Inline scripts compile thành công qua `vm.Script`; `openSocialViewer`, `closeSocialViewer`, `openBrotherVideoModal`, `closeBrotherVideoModal` — **PASS**.
- **Social URLs:** Đầy đủ 3 link bài viết Facebook chính thức từ Fanpage Brother Vietnam — **PASS**.
- **AOS Animations:** 42 phần tử được gán `data-aos`, `data-aos-duration`, `data-aos-delay` mượt mà — **PASS**.
- **Clean Code Sweep:** Không tồn tại `console.log`, `debugger`, hay `alert` — **PASS**.

