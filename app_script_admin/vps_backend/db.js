const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const dbPath = path.join(dataDir, 'sales_admin.db');
const db = new Database(dbPath);

// Enable WAL mode for high concurrency
db.pragma('journal_mode = WAL');

// Initialize tables
db.exec(`
CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sheet_name TEXT DEFAULT 'SalesData',
  ma_sp TEXT UNIQUE NOT NULL,
  san_pham TEXT,
  gia_ban REAL DEFAULT 0,
  gia_von REAL DEFAULT 0,
  tien_loi REAL DEFAULT 0,
  tien_cod REAL DEFAULT 0,
  khach_coc REAL DEFAULT 0,
  ten_khach TEXT,
  sdt_khach TEXT,
  ai_chot TEXT,
  ngay_chot TEXT,
  trang_thai TEXT DEFAULT 'Còn hàng',
  hinh_thuc TEXT DEFAULT 'COD',
  dia_chi TEXT,
  ghi_chu TEXT,
  ngay_tao TEXT,
  updated_at TEXT,
  synced_to_sheet INTEGER DEFAULT 1,
  sync_source TEXT DEFAULT 'vps'
);

CREATE INDEX IF NOT EXISTS idx_orders_masp ON orders(ma_sp);
CREATE INDEX IF NOT EXISTS idx_orders_ngaychot ON orders(ngay_chot);
CREATE INDEX IF NOT EXISTS idx_orders_sdt ON orders(sdt_khach);
CREATE INDEX IF NOT EXISTS idx_orders_trangthai ON orders(trang_thai);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS activity_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action TEXT,
  details TEXT,
  timestamp TEXT
);
`);

// Migration: Ensure Viettel Post columns exist in orders table
try {
  const cols = db.pragma('table_info(orders)').map(c => c.name);
  if (!cols.includes('loai_hang_hoa')) {
    db.exec("ALTER TABLE orders ADD COLUMN loai_hang_hoa TEXT DEFAULT 'Bưu kiện'");
  }
  if (!cols.includes('tinh_chat_hang_hoa')) {
    db.exec("ALTER TABLE orders ADD COLUMN tinh_chat_hang_hoa TEXT DEFAULT ''");
  }
  if (!cols.includes('dich_vu')) {
    db.exec("ALTER TABLE orders ADD COLUMN dich_vu TEXT DEFAULT ''");
  }
  if (!cols.includes('dich_vu_cong_them')) {
    db.exec("ALTER TABLE orders ADD COLUMN dich_vu_cong_them TEXT DEFAULT ''");
  }
} catch (e) {
  console.warn('[DB Migration Warning]:', e.message);
}

// Helper to get a setting
function getSetting(key, fallback = null) {
  const row = db.prepare('SELECT value FROM settings WHERE key = ?').get(key);
  return row ? row.value : fallback;
}

function setSetting(key, value) {
  db.prepare('INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value').run(key, String(value));
}

// Ensure default settings
if (!getSetting('SALES_ADMIN_PASSWORD')) {
  setSetting('SALES_ADMIN_PASSWORD', '1512');
}

module.exports = {
  db,
  getSetting,
  setSetting
};
