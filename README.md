# Telegram Bot Ghi Nhớ Giá Đấu Quẹt (Phiên bản V1)

Bot Telegram cá nhân giúp ghi nhớ giá đấu thắng của từng cây quẹt (Dupont, Zippo, Dunhill...), tra cứu tức thì khi đang đấu, và đặt mốc trần bid cá nhân.

---

## 1. Tính năng cốt lõi (V1)

- **Nhập 1 dòng siêu tốc**: 
  - Cú pháp: `/data dupont sơn mài 1 line xanh lá có box 13.400Y`
  - Hỗ trợ thêm phí/ghi chú sau dấu pipe: `| phí nhật=1200Y | tình trạng=đẹp | ngày=2026-09-07`
  - Tự động nhận diện trường hợp mơ hồ (ví dụ: `full boc` -> bot tạo bản nháp và hỏi chọn: Có hộp / Đủ hộp giấy / Giữ nguyên mô tả).
- **Tra cứu thông minh (Natural Search)**:
  - Gõ tên quẹt tự nhiên không cần lệnh: `dupont son mai 1 line xanh la`
  - Bỏ từ đệm câu hỏi: `cây dupont 1 line xanh lá giá bao nhiêu`
  - Phân tách nhóm so sánh chính xác (không gộp line 1 với line 2; không tự bù trừ hộp hay tình trạng).
- **Chính sách mốc bid tham khảo**:
  - Có trần cá nhân: Hiển thị đúng mức trần bạn đã đặt.
  - 1 giao dịch: Hiển thị giá từng thắng (ghi rõ 1 bản ghi, không bịa giá thị trường).
  - 2 giao dịch: Hiển thị khoảng giá (min - max), không tự chốt 1 con số.
  - Từ 3 giao dịch: Tính trung vị (median) trên cửa sổ 180 ngày hoặc toàn bộ lịch sử.
- **Bảo mật & Độ bền**:
  - Chỉ cho phép đúng `TELEGRAM_OWNER_ID` được cấu hình sử dụng.
  - SQLite WAL mode, Transaction an toàn, FTS5 tìm kiếm toàn văn.
  - Idempotency chống lặp tin nhắn, hỗ trợ hoàn tác `/undo`.
  - SQLite Native Backup API cho phép snapshot trực tiếp khi bot đang chạy.

---

## 2. Hướng dẫn Cài đặt & Cấu hình

### Bước 1: Tạo Bot Telegram & Lấy thông tin
1. Mở Telegram, tìm `@BotFather` và gõ `/newbot` để tạo bot mới, đặt tên và nhận `TELEGRAM_BOT_TOKEN`.
2. Tìm `@userinfobot` trên Telegram để lấy `Id` của bạn (ví dụ: `123456789`) -> đây là `TELEGRAM_OWNER_ID`.

### Bước 2: Thiết lập file môi trường `.env`
Sao chép file mẫu `.env.example` thành `.env`:
```bash
cp .env.example .env
```
Mở file `.env` và điền thông tin:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_OWNER_ID=123456789
DB_PATH=data/quet_vault.db
BACKUP_DIR=backups
PRICE_HIGH_THRESHOLD_JPY=500000
```

### Bước 3: Cài đặt thư viện
```bash
pip install -r requirements.txt
```

---

## 3. Chạy Kiểm Thử (Acceptance Tests)

Toàn bộ 30 ca kiểm thử nghiệp vụ (T01 - T30) được tự động hóa bằng pytest:
```bash
pytest tests/test_suite.py -v
```
Kết quả kiểm thử đạt 100% PASS (31 passed).

---

## 4. Khởi Chạy Bot

Khởi chạy ứng dụng ở chế độ Long Polling:
```bash
python bot.py
```
Khi chạy thành công, bot sẽ ghi log:
```
Khởi tạo database tại .../data/quet_vault.db thành công.
Bot đang khởi động ở chế độ Long Polling...
```

---

## 5. Danh mục Lệnh (Commands)

| Lệnh | Ý nghĩa |
|---|---|
| `/start`, `/help` | Mở menu chính và hướng dẫn sử dụng |
| `/data <mô tả> <giá>` | Lưu giá thắng (mặc định JPY, ví dụ: `13.400Y` hoặc `13400`) |
| Gõ tên quẹt hoặc `/find <từ khóa>` | Tra cứu lịch sử giá và mốc tham khảo |
| `/recent` | Xem 10 bản ghi đã lưu gần nhất |
| `/view <ID>` | Xem chi tiết bản ghi (ví dụ: `/view Q0001`) |
| `/delete <ID>` | Xóa mềm bản ghi (có nút xác nhận) |
| `/undo` | Hoàn tác thao tác dữ liệu gần nhất |
| `/cap <ID> <giá>` | Đặt trần bid cá nhân cho nhóm so sánh của cây đó |
| `/cap <ID> off` | Tắt trần bid cá nhân đã đặt |
| `/stats` | Xem thống kê số lượng bản ghi và nhãn hiệu |
| `/export` | Xuất dữ liệu ra file JSON và CSV UTF-8 (mở chuẩn Excel) |
| `/cancel` | Hủy thao tác / bản nháp đang xử lý |

---

## 6. Quy trình Sao lưu (Backup) & Phục hồi (Restore)

Hệ thống sử dụng **SQLite Backup API** native của Python (`sqlite3.Connection.backup`), đảm bảo file backup luôn nhất quán ngay cả khi bot đang nhận ghi dữ liệu.

### Thực hiện Snapshot Backup thủ công hoặc định kỳ:
Chạy script Python nhỏ:
```python
from pathlib import Path
from db import get_db_connection, backup_database
from config import load_config

cfg = load_config()
conn = get_db_connection(cfg.db_path)
backup_database(conn, Path("backups/quet_vault_backup.db"))
conn.close()
print("Backup thành công!")
```

### Phục hồi sang Database mới:
```python
from pathlib import Path
from db import restore_database

ok = restore_database("backups/quet_vault_backup.db", "data/quet_vault_restored.db")
if ok:
    print("Khôi phục thành công và toàn vẹn 100% dữ liệu!")
```
