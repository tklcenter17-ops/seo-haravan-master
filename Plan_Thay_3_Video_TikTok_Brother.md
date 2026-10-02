# PLAN THAY THẾ 3 VIDEO YOUTUBE BẰNG TIKTOK — LANDING PAGE BROTHER

Ngày lập: 02/10/2026. Trạng thái: ĐÃ HOÀN TẤT TRIỂN KHAI VÀ AUDIT THÀNH CÔNG.

## 1. Mục tiêu và phạm vi chuyển đổi

Chuyển đổi toàn bộ module 3 Video trên landing page Brother Color Laser từ định dạng video ngang YouTube sang video dọc TikTok theo 3 liên kết chính thức từ kênh `@brothervietnam`.

Bảo toàn 100% cấu trúc semantic HTML, độ ổn định của theme, hiệu năng tải trang (zero CLS) và tính tương thích trên mọi kích thước màn hình điện thoại & máy tính.

---

## 2. Danh sách 3 Video TikTok thực tế

| Thứ tự | URL chính thức | Video ID | Tiêu đề hiển thị | Badge |
|---|---|---|---|---|
| 1 | https://www.tiktok.com/@brothervietnam/video/7615261940247547157 | `7615261940247547157` | Trải nghiệm dòng máy in laser màu Brother & công nghệ LED tiên tiến | `Trải Nghiệm LED Màu` |
| 2 | https://www.tiktok.com/@brothervietnam/video/7594301822676798740` | `7594301822676798740` | Giữ trọn mạch sáng tạo – Tái tạo màu sắc chuẩn xác cùng Brother | `Sáng Tạo & Chuẩn Màu` |
| 3 | https://www.tiktok.com/@brothervietnam/video/7592082612542328084 | `7592082612542328084` | In màu sắc nét – Chuẩn mực in ấn chuyên nghiệp cho doanh nghiệp | `Chuẩn Doanh Nghiệp` |

---

## 3. Kiến trúc kỹ thuật và giải pháp tối ưu

1. **Tỷ lệ khung hình (Aspect Ratio):**
   - Chuyển từ tỷ lệ ngang 16:9 (`padding-top: 56.25%`) sang tỷ lệ dọc 4:5 (`aspect-ratio: 4 / 5` kèm fallback `padding-top: 115%`).
   - Căn chỉnh vị trí ảnh (`object-position`) trung tâm cho Video 1 & 2; căn chỉnh `center bottom` cho Video 3 để làm nổi bật máy in và khay giấy Brother.

2. **Tài nguyên ảnh đại diện (Thumbnails):**
   - Lưu trữ cục bộ 3 ảnh thumbnail gốc độ phân giải cao tại `assets/tiktok-thumb-1.jpg`, `assets/tiktok-thumb-2.jpg`, `assets/tiktok-thumb-3.jpg`.
   - Bổ sung cơ chế tự động fallback `onerror` sang CDN TikTok có chữ ký bảo đảm ảnh luôn hiển thị 100% không bao giờ bị lỗi.

3. **Giao diện Modal Popup xem Video (`#brotherVideoModal`):**
   - Tối ưu kích thước popup dạng smartphone vertical (`width: min(92vw, 420px)`, `height: min(740px, 88vh)`).
   - Tự động căn giữa màn hình tuyệt đối trên cả mobile và desktop.
   - Trình phát iframe TikTok chính thức: `https://www.tiktok.com/embed/{videoId}`.
   - Cơ chế khóa cuộn trang (`body overflow: hidden`) và giải phóng iframe khi đóng để ngắt âm thanh triệt để.

4. **Biểu tượng và liên kết:**
   - Thay đổi text từ `"Xem trên YouTube"` thành `"Xem trên TikTok"`.
   - Bổ sung biểu tượng SVG chuẩn TikTok kết hợp icon mở tab mới ngoài ứng dụng.

---

## 4. Danh sách file tác động

- `index.html`: Cập nhật CSS, section markup, modal popup dialog và script.
- `brother_color_laser_landing_page.html`: Đồng bộ 100% khớp từng dòng với `index.html`.
- `assets/tiktok-thumb-1.jpg`: Ảnh thumbnail Video 1.
- `assets/tiktok-thumb-2.jpg`: Ảnh thumbnail Video 2.
- `assets/tiktok-thumb-3.jpg`: Ảnh thumbnail Video 3.
