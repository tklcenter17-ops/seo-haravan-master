# 📋 HƯỚNG DẪN LÀM VIỆC TẠI NHÀ — DỰ ÁN SALES ADMIN SYSTEM
> **Tài liệu hướng dẫn đồng bộ và làm việc từ xa tối nay**  
> **Repository:** `tklcenter17-ops/seo-haravan-master`  
> **Thư mục dự án:** `app_script_admin/`  
> **Ngày tạo:** 12/10/2026  

---

## 1. 🚀 Bước 1: Kéo Code Về Máy Tính Ở Nhà

Mở Terminal / PowerShell / Git Bash trên máy tính ở nhà:

### A. Nếu máy tính ở nhà ĐÃ CÓ sẵn repo này từ trước:
```bash
# Di chuyển vào thư mục repo trên máy bạn
cd duong-dan-den/seo-haravan-master

# Kéo toàn bộ code mới nhất đã cập nhật từ công ty về
git pull origin master

# Di chuyển vào thư mục dự án
cd app_script_admin
```

### B. Nếu máy tính ở nhà CHƯA CÓ repo:
```bash
# Clone qua SSH (nếu máy nhà đã cài SSH key GitHub):
git clone git@github.com:tklcenter17-ops/seo-haravan-master.git

# HOẶC clone qua HTTPS (nếu máy nhà chưa setup SSH):
git clone https://github.com/tklcenter17-ops/seo-haravan-master.git

# Di chuyển vào dự án:
cd seo-haravan-master/app_script_admin
```

---

## 2. 📁 Cấu Trúc Các Phân Hệ & Vị Trí Cần Sửa

Thư mục `app_script_admin/` bao gồm 3 phân hệ chính:

```text
app_script_admin/
├── 🟢 PHÂN HỆ 1: GOOGLE APPS SCRIPT (Chính)
│   ├── Code.js              # Backend chính: CRUD Sheet, Telegram Bot, Gemini AI (~4.5k dòng)
│   ├── StatsService.js      # Service thống kê: KPI, % tăng trưởng, audit dữ liệu
│   ├── Index.html           # Khung giao diện HTML: SPA Dashboard, Modal, Sidebar
│   ├── Script.html          # Logic JavaScript Client: Chart.js, xử lý sự kiện, gọi backend
│   ├── Style.html           # Toàn bộ CSS, Dark/Light mode theme, Responsive UI
│   ├── appsscript.json      # File manifest môi trường Apps Script
│   ├── .clasp.json          # File cấu hình Clasp CLI (Script ID đã có sẵn)
│   └── README.md            # Tài liệu tổng quan chi tiết của dự án
│
├── 🔵 PHÂN HỆ 2: VERCEL FRONTEND (Nếu chạy/host độc lập)
│   └── vercel_frontend/
│       ├── index.html, script.js, style.css
│       └── adapter.js       # Adapter chuyển đổi API
│
└── 🟠 PHÂN HỆ 3: VPS BACKEND (Nếu chạy server Node.js riêng)
    └── vps_backend/
        ├── server.js        # Server Express
        ├── db.js            # SQLite database helper
        └── stats.js         # Logic thống kê
```

---

## 3. ⚙️ Hướng Dẫn Đồng Bộ Với Google Apps Script (Clasp)

Nếu tối nay bạn muốn test hoặc đẩy code trực tiếp lên Google Apps Script:

### 1. Cài đặt Clasp (nếu máy nhà chưa có):
```bash
npm install -g @google/clasp
```

### 2. Đăng nhập tài khoản Google quản lý Script:
```bash
clasp login
```

### 3. Đẩy code lên Google Apps Script:
File `.clasp.json` đã có sẵn Script ID: `1tzooqgSnUyCdOKqQwJ5mz99CkHuT9naZNPJzv9M5WgQxJ1rPKlsSJoND`  
Từ thư mục `app_script_admin`, chỉ cần chạy:
```bash
# Đẩy toàn bộ code lên Google Apps Script:
clasp push

# Mở nhanh trình duyệt vào màn hình Apps Script Editor:
clasp open
```

---

## 4. 🌐 Hướng Dẫn Chạy Thử Local Trên Máy Tính

### Cách 1: Test nhanh giao diện (Frontend)
Mở file `app_script_admin/vercel_frontend/index.html` trực tiếp bằng trình duyệt (hoặc dùng tiện ích **Live Server** trong VS Code).

### Cách 2: Chạy Backend Node.js độc lập (Nếu làm việc trên VPS Backend)
```bash
cd vps_backend
npm install
node server.js
```
*Server sẽ chạy tại `http://localhost:3000`.*

---

## 5. 📤 Bước Cuối: Đẩy Lại Lên GitHub Sau Khi Làm Xong Tối Nay

Sau khi code xong ở nhà, bạn chạy các lệnh sau để đẩy code lên GitHub để sáng mai lên công ty làm tiếp:

```bash
# 1. Đứng tại thư mục gốc của repo:
cd ..   # nếu đang ở trong app_script_admin

# 2. Kiểm tra các file đã chỉnh sửa:
git status

# 3. Thêm các file của app_script_admin:
git add app_script_admin/

# 4. Tạo commit:
git commit -m "feat(app_script_admin): cap nhat code buoi toi tai nha"

# 5. Đẩy lên GitHub:
git push origin master
```

---

## 6. ☀️ Sáng Mai Lên Công Ty Cần Làm Gì?

Chỉ cần mở terminal máy công ty tại `d:\CV\Anta_new` và gõ:
```bash
git pull origin master
```
👉 Toàn bộ thành quả bạn làm ở nhà tối nay sẽ lập tức cập nhật về máy công ty! 🚀

---

## 7. 📦 Tính Năng Mới: Nút "Xuất Excel Chuẩn ViettelPost"

Hệ thống đã có sẵn nút **"Xuất Excel ViettelPost"** màu đỏ nổi bật tại 3 vị trí:
1. **Quản lý sản phẩm (`#page-products`):** Nằm cạnh nút "Xuất CSV" ở thanh toolbar trên cùng. Bấm vào sẽ tự động lọc các đơn có thông tin khách và xuất ra file Excel.
2. **Đơn chốt theo ngày (`#page-daily`):** Nằm ở thanh điều khiển ngày. Bấm vào sẽ lấy toàn bộ đơn hàng trong ngày và xuất file Excel.
3. **Tạo đơn Viettel (`#page-viettel_orders`):** Nằm ở menu thanh bên (Sidebar), cho phép quản lý chi tiết từng kiện hàng đã gộp.

### ✨ Các trường dữ liệu được tự động điền chuẩn 100%:
- **Trọng lượng:** Mặc định `300` gram (nếu chưa nhập).
- **Người trả cước:** Tự động điền `Người nhận trả cước` (với đơn COD) hoặc `Người gửi trả cước` (với đơn Freeship/CK đủ).
- **Tiền COD:** = `0` nếu đã CK đủ; = `Giá bán` nếu thu hộ COD.
- **Giá trị hàng hóa:** Luôn đảm bảo `> 0` để ViettelPost không báo lỗi thiếu trường bắt buộc.
- **Yêu cầu giao hàng:** Luôn kèm `Cho xem hàng không cho thử`.
- **Số điện thoại:** Định dạng chuẩn văn bản `@` giữ nguyên số 0 ở đầu.

👉 **Cách tạo đơn trên web ViettelPost:**
1. Bấm nút **"Xuất Excel ViettelPost"** trên Web App để tải file `.xlsx`.
2. Mở web [viettelpost.com.vn](https://viettelpost.com.vn) ➔ Vào mục **Tạo đơn** ➔ Chọn **Nhập Excel**.
3. Kéo thả file vừa tải lên ➔ Hệ thống xanh 100%, không bị báo thiếu data ➔ Bấm **Đẩy đơn** là xong!

---

## ⚠️ Lưu Ý Quan Trọng
- **Không chỉnh sửa thư mục `seo/`**: Thư mục `seo/` dùng riêng cho dự án SEO Theme Haravan.
- **Không hardcode thông tin nhạy cảm**: Không ghi mật khẩu hay Bot Token trực tiếp vào code; hãy dùng `ScriptProperties` của Google Apps Script hoặc biến môi trường `.env`.
- **Cơ sở dữ liệu VPS an toàn 100%**: File database `sales_admin.db` lưu trên VPS `103.166.185.85` hoàn toàn không bị ảnh hưởng khi deploy Vercel hoặc cập nhật code frontend.
