# 📊 SALES ADMIN SYSTEM — HỆ THỐNG QUẢN LÝ BÁN HÀNG & BÁO CÁO DOANH SỐ

> **Nền tảng:** Google Apps Script (Web App SPA) + Google Sheets Database  
> **Script ID:** `1tzooqgSnUyCdOKqQwJ5mz99CkHuT9naZNPJzv9M5WgQxJ1rPKlsSJoND`  
> **Thời gian khởi tạo clone:** 04/09/2026  

---

## 1. 🎯 Tổng Quan Dự Án

**Sales Admin System** là hệ thống quản lý bán hàng và phân tích doanh thu toàn diện được xây dựng dưới dạng ứng dụng Web App chạy trên hạ tầng **Google Apps Script**. Hệ thống sử dụng **Google Sheets** làm cơ sở dữ liệu thời gian thực (real-time database), cung cấp giao diện quản trị hiện đại (Single Page Application) phục vụ các hoạt động bán hàng, quản lý kho, chăm sóc khách hàng VIP, tự động hóa thông báo qua Telegram và trợ lý AI Gemini.

### ✨ Điểm nổi bật
- **Không tốn chi phí server:** Chạy 100% không máy chủ (Serverless) trên hạ tầng Google Cloud & Google Workspace.
- **Tốc độ cao với Chunked Cache:** Sử dụng `CacheService` phân mảnh 30KB với TTL 2 phút, giải quyết triệt để vấn đề nghẽn giới hạn đọc/ghi của Google Sheets.
- **Tích hợp đa kênh:** Kết nối Telegram Bot (thông báo đơn hàng, tra cứu tồn kho qua bot), AI Gemini (hỏi đáp dữ liệu kinh doanh), và Google Drive (tự động sao lưu).

---

## 2. 📁 Cấu Trúc Thư Mục & Vai Trò Từng File

```text
app_scipt/
├── .clasp.json          # Cấu hình đồng bộ mã nguồn với Google Clasp CLI
├── appsscript.json      # Manifest cấu hình môi trường Apps Script, OAuth scopes, timezone
├── Code.js              # Backend chính: CRUD, Telegram Bot, Gemini AI, Triggers, Auth (~4.5k dòng)
├── StatsService.js      # Service layer: Thống kê nâng cao, KPI tăng trưởng, Data Quality (~660 dòng)
├── Index.html           # Khung HTML giao diện (Dashboard, Sidebar, Modal, Layout SPA) (~1.9k dòng)
├── Script.html          # Logic JavaScript client-side, giao tiếp google.script.run, Chart.js (~250 KB)
├── Style.html           # Toàn bộ mã nguồn CSS, biến màu theme sáng/tối, responsive UI (~132 KB)
└── README.md            # Tài liệu mô tả dự án (file này)
```

---

## 3. 🧩 Kiến Trúc Kỹ Thuật & Dữ Liệu

### 3.1. Các bảng tính dữ liệu (Google Sheets)
Hệ thống hỗ trợ đọc/ghi trên 3 sheet chính:
1. **`SalesData`**: Sheet bán hàng tiêu chuẩn, lưu trữ thông tin sản phẩm và các đơn bán thông thường.
2. **`Mã V`**: Sheet quản lý các đơn hàng/sản phẩm thuộc mã đặc thù (mã V).
3. **`THANH LÝ`**: Sheet phục vụ phân hệ xả kho, hàng thanh lý, giảm giá đặc biệt.

### 3.2. Cơ chế Alias Header thông minh (`HEADER_ALIASES`)
Hệ thống không phụ thuộc cứng vào vị trí cột trên Google Sheet mà tự động quét và ánh xạ linh hoạt tên cột:
- **Mã SP:** `MÃ SP`, `Mã SP`, `SKU`, `Mã hàng`, `Mã sản phẩm`...
- **Sản phẩm:** `Sản phẩm`, `Tên sản phẩm`, `Tên SP`, `Dịch vụ`, `Mặt hàng`...
- **Giá bán & Doanh thu:** `Giá bán`, `Doanh thu`, `Thành tiền`, `Tổng tiền`, `Giá trị đơn`...
- **Chi phí & Lợi nhuận:** `Giá vốn`, `Tiền lời`, `Lợi nhuận`, `Tiền COD`...
- **Thông tin khách:** `Tên khách hàng`, `SĐT khách hàng`, `Ai chốt`...

### 3.3. Tầng Caching (CacheService)
- Dữ liệu được tuần tự hóa dạng JSON và nén theo từng khối 30KB (`CACHE_CHUNK_SIZE = 30 * 1024`), lưu tối đa 60 khối.
- Giúp ứng dụng Web App tải dữ liệu tức thì (sub-second load time) mà không phải gọi API Google Sheets mỗi lần người dùng bấm chuyển trang.

---

## 4. 🚀 Các Phân Hệ & Chức Năng Nổi Bật

### 4.1. Màn hình Dashboard & Nhịp vận hành (Shop Pulse)
- **Shop Pulse (Vận hành trực tiếp):** Đồng hồ đo vòng tròn thể hiện điểm sức khỏe vận hành (Health Score), cập nhật trực tiếp doanh thu chốt hôm nay, tiền thực tế đã thu, COD đang phát sinh ngoài đường và số việc tồn đọng cần xử lý.
- **4 Thẻ KPI chính:**
  - Tổng doanh thu (kèm biểu đồ Sparkline).
  - Lợi nhuận ròng.
  - Tổng lỗ / Giá vốn.
  - Kho hàng (số lượng sản phẩm còn trong kho).
- **Hệ thống biểu đồ (Chart.js):**
  - Biểu đồ Doanh thu & Lợi nhuận theo ngày (Area Chart).
  - Biểu đồ Cơ cấu trạng thái hàng (Donut Chart).
  - Biểu đồ Số đơn theo ngày (Bar Chart).
  - Biểu đồ Hình thức giao hàng (COD, chuyển khoản, freeship...).

### 4.2. Customer Lifetime Dashboard & VIP Tiers
- **Phân hạng khách hàng 4 cấp độ:**
  - 💎 **VIP Kim Cương:** LTV ≥ 100.000.000 ₫ hoặc ≥ 30 đơn.
  - 🥇 **VIP Vàng:** LTV ≥ 50.000.000 ₫ hoặc ≥ 15 đơn.
  - 🥈 **VIP Bạc:** LTV ≥ 20.000.000 ₫ hoặc ≥ 8 đơn.
  - 🥉 **VIP Đồng:** LTV ≥ 5.000.000 ₫ hoặc ≥ 3 đơn.
  *(Các mốc chi tiêu có thể tùy biến động ngay trong giao diện cài đặt)*.
- **Theo dõi vòng đời khách hàng:** Phân loại khách hàng mới, khách hàng quay lại và khách hàng có nguy cơ rời bỏ.
- **Vòng quay may mắn (Lucky Spin Wheel):** Mini-game tích hợp trực tiếp trên dashboard để tri ân hoặc kích cầu khách hàng.

### 4.3. Quản lý sản phẩm & Bán hàng (Products & Daily Orders)
- **CRUD đầy đủ:** Thêm mới, sửa, cập nhật nhanh trạng thái đơn (`Còn hàng`, `Đã bán`, `Đợi CK`, `Đã xóa`).
- **Lọc và tìm kiếm nhanh:** Lọc đa điều kiện theo trạng thái, nhân viên chốt, phương thức vận chuyển, khoảng ngày.
- **Xuất báo cáo:** Hỗ trợ xuất dữ liệu lọc ra định dạng file CSV trực tiếp từ trình duyệt.

### 4.4. Tra cứu Mã SP & Lịch sử khách hàng
- Tra cứu nhanh trạng thái sản phẩm bằng Mã SP/SKU.
- Nhập số điện thoại khách hàng để xem toàn bộ lịch sử các đơn hàng đã mua, tổng tiền đã chi (LTV), cấp bậc VIP và các lưu ý giao dịch trước đó.

### 4.5. Phân tích doanh số chuyên sâu (`StatsService.js`)
- Lọc theo chu kỳ linh hoạt: Hôm nay, Hôm qua, 7 ngày qua, 30 ngày qua, Tháng này, Tháng trước, Quý này, Năm nay, hoặc Khoảng ngày tùy chọn.
- Tự động tính toán **tốc độ tăng trưởng (% growth)** so với kỳ trước đó đối với: Doanh thu, Lợi nhuận, Số đơn, Giá trị trung bình đơn (AOV).
- Báo cáo Data Quality: Tự động rà soát phát hiện các dòng thiếu ngày chốt, sai định dạng tiền, dữ liệu rác trên Sheet.

### 4.6. Trợ lý AI Gemini (`gemini-2.0-flash`)
- Tích hợp cửa sổ chat thông minh ngay trên Dashboard.
- Cung cấp ngữ cảnh thực tế của shop (doanh thu tháng, top sản phẩm bán chạy, danh sách khách hàng VIP, khách hàng cần gọi lại...).
- Hỗ trợ các câu hỏi mẫu như:
  - *"Doanh thu hôm nay/tháng này thế nào?"*
  - *"Tại sao doanh thu giảm?"*
  - *"Sản phẩm nào bán tốt nhất?"*
  - *"Danh sách khách hàng cần gọi lại thoại chăm sóc?"*

### 4.7. Tự động hóa & Tích hợp Telegram Bot
- **Thông báo đa kênh:**
  - Tự động gửi tin nhắn Telegram khi có đơn hàng mới hoặc đơn hàng được chốt sang trạng thái `Đã bán`.
  - Hỗ trợ cả 2 cơ chế: Bấm lưu từ Web App và sửa trực tiếp trên Google Sheets (thông qua Installable Trigger `onEdit`).
- **Bot tra cứu tồn kho:** Người bán hàng/nhân viên có thể chat trực tiếp với Bot Telegram bằng cú pháp mã sản phẩm để kiểm tra hàng còn hay đã bán ngay lập tức.
- **Báo cáo định kỳ:** Gửi báo cáo tổng hợp tình hình kinh doanh mỗi ngày qua Telegram.
- **Cảnh báo vận hành (Alerts):** Cảnh báo đơn đợi chuyển khoản quá lâu, đơn trễ hẹn giao hàng, COD chưa đối soát...

### 4.8. Quản trị & Bảo mật
- **Bảo mật truy cập:** Yêu cầu mật khẩu đăng nhập (mặc định cấu hình trong `ScriptProperties`).
- **Sao lưu tự động (Automated Backup):** Tự động clone bản sao của Spreadsheet sang thư mục sao lưu trên Google Drive theo lịch định kỳ.
- **Kiểm toán hệ thống (System Health Audit):** Kiểm tra trạng thái các triggers, sức khỏe cấu trúc bảng tính, dung lượng cache.
- **Nhật ký hoạt động (Activity Logs):** Ghi nhận chi tiết lịch sử thao tác thêm, sửa, xóa của người dùng.

---

## 5. ⚙️ Cấu Hình Hệ Thống (Script Properties)

Các biến cấu hình được lưu trữ an toàn trong **Script Properties** của Google Apps Script:

| Tên Thuộc Tính | Mô Tả | Giá Trị Mặc Định / Ví Dụ |
| :--- | :--- | :--- |
| `SALES_ADMIN_PASSWORD` | Mật khẩu đăng nhập vào Web App | `1512` |
| `TELEGRAM_BOT_TOKEN` | Token của Telegram Bot tạo từ @BotFather | `123456789:ABCdefGHIjkl...` |
| `TELEGRAM_CHAT_ID` | Chat ID của nhóm nhận thông báo bán hàng | `-100xxxxxxxxxx` |
| `GEMINI_API_KEY` | Khóa API Google Gemini AI | `AIzaSy...` |
| `GEMINI_MODEL` | Tên model Gemini sử dụng | `gemini-2.0-flash` |
| `SALES_ADMIN_CUSTOMER_VIP_TIER_CONFIG_V1` | JSON cấu hình tên hạng và mốc tiền VIP | Tự động sinh từ hệ thống |

---

## 6. 🛠️ Hướng Dẫn Phát Triển & Triển Khai (Deployment)

Mã nguồn được quản lý bằng **Google Clasp**:

### 1. Đồng bộ code từ máy lên Apps Script
```powershell
cd d:\CV\Anta_new\app_scipt
clasp push
```

### 2. Kéo code mới nhất từ Apps Script về máy
```powershell
cd d:\CV\Anta_new\app_scipt
clasp pull
```

### 3. Đồng bộ giao diện sang bản Vercel
`Script.html` / `Style.html` là bản gốc. `vercel_frontend/script.js` và `style.css` được sinh từ chúng, **không sửa tay**:
```powershell
cd app_script_admin
node sync-frontend.js          # sinh lại script.js, style.css cho bản Vercel
node sync-frontend.js --check  # chỉ kiểm tra có lệch không (exit 1 nếu lệch)
```
`Index.html` không đồng bộ tự động vì bản Vercel có phần riêng (adapter, link CSS, cấu hình VIP).

### 4. Cài đặt các Trigger tự động
Trong giao diện Web App, truy cập mục **Cấu hình hệ thống (Settings)** hoặc chạy các hàm sau từ trình soạn thảo Apps Script:
- `ensureAllSystemTriggersInstalled()`: Kích hoạt toàn bộ trigger (onEdit, pending queue, backup, daily report).
- `setupTelegramWebhook()`: Đăng ký Webhook cho Telegram Bot phục vụ tra cứu mã sản phẩm.

---

## 7. 📝 Tổng Kết

Dự án **Sales Admin System** là một giải pháp hoàn chỉnh, chuyên nghiệp cho việc vận hành kinh doanh bán lẻ và thương mại điện tử dựa trên Google Workspace. Với sự kết hợp giữa giao diện Web App mượt mà, phân tích dữ liệu chuyên sâu và tự động hóa qua Telegram & AI Gemini, hệ thống giúp tối ưu hóa tối đa quy trình xử lý đơn hàng và chăm sóc khách hàng.
