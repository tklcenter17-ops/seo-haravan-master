# PLAN BỔ SUNG 3 VIDEO YOUTUBE — LANDING PAGE BROTHER

Ngày lập: 01/10/2026. Trạng thái: ĐÃ TRIỂN KHAI VÀ NGHIỆM THU THÀNH CÔNG trên landing page Brother.

## 1. Vị trí và mục tiêu

Ảnh cho thấy bảng so sánh kết thúc bằng dòng “Chọn đặt mua”, bên dưới là khoảng trống và đầu mục “CÔNG NGHỆ & ĐỘ BỀN”. Chèn module video sau toàn bộ bảng so sánh và trước mục này.

Thứ tự nội dung sau sửa: bảng so sánh → module 3 video → Công nghệ & Độ bền. Không chèn video vào hàng hoặc ô của bảng. Khung đỏ là dấu chỉ vị trí, không phải đường viền cần đưa vào giao diện. Chiều cao vùng này được mở rộng tự nhiên theo nội dung, không ép 3 video vào chiều cao khoảng trống trong ảnh.

Mục tiêu: giúp người xem tiếp cận video sau khi so sánh máy; hình thức đồng bộ với landing page Brother, dễ thao tác trên điện thoại và giảm tải trình phát ở lần mở trang đầu tiên.

## 2. Danh sách video và quy tắc xử lý

| Thứ tự | URL người dùng cung cấp | Video ID | Cách sử dụng |
|---|---|---|---|
| 1 | https://www.youtube.com/watch?v=eOrpTV3pSPE | `eOrpTV3pSPE` | Một video độc lập |
| 2 | https://www.youtube.com/watch?v=-pC7kvdlk5M&list=PLEYQY7C6hsz6s8MnrRdeQ5AYp-cLlnNbj&index=1 | `-pC7kvdlk5M` | Lấy video từ `v`; bỏ playlist trong URL trình phát |
| 3 | https://www.youtube.com/watch?v=FvwQEDnetBk&list=PLEYQY7C6hsz6s8MnrRdeQ5AYp-cLlnNbj&index=3 | `FvwQEDnetBk` | Lấy video từ `v`; bỏ playlist trong URL trình phát |

Giữ nguyên thứ tự 1–2–3. Các link có `list` và `index` vẫn được hiểu là video cụ thể, vì yêu cầu là thêm 3 link vào 3 thẻ. Link mở trực tiếp trên YouTube cũng dùng URL video độc lập để có hành vi nhất quán.

Kết quả kiểm tra nguồn hiện có: kết quả tìm kiếm YouTube cho video thứ 2 ghi nhận tiêu đề hướng dẫn cài đặt, sử dụng Brother HL-L8360CDW. Đây chưa phải kết quả kiểm tra phát video trong website. Chưa xác minh đầy đủ tiêu đề, nội dung và quyền nhúng của cả 3 video. Khi triển khai phải mở từng video, kiểm tra nội dung phù hợp và thử nhúng thực tế; không tự gán tất cả video thành video giới thiệu máy Brother.

## 3. Phương án giao diện chốt

### 3.1. Bố cục tổng thể

- Một section riêng, căn theo container và lề của bảng so sánh hiện tại.
- Tiêu đề H2 dự kiến: “Video trải nghiệm & hướng dẫn”. Chốt tên sau khi kiểm tra nội dung cả 3 link.
- Tiêu đề căn giữa; không thêm lời quảng cáo hoặc thông số chưa có nguồn.
- Bên dưới là 3 thẻ video bằng nhau trên desktop; tất cả dùng ảnh đại diện và nút Play.
- Mỗi thẻ có tiêu đề ngắn, đúng nội dung video, và liên kết “Xem trên YouTube”.
- Bấm ảnh hoặc nút Play mở chung một popup xem video. Liên kết “Xem trên YouTube” là hành động độc lập.
- Module mở rộng chiều cao trang tự nhiên; mục “Công nghệ & Độ bền” nằm tiếp theo với khoảng cách rõ ràng.

Với 3 video, dùng grid giúp người xem thấy danh sách ngay. Không cần slider, thư viện animation hay nút chuyển trang.

### 3.2. Style đề xuất

| Thành phần | Quy cách dự kiến |
|---|---|
| Nền module | Xám rất nhạt như khu vực bảng so sánh; lấy màu thực tế từ stylesheet khi triển khai |
| Thẻ video | Nền trắng, viền mảnh nhẹ, bo góc 14–16px, bóng nhẹ |
| Màu nhấn | Tái sử dụng màu xanh Brother từ nút “Đặt Model Này”; không tự thay màu toàn trang |
| Font | Kế thừa font landing page, không tải thêm font riêng |
| Tiêu đề section | Khoảng 30–34px desktop, 24–28px mobile; weight theo font hiện tại |
| Tiêu đề video | 16–18px, line-height khoảng 1.45; độ dài gọn, vẫn thể hiện đúng nội dung |
| Ảnh đại diện | Khung 16:9, bo góc phần trên thẻ; chọn ảnh rõ, kiểm tra chữ có bị crop |
| Nút Play | Vòng tròn xanh Brother, biểu tượng trắng; 56px desktop, 48px mobile |
| Nội dung dưới ảnh | Padding 16–20px; khoảng cách đều giữa tiêu đề và link |
| Khoảng cách giữa thẻ | 24px desktop; 16–20px trên màn hình nhỏ |
| Padding section | Dự kiến 48–56px desktop, 28–36px mobile; điều chỉnh theo khoảng cách section sẵn có |

Hover trên thiết bị có chuột: thẻ nâng tối đa 3px, viền xanh nhẹ và bóng rõ hơn; chuyển động 160–200ms. Nút Play luôn hiển thị. Focus bàn phím có viền rõ. Khi người dùng giảm chuyển động, bỏ hiệu ứng nâng và zoom.

Không dùng nền gradient nổi bật, bóng đậm hoặc animation lặp. Module cần hòa vào bảng so sánh và hệ thống nút xanh trong ảnh.

### 3.3. Responsive

| Độ rộng viewport | Bố cục | Lưu ý |
|---|---|---|
| 320–767px | 1 cột, 3 video xếp dọc | Lề tối thiểu 16px hoặc theo container hiện tại; đủ vùng bấm, không tràn ngang |
| 768–1023px | 2 cột, video thứ 3 nằm đầu hàng sau | Cùng độ rộng với 2 thẻ trên; không kéo thẻ cuối rộng gấp đôi |
| Từ 1024px | 3 cột bằng nhau | Căn thẳng với container bảng; thumbnail và nội dung thẻ đều nhau |

Breakpoint được điều chỉnh nếu container thực tế khiến thẻ quá hẹp. Ảnh 16:9 giữ sẵn kích thước để không làm dịch chuyển nội dung khi tải. Không giới hạn chiều cao toàn section. Kiểm tra tiêu đề dài không bị cắt mất thông tin quan trọng; ưu tiên biên tập tiêu đề gọn thay vì ép một dòng.

## 4. Hành vi xem video

### 4.1. Trước khi bấm

- Hiển thị 3 ảnh đại diện, tiêu đề, Play và link trực tiếp.
- Không tạo iframe YouTube hay tải IFrame Player API từ lúc mở trang.
- Ảnh dưới màn hình đầu tiên dùng lazy loading; ảnh có vùng kích thước cố định.
- Ảnh lỗi thì dùng nền giữ đúng tỷ lệ và nhãn video; người dùng vẫn bấm xem được.

### 4.2. Khi bấm

1. Ghi nhớ phần tử vừa bấm để trả focus khi đóng popup.
2. Mở popup, hiển thị tiêu đề video và nút đóng.
3. Tạo duy nhất một iframe từ video ID đã xác định; không đưa nguyên URL tùy ý vào iframe.
4. Hiển thị controls, cho phép fullscreen và cấu hình `playsinline=1`.
5. Có thể yêu cầu phát sau thao tác bấm; nếu trình duyệt không cho autoplay, người dùng bấm Play của YouTube. Không tự phát khi tải trang hoặc cuộn tới section.
6. Luôn có link “Xem trên YouTube” bên ngoài iframe để dùng khi video không nhúng được.

YouTube quy định vùng trình phát tối thiểu 200 × 200px. Popup ưu tiên 16:9 ở màn hình đủ rộng; trên điện thoại hẹp, bảo đảm chiều cao trình phát ít nhất 200px. Không ép iframe vào thumbnail thấp hơn giới hạn này.

### 4.3. Đóng và mở lại

- Đóng bằng nút × có nhãn, phím Escape hoặc bấm vùng nền ngoài popup.
- Gỡ iframe khi đóng để dừng âm thanh và phát video.
- Trả focus về thẻ vừa mở; phục hồi vị trí cuộn và trạng thái scroll ban đầu.
- Popup giới hạn chiều cao theo vùng nhìn; nút đóng luôn tiếp cận được, kể cả màn hình ngang.
- Chỉ có một popup và một iframe hoạt động. Mở lại video bắt đầu bằng iframe mới; không thêm tính năng nhớ thời gian xem.
- Dùng dialog có hỗ trợ focus, hoặc triển khai đủ focus trap và thao tác bàn phím nếu môi trường cần phương án khác.

Không che lên controls của YouTube và không hứa loại bỏ quảng cáo, thương hiệu hay toàn bộ video liên quan. Không cần IFrame Player API cho luồng một iframe rồi gỡ khi đóng. Lỗi bên trong iframe khác nguồn không thể kiểm tra đơn giản bằng cách đọc DOM; kiểm tra phát thực tế và giữ link fallback sẵn có.

## 5. Kế hoạch triển khai 6 phase

### Phase 1 — Kiểm tra nguồn và điểm chèn

- Đọc file HTML/Liquid hiện hành và stylesheet/script liên quan.
- Xác định node đóng bảng so sánh, wrapper của bảng, container trang và section Công nghệ & Độ bền.
- Kiểm tra khoảng trắng hiện tại đến từ padding, margin, chiều cao cố định hay phần tử rỗng. Chỉ điều chỉnh phần tạo khoảng trống tại vị trí này nếu cần.
- Ghi nhận selector bảng, nút đặt mua, menu anchor và script hiện có để tránh trùng tên.
- Kiểm tra từng link video, tiêu đề, thumbnail và khả năng nhúng trên domain thực tế.

Đầu ra: vị trí chèn chính xác, danh sách 3 video được kiểm tra và phạm vi thay đổi cụ thể. Ảnh hiện tại chỉ xác định vị trí bằng hình, chưa chứng minh cấu trúc DOM hay lỗi CSS của file nguồn.

### Phase 2 — Chốt nội dung và cấu trúc

- Chốt tiêu đề section theo nội dung video thực tế.
- Chuẩn hóa dữ liệu 3 video: ID, tiêu đề hiển thị, ảnh đại diện và URL xem trực tiếp.
- Dựng section và grid theo thứ tự đã xác định.
- Tách button mở video với link YouTube; không lồng button vào link.
- Đặt class có tiền tố riêng, ví dụ `brother-video-*`; ID section duy nhất.

Đầu ra: cấu trúc hợp lệ, đủ 3 video, không nằm trong bảng.

### Phase 3 — Style từ mobile lên desktop

- Hoàn thiện 1 cột trên 320–767px trước; kiểm tra vùng bấm và xuống dòng.
- Mở rộng 2 cột tablet, 3 cột desktop.
- Đồng bộ màu xanh, font, container và bo góc với giao diện hiện tại.
- Bổ sung hover, focus và reduced motion.
- Cân khoảng cách giữa cuối bảng, module mới và mục tiếp theo.

Đầu ra: thẻ cân đối trên mọi breakpoint; không có thanh cuộn ngang mới ngoài vùng bảng vốn có.

### Phase 4 — Popup và tải trình phát theo thao tác

- Khởi tạo chung một popup; event handler chỉ phục vụ module mới.
- Tạo iframe khi bấm; kiểm soát URL theo ID, title rõ ràng và quyền fullscreen.
- Xử lý đóng, Escape, backdrop, focus, scroll và gỡ iframe.
- Giữ link xem trực tiếp sử dụng được khi JavaScript hoặc nhúng gặp vấn đề.

Đầu ra: một video phát tại một thời điểm; đóng popup không còn tiếng.

### Phase 5 — Tích hợp và hiệu năng

- Kiểm tra diff chỉ gồm section, style và hành vi video cần thiết.
- Không thêm thư viện slider/video/font mới cho module.
- Kiểm tra Network trước lần bấm đầu: không có request tải player/API do module này tạo ra; thumbnail có thể tải riêng.
- Xác nhận ảnh không làm nhảy layout; popup không gây mất vị trí cuộn hoặc xung đột popup đặt mua.
- Giữ nguyên link menu và thao tác đặt model. Không thêm mục menu hay schema video nếu không có yêu cầu và metadata đầy đủ.
- Nếu tích hợp Haravan, chỉ mở rộng `config/settings.html` khi phạm vi triển khai yêu cầu cấu hình; không tự sửa `settings_schema.json` hoặc `settings_data.json` cho một module video cố định.

Đầu ra: module tích hợp gọn, có số liệu so sánh tải trang khi cần; không cam kết điểm PageSpeed cụ thể khi chưa đo.

### Phase 6 — QA và bàn giao

- Chạy checklist bên dưới; sửa lỗi rồi kiểm tra lại những phần chịu ảnh hưởng.
- Ghi rõ video nào đã phát thành công, trình duyệt/viewport kiểm tra và vấn đề còn tồn tại nếu có.
- Bàn giao file thay đổi cùng ghi chú vị trí section và dữ liệu video.

Đầu ra: kết quả kiểm chứng thực tế, không chỉ xác nhận bằng đọc code.

## 6. Checklist QA khi triển khai

| Nhóm | Kiểm tra | Điều kiện đạt |
|---|---|---|
| Vị trí | Sau toàn bộ bảng, trước Công nghệ & Độ bền | Đúng vị trí ảnh; không chèn vào table |
| Nội dung | 3 ID và thứ tự | Không sai dấu `-`, không đổi thứ tự, không tự thay video |
| Link | Video 2 và 3 có playlist ban đầu | Trình phát chỉ mở đúng video được chọn |
| Metadata | Tiêu đề, thumbnail, nội dung | Khớp video; không tự gán model hoặc thời lượng |
| Quyền nhúng | Thử cả 3 video trên domain thực tế | Phát được hoặc có fallback rõ ràng và ghi nhận hạn chế |
| Desktop | 1024, 1280, 1440, 1920px | 3 cột đều, đúng container, nội dung không chồng nhau |
| Tablet | 768 và 820px | 2 cột; thẻ cuối không bị kéo giãn |
| Mobile | 320, 360, 390, 430px | 1 cột; không tràn ngang; Play luôn thấy |
| Landscape | Xoay điện thoại khi popup mở | Nút đóng tiếp cận được; player không vỡ bố cục |
| Popup | Mở mỗi video, đóng, mở lại | Chỉ một iframe hoạt động |
| Âm thanh | Đóng lúc video đang phát | Dừng tiếng ngay sau khi iframe bị gỡ |
| Bàn phím | Tab, Enter, Escape | Focus rõ, không thoát ra sau popup, trả focus đúng |
| Mobile browser | Chrome Android, Safari iPhone | Thao tác Play, fullscreen, đóng và scroll đúng |
| Desktop browser | Chrome, Edge, Firefox, Safari khi có môi trường | Không lỗi JS hay khác biệt bố cục ảnh hưởng sử dụng |
| Scroll | Đóng sau khi cuộn và khi xem ngang | Không nhảy về đầu trang; phục hồi trạng thái trước popup |
| Tải ban đầu | Network trước bấm | Không khởi tạo iframe/API YouTube từ module |
| Layout shift | Ảnh tải chậm hoặc lỗi | Khung ảnh giữ kích thước; không đẩy giật nội dung |
| Fallback | Chặn nhúng, mất mạng, JS tắt | Có link video rõ ràng; giao diện vẫn đọc được |
| Hồi quy | Nút đặt model, menu anchor, bảng trên mobile | Các hành vi hiện có vẫn hoạt động |
| Chất lượng code | Selector, ID, HTML, UTF-8, diff | Không CSS global mới, ID trùng, ký tự lỗi hay thay đổi ngoài phạm vi |

## 7. Nguồn kỹ thuật và giới hạn kiểm tra

- YouTube Embedded Players and Player Parameters: https://developers.google.com/youtube/player_parameters — định dạng embed, controls, playsinline, kích thước tối thiểu và tham số trình phát.
- Kết quả YouTube video thứ 2: https://www.youtube.com/watch?v=-pC7kvdlk5M — dùng làm dấu hiệu nhận diện nội dung, cần kiểm tra phát thực tế khi triển khai.
- Ảnh đính kèm được dùng để xác định vị trí và phong cách hiện tại. Chưa kiểm tra source HTML/Liquid và chưa chạy website; checklist phía trên là kế hoạch kiểm tra, không phải các kiểm tra đã hoàn thành.

Phương án bàn giao mong muốn: module 3 thẻ video đồng bộ Brother, desktop 3 cột, mobile 1 cột; popup dùng chung và trình phát chỉ tải sau thao tác người xem.

## 8. Báo cáo triển khai thực tế (01/10/2026)

- **Vị trí tích hợp:** Section `#video-trai-nghiem` nằm ngay sau bảng so sánh (`#bang-so-sanh`) và trước mục Công nghệ & Độ bền (`#loi-ich`).
- **Hiệu ứng AOS:** Đã tích hợp AOS (Animate On Scroll) cho toàn bộ các section trên landing page với `data-aos`, `data-aos-duration`, `data-aos-delay`.
- **Cơ chế Video Modal:** Nạp iframe khi bấm Play, ngắt video và tiếng hoàn toàn khi đóng, hỗ trợ backdrop click và phím Escape.
- **Tệp đồng bộ:** Cả `index.html` và `brother_color_laser_landing_page.html` đều đã được đồng bộ 100%.
- **Kiểm toán code:** Cú pháp JavaScript và cân bằng thẻ HTML section/dialog đạt 100% PASS.
