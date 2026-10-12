// ============================================================
// SALES ADMIN SYSTEM - StatsService.js
// Service Layer for Advanced Revenue Statistics & Reporting
// ============================================================

/**
 * Trả về thống kê nâng cao theo các khoảng thời gian lọc động
 * @param {string} filterType - Loại bộ lọc ('today', 'yesterday', '7days', '30days', 'month', 'last_month', 'quarter', 'year', 'custom')
 * @param {string} [customStart] - Ngày bắt đầu tùy chọn (dạng yyyy-MM-dd)
 * @param {string} [customEnd] - Ngày kết thúc tùy chọn (dạng yyyy-MM-dd)
 * @return {Object} Dữ liệu KPI, Biểu đồ và Phân tích chuyên sâu
 */
function getAdvancedStats(filterType, customStart, customEnd, filters) {
  const rows = applyReportFilters_(getAllReportRows(), filters || {});
  const ranges = getPeriodRanges_(filterType, customStart, customEnd);

  const curRows = [];
  const prevRows = [];

  rows.forEach(r => {
    if (!isRevenueRow_(r)) return;

    const date = r.ngayChot;
    if (!date) return;

    if (date >= ranges.currentStart && date <= ranges.currentEnd) {
      curRows.push(r);
    } else if (date >= ranges.prevStart && date <= ranges.prevEnd) {
      prevRows.push(r);
    }
  });

  // Tính KPI kỳ này
  const curStats = calculateStatsSummary_(curRows);
  // Tính KPI kỳ trước
  const prevStats = calculateStatsSummary_(prevRows);

  // Tính % tăng trưởng (growth rate)
  const growth = {
    revenue: calculateGrowthPercentage_(curStats.revenue, prevStats.revenue),
    profit: calculateGrowthPercentage_(curStats.profit, prevStats.profit),
    orders: calculateGrowthPercentage_(curStats.orders, prevStats.orders),
    aov: calculateGrowthPercentage_(curStats.aov, prevStats.aov),
    soldProducts: calculateGrowthPercentage_(curStats.soldProducts, prevStats.soldProducts)
  };

  // Thống kê doanh số theo các chiều chi tiết (vẽ biểu đồ và lập bảng báo cáo)
  const dailyStats = getDailyStatsBreakdown_(curRows, ranges.currentStart, ranges.currentEnd);
  const weeklyStats = getWeeklyStatsBreakdown_(curRows, ranges.currentStart, ranges.currentEnd);
  const monthlyStats = getMonthlyStatsBreakdown_(curRows, ranges.currentStart, ranges.currentEnd);

  // Phân tích Top sản phẩm bán chạy nhất (Top 10)
  const topProducts = getTopProducts_(curRows, 10);

  // Phân tích Top khách hàng mua nhiều nhất (Top 10)
  const topCustomers = getTopCustomers_(curRows, 10);

  const customerBreakdown = getCustomerRevenueBreakdown_(curRows, 50);
  const sheetBreakdown = getSheetBreakdown_(curRows);
  const qualityRows = rows.filter((r) => !r.ngayChot || (r.ngayChot >= ranges.currentStart && r.ngayChot <= ranges.currentEnd));
  const dataQualityIssues = getDataQualityIssues_(qualityRows, 50);

  // Phân tích theo hình thức giao hàng
  const deliveryBreakdown = getDeliveryBreakdown_(curRows);

  // Phân tích theo trạng thái sản phẩm
  const statusBreakdown = getStatusBreakdown_(curRows);

  return {
    ranges,
    kpi: {
      current: curStats,
      previous: prevStats,
      growth
    },
    dailyBreakdown: dailyStats,
    weeklyBreakdown: weeklyStats,
    monthlyBreakdown: monthlyStats,
    topProducts,
    topCustomers,
    customerBreakdown,
    sheetBreakdown,
    dataQualityIssues,
    deliveryBreakdown,
    statusBreakdown,
    orderRows: curRows.sort((a, b) => String(b.ngayChot || '').localeCompare(String(a.ngayChot || '')))
  };
}

function applyReportFilters_(rows, filters) {
  const customerNeedle = normalizeTextForFilter_(filters.customer || '');
  const status = String(filters.status || '').trim();
  const sheetName = String(filters.sheetName || '').trim();
  const orderType = String(filters.orderType || '').trim();

  return rows.filter((row) => {
    if (sheetName && row.sourceSheet !== sheetName) return false;
    if (status && row.trangThai !== status && row.trangThaiGoc !== status) return false;
    if (orderType && row.hinhThuc !== orderType && row.loaiDon !== orderType && row.sourceSheet !== orderType) return false;

    if (customerNeedle) {
      const haystack = normalizeTextForFilter_([
        row.tenKhach,
        row.sdtKhach,
        row.maSP,
        row.sanPham,
        row.aiChot
      ].join(' '));
      if (!haystack.includes(customerNeedle)) return false;
    }

    return true;
  });
}

function normalizeTextForFilter_(value) {
  return stripVietnameseMarks_(String(value || '').toLowerCase()).replace(/\s+/g, ' ').trim();
}

/**
 * Trả về mốc ngày bắt đầu và kết thúc của kỳ hiện tại và kỳ trước để so sánh
 * @private
 */
function getPeriodRanges_(filterType, customStart, customEnd) {
  const now = new Date();
  const timeZone = Session.getScriptTimeZone();
  const todayStr = Utilities.formatDate(now, timeZone, 'yyyy-MM-dd');
  const today = new Date(todayStr);

  let currentStart, currentEnd;
  let prevStart, prevEnd;

  switch (filterType) {
    case 'today':
      currentStart = currentEnd = todayStr;
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000);
      prevStart = prevEnd = Utilities.formatDate(yesterday, timeZone, 'yyyy-MM-dd');
      break;

    case 'yesterday':
      const yest = new Date(today.getTime() - 24 * 60 * 60 * 1000);
      currentStart = currentEnd = Utilities.formatDate(yest, timeZone, 'yyyy-MM-dd');
      const dayBeforeYest = new Date(today.getTime() - 2 * 24 * 60 * 60 * 1000);
      prevStart = prevEnd = Utilities.formatDate(dayBeforeYest, timeZone, 'yyyy-MM-dd');
      break;

    case '7days':
      const d7 = new Date(today.getTime() - 6 * 24 * 60 * 60 * 1000);
      currentStart = Utilities.formatDate(d7, timeZone, 'yyyy-MM-dd');
      currentEnd = todayStr;

      const p7Start = new Date(d7.getTime() - 7 * 24 * 60 * 60 * 1000);
      const p7End = new Date(d7.getTime() - 1 * 24 * 60 * 60 * 1000);
      prevStart = Utilities.formatDate(p7Start, timeZone, 'yyyy-MM-dd');
      prevEnd = Utilities.formatDate(p7End, timeZone, 'yyyy-MM-dd');
      break;

    case '30days':
      const d30 = new Date(today.getTime() - 29 * 24 * 60 * 60 * 1000);
      currentStart = Utilities.formatDate(d30, timeZone, 'yyyy-MM-dd');
      currentEnd = todayStr;

      const p30Start = new Date(d30.getTime() - 30 * 24 * 60 * 60 * 1000);
      const p30End = new Date(d30.getTime() - 1 * 24 * 60 * 60 * 1000);
      prevStart = Utilities.formatDate(p30Start, timeZone, 'yyyy-MM-dd');
      prevEnd = Utilities.formatDate(p30End, timeZone, 'yyyy-MM-dd');
      break;

    case 'month':
      const y = today.getFullYear();
      const m = today.getMonth();
      currentStart = Utilities.formatDate(new Date(y, m, 1), timeZone, 'yyyy-MM-dd');
      currentEnd = todayStr;

      prevStart = Utilities.formatDate(new Date(y, m - 1, 1), timeZone, 'yyyy-MM-dd');
      const prevMonthEnd = new Date(y, m, 0); 
      const correspondingDay = Math.min(today.getDate(), prevMonthEnd.getDate());
      prevEnd = Utilities.formatDate(new Date(y, m - 1, correspondingDay), timeZone, 'yyyy-MM-dd');
      break;

    case 'last_month':
      const yL = today.getFullYear();
      const mL = today.getMonth();
      currentStart = Utilities.formatDate(new Date(yL, mL - 1, 1), timeZone, 'yyyy-MM-dd');
      currentEnd = Utilities.formatDate(new Date(yL, mL, 0), timeZone, 'yyyy-MM-dd');

      prevStart = Utilities.formatDate(new Date(yL, mL - 2, 1), timeZone, 'yyyy-MM-dd');
      prevEnd = Utilities.formatDate(new Date(yL, mL - 1, 0), timeZone, 'yyyy-MM-dd');
      break;

    case 'quarter':
      const yQ = today.getFullYear();
      const mQ = today.getMonth();
      const qStartMonth = Math.floor(mQ / 3) * 3;
      currentStart = Utilities.formatDate(new Date(yQ, qStartMonth, 1), timeZone, 'yyyy-MM-dd');
      currentEnd = todayStr;

      prevStart = Utilities.formatDate(new Date(yQ, qStartMonth - 3, 1), timeZone, 'yyyy-MM-dd');
      const diffDays = Math.round((today.getTime() - new Date(yQ, qStartMonth, 1).getTime()) / (24 * 60 * 60 * 1000));
      const pqStart = new Date(yQ, qStartMonth - 3, 1);
      const pqEnd = new Date(pqStart.getTime() + diffDays * 24 * 60 * 60 * 1000);
      prevEnd = Utilities.formatDate(pqEnd, timeZone, 'yyyy-MM-dd');
      break;

    case 'year':
      const yY = today.getFullYear();
      currentStart = Utilities.formatDate(new Date(yY, 0, 1), timeZone, 'yyyy-MM-dd');
      currentEnd = todayStr;

      prevStart = Utilities.formatDate(new Date(yY - 1, 0, 1), timeZone, 'yyyy-MM-dd');
      const yYDiffDays = Math.round((today.getTime() - new Date(yY, 0, 1).getTime()) / (24 * 60 * 60 * 1000));
      const pyStart = new Date(yY - 1, 0, 1);
      const pyEnd = new Date(pyStart.getTime() + yYDiffDays * 24 * 60 * 60 * 1000);
      prevEnd = Utilities.formatDate(pyEnd, timeZone, 'yyyy-MM-dd');
      break;

    case 'custom':
      currentStart = customStart;
      currentEnd = customEnd;

      const cs = new Date(customStart);
      const ce = new Date(customEnd);
      const diffMs = ce.getTime() - cs.getTime();
      const diffTime = diffMs >= 0 ? diffMs : 0;

      const ps = new Date(cs.getTime() - diffTime - 24 * 60 * 60 * 1000);
      const pe = new Date(cs.getTime() - 24 * 60 * 60 * 1000);
      prevStart = Utilities.formatDate(ps, timeZone, 'yyyy-MM-dd');
      prevEnd = Utilities.formatDate(pe, timeZone, 'yyyy-MM-dd');
      break;

    default:
      currentStart = currentEnd = prevStart = prevEnd = todayStr;
  }

  return { currentStart, currentEnd, prevStart, prevEnd };
}

/**
 * Tính toán tổng hợp KPI từ các dòng dữ liệu
 * @private
 */
function calculateStatsSummary_(rows) {
  const revenueRows = rows.filter(isRevenueRow_);
  let revenue = 0;
  let cost = 0;
  let profit = 0;
  let cod = 0;
  let deposit = 0;
  let soldProducts = 0;
  let pendingProducts = 0;

  const customerMap = {};

  revenueRows.forEach(r => {
    const isWaiting = isWaitingInternal_(r.trangThai);

    revenue += r.giaBan || 0;
    cost += r.giaVon || 0;
    profit += r.tienLoi || 0;
    deposit += r.khachCoc || 0;
    if (r.hinhThuc === 'COD') {
      cod += r.tienCOD || 0;
    }

    if (isWaiting) pendingProducts++;
    else soldProducts++;

    const customerKey = String(r.sdtKhach || r.tenKhach || '').trim();
    if (customerKey) customerMap[customerKey] = true;
  });

  const orders = revenueRows.length;
  const customers = Object.keys(customerMap).length;
  const aov = orders > 0 ? Math.round(revenue / orders) : 0;

  return {
    revenue,
    cost,
    profit,
    cod,
    deposit,
    orders,
    customers,
    aov,
    soldProducts,
    pendingProducts
  };
}



/**
 * Tích lũy số liệu thống kê cho dòng doanh thu vào đối tượng mục tiêu
 * @private
 */
function aggregateStatsRow_(target, r) {
  if (isRevenueRow_(r)) {
    target.revenue += r.giaBan || 0;
    target.cost += r.giaVon || 0;
    target.profit += r.tienLoi || 0;
    target.deposit += r.khachCoc || 0;
    if (r.hinhThuc === 'COD') {
      target.cod += r.tienCOD || 0;
    }
    target.orders += 1;
  }
}

/**
 * Trả về danh sách phân tích doanh thu theo ngày chi tiết (không bị thiếu ngày)
 * @private
 */
function getDailyStatsBreakdown_(rows, startDateStr, endDateStr) {
  const dailyData = {};
  const start = new Date(startDateStr);
  const end = new Date(endDateStr);
  const timeZone = Session.getScriptTimeZone();

  let temp = new Date(start);
  while (temp <= end) {
    const key = Utilities.formatDate(temp, timeZone, 'yyyy-MM-dd');
    dailyData[key] = { date: key, label: key, revenue: 0, cost: 0, profit: 0, cod: 0, deposit: 0, orders: 0 };
    temp.setDate(temp.getDate() + 1);
  }

  rows.forEach(r => {
    const date = r.ngayChot;
    if (dailyData[date]) {
      aggregateStatsRow_(dailyData[date], r);
    }
  });

  return Object.keys(dailyData).sort().map(k => dailyData[k]);
}

function getWeeklyStatsBreakdown_(rows, startDateStr, endDateStr) {
  const weeklyData = {};
  const timeZone = Session.getScriptTimeZone();

  rows.forEach(r => {
    const dateStr = r.ngayChot;
    if (!dateStr) return;

    // Tìm ngày thứ Hai đầu tuần của ngày này
    const date = new Date(dateStr);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    const monday = new Date(date.setDate(diff));
    const mondayStr = Utilities.formatDate(monday, timeZone, 'yyyy-MM-dd');

    const weekKey = mondayStr;
    if (!weeklyData[weekKey]) {
      const formattedMon = Utilities.formatDate(monday, timeZone, 'dd/MM');
      // Thêm ngày Chủ Nhật để biểu thị khoảng tuần
      const sunday = new Date(monday.getTime() + 6 * 24 * 60 * 60 * 1000);
      const formattedSun = Utilities.formatDate(sunday, timeZone, 'dd/MM/yyyy');
      
      weeklyData[weekKey] = {
        date: weekKey,
        label: `Tuần ${formattedMon} ➔ ${formattedSun}`,
        revenue: 0,
        cost: 0,
        profit: 0,
        cod: 0,
        deposit: 0,
        orders: 0
      };
    }

    aggregateStatsRow_(weeklyData[weekKey], r);
  });

  return Object.keys(weeklyData).sort().map(k => weeklyData[k]);
}

function getMonthlyStatsBreakdown_(rows, startDateStr, endDateStr) {
  const monthlyData = {};
  const timeZone = Session.getScriptTimeZone();

  rows.forEach(r => {
    const dateStr = r.ngayChot;
    if (!dateStr) return;

    const [y, m, d] = dateStr.split('-');
    const monthKey = `${y}-${m}`;

    if (!monthlyData[monthKey]) {
      monthlyData[monthKey] = {
        date: monthKey,
        label: `Tháng ${m}/${y}`,
        revenue: 0,
        cost: 0,
        profit: 0,
        cod: 0,
        deposit: 0,
        orders: 0
      };
    }

    aggregateStatsRow_(monthlyData[monthKey], r);
  });

  return Object.keys(monthlyData).sort().map(k => monthlyData[k]);
}

/**
 * Lấy Top 10 sản phẩm bán chạy nhất
 * @private
 */
function getTopProducts_(rows, limit) {
  const prodMap = {};

  rows.forEach(r => {
    if (!isRevenueRow_(r)) return;
    const id = String(r.sanPham || r.maSP || '').trim();
    if (!id) return;

    if (!prodMap[id]) {
      prodMap[id] = { maSP: String(r.maSP || '').trim() || id, productName: id, quantity: 0, revenue: 0, profit: 0 };
    }
    prodMap[id].quantity += 1;
    prodMap[id].revenue += r.giaBan || 0;
    prodMap[id].profit += r.tienLoi || 0;
  });

  return Object.values(prodMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit);
}

/**
 * Lấy Top 10 khách hàng chi tiêu nhiều nhất
 * @private
 */
function getTopCustomers_(rows, limit) {
  const custMap = {};

  rows.forEach(r => {
    if (!isRevenueRow_(r)) return;
    const name = String(r.tenKhach || '').trim();
    const phone = String(r.sdtKhach || '').trim();
    if (!name && !phone) return;

    const key = phone || name;

    if (!custMap[key]) {
      custMap[key] = { name: name || 'Khách ẩn danh', phone: phone || '—', orders: 0, revenue: 0, profit: 0 };
    }
    custMap[key].orders += 1;
    custMap[key].revenue += r.giaBan || 0;
    custMap[key].profit += r.tienLoi || 0;
  });

  return Object.values(custMap)
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit);
}

/**
 * Cơ cấu theo hình thức giao hàng
 * @private
 */
function getDeliveryBreakdown_(rows) {
  let codCount = 0;
  let codRevenue = 0;
  let freeCount = 0;
  let freeRevenue = 0;

  rows.forEach(r => {
    if (!isRevenueRow_(r)) return;
    if (r.hinhThuc === 'COD') {
      codCount++;
      codRevenue += r.giaBan || 0;
    } else {
      freeCount++;
      freeRevenue += r.giaBan || 0;
    }
  });

  return {
    cod: { count: codCount, revenue: codRevenue },
    freeship: { count: freeCount, revenue: freeRevenue }
  };
}

/**
 * Cơ cấu trạng thái sản phẩm
 * @private
 */
function getStatusBreakdown_(rows) {
  let inStock = 0;
  let sold = 0;
  let pending = 0;

  rows.forEach(r => {
    if (!isRevenueRow_(r)) return;
    if (isSoldInternal_(r.trangThai)) {
      sold++;
    } else if (isWaitingInternal_(r.trangThai)) {
      pending++;
    } else {
      inStock++;
    }
  });

  return { inStock, sold, pending };
}

function getCustomerRevenueBreakdown_(rows, limit) {
  const custMap = {};

  rows.forEach((r) => {
    if (!isRevenueRow_(r)) return;
    const name = String(r.tenKhach || '').trim() || 'Khách chưa tên';
    const phone = String(r.sdtKhach || '').trim();
    const key = phone || normalizeTextForFilter_(name);

    if (!custMap[key]) {
      custMap[key] = {
        name,
        phone: phone || '—',
        orders: 0,
        revenue: 0,
        profit: 0,
        sheets: {},
        tagMap: {}
      };
    }

    custMap[key].orders += 1;
    custMap[key].revenue += r.giaBan || 0;
    custMap[key].profit += r.tienLoi || 0;
    custMap[key].sheets[r.sourceSheet || SHEET_NAME] = true;
    collectCustomerStatsTags_(custMap[key], r);
  });

  // Calculate lifetime stats for VIP tier determination
  const allReportRows = getAllReportRows();
  const lifetimeMap = {};
  allReportRows.forEach((r) => {
    if (!isRevenueRow_(r)) return;
    const name = String(r.tenKhach || '').trim() || 'Khách chưa tên';
    const phone = String(r.sdtKhach || '').trim();
    const key = phone || normalizeTextForFilter_(name);

    if (!lifetimeMap[key]) {
      lifetimeMap[key] = { orders: 0, revenue: 0 };
    }
    lifetimeMap[key].orders += 1;
    lifetimeMap[key].revenue += r.giaBan || 0;
  });

  return Object.values(custMap)
    .map((item) => {
      item.aov = item.orders ? Math.round(item.revenue / item.orders) : 0;
      item.sheetList = Object.keys(item.sheets).join(', ');
      
      const key = item.phone !== '—' ? item.phone : normalizeTextForFilter_(item.name);
      const lifetime = lifetimeMap[key] || { revenue: item.revenue, orders: item.orders };
      item.vipTier = getCustomerVipTierInfo_(lifetime.revenue, lifetime.orders);
      
      if (item.vipTier.key !== 'regular') item.tagMap['VIP'] = true;
      if (lifetime.orders > 1) item.tagMap['Khách cũ'] = true;
      item.tags = getOrderedCustomerStatsTags_(item.tagMap);
      delete item.sheets;
      delete item.tagMap;
      return item;
    })
    .sort((a, b) => b.revenue - a.revenue)
    .slice(0, limit || 50);
}

function collectCustomerStatsTags_(item, row) {
  const signal = stripVietnameseMarks_([
    row.tenKhach,
    row.nguonKhach,
    row.ghiChu,
    row.diaChi
  ].join(' ')).toLowerCase();
  const isDeleted = isDeletedInternal_(row.trangThai);

  if (isDeleted || signal.includes('bom') || signal.includes('boom') ||
      signal.includes('hoan') || signal.includes('huy') ||
      signal.includes('tra hang') || signal.includes('tu choi nhan')) {
    item.tagMap['Bom hàng'] = true;
  }
  if (signal.includes('kho tinh') || signal.includes('phan nan') ||
      signal.includes('khieu nai') || signal.includes('can than') ||
      signal.includes('doi hoi')) {
    item.tagMap['Khó tính'] = true;
  }
  if (signal.includes('dai ly') || signal.includes('daily') || signal.includes('agency')) {
    item.tagMap['Đại lý'] = true;
  }
  if (signal.includes('ban si') || signal.includes('khach si') ||
      signal.includes('lay si') || signal.includes('si ') ||
      signal.endsWith(' si') || signal.includes('wholesale')) {
    item.tagMap['Sỉ'] = true;
  }
}

function getOrderedCustomerStatsTags_(tagMap) {
  const tags = Object.keys(tagMap || {});
  const preferred = ['VIP', 'Khách cũ', 'Đại lý', 'Sỉ', 'Khó tính', 'Bom hàng'];
  return preferred.filter((tag) => tags.indexOf(tag) !== -1)
    .concat(tags.filter((tag) => preferred.indexOf(tag) === -1));
}

function getSheetBreakdown_(rows) {
  const sheetMap = {};

  rows.forEach((r) => {
    if (!isRevenueRow_(r)) return;
    const key = r.sourceSheet || SHEET_NAME;
    if (!sheetMap[key]) {
      sheetMap[key] = { sheetName: key, orders: 0, customers: {}, revenue: 0, profit: 0, aov: 0 };
    }

    sheetMap[key].orders += 1;
    sheetMap[key].revenue += r.giaBan || 0;
    sheetMap[key].profit += r.tienLoi || 0;

    const customerKey = String(r.sdtKhach || r.tenKhach || '').trim();
    if (customerKey) sheetMap[key].customers[customerKey] = true;
  });

  return Object.values(sheetMap)
    .map((item) => {
      item.customerCount = Object.keys(item.customers).length;
      item.aov = item.orders ? Math.round(item.revenue / item.orders) : 0;
      delete item.customers;
      return item;
    })
    .sort((a, b) => b.revenue - a.revenue);
}

function getDataQualityIssues_(rows, limit) {
  return rows
    .map((r) => {
      const issues = [];
      if (!r.ngayChot) issues.push('Thiếu ngày chốt/ngày đơn');
      if (!r.tenKhach && !r.sdtKhach) issues.push('Thiếu khách hàng');
      if (!r.maSP && !r.sanPham) issues.push('Thiếu mã SP/sản phẩm');
      if (!r.giaBan || r.giaBan <= 0) issues.push('Doanh thu bằng 0 hoặc thiếu');
      if (!r.trangThaiGoc && r.sourceSheet !== LIQUIDATION_SHEET_NAME) issues.push('Thiếu trạng thái');

      return {
        sourceSheet: r.sourceSheet || SHEET_NAME,
        rowIndex: r.rowIndex,
        maSP: r.maSP || r.sanPham || '—',
        tenKhach: r.tenKhach || '—',
        ngayChot: r.ngayChot || '—',
        revenue: r.giaBan || 0,
        issues
      };
    })
    .filter((item) => item.issues.length)
    .sort((a, b) => b.issues.length - a.issues.length || b.revenue - a.revenue)
    .slice(0, limit || 50);
}
