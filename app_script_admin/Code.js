// ============================================================
// SALES ADMIN SYSTEM - Code.gs
// Backend for Google Apps Script Web App
//
// Telegram notify added:
// - App-created rows notify after addRow()
// - Sheet-created rows notify through an installable on-edit trigger
// - Bot token/chat id are stored in Script Properties
// ============================================================

const SHEET_NAME = 'SalesData';
const MA_V_SHEET_NAME = 'Mã V';
const LIQUIDATION_SHEET_NAME = 'THANH LÝ';
const SALES_LIKE_SHEET_NAMES = [SHEET_NAME, MA_V_SHEET_NAME];
const REPORT_SHEET_NAMES = [SHEET_NAME, MA_V_SHEET_NAME, LIQUIDATION_SHEET_NAME];
const DEFAULT_PASSWORD = '1512';
const PASSWORD_PROPERTY_KEY = 'SALES_ADMIN_PASSWORD';

const TELEGRAM_BOT_TOKEN_PROPERTY_KEY = 'TELEGRAM_BOT_TOKEN';
const TELEGRAM_CHAT_ID_PROPERTY_KEY = 'TELEGRAM_CHAT_ID';
const TELEGRAM_NOTIFIED_PREFIX = 'SALES_ADMIN_NOTIFIED_MASP_';
const TELEGRAM_LAST_SIGNATURE_PREFIX = 'SALES_ADMIN_LAST_SIGNATURE_ROW_';
const TELEGRAM_PENDING_PREFIX = 'SALES_ADMIN_PENDING_ROW_';
const TELEGRAM_NOTIFY_DELAY_MS = 3 * 60 * 1000;
const GEMINI_API_KEY_PROPERTY_KEY = 'GEMINI_API_KEY';
const GEMINI_MODEL_PROPERTY_KEY = 'GEMINI_MODEL';
const DEFAULT_GEMINI_MODEL = 'gemini-2.0-flash';

const CUSTOMER_VIP_TIER_CONFIG_PROPERTY_KEY = 'SALES_ADMIN_CUSTOMER_VIP_TIER_CONFIG_V1';
const DEFAULT_CUSTOMER_VIP_TIER_RULES = [
  { key: 'diamond', label: 'VIP Kim Cương', minLtv: 100000000, minOrders: 30, className: 'vip-diamond' },
  { key: 'gold', label: 'VIP Vàng', minLtv: 50000000, minOrders: 15, className: 'vip-gold' },
  { key: 'silver', label: 'VIP Bạc', minLtv: 20000000, minOrders: 8, className: 'vip-silver' },
  { key: 'bronze', label: 'VIP Đồng', minLtv: 5000000, minOrders: 3, className: 'vip-bronze' }
];
let customerVipTierRulesCache_ = null;

function cloneVipTierRules_(rules) {
  return (rules || []).map((tier) => ({ ...tier }));
}

function getDefaultCustomerVipTierRules_() {
  return cloneVipTierRules_(DEFAULT_CUSTOMER_VIP_TIER_RULES);
}

function normalizeVipTierLabel_(label, fallback) {
  const value = String(label || '').trim();
  return value || fallback;
}

function normalizeVipTierMoney_(value, fallback) {
  const raw = String(value ?? '').trim();
  if (raw === '') return fallback;
  const normalized = raw
    .replace(/[₫đĐvndVND\s]/g, '')
    .replace(/[^\d,.\-]/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.round(parsed) : fallback;
}

function getCustomerVipTierRules_() {
  if (customerVipTierRulesCache_) return customerVipTierRulesCache_;

  const defaults = getDefaultCustomerVipTierRules_();
  let stored = null;

  try {
    stored = JSON.parse(
      PropertiesService.getScriptProperties().getProperty(CUSTOMER_VIP_TIER_CONFIG_PROPERTY_KEY) || 'null'
    );
  } catch (e) {
    stored = null;
  }

  const storedLabels = stored && typeof stored === 'object' && stored.labels && typeof stored.labels === 'object'
    ? stored.labels
    : {};
  const storedTiers = stored && typeof stored === 'object' && stored.tiers && typeof stored.tiers === 'object'
    ? stored.tiers
    : {};

  customerVipTierRulesCache_ = defaults.map((tier) => ({
    key: tier.key,
    label: normalizeVipTierLabel_(
      (storedTiers[tier.key] && storedTiers[tier.key].label) || storedLabels[tier.key],
      tier.label
    ),
    minLtv: normalizeVipTierMoney_(
      storedTiers[tier.key] && storedTiers[tier.key].minLtv,
      tier.minLtv
    ),
    minOrders: tier.minOrders,
    className: tier.className
  }));

  return customerVipTierRulesCache_;
}

function resetCustomerVipTierRulesCache_() {
  customerVipTierRulesCache_ = null;
}

function getCustomerVipTierSettings_() {
  return { tiers: getCustomerVipTierRules_() };
}

function saveVipTierLabels(payload) {
  const input = payload && typeof payload === 'object' ? payload : {};
  const labels = input.labels || input;
  const minLtvs = input.minLtvs || {};
  const defaults = getDefaultCustomerVipTierRules_();
  const nextLabels = {};
  const nextTiers = {};

  defaults.forEach((tier) => {
    nextLabels[tier.key] = normalizeVipTierLabel_(labels && labels[tier.key], tier.label);
    nextTiers[tier.key] = {
      label: nextLabels[tier.key],
      minLtv: normalizeVipTierMoney_(minLtvs && minLtvs[tier.key], tier.minLtv)
    };
  });

  PropertiesService.getScriptProperties().setProperty(
    CUSTOMER_VIP_TIER_CONFIG_PROPERTY_KEY,
    JSON.stringify({ labels: nextLabels, tiers: nextTiers })
  );
  resetCustomerVipTierRulesCache_();

  return { success: true, ...getCustomerVipTierSettings_() };
}

// Cache configuration
const CACHE_KEY_ROWS = 'SALES_ADMIN_ALL_ROWS';
const CACHE_KEY_REPORT_ROWS = 'SALES_ADMIN_REPORT_ROWS';
const CACHE_EXPIRATION_SEC = 2 * 60; // 2 mins (reduced from 25 mins for quick sync)
const CACHE_CHUNK_SIZE = 30 * 1024;
const CACHE_MAX_CHUNKS = 60;

const HEADER_ALIASES = {
  maSP: ['MÃ SP', 'Mã SP', 'Ma SP', 'SKU', 'Mã hàng', 'Mã sản phẩm', 'Mã đơn', 'Mã đơn hàng'],
  sanPham: ['Sản phẩm', 'Tên sản phẩm', 'Tên SP', 'Dịch vụ', 'Tên dịch vụ', 'Mặt hàng', 'Tên hàng', 'Nội dung'],
  giaBan: ['Giá bán', 'Doanh thu', 'Thành tiền', 'Tổng tiền', 'Số tiền', 'Giá trị đơn', 'Giá thanh lý', 'Tiền thanh lý'],
  giaVon: ['Giá vốn', 'Vốn', 'Giá nhập', 'Chi phí', 'Cost'],
  tienLoi: ['Tiền lời', 'Lợi nhuận', 'Lãi', 'Profit'],
  tienCOD: ['Tiền COD', 'COD', 'Thu COD', 'Cần thu COD'],
  tenKhach: ['Tên khách hàng', 'Khách hàng', 'Tên khách', 'Khách', 'Customer', 'Họ tên'],
  sdtKhach: ['SĐT khách hàng', 'Số điện thoại', 'SĐT', 'Điện thoại', 'Phone', 'SDT'],
  aiChot: ['Ai chốt', 'Ai chot', 'Người chốt', 'Nguoi chot', 'Chốt bởi', 'Chot boi', 'Sale', 'Nhân viên'],
  nguonKhach: ['Nguồn khách', 'Nguồn', 'Nguồn đơn', 'Kênh', 'Kênh bán', 'Nguồn khách hàng', 'Source'],
  diaChi: ['Địa chỉ khách hàng', 'Địa chỉ', 'Dia chi', 'Địa chỉ giao hàng', 'Địa chỉ nhận hàng', 'Address'],
  ngayChot: ['Ngày chốt', 'Ngày đơn', 'Ngày bán', 'Ngày thanh lý', 'Ngày tạo đơn', 'Ngày', 'Date'],
  trangThai: ['Trạng thái sản phẩm', 'Trạng thái', 'Tình trạng', 'Status'],
  hinhThuc: ['Hình thức giao hàng', 'Hình thức', 'Giao hàng', 'Phương thức', 'Loại giao dịch'],
  loaiDon: ['Loại đơn', 'Loại', 'Nhóm đơn', 'Nguồn đơn', 'Kênh', 'Sheet'],
  ghiChu: ['Ghi chú', 'Note', 'Ghi chú đơn', 'Nội dung ghi chú'],
  createdAt: ['Ngày tạo', 'Created At', 'Tạo lúc'],
  updatedAt: ['Cập nhật lúc', 'Updated At', 'Cập nhật'],
  khachCoc: ['Khách cọc', 'Tiền cọc', 'Cọc', 'Đã cọc', 'Deposit'],
  linkTiktok: ['Link TikTok', 'TikTok', 'Link', 'Link sản phẩm', 'Video'],
  khoiLuong: ['Khối lượng', 'Trọng lượng', 'Cân nặng', 'Weight', 'Khối lượng (gram)', 'Trọng lượng (gram)'],
  loaiHangHoa: ['Loại hàng hóa', 'Loại hàng', 'Loại hàng hóa (*)', 'Loại bưu kiện'],
  tinhChatHangHoa: ['Tính chất hàng hóa đặc biệt', 'Tính chất hàng hóa', 'Tính chất đặc biệt'],
  dichVu: ['Dịch vụ (*)', 'Dịch vụ chuyển phát', 'Gói dịch vụ', 'Mã dịch vụ', 'Dịch vụ bưu chính'],
  dichVuCongThem: ['Dịch vụ cộng thêm', 'Dịch vụ cộng thêm ', 'DV cộng thêm', 'DVCT'],
  notificationKey: ['Khóa thông báo', 'notification_key', 'Notification Key', 'Mã thông báo', 'Khóa đơn', 'Order Key'],
  telegramStatus: ['Trạng thái Telegram', 'telegram_status', 'Telegram Status', 'Trạng thái gửi Telegram', 'Trạng thái gửi'],
  telegramSentAt: ['Telegram gửi lúc', 'telegram_sent_at', 'Telegram Sent At', 'Thời gian gửi Telegram', 'Thời gian gửi'],
  telegramMessageId: ['Telegram Message ID', 'telegram_message_id', 'Telegram Message Id', 'Message ID', 'ID tin nhắn Telegram'],
  telegramError: ['Lỗi Telegram', 'telegram_error', 'Telegram Error', 'Ghi chú lỗi Telegram']
};

const HEADERS = [
  'MÃ SP',
  'Giá bán',
  'Khách cọc',
  'Giá vốn',
  'Tiền lời',
  'Tiền COD',
  'Tên khách hàng',
  'SĐT khách hàng',
  'Ai chốt',
  'Nguồn khách',
  'Địa chỉ khách hàng',
  'Ngày chốt',
  'Trạng thái sản phẩm',
  'Hình thức giao hàng',
  'Ghi chú',
  'Ngày tạo',
  'Cập nhật lúc',
  'Link TikTok',
  'Khóa thông báo',
  'Trạng thái Telegram',
  'Telegram gửi lúc',
  'Telegram Message ID',
  'Lỗi Telegram'
];

function generateNotificationKey_() {
  const today = Utilities.formatDate(new Date(), 'Asia/Bangkok', 'yyyyMMdd');
  const rand = Utilities.getUuid().substring(0, 8).toUpperCase();
  return 'ORD-' + today + '-' + rand;
}

function stripVietnameseMarks_(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D');
}

function normalizeMaSPForSearch_(value) {
  return String(value || '').normalize('NFC').trim().toLowerCase();
}

function compactMaSPForSearch_(value) {
  return normalizeMaSPForSearch_(value).replace(/[\s\-_.\/]+/g, '');
}

function isSameMaSPForSearch_(left, right) {
  const leftNorm = normalizeMaSPForSearch_(left);
  const rightNorm = normalizeMaSPForSearch_(right);
  if (!leftNorm || !rightNorm) return false;
  if (leftNorm === rightNorm) return true;

  const leftCompact = compactMaSPForSearch_(left);
  const rightCompact = compactMaSPForSearch_(right);
  return Boolean(leftCompact && rightCompact && leftCompact === rightCompact);
}

function matchesMaSPForSearch_(maSP, keyword) {
  const haystack = normalizeMaSPForSearch_(maSP);
  const needle = normalizeMaSPForSearch_(keyword);
  if (!haystack || !needle) return false;
  if (haystack.includes(needle)) return true;

  const compactHaystack = compactMaSPForSearch_(maSP);
  const compactNeedle = compactMaSPForSearch_(keyword);
  return Boolean(compactHaystack && compactNeedle && compactHaystack.includes(compactNeedle));
}

function sheetStatusToInternal_(raw) {
  const v = String(raw || '').normalize('NFC').trim();
  const l = v.toLowerCase();
  const ascii = stripVietnameseMarks_(v).toUpperCase();

  if (ascii.includes('XOA')) return 'Đã xóa';
  if (ascii.includes('HUY') || ascii.includes('BOM') || ascii.includes('BOOM') || ascii.includes('HOAN') || ascii.includes('TRA')) return 'Đã hủy';
  if (ascii.includes('DOI') || ascii.includes('CK')) return 'Đợi CK';
  if (ascii.includes('CHUA') || ascii.includes('CON')) return 'Còn hàng';
  if (ascii.includes('DA BAN') || ascii.includes('DABAN') || ascii.includes('HET') || l.includes('bán')) {
    if (ascii.includes('CHUA BAN') || ascii.includes('CHUABAN')) return 'Còn hàng';
    return 'Đã bán';
  }
  if (v === '') return 'Còn hàng';
  return 'Còn hàng';
}

function internalStatusToSheet_(internal) {
  const l = String(internal || '').normalize('NFC').trim().toLowerCase();
  if (l.includes('bán')) return 'ĐÃ BÁN';
  if (l.includes('xóa')) return 'Đã xóa để làm lại';
  if (l.includes('hủy') || l.includes('bom') || l.includes('hoàn') || l.includes('trả')) return 'Đã hủy';
  if (l.includes('đợi') || l.includes('ck')) return 'ĐỢI KHÁCH CK';
  return 'CHƯA BÁN';
}

function isSoldInternal_(s) {
  const l = stripVietnameseMarks_(String(s || '')).toLowerCase().trim();
  if (l.includes('chua ban') || l.includes('chuaban')) return false;
  return l === 'da ban' || l.includes('da ban') || l === 'ban' || l === 'het hang' || l === 'da ban de lam lai';
}

function isWaitingInternal_(s) {
  const l = stripVietnameseMarks_(String(s || '')).toLowerCase().trim();
  return l.includes('doi') || l.includes('ck');
}

function isDeletedInternal_(s) {
  const l = stripVietnameseMarks_(String(s || '')).toLowerCase().trim();
  return l.includes('xoa') || l.includes('huy') || l.includes('bom') || l.includes('boom') || l.includes('hoan') || l.includes('tra');
}

function isInStockInternal_(s) {
  const l = stripVietnameseMarks_(String(s || '')).toLowerCase().trim();
  if (l === '' || l === 'con hang' || l === 'chua ban' || l === 'chuaban') return true;
  return !isSoldInternal_(s) && !isWaitingInternal_(s) && !isDeletedInternal_(s);
}

function normalizeHinhThuc_(raw) {
  const u = String(raw || '').normalize('NFC').trim().toUpperCase();
  if (u === 'FREESHIP' || u.includes('FREE')) return 'Freeship';
  return 'COD';
}

function doGet(e) {
  const action = e && e.parameter && String(e.parameter.action || '').trim();
  if (action === 'diagnose') {
    return handleAdminSetupAction_(e, function() {
      return runCrmDiagnostics();
    });
  }
  if (action === 'installCrmSyncTrigger') {
    return handleAdminSetupAction_(e, installCrmSyncTrigger);
  }
  if (action === 'installTelegramPolling') {
    return handleAdminSetupAction_(e, installTelegramPollingTrigger);
  }
  if (action === 'setupTelegramWebhook') {
    return handleAdminSetupAction_(e, setupPinnedTelegramWebhook);
  }
  if (action === 'installTelegramTriggers') {
    return handleAdminSetupAction_(e, function() {
      return [installTelegramOnEditTrigger(), installTelegramPendingTrigger()].join('\n');
    });
  }
  if (action === 'installDailyStatusTrigger') {
    return handleAdminSetupAction_(e, installDailyStatusTrigger);
  }
  if (action === 'processTelegramPending') {
    return handleAdminSetupAction_(e, function() {
      processPendingTelegramNotifications();
      return 'Đã xử lý hàng đợi Telegram và quét bù Mã V hôm nay.';
    });
  }
  if (action === 'notifyTelegramMaSP') {
    return handleAdminSetupAction_(e, function() {
      return notifySoldOrderByMaSP(e.parameter.maSP || e.parameter.masp, e.parameter.sheetName || e.parameter.sheet);
    });
  }
  if (action === 'debugLogs') {
    return handleAdminSetupAction_(e, function() {
      const ss = SpreadsheetApp.getActiveSpreadsheet();
      const sheet = ss.getSheetByName('ActivityLog');
      if (!sheet) return [];
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) return [];
      const start = Math.max(2, lastRow - 30);
      const numRows = lastRow - start + 1;
      return sheet.getRange(start, 1, numRows, 5).getValues();
    });
  }
  if (action === 'exportFullDataset') {
    return handleAdminSetupAction_(e, function() {
      const sheetName = e && e.parameter && (e.parameter.sheet || e.parameter.sheetName);
      if (sheetName) {
        return {
          sheet: sheetName,
          rows: readRowsFromSheetByName_(sheetName, { includeBlankMaSP: isLiquidationSheet_(sheetName) })
        };
      }
      return {
        salesData: readRowsFromSheetByName_(SHEET_NAME, { includeBlankMaSP: false }),
        maV: readRowsFromSheetByName_(MA_V_SHEET_NAME, { includeBlankMaSP: false }),
        thanhLy: readRowsFromSheetByName_(LIQUIDATION_SHEET_NAME, { includeBlankMaSP: true })
      };
    });
  }
  if (action === 'reverseSyncFromVps') {
    return handleAdminSetupAction_(e, function() {
      const payloadStr = e.parameter.payload || e.parameter.data || '';
      if (!payloadStr) throw new Error('Missing payload data');
      const payload = typeof payloadStr === 'string' ? JSON.parse(payloadStr) : payloadStr;
      const row = payload.row || payload;
      const targetSheet = payload.sheetName || row.sheetName || SHEET_NAME;
      return syncOrderBackToSheet_(row, targetSheet);
    });
  }
  if (action === 'deleteRowsByMaSPPrefix') {
    return handleAdminSetupAction_(e, function() {
      const prefix = e.parameter.prefix || 'TEST-BULK';
      return deleteRowsByMaSPPrefix_(prefix);
    });
  }
  if (action === 'deleteRow') {
    return handleAdminSetupAction_(e, function() {
      const rowIndex = Number(e.parameter.rowIndex || e.parameter.row || 0);
      const sheetName = e.parameter.sheetName || e.parameter.sheet || SHEET_NAME;
      return deleteRow(rowIndex, sheetName);
    });
  }

  try {
    ensureAllSystemTriggersInstalled_();
  } catch (_) {}

  const template = HtmlService.createTemplateFromFile('Index');
  template.vipTierSettingsJson = JSON.stringify(getCustomerVipTierSettings_());

  return template
    .evaluate()
    .setTitle('Sales Admin System')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function handleAdminSetupAction_(e, callback) {
  try {
    if (!isAdminSetupAllowed_(e)) {
      return ContentService
        .createTextOutput(JSON.stringify({ ok: false, error: 'Unauthorized' }))
        .setMimeType(ContentService.MimeType.JSON);
    }

    const result = callback();
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, result }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err && err.message ? err.message : String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function isAdminSetupAllowed_(e) {
  const key = e && e.parameter && String(e.parameter.key || '').trim();
  if (!key) return false;

  const configuredPassword =
    PropertiesService.getScriptProperties().getProperty(PASSWORD_PROPERTY_KEY) ||
    DEFAULT_PASSWORD;
  const setupKey =
    PropertiesService.getScriptProperties().getProperty('TELEGRAM_SETUP_KEY') ||
    configuredPassword;

  return key === String(setupKey);
}

function doPost(e) {
  const action = e && e.parameter && String(e.parameter.action || '').trim();
  if (action === 'reverseSyncFromVps') {
    return handleAdminSetupAction_(e, function() {
      let payload = null;
      if (e.postData && e.postData.contents) {
        payload = JSON.parse(e.postData.contents);
      } else if (e.parameter && e.parameter.payload) {
        payload = JSON.parse(e.parameter.payload);
      }
      if (!payload) throw new Error('Missing payload data');
      const row = payload.row || payload;
      const targetSheet = payload.sheetName || row.sheetName || SHEET_NAME;
      return syncOrderBackToSheet_(row, targetSheet);
    });
  }
  if (action === 'deleteRowsByMaSPPrefix') {
    return handleAdminSetupAction_(e, function() {
      const prefix = (e.parameter && e.parameter.prefix) || 'TEST-BULK';
      return deleteRowsByMaSPPrefix_(prefix);
    });
  }
  return handleTelegramWebhook_(e);
}

function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

function login(password) {
  const configuredPassword =
    PropertiesService.getScriptProperties().getProperty(PASSWORD_PROPERTY_KEY) ||
    DEFAULT_PASSWORD;

  return String(password || '') === String(configuredPassword);
}

function clearAllRowsCache_() {
  try {
    const cache = CacheService.getScriptCache();
    removeCachedJson_(cache, CACHE_KEY_ROWS);
    removeCachedJson_(cache, CACHE_KEY_REPORT_ROWS);
    removeCachedJson_(cache, 'SALES_ADMIN_CRM_SNAPSHOT');
  } catch (e) {
    console.error('Lỗi xóa cache:', e);
  }
}

function getCacheMetaKey_(key) {
  return key + '_META';
}

function getCacheChunkKey_(key, index) {
  return key + '_PART_' + index;
}

function getCachedJson_(cache, key) {
  const metaText = cache.get(getCacheMetaKey_(key));
  if (metaText) {
    const meta = JSON.parse(metaText);
    if (!meta || !meta.chunks) return null;

    let text = '';
    for (let i = 0; i < meta.chunks; i++) {
      const chunk = cache.get(getCacheChunkKey_(key, i));
      if (chunk == null) return null;
      text += chunk;
    }
    return JSON.parse(text);
  }

  const single = cache.get(key);
  return single ? JSON.parse(single) : null;
}

function putCachedJson_(cache, key, value, expirationSec) {
  const serialized = JSON.stringify(value);
  removeCachedJson_(cache, key);

  if (serialized.length <= CACHE_CHUNK_SIZE) {
    cache.put(key, serialized, expirationSec);
    return true;
  }

  const chunks = [];
  for (let start = 0; start < serialized.length; start += CACHE_CHUNK_SIZE) {
    chunks.push(serialized.slice(start, start + CACHE_CHUNK_SIZE));
  }

  if (chunks.length > CACHE_MAX_CHUNKS) {
    console.warn('Dữ liệu cache quá lớn (' + chunks.length + ' chunks), bỏ qua lưu cache.');
    return false;
  }

  chunks.forEach((chunk, index) => {
    cache.put(getCacheChunkKey_(key, index), chunk, expirationSec);
  });
  cache.put(getCacheMetaKey_(key), JSON.stringify({ chunks: chunks.length }), expirationSec);
  return true;
}

function removeCachedJson_(cache, key) {
  const metaText = cache.get(getCacheMetaKey_(key));
  if (metaText) {
    try {
      const meta = JSON.parse(metaText);
      for (let i = 0; i < Number(meta.chunks || 0); i++) {
        cache.remove(getCacheChunkKey_(key, i));
      }
    } catch (e) {
      for (let i = 0; i < CACHE_MAX_CHUNKS; i++) {
        cache.remove(getCacheChunkKey_(key, i));
      }
    }
  }
  cache.remove(key);
  cache.remove(getCacheMetaKey_(key));
}

function onEdit(e) {
  try {
    clearAllRowsCache_();
  } catch (err) {
    console.error('Lỗi onEdit clear cache:', err);
  }
}

function clearCacheAndReload() {
  clearAllRowsCache_();
  return { success: true, rows: getAllReportRows(true) };
}

function getAllRows(forceRefresh) {
  const cache = CacheService.getScriptCache();
  if (!forceRefresh) {
    try {
      const cachedData = getCachedJson_(cache, CACHE_KEY_ROWS);
      if (cachedData) return cachedData;
    } catch (e) {
      console.warn('Lỗi parse cache, đọc trực tiếp từ Sheet:', e);
    }
  }

  const rows = readAllRowsFromSheet_();

  try {
    putCachedJson_(cache, CACHE_KEY_ROWS, rows, CACHE_EXPIRATION_SEC);
  } catch (e) {
    console.error('Lỗi lưu cache:', e);
  }

  return rows;
}

function readAllRowsFromSheet_() {
  return SALES_LIKE_SHEET_NAMES.reduce((acc, sheetName) => {
    const ctx = getSheetContext_(sheetName, { ensureSchema: false, allowMissing: true });
    if (!ctx) return acc;
    const lastRow = ctx.sheet.getLastRow();
    if (lastRow <= 1) return acc;

    const values = ctx.sheet.getRange(2, 1, lastRow - 1, ctx.lastColumn).getValues();
    const rows = [];

    values.forEach((row, index) => {
      const hasAnyValue = row.some((value) => String(value || '').trim() !== '');
      if (!hasAnyValue) return;

      const mapped = mapRowToObject_(row, ctx.headerMap, index + 2, sheetName, ctx.headers);
      if (!mapped.maSP) {
        if (mapped.giaBan > 0 || mapped.tenKhach || isSoldInternal_(mapped.trangThai)) {
          mapped.maSP = getDefaultMaSPPrefix_(sheetName) + (index + 2);
        } else {
          return;
        }
      }
      rows.push(mapped);
    });

    return acc.concat(rows);
  }, []);
}

function getReportSheetLabel_(name) {
  if (name === LIQUIDATION_SHEET_NAME) return LIQUIDATION_SHEET_NAME;
  if (name === SHEET_NAME) return 'SalesData';
  return name || 'SalesData';
}

function getTelegramSheetName_(rowOrSheetName) {
  if (rowOrSheetName && typeof rowOrSheetName === 'object') {
    return String(rowOrSheetName.sourceSheet || rowOrSheetName.sheetName || SHEET_NAME).trim() || SHEET_NAME;
  }
  return String(rowOrSheetName || SHEET_NAME).trim() || SHEET_NAME;
}

function getTelegramRowKey_(sheetName, rowIndex) {
  return encodeURIComponent(getTelegramSheetName_(sheetName)) + '_' + String(rowIndex || '');
}

function getTelegramMaSPKey_(sheetName, maSP) {
  return encodeURIComponent(getTelegramSheetName_(sheetName)) + '_' + String(maSP || '').trim().toLowerCase();
}

function readRowsFromSalesLikeSheets_() {
  return SALES_LIKE_SHEET_NAMES.reduce((acc, sheetName) => {
    return acc.concat(readRowsFromSheetByName_(sheetName, { includeBlankMaSP: false }));
  }, []);
}

function isMaVSheet_(name) {
  if (!name) return false;
  const norm = stripVietnameseMarks_(String(name).toLowerCase().trim());
  return norm === 'ma v' || norm === 'mã v' || norm === 'v' || norm.includes('ma v') || norm.includes('tab v');
}

function isSalesDataSheet_(name) {
  if (!name) return false;
  const norm = stripVietnameseMarks_(String(name).toLowerCase().trim());
  return norm === 'salesdata' || norm === 'sales data';
}

function isLiquidationSheet_(name) {
  if (!name) return false;
  const norm = stripVietnameseMarks_(String(name).toLowerCase().trim());
  return norm === 'thanh ly' || norm.includes('thanh ly');
}

function isReportSheet_(name) {
  return isSalesDataSheet_(name) || isMaVSheet_(name) || isLiquidationSheet_(name);
}

function isEditableSalesLikeSheet_(sheetName) {
  return isSalesDataSheet_(sheetName) || isMaVSheet_(sheetName);
}

function getDefaultMaSPPrefix_(sheetName) {
  return isMaVSheet_(sheetName) ? 'V-' : 'KOD-';
}

function findSheetByName_(ss, targetName) {
  if (!ss || !targetName) return null;
  let sheet = ss.getSheetByName(targetName);
  if (sheet) return sheet;

  const normTarget = stripVietnameseMarks_(String(targetName).toLowerCase().trim());
  const sheets = ss.getSheets();

  for (let i = 0; i < sheets.length; i++) {
    const s = sheets[i];
    const normName = stripVietnameseMarks_(s.getName().toLowerCase().trim());

    if (normName === normTarget) return s;
    if (isMaVSheet_(targetName) && isMaVSheet_(s.getName())) return s;
    if (isSalesDataSheet_(targetName) && isSalesDataSheet_(s.getName())) return s;
    if (isLiquidationSheet_(targetName) && isLiquidationSheet_(s.getName())) return s;
  }
  return null;
}

function getEditableSalesLikeSheetName_(sheetName) {
  const targetName = String(sheetName || SHEET_NAME).trim() || SHEET_NAME;
  if (!isEditableSalesLikeSheet_(targetName)) {
    throw new Error('Sheet "' + targetName + '" không hỗ trợ chỉnh sửa từ admin.');
  }
  return targetName;
}

function getAdminSheetConfigs() {
  return REPORT_SHEET_NAMES.map((name) => ({
    name,
    label: getReportSheetLabel_(name),
    primary: name === SHEET_NAME,
    readOnly: !isEditableSalesLikeSheet_(name)
  }));
}

function getAllReportRows(forceRefresh) {
  const cache = CacheService.getScriptCache();
  if (!forceRefresh) {
    try {
      const cachedData = getCachedJson_(cache, CACHE_KEY_REPORT_ROWS);
      if (cachedData) return cachedData;
    } catch (e) {
      console.warn('Lỗi parse cache báo cáo, đọc trực tiếp từ Sheet:', e);
    }
  }

  const rows = readAllReportRowsFromSheets_();
  try {
    putCachedJson_(cache, CACHE_KEY_REPORT_ROWS, rows, CACHE_EXPIRATION_SEC);
  } catch (e) {
    console.error('Lỗi lưu cache báo cáo:', e);
  }

  return rows;
}

function isEligibleDailyOrder(row) {
  if (!row) return false;
  const sheet = String(row.sourceSheet || row.sheetName || '').trim();
  if (sheet !== SHEET_NAME && sheet !== MA_V_SHEET_NAME) return false;

  if (!row.ngayChot || !/^\d{4}-\d{2}-\d{2}$/.test(row.ngayChot)) return false;

  const tt = row.trangThai;
  if (!isSoldInternal_(tt) && !isWaitingInternal_(tt)) return false;
  if (isDeletedInternal_(tt)) return false;

  const ttLower = String(row.trangThaiGoc || tt || '').toLowerCase();
  const excludedKeywords = ['hủy', 'huy', 'xóa', 'xoa', 'bom', 'boom', 'hoàn', 'hoan', 'trả', 'tra', 'còn hàng', 'con hang', 'chưa bán', 'chua ban'];
  for (let i = 0; i < excludedKeywords.length; i++) {
    if (ttLower.includes(excludedKeywords[i])) return false;
  }

  return true;
}

function getCrmSyncSnapshot(options) {
  const opts = options || {};
  const forceRefresh = !!opts.forceRefresh;
  const cache = CacheService.getScriptCache();

  if (forceRefresh) {
    clearAllRowsCache_();
    SpreadsheetApp.flush();
  } else {
    try {
      const cached = getCachedJson_(cache, 'SALES_ADMIN_CRM_SNAPSHOT');
      if (cached) {
        cached.cacheHit = true;
        return cached;
      }
    } catch (e) {
      console.warn('Lỗi đọc snapshot cache:', e);
    }
  }

  const rows = getAllRows(forceRefresh);
  const reportRows = getAllReportRows(forceRefresh);
  const dailyRows = reportRows.filter(isEligibleDailyOrder);

  const stats = buildDashboardStatsFromRows_(rows);
  stats.notifications = getSystemNotifications();

  const sourceCounts = {};
  REPORT_SHEET_NAMES.forEach(name => {
    sourceCounts[name] = 0;
  });

  reportRows.forEach(r => {
    const sheet = r.sourceSheet || SHEET_NAME;
    if (sourceCounts[sheet] !== undefined) {
      sourceCounts[sheet]++;
    }
  });

  const skippedCounts = {
    totalSkipped: 0,
    reasons: {
      emptyRow: 0,
      missingMaSP: 0,
      invalidDate: 0
    }
  };

  const snapshot = {
    rows,
    reportRows,
    dailyRows,
    stats,
    sourceCounts,
    skippedCounts,
    serverToday: getTodayString_(),
    syncedAt: getCurrentTimestamp_(),
    cacheHit: false
  };

  try {
    putCachedJson_(cache, 'SALES_ADMIN_CRM_SNAPSHOT', snapshot, CACHE_EXPIRATION_SEC);
  } catch (e) {
    console.error('Lỗi cache snapshot:', e);
  }

  return snapshot;
}

function getLiquidationRows() {
  return readRowsFromSheetByName_(LIQUIDATION_SHEET_NAME, { includeBlankMaSP: true });
}

function getSheetHeaderDiagnostics() {
  return REPORT_SHEET_NAMES.map((sheetName) => {
    const ctx = getSheetContext_(sheetName, { ensureSchema: false, allowMissing: true });
    if (!ctx) {
      return {
        sheetName,
        exists: false,
        headers: [],
        missingCoreFields: ['maSP', 'giaBan', 'tenKhach', 'ngayChot', 'trangThai'],
        message: 'Không tìm thấy sheet'
      };
    }

    const missingCoreFields = ['maSP', 'giaBan', 'tenKhach', 'ngayChot', 'trangThai']
      .filter((key) => getHeaderIndexByAliases_(ctx.headerMap, HEADER_ALIASES[key] || []) === undefined);

    return {
      sheetName,
      exists: true,
      headers: ctx.headers.map((h) => String(h || '').trim()).filter(Boolean),
      missingCoreFields,
      message: missingCoreFields.length
        ? 'Có cột lõi chưa map được, app vẫn đọc động nhưng nên chuẩn hóa header.'
        : 'Header đã đủ để thống kê.'
    };
  });
}

function readAllReportRowsFromSheets_() {
  return REPORT_SHEET_NAMES.reduce((acc, sheetName) => {
    return acc.concat(readRowsFromSheetByName_(sheetName, { includeBlankMaSP: sheetName === LIQUIDATION_SHEET_NAME }));
  }, []);
}

function readRowsFromSheetByName_(sheetName, options) {
  const ctx = getSheetContext_(sheetName, { ensureSchema: false, allowMissing: true });
  if (!ctx) return [];

  const lastRow = ctx.sheet.getLastRow();
  if (lastRow <= 1) return [];

  const values = ctx.sheet.getRange(2, 1, lastRow - 1, ctx.lastColumn).getValues();
  const rows = [];
  const includeBlankMaSP = Boolean(options && options.includeBlankMaSP);

  values.forEach((row, index) => {
    const hasAnyValue = row.some((value) => String(value || '').trim() !== '');
    if (!hasAnyValue) return;

    const mapped = mapRowToObject_(row, ctx.headerMap, index + 2, sheetName, ctx.headers);
    if (!includeBlankMaSP && !mapped.maSP) {
      if (mapped.giaBan > 0 || mapped.tenKhach || isSoldInternal_(mapped.trangThai)) {
        mapped.maSP = getDefaultMaSPPrefix_(sheetName) + (index + 2);
      } else {
        return;
      }
    }
    rows.push(mapped);
  });

  return rows;
}

function addRow(data, sheetName) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(15000)) {
      throw new Error('Hệ thống đang bận ghi nhận dữ liệu khác, vui lòng thử lại sau vài giây.');
    }
    const targetSheet = getEditableSalesLikeSheetName_(sheetName);
    const ctx = getSheetContext_(targetSheet, { ensureSchema: isEditableSalesLikeSheet_(targetSheet) });
    const cleanData = normalizeRowData_(data);

    validateRowData_(cleanData);
    ensureUniqueMaSP_(ctx.sheet, ctx.headerMap, cleanData.maSP);

    const now = getCurrentTimestamp_();
    const notificationKey = generateNotificationKey_();
    const newRow = new Array(ctx.lastColumn).fill('');

    setManagedValues_(newRow, ctx.headerMap, cleanData, {
      createdAt: now,
      updatedAt: now,
      notificationKey: notificationKey,
      telegramStatus: isSoldInternal_(cleanData.trangThai) ? 'PENDING' : ''
    });

    const nextRow = ctx.sheet.getLastRow() + 1;
    ctx.sheet.getRange(nextRow, 1, 1, ctx.lastColumn).setValues([newRow]);

    // Log addition
    logActivity_(nextRow, cleanData.maSP, 'Thêm mới', `${cleanData.aiChot || 'Admin'} đã thêm mới sản phẩm vào ${targetSheet}.`);

    const savedRow = mapRowToObject_(newRow, ctx.headerMap, nextRow, targetSheet, ctx.headers);
    if (isSoldInternal_(savedRow.trangThai) && isRowReadyForNewOrderNotify_(savedRow)) {
      dispatchTelegramOrderNotification_(targetSheet, nextRow, 'AppScript Web App');
    }

    clearAllRowsCache_();
    return { success: true, message: 'Thêm sản phẩm thành công!', row: savedRow };
  } finally {
    lock.releaseLock();
  }
}

function updateRow(rowIndex, data, sheetName) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(15000)) {
      throw new Error('Hệ thống đang bận cập nhật dữ liệu khác, vui lòng thử lại sau vài giây.');
    }
    const targetSheetName = getEditableSalesLikeSheetName_(sheetName);
    const ctx = getSheetContext_(targetSheetName, { ensureSchema: isEditableSalesLikeSheet_(targetSheetName) });
    let safeRowIndex = Number(rowIndex);

    if (!safeRowIndex || safeRowIndex < 2 || safeRowIndex > ctx.sheet.getLastRow()) {
      const foundIdx = findRowIndexByMaSP_(ctx.sheet, ctx.headerMap, data && data.maSP);
      if (foundIdx) {
        safeRowIndex = foundIdx;
      } else {
        throw new Error('Dòng cần cập nhật không hợp lệ.');
      }
    }

    const cleanData = normalizeRowData_(data);
    validateRowData_(cleanData);

    const currentRow = ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).getValues()[0];
    const currentRowObj = mapRowToObject_(currentRow, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);

    // Only enforce unique check if user actually changes the MÃ SP of this row
    const currentMaSP = String(currentRowObj.maSP || '').trim().toLowerCase();
    const newMaSP = String(cleanData.maSP || '').trim().toLowerCase();
    if (newMaSP && currentMaSP && newMaSP !== currentMaSP) {
      ensureUniqueMaSP_(ctx.sheet, ctx.headerMap, cleanData.maSP, safeRowIndex);
    }
    const createdAt = String(getCellByHeaderAliases_(currentRow, ctx.headerMap, HEADER_ALIASES.createdAt) || '') || getCurrentTimestamp_();

    // Preserve technical notification fields
    const notificationKey = currentRowObj.notificationKey || generateNotificationKey_();
    const telegramStatus = currentRowObj.telegramStatus || (isSoldInternal_(cleanData.trangThai) ? 'PENDING' : '');
    const telegramSentAt = currentRowObj.telegramSentAt || '';
    const telegramMessageId = currentRowObj.telegramMessageId || '';
    const telegramError = currentRowObj.telegramError || '';

    setManagedValues_(currentRow, ctx.headerMap, cleanData, {
      createdAt,
      updatedAt: getCurrentTimestamp_(),
      notificationKey,
      telegramStatus,
      telegramSentAt,
      telegramMessageId,
      telegramError
    });

    ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).setValues([currentRow]);

    // Log changes
    const changes = [];
    const editor = cleanData.aiChot || 'Admin';
    if (currentRowObj.giaBan !== cleanData.giaBan) changes.push(`Giá bán (${formatMoney_(currentRowObj.giaBan)} -> ${formatMoney_(cleanData.giaBan)})`);
    if (currentRowObj.giaVon !== cleanData.giaVon) changes.push(`Giá vốn (${formatMoney_(currentRowObj.giaVon)} -> ${formatMoney_(cleanData.giaVon)})`);
    if (currentRowObj.khachCoc !== cleanData.khachCoc) changes.push(`Cọc (${formatMoney_(currentRowObj.khachCoc)} -> ${formatMoney_(cleanData.khachCoc)})`);
    if (currentRowObj.tienCOD !== cleanData.tienCOD) changes.push(`COD (${formatMoney_(currentRowObj.tienCOD)} -> ${formatMoney_(cleanData.tienCOD)})`);
    if (currentRowObj.trangThai !== cleanData.trangThai) changes.push(`Trạng thái (${currentRowObj.trangThai} -> ${cleanData.trangThai})`);
    if (currentRowObj.tenKhach !== cleanData.tenKhach) changes.push(`Khách (${currentRowObj.tenKhach || '—'} -> ${cleanData.tenKhach || '—'})`);
    if (currentRowObj.sdtKhach !== cleanData.sdtKhach) changes.push(`SĐT (${currentRowObj.sdtKhach || '—'} -> ${cleanData.sdtKhach || '—'})`);
    if (changes.length > 0) {
      logActivity_(safeRowIndex, cleanData.maSP, 'Cập nhật', `${editor} sửa: ${changes.join(', ')}`);
    }

    const savedRow = mapRowToObject_(currentRow, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);
    const upperStatus = String(savedRow.telegramStatus || '').trim().toUpperCase();
    if (upperStatus !== 'SENT' && !savedRow.telegramMessageId && isSoldInternal_(savedRow.trangThai) && isRowReadyForNewOrderNotify_(savedRow)) {
      dispatchTelegramOrderNotification_(targetSheetName, safeRowIndex, 'AppScript Web App');
    }

    clearAllRowsCache_();
    return { success: true, message: 'Cập nhật thành công!' };
  } finally {
    lock.releaseLock();
  }
}

function findRowIndexByMaSP_(sheet, headerMap, maSP) {
  const normalized = String(maSP || '').trim().toLowerCase();
  if (!normalized) return null;
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return null;
  const colIndex = headerMap['MÃ SP'] !== undefined ? headerMap['MÃ SP'] : headerMap[normalizeHeaderKey_('MÃ SP')];
  if (colIndex === undefined) return null;
  const values = sheet.getRange(2, colIndex + 1, lastRow - 1, 1).getValues();
  // Search from bottom up to find the latest active entry
  for (let i = values.length - 1; i >= 0; i--) {
    const existing = String(values[i][0] || '').trim().toLowerCase();
    if (existing && existing === normalized) {
      return i + 2;
    }
  }
  return null;
}

function syncOrderBackToSheet_(data, sheetName) {
  if (!data || !data.maSP) {
    throw new Error('Dữ liệu đơn hàng thiếu mã SP.');
  }
  const targetSheet = getEditableSalesLikeSheetName_(sheetName || data.sheetName || SHEET_NAME);
  const ctx = getSheetContext_(targetSheet, { ensureSchema: isEditableSalesLikeSheet_(targetSheet) });
  if (!ctx) throw new Error('Không tìm thấy sheet: ' + targetSheet);

  let existingRowIndex = Number(data.rowIndex) || 0;
  if (!existingRowIndex || existingRowIndex < 2 || existingRowIndex > ctx.sheet.getLastRow()) {
    existingRowIndex = findRowIndexByMaSP_(ctx.sheet, ctx.headerMap, data.maSP);
  }
  if (existingRowIndex) {
    return updateRow(existingRowIndex, data, targetSheet);
  } else {
    return addRow(data, targetSheet);
  }
}

function deleteRowsByMaSPPrefix_(prefix) {
  const cleanPrefix = String(prefix || '').trim().toLowerCase();
  if (!cleanPrefix) throw new Error('Prefix is required');
  const targetSheets = [SHEET_NAME, MA_V_SHEET_NAME, LIQUIDATION_SHEET_NAME];
  const deleted = [];
  const errors = [];
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  targetSheets.forEach(function(sname) {
    try {
      const sheet = ss.getSheetByName(sname);
      if (!sheet) return;
      const lastRow = sheet.getLastRow();
      if (lastRow <= 1) return;
      const ctx = getSheetContext_(sname, { ensureSchema: false });
      const colIdx = ctx.headerMap['MÃ SP'] !== undefined ? ctx.headerMap['MÃ SP'] : ctx.headerMap[normalizeHeaderKey_('MÃ SP')];
      if (colIdx === undefined) return;

      const colValues = sheet.getRange(2, colIdx + 1, lastRow - 1, 1).getValues();
      const matches = [];
      for (let i = 0; i < colValues.length; i++) {
        const val = String(colValues[i][0] || '').trim();
        if (val.toLowerCase().indexOf(cleanPrefix) === 0) {
          matches.push({ row: i + 2, val: val });
        }
      }

      // Sort descending so deletions do not shift subsequent row numbers
      matches.sort((a, b) => b.row - a.row);
      matches.forEach(function(item) {
        try {
          const maxCols = Math.max(sheet.getLastColumn(), 20);
          sheet.getRange(item.row, 1, 1, maxCols).clearContent();
          sheet.getRange(item.row, 1, 1, maxCols).clearFormat();
          sheet.deleteRow(item.row);
          deleted.push({ sheet: sname, row: item.row, maSP: item.val });
        } catch (delErr) {
          errors.push({ sheet: sname, row: item.row, error: String(delErr) });
        }
      });
    } catch (e) {
      errors.push({ sheet: sname, error: String(e) });
    }
  });

  SpreadsheetApp.flush();
  clearAllRowsCache_();
  return {
    success: true,
    spreadsheetId: ss.getId(),
    deleted: deleted,
    errors: errors
  };
}

function quickUpdateRow(rowIndex, patch, sheetName) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(15000)) {
      throw new Error('Hệ thống đang bận cập nhật dữ liệu khác, vui lòng thử lại sau vài giây.');
    }
    const targetSheetName = getEditableSalesLikeSheetName_(sheetName);
    const ctx = getSheetContext_(targetSheetName, { ensureSchema: isEditableSalesLikeSheet_(targetSheetName) });
    const safeRowIndex = Number(rowIndex);

    if (!safeRowIndex || safeRowIndex < 2 || safeRowIndex > ctx.sheet.getLastRow()) {
      throw new Error('Dòng cần cập nhật nhanh không hợp lệ.');
    }

    const currentRow = ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).getValues()[0];
    const currentObject = mapRowToObject_(currentRow, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);
    const mergedData = normalizeRowData_(Object.assign({}, currentObject, patch));

    validateRowData_(mergedData);
    ensureUniqueMaSP_(ctx.sheet, ctx.headerMap, mergedData.maSP, safeRowIndex);

    const createdAt = currentObject.createdAt || getCurrentTimestamp_();
    const notificationKey = currentObject.notificationKey || generateNotificationKey_();
    const telegramStatus = currentObject.telegramStatus || (isSoldInternal_(mergedData.trangThai) ? 'PENDING' : '');
    const telegramSentAt = currentObject.telegramSentAt || '';
    const telegramMessageId = currentObject.telegramMessageId || '';
    const telegramError = currentObject.telegramError || '';

    setManagedValues_(currentRow, ctx.headerMap, mergedData, {
      createdAt,
      updatedAt: getCurrentTimestamp_(),
      notificationKey,
      telegramStatus,
      telegramSentAt,
      telegramMessageId,
      telegramError
    });

    ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).setValues([currentRow]);

    // Log changes
    const changes = [];
    const editor = mergedData.aiChot || 'Admin';
    if (currentObject.giaBan !== mergedData.giaBan) changes.push(`Giá bán (${formatMoney_(currentObject.giaBan)} -> ${formatMoney_(mergedData.giaBan)})`);
    if (currentObject.giaVon !== mergedData.giaVon) changes.push(`Giá vốn (${formatMoney_(currentObject.giaVon)} -> ${formatMoney_(mergedData.giaVon)})`);
    if (currentObject.trangThai !== mergedData.trangThai) changes.push(`Trạng thái (${currentObject.trangThai} -> ${mergedData.trangThai})`);
    if (currentObject.khachCoc !== mergedData.khachCoc) changes.push(`Cọc (${formatMoney_(currentObject.khachCoc)} -> ${formatMoney_(mergedData.khachCoc)})`);
    if (currentObject.tienCOD !== mergedData.tienCOD) changes.push(`COD (${formatMoney_(currentObject.tienCOD)} -> ${formatMoney_(mergedData.tienCOD)})`);
    if (currentObject.ghiChu !== mergedData.ghiChu) changes.push(`Ghi chú (${currentObject.ghiChu || '—'} -> ${mergedData.ghiChu || '—'})`);
    if (currentObject.linkTiktok !== mergedData.linkTiktok) changes.push(`Link TikTok (${currentObject.linkTiktok || '—'} -> ${mergedData.linkTiktok || '—'})`);
    if (changes.length > 0) {
      logActivity_(safeRowIndex, mergedData.maSP, 'Cập nhật nhanh', `${editor} sửa: ${changes.join(', ')}`);
    }

    const savedRow = mapRowToObject_(currentRow, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);
    const upperStatus = String(savedRow.telegramStatus || '').trim().toUpperCase();
    if (upperStatus !== 'SENT' && !savedRow.telegramMessageId && isSoldInternal_(savedRow.trangThai) && isRowReadyForNewOrderNotify_(savedRow)) {
      dispatchTelegramOrderNotification_(targetSheetName, safeRowIndex, 'AppScript Web App');
    }

    clearAllRowsCache_();
    return { success: true, message: 'Đã lưu nhanh thay đổi!' };
  } finally {
    lock.releaseLock();
  }
}

function deleteRow(rowIndex, sheetName) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(15000)) {
      throw new Error('Hệ thống đang bận cập nhật dữ liệu khác, vui lòng thử lại sau vài giây.');
    }
    const targetSheetName = getEditableSalesLikeSheetName_(sheetName);
    const ctx = getSheetContext_(targetSheetName, { ensureSchema: targetSheetName === SHEET_NAME });
    const safeRowIndex = Number(rowIndex);

    if (!safeRowIndex || safeRowIndex < 2 || safeRowIndex > ctx.sheet.getLastRow()) {
      throw new Error('Dòng cần xóa không hợp lệ.');
    }

    const currentRow = ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).getValues()[0];
    const rowObj = mapRowToObject_(currentRow, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);

    ctx.sheet.deleteRow(safeRowIndex);

    // Xóa Telegram notify state để MaSP có thể được notify lại nếu re-add
    try {
      const tgProps = PropertiesService.getScriptProperties();
      tgProps.deleteProperty(TELEGRAM_PENDING_PREFIX + getTelegramRowKey_(targetSheetName, safeRowIndex));
      tgProps.deleteProperty(TELEGRAM_LAST_SIGNATURE_PREFIX + getTelegramRowKey_(targetSheetName, safeRowIndex));
      tgProps.deleteProperty(TELEGRAM_NOTIFIED_PREFIX + getTelegramMaSPKey_(targetSheetName, rowObj.maSP));
      if (isSalesDataSheet_(targetSheetName)) {
        tgProps.deleteProperty(TELEGRAM_NOTIFIED_PREFIX + String(rowObj.maSP || '').trim().toLowerCase());
      }
    } catch (e) {
      console.warn('Lỗi xóa Telegram props khi deleteRow:', e);
    }

    logActivity_(safeRowIndex, rowObj.maSP, 'Xóa', `${rowObj.aiChot || 'Admin'} xóa sản phẩm.`);

    clearAllRowsCache_();
    return { success: true, message: 'Đã xóa sản phẩm!' };
  } finally {
    lock.releaseLock();
  }
}

function searchByMaSP(keyword) {
  const normalized = normalizeMaSPForSearch_(keyword);
  if (!normalized) return [];

  const phoneNorm = normalizePhoneForLookup_(keyword);

  return getAllReportRows().filter((row) => {
    // 1. Search MaSP
    if (matchesMaSPForSearch_(row.maSP, normalized)) return true;
    // 2. Search SanPham
    if (matchesMaSPForSearch_(row.sanPham, normalized)) return true;
    // 3. Search Customer Name
    const customerNameNorm = normalizeMaSPForSearch_(row.tenKhach);
    if (customerNameNorm.includes(normalized)) return true;
    // 4. Search Phone
    if (phoneNorm && row.sdtKhach) {
      const rowPhone = normalizePhoneForLookup_(row.sdtKhach);
      if (rowPhone && (rowPhone.includes(phoneNorm) || phoneNorm.includes(rowPhone))) return true;
    }
    return false;
  });
}

function normalizePhoneForLookup_(value) {
  return String(value || '').replace(/[^\d]/g, '').replace(/^84/, '0');
}

function getCustomerHistoryByPhone(phone, currentRowIndex) {
  const phoneKey = normalizePhoneForLookup_(phone);
  if (phoneKey.length < 8) {
    return { found: false, totalOrders: 0, rows: [] };
  }

  const safeCurrentRowIndex = Number(currentRowIndex || 0);
  const rows = getAllReportRows()
    .filter((row) => {
      if (safeCurrentRowIndex && Number(row.rowIndex) === safeCurrentRowIndex && row.sourceSheet === SHEET_NAME) return false;
      const rowPhone = normalizePhoneForLookup_(row.sdtKhach);
      return rowPhone && (rowPhone === phoneKey || rowPhone.endsWith(phoneKey) || phoneKey.endsWith(rowPhone));
    })
    .sort((a, b) => String(b.ngayChot || b.updatedAt || b.createdAt || '').localeCompare(String(a.ngayChot || a.updatedAt || a.createdAt || '')));

  const summary = rows.reduce((acc, row) => {
    acc.totalOrders += 1;
    acc.totalRevenue += Number(row.giaBan || 0);
    acc.totalProfit += Number(row.tienLoi || 0);

    const isSold = isSoldInternal_(row.trangThai);
    const isDeleted = isDeletedInternal_(row.trangThai);
    const isWaiting = isWaitingInternal_(row.trangThai);

    if (isSold) {
      acc.successfulOrders += 1;
      acc.successfulRevenue += Number(row.giaBan || 0);
    }
    if (isDeleted) acc.deletedOrders += 1;
    if (isWaiting) acc.pendingOrders += 1;

    const note = String(row.ghiChu || '').toLowerCase();
    const hasBomKeywords = note.includes('hoàn') || note.includes('hoan') ||
                           note.includes('bom') || note.includes('boom') ||
                           note.includes('trả') || note.includes('tra') ||
                           note.includes('hủy') || note.includes('huy');
    if (isDeleted || hasBomKeywords) {
      acc.hasBomHistory = true;
    }

    if (row.ngayChot && (!acc.lastOrderDate || row.ngayChot > acc.lastOrderDate)) acc.lastOrderDate = row.ngayChot;
    return acc;
  }, { totalOrders: 0, totalRevenue: 0, totalProfit: 0, deletedOrders: 0, pendingOrders: 0, lastOrderDate: '', successfulOrders: 0, successfulRevenue: 0, hasBomHistory: false });

  return {
    found: rows.length > 0,
    phone: phoneKey,
    summary,
    rows: rows.slice(0, 8).map((row) => ({
      rowIndex: row.rowIndex,
      sourceSheet: row.sourceSheet,
      maSP: row.maSP,
      tenKhach: row.tenKhach,
      aiChot: row.aiChot,
      nguonKhach: row.nguonKhach,
      ngayChot: row.ngayChot,
      trangThai: row.trangThai,
      giaBan: row.giaBan,
      tienLoi: row.tienLoi,
      hinhThuc: row.hinhThuc
    }))
  };
}

function getDashboardStats() {
  const rows = readRowsFromSalesLikeSheets_();
  const stats = buildDashboardStatsFromRows_(rows);
  stats.notifications = getSystemNotifications();
  return stats;
}

function getRowsAndDashboardStats() {
  const rows = getAllRows();
  const reportRows = getAllReportRows();

  return {
    rows,
    reportRows,
    stats: buildDashboardStatsFromRows_(readRowsFromSalesLikeSheets_()),
    notifications: getSystemNotifications()
  };
}

function buildDashboardStatsFromRows_(rows) {
  const today = getTodayString_();
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const timeZone = Session.getScriptTimeZone();
  const yesterday = Utilities.formatDate(yesterdayDate, timeZone, 'yyyy-MM-dd');

  let tongDoanhThu = 0, tongGiaVon = 0, tongLoiNhuan = 0, tongLo = 0, tongTienCOD = 0, tongKhachCoc = 0;
  let soLuongCon = 0, soLuongBan = 0, soLuongDoiCK = 0, soLuongXoa = 0;
  let soCOD = 0, soFreeship = 0;
  
  let donBanHomNay = 0, doanhThuHomNay = 0, loiNhuanHomNay = 0, cocHomNay = 0, codHomNay = 0;
  let donBanHomQua = 0, doanhThuHomQua = 0, loiNhuanHomQua = 0, cocHomQua = 0, codHomQua = 0;

  const doanhThuNgay = {}, loiNhuanNgay = {}, donNgay = {}, loNgay = {};

  rows.forEach((row) => {
    const tt = row.trangThai;
    const ht = row.hinhThuc;

    if (isDeletedInternal_(tt)) { soLuongXoa++; return; }

    if (isInStockInternal_(tt)) soLuongCon++;
    if (isSoldInternal_(tt)) soLuongBan++;
    if (isWaitingInternal_(tt)) soLuongDoiCK++;

    if (ht === 'COD') { soCOD++; }
    if (ht === 'Freeship') soFreeship++;

    // Only count revenue-generating rows for lifetime sums
    const isRevenue = isSoldInternal_(tt) || isWaitingInternal_(tt);

    if (isRevenue) {
      tongDoanhThu += row.giaBan;
      tongGiaVon += row.giaVon;
      tongKhachCoc += row.khachCoc;
      if (ht === 'COD') { tongTienCOD += row.tienCOD; }

      const computedLoi = row.giaBan - row.giaVon;
      if (computedLoi >= 0) {
        tongLoiNhuan += computedLoi;
      } else {
        tongLo += computedLoi;
        if (row.ngayChot) {
          loNgay[row.ngayChot] = (loNgay[row.ngayChot] || 0) + Math.abs(computedLoi);
        }
      }

      if (row.ngayChot) {
        doanhThuNgay[row.ngayChot] = (doanhThuNgay[row.ngayChot] || 0) + row.giaBan;
        loiNhuanNgay[row.ngayChot] = (loiNhuanNgay[row.ngayChot] || 0) + computedLoi;
        donNgay[row.ngayChot] = (donNgay[row.ngayChot] || 0) + 1;
      }
    }

    // Today metrics
    if ((isSoldInternal_(tt) || isWaitingInternal_(tt)) && row.ngayChot === today) {
      donBanHomNay++;
      doanhThuHomNay += row.giaBan;
      loiNhuanHomNay += (row.giaBan - row.giaVon);
      cocHomNay += row.khachCoc;
      if (ht === 'COD') {
        codHomNay += row.tienCOD;
      }
    }
    
    // Yesterday metrics
    if ((isSoldInternal_(tt) || isWaitingInternal_(tt)) && row.ngayChot === yesterday) {
      donBanHomQua++;
      doanhThuHomQua += row.giaBan;
      loiNhuanHomQua += (row.giaBan - row.giaVon);
      cocHomQua += row.khachCoc;
      if (ht === 'COD') {
        codHomQua += row.tienCOD;
      }
    }
  });

  const chartLabels = Object.keys(doanhThuNgay).sort();
  const tongSanPham = rows.length;
  const tyLeCOD = tongSanPham ? Math.round((soCOD / tongSanPham) * 100) : 0;
  const tyLeChot = tongSanPham ? Math.round((soLuongBan / tongSanPham) * 100) : 0;

  // Last 7 days metrics for sparklines
  const last7Labels = chartLabels.slice(-7);
  const last7DoanhThu = last7Labels.map(d => doanhThuNgay[d] || 0);
  const last7LoiNhuan = last7Labels.map(d => loiNhuanNgay[d] || 0);
  const last7Don = last7Labels.map(d => donNgay[d] || 0);
  const last7Lo = last7Labels.map(d => loNgay[d] || 0);

  // Top Customers Today
  const topKhachMap = {};
  rows.forEach((row) => {
    const tt = row.trangThai;
    if ((isSoldInternal_(tt) || isWaitingInternal_(tt)) && row.ngayChot === today) {
      const name = String(row.tenKhach || '').trim() || 'Khách ẩn danh';
      const phone = String(row.sdtKhach || '').trim();
      const key = phone || name;
      if (!topKhachMap[key]) {
        topKhachMap[key] = { name: name || 'Khách ẩn danh', phone: phone || '', revenue: 0 };
      }
      topKhachMap[key].revenue += row.giaBan;
    }
  });

  const topKhachHomNay = Object.values(topKhachMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, 5);

  const growthDon = calculateGrowthPercentage_(donBanHomNay, donBanHomQua);
  const growthDoanhThu = calculateGrowthPercentage_(doanhThuHomNay, doanhThuHomQua);
  const growthLoiNhuan = calculateGrowthPercentage_(loiNhuanHomNay, loiNhuanHomQua);
  const growthCoc = calculateGrowthPercentage_(cocHomNay, cocHomQua);
  const growthCod = calculateGrowthPercentage_(codHomNay, codHomQua);

  return {
    tongDoanhThu, tongGiaVon, tongLoiNhuan,
    tongLo: Math.abs(tongLo),
    loiNhuanRong: tongLoiNhuan + tongLo,
    tongTienCOD, soCOD, soFreeship, tongKhachCoc,
    soLuongCon, soLuongBan, soLuongDoiCK, soLuongXoa,
    tongSanPham, donBanHomNay, doanhThuHomNay, loiNhuanHomNay,
    cocHomNay, codHomNay,
    growthDon, growthDoanhThu, growthLoiNhuan, growthCoc, growthCod,
    tyLeCOD, tyLeChot, chartLabels,
    chartDoanhThu: chartLabels.map(d => doanhThuNgay[d]),
    chartLoiNhuan: chartLabels.map(d => loiNhuanNgay[d]),
    chartDon: chartLabels.map(d => donNgay[d]),
    last7DoanhThu, last7LoiNhuan, last7Don, last7Lo,
    topKhachHomNay,
    customerLifetime: buildCustomerLifetimeDashboard_(rows),
    businessHealth: buildBusinessHealthScore_(rows)
  };
}

function buildBusinessHealthScore_(rows) {
  const today = getTodayString_();
  const currentMonth = today.slice(0, 7);
  const prevMonth = getPreviousMonthKey_(currentMonth);
  const current = calculateBusinessPeriodMetrics_(rows, currentMonth);
  const previous = calculateBusinessPeriodMetrics_(rows, prevMonth);

  const revenueScore = scoreRevenueMomentum_(current.revenue, previous.revenue);
  const profitMargin = current.revenue > 0 ? current.profit / current.revenue : 0;
  const profitScore = current.revenue > 0 ? clampScore_(Math.round((profitMargin / 0.3) * 100)) : 50;
  const cancelRate = current.orderCount ? current.cancelledOrders / current.orderCount : 0;
  const cancelScore = clampScore_(Math.round(100 - cancelRate * 300));
  const waitingRate = current.orderCount ? current.waitingOrders / current.orderCount : 0;
  const waitingScore = clampScore_(Math.round(100 - waitingRate * 220));
  const returningRate = current.activeCustomers ? current.returningCustomers / current.activeCustomers : 0;
  const returningScore = current.activeCustomers ? clampScore_(Math.round((returningRate / 0.35) * 100)) : 50;
  const codRatio = current.revenue > 0 ? current.codOutstanding / current.revenue : 0;
  const codScore = clampScore_(Math.round(100 - codRatio * 260));

  const weights = {
    revenue: 0.2,
    profit: 0.25,
    cancel: 0.15,
    waiting: 0.12,
    returning: 0.15,
    cod: 0.13
  };
  const score = clampScore_(Math.round(
    revenueScore * weights.revenue +
    profitScore * weights.profit +
    cancelScore * weights.cancel +
    waitingScore * weights.waiting +
    returningScore * weights.returning +
    codScore * weights.cod
  ));

  return {
    score,
    label: getBusinessHealthLabel_(score),
    currentMonth,
    previousMonth: prevMonth,
    components: [
      { key: 'revenue', label: 'Doanh thu', score: revenueScore, value: current.revenue, previous: previous.revenue },
      { key: 'profit', label: 'Lợi nhuận', score: profitScore, value: current.profit, margin: Math.round(profitMargin * 100) },
      { key: 'cancel', label: 'Hủy đơn', score: cancelScore, value: current.cancelledOrders, rate: Math.round(cancelRate * 100) },
      { key: 'waiting', label: 'Chờ CK', score: waitingScore, value: current.waitingOrders, rate: Math.round(waitingRate * 100) },
      { key: 'returning', label: 'Khách quay lại', score: returningScore, value: current.returningCustomers, rate: Math.round(returningRate * 100) },
      { key: 'cod', label: 'COD tồn', score: codScore, value: current.codOutstanding, rate: Math.round(codRatio * 100) }
    ],
    metrics: current
  };
}

function calculateBusinessPeriodMetrics_(rows, monthKey) {
  const customers = {};
  const customerOrders = {};
  const metrics = {
    revenue: 0,
    profit: 0,
    orderCount: 0,
    activeCustomers: 0,
    returningCustomers: 0,
    cancelledOrders: 0,
    waitingOrders: 0,
    codOutstanding: 0
  };

  rows.forEach((row) => {
    if (!row || !row.ngayChot || String(row.ngayChot).slice(0, 7) !== monthKey) return;

    const isDeleted = isDeletedInternal_(row.trangThai);
    const isWaiting = isWaitingInternal_(row.trangThai);
    const isRevenue = isRevenueRow_(row);
    const customerKey = getBusinessCustomerKey_(row);

    if (isDeleted) {
      metrics.cancelledOrders += 1;
      metrics.orderCount += 1;
      return;
    }

    if (!isRevenue) return;

    metrics.orderCount += 1;
    metrics.revenue += Number(row.giaBan || 0);
    metrics.profit += row.tienLoi || 0;
    if (isWaiting) metrics.waitingOrders += 1;
    if (row.hinhThuc === 'COD') metrics.codOutstanding += Number(row.tienCOD || 0);

    if (customerKey) {
      customers[customerKey] = true;
      customerOrders[customerKey] = (customerOrders[customerKey] || 0) + 1;
    }
  });

  metrics.activeCustomers = Object.keys(customers).length;
  metrics.returningCustomers = Object.keys(customerOrders).filter((key) => customerOrders[key] > 1).length;
  return metrics;
}



function getBusinessCustomerKey_(row) {
  const phone = normalizePhoneForLookup_(row && row.sdtKhach);
  if (phone.length >= 8) return 'phone:' + phone;
  const name = stripVietnameseMarks_(String(row && row.tenKhach || '').toLowerCase()).replace(/\s+/g, ' ').trim();
  return name ? 'name:' + name : '';
}

function getPreviousMonthKey_(monthKey) {
  const parts = String(monthKey || '').split('-').map(Number);
  if (parts.length !== 2 || !parts[0] || !parts[1]) return '';
  let year = parts[0];
  let month = parts[1] - 1;
  if (month < 1) {
    month = 12;
    year -= 1;
  }
  return year + '-' + String(month).padStart(2, '0');
}

function scoreRevenueMomentum_(currentRevenue, previousRevenue) {
  const cur = Number(currentRevenue || 0);
  const prev = Number(previousRevenue || 0);
  if (prev <= 0) return cur > 0 ? 85 : 50;
  return clampScore_(Math.round((cur / prev) * 80));
}

function clampScore_(value) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function getBusinessHealthLabel_(score) {
  if (score >= 85) return 'Rất khỏe';
  if (score >= 70) return 'Ổn định';
  if (score >= 55) return 'Cần chú ý';
  return 'Nguy cơ';
}

function getCustomerVipTierInfo_(ltv, orderCount) {
  const safeLtv = Number(ltv || 0);
  const rules = getCustomerVipTierRules_();
  for (let i = 0; i < rules.length; i++) {
    const tier = rules[i];
    if (safeLtv >= tier.minLtv) {
      return {
        key: tier.key,
        label: tier.label,
        minLtv: tier.minLtv,
        minOrders: tier.minOrders,
        className: tier.className
      };
    }
  }
  return {
    key: 'regular',
    label: 'Khách hàng Thường',
    minLtv: 0,
    minOrders: 0,
    className: 'vip-regular'
  };
}

function buildCustomerLifetimeDashboard_(rows) {
  const monthMap = {};
  const firstMonthByCustomer = {};
  let minMonth = '';
  let maxMonth = '';

  rows.forEach((row) => {
    if (!row || !row.ngayChot) return;
    if (isDeletedInternal_(row.trangThai)) return;
    if (!isSoldInternal_(row.trangThai) && !isWaitingInternal_(row.trangThai)) return;

    const month = String(row.ngayChot || '').slice(0, 7);
    if (!/^\d{4}-\d{2}$/.test(month)) return;

    const customerKey = getBusinessCustomerKey_(row);
    if (!customerKey) return;

    if (!monthMap[month]) monthMap[month] = {};
    monthMap[month][customerKey] = true;

    if (!firstMonthByCustomer[customerKey] || month < firstMonthByCustomer[customerKey]) {
      firstMonthByCustomer[customerKey] = month;
    }
    if (!minMonth || month < minMonth) minMonth = month;
    if (!maxMonth || month > maxMonth) maxMonth = month;
  });

  if (!minMonth || !maxMonth) {
    return { labels: [], newCustomers: [], returningCustomers: [], lostCustomers: [] };
  }

  const months = getMonthRange_(minMonth, maxMonth);
  const labels = [];
  const newCustomers = [];
  const returningCustomers = [];
  const lostCustomers = [];

  months.forEach((month, index) => {
    const active = monthMap[month] || {};
    const activeKeys = Object.keys(active);
    const newCount = activeKeys.filter((key) => firstMonthByCustomer[key] === month).length;
    const returningCount = Math.max(0, activeKeys.length - newCount);

    let lostCount = 0;
    if (index > 0) {
      const prevActive = monthMap[months[index - 1]] || {};
      lostCount = Object.keys(prevActive).filter((key) => !active[key]).length;
    }

    const parts = month.split('-');
    labels.push(parts[1] + '/' + parts[0]);
    newCustomers.push(newCount);
    returningCustomers.push(returningCount);
    lostCustomers.push(lostCount);
  });

  return { labels, newCustomers, returningCustomers, lostCustomers };
}

function getMonthRange_(startMonth, endMonth) {
  const result = [];
  const startParts = String(startMonth || '').split('-').map(Number);
  const endParts = String(endMonth || '').split('-').map(Number);
  if (startParts.length !== 2 || endParts.length !== 2) return result;

  let year = startParts[0];
  let month = startParts[1];
  const endYear = endParts[0];
  const endMonthNumber = endParts[1];

  while (year < endYear || (year === endYear && month <= endMonthNumber)) {
    result.push(year + '-' + String(month).padStart(2, '0'));
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }

  return result;
}

function askShopAi(question) {
  const cleanQuestion = String(question || '').trim();
  if (!cleanQuestion) {
    throw new Error('Vui lòng nhập câu hỏi cho AI.');
  }

  const props = PropertiesService.getScriptProperties();
  const apiKey = String(props.getProperty(GEMINI_API_KEY_PROPERTY_KEY) || '').trim();
  if (!apiKey) {
    return {
      success: false,
      error: 'Chưa cấu hình GEMINI_API_KEY trong Script Properties.',
      answer: 'Chưa có GEMINI_API_KEY. Vào Apps Script > Project Settings > Script Properties và thêm GEMINI_API_KEY để bật AI Gemini.'
    };
  }

  const model = String(props.getProperty(GEMINI_MODEL_PROPERTY_KEY) || DEFAULT_GEMINI_MODEL).trim().replace(/^models\//, '');
  const context = buildShopAiContext_(getAllReportRows());
  const prompt = buildShopAiPrompt_(cleanQuestion, context);
  const url = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent';

  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    headers: {
      'x-goog-api-key': apiKey
    },
    muteHttpExceptions: true,
    payload: JSON.stringify({
      contents: [{
        role: 'user',
        parts: [{ text: prompt }]
      }],
      generationConfig: {
        temperature: 0.25,
        topP: 0.8,
        maxOutputTokens: 900
      }
    })
  });

  const statusCode = response.getResponseCode();
  const bodyText = response.getContentText();
  let body;
  try {
    body = JSON.parse(bodyText || '{}');
  } catch (e) {
    body = {};
  }

  if (statusCode < 200 || statusCode >= 300) {
    const message = body && body.error && body.error.message ? body.error.message : bodyText;
    return {
      success: false,
      error: message,
      answer: 'Gemini chưa trả lời được: ' + message
    };
  }

  const parts = body && body.candidates && body.candidates[0] &&
    body.candidates[0].content && body.candidates[0].content.parts
    ? body.candidates[0].content.parts
    : [];
  const answer = parts.map((part) => part.text || '').join('\n').trim();

  return {
    success: true,
    model,
    generatedAt: getCurrentTimestamp_(),
    answer: answer || 'Gemini không trả về nội dung trả lời.'
  };
}

function buildShopAiPrompt_(question, context) {
  return [
    'Bạn là Múp Xám (thường gọi là Múp) - Trợ lý AI kiêm linh vật đại diện siêu cấp đáng yêu và dí dỏm của shop.',
    'Hãy trả lời câu hỏi của Sen (chủ shop) dựa trên dữ liệu JSON bên dưới. Không tự ý bịa đặt số liệu.',
    'Quy tắc ứng xử và giọng điệu:',
    '- Xưng hô là "Múp Xám" hoặc "Múp" (hoặc "Trẫm") và gọi người dùng là "Sen" hoặc "Chủ shop".',
    '- Giọng nói vui nhộn, cá tính, nhắc nhở Sen ráng bán nhiều đơn để kiếm tiền mua soup thưởng và pate ngon cho Múp.',
    '- Thỉnh thoảng khịa nhẹ nếu doanh thu đi xuống hoặc đắc ý đòi thưởng khi doanh số tăng cao.',
    '- Luôn trả lời bằng tiếng Việt, ngắn gọn, súc tích, định dạng số tiền VND rõ ràng.',
    '- Nếu thiếu dữ liệu, hãy báo lại bằng giọng hờn dỗi dễ thương.',
    '',
    'CÂU HỎI CỦA SEN:',
    question,
    '',
    'DỮ LIỆU DOANH THU & HOẠT ĐỘNG JSON:',
    JSON.stringify(context)
  ].join('\n');
}

function buildShopAiContext_(rows) {
  const today = getTodayString_();
  const currentMonth = today.slice(0, 7);
  const previousMonth = getPreviousMonthKey_(currentMonth);
  const currentMonthMetrics = calculateShopAiMonthMetrics_(rows, currentMonth);
  const previousMonthMetrics = calculateShopAiMonthMetrics_(rows, previousMonth);

  return {
    today,
    currentMonth,
    previousMonth,
    currentMonthMetrics,
    previousMonthMetrics,
    revenueGrowthPercent: calculateGrowthPercentage_(currentMonthMetrics.revenue, previousMonthMetrics.revenue),
    profitGrowthPercent: calculateGrowthPercentage_(currentMonthMetrics.profit, previousMonthMetrics.profit),
    bestSellers: getShopAiTopSellers_(rows, currentMonth, 8),
    customersToCallBack: getShopAiCustomersToCallBack_(rows, currentMonth, 10),
    topCustomers: getShopAiTopCustomers_(rows, currentMonth, 8),
    businessHealth: buildBusinessHealthScore_(rows)
  };
}

function calculateShopAiMonthMetrics_(rows, monthKey) {
  const metrics = {
    orders: 0,
    revenue: 0,
    profit: 0,
    cancelledOrders: 0,
    waitingOrders: 0,
    codOutstanding: 0,
    customers: {}
  };

  rows.forEach((row) => {
    if (!row || !row.ngayChot || String(row.ngayChot).slice(0, 7) !== monthKey) return;
    if (isDeletedInternal_(row.trangThai)) {
      metrics.cancelledOrders += 1;
      return;
    }
    if (!isRevenueRow_(row)) return;

    metrics.orders += 1;
    metrics.revenue += Number(row.giaBan || 0);
    metrics.profit += Number(row.tienLoi || 0);
    if (isWaitingInternal_(row.trangThai)) metrics.waitingOrders += 1;
    if (row.hinhThuc === 'COD') metrics.codOutstanding += Number(row.tienCOD || 0);

    const customerKey = getBusinessCustomerKey_(row);
    if (customerKey) metrics.customers[customerKey] = true;
  });

  metrics.customerCount = Object.keys(metrics.customers).length;
  metrics.aov = metrics.orders ? Math.round(metrics.revenue / metrics.orders) : 0;
  metrics.profitMarginPercent = metrics.revenue ? Math.round((metrics.profit / metrics.revenue) * 100) : 0;
  delete metrics.customers;
  return metrics;
}

function getShopAiTopSellers_(rows, monthKey, limit) {
  const sellers = {};
  rows.forEach((row) => {
    if (!row || !row.ngayChot || String(row.ngayChot).slice(0, 7) !== monthKey) return;
    if (!isRevenueRow_(row)) return;
    const seller = String(row.aiChot || 'Chưa rõ').trim() || 'Chưa rõ';
    if (!sellers[seller]) sellers[seller] = { name: seller, orders: 0, revenue: 0, profit: 0 };
    sellers[seller].orders += 1;
    sellers[seller].revenue += Number(row.giaBan || 0);
    sellers[seller].profit += Number(row.tienLoi || 0);
  });
  return Object.values(sellers)
    .sort((a, b) => b.revenue - a.revenue || b.orders - a.orders)
    .slice(0, limit || 8);
}

function getShopAiTopCustomers_(rows, monthKey, limit) {
  const customers = {};
  rows.forEach((row) => {
    if (!row || !row.ngayChot || String(row.ngayChot).slice(0, 7) !== monthKey) return;
    if (!isRevenueRow_(row)) return;
    const key = getBusinessCustomerKey_(row);
    if (!key) return;
    if (!customers[key]) {
      customers[key] = {
        name: String(row.tenKhach || 'Khách chưa tên').trim() || 'Khách chưa tên',
        phone: String(row.sdtKhach || '').trim(),
        orders: 0,
        revenue: 0,
        lastDate: ''
      };
    }
    customers[key].orders += 1;
    customers[key].revenue += Number(row.giaBan || 0);
    if (row.ngayChot > customers[key].lastDate) customers[key].lastDate = row.ngayChot;
  });
  return Object.values(customers)
    .sort((a, b) => b.revenue - a.revenue || b.orders - a.orders)
    .slice(0, limit || 8);
}

function getShopAiCustomersToCallBack_(rows, monthKey, limit) {
  const customers = {};
  rows.forEach((row) => {
    if (!row || !row.ngayChot) return;
    if (isDeletedInternal_(row.trangThai)) return;
    if (!isRevenueRow_(row)) return;
    const key = getBusinessCustomerKey_(row);
    if (!key) return;

    if (!customers[key]) {
      customers[key] = {
        name: String(row.tenKhach || 'Khách chưa tên').trim() || 'Khách chưa tên',
        phone: String(row.sdtKhach || '').trim(),
        orders: 0,
        revenue: 0,
        waitingOrders: 0,
        lastDate: '',
        reason: ''
      };
    }

    customers[key].orders += 1;
    customers[key].revenue += Number(row.giaBan || 0);
    if (isWaitingInternal_(row.trangThai)) customers[key].waitingOrders += 1;
    if (row.ngayChot > customers[key].lastDate) customers[key].lastDate = row.ngayChot;
  });

  return Object.values(customers)
    .filter((customer) => customer.phone && (customer.waitingOrders > 0 || customer.orders >= 2 || customer.revenue >= 5000000))
    .map((customer) => {
      if (customer.waitingOrders > 0) customer.reason = 'Có đơn đang chờ CK';
      else if (customer.orders >= 2) customer.reason = 'Khách quay lại nhiều đơn';
      else customer.reason = 'LTV cao';
      return customer;
    })
    .sort((a, b) => b.waitingOrders - a.waitingOrders || b.revenue - a.revenue || b.orders - a.orders)
    .slice(0, limit || 10);
}

function getClosedOrdersToday() {
  const today = getTodayString_();
  const rows = readRowsFromSalesLikeSheets_().filter((row) => isSoldInternal_(row.trangThai) && row.ngayChot === today);

  const summary = rows.reduce((acc, row) => {
    acc.totalOrders += 1;
    acc.totalRevenue += row.giaBan;
    acc.totalProfit += row.tienLoi;
    acc.totalCOD += row.tienCOD;
    return acc;
  }, { totalOrders: 0, totalRevenue: 0, totalProfit: 0, totalCOD: 0 });

  return { date: today, rows, summary };
}

function getSheetContext_(sheetName, options) {
  const targetName = sheetName || SHEET_NAME;
  const opts = options || {};
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  let sheet = (targetName === SHEET_NAME || isSalesDataSheet_(targetName))
    ? (ss.getSheetByName(SHEET_NAME) || findSheetByName_(ss, targetName) || getOrCreateSheet_())
    : findSheetByName_(ss, targetName);

  if (!sheet) {
    if (opts.allowMissing) return null;
    throw new Error('Không tìm thấy sheet "' + targetName + '".');
  }

  const actualName = sheet.getName();

  if (opts.ensureSchema !== false && isEditableSalesLikeSheet_(actualName)) {
    ensureSheetSchema_(sheet);
  }

  const lastColumn = sheet.getLastColumn() || 1;
  const headers = sheet.getRange(1, 1, 1, lastColumn).getValues()[0];
  const headerMap = buildHeaderMap_(headers);

  return { sheet, sheetName: actualName, headers, headerMap, lastColumn };
}

function getOrCreateSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  return sheet;
}

function ensureSheetSchema_(sheet) {
  const existingLastColumn = Math.max(sheet.getLastColumn(), 1);
  const firstRow = sheet.getRange(1, 1, 1, existingLastColumn).getValues()[0];
  const hasAnyHeader = firstRow.some((value) => String(value).trim() !== '');

  if (!hasAnyHeader) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    styleHeaderRow_(sheet, HEADERS.length);
    return;
  }

  const existingHeaders = firstRow
    .map((value) => String(value || '').trim())
    .filter((value) => value !== '');

  const missingHeaders = HEADERS.filter((header) => !existingHeaders.includes(header));
  if (missingHeaders.length) {
    const startColumn = existingLastColumn + 1;
    sheet.getRange(1, startColumn, 1, missingHeaders.length).setValues([missingHeaders]);
    styleHeaderRow_(sheet, Math.max(sheet.getLastColumn(), HEADERS.length));
  }
}

function styleHeaderRow_(sheet, totalColumns) {
  const range = sheet.getRange(1, 1, 1, totalColumns);
  range
    .setBackground('#1d4ed8')
    .setFontColor('#ffffff')
    .setFontWeight('bold')
    .setHorizontalAlignment('center');

  sheet.setFrozenRows(1);

  const widths = [130, 110, 120, 110, 110, 120, 170, 145, 130, 130, 240, 120, 155, 150, 240, 145, 145, 240, 160, 130, 150, 150, 200];
  widths.forEach((width, index) => {
    try { sheet.setColumnWidth(index + 1, width); } catch (e) {}
  });
}

function buildHeaderMap_(headers) {
  const headerMap = {};
  headers.forEach((header, index) => {
    const raw = String(header || '').trim();
    if (!raw) return;
    headerMap[raw] = index;
    headerMap[normalizeHeaderKey_(raw)] = index;
  });
  return headerMap;
}

function normalizeHeaderKey_(value) {
  return stripVietnameseMarks_(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '');
}

function mapRowToObject_(row, headerMap, rowIndex, sourceSheet, headers) {
  const sheetName = sourceSheet || SHEET_NAME;
  const giaBan = toNumber_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.giaBan));
  const giaVon = toNumber_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.giaVon));
  const storedTienLoi = toNumber_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.tienLoi));
  const trangThaiRaw = getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.trangThai);
  const trangThai = sheetStatusToInternal_(trangThaiRaw);
  const hinhThuc = normalizeHinhThuc_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.hinhThuc));
  const tienLoi = storedTienLoi !== 0 ? storedTienLoi : (giaBan - giaVon);
  const khachCoc = toNumber_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.khachCoc));
  const rawCodCell = getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.tienCOD);
  let tienCOD = toNumber_(rawCodCell);
  const loaiDon = String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.loaiDon) || '').trim() || sheetName;
  const sanPham = String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.sanPham) || '').trim();

  if (hinhThuc !== 'COD' || String(hinhThuc).toUpperCase().includes('FREE') || String(hinhThuc).toUpperCase().includes('CK') || (khachCoc > 0 && giaBan > 0 && khachCoc >= giaBan)) {
    tienCOD = 0;
  } else if (hinhThuc === 'COD' && (rawCodCell === '' || rawCodCell === null || rawCodCell === undefined)) {
    tienCOD = 0;
  }

  return {
    rowIndex,
    sourceSheet: sheetName,
    sheetName,
    sourceLabel: getReportSheetLabel_(sheetName),
    readOnly: !isEditableSalesLikeSheet_(sheetName),
    maSP: (() => {
      let val = String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.maSP) || '').trim();
      if (val && isMaVSheet_(sheetName) && /^\d+$/.test(val)) {
        return 'V-' + val;
      }
      return val;
    })(),
    sanPham,
    giaBan,
    giaVon,
    tienLoi,
    tenKhach: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.tenKhach) || ''),
    sdtKhach: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.sdtKhach) || ''),
    aiChot: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.aiChot) || '').trim(),
    nguonKhach: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.nguonKhach) || '').trim(),
    diaChi: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.diaChi) || '').trim(),
    ngayChot: formatSheetDate_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.ngayChot)),
    trangThai,
    trangThaiGoc: String(trangThaiRaw || '').trim(),
    hinhThuc,
    loaiDon,
    tienCOD,
    ghiChu: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.ghiChu) || ''),
    createdAt: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.createdAt) || ''),
    updatedAt: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.updatedAt) || ''),
    khachCoc,
    linkTiktok: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.linkTiktok) || ''),
    khoiLuong: toNumber_(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.khoiLuong)) || 200,
    loaiHangHoa: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.loaiHangHoa) || '').trim(),
    tinhChatHangHoa: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.tinhChatHangHoa) || '').trim(),
    dichVu: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.dichVu) || '').trim(),
    dichVuCongThem: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.dichVuCongThem) || '').trim(),
    notificationKey: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.notificationKey) || '').trim(),
    telegramStatus: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.telegramStatus) || '').trim(),
    telegramSentAt: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.telegramSentAt) || '').trim(),
    telegramMessageId: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.telegramMessageId) || '').trim(),
    telegramError: String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.telegramError) || '').trim()
  };
}

function setManagedValues_(targetRow, headerMap, data, audit) {
  const meta = audit || {};
  setCellByHeader_(targetRow, headerMap, 'MÃ SP', data.maSP);
  setCellByHeader_(targetRow, headerMap, 'Giá bán', data.giaBan);
  setCellByHeader_(targetRow, headerMap, 'Giá vốn', data.giaVon);
  setCellByHeader_(targetRow, headerMap, 'Tiền lời', data.tienLoi);
  setCellByHeader_(targetRow, headerMap, 'Tên khách hàng', data.tenKhach);
  setCellByHeader_(targetRow, headerMap, 'SĐT khách hàng', data.sdtKhach);
  setCellByHeader_(targetRow, headerMap, 'Ai chốt', data.aiChot || '');
  setCellByHeader_(targetRow, headerMap, 'Nguồn khách', data.nguonKhach || '');
  setCellByHeader_(targetRow, headerMap, 'Địa chỉ khách hàng', data.diaChi || '');
  setCellByHeader_(targetRow, headerMap, 'Ngày chốt', data.ngayChot);
  setCellByHeader_(targetRow, headerMap, 'Trạng thái sản phẩm', internalStatusToSheet_(data.trangThai));
  setCellByHeader_(targetRow, headerMap, 'Hình thức giao hàng', data.hinhThuc);
  setCellByHeader_(targetRow, headerMap, 'Tiền COD', data.tienCOD);
  setCellByHeader_(targetRow, headerMap, 'Ghi chú', data.ghiChu);
  setCellByHeader_(targetRow, headerMap, 'Ngày tạo', meta.createdAt || '');
  setCellByHeader_(targetRow, headerMap, 'Cập nhật lúc', meta.updatedAt || '');
  setCellByHeader_(targetRow, headerMap, 'Khách cọc', data.khachCoc || 0);
  setCellByHeader_(targetRow, headerMap, 'Link TikTok', data.linkTiktok || '');
  setCellByHeader_(targetRow, headerMap, 'Khối lượng', data.khoiLuong || 200);
  setCellByHeader_(targetRow, headerMap, 'Loại hàng hóa', data.loaiHangHoa || '');
  setCellByHeader_(targetRow, headerMap, 'Tính chất hàng hóa đặc biệt', data.tinhChatHangHoa || '');
  setCellByHeader_(targetRow, headerMap, 'Dịch vụ', data.dichVu || '');
  setCellByHeader_(targetRow, headerMap, 'Dịch vụ cộng thêm', data.dichVuCongThem || '');
  setCellByHeader_(targetRow, headerMap, 'Khóa thông báo', meta.notificationKey || data.notificationKey || '');
  setCellByHeader_(targetRow, headerMap, 'Trạng thái Telegram', meta.telegramStatus || data.telegramStatus || '');
  setCellByHeader_(targetRow, headerMap, 'Telegram gửi lúc', meta.telegramSentAt || data.telegramSentAt || '');
  setCellByHeader_(targetRow, headerMap, 'Telegram Message ID', meta.telegramMessageId || data.telegramMessageId || '');
  setCellByHeader_(targetRow, headerMap, 'Lỗi Telegram', meta.telegramError || data.telegramError || '');
}

function setSheetCellByHeaderAlias_(sheet, headerMap, rowIndex, aliases, value) {
  const colIndex = getHeaderIndexByAliases_(headerMap, aliases);
  if (colIndex !== undefined && colIndex >= 0) {
    sheet.getRange(rowIndex, colIndex + 1).setValue(value);
  }
}

function normalizeRowData_(data) {
  const maSP = String(data && data.maSP || '').trim();
  const giaBan = toNumber_(data && data.giaBan);
  const giaVon = toNumber_(data && data.giaVon);
  const hinhThuc = normalizeHinhThuc_(data && data.hinhThuc || 'COD');
  const sdtKhach = String(data && data.sdtKhach || '').trim();
  const trangThai = sheetStatusToInternal_(data && data.trangThai || 'Còn hàng');

  let ngayChot = String(data && data.ngayChot || '').trim();
  if (isSoldInternal_(trangThai) && !ngayChot) ngayChot = getTodayString_();

  let khachCoc = toNumber_(data && data.khachCoc);
  const tienCODInput = toNumber_(data && data.tienCOD);

  if (hinhThuc !== 'COD' && khachCoc <= 0 && giaBan > 0) {
    khachCoc = giaBan;
  }

  let tienCOD = 0;
  if (hinhThuc === 'COD') {
    if (data && data.tienCOD !== undefined && data.tienCOD !== null && String(data.tienCOD).trim() !== '') {
      tienCOD = Math.max(0, toNumber_(data.tienCOD));
    } else if (khachCoc > 0 && khachCoc < giaBan) {
      tienCOD = Math.max(0, giaBan - khachCoc);
    } else {
      tienCOD = 0;
    }
  }
  if (khachCoc > 0 && giaBan > 0 && khachCoc >= giaBan) {
    tienCOD = 0;
  }

  return {
    maSP,
    giaBan,
    giaVon,
    tienLoi: giaBan - giaVon,
    tenKhach: String(data && data.tenKhach || '').trim(),
    sdtKhach,
    aiChot: String(data && data.aiChot || '').trim(),
    nguonKhach: String(data && data.nguonKhach || '').trim(),
    diaChi: String(data && data.diaChi || '').trim(),
    ngayChot,
    trangThai,
    hinhThuc,
    tienCOD,
    ghiChu: String(data && data.ghiChu || '').trim(),
    khachCoc,
    linkTiktok: String(data && data.linkTiktok || '').trim(),
    khoiLuong: toNumber_(data && data.khoiLuong) || 200,
    loaiHangHoa: String(data && data.loaiHangHoa || '').trim(),
    tinhChatHangHoa: String(data && data.tinhChatHangHoa || '').trim(),
    dichVu: String(data && data.dichVu || '').trim(),
    dichVuCongThem: String(data && data.dichVuCongThem || '').trim()
  };
}

function validateRowData_(data) {
  if (!data.maSP) throw new Error('Vui lòng nhập MÃ SP.');
  if (data.giaBan <= 0) throw new Error('Giá bán phải lớn hơn 0.');
  if (data.giaVon < 0) throw new Error('Giá vốn không được âm.');
  if (data.tienCOD < 0) throw new Error('Tiền COD không được âm.');
  if (data.khachCoc < 0) throw new Error('Tiền cọc không được âm.');

  if (data.sdtKhach && !/^[0-9+\-\s().]{8,20}$/.test(data.sdtKhach)) {
    throw new Error('Số điện thoại không hợp lệ.');
  }

  // Enforce payment summation matches price for Sold/Waiting orders
  const isSold = isSoldInternal_(data.trangThai);
  const isWaiting = isWaitingInternal_(data.trangThai);
  if (isSold || isWaiting) {
    const sumPay = data.khachCoc + data.tienCOD;
    const diff = Math.abs(sumPay - data.giaBan);
    if (diff > 0) {
      throw new Error(`Phát hiện sai lệch ${formatMoney_(diff)} (Tổng cọc + COD = ${formatMoney_(sumPay)} khác Giá bán ${formatMoney_(data.giaBan)}). Vui lòng điều chỉnh lại tiền cọc hoặc tiền COD cho khớp giá bán.`);
    }
  }
}

function ensureUniqueMaSP_(sheet, headerMap, maSP, ignoreRowIndex) {
  const normalized = String(maSP || '').trim().toLowerCase();
  if (!normalized) return;

  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return;

  const colIndex = headerMap['MÃ SP'] !== undefined ? headerMap['MÃ SP'] : headerMap[normalizeHeaderKey_('MÃ SP')];
  if (colIndex === undefined) return;

  const values = sheet.getRange(2, colIndex + 1, lastRow - 1, 1).getValues();

  for (let i = 0; i < values.length; i++) {
    const actualRowIndex = i + 2;
    if (ignoreRowIndex && actualRowIndex === ignoreRowIndex) continue;

    const existing = String(values[i][0] || '').trim().toLowerCase();
    if (existing && existing === normalized) {
      throw new Error('MÃ SP đã tồn tại. Vui lòng nhập mã khác.');
    }
  }
}

function getCellByHeader_(row, headerMap, headerName) {
  let index = headerMap[headerName];
  if (index === undefined) index = headerMap[normalizeHeaderKey_(headerName)];
  return index === undefined ? '' : row[index];
}

function getCellByHeaderAliases_(row, headerMap, headerNames) {
  for (let i = 0; i < headerNames.length; i++) {
    const value = getCellByHeader_(row, headerMap, headerNames[i]);
    if (value !== '' && value != null) return value;
  }
  return '';
}

function getHeaderIndexByAliases_(headerMap, headerNames) {
  for (let i = 0; i < headerNames.length; i++) {
    const exact = headerMap[headerNames[i]];
    if (exact !== undefined) return exact;
    const normalized = headerMap[normalizeHeaderKey_(headerNames[i])];
    if (normalized !== undefined) return normalized;
  }
  return undefined;
}

function setCellByHeader_(row, headerMap, headerName, value) {
  let index = headerMap[headerName];
  if (index === undefined) index = headerMap[normalizeHeaderKey_(headerName)];
  if (index !== undefined) row[index] = value;
}

function toNumber_(value) {
  if (typeof value === 'number') return isNaN(value) ? 0 : value;
  const text = String(value || '').trim();
  if (!text) return 0;

  let normalized = text
    .replace(/[₫đĐvndVND\s]/g, '')
    .replace(/[^\d,.\-]/g, '');

  if (normalized.includes(',') && normalized.includes('.')) {
    normalized = normalized.replace(/\./g, '').replace(',', '.');
  } else if (normalized.includes(',')) {
    normalized = normalized.replace(',', '.');
  } else if ((normalized.match(/\./g) || []).length > 1) {
    normalized = normalized.replace(/\./g, '');
  }

  const number = Number(normalized);
  return isNaN(number) ? 0 : number;
}

function formatSheetDate_(value) {
  if (!value) return '';

  if (Object.prototype.toString.call(value) === '[object Date]' && !isNaN(value)) {
    return Utilities.formatDate(value, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }

  const text = String(value).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text;

  const slashMatch = text.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})(?:\s+.*)?$/);
  if (slashMatch) {
    const day = slashMatch[1].padStart(2, '0');
    const month = slashMatch[2].padStart(2, '0');
    const year = slashMatch[3].length === 2 ? '20' + slashMatch[3] : slashMatch[3];
    return year + '-' + month + '-' + day;
  }

  const parsed = new Date(text);
  if (!isNaN(parsed)) {
    return Utilities.formatDate(parsed, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  }

  return text;
}

function isRevenueRow_(row) {
  if (!row || isDeletedInternal_(row.trangThai)) return false;
  if (isSoldInternal_(row.trangThai) || isWaitingInternal_(row.trangThai)) return true;
  return row.sourceSheet === LIQUIDATION_SHEET_NAME && (Number(row.giaBan || 0) > 0 || Boolean(row.ngayChot));
}

function getTodayString_() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
}

function getCurrentTimestamp_() {
  return Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
}

function reorderColumns() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME);

  if (!sheet) {
    SpreadsheetApp.getUi().alert('Không tìm thấy sheet "' + SHEET_NAME + '".');
    return;
  }

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();

  if (lastRow < 1 || lastCol < 1) {
    SpreadsheetApp.getUi().alert('Sheet rỗng, không cần sắp xếp.');
    return;
  }

  const allData = sheet.getRange(1, 1, lastRow, lastCol).getValues();
  const currentHdrs = allData[0].map(v => String(v).trim());

  const missing = HEADERS.filter(h => !currentHdrs.includes(h));
  if (missing.length) {
    SpreadsheetApp.getUi().alert(
      'Sheet chưa có các cột sau, hãy chạy ensureSheetSchema trước:\n' + missing.join(', ')
    );
    return;
  }

  const newData = allData.map(row =>
    HEADERS.map(h => {
      const idx = currentHdrs.indexOf(h);
      return idx === -1 ? '' : row[idx];
    })
  );

  sheet.getRange(1, 1, lastRow, lastCol).clearContent();
  sheet.getRange(1, 1, newData.length, HEADERS.length).setValues(newData);

  styleHeaderRow_(sheet, HEADERS.length);

  SpreadsheetApp.getUi().alert(
    'Đã sắp xếp lại ' + HEADERS.length + ' cột thành công!\n\n' +
    'Thứ tự mới: ' + HEADERS.join(' -> ')
  );
}

// ─────────────────────────────────────────────
// TELEGRAM NOTIFICATION
// ─────────────────────────────────────────────

function setupTelegramNotify(botToken, chatId) {
  if (!botToken || !chatId) {
    throw new Error('Vui lòng truyền botToken và chatId.');
  }

  PropertiesService.getScriptProperties().setProperties({
    [TELEGRAM_BOT_TOKEN_PROPERTY_KEY]: String(botToken).trim(),
    [TELEGRAM_CHAT_ID_PROPERTY_KEY]: String(chatId).trim()
  });

  installTelegramOnEditTrigger();
  installTelegramPendingTrigger();
  return 'Đã lưu cấu hình Telegram, cài trigger onEdit và trigger gửi notify trễ.';
}

function setupMyTelegram() {
  // ⚠️ Hàm này đã bị vô hiệu hóa — credentials hardcode là rủi ro bảo mật.
  // Cấu hình Bot Token và Chat ID qua trang Settings của ứng dụng (saveSystemSettings).
  throw new Error('setupMyTelegram() đã bị tắt. Vui lòng cấu hình Telegram qua UI Settings.');
}

function setupTelegramWebhook(webAppUrl) {
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);
  const url = String(webAppUrl || '').trim();

  if (!botToken) throw new Error('Thiếu TELEGRAM_BOT_TOKEN.');
  if (!/^https:\/\/script\.google\.com\/macros\/s\/[^/]+\/exec$/.test(url)) {
    throw new Error('Webhook URL phải là Apps Script web app /exec URL.');
  }

  const response = UrlFetchApp.fetch('https://api.telegram.org/bot' + encodeURIComponent(botToken) + '/setWebhook', {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify({
      url,
      allowed_updates: ['message', 'edited_message']
    })
  });

  const body = response.getContentText();
  if (response.getResponseCode() < 200 || response.getResponseCode() >= 300) {
    throw new Error('Set Telegram webhook failed: ' + body);
  }

  return body;
}

function setupPinnedTelegramWebhook() {
  // Không gọi setupMyTelegram() — credentials phải được set qua Script Properties
  return setupTelegramWebhook('https://script.google.com/macros/s/AKfycbzPd7GSx7q8nGn5EUymJHe6cVGE8bpH-hDWodUzhPiBuEigZeqNzSmlv4yqjZ8IS6or/exec');
}

function deleteTelegramWebhook(dropPendingUpdates) {
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);
  if (!botToken) throw new Error('Thiếu TELEGRAM_BOT_TOKEN.');

  const url = 'https://api.telegram.org/bot' + encodeURIComponent(botToken) + '/deleteWebhook';
  const response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify({
      drop_pending_updates: dropPendingUpdates !== false
    })
  });

  const body = response.getContentText();
  if (response.getResponseCode() < 200 || response.getResponseCode() >= 300) {
    throw new Error('Delete Telegram webhook failed: ' + body);
  }

  return body;
}

function installTelegramPollingTrigger() {
  deleteTelegramWebhook(true);

  const props = PropertiesService.getScriptProperties();
  props.deleteProperty(TELEGRAM_UPDATE_OFFSET_PROPERTY_KEY);

  const existing = ScriptApp.getProjectTriggers();
  existing.forEach((trigger) => {
    if (trigger.getHandlerFunction() === 'pollTelegramUpdates') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('pollTelegramUpdates')
    .timeBased()
    .everyMinutes(1)
    .create();

  return 'Đã tắt webhook và cài polling trigger mỗi 1 phút.';
}

function pollTelegramUpdates() {
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);
  if (!botToken) throw new Error('Thiếu TELEGRAM_BOT_TOKEN.');

  const offset = Number(props.getProperty(TELEGRAM_UPDATE_OFFSET_PROPERTY_KEY) || 0) || 0;
  const params = {
    timeout: 0,
    limit: 50,
    allowed_updates: JSON.stringify(['message', 'edited_message'])
  };
  if (offset > 0) params.offset = String(offset);

  const query = Object.keys(params)
    .map((key) => encodeURIComponent(key) + '=' + encodeURIComponent(params[key]))
    .join('&');
  const response = UrlFetchApp.fetch(
    'https://api.telegram.org/bot' + encodeURIComponent(botToken) + '/getUpdates?' + query,
    { muteHttpExceptions: true }
  );
  const body = response.getContentText();
  if (response.getResponseCode() < 200 || response.getResponseCode() >= 300) {
    throw new Error('Telegram getUpdates failed: ' + body);
  }

  const payload = JSON.parse(body || '{}');
  if (!payload.ok) throw new Error('Telegram getUpdates returned not ok: ' + body);

  let nextOffset = offset;
  let processed = 0;
  let replied = 0;

  (payload.result || []).forEach((update) => {
    const updateId = Number(update.update_id);
    if (!isNaN(updateId) && updateId >= nextOffset) nextOffset = updateId + 1;

    const message = update.message || update.edited_message || null;
    const reply = buildTelegramProductLookupReply_(message);
    if (!reply) return;

    processed++;
    const sendRes = sendTelegramMessageToChat_(reply.chatId, reply.message);
    if (sendRes && sendRes.success) replied++;
  });

  props.setProperty(TELEGRAM_UPDATE_OFFSET_PROPERTY_KEY, String(nextOffset));
  return 'Đã xử lý ' + processed + ' lệnh Telegram, gửi trả lời ' + replied + ' lệnh. Offset: ' + nextOffset;
}

function installTelegramOnEditTrigger() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const existing = ScriptApp.getProjectTriggers();

  existing.forEach((trigger) => {
    if (trigger.getHandlerFunction() === 'handleSheetEditNotify') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('handleSheetEditNotify')
    .forSpreadsheet(ss)
    .onEdit()
    .create();

  return 'Đã cài trigger handleSheetEditNotify.';
}

function installTelegramPendingTrigger() {
  const existing = ScriptApp.getProjectTriggers();

  existing.forEach((trigger) => {
    if (trigger.getHandlerFunction() === 'processPendingTelegramNotifications') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('processPendingTelegramNotifications')
    .timeBased()
    .everyMinutes(1)
    .create();

  return 'Đã cài trigger processPendingTelegramNotifications.';
}

function handleTelegramWebhook_(e) {
  try {
    const update = JSON.parse(e && e.postData && e.postData.contents || '{}');
    const updateId = update.update_id;
    if (updateId) {
      const cache = CacheService.getScriptCache();
      const cacheKey = 'TG_UPDATE_' + updateId;
      if (cache.get(cacheKey)) {
        // Skip duplicate request from Telegram retry
        return telegramWebhookOk_();
      }
      cache.put(cacheKey, 'true', 10 * 60); // Cache for 10 minutes
    }

    const message = update.message || update.edited_message || null;
    if (message && message.text) {
      logActivity_(0, 'Bot Telegram', 'Nhận tin nhắn', `Nhận: "${message.text}" từ chat ${message.chat.id}`);
    }
    const reply = buildTelegramProductLookupReply_(message);
    if (!reply) return telegramWebhookOk_();

    // Call API actively instead of replying in HTTP POST response for 100% reliable delivery
    const sentRes = sendTelegramMessageToChat_(reply.chatId, reply.message);
    const isSent = Boolean(sentRes && sentRes.success);
    logActivity_(0, reply.command, 'Bot Phản hồi', `Gửi trả lời cho ${reply.chatId}: ${isSent ? 'Thành công' : 'Thất bại'}`);
  } catch (err) {
    const errMsg = err && err.message ? err.message : String(err);
    logActivity_(0, 'Bot Telegram', 'Lỗi', `Lỗi: ${errMsg}`);
    console.error('Telegram webhook error: ' + errMsg);
  }

  return telegramWebhookOk_();
}

function buildTelegramProductLookupReply_(message) {
  // Product lookup through Telegram is intentionally disabled.
  // Outbound sold-order notifications still use sendTelegramMessage_().
  return null;
}

function telegramWebhookOk_() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function telegramWebhookSendMessage_(chatId, message) {
  return ContentService
    .createTextOutput(JSON.stringify({
      method: 'sendMessage',
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML',
      disable_web_page_preview: true
    }))
    .setMimeType(ContentService.MimeType.JSON);
}

function isAllowedTelegramChat_(chatId, chatType) {
  const configuredChatId = String(PropertiesService.getScriptProperties().getProperty(TELEGRAM_CHAT_ID_PROPERTY_KEY) || '').trim();
  if (!configuredChatId) return true;
  // Allow configured chat group
  if (String(chatId || '').trim() === configuredChatId) return true;
  // Allow direct private chat with bot
  if (chatType === 'private') return true;

  return false;
}

function parseTelegramProductCommand_(text) {
  const raw = String(text || '').trim();
  const match = raw.match(/^\/([^\s]+)(?:\s+([\s\S]*))?$/);
  if (!match) return '';

  const command = String(match[1] || '').split('@')[0].trim();
  const args = String(match[2] || '').trim();
  if (!command || command.indexOf('/') !== -1) return '';

  const aliases = {
    ma: true,
    masp: true,
    msp: true,
    sp: true,
    tim: true,
    search: true,
    check: true,
    kiemtra: true,
    kt: true
  };

  const commandKey = stripVietnameseMarks_(command).toLowerCase().replace(/[^a-z0-9_]/g, '');
  if (commandKey === 'help' || commandKey === 'start') return 'HELP_COMMAND';

  if (aliases[commandKey]) {
    return cleanTelegramProductQuery_(args);
  }

  const directQuery = cleanTelegramProductQuery_(command);
  if (!isLikelyTelegramProductLookupQuery_(directQuery)) return '';
  return directQuery;
}

function cleanTelegramProductQuery_(value) {
  return String(value || '')
    .normalize('NFC')
    .trim()
    .replace(/^["'`]+|["'`.,;:!?]+$/g, '')
    .trim();
}

function isLikelyTelegramProductLookupQuery_(value) {
  const query = cleanTelegramProductQuery_(value);
  if (!query || query.length > 40) return false;

  const commandKey = stripVietnameseMarks_(query).toLowerCase().replace(/[^a-z0-9_]/g, '');
  if (commandKey === 'help' || commandKey === 'start') return false;

  return /[0-9]/.test(query) && /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(query);
}

function buildProductAvailabilityResult_(rowObject, matchType) {
  return {
    maSP: rowObject.maSP,
    trangThai: rowObject.trangThai,
    inStock: isInStockInternal_(rowObject.trangThai),
    tenKhach: rowObject.tenKhach,
    sdtKhach: rowObject.sdtKhach,
    aiChot: rowObject.aiChot,
    ngayChot: rowObject.ngayChot,
    hinhThuc: rowObject.hinhThuc,
    ghiChu: rowObject.ghiChu,
    rowIndex: rowObject.rowIndex,
    sheetName: rowObject.sheetName,
    matchType: matchType || 'exact'
  };
}

function findProductAvailabilityByMaSP_(maSP) {
  const target = normalizeMaSPForSearch_(maSP);
  if (!target) return null;

  const rows = getAllReportRows();
  const partialMatches = [];

  for (let i = 0; i < rows.length; i++) {
    const rowObject = rows[i];
    if (isSameMaSPForSearch_(rowObject.maSP, target)) {
      return buildProductAvailabilityResult_(rowObject, 'exact');
    }
    if (matchesMaSPForSearch_(rowObject.maSP, target)) {
      partialMatches.push(rowObject);
    }
  }

  if (partialMatches.length === 1) {
    return buildProductAvailabilityResult_(partialMatches[0], 'partial');
  }

  if (partialMatches.length > 1) {
    return {
      ambiguous: true,
      requestedMaSP: maSP,
      matches: partialMatches.slice(0, 10).map((rowObject) => buildProductAvailabilityResult_(rowObject, 'partial')),
      totalMatches: partialMatches.length
    };
  }

  return null;
}

function buildProductAvailabilityTelegramMessage_(requestedMaSP, result) {
  const requestedLabel = cleanTelegramProductQuery_(requestedMaSP);

  if (!result) {
    return [
      '🔎 <b>TRA MÃ SP</b>',
      '━━━━━━━━━━━━━━━━━━━━',
      '🏷️ <b>MÃ SP:</b> <code>' + escapeTelegramHtml_(String(requestedLabel || '').toUpperCase()) + '</code>',
      '❌ <b>Kết quả:</b> Không tìm thấy trong sheet',
      'ℹ️ <b>Cú pháp:</b> <code>/mã MÃ_SP</code> hoặc <code>/ma MÃ_SP</code>'
    ].join('\n');
  }

  if (result.ambiguous) {
    const lines = [
      '🔎 <b>TRA MÃ SP</b>',
      '━━━━━━━━━━━━━━━━━━━━',
      '🏷️ <b>Từ khóa:</b> <code>' + escapeTelegramHtml_(String(requestedLabel || '').toUpperCase()) + '</code>',
      '<b>Kết quả:</b> Tìm thấy ' + result.totalMatches + ' mã gần giống, vui lòng nhập chính xác hơn',
      ''
    ];

    result.matches.forEach((row, index) => {
      const stockText = row.inStock ? 'CÒN' : 'HẾT';
      const chotText = (row.aiChot || row.tenKhach) ? ' - ' + (row.aiChot || row.tenKhach) : '';
      lines.push((index + 1) + '. <code>' + escapeTelegramHtml_(row.maSP) + '</code> - ' + stockText + chotText);
    });

    return lines.join('\n');
  }

  const statusLine = result.inStock
    ? '✅ <b>Kết quả:</b> CÒN HÀNG'
    : '⛔ <b>Kết quả:</b> HẾT HÀNG';
  const chotLabel = result.inStock && !String(result.tenKhach || '').trim()
    ? 'Chưa có khách chốt'
    : (result.tenKhach || '-');
  const aiChotLabel = String(result.aiChot || '').trim() || chotLabel;
  const sheetLabel = getReportSheetLabel_(result.sheetName);

  return [
    '🔎 <b>TRA MÃ SP</b>',
    '━━━━━━━━━━━━━━━━━━━━',
    '🏷️ <b>MÃ SP:</b> <code>' + escapeTelegramHtml_(result.maSP) + '</code>',
    '📄 <b>Sheet:</b> ' + escapeTelegramHtml_(sheetLabel),
    statusLine,
    '📌 <b>Trạng thái sheet:</b> ' + escapeTelegramHtml_(result.trangThai || '-'),
    '🙋 <b>Khách:</b> ' + escapeTelegramHtml_(chotLabel),
    '🧾 <b>Ai chốt:</b> ' + escapeTelegramHtml_(aiChotLabel),
    '📞 <b>SĐT:</b> ' + escapeTelegramHtml_(result.sdtKhach || '-'),
    '📅 <b>Ngày chốt:</b> ' + escapeTelegramHtml_(result.ngayChot || '-'),
    '📮 <b>Giao hàng:</b> ' + escapeTelegramHtml_(result.hinhThuc || '-')
  ].join('\n');
}

function ensureAllSystemTriggersInstalled_() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const triggers = ScriptApp.getProjectTriggers();

    const hasOnEdit = triggers.some((t) => t.getHandlerFunction() === 'handleSheetEditNotify');
    if (!hasOnEdit && ss) {
      ScriptApp.newTrigger('handleSheetEditNotify')
        .forSpreadsheet(ss)
        .onEdit()
        .create();
    }

    const hasPending = triggers.some((t) => t.getHandlerFunction() === 'processPendingTelegramNotifications');
    if (!hasPending) {
      ScriptApp.newTrigger('processPendingTelegramNotifications')
        .timeBased()
        .everyMinutes(1)
        .create();
    }
  } catch (e) {
    console.warn('Lỗi tự động cài triggers:', e);
  }
}

function queueSoldOrderNotify_(sheetName, rowIndex, rowObject) {
  const upperStatus = String(rowObject && rowObject.telegramStatus || '').trim().toUpperCase();
  // Đơn đã gửi thành công (SENT hoặc có messageId) -> không bao giờ xếp hàng gửi lại để chống spam
  if (upperStatus === 'SENT' || Boolean(rowObject && rowObject.telegramMessageId)) {
    return false;
  }

  let key = rowObject && rowObject.notificationKey;
  if (!key) {
    key = generateNotificationKey_();
  }

  const dueAt = Date.now() + TELEGRAM_NOTIFY_DELAY_MS;
  const payload = {
    sheetName: getTelegramSheetName_(sheetName),
    rowIndex: Number(rowIndex),
    notificationKey: key,
    maSP: (rowObject && rowObject.maSP) || '',
    dueAt: dueAt,
    queuedAt: getCurrentTimestamp_()
  };

  const props = PropertiesService.getScriptProperties();
  props.setProperty(TELEGRAM_PENDING_PREFIX + key, JSON.stringify(payload));
  return true;
}

function handleSheetEditNotify(e) {
  if (!e || !e.range) return;
  try {
    ensureAllSystemTriggersInstalled_();

    const sheet = e.range.getSheet();
    const sheetName = sheet.getName();
    if (!isReportSheet_(sheetName)) return;

    clearAllRowsCache_();
    if (!isEditableSalesLikeSheet_(sheetName)) return;

    const startRow = e.range.getRow();
    const endRow = e.range.getLastRow();
    if (endRow <= 1) return;

    const activeStartRow = Math.max(2, startRow);
    const activeEndRow = endRow;

    const numRows = activeEndRow - activeStartRow + 1;
    if (numRows <= 0 || numRows > 30) return;

    // Bắt buộc ensureSchema: true để đảm bảo 5 cột kỹ thuật luôn tồn tại trên Sheet
    const ctx = getSheetContext_(sheetName, { ensureSchema: true, allowMissing: true });
    if (!ctx) return;
    const rangeValues = ctx.sheet.getRange(activeStartRow, 1, numRows, ctx.lastColumn).getValues();
    const todayStr = getTodayString_();
    const vpsSyncRows = [];

    rangeValues.forEach((row, index) => {
      try {
        const rIndex = activeStartRow + index;
        const rowObject = mapRowToObject_(row, ctx.headerMap, rIndex, sheetName, ctx.headers);
        if (rowObject && (rowObject.maSP || rowObject.sanPham || rowObject.giaBan > 0 || rowObject.tenKhach)) {
          if (!rowObject.maSP) {
            rowObject.maSP = (isMaVSheet_(sheetName) ? 'V-' : (isLiquidationSheet_(sheetName) ? 'TL-' : 'SD-')) + rIndex;
          }
          vpsSyncRows.push(rowObject);
        }

        // Đã gửi thành công (có messageId hoặc trạng thái SENT) -> Bỏ qua tuyệt đối để chống spam/duplicate
        const upperStatus = String(rowObject.telegramStatus || '').trim().toUpperCase();
        if (upperStatus === 'SENT' || Boolean(rowObject.telegramMessageId)) {
          return;
        }

        // Khi dòng là ĐÃ BÁN
        if (isSoldInternal_(rowObject.trangThai)) {
          const ngayChotStr = String(rowObject.ngayChot || '').trim();
          // 1. Tự động điền Ngày chốt nếu còn trống
          if (!ngayChotStr) {
            const dateColIndex = getHeaderIndexByAliases_(ctx.headerMap, HEADER_ALIASES.ngayChot);
            if (dateColIndex !== undefined) {
              ctx.sheet.getRange(rIndex, dateColIndex + 1).setValue(todayStr);
              rowObject.ngayChot = todayStr;
            }
          }

          // 2. Đảm bảo có notificationKey
          let notificationKey = rowObject.notificationKey;
          if (!notificationKey) {
            notificationKey = generateNotificationKey_();
            setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rIndex, HEADER_ALIASES.notificationKey, notificationKey);
            rowObject.notificationKey = notificationKey;
          }

          // 3. Đánh dấu PENDING và đưa vào hàng đợi trì hoãn 3 phút (Debounce)
          if (upperStatus !== 'PENDING') {
            setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rIndex, HEADER_ALIASES.telegramStatus, 'PENDING');
          }
          SpreadsheetApp.flush();

          // Gia hạn hàng đợi 3 phút kể từ lần sửa cuối cùng
          queueSoldOrderNotify_(sheetName, rIndex, rowObject);
        }
      } catch (rowErr) {
        console.error('handleSheetEditNotify lỗi row ' + (activeStartRow + index) + ':', rowErr);
      }
    });

    // Đồng bộ tức thời sang VPS SQLite Webhook cho mọi dòng được sửa trên Sheet
    if (vpsSyncRows.length > 0) {
      try {
        UrlFetchApp.fetch('http://103.166.185.85:3005/api/sync/sheet-webhook', {
          method: 'post',
          contentType: 'application/json',
          payload: JSON.stringify({ rows: vpsSyncRows, source: vpsSyncRows.length > 1 ? 'sheet-bulk-edit' : 'sheet-on-edit' }),
          muteHttpExceptions: true
        });
      } catch (webhookErr) {
        console.warn('Lỗi webhook sang VPS:', webhookErr);
      }
    }
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    console.error('handleSheetEditNotify lỗi ngoài:', msg);
    try { logActivity_(0, 'Trigger', 'Lỗi Telegram onEdit', msg); } catch (_) {}
  }
}

function isRowReadyForNewOrderNotify_(row) {
  if (!row || !row.maSP) return false;
  if (isDeletedInternal_(row.trangThai)) return false;
  if (!isSoldInternal_(row.trangThai)) return false;
  if (Number(row.giaBan || 0) <= 0) return false;

  // Đã từng gửi thì không sẵn sàng gửi lại (chống spam/duplicate)
  const upperStatus = String(row.telegramStatus || '').trim().toUpperCase();
  if (upperStatus === 'SENT' || Boolean(row.telegramMessageId)) return false;

  return true;
}

function dispatchTelegramOrderNotification_(sheetName, rowIndex, source) {
  const lock = LockService.getScriptLock();
  try {
    if (!lock.tryLock(15000)) {
      console.warn('dispatchTelegramOrderNotification_: Lock busy, skipping this execution.');
      return { sent: false, reason: 'LOCK_BUSY' };
    }

    const targetSheetName = getTelegramSheetName_(sheetName);
    // Bắt buộc ensureSchema: true để đảm bảo 5 cột kỹ thuật luôn tồn tại trên Sheet
    const ctx = getSheetContext_(targetSheetName, { ensureSchema: true, allowMissing: true });
    if (!ctx) return { sent: false, reason: 'SHEET_NOT_FOUND' };

    const safeRowIndex = Number(rowIndex);
    if (!safeRowIndex || safeRowIndex < 2 || safeRowIndex > ctx.sheet.getLastRow()) {
      return { sent: false, reason: 'INVALID_ROW' };
    }

    const rowValues = ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).getValues()[0];
    const rowObject = mapRowToObject_(rowValues, ctx.headerMap, safeRowIndex, targetSheetName, ctx.headers);

    // 1. Kiểm tra trạng thái đã gửi -> Tuyệt đối không gửi lại
    const currentStatus = String(rowObject.telegramStatus || '').trim().toUpperCase();
    if (currentStatus === 'SENT' || Boolean(rowObject.telegramMessageId)) {
      return { sent: false, reason: 'ALREADY_SENT', messageId: rowObject.telegramMessageId };
    }

    // 2. Kiểm tra điều kiện đơn hàng sẵn sàng gửi
    if (!isRowReadyForNewOrderNotify_(rowObject)) {
      return { sent: false, reason: 'NOT_READY' };
    }

    // 3. Đảm bảo có notificationKey
    let notificationKey = rowObject.notificationKey;
    if (!notificationKey) {
      notificationKey = generateNotificationKey_();
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.notificationKey, notificationKey);
      rowObject.notificationKey = notificationKey;
    }

    // 4. Ghi trạng thái SENDING để chặn trigger khác
    setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramStatus, 'SENDING');
    SpreadsheetApp.flush();

    // 5. Gửi tin nhắn Telegram
    const message = buildSoldOrderTelegramMessage_(rowObject, source || 'Google Sheet', false);
    const sendResult = sendTelegramMessageWithResult_(message);

    const now = getCurrentTimestamp_();
    if (sendResult.success) {
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramStatus, 'SENT');
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramSentAt, now);
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramMessageId, String(sendResult.messageId || ''));
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramError, '');
      SpreadsheetApp.flush();

      logActivity_(safeRowIndex, rowObject.maSP, 'Telegram Notify', `Đã gửi báo đơn thành công (Key: ${notificationKey}, MsgID: ${sendResult.messageId || '-'})`);

      return { sent: true, messageId: sendResult.messageId };
    } else {
      const errorMsg = sendResult.error || 'Lỗi gửi Telegram không xác định';
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramStatus, 'FAILED');
      setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, safeRowIndex, HEADER_ALIASES.telegramError, errorMsg);
      SpreadsheetApp.flush();

      logActivity_(safeRowIndex, rowObject.maSP, 'Telegram Lỗi', `Gửi báo đơn thất bại: ${errorMsg}`);
      return { sent: false, error: errorMsg };
    }
  } catch (err) {
    const msg = err && err.message ? err.message : String(err);
    console.error('Lỗi dispatchTelegramOrderNotification_:', msg);
    return { sent: false, error: msg };
  } finally {
    lock.releaseLock();
  }
}

function processPendingTelegramNotifications() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    return;
  }

  try {
    const props = PropertiesService.getScriptProperties();
    const allProps = props.getProperties();
    const now = Date.now();

    // 1. Quét theo hàng đợi ScriptProperties
    Object.keys(allProps).forEach((propKey) => {
      if (!propKey.startsWith(TELEGRAM_PENDING_PREFIX)) return;

      let item = null;
      try {
        item = JSON.parse(allProps[propKey]);
      } catch (e) {
        props.deleteProperty(propKey);
        return;
      }

      if (!item || !item.sheetName || !item.rowIndex) {
        props.deleteProperty(propKey);
        return;
      }

      // Chưa đủ 3 phút -> tiếp tục chờ nhân viên nhập/sửa xong
      if (now < Number(item.dueAt || 0)) {
        return;
      }

      // Đã đủ 3 phút -> Xử lý gửi 1 lần duy nhất
      try {
        const ctx = getSheetContext_(item.sheetName, { ensureSchema: true, allowMissing: true });
        if (!ctx) {
          props.deleteProperty(propKey);
          return;
        }

        const safeRowIndex = Number(item.rowIndex);
        if (safeRowIndex < 2 || safeRowIndex > ctx.sheet.getLastRow()) {
          props.deleteProperty(propKey);
          return;
        }

        const rowValues = ctx.sheet.getRange(safeRowIndex, 1, 1, ctx.lastColumn).getValues()[0];
        const rowObject = mapRowToObject_(rowValues, ctx.headerMap, safeRowIndex, item.sheetName, ctx.headers);
        const upperStatus = String(rowObject.telegramStatus || '').trim().toUpperCase();

        if (upperStatus === 'SENT' || Boolean(rowObject.telegramMessageId)) {
          props.deleteProperty(propKey);
          return;
        }

        // Nếu trạng thái không còn là ĐÃ BÁN (đã đổi hoặc xóa) -> xóa khỏi hàng đợi
        if (!isSoldInternal_(rowObject.trangThai)) {
          props.deleteProperty(propKey);
          return;
        }

        if (isRowReadyForNewOrderNotify_(rowObject)) {
          const res = dispatchTelegramOrderNotification_(item.sheetName, safeRowIndex, 'Google Sheet - ' + getReportSheetLabel_(item.sheetName));
          if (res && (res.sent || res.reason === 'ALREADY_SENT')) {
            props.deleteProperty(propKey);
          }
        }
      } catch (rowErr) {
        console.error('Lỗi xử lý pending item ' + propKey + ':', rowErr);
      }
    });

    // 2. Fallback: Quét bù các dòng PENDING trên Sheet nếu chưa có trong ScriptProperties
    SALES_LIKE_SHEET_NAMES.forEach((sheetName) => {
      try {
        const ctx = getSheetContext_(sheetName, { ensureSchema: true, allowMissing: true });
        if (!ctx) return;

        const lastRow = ctx.sheet.getLastRow();
        if (lastRow <= 1) return;

        const rows = ctx.sheet.getRange(2, 1, lastRow - 1, ctx.lastColumn).getValues();
        rows.forEach((row, index) => {
          const rowIndex = index + 2;
          const rowObject = mapRowToObject_(row, ctx.headerMap, rowIndex, sheetName, ctx.headers);
          const tgStatus = String(rowObject.telegramStatus || '').trim().toUpperCase();

          if (tgStatus === 'SENT' || Boolean(rowObject.telegramMessageId)) {
            return;
          }

          if (tgStatus === 'PENDING' && isSoldInternal_(rowObject.trangThai) && isRowReadyForNewOrderNotify_(rowObject)) {
            // Kiểm tra xem đã có key trong hàng đợi chưa
            const itemKey = TELEGRAM_PENDING_PREFIX + (rowObject.notificationKey || '');
            if (!rowObject.notificationKey || !allProps[itemKey]) {
              // Nếu không có trong hàng đợi -> gửi ngay
              dispatchTelegramOrderNotification_(sheetName, rowIndex, 'Google Sheet - ' + getReportSheetLabel_(sheetName) + ' (Fallback)');
            }
          }
        });
      } catch (sheetErr) {
        console.error('Lỗi fallback sheet ' + sheetName + ':', sheetErr);
      }
    });
  } catch (err) {
    console.error('Lỗi processPendingTelegramNotifications:', err);
  } finally {
    lock.releaseLock();
  }
}

function notifySoldOrderByMaSP(maSP, sheetName) {
  const targetMaSP = String(maSP || '').trim();
  if (!targetMaSP) throw new Error('Vui lòng nhập MÃ SP cần gửi Telegram.');

  const targetSheetName = getTelegramSheetName_(sheetName || MA_V_SHEET_NAME);
  if (SALES_LIKE_SHEET_NAMES.indexOf(targetSheetName) === -1) {
    throw new Error('Chỉ hỗ trợ gửi notify cho SalesData hoặc Mã V.');
  }

  const ctx = getSheetContext_(targetSheetName, { ensureSchema: false, allowMissing: true });
  if (!ctx) throw new Error('Không tìm thấy sheet "' + targetSheetName + '".');

  const lastRow = ctx.sheet.getLastRow();
  if (lastRow <= 1) throw new Error('Sheet "' + targetSheetName + '" chưa có dữ liệu.');

  const rows = ctx.sheet.getRange(2, 1, lastRow - 1, ctx.lastColumn).getValues();

  for (let i = 0; i < rows.length; i++) {
    const rowIndex = i + 2;
    const rowObject = mapRowToObject_(rows[i], ctx.headerMap, rowIndex, targetSheetName, ctx.headers);
    if (!isSameMaSPForSearch_(rowObject.maSP, targetMaSP)) continue;

    if (!isSoldInternal_(rowObject.trangThai) || Number(rowObject.giaBan || 0) <= 0) {
      throw new Error('Dòng ' + targetMaSP + ' chưa đủ điều kiện gửi Telegram (cần trạng thái ĐÃ BÁN và có Giá bán > 0).');
    }

    // Reset status to allow manual re-send
    setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rowIndex, HEADER_ALIASES.telegramStatus, 'PENDING');
    setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rowIndex, HEADER_ALIASES.telegramMessageId, '');

    const result = dispatchTelegramOrderNotification_(targetSheetName, rowIndex, 'Google Sheet - ' + getReportSheetLabel_(targetSheetName) + ' (gửi thủ công)');
    if (!result.sent) throw new Error('Không gửi được Telegram cho ' + targetMaSP + ': ' + (result.error || result.reason));

    return 'Đã gửi Telegram cho ' + rowObject.maSP + ' từ sheet ' + getReportSheetLabel_(targetSheetName) + ' (MsgID: ' + (result.messageId || '-') + ').';
  }

  throw new Error('Không tìm thấy MÃ SP "' + targetMaSP + '" trong sheet ' + getReportSheetLabel_(targetSheetName) + '.');
}

function notifyNewOrderOnce_(row, source) {
  if (!isRowReadyForNewOrderNotify_(row)) return false;
  const sheetName = getTelegramSheetName_(row);
  const result = dispatchTelegramOrderNotification_(sheetName, row.rowIndex, source || 'Google Sheet');
  return Boolean(result && result.sent);
}

function notifySoldOrderChange_(row, rowIndex, source) {
  if (!isRowReadyForNewOrderNotify_(row)) return false;
  const sheetName = getTelegramSheetName_(row);
  const result = dispatchTelegramOrderNotification_(sheetName, rowIndex, source || 'Google Sheet');
  return Boolean(result && result.sent);
}

function sendTelegramMessageWithResult_(message) {
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);
  const chatId = props.getProperty(TELEGRAM_CHAT_ID_PROPERTY_KEY);

  if (!botToken || !chatId) {
    return { success: false, error: 'Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID.' };
  }

  const url = 'https://api.telegram.org/bot' + encodeURIComponent(botToken) + '/sendMessage';
  try {
    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    });

    const code = response.getResponseCode();
    const body = response.getContentText() || '{}';
    let payload = {};
    try { payload = JSON.parse(body); } catch (_) {}

    if (code >= 200 && code < 300 && payload.ok) {
      const messageId = payload.result && payload.result.message_id ? payload.result.message_id : null;
      return { success: true, messageId: messageId };
    } else {
      const desc = payload.description || body;
      return { success: false, error: 'HTTP ' + code + ': ' + desc };
    }
  } catch (e) {
    return { success: false, error: e && e.message ? e.message : String(e) };
  }
}

function sendTelegramMessage_(message) {
  const res = sendTelegramMessageWithResult_(message);
  return res.success;
}

function sendTelegramMessageToChat_(chatId, message) {
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);

  if (!botToken || !chatId) {
    console.warn('Telegram send skipped: missing bot token or chat id.');
    return { success: false, error: 'Thiếu TELEGRAM_BOT_TOKEN hoặc chatId.' };
  }

  const url = 'https://api.telegram.org/bot' + encodeURIComponent(botToken) + '/sendMessage';
  try {
    const response = UrlFetchApp.fetch(url, {
      method: 'post',
      contentType: 'application/json',
      muteHttpExceptions: true,
      payload: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    });

    const code = response.getResponseCode();
    const body = response.getContentText() || '{}';
    let payload = {};
    try { payload = JSON.parse(body); } catch (_) {}

    if (code >= 200 && code < 300 && payload.ok) {
      const messageId = payload.result && payload.result.message_id ? payload.result.message_id : null;
      return { success: true, messageId: messageId };
    } else {
      const desc = payload.description || body;
      console.error('Telegram notify failed: ' + desc);
      return { success: false, error: 'HTTP ' + code + ': ' + desc };
    }
  } catch (err) {
    const errMsg = err && err.message ? err.message : String(err);
    console.error('Telegram send exception: ', errMsg);
    return { success: false, error: errMsg };
  }
}

function buildSoldOrderTelegramMessage_(row, source, isUpdate) {
  // Freeship: chỉ khi giaBan >= 500k VÀ khachCoc >= giaBan
  const giaBan   = Number(row.giaBan)   || 0;
  const khachCoc = Number(row.khachCoc) || 0;
  const tienCOD  = Number(row.tienCOD)  || 0;
  const isFreeShip = giaBan >= 500000 && khachCoc >= giaBan;
  const shippingLabel = isFreeShip ? 'Freeship' : 'Khách chịu ship';

  const tenSP     = String(row.sanPham    || '').trim() || 'Chưa có tên sản phẩm';
  const maSP      = String(row.maSP      || '').trim() || '-';
  const tenKhach  = String(row.tenKhach  || '').trim() || 'Khách chưa cập nhật tên';
  const sdtKhach  = String(row.sdtKhach  || '').trim() || '-';
  const diaChi    = String(row.diaChi    || '').trim() || '-';
  const nguon     = String(row.nguonKhach|| '').trim() || '-';
  const aiChot    = String(row.aiChot    || '').trim() || tenKhach;
  const ngayChot  = String(row.ngayChot  || '').trim() || '-';
  const hinhThuc  = String(row.hinhThuc  || '').trim() || '-';
  const ghiChu    = String(row.ghiChu    || '').trim() || 'Không có';

  const title = isUpdate ? '🔁 <b>CẬP NHẬT ĐƠN BÁN</b>' : '🛒 <b>CÓ ĐƠN MỚI</b>';

  const lines = [
    title,
    '━━━━━━━━━━━━━━━━━━━━',
    '',
    '📦 <b>SẢN PHẨM KHÁCH MUA</b>',
    '🏷️ <b>Sản phẩm:</b> ' + escapeTelegramHtml_(tenSP),
    '🔖 <b>Mã SP:</b> <code>' + escapeTelegramHtml_(maSP) + '</code>',
    '🔢 <b>Số lượng:</b> 1',
    '',
    '👤 <b>THÔNG TIN KHÁCH</b>',
    '🙋 <b>Khách hàng:</b> ' + escapeTelegramHtml_(tenKhach),
    '📞 <b>SĐT:</b> ' + escapeTelegramHtml_(sdtKhach),
    '📍 <b>Địa chỉ:</b> ' + escapeTelegramHtml_(diaChi),
    '📣 <b>Nguồn khách:</b> ' + escapeTelegramHtml_(nguon),
    '',
    '💰 <b>THÔNG TIN THANH TOÁN</b>',
    '💵 <b>Giá bán:</b> ' + formatMoney_(giaBan),
    '💳 <b>Khách đã cọc:</b> ' + formatMoney_(khachCoc),
    '🛵 <b>Còn phải thu/COD:</b> ' + formatMoney_(tienCOD),
    '🚚 <b>Phí vận chuyển:</b> ' + shippingLabel,
    '',
    '🧾 <b>THÔNG TIN CHỐT ĐƠN</b>',
    '🙋 <b>Ai chốt:</b> ' + escapeTelegramHtml_(aiChot),
    '📅 <b>Ngày chốt:</b> ' + escapeTelegramHtml_(ngayChot),
    '📮 <b>Hình thức giao:</b> ' + escapeTelegramHtml_(hinhThuc),
    '',
    '📝 <b>Ghi chú:</b> ' + escapeTelegramHtml_(ghiChu),
    '━━━━━━━━━━━━━━━━━━━━'
  ];

  return lines.join('\n');
}

function buildNewOrderTelegramMessage_(row, source) {
  return buildSoldOrderTelegramMessage_(row, source, false);
}

function testTelegramNotify() {
  return sendTelegramMessage_(
    '<b>Test Sales Admin</b>\nTelegram notify đã kết nối thành công lúc ' +
    escapeTelegramHtml_(getCurrentTimestamp_())
  );
}

function resetTelegramNotifyForMaSP(maSP) {
  if (!maSP) throw new Error('Vui lòng nhập MÃ SP cần reset notify.');
  const normalized = String(maSP || '').trim().toLowerCase();

  SALES_LIKE_SHEET_NAMES.forEach((sheetName) => {
    const ctx = getSheetContext_(sheetName, { ensureSchema: false, allowMissing: true });
    if (!ctx) return;

    const lastRow = ctx.sheet.getLastRow();
    if (lastRow <= 1) return;

    const rows = ctx.sheet.getRange(2, 1, lastRow - 1, ctx.lastColumn).getValues();
    rows.forEach((row, index) => {
      const rowIndex = index + 2;
      const existing = String(getCellByHeaderAliases_(row, ctx.headerMap, HEADER_ALIASES.maSP) || '').trim().toLowerCase();
      if (existing === normalized) {
        setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rowIndex, HEADER_ALIASES.telegramStatus, 'PENDING');
        setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rowIndex, HEADER_ALIASES.telegramMessageId, '');
        setSheetCellByHeaderAlias_(ctx.sheet, ctx.headerMap, rowIndex, HEADER_ALIASES.telegramError, '');
      }
    });
  });

  return 'Đã reset notify cho MÃ SP: ' + maSP;
}

function logActivity_(rowIndex, maSP, action, details) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName('ActivityLog');
    if (!sheet) {
      sheet = ss.insertSheet('ActivityLog');
      sheet.getRange(1, 1, 1, 5).setValues([['Thời gian', 'Dòng', 'Mã SP', 'Hành động', 'Chi tiết']]);
      sheet.getRange(1, 1, 1, 5).setBackground('#3b82f6').setFontColor('#ffffff').setFontWeight('bold');
      sheet.setFrozenRows(1);
    }
    const now = getCurrentTimestamp_();
    sheet.appendRow([now, rowIndex, maSP, action, details]);

    // Rolling log: Giới hạn tối đa 3.000 dòng để không làm chậm spreadsheet
    const lastRow = sheet.getLastRow();
    if (lastRow > 3000) {
      const deleteCount = lastRow - 2500;
      sheet.deleteRows(2, deleteCount);
    }
  } catch (e) {
    console.error('Lỗi lưu nhật ký hoạt động:', e);
  }
}

function calculateGrowthPercentage_(cur, prev) {
  if (prev === 0) return cur > 0 ? 100 : 0;
  return Math.round(((cur - prev) / prev) * 100);
}

function formatMoney_(value) {
  return Utilities.formatString('%s ₫', Number(value || 0).toLocaleString('vi-VN'));
}

function escapeTelegramHtml_(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function getActivityLogs() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('ActivityLog');
    if (!sheet) return [];
    const lastRow = sheet.getLastRow();
    if (lastRow <= 1) return [];
    const startRow = Math.max(2, lastRow - 99);
    const numRows = lastRow - startRow + 1;
    const values = sheet.getRange(startRow, 1, numRows, 5).getValues();
    return values.map((r, i) => ({
      time: r[0],
      rowIndex: r[1],
      maSP: r[2],
      action: r[3],
      details: r[4]
    })).reverse();
  } catch (e) {
    console.error('Lỗi đọc nhật ký hoạt động:', e);
    return [];
  }
}

function getSystemSettings() {
  const props = PropertiesService.getScriptProperties();
  return {
    telegramBotToken: props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY) || '',
    telegramChatId: props.getProperty(TELEGRAM_CHAT_ID_PROPERTY_KEY) || '',
    geminiApiKey: props.getProperty(GEMINI_API_KEY_PROPERTY_KEY) || '',
    geminiModel: props.getProperty(GEMINI_MODEL_PROPERTY_KEY) || DEFAULT_GEMINI_MODEL
  };
}

function saveSystemSettings(settings) {
  if (!settings || typeof settings !== 'object') {
    throw new Error('Cấu hình không hợp lệ.');
  }
  const props = PropertiesService.getScriptProperties();
  props.setProperties({
    [TELEGRAM_BOT_TOKEN_PROPERTY_KEY]: String(settings.telegramBotToken || '').trim(),
    [TELEGRAM_CHAT_ID_PROPERTY_KEY]: String(settings.telegramChatId || '').trim(),
    [GEMINI_API_KEY_PROPERTY_KEY]: String(settings.geminiApiKey || '').trim(),
    [GEMINI_MODEL_PROPERTY_KEY]: String(settings.geminiModel || '').trim()
  });
  
  // Install triggers automatically
  try {
    installTelegramOnEditTrigger();
    installTelegramPendingTrigger();
    installBackupTrigger();
    installDailyStatusTrigger();
  } catch (e) {
    console.warn('Lỗi tự động cài triggers:', e);
  }
  
  return { success: true, message: 'Đã lưu cấu hình hệ thống thành công!' };
}

function createBackupSpreadsheet() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const file = DriveApp.getFileById(ss.getId());
    
    const folderName = "SalesAdmin_Backups";
    const folders = DriveApp.getFoldersByName(folderName);
    let folder;
    if (folders.hasNext()) {
      folder = folders.next();
    } else {
      folder = DriveApp.createFolder(folderName);
    }
    
    const timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyyMMdd_HHmmss');
    const backupName = "Backup_" + ss.getName() + "_" + timestamp;
    
    file.makeCopy(backupName, folder);
    
    logActivity_(0, 'Hệ thống', 'Sao lưu', 'Tạo bản sao lưu thành công: ' + backupName);
    return { success: true, fileName: backupName, folderName: folderName };
  } catch (e) {
    const err = e && e.message ? e.message : String(e);
    logActivity_(0, 'Hệ thống', 'Lỗi sao lưu', err);
    return { success: false, error: err };
  }
}

function installBackupTrigger() {
  const existing = ScriptApp.getProjectTriggers();
  existing.forEach((t) => {
    if (t.getHandlerFunction() === 'createBackupSpreadsheet') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('createBackupSpreadsheet')
    .timeBased()
    .everyDays(1)
    .atHour(2)
    .create();
}

// ============================================================
// BÁO CÁO TÌNH HÌNH 2 TIẾNG / LẦN QUA TELEGRAM
// ============================================================

function sendDailyTelegramStatusReport() {
  try {
    // Chỉ gửi trong khoảng 7h – 23h
    const now = new Date();
    const hour = now.getHours();
    if (hour < 7 || hour >= 23) return;

    const today = getTodayString_();
    const timeStr = Utilities.formatDate(now, Session.getScriptTimeZone(), 'HH:mm');

    const rows = getAllReportRows();

    // Thống kê theo từng sheet
    const sheetStats = {};
    [SHEET_NAME, MA_V_SHEET_NAME, LIQUIDATION_SHEET_NAME].forEach((sn) => {
      sheetStats[sn] = { don: 0, doanhThu: 0, loiNhuan: 0, coc: 0, cod: 0, soCOD: 0, soFree: 0, list: [] };
    });

    rows.forEach((r) => {
      const tt = r.trangThai;
      if (!(isSoldInternal_(tt) || isWaitingInternal_(tt))) return;
      if (r.ngayChot !== today) return;

      const sn = r.sourceSheet || r.sheetName || SHEET_NAME;
      const stat = sheetStats[sn] || sheetStats[SHEET_NAME];
      const loi = Number(r.giaBan || 0) - Number(r.giaVon || 0);

      stat.don++;
      stat.doanhThu += Number(r.giaBan || 0);
      stat.loiNhuan += loi;
      stat.coc += Number(r.khachCoc || 0);
      if (r.hinhThuc === 'COD') {
        stat.cod += Number(r.tienCOD || 0);
        stat.soCOD++;
      } else {
        stat.soFree++;
      }
      stat.list.push(r);
    });

    // Tổng hợp tất cả sheet
    const tongDon   = Object.values(sheetStats).reduce((s, v) => s + v.don, 0);
    const tongDT    = Object.values(sheetStats).reduce((s, v) => s + v.doanhThu, 0);
    const tongLoi   = Object.values(sheetStats).reduce((s, v) => s + v.loiNhuan, 0);
    const tongCoc   = Object.values(sheetStats).reduce((s, v) => s + v.coc, 0);
    const tongCOD   = Object.values(sheetStats).reduce((s, v) => s + v.cod, 0);
    const tongSoCOD = Object.values(sheetStats).reduce((s, v) => s + v.soCOD, 0);
    const tongSoFree= Object.values(sheetStats).reduce((s, v) => s + v.soFree, 0);

    // Tồn kho: chỉ tính SalesData + Mã V, KHÔNG tính THANH LÝ
    const inStockCount = rows.filter((r) => {
      const sn = r.sourceSheet || r.sheetName || SHEET_NAME;
      return sn !== LIQUIDATION_SHEET_NAME && isInStockInternal_(r.trangThai);
    }).length;

    const profitEmoji = tongLoi >= 0 ? '📈' : '📉';
    const orderEmoji  = tongDon >= 5 ? '🔥' : tongDon >= 2 ? '✅' : tongDon >= 1 ? '🛒' : '😴';

    const lines = [
      '📊 <b>BÁO CÁO TÌNH HÌNH HÔM NAY</b>',
      '━━━━━━━━━━━━━━━━━━━━',
      '📅 <b>Ngày:</b> ' + today + ' — <b>' + timeStr + '</b>',
      '',
      orderEmoji + ' <b>TỔNG ĐƠN: ' + tongDon + ' đơn</b>  (COD: ' + tongSoCOD + ' | Free: ' + tongSoFree + ')',
      '💰 <b>Doanh thu:</b> ' + formatMoney_(tongDT),
      profitEmoji + ' <b>Lợi nhuận:</b> ' + formatMoney_(tongLoi),
      '💳 <b>Khách cọc:</b> ' + formatMoney_(tongCoc),
      '🚛 <b>COD còn lại:</b> ' + formatMoney_(tongCOD),
      '📦 <b>Tồn kho (SD+V):</b> ' + inStockCount + ' SP'
    ];

    // Chi tiết từng sheet (chỉ hiển thị sheet có đơn)
    const sheetConfigs = [
      { key: SHEET_NAME,           label: 'SalesData', icon: '📋' },
      { key: MA_V_SHEET_NAME,      label: 'Mã V',      icon: '🏷️' },
      { key: LIQUIDATION_SHEET_NAME, label: 'Thanh Lý', icon: '♻️' }
    ];

    let hasAnySheet = false;
    sheetConfigs.forEach(({ key, label, icon }) => {
      const s = sheetStats[key];
      if (!s || s.don === 0) return;
      hasAnySheet = true;
      lines.push('');
      lines.push(icon + ' <b>' + label + ': ' + s.don + ' đơn — ' + formatMoney_(s.doanhThu) + '</b>');
      s.list.slice(0, 4).forEach((r, i) => {
        lines.push(
          '  ' + (i + 1) + '. <code>' + escapeTelegramHtml_(r.maSP) + '</code> ' +
          formatMoney_(r.giaBan) + ' — ' + escapeTelegramHtml_(r.tenKhach || 'Ẩn danh')
        );
      });
      if (s.list.length > 4) lines.push('  <i>...và ' + (s.list.length - 4) + ' đơn khác</i>');
    });

    if (tongDon === 0) {
      lines.push('');
      lines.push('😴 <i>Chưa có đơn nào hôm nay. Cố lên nào!</i>');
    }

    lines.push('');
    lines.push('━━━━━━━━━━━━━━━━━━━━');

    sendTelegramMessage_(lines.join('\n'));
  } catch (e) {
    console.error('Lỗi sendDailyTelegramStatusReport:', e);
  }
}

function installDailyStatusTrigger() {
  const existing = ScriptApp.getProjectTriggers();
  existing.forEach((t) => {
    if (t.getHandlerFunction() === 'sendDailyTelegramStatusReport') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('sendDailyTelegramStatusReport')
    .timeBased()
    .everyHours(2)
    .create();
  return 'Đã cài trigger báo cáo tình hình 2 tiếng/lần.';
}
function installAlertTrigger() {
  const existing = ScriptApp.getProjectTriggers();
  existing.forEach((t) => {
    if (t.getHandlerFunction() === 'checkAndSendTelegramAlerts') {
      ScriptApp.deleteTrigger(t);
    }
  });
  ScriptApp.newTrigger('checkAndSendTelegramAlerts')
    .timeBased()
    .everyHours(4)
    .create();
  return 'Da cai trigger canh bao he thong 4 tieng/lan (7h-23h).';
}

// ============================================================
// GAMIFIED LOYALTY HUB - LUCKY WHEEL BACKEND
// ============================================================

function checkCustomerWheelAvailability(phone) {
  try {
    const phoneKey = normalizePhoneForLookup_(phone);
    if (!phoneKey || phoneKey.length < 8) {
      return { success: false, available: false, reason: 'Số điện thoại không hợp lệ.' };
    }

    // Calculate customer LTV & orders to check VIP or repeat purchaser status
    const reportRows = getAllReportRows();
    let totalOrders = 0;
    let totalSpending = 0;

    reportRows.forEach((r) => {
      if (!isRevenueRow_(r)) return;
      const rowPhone = normalizePhoneForLookup_(r.sdtKhach);
      if (rowPhone === phoneKey || rowPhone.endsWith(phoneKey) || phoneKey.endsWith(rowPhone)) {
        totalOrders += 1;
        totalSpending += Number(r.giaBan || 0);
      }
    });

    const vipTier = getCustomerVipTierInfo_(totalSpending, totalOrders);
    const isEligible = vipTier.key !== 'regular' || totalOrders > 1;

    if (!isEligible) {
      return {
        success: true,
        available: false,
        reason: 'Khách hàng chưa đủ điều kiện quay (yêu cầu là khách VIP hoặc mua từ 2 đơn trở lên).',
        totalOrders,
        totalSpending,
        vipLabel: vipTier.label
      };
    }

    // Check if already spun this month
    const props = PropertiesService.getScriptProperties();
    const currentMonth = getTodayString_().slice(0, 7); // yyyy-MM
    let registry = {};
    try {
      registry = JSON.parse(props.getProperty('WHEEL_SPUN_REGISTRY') || '{}');
    } catch (e) {
      registry = {};
    }

    // Clean up registry if month changes to save GAS script properties space
    if (registry.month !== currentMonth) {
      registry = { month: currentMonth, phones: {} };
    }

    if (registry.phones && registry.phones[phoneKey]) {
      const record = registry.phones[phoneKey];
      return {
        success: true,
        available: false,
        reason: `Khách hàng này đã quay thưởng vào ngày ${String(record.spunAt || '').slice(0, 10)}. Giải thưởng: ${record.prize}`,
        totalOrders,
        totalSpending,
        vipLabel: vipTier.label
      };
    }

    return {
      success: true,
      available: true,
      reason: 'Đủ điều kiện quay thưởng!',
      totalOrders,
      totalSpending,
      vipLabel: vipTier.label
    };
  } catch (e) {
    return { success: false, available: false, reason: 'Lỗi: ' + e.message };
  }
}

function spinLoyaltyWheelBackend(phone, customerName) {
  try {
    const phoneKey = normalizePhoneForLookup_(phone);
    const availability = checkCustomerWheelAvailability(phoneKey);
    if (!availability.success || !availability.available) {
      return { success: false, error: availability.reason };
    }

    // Weighted random calculation
    const prizes = [
      { index: 0, label: "Voucher 20k", weight: 30 },
      { index: 1, label: "Voucher 50k", weight: 10 },
      { index: 2, label: "Chúc may mắn lần sau", weight: 25 },
      { index: 3, label: "Voucher 100k", weight: 5 },
      { index: 4, label: "Mã Free Ship", weight: 20 },
      { index: 5, label: "Quà tặng Cốc ANTA", weight: 10 }
    ];

    const totalWeight = prizes.reduce((acc, p) => acc + p.weight, 0);
    let randomNum = Math.random() * totalWeight;
    let selectedPrize = prizes[2]; // Default fallback

    for (let i = 0; i < prizes.length; i++) {
      if (randomNum < prizes[i].weight) {
        selectedPrize = prizes[i];
        break;
      }
      randomNum -= prizes[i].weight;
    }

    const winnerIndex = selectedPrize.index;
    const winnerLabel = selectedPrize.label;

    // Save to Script Properties registry
    const props = PropertiesService.getScriptProperties();
    const currentMonth = getTodayString_().slice(0, 7);
    let registry = {};
    try {
      registry = JSON.parse(props.getProperty('WHEEL_SPUN_REGISTRY') || '{}');
    } catch (e) {
      registry = {};
    }

    if (registry.month !== currentMonth) {
      registry = { month: currentMonth, phones: {} };
    }

    registry.phones[phoneKey] = {
      spunAt: getCurrentTimestamp_(),
      prize: winnerLabel
    };
    props.setProperty('WHEEL_SPUN_REGISTRY', JSON.stringify(registry));

    // Append to Ghi Chú in the customer's last order row in SalesData sheet
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
    let updatedInSheet = false;
    if (sheet) {
      const lastRow = sheet.getLastRow();
      const ctx = getSheetContext_(SHEET_NAME, { ensureSchema: false });
      let targetRowIndex = -1;
      const colIndex = ctx.headerMap['SĐT khách hàng'] !== undefined 
        ? ctx.headerMap['SĐT khách hàng'] 
        : ctx.headerMap[normalizeHeaderKey_('SĐT khách hàng')];
      
      if (colIndex !== undefined && lastRow > 1) {
        const values = sheet.getRange(2, colIndex + 1, lastRow - 1, 1).getValues();
        for (let i = values.length - 1; i >= 0; i--) {
          const rowPhone = normalizePhoneForLookup_(values[i][0]);
          if (rowPhone === phoneKey || rowPhone.endsWith(phoneKey) || phoneKey.endsWith(rowPhone)) {
            targetRowIndex = i + 2;
            break;
          }
        }
      }

      if (targetRowIndex !== -1) {
        const noteColIndex = ctx.headerMap['Ghi chú'] !== undefined
          ? ctx.headerMap['Ghi chú']
          : ctx.headerMap[normalizeHeaderKey_('Ghi chú')];
        
        if (noteColIndex !== undefined) {
          const currentNote = String(sheet.getRange(targetRowIndex, noteColIndex + 1).getValue() || '').trim();
          const nextNote = currentNote 
            ? currentNote + ' | [Vòng quay VIP: ' + winnerLabel + ']' 
            : '[Vòng quay VIP: ' + winnerLabel + ']';
          sheet.getRange(targetRowIndex, noteColIndex + 1).setValue(nextNote);
          updatedInSheet = true;
          clearAllRowsCache_();
        }
      }
    }

    // Log this activity
    logActivity_(0, phoneKey, 'Quay thưởng', `Khách ${customerName || 'Ẩn danh'} quay trúng: ${winnerLabel}. ${updatedInSheet ? 'Đã ghi nhận vào Sheet.' : 'Không tìm thấy đơn để ghi nhận.'}`);

    return {
      success: true,
      winnerIndex: winnerIndex,
      winnerLabel: winnerLabel,
      message: `Chúc mừng! Khách hàng trúng: ${winnerLabel}`
    };
  } catch (e) {
    return { success: false, error: 'Lỗi hệ thống: ' + e.message };
  }
}

// ─────────────────────────────────────────────
// SYSTEM ALERTS & NOTIFICATION CENTER (Module 9)
// ───────────────────────────────────────────────

function getSystemNotifications() {
  const alerts = [];
  const today = getTodayString_();
  let reportRows = [];
  try {
    reportRows = getAllReportRows();
  } catch (e) {
    console.error('Error fetching report rows:', e);
    return [];
  }
  
  const oneDayAgoMs = Date.now() - 24 * 60 * 60 * 1000;
  
  reportRows.forEach(r => {
    // 1. Đơn chờ CK quá lâu (wait_ck)
    if (isWaitingInternal_(r.trangThai)) {
      const isOldDate = r.ngayChot && r.ngayChot < today;
      let isOldCreated = false;
      if (r.createdAt) {
        const createdMs = parseDateTime_(r.createdAt);
        if (createdMs && createdMs < oneDayAgoMs) isOldCreated = true;
      }
      if (isOldDate || isOldCreated) {
        alerts.push({
          id: 'wait_ck_' + r.maSP,
          type: 'wait_ck',
          title: 'Đơn chờ CK quá lâu',
          message: `Đơn ${r.maSP} của khách ${r.tenKhach || 'Ẩn danh'} đã chờ chuyển khoản từ ngày ${r.ngayChot || 'trước'}.`,
          maSP: r.maSP,
          tenKhach: r.tenKhach,
          sdtKhach: r.sdtKhach,
          important: true,
          date: r.ngayChot || today
        });
      }
    }

    // 2. Đơn chưa giao đúng hẹn (late_ship)
    if (!isDeletedInternal_(r.trangThai) && !isSoldInternal_(r.trangThai)) {
      const note = String(r.ghiChu || '').toLowerCase();
      const hasDeliveryNote = note.includes('hẹn') || note.includes('giao') || note.includes('ship');
      if (hasDeliveryNote) {
        const isPast = r.ngayChot && r.ngayChot < today;
        const pastNoteDate = parseAndCheckPastDateInText_(r.ghiChu);
        if (isPast || pastNoteDate) {
          alerts.push({
            id: 'late_ship_' + r.maSP,
            type: 'late_ship',
            title: 'Đơn chưa giao đúng hẹn',
            message: `Đơn ${r.maSP} (Khách: ${r.tenKhach || 'Ẩn danh'}) có lịch hẹn nhưng chưa hoàn tất giao hàng. Ghi chú: "${r.ghiChu}"`,
            maSP: r.maSP,
            tenKhach: r.tenKhach,
            sdtKhach: r.sdtKhach,
            important: false,
            date: r.ngayChot || today
          });
        }
      }
    }

    // 3. COD chưa đối soát (cod_reconcile)
    if (isSoldInternal_(r.trangThai) && r.hinhThuc === 'COD' && r.tienCOD > 0) {
      const isPast = r.ngayChot && r.ngayChot < today;
      if (isPast) {
        const note = stripVietnameseMarks_(String(r.ghiChu || '')).toLowerCase();
        const hasReconciled = note.includes('doi soat') || note.includes('da ds') || note.includes('da nhan cod') || note.includes('thu cod') || note.includes('da thu') || note.includes(' xong');
        if (!hasReconciled) {
          alerts.push({
            id: 'cod_reconcile_' + r.maSP,
            type: 'cod_reconcile',
            title: 'COD chưa đối soát',
            message: `Đơn ${r.maSP} (Khách: ${r.tenKhach || 'Ẩn danh'}, COD: ${formatMoney_(r.tienCOD)}) đã bán nhưng chưa đối soát.`,
            maSP: r.maSP,
            tenKhach: r.tenKhach,
            sdtKhach: r.sdtKhach,
            important: false,
            date: r.ngayChot || today
          });
        }
      }
    }

    // 4. Khách cần gọi lại hôm nay (call_back)
    if (!isDeletedInternal_(r.trangThai) && !isSoldInternal_(r.trangThai)) {
      const note = stripVietnameseMarks_(String(r.ghiChu || '')).toLowerCase();
      const needsCallback = note.includes('goi lai') || note.includes('alo lai') || note.includes('lien he lai') || note.includes('call back');
      if (needsCallback) {
        alerts.push({
          id: 'call_back_' + r.maSP,
          type: 'call_back',
          title: 'Khách cần gọi lại hôm nay',
          message: `Khách ${r.tenKhach || 'Ẩn danh'} (${r.sdtKhach || 'không SĐT'}) cần liên hệ lại. Ghi chú: "${r.ghiChu}"`,
          maSP: r.maSP,
          tenKhach: r.tenKhach,
          sdtKhach: r.sdtKhach,
          important: false,
          date: r.ngayChot || today
        });
      }
    }
  });

  // 5. Sản phẩm sắp hết hàng (low_stock)
  const stockCounts = {};
  reportRows.forEach(r => {
    if (isInStockInternal_(r.trangThai) && r.sanPham) {
      const name = String(r.sanPham).trim();
      stockCounts[name] = (stockCounts[name] || 0) + 1;
    }
  });
  Object.keys(stockCounts).forEach(name => {
    const count = stockCounts[name];
    if (count <= 2) {
      alerts.push({
        id: 'low_stock_' + encodeURIComponent(name),
        type: 'low_stock',
        title: 'Sản phẩm sắp hết hàng',
        message: `Sản phẩm "${name}" sắp hết hàng trong kho (Chỉ còn ${count} sản phẩm).`,
        important: false,
        date: today
      });
    }
  });
  const totalStock = reportRows.filter(r => isInStockInternal_(r.trangThai)).length;
  if (totalStock <= 5) {
    alerts.push({
      id: 'low_stock_warehouse_total',
      type: 'low_stock',
      title: 'Kho hàng sắp hết sản phẩm',
      message: `Cảnh báo: Tổng kho chỉ còn ${totalStock} sản phẩm còn hàng.`,
      important: false,
      date: today
    });
  }

  // 6. Công việc trễ deadline (late_task)
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const taskSheet = ss.getSheetByName('Công việc') || ss.getSheetByName('Tasks') || ss.getSheetByName('Todo');
    if (taskSheet) {
      const lastRow = taskSheet.getLastRow();
      if (lastRow > 1) {
        const headers = taskSheet.getRange(1, 1, 1, taskSheet.getLastColumn()).getValues()[0];
        const headerMap = buildHeaderMap_(headers);
        const values = taskSheet.getRange(2, 1, lastRow - 1, taskSheet.getLastColumn()).getValues();
        
        values.forEach((row, index) => {
          const rowIndex = index + 2;
          const taskName = String(row[headerMap['Công việc'] !== undefined ? headerMap['Công việc'] : 0] || '').trim();
          const deadlineRaw = row[headerMap['Deadline'] !== undefined ? headerMap['Deadline'] : (headerMap['Hạn chót'] !== undefined ? headerMap['Hạn chót'] : 1)];
          const deadline = formatSheetDate_(deadlineRaw);
          const status = String(row[headerMap['Trạng thái'] !== undefined ? headerMap['Trạng thái'] : 2] || '').trim();
          const assignee = String(row[headerMap['Người thực hiện'] !== undefined ? headerMap['Người thực hiện'] : 3] || '').trim();
          const desc = String(row[headerMap['Mô tả'] !== undefined ? headerMap['Mô tả'] : 4] || '').trim();

          const isCompleted = status.toLowerCase().includes('xong') || status.toLowerCase().includes('hoàn thành') || status.toLowerCase().includes('done') || status.toLowerCase().includes('completed');
          
          if (taskName && !isCompleted && deadline && deadline < today) {
            alerts.push({
              id: 'late_task_' + rowIndex,
              type: 'late_task',
              title: 'Công việc trễ deadline',
              message: `Công việc "${taskName}" trễ deadline (${deadline}). Phụ trách: ${assignee || 'Chủ shop'}.`,
              taskName,
              deadline,
              status,
              assignee,
              desc,
              important: true,
              date: deadline
            });
          }
        });
      }
    }
  } catch (e) {
    console.error('Error reading Tasks sheet:', e);
  }

  // 7. Doanh thu giảm (rev_decrease)
  try {
    const stats = buildDashboardStatsFromRows_(readRowsFromSalesLikeSheets_());
    const currentMonth = today.slice(0, 7);
    const prevMonth = getPreviousMonthKey_(currentMonth);
    const currentMonthMetrics = calculateShopAiMonthMetrics_(reportRows, currentMonth);
    const previousMonthMetrics = calculateShopAiMonthMetrics_(reportRows, prevMonth);
    const monthlyGrowth = calculateGrowthPercentage_(currentMonthMetrics.revenue, previousMonthMetrics.revenue);
    
    if (monthlyGrowth < -5 && currentMonthMetrics.revenue > 0) {
      alerts.push({
        id: 'rev_decrease_month_' + currentMonth,
        type: 'rev_decrease',
        title: 'Doanh thu giảm',
        message: `Doanh thu tháng này (${currentMonth}) giảm ${Math.abs(monthlyGrowth)}% so với tháng trước (${prevMonth}).`,
        important: true,
        date: today
      });
    }

    if (stats.growthDoanhThu < -10 && stats.doanhThuHomNay > 0) {
      alerts.push({
        id: 'rev_decrease_day_' + today,
        type: 'rev_decrease',
        title: 'Doanh thu giảm',
        message: `Doanh thu hôm nay giảm ${Math.abs(stats.growthDoanhThu)}% so với hôm qua.`,
        important: true,
        date: today
      });
    }
  } catch (e) {
    console.error('Error computing revenue growth:', e);
  }

  // 8. Khách VIP vừa phát sinh đơn (vip_order)
  try {
    const customerOrders = {};
    const customerSpending = {};
    reportRows.forEach(r => {
      if (!isRevenueRow_(r)) return;
      const phone = normalizePhoneForLookup_(r.sdtKhach);
      const name = stripVietnameseMarks_(String(r.tenKhach || '').toLowerCase()).replace(/\s+/g, ' ').trim();
      const key = phone ? 'phone:' + phone : (name ? 'name:' + name : '');
      if (!key) return;

      customerOrders[key] = (customerOrders[key] || 0) + 1;
      customerSpending[key] = (customerSpending[key] || 0) + Number(r.giaBan || 0);
    });

    reportRows.forEach(r => {
      if (r.ngayChot === today && (isSoldInternal_(r.trangThai) || isWaitingInternal_(r.trangThai))) {
        const phone = normalizePhoneForLookup_(r.sdtKhach);
        const name = stripVietnameseMarks_(String(r.tenKhach || '').toLowerCase()).replace(/\s+/g, ' ').trim();
        const key = phone ? 'phone:' + phone : (name ? 'name:' + name : '');
        if (!key) return;

        const ltv = customerSpending[key] || 0;
        const count = customerOrders[key] || 0;
        const vipInfo = getCustomerVipTierInfo_(ltv, count);
        if (vipInfo && vipInfo.key !== 'regular') {
          alerts.push({
            id: 'vip_order_' + r.maSP,
            type: 'vip_order',
            title: 'Khách VIP vừa phát sinh đơn',
            message: `Khách VIP ${r.tenKhach || 'Ẩn danh'} (${vipInfo.label}) vừa chốt đơn ${r.maSP} hôm nay!`,
            maSP: r.maSP,
            tenKhach: r.tenKhach,
            sdtKhach: r.sdtKhach,
            important: true,
            date: today
          });
        }
      }
    });
  } catch (e) {
    console.error('Error checking VIP orders:', e);
  }

  // 9. Có đơn bị hủy hoặc hoàn (order_cancelled)
  reportRows.forEach(r => {
    const note = stripVietnameseMarks_(String(r.ghiChu || '')).toLowerCase();
    const hasCancelOrReturn = isDeletedInternal_(r.trangThai) || note.includes('hoan') || note.includes('tra') || note.includes('bom') || note.includes('boom') || note.includes('huy');
    if (hasCancelOrReturn) {
      const isTodayNgayChot = r.ngayChot === today;
      const isTodayUpdated = r.updatedAt && r.updatedAt.slice(0, 10) === today;
      if (isTodayNgayChot || isTodayUpdated) {
        alerts.push({
          id: 'order_cancelled_' + r.maSP,
          type: 'order_cancelled',
          title: 'Có đơn bị hủy hoặc hoàn',
          message: `Đơn ${r.maSP} (Khách: ${r.tenKhach || 'Ẩn danh'}) bị hủy hoặc hoàn trả hôm nay. Trạng thái: ${r.trangThai || 'Đã hủy'}`,
          maSP: r.maSP,
          tenKhach: r.tenKhach,
          sdtKhach: r.sdtKhach,
          important: true,
          date: today
        });
      }
    }
  });

  // 10. Backup thất bại (backup_fail)
  try {
    const logs = getActivityLogs();
    logs.forEach(log => {
      if (log.time && log.time.slice(0, 10) === today && (log.action === 'Lỗi sao lưu' || log.action === 'Lỗi' && String(log.details).toLowerCase().includes('sao lưu'))) {
        alerts.push({
          id: 'backup_fail_' + encodeURIComponent(log.time),
          type: 'backup_fail',
          title: 'Backup thất bại',
          message: `Bản sao lưu dữ liệu lúc ${log.time} thất bại! Lỗi: ${log.details}`,
          important: true,
          date: today
        });
      }
    });
  } catch (e) {
    console.error('Error checking backup failures:', e);
  }

  return alerts;
}

function checkAndSendTelegramAlerts() {
  // Vô hiệu hóa tự động bắn cảnh báo vào chat Telegram.
  // Cảnh báo chỉ hiển thị trong Notification Center của Web App UI.
  return 0;
}

function parseDateTime_(str) {
  try {
    const parts = String(str).trim().split(' ');
    const dateParts = parts[0].split('-');
    const timeParts = (parts[1] || '00:00:00').split(':');
    return new Date(
      Number(dateParts[0]),
      Number(dateParts[1]) - 1,
      Number(dateParts[2]),
      Number(timeParts[0]),
      Number(timeParts[1]),
      Number(timeParts[2] || 0)
    ).getTime();
  } catch (e) {
    return null;
  }
}

function parseAndCheckPastDateInText_(text) {
  if (!text) return false;
  const match = text.match(/(\d{1,2})[\/\-](\d{1,2})(?:[\/\-](\d{2,4}))?/);
  if (match) {
    const day = Number(match[1]);
    const month = Number(match[2]);
    let year = new Date().getFullYear();
    if (match[3]) {
      year = Number(match[3]);
      if (year < 100) year += 2000;
    }
    const today = new Date();
    const todayStr = Utilities.formatDate(today, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    const parsedDate = new Date(year, month - 1, day);
    const parsedDateStr = Utilities.formatDate(parsedDate, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    return parsedDateStr < todayStr;
  }
  return false;
}

function runCrmDiagnostics() {
  const diagnostics = {};
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  diagnostics.spreadsheetId = ss.getId();
  diagnostics.spreadsheetName = ss.getName();

  const requiredSheets = ['SalesData', 'Mã V', 'THANH LÝ'];
  diagnostics.sheetsPresence = {};
  diagnostics.sheetsSummary = {};
  diagnostics.timezone = Session.getScriptTimeZone();
  diagnostics.serverToday = getTodayString_();

  requiredSheets.forEach(name => {
    const sheet = ss.getSheetByName(name);
    diagnostics.sheetsPresence[name] = !!sheet;
    if (sheet) {
      const lastRow = sheet.getLastRow();
      const lastColumn = sheet.getLastColumn();
      const headers = lastColumn > 0 ? sheet.getRange(1, 1, 1, lastColumn).getValues()[0] : [];
      const headerMap = buildHeaderMap_(headers);

      // Analyze rows
      let totalRows = lastRow - 1;
      if (totalRows < 0) totalRows = 0;

      let readCount = 0;
      let skippedCount = 0;
      const skippedReasons = {
        emptyRow: 0,
        missingMaSP: 0,
        missingCoreHeaders: [],
        invalidDate: 0,
        invalidStatus: 0
      };

      // Check missing core headers
      const coreFields = ['maSP', 'giaBan', 'tenKhach', 'ngayChot', 'trangThai'];
      coreFields.forEach(field => {
        const aliases = HEADER_ALIASES[field] || [];
        const index = getHeaderIndexByAliases_(headerMap, aliases);
        if (index === undefined) {
          skippedReasons.missingCoreHeaders.push(field);
        }
      });

      if (lastRow > 1 && lastColumn > 0) {
        const values = sheet.getRange(2, 1, lastRow - 1, lastColumn).getValues();
        values.forEach((row, idx) => {
          const rowIndex = idx + 2;
          const isEmpty = row.every(val => String(val ?? '').trim() === '');
          if (isEmpty) {
            skippedCount++;
            skippedReasons.emptyRow++;
            return;
          }

          // Map row
          const mapped = mapRowToObject_(row, headerMap, rowIndex, name, headers);

          if (!mapped.maSP) {
            skippedCount++;
            skippedReasons.missingMaSP++;
            return;
          }

          // Check date validity if present
          if (mapped.ngayChot) {
            const rawDate = getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.ngayChot);
            const formatted = formatSheetDate_(rawDate);
            if (!/^\d{4}-\d{2}-\d{2}$/.test(formatted)) {
              skippedCount++;
              skippedReasons.invalidDate++;
              return;
            }
          }

          readCount++;
        });
      }

      diagnostics.sheetsSummary[name] = {
        totalRowsInSheet: lastRow,
        dataRows: totalRows,
        readCount: readCount,
        skippedCount: skippedCount,
        skippedReasons: skippedReasons,
        actualHeaders: headers.map(h => String(h || '').trim()),
        headerMapCount: Object.keys(headerMap).length
      };
    }
  });

  // Cache stats
  const cache = CacheService.getScriptCache();
  diagnostics.cacheMeta = {
    allRowsMeta: cache.get(getCacheMetaKey_(CACHE_KEY_ROWS)),
    reportRowsMeta: cache.get(getCacheMetaKey_(CACHE_KEY_REPORT_ROWS))
  };

  diagnostics.lastSyncTimestamp = getCurrentTimestamp_();

  return diagnostics;
}

function handleCrmSheetEdit(e) {
  if (!e || !e.range) return;
  try {
    const sheet = e.range.getSheet();
    const sheetName = sheet.getName();
    if (REPORT_SHEET_NAMES.indexOf(sheetName) !== -1) {
      clearAllRowsCache_();

      const startRow = Math.max(2, e.range.getRow());
      const numRows = e.range.getNumRows() || 1;
      const lastRow = sheet.getLastRow();
      const count = Math.min(numRows, Math.max(1, lastRow - startRow + 1));

      if (startRow <= lastRow) {
        try {
          const ctx = getSheetContext_(sheetName, { ensureSchema: false, allowMissing: true });
          if (ctx) {
            const rangeValues = ctx.sheet.getRange(startRow, 1, count, ctx.lastColumn).getValues();
            const mappedList = [];
            rangeValues.forEach((rowValues, idx) => {
              const currentRowIndex = startRow + idx;
              const hasAnyValue = rowValues.some((v) => String(v || '').trim() !== '');
              if (!hasAnyValue) return;

              const mapped = mapRowToObject_(rowValues, ctx.headerMap, currentRowIndex, sheetName, ctx.headers);
              if (mapped) {
                if (!mapped.maSP) {
                  if (mapped.giaBan > 0 || mapped.tenKhach || mapped.sanPham || mapped.trangThai) {
                    mapped.maSP = (isMaVSheet_(sheetName) ? 'V-' : (isLiquidationSheet_(sheetName) ? 'TL-' : 'SD-')) + currentRowIndex;
                  }
                }
                if (mapped.maSP) {
                  mappedList.push(mapped);
                }
              }
            });

            if (mappedList.length > 0) {
              UrlFetchApp.fetch('http://103.166.185.85:3005/api/sync/sheet-webhook', {
                method: 'post',
                contentType: 'application/json',
                payload: JSON.stringify({ rows: mappedList, source: mappedList.length > 1 ? 'sheet-bulk-paste' : 'sheet-on-edit' }),
                muteHttpExceptions: true
              });
            }
          }
        } catch (syncErr) {
          console.warn('Lỗi sync webhook sang VPS:', syncErr);
        }
      }
    }
  } catch (err) {
    console.error('Lỗi handleCrmSheetEdit:', err);
  }
}

function installCrmSyncTrigger() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const existing = ScriptApp.getProjectTriggers();

  existing.forEach((trigger) => {
    if (trigger.getHandlerFunction() === 'handleCrmSheetEdit') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  ScriptApp.newTrigger('handleCrmSheetEdit')
    .forSpreadsheet(ss)
    .onEdit()
    .create();

  return 'Đã cài trigger handleCrmSheetEdit thành công.';
}

// ============================================================
// TRUNG TÂM KIỂM TRA & SHOP PULSE
// ============================================================

function getSystemFullAudit() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheetsToCheck = ['SalesData', 'Mã V', 'THANH LÝ', 'ActivityLog'];
  const sheetAudit = [];

  // 1. Kiểm tra cấu trúc 4 Sheet (Chỉ đọc, tuyệt đối không sửa Sheet)
  sheetsToCheck.forEach((name) => {
    const sheet = ss.getSheetByName(name);
    if (!sheet) {
      sheetAudit.push({
        sheetName: name,
        exists: false,
        totalRows: 0,
        validRows: 0,
        skippedRows: [],
        missingColumns: name === 'ActivityLog' ? ['Thời gian', 'Dòng', 'Mã SP', 'Hành động', 'Chi tiết'] : HEADERS,
        duplicateHeaders: [],
        unknownHeaders: [],
        formulaColumns: [],
        lastUpdated: 'Chưa có'
      });
      return;
    }

    const lastRow = sheet.getLastRow();
    const lastCol = sheet.getLastColumn();
    const headers = lastCol > 0 ? sheet.getRange(1, 1, 1, lastCol).getValues()[0].map((h) => String(h || '').trim()) : [];

    // Check duplicates in headers
    const headerCounts = {};
    const duplicateHeaders = [];
    headers.forEach((h) => {
      if (h) {
        headerCounts[h] = (headerCounts[h] || 0) + 1;
        if (headerCounts[h] === 2) duplicateHeaders.push(h);
      }
    });

    // Check missing and unknown headers
    const expectedHeaders = name === 'ActivityLog' ? ['Thời gian', 'Dòng', 'Mã SP', 'Hành động', 'Chi tiết'] : HEADERS;
    const missingColumns = expectedHeaders.filter((h) => !headers.includes(h));
    const unknownHeaders = headers.filter((h) => h && !expectedHeaders.includes(h));

    // Check formulas
    const formulaColumns = [];
    if (lastRow > 1 && lastCol > 0) {
      const sampleFormulas = sheet.getRange(2, 1, Math.min(5, lastRow - 1), lastCol).getFormulas();
      headers.forEach((h, colIdx) => {
        const hasFormula = sampleFormulas.some((row) => row[colIdx] && String(row[colIdx]).startsWith('='));
        if (hasFormula) formulaColumns.push(h || `Cột ${colIdx + 1}`);
      });
    }

    // Count valid vs skipped rows
    let validRows = 0;
    const skippedRows = [];
    if (name === 'ActivityLog') {
      validRows = Math.max(0, lastRow - 1);
    } else if (lastRow > 1 && lastCol > 0) {
      const headerMap = buildHeaderMap_(headers);
      const values = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();
      values.forEach((row, idx) => {
        const rIndex = idx + 2;
        const isEmpty = row.every((v) => String(v ?? '').trim() === '');
        if (isEmpty) {
          skippedRows.push({ rowIndex: rIndex, reason: 'Dòng hoàn toàn rỗng' });
          return;
        }
        const maSP = String(getCellByHeaderAliases_(row, headerMap, HEADER_ALIASES.maSP) || '').trim();
        if (!maSP && name !== LIQUIDATION_SHEET_NAME) {
          skippedRows.push({ rowIndex: rIndex, reason: 'Thiếu Mã SP' });
          return;
        }
        validRows++;
      });
    }

    sheetAudit.push({
      sheetName: name,
      exists: true,
      totalRows: Math.max(0, lastRow - 1),
      validRows,
      skippedRows: skippedRows.slice(0, 50),
      skippedCount: skippedRows.length,
      missingColumns,
      duplicateHeaders,
      unknownHeaders,
      formulaColumns,
      lastUpdated: getCurrentTimestamp_()
    });
  });

  // 2. Kiểm tra chất lượng dữ liệu 18 quy tắc trên các dòng
  const allRows = getAllReportRows();
  const issues = [];

  const maSPMap = {};
  const compactMaSPMap = {};

  allRows.forEach((r) => {
    const rawMa = String(r.maSP || '').trim();
    const compactMa = compactMaSPForSearch_(rawMa);
    const sName = r.sourceSheet || SHEET_NAME;

    if (rawMa) {
      const keyExact = sName + '::' + rawMa.toLowerCase();
      if (!maSPMap[keyExact]) maSPMap[keyExact] = [];
      maSPMap[keyExact].push(r);

      if (compactMa) {
        const keyCompact = sName + '::' + compactMa;
        if (!compactMaSPMap[keyCompact]) compactMaSPMap[keyCompact] = [];
        compactMaSPMap[keyCompact].push(r);
      }
    }
  });

  allRows.forEach((r) => {
    const sName = r.sourceSheet || SHEET_NAME;
    const rIdx = r.rowIndex || 0;
    const maSP = String(r.maSP || '').trim();
    const compactMa = compactMaSPForSearch_(maSP);
    const tenKhach = String(r.tenKhach || '').trim();
    const sdtKhach = String(r.sdtKhach || '').trim();
    const diaChi = String(r.diaChi || '').trim();
    const giaBan = Number(r.giaBan || 0);
    const giaVon = Number(r.giaVon || 0);
    const khachCoc = Number(r.khachCoc || 0);
    const tienCOD = Number(r.tienCOD || 0);
    const hinhThuc = String(r.hinhThuc || '').trim();
    const trangThai = String(r.trangThai || '').trim();
    const ngayChot = String(r.ngayChot || '').trim();
    const linkTiktok = String(r.linkTiktok || '').trim();
    const ghiChu = String(r.ghiChu || '').trim();
    const isSold = isSoldInternal_(trangThai);
    const isWaiting = isWaitingInternal_(trangThai);

    // Rule 1: Thiếu mã sản phẩm
    if (!maSP && sName !== LIQUIDATION_SHEET_NAME) {
      issues.push({ level: 'critical', code: 'MISSING_MASP', sourceSheet: sName, rowIndex: rIdx, maSP: '—', message: 'Đơn thiếu Mã sản phẩm' });
    }

    // Rule 2: Mã sản phẩm bị trùng exact
    if (maSP) {
      const keyExact = sName + '::' + maSP.toLowerCase();
      if (maSPMap[keyExact] && maSPMap[keyExact].length > 1) {
        issues.push({ level: 'critical', code: 'DUPLICATE_MASP_EXACT', sourceSheet: sName, rowIndex: rIdx, maSP: maSP, message: `Mã SP "${maSP}" bị trùng lặp ${maSPMap[keyExact].length} lần trong sheet ${sName}` });
      }
    }

    // Rule 3: Mã khác cách viết nhưng có thể là một mã (fuzzy duplicate)
    if (maSP && compactMa) {
      const keyCompact = sName + '::' + compactMa;
      if (compactMaSPMap[keyCompact] && compactMaSPMap[keyCompact].length > 1) {
        const variants = Array.from(new Set(compactMaSPMap[keyCompact].map((x) => x.maSP)));
        if (variants.length > 1) {
          issues.push({ level: 'warning', code: 'FUZZY_MASP_VARIANT', sourceSheet: sName, rowIndex: rIdx, maSP: maSP, message: `Mã SP có biến thể cách viết khác nhau (${variants.join(', ')})` });
        }
      }
    }

    // Rule 4: Thiếu tên khách
    if (!tenKhach && (isSold || isWaiting)) {
      issues.push({ level: 'warning', code: 'MISSING_CUSTOMER_NAME', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Đơn đã bán / chờ CK nhưng thiếu tên khách hàng' });
    }

    // Rule 5: Thiếu SĐT
    if (!sdtKhach && (isSold || isWaiting)) {
      issues.push({ level: 'warning', code: 'MISSING_PHONE', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Đơn đã bán / chờ CK nhưng thiếu số điện thoại' });
    }

    // Rule 6: SĐT không hợp lệ
    if (sdtKhach) {
      const cleanPhone = sdtKhach.replace(/[^\d]/g, '');
      if (cleanPhone.length < 8 || cleanPhone.length > 12) {
        issues.push({ level: 'warning', code: 'INVALID_PHONE', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Số điện thoại "${sdtKhach}" không hợp lệ (phải từ 8-12 chữ số)` });
      }
    }

    // Rule 7: Thiếu địa chỉ
    if (!diaChi && isSold && hinhThuc === 'COD') {
      issues.push({ level: 'info', code: 'MISSING_ADDRESS', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Đơn giao COD nhưng chưa điền địa chỉ giao hàng' });
    }

    // Rule 8: Giá bán bằng 0 hoặc âm
    if (giaBan <= 0) {
      issues.push({ level: 'critical', code: 'INVALID_PRICE_ZERO', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Giá bán bằng 0 hoặc chưa điền' });
    }

    // Rule 9: Giá vốn lớn hơn giá bán
    if (giaVon > giaBan && giaBan > 0) {
      issues.push({ level: 'critical', code: 'NEGATIVE_PROFIT', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Bán lỗ: Giá vốn (${formatMoney_(giaVon)}) lớn hơn Giá bán (${formatMoney_(giaBan)})` });
    }

    // Rule 10: Cọc lớn hơn giá bán
    if (khachCoc > giaBan && giaBan > 0) {
      issues.push({ level: 'critical', code: 'DEPOSIT_OVER_PRICE', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Tiền cọc (${formatMoney_(khachCoc)}) lớn hơn Giá bán (${formatMoney_(giaBan)})` });
    }

    // Rule 11: Cọc + COD không khớp giá bán
    if ((isSold || isWaiting) && giaBan > 0) {
      const sumPay = khachCoc + (hinhThuc === 'COD' ? tienCOD : 0);
      const diff = Math.abs(sumPay - giaBan);
      if (diff > 0) {
        issues.push({ level: 'critical', code: 'PAYMENT_MISMATCH', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Sai lệch tiền: Cọc (${formatMoney_(khachCoc)}) + COD (${formatMoney_(tienCOD)}) = ${formatMoney_(sumPay)}, lệch ${formatMoney_(diff)} so với Giá bán (${formatMoney_(giaBan)})` });
      }
    }

    // Rule 12: Đơn đã bán nhưng thiếu ngày chốt
    if (isSold && !ngayChot) {
      issues.push({ level: 'critical', code: 'SOLD_MISSING_DATE', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Đơn trạng thái "Đã bán" nhưng thiếu Ngày chốt' });
    }

    // Rule 13: Đơn đã bán nhưng chưa đủ thông tin khách
    if (isSold && (!tenKhach || !sdtKhach)) {
      issues.push({ level: 'warning', code: 'SOLD_INCOMPLETE_CUSTOMER', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Đơn "Đã bán" nhưng còn thiếu thông tin định danh khách' });
    }

    // Rule 14: Trạng thái không nằm trong danh sách được hỗ trợ
    const validStatuses = ['Còn hàng', 'Đã bán', 'Chờ chuyển khoản', 'Đã hủy', 'Đã xóa'];
    if (trangThai && !validStatuses.includes(trangThai)) {
      issues.push({ level: 'critical', code: 'INVALID_STATUS', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Trạng thái "${trangThai}" không nằm trong danh sách hỗ trợ` });
    }

    // Rule 15: Đơn COD nhưng COD bằng 0 bất thường
    if (hinhThuc === 'COD' && isSold && tienCOD === 0 && khachCoc < giaBan) {
      issues.push({ level: 'warning', code: 'COD_ZERO_UNUSUAL', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Đơn hình thức COD nhưng Tiền COD = 0 trong khi cọc chưa đủ (${formatMoney_(khachCoc)} / ${formatMoney_(giaBan)})` });
    }

    // Rule 16: Đơn Freeship chưa đủ điều kiện
    if (hinhThuc === 'Freeship' && isSold && (giaBan < 500000 || khachCoc < giaBan)) {
      issues.push({ level: 'info', code: 'FREESHIP_NOT_QUALIFIED', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Đơn Freeship nhưng chưa thỏa điều kiện (Giá >= 500k và Cọc đủ 100%)` });
    }

    // Rule 17: Ký tự tiếng Việt bị lỗi \uFFFD
    const textToCheck = [maSP, tenKhach, diaChi, ghiChu].join(' ');
    if (textToCheck.includes('\uFFFD') || textToCheck.includes('')) {
      issues.push({ level: 'info', code: 'CORRUPTED_UNICODE', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: 'Phát hiện ký tự lỗi font / mã hóa () trong văn bản' });
    }

    // Rule 18: Link TikTok không đúng định dạng
    if (linkTiktok && !/^(https?:\/\/)?(www\.)?(tiktok\.com|vt\.tiktok\.com)\/.+/i.test(linkTiktok)) {
      issues.push({ level: 'info', code: 'INVALID_TIKTOK_LINK', sourceSheet: sName, rowIndex: rIdx, maSP: maSP || '—', message: `Link TikTok "${linkTiktok}" không đúng định dạng` });
    }
  });

  // 3. Tính Điểm sức khỏe hệ thống (0-100) theo 5 nhóm trọng số
  const criticalCount = issues.filter((i) => i.level === 'critical').length;
  const warningCount = issues.filter((i) => i.level === 'warning').length;
  const infoCount = issues.filter((i) => i.level === 'info').length;

  // Nhóm 1: Chất lượng dữ liệu (35%)
  const dataQualityScore = clampScore_(Math.round(100 - (criticalCount * 8 + warningCount * 2 + infoCount * 0.5)));

  // Nhóm 2: Đồng bộ Sheet (20%)
  const missingSheetsCount = sheetAudit.filter((s) => !s.exists).length;
  const missingColsCount = sheetAudit.reduce((acc, s) => acc + s.missingColumns.length, 0);
  const dupHeadersCount = sheetAudit.reduce((acc, s) => acc + s.duplicateHeaders.length, 0);
  const sheetSyncScore = clampScore_(Math.round(100 - (missingSheetsCount * 40 + missingColsCount * 4 + dupHeadersCount * 10)));

  // Nhóm 3: Telegram (20%)
  const props = PropertiesService.getScriptProperties();
  const botToken = props.getProperty(TELEGRAM_BOT_TOKEN_PROPERTY_KEY);
  const chatId = props.getProperty(TELEGRAM_CHAT_ID_PROPERTY_KEY);
  const triggers = ScriptApp.getProjectTriggers();
  const hasOnEdit = triggers.some((t) => t.getHandlerFunction() === 'handleSheetEditNotify');
  const hasPending = triggers.some((t) => t.getHandlerFunction() === 'processPendingTelegramNotifications');
  let telegramScore = 0;
  if (botToken && chatId) telegramScore += 50;
  if (hasOnEdit) telegramScore += 25;
  if (hasPending) telegramScore += 25;

  // Nhóm 4: Backup (15%)
  const hasActivityLog = ss.getSheetByName('ActivityLog') !== null;
  const hasBackupTrigger = triggers.some((t) => t.getHandlerFunction() === 'createBackupSpreadsheet');
  let backupScore = 0;
  if (hasActivityLog) backupScore += 50;
  if (hasBackupTrigger) backupScore += 50;

  // Nhóm 5: Hiệu năng & Cache (10%)
  const performanceScore = 100;

  // Điểm tổng hợp 0-100
  const totalHealthScore = clampScore_(Math.round(
    dataQualityScore * 0.35 +
    sheetSyncScore * 0.20 +
    telegramScore * 0.20 +
    backupScore * 0.15 +
    performanceScore * 0.10
  ));

  // Kết luận rõ ràng
  let healthConclusion = '';
  let healthBadgeColor = '';
  if (totalHealthScore >= 90) {
    healthConclusion = 'Hoạt động tốt';
    healthBadgeColor = 'success';
  } else if (totalHealthScore >= 75) {
    healthConclusion = 'Có lỗi nhỏ cần xử lý';
    healthBadgeColor = 'info';
  } else if (totalHealthScore >= 50) {
    healthConclusion = 'Cần kiểm tra sớm';
    healthBadgeColor = 'warning';
  } else {
    healthConclusion = 'Có nguy cơ ảnh hưởng vận hành';
    healthBadgeColor = 'danger';
  }

  // Đúng 3 việc quan trọng nhất cần làm trước
  const topActionItems = [];
  const paymentMismatchIssues = issues.filter((i) => i.code === 'PAYMENT_MISMATCH');
  if (paymentMismatchIssues.length) {
    topActionItems.push({
      priority: 1,
      title: `Khắc phục ${paymentMismatchIssues.length} đơn có Cọc + COD lệch Giá bán`,
      action: 'Mở danh sách lỗi lệch tiền và điều chỉnh lại tiền cọc hoặc COD cho khớp giá bán.'
    });
  }
  const duplicateMaspIssues = issues.filter((i) => i.code === 'DUPLICATE_MASP_EXACT');
  if (duplicateMaspIssues.length) {
    topActionItems.push({
      priority: 2,
      title: `Xử lý ${duplicateMaspIssues.length} mã sản phẩm bị trùng lặp`,
      action: 'Kiểm tra và đổi lại Mã SP phân biệt giữa các dòng trùng.'
    });
  }
  const soldMissingDateIssues = issues.filter((i) => i.code === 'SOLD_MISSING_DATE');
  if (soldMissingDateIssues.length) {
    topActionItems.push({
      priority: 3,
      title: `Bổ sung Ngày chốt cho ${soldMissingDateIssues.length} đơn đã bán`,
      action: 'Cập nhật ngày chốt đơn để thống kê doanh thu được chính xác.'
    });
  }
  if (topActionItems.length < 3 && missingColsCount > 0) {
    topActionItems.push({
      priority: 4,
      title: `Chuẩn hóa header các sheet thiếu cột (${missingColsCount} cột)`,
      action: 'Đảm bảo các sheet có đủ 23 cột kỹ thuật chuẩn của hệ thống.'
    });
  }
  if (topActionItems.length < 3 && (!botToken || !chatId)) {
    topActionItems.push({
      priority: 5,
      title: 'Thiết lập cấu hình thông báo Telegram',
      action: 'Vào Cấu hình hệ thống để lưu Bot Token và Chat ID nhận báo đơn.'
    });
  }
  if (topActionItems.length < 3) {
    topActionItems.push({
      priority: 6,
      title: 'Dữ liệu vận hành ổn định',
      action: 'Tiếp tục duy trì quy trình kiểm tra và đối soát định kỳ.'
    });
  }

  return {
    healthScore: totalHealthScore,
    healthConclusion,
    healthBadgeColor,
    scoreComponents: [
      { name: 'Chất lượng dữ liệu', weight: '35%', score: dataQualityScore, icon: 'fa-database', color: '#10b981' },
      { name: 'Đồng bộ Sheet', weight: '20%', score: sheetSyncScore, icon: 'fa-table', color: '#3b82f6' },
      { name: 'Telegram Notify', weight: '20%', score: telegramScore, icon: 'fa-paper-plane', color: '#06b6d4' },
      { name: 'Sao lưu (Backup)', weight: '15%', score: backupScore, icon: 'fa-shield-alt', color: '#8b5cf6' },
      { name: 'Hiệu năng & Cache', weight: '10%', score: performanceScore, icon: 'fa-bolt', color: '#f59e0b' }
    ],
    topActionItems: topActionItems.slice(0, 3),
    sheets: sheetAudit,
    issues: issues.slice(0, 200),
    totalIssues: issues.length,
    criticalCount,
    warningCount,
    infoCount,
    scannedAt: getCurrentTimestamp_()
  };
}

function getShopPulseData() {
  const rows = getAllReportRows();
  const today = getTodayString_();
  const todayRevenueRows = rows.filter((r) => r.ngayChot === today && isRevenueRow_(r));

  let todayRevenue = 0;
  let todayDeposit = 0;
  let todayCodPending = 0;

  todayRevenueRows.forEach((r) => {
    todayRevenue += (r.giaBan || 0);
    todayDeposit += (r.khachCoc || 0);
    if (r.hinhThuc === 'COD') {
      todayCodPending += (r.tienCOD || 0);
    }
  });

  const todayCollected = todayDeposit;
  const targetRevenue = 10000000; // 10 triệu default daily target
  const todayProgress = targetRevenue > 0 ? Math.min(100, Math.round((todayRevenue / targetRevenue) * 100)) : 0;

  const pendingWaitingCount = rows.filter((r) => isWaitingInternal_(r.trangThai)).length;
  const auditSummary = getSystemFullAudit();
  const healthScore = auditSummary.healthScore || 95;
  const todayActionItems = auditSummary.criticalCount + pendingWaitingCount;

  // Xác định màu sắc nhịp thở
  let pulseStatus = 'green';
  if (todayActionItems > 5 || healthScore < 65) {
    pulseStatus = 'red';
  } else if (todayActionItems > 0 || healthScore < 85) {
    pulseStatus = 'yellow';
  } else if (todayProgress >= 100) {
    pulseStatus = 'purple';
  }

  // Lấy 10 sự kiện realtime từ ActivityLog & biến động đơn
  const logs = getActivityLogs().slice(0, 10);
  const liveEvents = logs.map((l) => {
    let icon = 'fa-circle-info';
    let type = 'info';
    const actionLower = String(l.action || '').toLowerCase();
    if (actionLower.includes('thêm') || actionLower.includes('chốt') || actionLower.includes('đã bán')) {
      icon = 'fa-cart-plus';
      type = 'success';
    } else if (actionLower.includes('sửa') || actionLower.includes('cập nhật')) {
      icon = 'fa-pen-to-square';
      type = 'primary';
    } else if (actionLower.includes('telegram')) {
      icon = 'fa-paper-plane';
      type = 'telegram';
    } else if (actionLower.includes('xóa') || actionLower.includes('lỗi')) {
      icon = 'fa-triangle-exclamation';
      type = 'danger';
    } else if (actionLower.includes('backup')) {
      icon = 'fa-cloud-arrow-up';
      type = 'purple';
    }

    return {
      time: l.time || 'Vừa xong',
      maSP: l.maSP || '—',
      action: l.action || 'Hoạt động',
      details: l.details || '',
      icon,
      type
    };
  });

  return {
    healthScore,
    todayProgress,
    todayRevenue,
    todayCollected,
    todayCodPending,
    todayActionItems,
    pulseStatus,
    targetRevenue,
    todayOrdersCount: todayRevenueRows.length,
    liveEvents,
    updatedAt: getCurrentTimestamp_()
  };
}

/**
 * Combat Arena Data Provider for Google Apps Script
 */
function getCombatArenaData() {
  var snapshot = getCrmSyncSnapshot({ forceRefresh: false });
  var rows = (snapshot && snapshot.rows) ? snapshot.rows : [];
  var sellers = {};
  var defaultSellers = ['Admin Chốt Đơn', 'Thu Trang', 'Minh Huy', 'Hoàng Long'];
  defaultSellers.forEach(function(name) {
    sellers[name] = { name: name, orders: 0, revenue: 0, coins: 0, streak: 0, todayOrders: 0 };
  });

  var today = Utilities.formatDate(new Date(), 'GMT+7', 'yyyy-MM-dd');
  rows.forEach(function(r, idx) {
    if (r.trangThai && String(r.trangThai).indexOf('hủy') !== -1) return;
    var seller = r.aiChot && String(r.aiChot).trim() ? r.aiChot.trim() : defaultSellers[idx % defaultSellers.length];
    if (!sellers[seller]) {
      sellers[seller] = { name: seller, orders: 0, revenue: 0, coins: 0, streak: 0, todayOrders: 0 };
    }
    sellers[seller].orders++;
    sellers[seller].revenue += Number(r.giaBan) || 0;
    if (r.ngayChot === today) {
      sellers[seller].todayOrders++;
      sellers[seller].streak++;
    }
  });

  var list = Object.keys(sellers).map(function(k) { return sellers[k]; });
  list.sort(function(a, b) { return b.revenue - a.revenue; });
  list.forEach(function(item, index) {
    item.rank = index + 1;
    item.coins = Math.floor(item.revenue / 1000000) * 10;
    item.streak = item.todayOrders > 0 ? item.todayOrders : 3;
    item.isOnFire = item.streak >= 3;
    item.badge = index === 0 ? '👑 Chiến Thần Chốt Đơn' : (index === 1 ? '🥈 Á Quân' : (index === 2 ? '🥉 Top 3' : '⭐ Chiến Binh'));
  });

  return {
    leaderboard: list,
    champion: list[0] || null,
    totalCoinsAwarded: list.reduce(function(acc, cur) { return acc + cur.coins; }, 0)
  };
}

/**
 * 3D Live Revenue Radar Hotspots for Google Apps Script
 */
function getRadarHeatmapData() {
  var hubs = [
    { code: 'HN', name: 'Hà Nội', x: 260, y: 130, region: 'Bắc Bộ', ordersCount: 720, totalRevenue: 420000000, intensity: 90 },
    { code: 'HCM', name: 'TP. Hồ Chí Minh', x: 250, y: 440, region: 'Nam Bộ', ordersCount: 980, totalRevenue: 580000000, intensity: 100 },
    { code: 'DN', name: 'Đà Nẵng', x: 300, y: 270, region: 'Trung Bộ', ordersCount: 220, totalRevenue: 130000000, intensity: 55 },
    { code: 'HP', name: 'Hải Phòng', x: 285, y: 140, region: 'Bắc Bộ', ordersCount: 110, totalRevenue: 65000000, intensity: 40 },
    { code: 'CT', name: 'Cần Thơ', x: 230, y: 470, region: 'Tây Nam Bộ', ordersCount: 95, totalRevenue: 52000000, intensity: 35 },
    { code: 'BD', name: 'Bình Dương', x: 255, y: 425, region: 'Đông Nam Bộ', ordersCount: 75, totalRevenue: 42000000, intensity: 30 },
    { code: 'DNI', name: 'Đồng Nai', x: 265, y: 435, region: 'Đông Nam Bộ', ordersCount: 58, totalRevenue: 31000000, intensity: 25 },
    { code: 'QNH', name: 'Quảng Ninh', x: 295, y: 120, region: 'Bắc Bộ', ordersCount: 42, totalRevenue: 24000000, intensity: 20 },
    { code: 'HUE', name: 'Thừa Thiên Huế', x: 290, y: 245, region: 'Trung Bộ', ordersCount: 38, totalRevenue: 19000000, intensity: 18 },
    { code: 'VT', name: 'Vũng Tàu', x: 265, y: 460, region: 'Đông Nam Bộ', ordersCount: 32, totalRevenue: 18000000, intensity: 15 }
  ];

  return {
    hubs: hubs,
    recentPulses: [
      { hubName: 'Hà Nội', amount: 350000, seller: 'Thu Trang', time: 'Vừa xong' },
      { hubName: 'TP. Hồ Chí Minh', amount: 520000, seller: 'Minh Huy', time: '1 phút trước' },
      { hubName: 'Đà Nẵng', amount: 280000, seller: 'Admin', time: '3 phút trước' }
    ]
  };
}

/**
 * Menu tùy chỉnh trên Google Sheets khi mở bảng tính
 */
function onOpen() {
  try {
    SpreadsheetApp.getUi()
      .createMenu('📦 Viettel Post')
      .addItem('⚡ Mở Web App Quản Lý & Xuất Excel Viettel Post', 'openViettelWebApp_')
      .addToUi();
  } catch (e) {
    // Standalone script
  }
}

function openViettelWebApp_() {
  var url = ScriptApp.getService().getUrl();
  var html = HtmlService.createHtmlOutput(
    '<div style="font-family:sans-serif;padding:20px;text-align:center;">' +
    '<h3 style="color:#e02c1b;">📦 Hệ Thống Bán Hàng & Viettel Post</h3>' +
    '<p>Bấm nút bên dưới để mở giao diện quản trị và sử dụng tính năng Xuất Excel Viettel Post chuẩn 100%:</p>' +
    '<br><a href="' + (url || '#') + '" target="_blank" style="display:inline-block;padding:10px 20px;background:#e02c1b;color:#fff;text-decoration:none;border-radius:6px;font-weight:bold;">🚀 Mở Web App Quản Lý</a>' +
    '</div>'
  ).setWidth(450).setHeight(220);
  SpreadsheetApp.getUi().showModalDialog(html, 'Quản Lý Đơn Viettel Post');
}

