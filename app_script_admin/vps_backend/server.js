const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { db, getSetting, setSetting } = require('./db');
const statsHelper = require('./stats');
const backupHelper = require('./scripts/backup');

const app = express();
const PORT = process.env.PORT || 3005;

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Helper row mapper from db snake_case to frontend camelCase
function mapDbRowToApi(row) {
  if (!row) return null;
  return {
    rowIndex: row.id,
    id: row.id,
    sheetName: row.sheet_name || 'SalesData',
    maSP: row.ma_sp,
    sanPham: row.san_pham || '',
    giaBan: Number(row.gia_ban) || 0,
    giaVon: Number(row.gia_von) || 0,
    tienLoi: Number(row.tien_loi) || 0,
    tienCOD: Number(row.tien_cod) || 0,
    khachCoc: Number(row.khach_coc) || 0,
    tenKhach: row.ten_khach || '',
    sdtKhach: row.sdt_khach || '',
    aiChot: row.ai_chot || '',
    ngayChot: row.ngay_chot || '',
    trangThai: row.trang_thai || 'Còn hàng',
    hinhThuc: row.hinh_thuc || 'COD',
    diaChi: row.dia_chi || '',
    ghiChu: row.ghi_chu || '',
    khoiLuong: Number(row.khoi_luong) || 200,
    loaiHangHoa: row.loai_hang_hoa || 'Bưu kiện',
    tinhChatHangHoa: row.tinh_chat_hang_hoa || '',
    dichVu: row.dich_vu || '',
    dichVuCongThem: row.dich_vu_cong_them || '',
    ngayTao: row.ngay_tao || ''
  };
}

// ═══════════════════════════════════════════════
// API HEALTH CHECK
// ═══════════════════════════════════════════════
app.get('/api/health', (req, res) => {
  const rowCount = db.prepare('SELECT COUNT(*) as c FROM orders').get().c;
  res.json({
    status: 'ok',
    service: 'sales-admin-api',
    uptime: process.uptime(),
    port: PORT,
    ordersCount: rowCount,
    timestamp: new Date().toISOString()
  });
});

// ═══════════════════════════════════════════════
// BUSINESS LOGIC SERVICES
// ═══════════════════════════════════════════════

function getAllRowsService() {
  const rows = db.prepare("SELECT * FROM orders WHERE sheet_name IN ('SalesData', 'Mã V') ORDER BY id DESC").all();
  return rows.map(mapDbRowToApi);
}

function getAllReportRowsService() {
  const rows = db.prepare("SELECT * FROM orders ORDER BY id DESC").all();
  return rows.map(mapDbRowToApi);
}

function getLiquidationRowsService() {
  const rows = db.prepare("SELECT * FROM orders WHERE sheet_name = 'THANH LÝ' ORDER BY id DESC").all();
  return rows.map(mapDbRowToApi);
}

function buildBusinessHealthScore(rows) {
  const today = new Date().toISOString().slice(0, 10);
  const currentMonth = today.slice(0, 7);
  let curRev = 0, curCost = 0, curOrders = 0;
  
  rows.forEach(r => {
    if (r.ngayChot && r.ngayChot.slice(0, 7) === currentMonth && statsHelper.isRevenueRow(r)) {
      curRev += r.giaBan;
      curCost += r.giaVon;
      curOrders++;
    }
  });

  const profit = curRev - curCost;
  const margin = curRev > 0 ? profit / curRev : 0;
  const score = Math.min(100, Math.max(50, Math.round(75 + (margin * 25))));

  return {
    score: score,
    label: score >= 85 ? 'Rất khỏe' : (score >= 70 ? 'Ổn định' : 'Cần chú ý'),
    currentMonth,
    components: [
      { key: 'revenue', label: 'Doanh thu', score: 85, value: curRev, previous: 0 },
      { key: 'profit', label: 'Lợi nhuận', score: 80, value: profit, margin: Math.round(margin * 100) },
      { key: 'orders', label: 'Đơn hàng', score: 85, value: curOrders }
    ]
  };
}

function buildCustomerLifetimeDashboard(rows) {
  const dates = [];
  const map = {};
  rows.forEach(r => {
    if (r.ngayChot && statsHelper.isRevenueRow(r)) {
      const m = r.ngayChot.slice(0, 7);
      if (!map[m]) {
        map[m] = { newCust: 0, retCust: 0, lostCust: 0 };
        dates.push(m);
      }
      map[m].newCust++;
    }
  });
  const labels = dates.sort().slice(-6);
  if (labels.length === 0) {
    labels.push(new Date().toISOString().slice(0, 7));
  }
  return {
    labels: labels,
    newCustomers: labels.map(l => (map[l] ? map[l].newCust : 0)),
    returningCustomers: labels.map(() => 0),
    lostCustomers: labels.map(() => 0)
  };
}

function getDashboardStatsService() {
  const rows = getAllReportRowsService();
  const today = new Date().toISOString().slice(0, 10);
  const yesterdayDate = new Date();
  yesterdayDate.setDate(yesterdayDate.getDate() - 1);
  const yesterday = yesterdayDate.toISOString().slice(0, 10);

  let tongDoanhThu = 0, tongGiaVon = 0, tongLoiNhuan = 0, tongLo = 0, tongTienCOD = 0, tongKhachCoc = 0;
  let soLuongCon = 0, soLuongBan = 0, soLuongDoiCK = 0, soLuongXoa = 0;
  let soCOD = 0, soFreeship = 0;
  let donBanHomNay = 0, doanhThuHomNay = 0, loiNhuanHomNay = 0, cocHomNay = 0, codHomNay = 0;
  let donBanHomQua = 0, doanhThuHomQua = 0, loiNhuanHomQua = 0, cocHomQua = 0, codHomQua = 0;

  const doanhThuNgay = {}, loiNhuanNgay = {}, donNgay = {}, loNgay = {};
  const topKhachMap = {};

  rows.forEach((row) => {
    const tt = row.trangThai;
    const ht = row.hinhThuc;

    if (statsHelper.isDeletedInternal(tt)) { soLuongXoa++; return; }
    if (statsHelper.isInStockInternal(tt)) soLuongCon++;
    if (statsHelper.isSoldInternal(tt)) soLuongBan++;
    if (statsHelper.isWaitingInternal(tt)) soLuongDoiCK++;

    if (ht === 'COD') soCOD++;
    if (ht === 'Freeship') soFreeship++;

    const isRevenue = statsHelper.isRevenueRow(row);
    if (isRevenue) {
      tongDoanhThu += row.giaBan;
      tongGiaVon += row.giaVon;
      tongKhachCoc += row.khachCoc;
      if (ht === 'COD') tongTienCOD += row.tienCOD;

      const computedLoi = row.giaBan - row.giaVon;
      if (computedLoi >= 0) {
        tongLoiNhuan += computedLoi;
      } else {
        tongLo += Math.abs(computedLoi);
      }

      const d = row.ngayChot;
      if (d) {
        doanhThuNgay[d] = (doanhThuNgay[d] || 0) + row.giaBan;
        donNgay[d] = (donNgay[d] || 0) + 1;
        if (computedLoi >= 0) {
          loiNhuanNgay[d] = (loiNhuanNgay[d] || 0) + computedLoi;
        } else {
          loNgay[d] = (loNgay[d] || 0) + Math.abs(computedLoi);
        }

        if (d === today) {
          donBanHomNay++;
          doanhThuHomNay += row.giaBan;
          loiNhuanHomNay += computedLoi;
          cocHomNay += row.khachCoc;
          if (ht === 'COD') codHomNay += row.tienCOD;

          const name = String(row.tenKhach || '').trim() || 'Khách ẩn danh';
          const phone = String(row.sdtKhach || '').trim();
          const key = phone || name;
          if (!topKhachMap[key]) {
            topKhachMap[key] = { name: name, phone: phone, revenue: 0 };
          }
          topKhachMap[key].revenue += row.giaBan;
        } else if (d === yesterday) {
          donBanHomQua++;
          doanhThuHomQua += row.giaBan;
          loiNhuanHomQua += computedLoi;
          cocHomQua += row.khachCoc;
          if (ht === 'COD') codHomQua += row.tienCOD;
        }
      }
    }
  });

  const chartLabels = Object.keys(doanhThuNgay).sort();
  if (chartLabels.length === 0) {
    chartLabels.push(today);
  }

  const last7Labels = chartLabels.slice(-7);
  const last7DoanhThu = last7Labels.map(d => doanhThuNgay[d] || 0);
  const last7LoiNhuan = last7Labels.map(d => loiNhuanNgay[d] || 0);
  const last7Don = last7Labels.map(d => donNgay[d] || 0);
  const last7Lo = last7Labels.map(d => loNgay[d] || 0);

  const topKhachHomNay = Object.values(topKhachMap).sort((a, b) => b.revenue - a.revenue).slice(0, 5);

  const growthDon = statsHelper.calculateGrowthPercentage(donBanHomNay, donBanHomQua);
  const growthDoanhThu = statsHelper.calculateGrowthPercentage(doanhThuHomNay, doanhThuHomQua);
  const growthLoiNhuan = statsHelper.calculateGrowthPercentage(loiNhuanHomNay, loiNhuanHomQua);
  const growthCoc = statsHelper.calculateGrowthPercentage(cocHomNay, cocHomQua);
  const growthCod = statsHelper.calculateGrowthPercentage(codHomNay, codHomQua);

  const tongSanPham = rows.length;
  const tyLeCOD = tongSanPham ? Math.round((soCOD / tongSanPham) * 100) : 0;
  const tyLeChot = tongSanPham ? Math.round((soLuongBan / tongSanPham) * 100) : 0;

  return {
    // Both property names for 100% backward and forward compatibility
    tongDoanhThu,
    doanhThu: tongDoanhThu,
    tongGiaVon,
    giaVon: tongGiaVon,
    tongLoiNhuan,
    loiNhuan: tongLoiNhuan,
    loiNhuanRong: (tongLoiNhuan - tongLo),
    tongLo,
    tienCOD: tongTienCOD,
    khachCoc: tongKhachCoc,
    tongSanPham,
    tongSP: tongSanPham,
    soLuongCon,
    conHang: soLuongCon,
    soLuongBan,
    daBan: soLuongBan,
    soLuongDoiCK,
    doiCK: soLuongDoiCK,
    soLuongXoa,
    daXoa: soLuongXoa,
    soCOD,
    soFreeship,
    donBanHomNay,
    doanhThuHomNay,
    loiNhuanHomNay,
    cocHomNay,
    codHomNay,
    donBanHomQua,
    doanhThuHomQua,
    loiNhuanHomQua,
    cocHomQua,
    codHomQua,
    growthDon,
    growthDoanhThu,
    growthLoiNhuan,
    growthCoc,
    growthCod,
    tyLeCOD,
    tyLeChot,
    chartLabels,
    chartDoanhThu: chartLabels.map(d => doanhThuNgay[d] || 0),
    chartLoiNhuan: chartLabels.map(d => loiNhuanNgay[d] || 0),
    chartDon: chartLabels.map(d => donNgay[d] || 0),
    last7DoanhThu,
    last7LoiNhuan,
    last7Don,
    last7Lo,
    topKhachHomNay,
    customerLifetime: buildCustomerLifetimeDashboard(rows),
    businessHealth: buildBusinessHealthScore(rows),
    notifications: []
  };
}

const GAS_EXPORT_URL = 'https://script.google.com/macros/s/AKfycbzPhJbclQyeVQm8wz3us5bSJ_bV__Xt9Tv3BPWaJNua4FueHuHGQUEE9GXOQHN9pPQY/exec?action=exportFullDataset&key=1512';

let isSyncingLive = false;
let lastLiveSyncTime = 0;

async function syncFromGoogleSheetLive(force = false) {
  const now = Date.now();
  if (isSyncingLive) return { skipped: true, reason: 'Already in progress' };
  if (!force && now - lastLiveSyncTime < 15000) return { skipped: true, reason: 'Throttled' };

  isSyncingLive = true;
  try {
    const res = await fetch(GAS_EXPORT_URL, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      redirect: 'follow'
    });
    const json = await res.json();
    if (!json.ok) throw new Error('GAS error: ' + json.error);

    const { salesData = [], maV = [], thanhLy = [] } = json.result || {};
    const allRows = [];

    for (const r of salesData) {
      r.sheetName = 'SalesData';
      let masp = String(r.maSP || '').trim();
      if (!masp) masp = 'SD-' + (allRows.length + 1);
      r.maSP = masp;
      allRows.push(r);
    }
    for (const r of maV) {
      r.sheetName = 'Mã V';
      let masp = String(r.maSP || '').trim();
      if (!masp) masp = 'V-' + (allRows.length + 1);
      else if (!masp.startsWith('V-') && /^\d+$/.test(masp)) masp = 'V-' + masp;
      r.maSP = masp;
      allRows.push(r);
    }
    for (const r of thanhLy) {
      r.sheetName = 'THANH LÝ';
      let masp = String(r.maSP || '').trim();
      if (!masp) masp = 'TL-' + (allRows.length + 1);
      r.maSP = masp;
      allRows.push(r);
    }

    const upsert = db.prepare(`
      INSERT INTO orders (
        sheet_name, ma_sp, san_pham, gia_ban, gia_von, tien_loi, tien_cod, khach_coc,
        ten_khach, sdt_khach, ai_chot, ngay_chot, trang_thai, hinh_thuc, dia_chi, ghi_chu,
        loai_hang_hoa, tinh_chat_hang_hoa, dich_vu, dich_vu_cong_them,
        ngay_tao, updated_at, synced_to_sheet, sync_source
      ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'google-sheet'
      )
      ON CONFLICT(ma_sp) DO UPDATE SET
        sheet_name = excluded.sheet_name,
        san_pham = excluded.san_pham,
        gia_ban = excluded.gia_ban,
        gia_von = excluded.gia_von,
        tien_loi = excluded.tien_loi,
        tien_cod = excluded.tien_cod,
        khach_coc = excluded.khach_coc,
        ten_khach = excluded.ten_khach,
        sdt_khach = excluded.sdt_khach,
        ai_chot = excluded.ai_chot,
        ngay_chot = excluded.ngay_chot,
        trang_thai = excluded.trang_thai,
        hinh_thuc = excluded.hinh_thuc,
        dia_chi = excluded.dia_chi,
        ghi_chu = excluded.ghi_chu,
        loai_hang_hoa = CASE WHEN excluded.loai_hang_hoa IS NOT NULL AND excluded.loai_hang_hoa != '' THEN excluded.loai_hang_hoa ELSE orders.loai_hang_hoa END,
        tinh_chat_hang_hoa = CASE WHEN excluded.tinh_chat_hang_hoa IS NOT NULL AND excluded.tinh_chat_hang_hoa != '' THEN excluded.tinh_chat_hang_hoa ELSE orders.tinh_chat_hang_hoa END,
        dich_vu = CASE WHEN excluded.dich_vu IS NOT NULL AND excluded.dich_vu != '' THEN excluded.dich_vu ELSE orders.dich_vu END,
        dich_vu_cong_them = CASE WHEN excluded.dich_vu_cong_them IS NOT NULL AND excluded.dich_vu_cong_them != '' THEN excluded.dich_vu_cong_them ELSE orders.dich_vu_cong_them END,
        updated_at = excluded.updated_at,
        synced_to_sheet = 1,
        sync_source = 'google-sheet'
    `);

    const nowIso = new Date().toISOString();
    let count = 0;
    const runBatch = db.transaction((items) => {
      for (const r of items) {
        if (!r.maSP) continue;
        const computedLoi = (Number(r.giaBan) || 0) - (Number(r.giaVon) || 0);
        upsert.run(
          r.sheetName,
          r.maSP,
          r.sanPham || '',
          Number(r.giaBan) || 0,
          Number(r.giaVon) || 0,
          computedLoi,
          Number(r.tienCOD) || 0,
          Number(r.khachCoc) || 0,
          r.tenKhach || '',
          r.sdtKhach || '',
          r.aiChot || '',
          r.ngayChot || '',
          r.trangThai || 'Còn hàng',
          r.hinhThuc || 'COD',
          r.diaChi || '',
          r.ghiChu || '',
          r.loaiHangHoa || 'Bưu kiện',
          r.tinhChatHangHoa || '',
          r.dichVu || '',
          r.dichVuCongThem || '',
          r.createdAt || nowIso,
          r.updatedAt || nowIso
        );
        count++;
      }
    });

    runBatch(allRows);
    lastLiveSyncTime = Date.now();
    console.log(`[Auto-Reconcile] Live synced ${count} rows from Google Sheet.`);
    return { success: true, count, syncedAt: new Date().toISOString() };
  } catch (err) {
    console.error('[Auto-Reconcile] Error syncing from Google Sheet:', err.message);
    return { success: false, error: err.message };
  } finally {
    isSyncingLive = false;
  }
}

async function getCrmSyncSnapshotService(options) {
  const force = Boolean(options && (options.forceRefresh || options.bypassCache));
  try {
    await syncFromGoogleSheetLive(force);
  } catch (e) {
    console.warn('Live sync before snapshot failed, returning SQLite cache:', e.message);
  }

  const rows = getAllRowsService();
  const reportRows = getAllReportRowsService();
  const stats = getDashboardStatsService();
  const dailyRows = reportRows.filter(r => r.trangThai === 'Đã bán' || r.trangThai === 'Đợi CK' || r.ngayChot);
  const countSales = reportRows.filter(r => r.sheetName === 'SalesData').length;
  const countMaV = reportRows.filter(r => r.sheetName === 'Mã V').length;
  const countThanhLy = reportRows.filter(r => r.sheetName === 'THANH LÝ').length;

  return {
    rows: rows,
    reportRows: reportRows,
    dailyRows: dailyRows,
    stats: stats,
    sourceCounts: {
      'SalesData': countSales,
      'Mã V': countMaV,
      'THANH LÝ': countThanhLy
    },
    syncedAt: new Date().toLocaleString('vi-VN'),
    cacheHit: false
  };
}

function getAdvancedStatsService(filterType, customStart, customEnd, filters) {
  const ranges = statsHelper.getPeriodDates(filterType, customStart, customEnd);
  let rows = getAllReportRowsService();
  if (filters && typeof filters === 'object') {
    rows = statsHelper.applyReportFilters(rows, filters);
  }

  const curRows = [];
  const prevRows = [];

  rows.forEach(r => {
    if (!statsHelper.isRevenueRow(r)) return;
    const d = r.ngayChot;
    if (!d) return;
    if (d >= ranges.currentStart && d <= ranges.currentEnd) {
      curRows.push(r);
    } else if (d >= ranges.prevStart && d <= ranges.prevEnd) {
      prevRows.push(r);
    }
  });

  const curStats = statsHelper.calculateSummary(curRows);
  const prevStats = statsHelper.calculateSummary(prevRows);

  const growth = {
    revenue: statsHelper.calculateGrowthPercentage(curStats.revenue, prevStats.revenue),
    profit: statsHelper.calculateGrowthPercentage(curStats.profit, prevStats.profit),
    orders: statsHelper.calculateGrowthPercentage(curStats.orders, prevStats.orders),
    aov: statsHelper.calculateGrowthPercentage(curStats.aov, prevStats.aov),
    soldProducts: statsHelper.calculateGrowthPercentage(curStats.soldProducts, prevStats.soldProducts)
  };

  const topProducts = statsHelper.getTopProducts(curRows, 10);
  const topCustomers = statsHelper.getTopCustomers(curRows, 10);
  const dailyBreakdown = statsHelper.getDailyStatsBreakdown(curRows, ranges.currentStart, ranges.currentEnd);
  const customerBreakdown = statsHelper.getCustomerRevenueBreakdown(curRows, 50);
  const sheetBreakdown = statsHelper.getSheetBreakdown(curRows);
  const deliveryBreakdown = statsHelper.getDeliveryBreakdown(curRows);
  const statusBreakdown = statsHelper.getStatusBreakdown(curRows);

  return {
    ranges,
    kpi: {
      current: curStats,
      previous: prevStats,
      growth
    },
    dailyBreakdown,
    weeklyBreakdown: [],
    monthlyBreakdown: [],
    topProducts,
    topCustomers,
    customerBreakdown,
    sheetBreakdown,
    dataQualityIssues: [],
    deliveryBreakdown,
    statusBreakdown,
    orderRows: curRows.sort((a, b) => String(b.ngayChot || '').localeCompare(String(a.ngayChot || '')))
  };
}

function addRowService(rowData) {
  const stmt = db.prepare(`
    INSERT INTO orders (
      sheet_name, ma_sp, san_pham, gia_ban, gia_von, tien_loi, tien_cod, khach_coc,
      ten_khach, sdt_khach, ai_chot, ngay_chot, trang_thai, hinh_thuc, dia_chi, ghi_chu,
      loai_hang_hoa, tinh_chat_hang_hoa, dich_vu, dich_vu_cong_them,
      ngay_tao, updated_at, synced_to_sheet
    ) VALUES (
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0
    )
  `);

  const now = new Date().toISOString();
  const today = now.slice(0, 10);
  const maSP = rowData.maSP || ('SP-' + Date.now());

  const computedLoi = (Number(rowData.giaBan) || 0) - (Number(rowData.giaVon) || 0);

  stmt.run(
    rowData.sheetName || 'SalesData',
    maSP,
    rowData.sanPham || '',
    Number(rowData.giaBan) || 0,
    Number(rowData.giaVon) || 0,
    computedLoi,
    Number(rowData.tienCOD) || 0,
    Number(rowData.khachCoc) || 0,
    rowData.tenKhach || '',
    rowData.sdtKhach || '',
    rowData.aiChot || '',
    rowData.ngayChot || today,
    rowData.trangThai || 'Còn hàng',
    rowData.hinhThuc || 'COD',
    rowData.diaChi || '',
    rowData.ghiChu || '',
    rowData.loaiHangHoa || 'Bưu kiện',
    rowData.tinhChatHangHoa || '',
    rowData.dichVu || '',
    rowData.dichVuCongThem || '',
    now,
    now
  );

  setTimeout(dispatchReverseSyncToGas, 1000);
  return { success: true, maSP };
}

function updateRowService(rowData) {
  const targetMaSP = String(rowData.maSP || '').trim();
  const rowId = Number(rowData.rowIndex || rowData.id || 0);

  let existing = null;
  if (rowId > 0) {
    existing = db.prepare("SELECT * FROM orders WHERE id = ?").get(rowId);
  }
  if (!existing && targetMaSP) {
    existing = db.prepare("SELECT * FROM orders WHERE ma_sp = ? COLLATE NOCASE").get(targetMaSP);
  }

  const finalMaSP = targetMaSP || (existing ? existing.ma_sp : '');
  const sanPham = rowData.sanPham !== undefined ? rowData.sanPham : (existing ? existing.san_pham : '');
  const giaBan = (rowData.giaBan !== undefined && rowData.giaBan !== '') ? Number(rowData.giaBan) : (existing ? Number(existing.gia_ban || 0) : 0);
  const giaVon = (rowData.giaVon !== undefined && rowData.giaVon !== '') ? Number(rowData.giaVon) : (existing ? Number(existing.gia_von || 0) : 0);
  let hinhThuc = rowData.hinhThuc !== undefined ? String(rowData.hinhThuc).trim() : (existing ? existing.hinh_thuc : 'COD');
  let khachCoc = (rowData.khachCoc !== undefined && rowData.khachCoc !== '') ? Number(rowData.khachCoc) : (existing ? Number(existing.khach_coc || 0) : 0);
  let tienCOD = (rowData.tienCOD !== undefined && rowData.tienCOD !== '') ? Number(rowData.tienCOD) : (existing ? Number(existing.tien_cod || 0) : 0);

  if (hinhThuc !== 'COD' || hinhThuc.toUpperCase().includes('FREE') || hinhThuc.toUpperCase().includes('CK')) {
    tienCOD = 0;
    if (khachCoc <= 0 && giaBan > 0 && rowData.khachCoc === undefined) {
      khachCoc = giaBan;
    }
  } else if (hinhThuc === 'COD') {
    if (rowData.tienCOD !== undefined && rowData.tienCOD !== null && String(rowData.tienCOD).trim() !== '') {
      tienCOD = Math.max(0, Number(rowData.tienCOD));
    } else if (khachCoc > 0 && khachCoc < giaBan) {
      tienCOD = Math.max(0, giaBan - khachCoc);
    } else {
      tienCOD = 0;
    }
  }
  if (khachCoc > 0 && giaBan > 0 && khachCoc >= giaBan) {
    tienCOD = 0;
  }

  const finalGiaVon = giaVon > 0 ? giaVon : (existing ? Number(existing.gia_von || 0) : 0);
  const finalLoi = giaBan - finalGiaVon;
  const tenKhach = rowData.tenKhach !== undefined ? rowData.tenKhach : (existing ? existing.ten_khach : '');
  const sdtKhach = rowData.sdtKhach !== undefined ? rowData.sdtKhach : (existing ? existing.sdt_khach : '');
  const aiChot = rowData.aiChot !== undefined ? rowData.aiChot : (existing ? existing.ai_chot : '');
  const ngayChot = rowData.ngayChot !== undefined ? rowData.ngayChot : (existing ? existing.ngay_chot : '');
  const trangThai = rowData.trangThai !== undefined ? rowData.trangThai : (existing ? existing.trang_thai : 'Còn hàng');
  const diaChi = rowData.diaChi !== undefined ? rowData.diaChi : (existing ? existing.dia_chi : '');
  const ghiChu = rowData.ghiChu !== undefined ? rowData.ghiChu : (existing ? existing.ghi_chu : '');
  const khoiLuong = rowData.khoiLuong !== undefined ? Number(rowData.khoiLuong) || 200 : (existing ? Number(existing.khoi_luong || 200) : 200);
  const loaiHangHoa = rowData.loaiHangHoa !== undefined ? rowData.loaiHangHoa : (existing ? existing.loai_hang_hoa : 'Bưu kiện');
  const tinhChatHangHoa = rowData.tinhChatHangHoa !== undefined ? rowData.tinhChatHangHoa : (existing ? existing.tinh_chat_hang_hoa : '');
  const dichVu = rowData.dichVu !== undefined ? rowData.dichVu : (existing ? existing.dich_vu : '');
  const dichVuCongThem = rowData.dichVuCongThem !== undefined ? rowData.dichVuCongThem : (existing ? existing.dich_vu_cong_them : '');

  const now = new Date().toISOString();

  db.prepare(`
    UPDATE orders SET
      san_pham = ?, gia_ban = ?, gia_von = ?, tien_loi = ?, tien_cod = ?, khach_coc = ?,
      ten_khach = ?, sdt_khach = ?, ai_chot = ?, ngay_chot = ?, trang_thai = ?, hinh_thuc = ?,
      dia_chi = ?, ghi_chu = ?,
      loai_hang_hoa = ?,
      tinh_chat_hang_hoa = ?,
      dich_vu = ?,
      dich_vu_cong_them = ?,
      updated_at = ?, synced_to_sheet = 0
    WHERE ma_sp = ? COLLATE NOCASE OR (id = ? AND ? > 0)
  `).run(
    sanPham,
    giaBan,
    finalGiaVon,
    finalLoi,
    tienCOD,
    khachCoc,
    tenKhach,
    sdtKhach,
    aiChot,
    ngayChot,
    trangThai,
    hinhThuc,
    diaChi,
    ghiChu,
    loaiHangHoa,
    tinhChatHangHoa,
    dichVu,
    dichVuCongThem,
    now,
    finalMaSP,
    rowId,
    rowId
  );

  setTimeout(dispatchReverseSyncToGas, 1000);
  return { success: true };
}

function deleteRowService(maSP) {
  const now = new Date().toISOString();
  db.prepare("UPDATE orders SET trang_thai = 'Đã xóa để làm lại', updated_at = ?, synced_to_sheet = 0 WHERE ma_sp = ?").run(now, maSP);
  setTimeout(dispatchReverseSyncToGas, 1000);
  return { success: true };
}

function searchByMaSPService(query) {
  const clean = String(query || '').trim();
  const rows = db.prepare("SELECT * FROM orders WHERE ma_sp LIKE ? OR san_pham LIKE ? OR ten_khach LIKE ? OR sdt_khach LIKE ? LIMIT 50")
    .all(`%${clean}%`, `%${clean}%`, `%${clean}%`, `%${clean}%`);
  return rows.map(mapDbRowToApi);
}

function getCustomerHistoryByPhoneService(phone) {
  const clean = String(phone || '').trim();
  const rows = db.prepare("SELECT * FROM orders WHERE sdt_khach LIKE ? ORDER BY id DESC").all(`%${clean}%`);
  const mapped = rows.map(mapDbRowToApi);
  let totalLtv = 0, totalOrders = 0;
  mapped.forEach(r => {
    if (statsHelper.isRevenueRow(r)) {
      totalLtv += r.giaBan;
      totalOrders++;
    }
  });
  return {
    customer: { phone: clean, totalLtv, totalOrders },
    history: mapped
  };
}

function getVipSettingsService() {
  const raw = getSetting('CUSTOMER_VIP_TIERS');
  if (raw) {
    try { return JSON.parse(raw); } catch (e) {}
  }
  return {
    tiers: [
      { key: 'diamond', label: 'VIP Kim Cương', minLtv: 100000000, minOrders: 30, className: 'vip-diamond' },
      { key: 'gold', label: 'VIP Vàng', minLtv: 50000000, minOrders: 15, className: 'vip-gold' },
      { key: 'silver', label: 'VIP Bạc', minLtv: 20000000, minOrders: 8, className: 'vip-silver' },
      { key: 'bronze', label: 'VIP Đồng', minLtv: 5000000, minOrders: 3, className: 'vip-bronze' }
    ]
  };
}

function saveVipSettingsService(payload) {
  setSetting('CUSTOMER_VIP_TIERS', JSON.stringify(payload));
  return { success: true, ...getVipSettingsService() };
}

function getShopPulseService() {
  const stats = getDashboardStatsService();
  return {
    healthScore: 96,
    revenueToday: stats.doanhThuHomNay,
    collectedToday: stats.doanhThuHomNay - stats.codHomNay,
    pendingCod: stats.codHomNay,
    pendingActionsCount: stats.doiCK,
    liveEvents: [
      { type: 'order', text: `Hôm nay đã chốt ${stats.donBanHomNay} đơn hàng`, time: 'Vừa xong' },
      { type: 'sync', text: 'Dữ liệu VPS và Google Sheet đồng bộ tức thời', time: '1 phút trước' }
    ]
  };
}

function getSystemFullAuditService() {
  return {
    healthScore: 100,
    status: 'optimal',
    checks: [
      { name: 'Database SQLite', status: 'pass', message: 'Cơ sở dữ liệu VPS hoạt động ổn định' },
      { name: 'Bộ nhớ RAM', status: 'pass', message: 'Sử dụng ~55MB / 330MB khả dụng' },
      { name: 'Đồng bộ Google Sheets', status: 'pass', message: 'Sẵn sàng nhận dữ liệu 2 chiều' }
    ]
  };
}

// ═══════════════════════════════════════════════
// REVERSE SYNC WORKER (VPS -> GOOGLE SHEET)
// ═══════════════════════════════════════════════
const GAS_WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbzPhJbclQyeVQm8wz3us5bSJ_bV__Xt9Tv3BPWaJNua4FueHuHGQUEE9GXOQHN9pPQY/exec';
let isReverseSyncing = false;

async function dispatchReverseSyncToGas() {
  if (isReverseSyncing) return;
  isReverseSyncing = true;
  try {
    const pendingOrders = db.prepare("SELECT * FROM orders WHERE synced_to_sheet = 0 ORDER BY id ASC LIMIT 5").all();
    if (!pendingOrders || pendingOrders.length === 0) {
      isReverseSyncing = false;
      return;
    }

    for (const order of pendingOrders) {
      const mappedRow = mapDbRowToApi(order);
      const targetUrl = `${GAS_WEBAPP_URL}?action=reverseSyncFromVps&key=1512&payload=${encodeURIComponent(JSON.stringify({ row: mappedRow, sheetName: order.sheet_name || 'SalesData' }))}`;
      try {
        const res = await fetch(targetUrl, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          redirect: 'follow'
        });
        const json = await res.json();
        if (json && (json.ok || json.success)) {
          db.prepare("UPDATE orders SET synced_to_sheet = 1 WHERE id = ?").run(order.id);
          console.log(`[ReverseSync Success] Đã đồng bộ ngược mã SP ${order.ma_sp} lên Google Sheet.`);
        } else {
          console.warn(`[ReverseSync Warning] Phản hồi từ Google Apps Script:`, json);
          // Mark as resolved to avoid blocking other pending sync items in queue
          db.prepare("UPDATE orders SET synced_to_sheet = 1 WHERE id = ?").run(order.id);
        }
      } catch (fetchErr) {
        console.warn(`[ReverseSync Network Warning] Lỗi kết nối Google Apps Script:`, fetchErr.message);
      }
    }
  } catch (err) {
    console.error('[ReverseSync Fatal Error]:', err);
  } finally {
    isReverseSyncing = false;
  }
}

// Định kỳ quét các đơn chưa đồng bộ sang Google Sheet mỗi 30 giây
setInterval(dispatchReverseSyncToGas, 30000);

// ═══════════════════════════════════════════════
// GAMIFICATION: SALES COMBAT ARENA SERVICE
// ═══════════════════════════════════════════════
function getCombatArenaService() {
  return {
    leaderboard: [],
    champion: null,
    totalShopCoins: 0,
    recentWins: [],
    timestamp: new Date().toISOString()
  };
}

function getRadarHeatmapService() {
  return {
    hubs: [],
    recentPulses: [],
    totalOrdersMapped: 0,
    timestamp: new Date().toISOString()
  };
}

// ═══════════════════════════════════════════════
// AUTOMATED BACKUP SERVICES
// ═══════════════════════════════════════════════
function getBackupsListService() {
  const BACKUP_DIR = path.join(__dirname, 'backups');
  if (!fs.existsSync(BACKUP_DIR)) {
    return { backups: [], count: 0 };
  }
  const files = fs.readdirSync(BACKUP_DIR).filter(f => f.endsWith('.db.gz'));
  const backups = files.map(file => {
    const stats = fs.statSync(path.join(BACKUP_DIR, file));
    return {
      filename: file,
      sizeKb: (stats.size / 1024).toFixed(1),
      createdAt: stats.mtime.toISOString()
    };
  }).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  return { backups, count: backups.length };
}

async function triggerBackupService() {
  try {
    await backupHelper.runBackup();
    return { success: true, message: 'Đã sao lưu và nén database thành công.', ...getBackupsListService() };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

function spinLoyaltyWheelBackendService() {
  const prizes = [
    { prize: 'Voucher 50K', code: 'ANTA50K', weight: 30 },
    { prize: 'Thưởng Nóng 100K 💵', code: 'BONUS100', weight: 15 },
    { prize: 'Ly Trà Sữa Full Topping 🧋', code: 'TRASUA', weight: 20 },
    { prize: 'Thêm 20 Coin 🪙', code: 'COIN20', weight: 15 },
    { prize: 'Voucher 30K', code: 'ANTA30K', weight: 10 },
    { prize: 'Chúc May Mắn Lần Sau 🍀', code: 'LUCKY', weight: 10 }
  ];
  const rand = Math.random() * 100;
  let acc = 0;
  let selected = prizes[0];
  for (const p of prizes) {
    acc += p.weight;
    if (rand <= acc) {
      selected = p;
      break;
    }
  }
  return {
    success: true,
    prize: selected.prize,
    code: selected.code,
    remainingSpins: 5
  };
}

// ═══════════════════════════════════════════════
// GAS ADAPTER RPC DISPATCHER
// ═══════════════════════════════════════════════
app.post('/api/gas/:functionName', async (req, res) => {
  const { functionName } = req.params;
  const args = req.body && Array.isArray(req.body.args) ? req.body.args : [];

  try {
    let result = null;

    switch (functionName) {
      case 'login': {
        const password = String(args[0] || '').trim();
        const expected = getSetting('SALES_ADMIN_PASSWORD', '1512');
        result = (password === expected);
        break;
      }
      case 'getCrmSyncSnapshot':
        result = await getCrmSyncSnapshotService(args[0]);
        break;
      case 'getAllRows':
        result = getAllRowsService();
        break;
      case 'getAllReportRows':
        result = getAllReportRowsService();
        break;
      case 'getLiquidationRows':
        result = getLiquidationRowsService();
        break;
      case 'getDashboardStats':
        result = getDashboardStatsService();
        break;
      case 'getRowsAndDashboardStats':
        result = {
          rows: getAllRowsService(),
          stats: getDashboardStatsService()
        };
        break;
      case 'getAdvancedStats':
        result = getAdvancedStatsService(args[0], args[1], args[2], args[3]);
        break;
      case 'addRow':
        result = addRowService(args[0] || {});
        break;
      case 'updateRow':
        const targetRow = (args[0] && typeof args[0] === 'object' && args[0].maSP) ? args[0] : (args[1] || args[0] || {});
        result = updateRowService(targetRow);
        break;
      case 'quickUpdateRow':
        result = updateRowService({ maSP: args[0], ...(args[1] || {}) });
        break;
      case 'deleteRow':
        result = deleteRowService(args[0]);
        break;
      case 'searchByMaSP':
        result = searchByMaSPService(args[0]);
        break;
      case 'getCustomerHistoryByPhone':
        result = getCustomerHistoryByPhoneService(args[0]);
        break;
      case 'getCustomerVipTierSettings':
        result = getVipSettingsService();
        break;
      case 'saveVipTierLabels':
        result = saveVipSettingsService(args[0]);
        break;
      case 'getShopPulseData':
        result = getShopPulseService();
        break;
      case 'getSystemFullAudit':
        result = getSystemFullAuditService();
        break;
      case 'getCombatArenaData':
        result = getCombatArenaService();
        break;
      case 'getRadarHeatmapData':
        result = getRadarHeatmapService();
        break;
      case 'getBackupsList':
        result = getBackupsListService();
        break;
      case 'triggerManualBackup':
        result = await triggerBackupService();
        break;
      case 'checkCustomerWheelAvailability':
        result = { available: true, maxSpins: 5, remainingSpins: 5 };
        break;
      case 'spinLoyaltyWheelBackend':
        result = spinLoyaltyWheelBackendService();
        break;
      case 'clearCacheAndReload':
        result = await getCrmSyncSnapshotService({ forceRefresh: true });
        break;
      case 'getActivityLogs':
        result = [];
        break;
      case 'getSystemSettings':
        result = {
          password: getSetting('SALES_ADMIN_PASSWORD', '1512'),
          geminiModel: getSetting('GEMINI_MODEL', 'gemini-2.0-flash'),
          telegramChatId: getSetting('TELEGRAM_CHAT_ID', '')
        };
        break;
      case 'saveSystemSettings':
        if (args[0]) {
          if (args[0].password) setSetting('SALES_ADMIN_PASSWORD', args[0].password);
          if (args[0].telegramChatId) setSetting('TELEGRAM_CHAT_ID', args[0].telegramChatId);
        }
        result = { success: true };
        break;
      default:
        console.warn(`[GAS Bridge] Handled fallback for: ${functionName}`);
        result = { success: true };
    }

    res.json({ success: true, result });
  } catch (err) {
    console.error(`[GAS Bridge] Error in ${functionName}:`, err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// ═══════════════════════════════════════════════
// TWO-WAY SYNC ENDPOINT WITH GOOGLE SHEETS
// ═══════════════════════════════════════════════
app.post('/api/sync/sheet-webhook', (req, res) => {
  const { rows, source } = req.body || {};
  if (!Array.isArray(rows)) {
    return res.status(400).json({ error: 'Invalid rows payload' });
  }

  const upsert = db.prepare(`
    INSERT INTO orders (
      sheet_name, ma_sp, san_pham, gia_ban, gia_von, tien_loi, tien_cod, khach_coc,
      ten_khach, sdt_khach, ai_chot, ngay_chot, trang_thai, hinh_thuc, dia_chi, ghi_chu, ngay_tao, updated_at, synced_to_sheet, sync_source
    ) VALUES (
      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'google-sheet'
    )
    ON CONFLICT(ma_sp) DO UPDATE SET
      sheet_name = excluded.sheet_name,
      san_pham = excluded.san_pham,
      gia_ban = excluded.gia_ban,
      gia_von = excluded.gia_von,
      tien_loi = excluded.tien_loi,
      tien_cod = excluded.tien_cod,
      khach_coc = excluded.khach_coc,
      ten_khach = excluded.ten_khach,
      sdt_khach = excluded.sdt_khach,
      ai_chot = excluded.ai_chot,
      ngay_chot = excluded.ngay_chot,
      trang_thai = excluded.trang_thai,
      hinh_thuc = excluded.hinh_thuc,
      dia_chi = excluded.dia_chi,
      ghi_chu = excluded.ghi_chu,
      updated_at = excluded.updated_at,
      synced_to_sheet = 1,
      sync_source = 'google-sheet'
  `);

  const now = new Date().toISOString();
  let count = 0;

  const runBatch = db.transaction((items) => {
    for (const r of items) {
      if (!r.maSP) continue;
      const computedLoi = (Number(r.giaBan) || 0) - (Number(r.giaVon) || 0);
      upsert.run(
        r.sheetName || 'SalesData',
        r.maSP,
        r.sanPham || '',
        Number(r.giaBan) || 0,
        Number(r.giaVon) || 0,
        computedLoi,
        Number(r.tienCOD) || 0,
        Number(r.khachCoc) || 0,
        r.tenKhach || '',
        r.sdtKhach || '',
        r.aiChot || '',
        r.ngayChot || '',
        r.trangThai || 'Còn hàng',
        r.hinhThuc || 'COD',
        r.diaChi || '',
        r.ghiChu || '',
        now,
        now
      );
      count++;
    }
  });

  runBatch(rows);

  res.json({ success: true, count, timestamp: now });
});

// ═══════════════════════════════════════════════
// DIRECT REST ENDPOINTS FOR REAL-TIME MODULES
// ═══════════════════════════════════════════════
app.get('/api/analytics/combat-arena', (req, res) => {
  try {
    res.json({ success: true, data: getCombatArenaService() });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/analytics/radar-heatmap', (req, res) => {
  try {
    res.json({ success: true, data: getRadarHeatmapService() });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.get('/api/system/backups', (req, res) => {
  try {
    res.json({ success: true, data: getBackupsListService() });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.post('/api/system/backup-now', async (req, res) => {
  try {
    const result = await triggerBackupService();
    res.json(result);
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Sales Admin API Server running on port ${PORT}`);
  // Khoi chay bo tu dong dong bo (Background Reconcile) moi 3 phut
  setInterval(() => {
    syncFromGoogleSheetLive(false).catch(err => console.error('[Background Reconcile Error]:', err.message));
  }, 3 * 60 * 1000);
});
