// Port of StatsService logic to Node.js / SQLite
function stripVietnameseMarks(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D');
}

function normalizeDate(d) {
  if (!d) return '';
  if (typeof d === 'string') return d.slice(0, 10);
  try {
    return new Date(d).toISOString().slice(0, 10);
  } catch (e) {
    return '';
  }
}

function isSoldInternal(s) {
  const raw = String(s || '').trim();
  const l = stripVietnameseMarks(raw).toLowerCase();
  if (l.includes('chua ban') || l.includes('chuaban')) return false;
  return l === 'da ban' || l.includes('da ban') || l === 'ban' || l.includes('ban') || l === 'het hang' || l.includes('het') || l.includes('da ban de lam lai');
}

function isWaitingInternal(s) {
  const raw = String(s || '').trim();
  const l = stripVietnameseMarks(raw).toLowerCase();
  return l.includes('doi') || l.includes('ck') || l.includes('cho') || l.includes('thanh toan');
}

function isDeletedInternal(s) {
  const raw = String(s || '').trim();
  const l = stripVietnameseMarks(raw).toLowerCase();
  return l.includes('xoa') || l.includes('huy') || l.includes('bom') || l.includes('boom') || l.includes('hoan') || l.includes('tra');
}

function isInStockInternal(s) {
  const raw = String(s || '').trim();
  const l = stripVietnameseMarks(raw).toLowerCase();
  if (l === '' || l === 'con hang' || l === 'chua ban' || l === 'chuaban' || l.includes('con') || l.includes('chua')) return true;
  return !isSoldInternal(s) && !isWaitingInternal(s) && !isDeletedInternal(s);
}

function isRevenueRow(row) {
  if (!row) return false;
  const tt = row.trangThai || row.trang_thai || '';
  if (isDeletedInternal(tt)) return false;
  return isSoldInternal(tt) || isWaitingInternal(tt);
}

function calculateGrowthPercentage(cur, prev) {
  if (!prev || prev === 0) {
    return cur > 0 ? 100 : 0;
  }
  return Math.round(((cur - prev) / prev) * 100);
}

function getPeriodDates(filterType, customStart, customEnd) {
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const fmt = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

  let currentStart = '', currentEnd = '', prevStart = '', prevEnd = '';

  if (filterType === 'today') {
    currentStart = currentEnd = fmt(now);
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    prevStart = prevEnd = fmt(yesterday);
  } else if (filterType === 'yesterday') {
    const y = new Date(now);
    y.setDate(now.getDate() - 1);
    currentStart = currentEnd = fmt(y);
    const y2 = new Date(now);
    y2.setDate(now.getDate() - 2);
    prevStart = prevEnd = fmt(y2);
  } else if (filterType === '7days') {
    const s = new Date(now);
    s.setDate(now.getDate() - 6);
    currentStart = fmt(s);
    currentEnd = fmt(now);
    const ps = new Date(s);
    ps.setDate(s.getDate() - 7);
    const pe = new Date(s);
    pe.setDate(s.getDate() - 1);
    prevStart = fmt(ps);
    prevEnd = fmt(pe);
  } else if (filterType === '30days') {
    const s = new Date(now);
    s.setDate(now.getDate() - 29);
    currentStart = fmt(s);
    currentEnd = fmt(now);
    const ps = new Date(s);
    ps.setDate(s.getDate() - 30);
    const pe = new Date(s);
    pe.setDate(s.getDate() - 1);
    prevStart = fmt(ps);
    prevEnd = fmt(pe);
  } else if (filterType === 'month') {
    currentStart = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`;
    currentEnd = fmt(now);
    const lastMonth = new Date(now.getFullYear(), now.getMonth(), 0);
    prevStart = `${lastMonth.getFullYear()}-${pad(lastMonth.getMonth() + 1)}-01`;
    prevEnd = fmt(lastMonth);
  } else if (filterType === 'custom' && customStart && customEnd) {
    currentStart = customStart;
    currentEnd = customEnd;
    const diff = Math.abs(new Date(customEnd) - new Date(customStart));
    const ps = new Date(new Date(customStart).getTime() - diff);
    const pe = new Date(new Date(customStart).getTime() - 86400000);
    prevStart = fmt(ps);
    prevEnd = fmt(pe);
  } else {
    // Default to month
    currentStart = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`;
    currentEnd = fmt(now);
    prevStart = currentStart;
    prevEnd = currentEnd;
  }

  return { currentStart, currentEnd, prevStart, prevEnd };
}

function calculateSummary(rows) {
  const revenueRows = (rows || []).filter(isRevenueRow);
  let revenue = 0, cost = 0, profit = 0, cod = 0, deposit = 0, soldProducts = 0, pendingProducts = 0;
  const customerMap = {};

  revenueRows.forEach(r => {
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);
    const khachCoc = Number(r.khachCoc ?? r.khach_coc) || 0;
    const tienCOD = Number(r.tienCOD ?? r.tien_cod) || 0;
    const tt = r.trangThai || r.trang_thai || '';
    const ht = r.hinhThuc || r.hinh_thuc || 'COD';

    const isWaiting = isWaitingInternal(tt);

    revenue += giaBan;
    cost += giaVon;
    profit += tienLoi;
    deposit += khachCoc;
    if (ht === 'COD') {
      cod += tienCOD;
    }

    if (isWaiting) pendingProducts++;
    else soldProducts++;

    const custKey = String(r.sdtKhach || r.sdt_khach || r.tenKhach || r.ten_khach || '').trim();
    if (custKey) customerMap[custKey] = true;
  });

  const orders = revenueRows.length;
  const customers = Object.keys(customerMap).length;
  const aov = orders > 0 ? Math.round(revenue / orders) : 0;
  return { revenue, cost, profit, cod, deposit, orders, customers, soldProducts, pendingProducts, aov };
}

function getDailyStatsBreakdown(rows, startDate, endDate) {
  const map = {};
  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const d = r.ngayChot || r.ngay_chot;
    if (!d) return;
    if (startDate && d < startDate) return;
    if (endDate && d > endDate) return;

    if (!map[d]) {
      map[d] = { date: d, revenue: 0, profit: 0, orders: 0, cost: 0 };
    }
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);

    map[d].revenue += giaBan;
    map[d].cost += giaVon;
    map[d].profit += tienLoi;
    map[d].orders++;
  });

  return Object.values(map).sort((a, b) => a.date.localeCompare(b.date));
}

function getCustomerRevenueBreakdown(rows, limit = 50) {
  const map = {};
  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const name = String(r.tenKhach || r.ten_khach || 'Khách vãng lai').trim();
    const phone = String(r.sdtKhach || r.sdt_khach || '').trim();
    const key = phone || name;
    if (!map[key]) {
      map[key] = { name, phone, orders: 0, revenue: 0, profit: 0 };
    }
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);

    map[key].revenue += giaBan;
    map[key].profit += tienLoi;
    map[key].orders++;
  });

  return Object.values(map).sort((a, b) => b.revenue - a.revenue).slice(0, limit);
}

function getSheetBreakdown(rows) {
  const map = {};
  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const sn = r.sheetName || r.sheet_name || 'SalesData';
    if (!map[sn]) {
      map[sn] = { sheetName: sn, orders: 0, revenue: 0, profit: 0 };
    }
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);

    map[sn].revenue += giaBan;
    map[sn].profit += tienLoi;
    map[sn].orders++;
  });

  return Object.values(map).sort((a, b) => b.revenue - a.revenue);
}

function getTopProducts(rows, limit = 10) {
  const prodMap = {};
  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const maSP = String(r.maSP || r.ma_sp || '').trim();
    const sanPham = String(r.sanPham || r.san_pham || '').trim();
    const id = sanPham || maSP || 'Chưa đặt tên';
    if (!id) return;

    if (!prodMap[id]) {
      prodMap[id] = {
        maSP: maSP || id,
        productName: id,
        name: id,
        quantity: 0,
        count: 0,
        revenue: 0,
        profit: 0
      };
    }
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);

    prodMap[id].quantity += 1;
    prodMap[id].count += 1;
    prodMap[id].revenue += giaBan;
    prodMap[id].profit += tienLoi;
  });

  return Object.values(prodMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit);
}

function getTopCustomers(rows, limit = 10) {
  const custMap = {};
  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const name = String(r.tenKhach || r.ten_khach || '').trim();
    const phone = String(r.sdtKhach || r.sdt_khach || '').trim();
    if (!name && !phone) return;

    const key = phone || name;
    if (!custMap[key]) {
      custMap[key] = {
        name: name || 'Khách ẩn danh',
        phone: phone || '—',
        orders: 0,
        count: 0,
        revenue: 0,
        profit: 0
      };
    }
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    const giaVon = Number(r.giaVon ?? r.gia_von ?? r.giaNhap ?? r.gia_nhap) || 0;
    const tienLoi = (r.tienLoi !== undefined && r.tienLoi !== null && r.tienLoi !== '')
      ? Number(r.tienLoi)
      : (giaBan - giaVon);

    custMap[key].orders += 1;
    custMap[key].count += 1;
    custMap[key].revenue += giaBan;
    custMap[key].profit += tienLoi;
  });

  return Object.values(custMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit);
}

function getDeliveryBreakdown(rows) {
  let codCount = 0;
  let codRevenue = 0;
  let freeCount = 0;
  let freeRevenue = 0;

  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const hinhThuc = stripVietnameseMarks(String(r.hinhThuc || r.hinh_thuc || '')).toUpperCase();
    const giaBan = Number(r.giaBan ?? r.gia_ban) || 0;
    if (hinhThuc.includes('COD')) {
      codCount++;
      codRevenue += giaBan;
    } else {
      freeCount++;
      freeRevenue += giaBan;
    }
  });

  return {
    cod: { count: codCount, revenue: codRevenue },
    freeship: { count: freeCount, revenue: freeRevenue }
  };
}

function getStatusBreakdown(rows) {
  let inStock = 0;
  let sold = 0;
  let pending = 0;

  (rows || []).forEach(r => {
    if (!isRevenueRow(r)) return;
    const st = r.trangThai || r.trang_thai;
    if (isSoldInternal(st)) {
      sold++;
    } else if (isWaitingInternal(st)) {
      pending++;
    } else {
      inStock++;
    }
  });

  return { inStock, sold, pending };
}

function applyReportFilters(rows, filters) {
  if (!filters || typeof filters !== 'object') return rows;
  const customerNeedle = stripVietnameseMarks(String(filters.customer || '').toLowerCase()).trim();
  const status = String(filters.status || '').trim();
  const sheetName = String(filters.sheetName || '').trim();
  const orderType = String(filters.orderType || '').trim();

  return (rows || []).filter(r => {
    if (sheetName && (r.sheetName || r.sheet_name) !== sheetName) return false;
    if (status && (r.trangThai || r.trang_thai) !== status) return false;
    if (orderType && (r.hinhThuc || r.hinh_thuc) !== orderType) return false;

    if (customerNeedle) {
      const haystack = stripVietnameseMarks([
        r.tenKhach || r.ten_khach,
        r.sdtKhach || r.sdt_khach,
        r.maSP || r.ma_sp,
        r.sanPham || r.san_pham,
        r.aiChot || r.ai_chot
      ].join(' ').toLowerCase()).trim();
      if (!haystack.includes(customerNeedle)) return false;
    }
    return true;
  });
}

module.exports = {
  stripVietnameseMarks,
  normalizeDate,
  isSoldInternal,
  isWaitingInternal,
  isDeletedInternal,
  isInStockInternal,
  isRevenueRow,
  calculateGrowthPercentage,
  getPeriodDates,
  calculateSummary,
  getDailyStatsBreakdown,
  getCustomerRevenueBreakdown,
  getSheetBreakdown,
  getTopProducts,
  getTopCustomers,
  getDeliveryBreakdown,
  getStatusBreakdown,
  applyReportFilters
};
