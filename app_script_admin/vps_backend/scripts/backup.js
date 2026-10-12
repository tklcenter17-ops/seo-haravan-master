const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

let DB_PATH = path.join(__dirname, '..', 'data', 'sales_admin.db');
if (!fs.existsSync(DB_PATH)) {
  const altPath = path.join(__dirname, '..', 'sales_admin.db');
  if (fs.existsSync(altPath)) DB_PATH = altPath;
}
const BACKUP_DIR = path.join(__dirname, '..', 'backups');
const MAX_AGE_DAYS = 14;
const MAX_AGE_MS = MAX_AGE_DAYS * 24 * 60 * 60 * 1000;

function formatTimestamp(d = new Date()) {
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}_${pad(d.getMonth() + 1)}_${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

async function runBackup() {
  const now = new Date();
  console.log(`[Backup ${now.toISOString()}] Bắt đầu quy trình sao lưu VPS...`);

  if (!fs.existsSync(DB_PATH)) {
    console.error(`[Backup Error] Không tìm thấy database tại: ${DB_PATH}`);
    process.exit(1);
  }

  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
  }

  const targetFilename = `sales_admin_${formatTimestamp(now)}.db.gz`;
  const targetPath = path.join(BACKUP_DIR, targetFilename);

  const readStream = fs.createReadStream(DB_PATH);
  const writeStream = fs.createWriteStream(targetPath);
  const gzip = zlib.createGzip({ level: 9 });

  await new Promise((resolve, reject) => {
    readStream
      .pipe(gzip)
      .pipe(writeStream)
      .on('finish', () => {
        const stats = fs.statSync(targetPath);
        console.log(`[Backup Success] Đã nén thành công: ${targetFilename} (${(stats.size / 1024).toFixed(1)} KB)`);
        resolve();
      })
      .on('error', (err) => {
        console.error('[Backup Pipe Error]:', err);
        reject(err);
      });
  });

  console.log(`[Backup Clean] Bắt đầu quét file cũ quá ${MAX_AGE_DAYS} ngày...`);
  const files = fs.readdirSync(BACKUP_DIR);
  let deletedCount = 0;

  files.forEach((file) => {
    if (!file.endsWith('.db.gz')) return;
    const filePath = path.join(BACKUP_DIR, file);
    try {
      const stat = fs.statSync(filePath);
      if (Date.now() - stat.mtimeMs > MAX_AGE_MS) {
        fs.unlinkSync(filePath);
        deletedCount++;
        console.log(`  - Đã xóa file cũ: ${file}`);
      }
    } catch (e) {
      console.warn(`  - Lỗi kiểm tra file ${file}:`, e.message);
    }
  });

  console.log(`[Backup Finish] Hoàn tất sao lưu. Đã xóa ${deletedCount} file cũ quá hạn.`);
}

if (require.main === module) {
  runBackup().catch((err) => {
    console.error('[Backup Fatal Error]:', err);
    process.exit(1);
  });
}

module.exports = { runBackup };
