/* ══════════════════════════════════════════════
   SALES ADMIN SYSTEM — Script.html
   Client-side JavaScript (Google Apps Script)
══════════════════════════════════════════════ */

// ─────────────────────────────────────────────
// MASCOT MÚP XÁM (TAMAGOTCHI PET) - GLOBAL STATE & UTILITIES
// ─────────────────────────────────────────────
let currentMascotState = 'idle';
let mascotHappiness = Number(localStorage.getItem('mascot_happiness') || 60);
let mascotGoldfish = Number(localStorage.getItem('mascot_goldfish_qty') || 0);

function getMascotSvg(state) {
  const isHappy = state === 'happy';
  const isSad = state === 'sad';
  const isThinking = state === 'thinking';

  let decorations = '';
  if (isHappy) {
    decorations = `
      <!-- Vương miện của đại gia -->
      <polygon points="42,24 44,14 50,19 56,14 58,24" fill="#fbbf24" stroke="#d97706" stroke-width="1.5"/>
      <circle cx="44" cy="14" r="1.5" fill="#f59e0b"/>
      <circle cx="50" cy="19" r="1.5" fill="#f59e0b"/>
      <circle cx="56" cy="14" r="1.5" fill="#f59e0b"/>
      
      <!-- Kính râm ngầu -->
      <path d="M28,45 L72,45 L66,54 L52,54 L48,54 L34,54 Z" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
      <line x1="48" y1="48" x2="52" y2="48" stroke="#fbbf24" stroke-width="1.5"/>
      
      <!-- Xu vàng bay lơ lửng -->
      <g class="coin coin-1"><circle cx="20" cy="30" r="4" fill="#fbbf24" stroke="#d97706" stroke-width="1"/><text x="20" y="32" font-size="5" fill="#78350f" text-anchor="middle" font-weight="bold" font-family="sans-serif">$</text></g>
      <g class="coin coin-2"><circle cx="80" cy="25" r="4" fill="#fbbf24" stroke="#d97706" stroke-width="1"/><text x="80" y="27" font-size="5" fill="#78350f" text-anchor="middle" font-weight="bold" font-family="sans-serif">$</text></g>
      <g class="coin coin-3"><circle cx="50" cy="22" r="3.5" fill="#fbbf24" stroke="#d97706" stroke-width="0.8"/><text x="50" y="24" font-size="4" fill="#78350f" text-anchor="middle" font-weight="bold" font-family="sans-serif">$</text></g>
    `;
  } else if (isSad) {
    decorations = `
      <!-- Nước mắt rơi -->
      <path class="tear tear-1" d="M38,54 C38,54 36,60 38,62 C40,62 40,60 38,54" fill="#3b82f6"/>
      <path class="tear tear-2" d="M62,54 C62,54 64,60 62,62 C60,62 60,60 62,54" fill="#3b82f6"/>
      
      <!-- Bát đồ ăn trống rỗng -->
      <path d="M38,88 L62,88 Q64,95 50,95 Q36,95 38,88 Z" fill="#64748b" stroke="#475569" stroke-width="1"/>
      <text x="50" y="93" font-size="5.5" fill="#e2e8f0" text-anchor="middle" font-family="sans-serif" font-weight="bold">ĐÓI</text>
    `;
  } else if (isThinking) {
    decorations = `
      <!-- Kính cận tri thức -->
      <circle cx="36" cy="50" r="6.5" fill="none" stroke="#a78bfa" stroke-width="1.5"/>
      <circle cx="64" cy="50" r="6.5" fill="none" stroke="#a78bfa" stroke-width="1.5"/>
      <line x1="42" y1="50" x2="58" y2="50" stroke="#a78bfa" stroke-width="1.5"/>
      
      <!-- Laptop mini đang gõ -->
      <rect x="35" y="78" width="30" height="13" rx="1" fill="#475569" stroke="#334155" stroke-width="1"/>
      <rect x="38" y="80" width="24" height="9" fill="#c084fc" opacity="0.6"/>
      <polygon points="32,92 30,96 70,96 68,92" fill="#334155"/>
      <line x1="30" y1="92" x2="70" y2="92" stroke="#1e293b" stroke-width="1"/>
    `;
  }

  const eyeMarkup = isHappy ? '' : `
    <!-- Mắt mèo -->
    <circle class="cat-eye" cx="36" cy="50" r="3.5" fill="#0f172a"/>
    <circle class="cat-eye" cx="64" cy="50" r="3.5" fill="#0f172a"/>
  `;

  return `
    <svg class="mascot-svg" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <!-- Đuôi mèo ngúng nguẩy -->
      <path class="cat-tail" d="M25,82 C12,82 6,65 14,56 C17,52 22,57 19,61 C13,71 18,76 25,76 Z" fill="#cbd5e1" stroke="#94a3b8" stroke-width="2"/>
      
      <!-- Thân mèo -->
      <ellipse cx="50" cy="80" rx="26" ry="16" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
      
      <!-- Hai chân trước nhấp nhô -->
      <g class="cat-paw-left">
        <ellipse cx="38" cy="88" rx="5" ry="4" fill="#cbd5e1"/>
      </g>
      <g class="cat-paw-right">
        <ellipse cx="62" cy="88" rx="5" ry="4" fill="#cbd5e1"/>
      </g>
      
      <!-- Tai trái -->
      <polygon points="22,34 16,12 38,28" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>
      <polygon points="24,31 19,16 35,26" fill="#fecdd3"/>
      
      <!-- Tai phải -->
      <polygon points="78,34 84,12 62,28" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>
      <polygon points="76,31 81,16 65,26" fill="#fecdd3"/>

      <!-- Đầu mèo -->
      <ellipse class="cat-body" cx="50" cy="52" rx="32" ry="24" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>
      
      <!-- Chi tiết mặt -->
      <g class="cat-body">
        <!-- Má hồng -->
        <ellipse cx="28" cy="56" rx="4" ry="2" fill="#fecdd3" opacity="0.8"/>
        <ellipse cx="72" cy="56" rx="4" ry="2" fill="#fecdd3" opacity="0.8"/>
        
        ${eyeMarkup}
        
        <!-- Mũi hồng -->
        <polygon points="50,54 47,51 53,51" fill="#f43f5e"/>
        
        <!-- Miệng -->
        <path d="M46,57 Q50,60 50,57 Q50,60 54,57" fill="none" stroke="#64748b" stroke-width="1.5" stroke-linecap="round"/>
        
        <!-- Râu mèo -->
        <line x1="22" y1="56" x2="8" y2="54" stroke="#cbd5e1" stroke-width="1.5"/>
        <line x1="22" y1="59" x2="9" y2="60" stroke="#cbd5e1" stroke-width="1.5"/>
        <line x1="78" y1="56" x2="92" y2="54" stroke="#cbd5e1" stroke-width="1.5"/>
        <line x1="78" y1="59" x2="91" y2="60" stroke="#cbd5e1" stroke-width="1.5"/>
      </g>
      
      ${decorations}
    </svg>
  `;
}

let mascotBubbleTimer = null;

function showMascotBubble() {
  const bubble = document.getElementById('floating-mascot-bubble');
  if (!bubble) return;
  bubble.classList.add('show');
  
  if (mascotBubbleTimer) clearTimeout(mascotBubbleTimer);
  mascotBubbleTimer = setTimeout(() => {
    closeMascotBubble();
  }, 8000);
}

function closeMascotBubble() {
  const bubble = document.getElementById('floating-mascot-bubble');
  if (bubble) bubble.classList.remove('show');
}

function toggleMascotBubble(e) {
  if (e) e.stopPropagation();
  const bubble = document.getElementById('floating-mascot-bubble');
  if (!bubble) return;
  
  if (bubble.classList.contains('show')) {
    closeMascotBubble();
  } else {
    showMascotBubble();
  }
}

function updateMascot(state, message) {
  currentMascotState = state;
  const container = document.getElementById('floating-mascot-container');
  const avatar = document.getElementById('floating-mascot-avatar');
  const textEl = document.getElementById('floating-mascot-bubble-text');
  
  if (container) {
    container.style.display = 'block';
    container.className = `floating-mascot-container mascot-state-${state}`;
  }
  if (avatar) {
    avatar.innerHTML = getMascotSvg(state);
  }
  
  if (textEl && message) {
    textEl.innerHTML = message;
    showMascotBubble();
  }
  updateMascotInteractUi();
}

function updateMascotInteractUi() {
  const qtyEl = document.getElementById('mascot-fish-qty');
  const fillEl = document.getElementById('mascot-happiness-fill');
  const valEl = document.getElementById('mascot-happiness-val');
  const btnSoup = document.getElementById('btn-feed-soup');
  const btnPate = document.getElementById('btn-feed-pate');
  
  if (qtyEl) qtyEl.textContent = mascotGoldfish;
  if (fillEl) fillEl.style.width = mascotHappiness + '%';
  if (valEl) valEl.textContent = mascotHappiness;
  
  if (btnSoup) btnSoup.disabled = mascotGoldfish < 1;
  if (btnPate) btnPate.disabled = mascotGoldfish < 3;
}

function petMascot(e) {
  if (e) {
    e.stopPropagation();
  }
  
  mascotHappiness = Math.min(100, mascotHappiness + 5);
  localStorage.setItem('mascot_happiness', mascotHappiness);
  updateMascotInteractUi();
  spawnFloatingHearts();
  
  // Custom happy meow animation state for 2.5s
  updateMascot('happy');
  
  const greetings = [
    "Múp: Meow~ Sướng quá Sen ơi! (+5 ❤️)",
    "Múp: Ư... gừ gừ... Sen gãi đúng chỗ ngứa rồi! (+5 ❤️)",
    "Múp: Yêu Sen nhất quả đất! Chải lông nữa đi Sen! (+5 ❤️)",
    "Múp: Meo~ Ấm áp quá... (+5 ❤️)"
  ];
  const textEl = document.getElementById('floating-mascot-bubble-text');
  if (textEl) {
    textEl.textContent = greetings[Math.floor(Math.random() * greetings.length)];
    showMascotBubble();
  }
  
  setTimeout(() => {
    const healthScore = Math.max(0, Math.min(100, Number(window.__DASHBOARD_HEALTH_SCORE__ || 100)));
    let mState = 'idle';
    if (healthScore >= 85) mState = 'happy';
    else if (healthScore < 60) mState = 'sad';
    updateMascot(mState);
  }, 2500);
}

function feedMascot(foodType) {
  const cost = foodType === 'pate' ? 3 : 1;
  const happinessGain = foodType === 'pate' ? 40 : 15;
  
  if (mascotGoldfish < cost) {
    const textEl = document.getElementById('floating-mascot-bubble-text');
    if (textEl) {
      textEl.innerHTML = `Múp: Không đủ 🐟 rồi Sen ơi! Ráng chốt thêm đơn kiếm Cá Vàng cho Múp đi mà... 😿`;
      showMascotBubble();
    }
    return;
  }
  
  mascotGoldfish -= cost;
  mascotHappiness = Math.min(100, mascotHappiness + happinessGain);
  localStorage.setItem('mascot_happiness', mascotHappiness);
  updateMascotInteractUi();
  spawnFloatingHearts();
  
  const textEl = document.getElementById('floating-mascot-bubble-text');
  if (textEl) {
    if (foodType === 'pate') {
      textEl.innerHTML = `Múp: 🥫 Ôi pate thượng hạng ngọt bùi béo ngậy! Đã thèm quá Sen ơi! (+40 ❤️)`;
    } else {
      textEl.innerHTML = `Múp: 🥣 Soup thưởng ngon ngọt lịm tim! Múp yêu Sen rất nhiều! (+15 ❤️)`;
    }
    showMascotBubble();
  }
  
  updateMascot('happy');
  
  setTimeout(() => {
    const healthScore = Math.max(0, Math.min(100, Number(window.__DASHBOARD_HEALTH_SCORE__ || 100)));
    let mState = 'idle';
    if (healthScore >= 85) mState = 'happy';
    else if (healthScore < 60) mState = 'sad';
    updateMascot(mState);
  }, 3000);
}

function spawnFloatingHearts() {
  const container = document.getElementById('floating-mascot-container');
  if (!container) return;
  
  const rect = container.getBoundingClientRect();
  const heartCount = 6;
  
  for (let i = 0; i < heartCount; i++) {
    const el = document.createElement('div');
    el.className = 'mascot-heart-particle';
    el.innerHTML = ['❤️', '💖', '💝', '✨'][Math.floor(Math.random() * 4)];
    
    // Position near the top of the avatar
    el.style.left = (rect.left + rect.width / 2 + (Math.random() * 20 - 10)) + 'px';
    el.style.top = (rect.top + 10 + (Math.random() * 20 - 10)) + 'px';
    
    const dx = (Math.random() * 60 - 30) + 'px';
    const dy = -(40 + Math.random() * 50) + 'px';
    const rot = (Math.random() * 40 - 20) + 'deg';
    
    el.style.setProperty('--dx', dx);
    el.style.setProperty('--dy', dy);
    el.style.setProperty('--rot', rot);
    
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 1000);
  }
}

function parseActivityToMascotStory(log) {
  const timeStr = log.time ? formatTimeOnly_(log.time) : '';
  const action = log.action || '';
  const maSP = log.maSP || 'sản phẩm';
  const details = log.details || '';
  
  let story = '';
  let isWarning = false;
  
  if (action.includes('Thêm mới')) {
    story = `Múp Xám vừa ngửi thấy mùi sản phẩm mới <b>${maSP}</b>! Sen chốt đơn nhanh kiếm pate nào! 😋`;
  } else if (action.includes('Cập nhật nhanh') || action.includes('Cập nhật')) {
    if (details.includes('Trạng thái') && details.includes('Đã bán')) {
      story = `Múp Xám vừa chén ngập mồm đơn <b>${maSP}</b>! Được Sen thưởng soup ngon ngọt lịm! 🐟✨`;
    } else if (details.includes('Trạng thái') && (details.includes('hủy') || details.includes('bom') || details.includes('trả'))) {
      story = `Ơ kìa! Đĩa thức ăn <b>${maSP}</b> bị giật mất rồi! Hủy đơn làm Múp Xám mếu máo buồn thiu... 😿`;
      isWarning = true;
    } else {
      story = `Hồ sơ sản phẩm <b>${maSP}</b> vừa được chải chuốt lại mượt mà cho Múp Xám ngắm! 🧼🐱`;
    }
  } else if (action.includes('Xóa')) {
    story = `Sản phẩm <b>${maSP}</b> đã bị xóa bay màu khỏi thực đơn của Múp Xám! 🧹`;
    isWarning = true;
  } else if (action.includes('Quay thưởng')) {
    story = `Múp Xám làm MC kéo cần quay thưởng cho khách VIP! Chúc mừng khách trúng quà nha! 🎉`;
  } else {
    story = `Múp Xám ghi nhận: ${details}`;
  }
  
  return { story, timeStr, isWarning };
}

function renderMascotActivityLogs(logs) {
  // Make the floating mascot speak the latest log in the bubble
  if (logs && logs.length > 0) {
    const latest = logs[0];
    const storyItem = parseActivityToMascotStory(latest);
    const textEl = document.getElementById('floating-mascot-bubble-text');
    if (textEl) {
      textEl.innerHTML = storyItem.story;
      showMascotBubble();
    }
  }

  const container = document.getElementById('mascot-log-list');
  if (!container) return;
  
  if (!logs || !logs.length) {
    container.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; text-align:center; padding: 20px;">Chưa có hoạt động nào hôm nay.</div>';
    return;
  }
  
  container.innerHTML = logs.slice(0, 15).map(log => {
    const item = parseActivityToMascotStory(log);
    const warningClass = item.isWarning ? 'warning' : '';
    return `
      <div class="mascot-log-item ${warningClass}">
        <span>${item.story}</span>
        <span class="mascot-log-time">${item.timeStr}</span>
      </div>
    `;
  }).join('');
}

function formatTimeOnly_(dateVal) {
  try {
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) {
      // Fallback if not standard Date object/string
      return String(dateVal).split('T')[1]?.slice(0, 5) || String(dateVal).split(' ')[1]?.slice(0, 5) || '';
    }
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  } catch (e) {
    return '';
  }
}

// ───────────────────────────────────────────────
// GLOBAL STATE
// ─────────────────────────────────────────────
let allRows        = [];
let filteredRows   = [];
let allReportRows  = [];
let liquidationRows = [];
let filteredLiquidationRows = [];
let currentPage    = 1;
let pageSize       = 10;
let totalPages     = 1;
let liquidationPage = 1;
let liquidationPageSize = 20;
let liquidationTotalPages = 1;
let currentSort    = { key: null, dir: 'asc' };
let liquidationSort = { key: 'ngayChot', dir: 'desc' };
let dailySort = { key: 'tenKhach', dir: 'asc' };
let deleteRowIndex = null;
let deleteRowMaSP  = '';
let deleteRowSheetName = 'SalesData';
let chartRevenue, chartStatus, chartOrders, chartDelivery, chartCustomerLifetime;
let chartRevenueFull, chartProfitFull, chartOrdersFull;
let sidebarCollapsed = false;

// States for advanced statistics page
let statsPeriod = 'month'; 
let statsSubTab = 'overview'; 
let statsTableView = 'day'; // 'day', 'week', 'month'
let statsDataCached = null; 
let statsLoadTimer = null;
let customerHistoryTimer = null;
let shopAiPending = false;
let chartRevenueAdvanced, chartRevenueProfitBar, chartTopProducts, chartTopCustomers, chartStatsDelivery, chartStatsStatus;

const DEFAULT_CUSTOMER_VIP_TIERS = [
  { key: 'diamond', label: 'VIP Kim Cương', minLtv: 100000000, minOrders: 30, className: 'vip-diamond' },
  { key: 'gold', label: 'VIP Vàng', minLtv: 50000000, minOrders: 15, className: 'vip-gold' },
  { key: 'silver', label: 'VIP Bạc', minLtv: 20000000, minOrders: 8, className: 'vip-silver' },
  { key: 'bronze', label: 'VIP Đồng', minLtv: 5000000, minOrders: 3, className: 'vip-bronze' }
];

function normalizeCustomerVipTierRules_(tiers) {
  const byKey = {};
  (Array.isArray(tiers) ? tiers : []).forEach(tier => {
    if (tier && tier.key) byKey[tier.key] = tier;
  });

  return DEFAULT_CUSTOMER_VIP_TIERS.map(defaultTier => {
    const tier = byKey[defaultTier.key] || {};
    const label = String(tier.label || defaultTier.label).trim() || defaultTier.label;
    const minLtv = Number(tier.minLtv);
    const minOrders = Number(tier.minOrders);
    return {
      key: defaultTier.key,
      label,
      minLtv: Number.isFinite(minLtv) && minLtv >= 0 ? Math.round(minLtv) : defaultTier.minLtv,
      minOrders: Number.isFinite(minOrders) && minOrders >= 0 ? Math.round(minOrders) : defaultTier.minOrders,
      className: tier.className || defaultTier.className
    };
  });
}

function setCustomerVipTierSettings_(settings) {
  const tiers = Array.isArray(settings) ? settings : (settings && settings.tiers);
  CUSTOMER_VIP_TIERS = normalizeCustomerVipTierRules_(tiers);
  if (typeof window !== 'undefined') {
    window.__VIP_TIER_SETTINGS__ = { tiers: CUSTOMER_VIP_TIERS.map(tier => ({ ...tier })) };
  }
  return CUSTOMER_VIP_TIERS;
}

const initialVipTierSettings = typeof window !== 'undefined' ? window.__VIP_TIER_SETTINGS__ : null;
let CUSTOMER_VIP_TIERS = normalizeCustomerVipTierRules_(initialVipTierSettings && initialVipTierSettings.tiers);

// ─────────────────────────────────────────────
// INIT
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setCurrentDate();
  showLoading();
  initColumnVisibility();
  // Small delay for loader UX
  setTimeout(() => {
    hideLoading();
    document.getElementById('password-input').focus();
  }, 1200);
  startAutoRefresh();
});

let autoRefreshTimer = null;
let lastSyncRequestTime = 0;

function triggerSoftSync() {
  const activePage = document.querySelector('.page-content:not(.hidden)');
  if (!activePage) return;
  
  lastSyncRequestTime = Date.now();
  const pageId = activePage.id;
  if (pageId === 'page-dashboard') loadDashboard(false);
  else if (pageId === 'page-products') loadProducts(false);
  else if (pageId === 'page-daily') loadDailyOrders(false);
}

// Đã TẮT tự động tải lại: dùng nút "Hôm nay" / nút làm mới để cập nhật thủ công.
function startAutoRefresh() {
  stopAutoRefresh();
}

function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
  }
}

function setCurrentDate() {
  const now = new Date();
  const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
  document.getElementById('current-date').textContent = now.toLocaleDateString('vi-VN', options);
}

// ─────────────────────────────────────────────
// LOADING
// ─────────────────────────────────────────────
function showLoading(msg) {
  const el = document.getElementById('loading-overlay');
  if (msg) el.querySelector('.loading-text').textContent = msg;
  el.classList.remove('hidden', 'fade-out');
}
function hideLoading() {
  const el = document.getElementById('loading-overlay');
  el.classList.add('fade-out');
  setTimeout(() => el.classList.add('hidden'), 400);
}

// ─────────────────────────────────────────────
// TOAST
// ─────────────────────────────────────────────
const TOAST_ICONS = {
  success: 'fa-check-circle',
  error:   'fa-times-circle',
  info:    'fa-info-circle',
  warning: 'fa-info-circle'
};
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <i class="fas ${TOAST_ICONS[type]} toast-icon"></i>
    <span class="toast-msg">${message}</span>
    <i class="fas fa-times toast-close" onclick="dismissToast(this.parentElement)"></i>
  `;
  container.appendChild(toast);
  setTimeout(() => dismissToast(toast), duration);
}
function dismissToast(el) {
  if (!el || !el.parentElement) return;
  el.classList.add('closing');
  setTimeout(() => el.remove(), 260);
}

function fmtVnd(n) {
  return new Intl.NumberFormat('vi-VN').format(Number(n || 0)) + ' ₫';
}

function fmtNum(n) {
  return new Intl.NumberFormat('vi-VN').format(Number(n || 0));
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function parseMoneyInput_(value, fallback = 0) {
  const raw = String(value ?? '').trim();
  if (!raw) return fallback;
  const normalized = raw
    .replace(/[₫đĐvndVND\s]/g, '')
    .replace(/[^\d,.\-]/g, '')
    .replace(/\./g, '')
    .replace(',', '.');
  const parsed = Number(normalized);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.round(parsed) : fallback;
}

function getComparableValue(row, key) {
  const value = row ? row[key] : '';
  if (['giaBan', 'giaVon', 'tienLoi', 'tienCOD', 'khachCoc', 'orders', 'revenue', 'profit', 'aov'].includes(key)) {
    return Number(value || 0);
  }
  if (['ngayChot', 'createdAt', 'updatedAt', 'date'].includes(key)) {
    return String(value || '');
  }
  return String(value || '').toLowerCase();
}

function compareRowsByKey(a, b, key, dir) {
  const va = getComparableValue(a, key);
  const vb = getComparableValue(b, key);
  if (va < vb) return dir === 'asc' ? -1 : 1;
  if (va > vb) return dir === 'asc' ? 1 : -1;
  return 0;
}

// ─────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────
function handleLogin(e) {
  e.preventDefault();
  const pw = document.getElementById('password-input').value.trim();
  const err = document.getElementById('login-error');
  err.classList.add('hidden');

  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xác thực...';

  google.script.run
    .withSuccessHandler(ok => {
      btn.disabled = false;
      btn.innerHTML = '<span>Đăng nhập</span><i class="fas fa-arrow-right"></i>';
      if (ok) {
        showLoading('Đang tải dữ liệu...');
        document.getElementById('login-page').classList.add('hidden');
        document.getElementById('app').classList.remove('hidden');
        loadDashboard();
      } else {
        err.classList.remove('hidden');
        document.getElementById('password-input').select();
      }
    })
    .withFailureHandler(err => {
      btn.disabled = false;
      btn.innerHTML = '<span>Đăng nhập</span><i class="fas fa-arrow-right"></i>';
      showToast('Lỗi kết nối server!', 'error');
    })
    .login(pw);
}

function togglePassword() {
  const inp  = document.getElementById('password-input');
  const icon = document.getElementById('eye-icon');
  if (inp.type === 'password') {
    inp.type = 'text';
    icon.className = 'fas fa-eye-slash';
  } else {
    inp.type = 'password';
    icon.className = 'fas fa-eye';
  }
}

function logout() {
  document.getElementById('app').classList.add('hidden');
  document.getElementById('login-page').classList.remove('hidden');
  document.getElementById('password-input').value = '';
  showToast('Đã đăng xuất!', 'info');
}

// ───────────────────────────────────────────────
// NAVIGATION / SIDEBAR
// ─────────────────────────────────────────────
function switchPage(page, navEl) {
  document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  document.getElementById(`page-${page}`).classList.remove('hidden');
  if (navEl) navEl.classList.add('active');

  const titles = {
    dashboard : 'Dashboard',
    products  : 'Quản lý sản phẩm',
    daily     : 'Đơn chốt theo ngày',
    viettel_orders: 'Tạo đơn Viettel Post',
    liquidation: 'Đơn chốt THANH LÝ',
    search    : 'Tra cứu MÃ SP',
    stats     : 'Biểu đồ chi tiết',
    system_audit: 'Trung tâm kiểm tra hệ thống',
    activity  : 'Nhật ký hoạt động',
    settings  : 'Cấu hình hệ thống'
  };
  document.getElementById('topbar-title').textContent = titles[page] || page;

  if (page === 'dashboard') {
    loadDashboard();
    loadShopPulseData();
  }
  if (page === 'products' ) loadProducts();
  if (page === 'liquidation') loadLiquidationRows();
  if (page === 'stats'    ) loadAdvancedStats();
  if (page === 'system_audit') loadSystemAudit();
  if (page === 'activity' ) loadActivityLogs();
  if (page === 'settings' ) loadSystemSettings();
  if (page === 'viettel_orders') {
    loadViettelOrdersPage();
  }
  if (page === 'daily'    ) {
    const range = getDailyDateRange();
    if (!range.start || !range.end) {
      setDailyToday();
    } else {
      // Just re-render client side if returning to tab
      if (allReportRows.length > 0) {
        renderDailyOrders(filterDailyOrders(allReportRows, range), range);
      } else {
        loadDailyOrders();
      }
    }
  }

  if (window.innerWidth <= 900) {
    document.getElementById('sidebar').classList.remove('mobile-open');
  }
  return false;
}

function toggleSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const wrapper  = document.getElementById('main-wrapper');
  if (window.innerWidth <= 900) {
    sidebar.classList.toggle('mobile-open');
  } else {
    sidebarCollapsed = !sidebarCollapsed;
    sidebar.classList.toggle('collapsed', sidebarCollapsed);
    wrapper.classList.toggle('sidebar-collapsed', sidebarCollapsed);
  }
}


// ──────────────────────────────────────────────
// LOAD ALL DATA (from GAS)
// ─────────────────────────────────────────────
function loadData(callback) {
  google.script.run
    .withSuccessHandler(rows => {
      allRows = (rows || []).reverse();
      filteredRows = [...allRows];
      currentPage = 1;
      buildCustomerHistoryMap();
      hideLoading();
      if (callback) callback();
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Không tải được dữ liệu: ' + e.message, 'error');
    })
    .getAllRows();
}

// ─────────────────────────────────────────────
// DASHBOARD & UNIFIED REFRESH
// ─────────────────────────────────────────────
function refreshData() {
  if (!document.getElementById('page-liquidation')?.classList.contains('hidden')) {
    loadLiquidationRows();
    return;
  }
  if (!document.getElementById('page-daily')?.classList.contains('hidden')) {
    loadDailyOrders();
    return;
  }
  if (!document.getElementById('page-stats')?.classList.contains('hidden')) {
    loadAdvancedStats();
    return;
  }

  showLoading('Đang đồng bộ dữ liệu...');
  google.script.run
    .withSuccessHandler(res => {
      if (!res) return;
      crmSnapshot = res;
      allRows = (res.rows || []).reverse();
      allReportRows = res.reportRows || [];
      filteredRows = [...allRows];
      
      buildCustomerHistoryMap();

      // 1. Update Products Page
      applyFilters();
      
      // 2. Update Daily Orders Page
      const dailyRange = getDailyDateRange();
      if (dailyRange.start && dailyRange.end) {
        const dailyFiltered = (res.dailyRows || []).filter(r => r.ngayChot && r.ngayChot >= dailyRange.start && r.ngayChot <= dailyRange.end);
        renderDailyOrders(dailyFiltered.reverse(), dailyRange);
      }
      
      // 3. Update Dashboard Stats
      if (res.stats) {
        renderDashboardStats(res.stats);
        renderDashboardCharts(res.stats);
      }

      // 4. Update Notifications (Module 9)
      if (res.stats && res.stats.notifications) {
        renderNotifications(res.stats.notifications);
      }

      updateSyncStatusUI(res);
      hideLoading();
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Lỗi đồng bộ dữ liệu: ' + e.message, 'error');
    })
    .getCrmSyncSnapshot({ forceRefresh: true });
}
let crmSnapshot = null;
let currentSyncRequestId = 0;

function updateSyncStatusUI(res) {
  const container = document.getElementById('crm-sync-status-info');
  if (!container) return;

  const countSales = res.sourceCounts?.['SalesData'] || 0;
  const countMaV = res.sourceCounts?.['Mã V'] || 0;
  const syncTime = res.syncedAt ? res.syncedAt.split(' ')[1] : '';

  let html = `
    <span><i class="fas fa-database"></i> SalesData: <strong>${countSales}</strong> dòng</span>
    <span><i class="fas fa-percentage"></i> Mã V: <strong>${countMaV}</strong> dòng</span>
    <span><i class="fas fa-sync-alt"></i> Đồng bộ: <strong>${syncTime || 'Vừa xong'}</strong> ${res.cacheHit ? '(Cache)' : '(Mới)'}</span>
  `;

  if (res.skippedCounts?.totalSkipped > 0) {
    html += ` <span style="color: #fca5a5;" title="Bỏ qua ${res.skippedCounts.totalSkipped} dòng do không hợp lệ"><i class="fas fa-exclamation-triangle"></i> Bỏ qua: ${res.skippedCounts.totalSkipped} dòng</span>`;
  }

  container.innerHTML = html;
}

function loadDashboard(forceRefresh) {
  lastSyncRequestTime = Date.now();
  const reqId = ++currentSyncRequestId;
  showLoading(forceRefresh ? 'Đang làm mới dashboard...' : 'Đang tải dashboard...');
  google.script.run
    .withSuccessHandler(res => {
      if (reqId !== currentSyncRequestId) return;
      hideLoading();
      if (!res) return;
      crmSnapshot = res;
      allRows = res.rows || [];
      allReportRows = res.reportRows || [];
      buildCustomerHistoryMap();
      renderDashboardStats(res.stats);
      renderDashboardCharts(res.stats);
      if (res.stats && res.stats.notifications) {
        renderNotifications(res.stats.notifications);
      }
      updateSyncStatusUI(res);
    })
    .withFailureHandler(e => {
      if (reqId !== currentSyncRequestId) return;
      hideLoading();
      showToast('Lỗi tải dashboard: ' + e.message, 'error');
    })
    .getCrmSyncSnapshot({ forceRefresh: !!forceRefresh });
}

function preloadAllReportRows() {
  // Already loaded in snapshot, no-op
}

function renderDashboardStats(s) {
  const fmt = (n) => new Intl.NumberFormat('vi-VN').format(Math.abs(n)) + ' ₫';

  document.getElementById('stat-doanh-thu').textContent      = fmt(s.tongDoanhThu);
  
  let revSubHtml = `${s.tongSanPham} sản phẩm`;
  if (s.growthDoanhThu !== undefined) {
    const isUp = s.growthDoanhThu >= 0;
    revSubHtml += ` · <span class="${isUp ? 'text-success' : 'text-danger'}" style="font-weight:600;"><i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i> ${isUp ? '+' : ''}${s.growthDoanhThu}% hôm nay</span>`;
  }
  document.getElementById('stat-tong-sp').innerHTML = revSubHtml;
  
  document.getElementById('stat-loi-nhuan-rong').textContent = (s.loiNhuanRong >= 0 ? '+' : '-') + fmt(s.loiNhuanRong);
  
  let profitSubHtml = `+Lợi nhuận dương: ${fmt(s.tongLoiNhuan)}`;
  if (s.growthLoiNhuan !== undefined) {
    const isUp = s.growthLoiNhuan >= 0;
    profitSubHtml += ` · <span class="${isUp ? 'text-success' : 'text-danger'}" style="font-weight:600;"><i class="fas fa-arrow-${isUp ? 'up' : 'down'}"></i> ${isUp ? '+' : ''}${s.growthLoiNhuan}% hôm nay</span>`;
  }
  document.getElementById('stat-loi-label').innerHTML = profitSubHtml;

  document.getElementById('stat-tong-lo').textContent        = '-' + fmt(s.tongLo);
  document.getElementById('stat-goc-hang').textContent       = 'Giá vốn: ' + fmt(s.tongGiaVon);
  document.getElementById('stat-con-hang').textContent       = s.soLuongCon;       // big purple card
  document.getElementById('stat-con-hang-mini').textContent  = s.soLuongCon;       // mini card row
  document.getElementById('stat-da-ban').textContent         = s.soLuongBan;
  document.getElementById('stat-doi-ck').textContent         = s.soLuongDoiCK || 0;
  document.getElementById('stat-da-xoa').textContent         = s.soLuongXoa || 0;
  document.getElementById('stat-cod').textContent            = s.soCOD;
  document.getElementById('stat-freeship').textContent       = s.soFreeship;
  document.getElementById('nav-badge-products').textContent  = s.tongSanPham;

  // F16: Sidebar stock badge
  const stockBadge = document.getElementById('nav-badge-stock');
  if (stockBadge) stockBadge.textContent = s.soLuongCon > 0 ? s.soLuongCon + ' kho' : '';

  // F9: Goal tracker
  updateGoalTracker(s);
  renderBusinessHealth(s.businessHealth);

  // Render Top Customers list
  const listEl = document.getElementById('top-customers-today-list');
  if (listEl) {
    if (s.topKhachHomNay && s.topKhachHomNay.length > 0) {
      listEl.innerHTML = s.topKhachHomNay.map((c, i) => `
        <div class="top-customer-item customer-name-clickable" onclick="openCustomerProfileModal('${escapeForInlineEdit(c.name)}', '${escapeForInlineEdit(c.phone)}')" title="Xem Customer 360">
          <div>
            <span class="top-customer-rank">#${i + 1}</span>
            <span class="top-customer-name">${escapeHtml(c.name)} ${c.phone ? `(${c.phone})` : ''}</span>
          </div>
          <span class="top-customer-revenue">${fmtVnd(c.revenue)}</span>
        </div>
      `).join('');
    } else {
      listEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:0.85rem;">Hôm nay chưa có đơn chốt</div>';
    }
  }

  // Update AI Insights Summary
  updateAISummary(s);

  // Update Mascot State & Bubble
  const safeScore = Math.max(0, Math.min(100, Number(s.businessHealth && s.businessHealth.score || 0)));
  window.__DASHBOARD_HEALTH_SCORE__ = safeScore;
  
  // Sync available goldfish count from daily chốt orders
  const ordersToday = Number(s.donBanHomNay || 0);
  let lastSyncedOrders = Number(localStorage.getItem('mascot_last_synced_orders') || 0);
  
  if (ordersToday < lastSyncedOrders) {
    // New day started! Reset sync counter
    lastSyncedOrders = 0;
  }
  
  if (ordersToday > lastSyncedOrders) {
    const diff = ordersToday - lastSyncedOrders;
    mascotGoldfish += diff;
    localStorage.setItem('mascot_goldfish_qty', mascotGoldfish);
    localStorage.setItem('mascot_last_synced_orders', ordersToday);
  } else {
    localStorage.setItem('mascot_last_synced_orders', ordersToday);
  }
  
  const mascotHealthBadge = document.getElementById('mascot-health-badge');
  if (mascotHealthBadge) {
    mascotHealthBadge.textContent = `Sức khỏe: ${safeScore}/100`;
  }
  
  let mState = 'idle';
  let mascotSpeech = '';
  if (safeScore >= 85) {
    mState = 'happy';
    mascotSpeech = `Sức khỏe shop đạt ${safeScore}/100! Thưởng soup ngon ngọt lịm với pate cho Múp Xám thôi Sen ơi! 🐟✨`;
  } else if (safeScore < 60) {
    mState = 'sad';
    mascotSpeech = `Sức khỏe shop chỉ có ${safeScore}/100 thôi á? Cứu Múp, đói héo hon rồi, ráng chốt đơn mua pate cho Múp đi! 😿`;
  } else {
    mState = 'idle';
    mascotSpeech = `Sức khỏe shop đạt ${safeScore}/100. Buôn bán túc tắc, Sen ráng bán nhiều để mua soup thưởng cho Múp Xám nhé! 🐾`;
  }
  
  updateMascot(mState, mascotSpeech);

  // Load and render mascot activity logs
  google.script.run
    .withSuccessHandler(logs => {
      renderMascotActivityLogs(logs);
    })
    .getActivityLogs();
}

function renderDashboardCharts(s) {
  const labels = s.chartLabels.length ? s.chartLabels : ['Chưa có dữ liệu'];
  const isDark = true;

  Chart.defaults.color = '#94a3b8';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';

  // Destroy old charts
  if (chartRevenue)  chartRevenue.destroy();
  if (chartStatus)   chartStatus.destroy();
  if (chartOrders)   chartOrders.destroy();
  if (chartDelivery) chartDelivery.destroy();
  if (chartCustomerLifetime) chartCustomerLifetime.destroy();

  // Create gradient fills
  const canvasRev = document.getElementById('chart-revenue');
  let bgRev = 'rgba(124, 58, 237, 0.05)';
  let bgProf = 'rgba(6, 182, 212, 0.05)';
  if (canvasRev) {
    const ctxRev = canvasRev.getContext('2d');
    if (ctxRev) {
      const gradRev = ctxRev.createLinearGradient(0, 0, 0, 260);
      gradRev.addColorStop(0, 'rgba(124, 58, 237, 0.35)');
      gradRev.addColorStop(1, 'rgba(124, 58, 237, 0.0)');
      bgRev = gradRev;

      const gradProf = ctxRev.createLinearGradient(0, 0, 0, 260);
      gradProf.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
      gradProf.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
      bgProf = gradProf;
    }
  }

  // Revenue & Profit Line Chart
  chartRevenue = new Chart(document.getElementById('chart-revenue'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Doanh thu',
          data: s.chartDoanhThu,
          borderColor: '#7c3aed',
          backgroundColor: bgRev,
          borderWidth: 2.5,
          pointRadius: 4, pointBackgroundColor: '#7c3aed',
          tension: 0.4, fill: true
        },
        {
          label: 'Lợi nhuận',
          data: s.chartLoiNhuan,
          borderColor: '#06b6d4',
          backgroundColor: bgProf,
          borderWidth: 2.5,
          pointRadius: 4, pointBackgroundColor: '#06b6d4',
          tension: 0.4, fill: true
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(26,26,46,0.95)',
          borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1,
          padding: 12, corner: 8,
          callbacks: {
            label: ctx => ' ' + ctx.dataset.label + ': ' +
              new Intl.NumberFormat('vi-VN').format(ctx.raw) + ' ₫'
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: {
          ticks: {
            font: { size: 11 },
            callback: v => new Intl.NumberFormat('vi-VN', { notation: 'compact' }).format(v)
          }
        }
      }
    }
  });

  // Status Doughnut
  chartStatus = new Chart(document.getElementById('chart-status'), {
    type: 'doughnut',
    data: {
      labels: ['Còn hàng', 'Đã bán', 'Đợi CK', 'Đã xóa'],
      datasets: [{
        data: [s.soLuongCon, s.soLuongBan, s.soLuongDoiCK || 0, s.soLuongXoa || 0],
        backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(99,102,241,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)'],
        borderColor: 'rgba(26,26,46,0)',
        borderWidth: 0, hoverOffset: 6
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: { size: 11 } } },
        tooltip: { backgroundColor: 'rgba(26,26,46,0.95)', borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1 }
      }
    }
  });

  // Orders Bar Chart
  chartOrders = new Chart(document.getElementById('chart-orders'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Số đơn',
        data: s.chartDon,
        backgroundColor: 'rgba(99,102,241,0.7)',
        borderColor: '#6366f1',
        borderWidth: 1, borderRadius: 6
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor: 'rgba(26,26,46,0.95)', borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1 }
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 11 } } },
        y: { ticks: { stepSize: 1, font: { size: 11 } } }
      }
    }
  });

  // Delivery Doughnut
  chartDelivery = new Chart(document.getElementById('chart-delivery'), {
    type: 'doughnut',
    data: {
      labels: ['COD', 'Freeship'],
      datasets: [{
        data: [s.soCOD, s.soFreeship],
        backgroundColor: ['rgba(245,158,11,0.8)', 'rgba(59,130,246,0.8)'],
        borderColor: 'rgba(26,26,46,0)',
        borderWidth: 0, hoverOffset: 6
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16, font: { size: 11 } } },
        tooltip: { backgroundColor: 'rgba(26,26,46,0.95)', borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1 }
      }
    }
  });

  const lifetimeCanvas = document.getElementById('chart-customer-lifetime');
  const lifetime = s.customerLifetime || {};
  if (lifetimeCanvas) {
    const hasLifetimeData = Boolean(lifetime.labels && lifetime.labels.length);
    const lifetimeLabels = hasLifetimeData ? lifetime.labels : ['Chưa có dữ liệu'];
    chartCustomerLifetime = new Chart(lifetimeCanvas, {
      type: 'bar',
      data: {
        labels: lifetimeLabels,
        datasets: [
          {
            label: 'Khách mới',
            data: hasLifetimeData ? (lifetime.newCustomers || []) : [0],
            backgroundColor: 'rgba(16,185,129,0.72)',
            borderColor: '#10b981',
            borderWidth: 1,
            borderRadius: 6
          },
          {
            label: 'Khách quay lại',
            data: hasLifetimeData ? (lifetime.returningCustomers || []) : [0],
            backgroundColor: 'rgba(99,102,241,0.72)',
            borderColor: '#818cf8',
            borderWidth: 1,
            borderRadius: 6
          },
          {
            label: 'Khách mất',
            data: hasLifetimeData ? (lifetime.lostCustomers || []) : [0],
            backgroundColor: 'rgba(239,68,68,0.66)',
            borderColor: '#ef4444',
            borderWidth: 1,
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { padding: 14, font: { size: 11 } } },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              label: ctx => ` ${ctx.dataset.label}: ${fmtNum(ctx.raw)} khách`
            }
          }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 11 } } },
          y: { beginAtZero: true, ticks: { stepSize: 1, font: { size: 11 } } }
        }
      }
    });
  }

  // Render sparklines
  renderSparkline('sparkline-revenue', s.last7DoanhThu || [], '#818cf8');
  renderSparkline('sparkline-profit', s.last7LoiNhuan || [], '#34d399');
  renderSparkline('sparkline-loss', s.last7Lo || [], '#ef4444');
}

function renderBusinessHealth(health) {
  const scoreEl = document.getElementById('business-health-score');
  const labelEl = document.getElementById('business-health-label');
  const fillEl = document.getElementById('business-health-gauge-fill');
  const activeRing = document.getElementById('health-ring-active');
  const factorsEl = document.getElementById('business-health-factors');
  if (!scoreEl || !labelEl || !factorsEl) return;

  const safeScore = Math.max(0, Math.min(100, Number(health && health.score || 0)));
  scoreEl.textContent = safeScore;
  labelEl.textContent = health && health.label ? health.label : 'Chưa đủ dữ liệu';
  labelEl.className = 'business-health-badge ' + getBusinessHealthClass_(safeScore);

  if (fillEl) {
    const rotation = -90 + (safeScore / 100) * 180;
    fillEl.style.transform = `rotate(${rotation}deg)`;
  }
  if (activeRing) {
    const circ = 251.327; // 2 * Math.PI * 40
    const offset = circ - (safeScore / 100) * circ;
    activeRing.style.strokeDashoffset = offset;
  }

  const components = health && health.components ? health.components : [];
  if (!components.length) {
    factorsEl.innerHTML = '<div class="profile-empty-line">Chưa có đủ dữ liệu để tính sức khỏe.</div>';
    return;
  }

  factorsEl.innerHTML = components.map(item => `
    <div class="business-health-factor">
      <span>${escapeHtml(item.label)}</span>
      <strong class="${getBusinessHealthClass_(item.score)}">${fmtNum(item.score)}/100</strong>
    </div>
  `).join('');
}

function getBusinessHealthClass_(score) {
  const safeScore = Number(score || 0);
  if (safeScore >= 85) return 'health-great';
  if (safeScore >= 70) return 'health-good';
  if (safeScore >= 55) return 'health-watch';
  return 'health-risk';
}

function askShopAiQuick(question) {
  const input = document.getElementById('shop-ai-input');
  if (input) input.value = question;
  askShopAi(question);
}

function askShopAiFromInput(event) {
  event.preventDefault();
  const input = document.getElementById('shop-ai-input');
  const question = String(input?.value || '').trim();
  askShopAi(question);
}

function askShopAi(question) {
  const cleanQuestion = String(question || '').trim();
  if (!cleanQuestion) {
    showToast('Nhập câu hỏi cho AI trước đã.', 'warning');
    return;
  }
  if (shopAiPending) return;

  const input = document.getElementById('shop-ai-input');
  const btn = document.getElementById('shop-ai-send');
  appendShopAiMessage(cleanQuestion, 'user');
  
  // Set Dashboard Mascot to thinking state
  updateMascot('thinking', 'Múp Xám đang gõ phím cạch cạch tra cứu dữ liệu sheet...');
  
  appendShopAiMessage('Múp Xám đang đọc dữ liệu và viết báo cáo...', 'assistant loading');
  shopAiPending = true;
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
  }

  google.script.run
    .withSuccessHandler(res => {
      shopAiPending = false;
      removeShopAiLoading();
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
      }
      if (input) input.value = '';
      
      const answerText = res && res.answer ? res.answer : 'Múp Xám chưa nhận được phản hồi từ Gemini.';
      const isError = res && res.success === false;
      appendShopAiMessage(answerText, isError ? 'assistant warning' : 'assistant');
      
      // Reset Dashboard Mascot back to original health-based state
      refreshDashboardMascotState_();
    })
    .withFailureHandler(e => {
      shopAiPending = false;
      removeShopAiLoading();
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i>';
      }
      appendShopAiMessage('Lỗi kết nối rồi sen ơi: ' + (e && e.message ? e.message : e), 'assistant warning');
      
      refreshDashboardMascotState_();
    })
    .askShopAi(cleanQuestion);
}

function refreshDashboardMascotState_() {
  const healthScore = Math.max(0, Math.min(100, Number(window.__DASHBOARD_HEALTH_SCORE__ || 100)));
  let mState = 'idle';
  let mascotSpeech = '';
  if (healthScore >= 85) {
    mState = 'happy';
    mascotSpeech = `Sức khỏe shop đạt ${healthScore}/100! Thưởng soup ngon ngọt lịm với pate cho Múp Xám thôi Sen ơi! 🐟✨`;
  } else if (healthScore < 60) {
    mState = 'sad';
    mascotSpeech = `Sức khỏe shop chỉ có ${healthScore}/100 thôi á? Cứu Múp, đói héo hon rồi, ráng chốt đơn mua pate cho Múp đi! 😿`;
  } else {
    mState = 'idle';
    mascotSpeech = `Sức khỏe shop đạt ${healthScore}/100. Buôn bán túc tắc, Sen ráng bán nhiều để mua soup thưởng cho Múp Xám nhé! 🐾`;
  }
  
  updateMascot(mState, mascotSpeech);
}

function appendShopAiMessage(text, type) {
  const windowEl = document.getElementById('shop-ai-chat-window');
  if (!windowEl) return;
  
  if (type === 'user') {
    const msg = document.createElement('div');
    msg.className = 'shop-ai-message user';
    msg.textContent = text;
    windowEl.appendChild(msg);
  } else if (type === 'assistant loading') {
    const container = document.createElement('div');
    container.className = 'chat-mascot-container loading';
    container.innerHTML = `
      <div class="chat-mascot-avatar">
        ${getMascotSvg('thinking')}
      </div>
      <div class="chat-mascot-typing">
        <span>${text}</span>
        <i class="fas fa-spinner fa-spin"></i>
      </div>
    `;
    windowEl.appendChild(container);
  } else {
    // Regular assistant response or warning
    const container = document.createElement('div');
    const isWarning = type.includes('warning');
    container.className = 'chat-mascot-container' + (isWarning ? ' warning' : '');
    
    // Choose mascot icon state based on response text
    let mascotIconState = 'idle';
    if (text.includes('giảm') || text.includes('lỗi') || text.includes('cảnh báo') || text.includes('bom') || isWarning) {
      mascotIconState = 'sad';
    } else if (text.includes('tăng') || text.includes('tốt') || text.includes('vượt trội') || text.includes('chúc mừng')) {
      mascotIconState = 'happy';
    }
    
    // Convert markdown-like headers and bold syntax from Gemini response
    let formattedText = String(text)
      .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
      .replace(/\*(.*?)\*/g, '<i>$1</i>')
      .replace(/\n/g, '<br>');

    container.innerHTML = `
      <div class="chat-mascot-avatar">
        ${getMascotSvg(mascotIconState)}
      </div>
      <div class="chat-mascot-bubble" style="${isWarning ? 'border-color: #ef4444; color: #f87171;' : ''}">
        ${formattedText}
      </div>
    `;
    windowEl.appendChild(container);
  }
  
  windowEl.scrollTop = windowEl.scrollHeight;
}

function removeShopAiLoading() {
  const windowEl = document.getElementById('shop-ai-chat-window');
  if (!windowEl) return;
  const loading = windowEl.querySelector('.chat-mascot-container.loading');
  if (loading) loading.remove();
}

// ─────────────────────────────────────────────
// PRODUCTS PAGE
// ─────────────────────────────────────────────
function loadProducts(forceRefresh) {
  lastSyncRequestTime = Date.now();
  const reqId = ++currentSyncRequestId;
  showSkeletonTable(8);
  google.script.run
    .withSuccessHandler(res => {
      if (reqId !== currentSyncRequestId) return;
      if (!res) return;
      crmSnapshot = res;
      allRows = (res.rows || []).reverse();
      allReportRows = res.reportRows || [];
      filteredRows = [...allRows];
      currentPage = 1;
      buildCustomerHistoryMap();
      applyFilters();
      updateCODBadge();
      updateSyncStatusUI(res);
    })
    .withFailureHandler(e => {
      if (reqId !== currentSyncRequestId) return;
      showToast('Lỗi tải sản phẩm!', 'error');
      renderTable(); // Clear skeleton
    })
    .getCrmSyncSnapshot({ forceRefresh: !!forceRefresh });
}

function applyFilters() {
  const q      = (document.getElementById('filter-search-input')?.value || '').toLowerCase();
  const tt     = document.getElementById('filter-trang-thai')?.value || '';
  const ht     = document.getElementById('filter-hinh-thuc')?.value || '';
  const dFrom  = document.getElementById('filter-date-from')?.value || '';
  const dTo    = document.getElementById('filter-date-to')?.value || '';

  filteredRows = allRows.filter(r => {
    const matchQ  = !q || r.maSP.toLowerCase().includes(q) || (r.tenKhach && r.tenKhach.toLowerCase().includes(q)) || (r.aiChot && r.aiChot.toLowerCase().includes(q));
    const matchTT = !tt || r.trangThai === tt;
    const matchHT = !ht || r.hinhThuc === ht;
    const matchDF = !dFrom || r.ngayChot >= dFrom;
    const matchDT = !dTo   || r.ngayChot <= dTo;
    return matchQ && matchTT && matchHT && matchDF && matchDT;
  });

  // Sort
  if (currentSort.key) {
    filteredRows.sort((a, b) => compareRowsByKey(a, b, currentSort.key, currentSort.dir));
  }

  totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;
  renderTable();
  renderPagination();
  document.getElementById('record-count-label').textContent = filteredRows.length + ' bản ghi';
  updateCODBadge(); // F10: update COD badge on every filter apply
}

function clearFilters() {
  document.getElementById('filter-search-input').value = '';
  document.getElementById('filter-trang-thai').value   = '';
  document.getElementById('filter-hinh-thuc').value    = '';
  document.getElementById('filter-date-from').value    = '';
  document.getElementById('filter-date-to').value      = '';
  currentSort = { key: null, dir: 'asc' };
  applyFilters();
}

function sortTable(key) {
  if (currentSort.key === key) {
    currentSort.dir = currentSort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    currentSort = { key, dir: 'asc' };
  }
  applyFilters();
}

function renderTable() {
  const tbody = document.getElementById('products-tbody');
  const empty = document.getElementById('empty-state-products');
  const table = document.getElementById('products-table');

  const start = (currentPage - 1) * pageSize;
  const pageRows = filteredRows.slice(start, start + pageSize);

  if (filteredRows.length === 0) {
    tbody.innerHTML = '';
    table.style.display = 'none';
    empty.classList.remove('hidden');
    return;
  }
  table.style.display = '';
  empty.classList.add('hidden');

  const fmt = n => new Intl.NumberFormat('vi-VN').format(n);
  const customerTotalsMap = buildCustomerTotalsMap_(filteredRows);

  tbody.innerHTML = pageRows.map(r => {
    const tienLoiClass = r.tienLoi >= 0 ? 'profit-positive' : 'profit-negative';
    const tienLoiSign  = r.tienLoi >= 0 ? '+' : '';

    const hasAnomaly = checkAnomaly(r);
    const ttBadge = getStatusBadge(r.trangThai);

    const htBadge = getShippingBadge(r, '', customerTotalsMap);

    const linkCell = r.linkTiktok
      ? `<a href="${r.linkTiktok}" target="_blank" rel="noopener" style="color:var(--primary-light);text-decoration:underline;font-size:0.8rem;">Xem</a>`
      : '<span class="text-muted">-</span>';
      
    const customerBadge = getCustomerBadgeHtml(r.tenKhach, r.sdtKhach);
    const customerCell = `
      <strong class="customer-name-clickable" onclick="openCustomerProfileModal('${escapeForInlineEdit(r.tenKhach)}', '${escapeForInlineEdit(r.sdtKhach)}')" title="Xem hồ sơ khách hàng">${r.tenKhach || '<span class="text-muted">-</span>'}</strong>${customerBadge}
      ${r.aiChot ? `<br><small>Chốt: ${escapeHtml(r.aiChot)}</small>` : ''}
      ${r.nguonKhach ? `<br><small>Nguồn: ${escapeHtml(r.nguonKhach)}</small>` : ''}
    `;

    const safeMaSP = r.maSP.replace(/'/g, "\\'").replace(/"/g, '');
    const rowClass = hasAnomaly ? 'row-anomaly' : '';
    const rowSheet = getRowSheetName_(r);
    
    // Quick Order action button: Check if row has valid maSP
    const hasValidMaSP = Boolean(r.maSP && String(r.maSP).trim() !== '');
    const isSold = r.trangThai === 'Đã bán';
    let quickOrderBtnHtml = '';
    if (!hasValidMaSP) {
      quickOrderBtnHtml = `<button type="button" class="btn-quick-order btn-disabled" disabled title="Dòng này chưa có Mã SP trong Sheet, không thể tạo đơn!"><i class="fas fa-ban"></i> Chưa có Mã</button>`;
    } else if (isSold) {
      quickOrderBtnHtml = `<button type="button" class="btn-quick-order btn-quick-order-edit" onclick="openQuickOrderModal(${r.rowIndex}, '${rowSheet}')" title="Xem / Cập nhật đơn Viettel Post"><i class="fas fa-check-circle"></i> Đã lên đơn</button>`;
    } else {
      quickOrderBtnHtml = `<button type="button" class="btn-quick-order" onclick="openQuickOrderModal(${r.rowIndex}, '${rowSheet}')" title="⚡ Tạo đơn nhanh Viettel Post cho mã ${escapeHtml(r.maSP)}"><i class="fas fa-bolt"></i> Tạo đơn</button>`;
    }

    return `<tr class="${rowClass}" data-rowindex="${r.rowIndex}" data-sheetname="${rowSheet}" data-masp="${safeMaSP}">
      <td title="${r.maSP}">${r.maSP} <br><span class="badge badge-info" style="font-size:0.65rem; padding: 2px 4px; margin-top:2px; background: #4f46e5; border: none; color: white;">${rowSheet}</span></td>
      <td class="cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'giaBan',${r.giaBan},'${rowSheet}')" title="Click để sửa giá">${fmt(r.giaBan)} ₫</td>
      <td class="col-giavon cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'giaVon',${r.giaVon},'${rowSheet}')" title="Click để sửa giá vốn">${fmt(r.giaVon)} ₫</td>
      <td class="${tienLoiClass}">${tienLoiSign}${fmt(r.tienLoi)} ₫</td>
      <td title="${r.diaChi || r.tenKhach || ''}">${customerCell}</td>
      <td class="col-sdt">${r.sdtKhach || '<span class="text-muted">-</span>'}</td>
      <td>${r.ngayChot ? r.ngayChot : '<span class="text-muted">-</span>'}</td>
      <td class="cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'trangThai','${r.trangThai}','${rowSheet}')" title="Click để đổi trạng thái">${ttBadge}</td>
      <td>${htBadge}</td>
      <td>${r.khachCoc ? fmt(r.khachCoc) + ' ₫' : '<span class="text-muted">-</span>'}</td>
      <td class="col-khoiluong cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'khoiLuong',${r.khoiLuong || 200},'${rowSheet}')" title="Click để sửa khối lượng">${r.khoiLuong || 200}g</td>
      <td class="col-ghichu cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'ghiChu','${escapeForInlineEdit(r.ghiChu)}','${rowSheet}')" title="Click để sửa ghi chú">${escapeHtml(r.ghiChu || '—')}</td>
      <td class="col-linktiktok cell-editable" onclick="if(event.target.tagName !== 'A') startInlineEdit(this,${r.rowIndex},'linkTiktok','${escapeForInlineEdit(r.linkTiktok)}','${rowSheet}')" title="Click để sửa link TikTok">${linkCell}</td>
      <td>${quickOrderBtnHtml}</td>
      <td>
        <div class="action-btns" style="${r.readOnly === true ? 'display:none;' : ''}">
          <button class="btn-action btn-edit" onclick="openEditModal(${r.rowIndex}, '${rowSheet}')" title="Sửa"><i class="fas fa-pencil-alt"></i></button>
          <button class="btn-action btn-copy" onclick="copyOrderToClipboard(${r.rowIndex}, '${rowSheet}')" title="Sao chép thông tin"><i class="far fa-copy"></i></button>
          <button class="btn-action btn-ship" onclick="markAsShipped(${r.rowIndex}, '${rowSheet}')" title="Đã giao"><i class="fas fa-truck"></i></button>
          <button class="btn-action btn-cancel" onclick="markAsCancelled(${r.rowIndex}, '${rowSheet}')" title="Hủy"><i class="fas fa-ban"></i></button>
        </div>
      </td>
    </tr>`;
  }).join('');

  // Totals calculations
  let totalGB = 0, totalGV = 0, totalTL = 0, totalCoc = 0, totalCOD = 0;
  filteredRows.forEach(r => {
    if (!isDeletedInternal_(r.trangThai)) {
      totalGB += Number(r.giaBan || 0);
      totalGV += Number(r.giaVon || 0);
      totalTL += Number(r.tienLoi || 0);
      totalCoc += Number(r.khachCoc || 0);
      if (r.hinhThuc === 'COD') {
        totalCOD += Number(r.tienCOD || 0);
      }
    }
  });

  const tfoot = document.getElementById('products-tfoot');
  if (tfoot) {
    tfoot.innerHTML = `
      <tr>
        <td><strong>TỔNG CỘNG</strong></td>
        <td><strong>${fmtVnd(totalGB)}</strong></td>
        <td class="col-giavon"><strong>${fmtVnd(totalGV)}</strong></td>
        <td class="${totalTL >= 0 ? 'profit-positive' : 'profit-negative'}"><strong>${totalTL >= 0 ? '+' : ''}${fmtVnd(totalTL)}</strong></td>
        <td><strong>${filteredRows.length} dòng</strong></td>
        <td class="col-sdt"></td>
        <td></td>
        <td></td>
        <td></td>
        <td><strong>Cọc: ${fmtVnd(totalCoc)}<br>COD: ${fmtVnd(totalCOD)}</strong></td>
        <td class="col-khoiluong"></td>
        <td class="col-ghichu"></td>
        <td class="col-linktiktok"></td>
        <td></td>
        <td></td>
      </tr>
    `;
  }

  attachSwipeHandlers(); // F15
}
// ─────────────────────────────────────────────
// PAGINATION
// ─────────────────────────────────────────────
function renderPagination() {
  const start = (currentPage - 1) * pageSize;
  const end   = Math.min(start + pageSize, filteredRows.length);
  document.getElementById('pagination-info').textContent = `Hiển thị ${start+1}–${end} / ${filteredRows.length}`;

  const numContainer = document.getElementById('page-numbers');
  numContainer.innerHTML = '';
  const range = getPageRange(currentPage, totalPages);
  range.forEach(p => {
    if (p === '...') {
      const el = document.createElement('span');
      el.className = 'page-num-btn'; el.textContent = '…'; el.style.cursor = 'default';
      numContainer.appendChild(el);
    } else {
      const btn = document.createElement('button');
      btn.className = 'page-num-btn' + (p === currentPage ? ' active' : '');
      btn.textContent = p;
      btn.onclick = () => goToPage(p);
      numContainer.appendChild(btn);
    }
  });

  document.getElementById('page-first').disabled = currentPage <= 1;
  document.getElementById('page-prev').disabled  = currentPage <= 1;
  document.getElementById('page-next').disabled  = currentPage >= totalPages;
  document.getElementById('page-last').disabled  = currentPage >= totalPages;
}

function getPageRange(cur, total) {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages = [1];
  if (cur > 3) pages.push('...');
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i);
  if (cur < total - 2) pages.push('...');
  pages.push(total);
  return pages;
}

function goToPage(p) {
  currentPage = Math.max(1, Math.min(p, totalPages));
  renderTable(); renderPagination();
}
function prevPage() { goToPage(currentPage - 1); }
function nextPage() { goToPage(currentPage + 1); }
function changePageSize(val) {
  pageSize = parseInt(val);
  currentPage = 1;
  applyFilters();
}

// ──────────────────────────────────────────────
// LIQUIDATION PAGE
// ─────────────────────────────────────────────
function loadLiquidationRows() {
  showLoading('Đang tải sheet THANH LÝ...');
  google.script.run
    .withSuccessHandler(rows => {
      liquidationRows = rows || [];
      filteredLiquidationRows = [...liquidationRows];
      liquidationPage = 1;
      applyLiquidationFilters();
      hideLoading();
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Không tải được sheet THANH LÝ: ' + e.message, 'error');
    })
    .getLiquidationRows();
}

function applyLiquidationFilters() {
  const q = (document.getElementById('liquidation-search-input')?.value || '').toLowerCase().trim();
  const status = document.getElementById('liquidation-status-filter')?.value || '';
  const dFrom = document.getElementById('liquidation-date-from')?.value || '';
  const dTo = document.getElementById('liquidation-date-to')?.value || '';

  filteredLiquidationRows = liquidationRows.filter(r => {
    const haystack = [
      r.maSP, r.sanPham, r.tenKhach, r.sdtKhach, r.aiChot, r.ghiChu, r.loaiDon
    ].join(' ').toLowerCase();
    const matchQ = !q || haystack.includes(q);
    const matchStatus = !status || r.trangThai === status || r.trangThaiGoc === status;
    const matchFrom = !dFrom || (r.ngayChot && r.ngayChot >= dFrom);
    const matchTo = !dTo || (r.ngayChot && r.ngayChot <= dTo);
    return matchQ && matchStatus && matchFrom && matchTo;
  });

  filteredLiquidationRows.sort((a, b) => compareRowsByKey(a, b, liquidationSort.key, liquidationSort.dir));
  liquidationTotalPages = Math.max(1, Math.ceil(filteredLiquidationRows.length / liquidationPageSize));
  if (liquidationPage > liquidationTotalPages) liquidationPage = liquidationTotalPages;
  renderLiquidationTable();
  renderLiquidationPagination();
  const countEl = document.getElementById('liquidation-count-label');
  if (countEl) countEl.textContent = filteredLiquidationRows.length + ' bản ghi';
}

function clearLiquidationFilters() {
  document.getElementById('liquidation-search-input').value = '';
  document.getElementById('liquidation-status-filter').value = '';
  document.getElementById('liquidation-date-from').value = '';
  document.getElementById('liquidation-date-to').value = '';
  liquidationSort = { key: 'ngayChot', dir: 'desc' };
  liquidationPage = 1;
  applyLiquidationFilters();
}

function sortLiquidationTable(key) {
  if (liquidationSort.key === key) {
    liquidationSort.dir = liquidationSort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    liquidationSort = { key, dir: key === 'ngayChot' || key === 'giaBan' ? 'desc' : 'asc' };
  }
  applyLiquidationFilters();
}

function renderLiquidationTable() {
  const tbody = document.getElementById('liquidation-tbody');
  const table = document.getElementById('liquidation-table');
  const empty = document.getElementById('empty-state-liquidation');
  if (!tbody || !table || !empty) return;

  const start = (liquidationPage - 1) * liquidationPageSize;
  const rows = filteredLiquidationRows.slice(start, start + liquidationPageSize);

  if (!filteredLiquidationRows.length) {
    tbody.innerHTML = '';
    table.style.display = 'none';
    empty.classList.remove('hidden');
    return;
  }

  table.style.display = '';
  empty.classList.add('hidden');

  tbody.innerHTML = rows.map(r => {
    const profitVal = Number(r.tienLoi || 0);
    const profitClass = profitVal >= 0 ? 'profit-positive' : 'profit-negative';
    const statusText = r.trangThaiGoc || r.trangThai || '—';
    const productText = r.sanPham ? `${escapeHtml(r.maSP || '—')}<br><small>${escapeHtml(r.sanPham)}</small>` : escapeHtml(r.maSP || '—');

    return `<tr>
      <td>${escapeHtml(r.ngayChot || '—')}</td>
      <td>${productText}</td>
      <td>${escapeHtml(r.tenKhach || '—')}</td>
      <td>${escapeHtml(r.sdtKhach || '—')}</td>
      <td><strong>${fmtVnd(r.giaBan)}</strong></td>
      <td>${r.giaVon ? fmtVnd(r.giaVon) : '<span class="text-muted">—</span>'}</td>
      <td class="${profitClass}">${profitVal >= 0 ? '+' : ''}${fmtVnd(profitVal)}</td>
      <td><span class="badge badge-muted">${escapeHtml(statusText)}</span></td>
      <td><span class="badge badge-info">${escapeHtml(r.loaiDon || r.sourceSheet || 'THANH LÝ')}</span></td>
      <td title="${escapeHtml(r.ghiChu || '')}">${escapeHtml(r.ghiChu || '—')}</td>
    </tr>`;
  }).join('');
}

function renderLiquidationPagination() {
  const start = filteredLiquidationRows.length ? (liquidationPage - 1) * liquidationPageSize + 1 : 0;
  const end = Math.min(liquidationPage * liquidationPageSize, filteredLiquidationRows.length);
  const info = document.getElementById('liquidation-pagination-info');
  if (info) info.textContent = `Hiển thị ${start}–${end} / ${filteredLiquidationRows.length}`;

  const numContainer = document.getElementById('liquidation-page-numbers');
  if (numContainer) {
    numContainer.innerHTML = '';
    getPageRange(liquidationPage, liquidationTotalPages).forEach(p => {
      if (p === '...') {
        const el = document.createElement('span');
        el.className = 'page-num-btn';
        el.textContent = '…';
        numContainer.appendChild(el);
      } else {
        const btn = document.createElement('button');
        btn.className = 'page-num-btn' + (p === liquidationPage ? ' active' : '');
        btn.textContent = p;
        btn.onclick = () => goToLiquidationPage(p);
        numContainer.appendChild(btn);
      }
    });
  }

  document.getElementById('liquidation-page-first').disabled = liquidationPage <= 1;
  document.getElementById('liquidation-page-prev').disabled = liquidationPage <= 1;
  document.getElementById('liquidation-page-next').disabled = liquidationPage >= liquidationTotalPages;
  document.getElementById('liquidation-page-last').disabled = liquidationPage >= liquidationTotalPages;
}

function goToLiquidationPage(page) {
  liquidationPage = Math.max(1, Math.min(Number(page) || 1, liquidationTotalPages));
  renderLiquidationTable();
  renderLiquidationPagination();
}

// ─────────────────────────────────────────────
// MODAL HELPERS
// ─────────────────────────────────────────────
function openModal(id)    { document.getElementById(id).classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
function closeModal(id)   { document.getElementById(id).classList.add('hidden'); document.body.style.overflow = ''; }
function closeModalOnOutside(e) {
  const card = e.currentTarget.querySelector('.modal-card');
  if (!card.contains(e.target)) closeModal(e.currentTarget.id);
}

// ─────────────────────────────────────────────
// ADD MODAL
// ─────────────────────────────────────────────
function openAddModal() {
  document.getElementById('modal-title').innerHTML = '<i class="fas fa-plus-circle"></i> Thêm sản phẩm';
  document.getElementById('modal-save-btn').innerHTML = '<i class="fas fa-save"></i> Thêm';
  document.getElementById('edit-row-index').value = '';
  const editSheetEl = document.getElementById('edit-sheet-name');
  if (editSheetEl) editSheetEl.value = '';
  clearModalForm();
  openModal('modal-product');
}

function getRowSheetName_(row) {
  return String(row?.sourceSheet || row?.sheetName || 'SalesData').trim() || 'SalesData';
}

function isClientEditableSheet_(sheetName) {
  return ['SalesData', 'Mã V'].includes(String(sheetName || 'SalesData').trim());
}

function findEditableRowByIndex(rowIndex, sheetName) {
  const safeRowIndex = Number(rowIndex);
  const targetSheet = String(sheetName || '').trim();
  const isEditableRow = r => {
    if (!r || Number(r.rowIndex) !== safeRowIndex) return false;
    const rowSheet = getRowSheetName_(r);
    if (targetSheet && rowSheet !== targetSheet) return false;
    return r.readOnly !== true || isClientEditableSheet_(rowSheet);
  };
  return allRows.find(isEditableRow) || allReportRows.find(isEditableRow) || null;
}

function openEditModal(rowIndex, sheetName) {
  const row = findEditableRowByIndex(rowIndex, sheetName);
  if (!row) { showToast('Không tìm thấy dữ liệu hoặc sheet này chưa hỗ trợ sửa!', 'error'); return; }
  const rowSheet = getRowSheetName_(row);

  document.getElementById('modal-title').innerHTML = '<i class="fas fa-pencil-alt"></i> Sửa sản phẩm';
  document.getElementById('modal-save-btn').innerHTML = '<i class="fas fa-save"></i> Lưu thay đổi';
  document.getElementById('edit-row-index').value     = rowIndex;
  const editSheetEl = document.getElementById('edit-sheet-name');
  if (editSheetEl) editSheetEl.value = rowSheet;

  document.getElementById('input-masp').value       = row.maSP;
  document.getElementById('input-giaban').value     = row.giaBan;
  document.getElementById('input-giavon').value     = row.giaVon;
  document.getElementById('input-tenkhach').value   = row.tenKhach || '';
  document.getElementById('input-sdtkhach').value   = row.sdtKhach || '';
  document.getElementById('input-aichot').value     = row.aiChot || '';
  document.getElementById('input-nguonkhach').value = row.nguonKhach || '';
  document.getElementById('input-diachi').value     = row.diaChi || '';
  document.getElementById('input-ngaychot').value   = row.ngayChot   || '';
  document.getElementById('input-trangthai').value  = row.trangThai  || 'Còn hàng';
  document.getElementById('input-hinhthuc').value   = row.hinhThuc   || 'COD';
  const explicitCod = (row.tienCOD !== undefined && row.tienCOD !== null && row.tienCOD !== '') ? Number(row.tienCOD) : null;
  window._userManuallyEditedProductCod = (explicitCod !== null);
  if (document.getElementById('input-tiencod')) {
    document.getElementById('input-tiencod').value = explicitCod !== null ? explicitCod : 0;
  }
  if (document.getElementById('input-ghichu'))    document.getElementById('input-ghichu').value    = row.ghiChu    || '';
  document.getElementById('input-khachcoc').value   = row.khachCoc   || 0;
  document.getElementById('input-linktiktok').value = row.linkTiktok || '';
  calcProfit();
  openModal('modal-product');
  loadCustomerHistory(row.sdtKhach || '', rowIndex);
}

function clearModalForm() {
  window._userManuallyEditedProductCod = false;
  ['input-masp','input-giaban','input-giavon','input-tenkhach','input-sdtkhach',
   'input-aichot','input-nguonkhach','input-diachi','input-ngaychot','input-khachcoc',
   'input-tiencod','input-ghichu','input-linktiktok'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('input-trangthai').value = 'Còn hàng';
  document.getElementById('input-hinhthuc').value  = 'COD';
  document.getElementById('preview-tien-loi').textContent = '0 ₫';
  showGiaVonHint(0);
  renderCustomerHistory(null);
}

function calcProfit() {
  const gb = parseFloat(document.getElementById('input-giaban').value) || 0;
  const gv = parseFloat(document.getElementById('input-giavon').value) || 0;
  const tl = gb - gv;
  const el = document.getElementById('preview-tien-loi');
  el.textContent = (tl >= 0 ? '+' : '') + new Intl.NumberFormat('vi-VN').format(tl) + ' ₫';
  el.style.color = tl >= 0 ? 'var(--success)' : 'var(--danger)';
  calcCOD(); // auto-update tiền COD whenever prices change
}

function onProductCodInput() {
  window._userManuallyEditedProductCod = true;
}

function calcCOD() {
  const ht  = document.getElementById('input-hinhthuc')?.value;
  if (ht !== 'COD') {
    const codEl = document.getElementById('input-tiencod');
    if (codEl) codEl.value = 0;
    return;
  }

  const gb  = parseFloat(document.getElementById('input-giaban').value)   || 0;
  const coc = parseFloat(document.getElementById('input-khachcoc').value)  || 0;
  const codEl = document.getElementById('input-tiencod');
  if (!codEl) return;

  // Nếu user đã chủ động nhập tiền COD (kể cả khi nhập 0) hoặc đơn có COD cụ thể, không tự ý đè lại giá bán
  if (window._userManuallyEditedProductCod) return;

  const autoVal = coc <= 0 ? gb : Math.max(0, gb - coc);
  codEl.value = autoVal;
}

// ─────────────────────────────────────────────
// AUTO-FILL GIÁ VỐN từ MÃ SP
// ─────────────────────────────────────────────
function autoFillFromMaSP() {
  const masp = document.getElementById('input-masp').value.trim().toLowerCase();
  const vonEl = document.getElementById('input-giavon');
  const isEditing = !!document.getElementById('edit-row-index').value;

  if (isEditing) return; // Không auto-fill khi đang sửa
  if (!masp || masp.length < 2) { showGiaVonHint(0); return; }

  // Tìm trong allRows có sẵn — thuần client-side, không gọi backend
  const pool = allRows.length ? allRows : allReportRows;
  const match =
    pool.find(r => String(r.maSP || '').trim().toLowerCase() === masp) ||
    pool.find(r => String(r.maSP || '').trim().toLowerCase().startsWith(masp));

  if (match && Number(match.giaVon) > 0) {
    showGiaVonHint(match.giaVon);
    // Chỉ điền nếu ô giá vốn đang rỗng / bằng 0
    if (!vonEl.value || parseFloat(vonEl.value) === 0) {
      vonEl.value = match.giaVon;
      calcProfit();
    }
  } else {
    showGiaVonHint(0);
  }
}

function showGiaVonHint(value) {
  const hint = document.getElementById('giavon-hint');
  if (!hint) return;
  if (value > 0) {
    hint.innerHTML = `<button type="button" onclick="applyGiaVonHint(${value})"
      style="font-size:0.72rem;padding:2px 10px;margin-top:5px;cursor:pointer;
             display:inline-flex;align-items:center;gap:5px;
             background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.3);
             border-radius:6px;color:var(--primary-light);">
      ↩ Dùng lại: <strong>${new Intl.NumberFormat('vi-VN').format(value)} ₫</strong></button>`;
  } else {
    hint.innerHTML = '';
  }
}

function applyGiaVonHint(val) {
  document.getElementById('input-giavon').value = val;
  calcProfit();
}

function debouncedLoadCustomerHistory() {
  clearTimeout(customerHistoryTimer);
  customerHistoryTimer = setTimeout(() => {
    const phone = document.getElementById('input-sdtkhach')?.value || '';
    const rowIndex = document.getElementById('edit-row-index')?.value || '';
    loadCustomerHistory(phone, rowIndex);
  }, 450);
}

function loadCustomerHistory(phone, rowIndex) {
  const cleanPhone = String(phone || '').replace(/[^\d]/g, '');
  if (cleanPhone.length < 8) {
    renderCustomerHistory(null);
    return;
  }

  renderCustomerHistory({ loading: true });
  google.script.run
    .withSuccessHandler(renderCustomerHistory)
    .withFailureHandler(() => renderCustomerHistory({ error: true }))
    .getCustomerHistoryByPhone(phone, rowIndex || '');
}

function renderCustomerHistory(data) {
  const panel = document.getElementById('customer-history-panel');
  if (!panel) return;

  if (!data) {
    panel.classList.add('hidden');
    panel.innerHTML = '';
    return;
  }

  panel.classList.remove('hidden');
  if (data.loading) {
    panel.innerHTML = '<div class="customer-history-head"><span><i class="fas fa-spinner fa-spin"></i> Đang kiểm tra lịch sử khách...</span></div>';
    return;
  }
  if (data.error) {
    panel.innerHTML = '<div class="customer-history-head"><span>Không kiểm tra được lịch sử khách lúc này</span></div>';
    return;
  }
  if (!data.found) {
    panel.innerHTML = `
      <div class="customer-history-head" style="margin-bottom: 0; align-items: center;">
        <span><i class="fas fa-user-clock"></i> Lịch sử khách</span>
        <span class="badge badge-info" style="font-size: 0.7rem; padding: 3px 8px; margin-left: auto;"><i class="fas fa-user-plus fa-xs"></i> Khách hàng mới</span>
      </div>
    `;
    return;
  }

  const summary = data.summary || {};
  const rows = data.rows || [];

  let badgesHtml = '';
  if (summary.hasBomHistory) {
    badgesHtml += `<span class="badge badge-danger" style="font-size: 0.7rem; padding: 3px 8px; margin-left: 6px;">Cảnh báo bom hàng</span>`;
  }
  if (summary.successfulOrders > 3 && summary.successfulRevenue > 2000000) {
    badgesHtml += `<span class="badge badge-success" style="font-size: 0.7rem; padding: 3px 8px; margin-left: 6px; background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.25); color: var(--success);"><i class="fas fa-crown fa-xs" style="color: gold;"></i> Khách VIP</span>`;
  }

  panel.innerHTML = `
    <div class="customer-history-head">
      <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 4px;">
        <span><i class="fas fa-user-clock"></i> Lịch sử khách</span>
        ${badgesHtml}
      </div>
      <span>${fmtNum(summary.totalOrders)} đơn · ${fmtVnd(summary.totalRevenue)}</span>
    </div>
    <div style="margin-bottom: 8px;">
      Gần nhất: <strong>${escapeHtml(summary.lastOrderDate || '—')}</strong>
      ${summary.pendingOrders ? ` · <span class="text-warning">${fmtNum(summary.pendingOrders)} đơn đợi CK</span>` : ''}
      ${summary.deletedOrders ? ` · <span class="text-danger">${fmtNum(summary.deletedOrders)} đơn đã xóa</span>` : ''}
    </div>
    <div class="customer-history-list">
      ${rows.map(r => `
        <div class="customer-history-item">
          <span title="${escapeHtml(r.maSP || '')}"><strong>${escapeHtml(r.maSP || '—')}</strong> · ${escapeHtml(r.trangThai || '—')}</span>
          <span>${escapeHtml(r.ngayChot || '—')}</span>
          <span>${fmtVnd(r.giaBan)}</span>
        </div>
      `).join('')}
    </div>
  `;
}

// ─────────────────────────────────────────────
// SAVE PRODUCT (ADD / EDIT)
// ─────────────────────────────────────────────
function saveProduct() {
  const masp    = document.getElementById('input-masp').value.trim();
  const giaBan  = parseFloat(document.getElementById('input-giaban').value) || 0;
  const giaVon  = parseFloat(document.getElementById('input-giavon').value) || 0;

  if (!masp) { showToast('Vui lòng nhập MÃ SP!', 'warning'); document.getElementById('input-masp').focus(); return; }
  if (giaBan <= 0) { showToast('Giá bán phải lớn hơn 0!', 'warning'); return; }

  const data = {
    maSP      : masp,
    giaBan,
    giaVon,
    tenKhach  : document.getElementById('input-tenkhach').value.trim(),
    sdtKhach  : document.getElementById('input-sdtkhach').value.trim(),
    aiChot    : document.getElementById('input-aichot').value.trim(),
    nguonKhach: document.getElementById('input-nguonkhach').value,
    diaChi    : document.getElementById('input-diachi').value.trim(),
    ngayChot  : document.getElementById('input-ngaychot').value,
    trangThai : document.getElementById('input-trangthai').value,
    hinhThuc  : document.getElementById('input-hinhthuc').value,
    tienCOD   : parseFloat(document.getElementById('input-tiencod')?.value)   || 0,
    ghiChu    : document.getElementById('input-ghichu')?.value?.trim()        || '',
    khachCoc  : parseFloat(document.getElementById('input-khachcoc').value)   || 0,
    linkTiktok: document.getElementById('input-linktiktok').value.trim()
  };

  const rowIdx = document.getElementById('edit-row-index').value;
  const rowSheet = document.getElementById('edit-sheet-name')?.value || 'SalesData';
  const btn    = document.getElementById('modal-save-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';

  const handler = result => {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-save"></i> Lưu';
    if (result && result.success) {
      showToast(result.message, 'success');
      closeModal('modal-product');

      // Trigger Ka-Ching & Confetti
      try {
        if (typeof playKaChingSound === 'function') playKaChingSound();
        if (typeof fireConfetti3D === 'function') fireConfetti3D();
      } catch (e) {
        console.warn('Sound/Confetti trigger error:', e);
      }

      // Optimistic update: cập nhật bảng, không chờ reload toàn trang
      if (rowIdx) {
        const safeIdx = parseInt(rowIdx);
        const localIdx = allRows.findIndex(r => Number(r.rowIndex) === safeIdx && getRowSheetName_(r) === rowSheet);
        if (localIdx !== -1) {
          allRows[localIdx] = Object.assign({}, allRows[localIdx], {
            maSP: data.maSP, giaBan: data.giaBan, giaVon: data.giaVon,
            tienLoi: data.giaBan - data.giaVon, tenKhach: data.tenKhach,
            sdtKhach: data.sdtKhach, aiChot: data.aiChot,
            nguonKhach: data.nguonKhach, diaChi: data.diaChi,
            ngayChot: data.ngayChot, trangThai: data.trangThai,
            hinhThuc: data.hinhThuc, tienCOD: data.tienCOD,
            ghiChu: data.ghiChu, khachCoc: data.khachCoc,
            linkTiktok: data.linkTiktok
          });
        }
      } else if (result.row) {
        allRows.unshift(result.row);
      }
      filteredRows = [...allRows];
      applyFilters();
      const dailyPage = document.getElementById('page-daily');
      if (dailyPage && !dailyPage.classList.contains('hidden')) loadDailyOrders();

      // Background sync sau 2s — không hiện loading overlay, không block UI
      setTimeout(() => {
        google.script.run
          .withSuccessHandler(res => {
            if (!res) return;
            crmSnapshot = res;
            allRows = (res.rows || []).reverse();
            allReportRows = res.reportRows || [];
            filteredRows = [...allRows];
            applyFilters();
            updateSyncStatusUI(res);
            if (res.stats && res.stats.notifications) {
              renderNotifications(res.stats.notifications);
            }
          })
          .getCrmSyncSnapshot({ forceRefresh: false });
      }, 2000);
    } else {
      showToast('Lỗi khi lưu dữ liệu!', 'error');
    }
  };
  const failHandler = e => {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-save"></i> Lưu';
    showToast('Lỗi kết nối: ' + e.message, 'error');
  };

  if (rowIdx) {
    google.script.run.withSuccessHandler(handler).withFailureHandler(failHandler).updateRow(parseInt(rowIdx), data, rowSheet);
  } else {
    google.script.run.withSuccessHandler(handler).withFailureHandler(failHandler).addRow(data, rowSheet);
  }
}

// ─────────────────────────────────────────────
// SEARCH & STRING HELPERS
// ─────────────────────────────────────────────
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

function getTodayString_() {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

// ─────────────────────────────────────────────
// QUICK ORDER VIETTEL POST (TẠO ĐƠN NHANH)
// ─────────────────────────────────────────────
function openQuickOrderModal(rowIndex, sheetName) {
  const row = findEditableRowByIndex(rowIndex, sheetName);
  if (!row) {
    showToast('Không tìm thấy dữ liệu sản phẩm!', 'error');
    return;
  }

  // RÀNG BUỘC THEO MÃ SẢN PHẨM: Nếu chưa có mã trong sheet thì TUYỆT ĐỐI không cho tạo đơn
  const maSP = String(row.maSP || '').trim();
  if (!maSP) {
    showToast('Lỗi: Dòng này chưa có Mã sản phẩm trong Sheet! Vui lòng nhập Mã SP trước khi tạo đơn.', 'error');
    return;
  }

  const rowSheet = getRowSheetName_(row);
  document.getElementById('quick-order-row-index').value = rowIndex;
  document.getElementById('quick-order-sheet-name').value = rowSheet;

  // Set snapshot banner
  const maspVal = document.getElementById('quick-order-masp-val');
  const maspInput = document.getElementById('quick-order-masp-input');
  const maspHint = document.getElementById('quick-order-masp-hint');
  const btnSave = document.getElementById('btn-save-quick-order');

  if (maspVal) {
    maspVal.classList.remove('hidden');
    maspVal.textContent = maSP;
  }
  if (maspInput) {
    maspInput.classList.add('hidden');
    maspInput.value = maSP;
  }
  if (maspHint) {
    maspHint.style.display = 'none';
  }
  if (btnSave) btnSave.disabled = false;

  document.getElementById('quick-order-masp').value = maSP;
  document.getElementById('quick-order-giaban-val').textContent = fmtVnd(row.giaBan || 0);
  document.getElementById('quick-order-giaban').value = row.giaBan || 0;

  const statusBadge = document.getElementById('quick-order-status-badge');
  if (statusBadge) {
    statusBadge.textContent = row.trangThai || 'Còn hàng';
    statusBadge.className = 'badge ' + (row.trangThai === 'Đã bán' ? 'badge-success' : (row.trangThai === 'Đợi CK' ? 'badge-warning' : 'badge-info'));
  }

  // Populate fields
  document.getElementById('quick-order-tenkhach').value = row.tenKhach || '';
  document.getElementById('quick-order-sdtkhach').value = row.sdtKhach || '';
  document.getElementById('quick-order-diachi').value   = row.diaChi || '';
  document.getElementById('quick-order-hinhthuc').value = row.hinhThuc || 'COD';
  document.getElementById('quick-order-khoiluong').value = row.khoiLuong || 200;
  document.getElementById('quick-order-khachcoc').value = row.khachCoc || 0;
  const explicitQuickCod = (row.tienCOD !== undefined && row.tienCOD !== null && row.tienCOD !== '') ? Number(row.tienCOD) : null;
  window._quickOrderUserEditedCod = (explicitQuickCod !== null);
  const quickCodEl = document.getElementById('quick-order-tiencod');
  if (quickCodEl) {
    quickCodEl.value = explicitQuickCod !== null ? explicitQuickCod : 0;
  }
  document.getElementById('quick-order-aichot').value   = row.aiChot || '';
  if (document.getElementById('quick-order-nguonkhach')) {
    document.getElementById('quick-order-nguonkhach').value = row.nguonKhach || 'TikTok Live';
  }

  if (document.getElementById('quick-order-loaihang')) {
    document.getElementById('quick-order-loaihang').value = row.loaiHangHoa || 'Bưu kiện';
  }
  if (document.getElementById('quick-order-tinhchat')) {
    document.getElementById('quick-order-tinhchat').value = row.tinhChatHangHoa || '';
  }
  if (document.getElementById('quick-order-dichvu')) {
    let rawDv = row.dichVu || '';
    if (rawDv === 'NCOD') rawDv = 'TMĐT Tiết Kiệm thỏa thuận';
    else if (rawDv === 'VTK') rawDv = 'CP tiết kiệm thỏa thuận';
    else if (rawDv === 'PHS' || rawDv.startsWith('PHS')) rawDv = 'Nội tỉnh tiết kiệm';
    else if (rawDv === 'VCN') rawDv = 'CP nhanh thỏa thuận';
    else if (rawDv === 'VHT') rawDv = 'Hỏa tốc thỏa thuận';
    if (!rawDv) {
      rawDv = (row.hinhThuc === 'Freeship' || (row.tienCOD || 0) <= 0) ? 'CP tiết kiệm thỏa thuận' : 'TMĐT Tiết Kiệm thỏa thuận';
    }
    document.getElementById('quick-order-dichvu').value = rawDv;
  }
  if (document.getElementById('quick-order-dvct')) {
    let rawDvct = row.dichVuCongThem;
    if (rawDvct === undefined || rawDvct === null || rawDvct === 'Khai giá') {
      rawDvct = (row.hinhThuc === 'Freeship' || (row.tienCOD || 0) <= 0) ? 'PXD' : 'COD, PXD';
    }
    const currentDv = document.getElementById('quick-order-dichvu')?.value || '';
    if (currentDv === 'Nội tỉnh tiết kiệm' || currentDv.includes('Nội tỉnh') || (row.diaChi && row.diaChi.includes('Hà Nội'))) {
      rawDvct = String(rawDvct).replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
      if (!rawDvct) rawDvct = (row.tienCOD > 0) ? 'COD, PXD' : 'PXD';
    }
    document.getElementById('quick-order-dvct').value = rawDvct;
  }

  // Ghi chú mẫu: Mặc định là 'CHO HÀNG XEM'
  const noteVal = row.ghiChu && row.ghiChu.trim() ? row.ghiChu : 'CHO HÀNG XEM';
  document.getElementById('quick-order-ghichu').value = noteVal;
  updateQuickNoteActiveTag(noteVal);

  calcQuickOrderCOD();
  openModal('modal-quick-order');

  // Auto-focus phone or name
  setTimeout(() => {
    const sdtInput = document.getElementById('quick-order-sdtkhach');
    if (sdtInput && !sdtInput.value) {
      sdtInput.focus();
    } else {
      const tenInput = document.getElementById('quick-order-tenkhach');
      if (tenInput && !tenInput.value) tenInput.focus();
      else if (document.getElementById('quick-order-diachi')) document.getElementById('quick-order-diachi').focus();
    }
  }, 150);
}

function openQuickOrderFromToolbar() {
  document.getElementById('quick-order-row-index').value = '';
  document.getElementById('quick-order-sheet-name').value = 'SalesData';

  const maspVal = document.getElementById('quick-order-masp-val');
  const maspInput = document.getElementById('quick-order-masp-input');
  const maspHint = document.getElementById('quick-order-masp-hint');
  const btnSave = document.getElementById('btn-save-quick-order');

  if (maspVal) maspVal.classList.add('hidden');
  if (maspInput) {
    maspInput.classList.remove('hidden');
    maspInput.value = '';
  }
  if (maspHint) {
    maspHint.style.display = 'block';
    maspHint.style.color = 'var(--text-muted)';
    maspHint.textContent = 'Nhập Mã SP có sẵn trong Sheet để tạo đơn';
  }

  document.getElementById('quick-order-masp').value = '';
  document.getElementById('quick-order-giaban-val').textContent = '0 ₫';
  document.getElementById('quick-order-giaban').value = 0;

  const statusBadge = document.getElementById('quick-order-status-badge');
  if (statusBadge) {
    statusBadge.textContent = 'Đơn mới';
    statusBadge.className = 'badge badge-info';
  }

  document.getElementById('quick-order-tenkhach').value = '';
  document.getElementById('quick-order-sdtkhach').value = '';
  document.getElementById('quick-order-diachi').value = '';
  document.getElementById('quick-order-hinhthuc').value = 'COD';
  document.getElementById('quick-order-khoiluong').value = 200;
  document.getElementById('quick-order-khachcoc').value = 0;
  window._quickOrderUserEditedCod = false;
  const toolbarQuickCodEl = document.getElementById('quick-order-tiencod');
  if (toolbarQuickCodEl) toolbarQuickCodEl.value = 0;
  document.getElementById('quick-order-aichot').value = '';
  if (document.getElementById('quick-order-nguonkhach')) {
    document.getElementById('quick-order-nguonkhach').value = 'TikTok Live';
  }

  if (document.getElementById('quick-order-loaihang')) {
    document.getElementById('quick-order-loaihang').value = 'Bưu kiện';
  }
  if (document.getElementById('quick-order-tinhchat')) {
    document.getElementById('quick-order-tinhchat').value = '';
  }
  if (document.getElementById('quick-order-dichvu')) {
    document.getElementById('quick-order-dichvu').value = 'NCOD';
  }
  if (document.getElementById('quick-order-dvct')) {
    document.getElementById('quick-order-dvct').value = 'COD, PXD';
  }

  document.getElementById('quick-order-ghichu').value = 'CHO HÀNG XEM';
  updateQuickNoteActiveTag('CHO HÀNG XEM');
  calcQuickOrderCOD();

  if (btnSave) btnSave.disabled = true;

  openModal('modal-quick-order');
  setTimeout(() => {
    if (maspInput) maspInput.focus();
  }, 150);
}

function onQuickOrderMaspInput(val) {
  const query = String(val || '').trim();
  const maspHint = document.getElementById('quick-order-masp-hint');
  const btnSave = document.getElementById('btn-save-quick-order');
  const maspHidden = document.getElementById('quick-order-masp');

  if (!query) {
    if (maspHint) {
      maspHint.style.display = 'block';
      maspHint.style.color = 'var(--text-muted)';
      maspHint.textContent = 'Vui lòng nhập Mã SP để tạo đơn';
    }
    if (btnSave) btnSave.disabled = true;
    maspHidden.value = '';
    return;
  }

  const applyFoundProduct = (found) => {
    maspHidden.value = found.maSP;
    document.getElementById('quick-order-row-index').value = found.rowIndex || '';
    document.getElementById('quick-order-sheet-name').value = getRowSheetName_(found);
    document.getElementById('quick-order-giaban-val').textContent = fmtVnd(found.giaBan || 0);
    document.getElementById('quick-order-giaban').value = found.giaBan || 0;

    const statusBadge = document.getElementById('quick-order-status-badge');
    if (statusBadge) {
      statusBadge.textContent = found.trangThai || 'Còn hàng';
      statusBadge.className = 'badge ' + (found.trangThai === 'Đã bán' ? 'badge-success' : (found.trangThai === 'Đợi CK' ? 'badge-warning' : 'badge-info'));
    }

    if (found.hinhThuc) {
      document.getElementById('quick-order-hinhthuc').value = found.hinhThuc;
    }

    const curHinhThuc = document.getElementById('quick-order-hinhthuc')?.value || found.hinhThuc || 'COD';
    if (curHinhThuc === 'Freeship') {
      document.getElementById('quick-order-khachcoc').value = found.giaBan || 0;
    } else if (found.khachCoc !== undefined && found.khachCoc !== null && found.khachCoc !== '') {
      document.getElementById('quick-order-khachcoc').value = found.khachCoc;
    }

    if (found.tenKhach && !document.getElementById('quick-order-tenkhach').value) {
      document.getElementById('quick-order-tenkhach').value = found.tenKhach;
    }
    if (found.sdtKhach && !document.getElementById('quick-order-sdtkhach').value) {
      document.getElementById('quick-order-sdtkhach').value = found.sdtKhach;
    }
    if (found.diaChi && !document.getElementById('quick-order-diachi').value) {
      document.getElementById('quick-order-diachi').value = found.diaChi;
    }
    if (found.khoiLuong) {
      document.getElementById('quick-order-khoiluong').value = found.khoiLuong;
    }

    calcQuickOrderCOD();

    if (maspHint) {
      maspHint.style.display = 'block';
      maspHint.style.color = 'var(--success)';
      maspHint.textContent = `✓ Tìm thấy sản phẩm: ${found.sanPham || found.maSP} (Giá: ${fmtVnd(found.giaBan || 0)})`;
    }
    if (btnSave) btnSave.disabled = false;
  };

  // 1. Look up in local allRows or allReportRows
  const localFound = allRows.find(r => isSameMaSPForSearch_(r.maSP, query)) || allReportRows.find(r => isSameMaSPForSearch_(r.maSP, query));
  if (localFound) {
    applyFoundProduct(localFound);
    return;
  }

  // 2. If not found in local memory, try server search if available
  if (query.length >= 2 && typeof google !== 'undefined' && google.script && google.script.run) {
    if (maspHint) {
      maspHint.style.display = 'block';
      maspHint.style.color = 'var(--text-muted)';
      maspHint.textContent = 'Đang tìm kiếm sản phẩm trong hệ thống...';
    }
    google.script.run
      .withSuccessHandler(res => {
        const list = Array.isArray(res) ? res : (res && res.result ? res.result : []);
        const remoteFound = list.find(r => isSameMaSPForSearch_(r.maSP, query));
        if (remoteFound) {
          applyFoundProduct(remoteFound);
        } else {
          if (maspHint) {
            maspHint.style.display = 'block';
            maspHint.style.color = 'var(--danger)';
            maspHint.textContent = `❌ Mã SP [${query}] chưa có trong Sheet! Không cho phép tạo đơn.`;
          }
          if (btnSave) btnSave.disabled = true;
          maspHidden.value = '';
        }
      })
      .withFailureHandler(() => {
        if (maspHint) {
          maspHint.style.display = 'block';
          maspHint.style.color = 'var(--danger)';
          maspHint.textContent = `❌ Mã SP [${query}] chưa có trong Sheet! Không cho phép tạo đơn.`;
        }
        if (btnSave) btnSave.disabled = true;
        maspHidden.value = '';
      })
      .searchByMaSP(query);
    return;
  }

  if (maspHint) {
    maspHint.style.display = 'block';
    maspHint.style.color = 'var(--danger)';
    maspHint.textContent = `❌ Mã SP [${query}] chưa có trong Sheet! Không cho phép tạo đơn.`;
  }
  if (btnSave) btnSave.disabled = true;
  maspHidden.value = '';
}

function setQuickOrderNote(noteText) {
  const input = document.getElementById('quick-order-ghichu');
  if (input) input.value = noteText;
  updateQuickNoteActiveTag(noteText);
}

function updateQuickNoteActiveTag(noteText) {
  const tags = document.querySelectorAll('.qnote-tag');
  tags.forEach(tag => {
    if (tag.textContent.trim() === String(noteText || '').trim()) {
      tag.classList.add('active');
    } else {
      tag.classList.remove('active');
    }
  });
}

function onQuickOrderCodInput() {
  window._quickOrderUserEditedCod = true;
  calcQuickOrderCOD();
}

function calcQuickOrderCOD() {
  const giaBan = parseFloat(document.getElementById('quick-order-giaban')?.value) || 0;
  const hinhThuc = document.getElementById('quick-order-hinhthuc')?.value || 'COD';
  const khachCocEl = document.getElementById('quick-order-khachcoc');
  let khachCoc = parseFloat(khachCocEl?.value) || 0;
  
  let cod = 0;
  if (hinhThuc === 'COD') {
    if (window._quickOrderUserEditedCod) {
      const curCod = parseFloat(document.getElementById('quick-order-tiencod')?.value);
      cod = !isNaN(curCod) ? Math.max(0, curCod) : 0;
    } else if (khachCoc > 0 && khachCoc >= giaBan) {
      cod = 0;
    } else if (khachCoc > 0) {
      cod = Math.max(0, giaBan - khachCoc);
    } else {
      cod = giaBan;
    }
  } else {
    cod = 0;
    if (khachCoc <= 0 && giaBan > 0 && khachCocEl) {
      khachCoc = giaBan;
      khachCocEl.value = khachCoc;
    }
  }
  const codEl = document.getElementById('quick-order-tiencod');
  if (codEl) codEl.value = cod;

  const dvEl = document.getElementById('quick-order-dichvu');
  const dvctEl = document.getElementById('quick-order-dvct');
  if (dvEl) {
    if (cod > 0) {
      if (!dvEl.value || dvEl.value === 'VTK' || dvEl.value === 'CP tiết kiệm thỏa thuận') {
        dvEl.value = 'LCOD';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'PXD' || dvctEl.value === 'GKN, PXD' || dvctEl.value === 'COD, PXD')) {
        dvctEl.value = 'COD, PXD, GKN';
      }
    } else {
      if (!dvEl.value || dvEl.value === 'LCOD' || dvEl.value === 'TMĐT Tiết Kiệm thỏa thuận' || dvEl.value === 'NCOD') {
        dvEl.value = 'VTK';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'COD, PXD' || dvctEl.value === 'COD, PXD, GKN' || dvctEl.value === 'PXD')) {
        dvctEl.value = 'GKN, PXD';
      }
    }
    if (dvEl.value === 'PHS' || dvEl.value === 'Nội tỉnh tiết kiệm' || dvEl.value.includes('Nội tỉnh')) {
      if (dvctEl) {
        dvctEl.value = dvctEl.value.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
        if (!dvctEl.value) dvctEl.value = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
      }
    }
  }
}

function onQuickOrderServiceChange() {
  const dvEl = document.getElementById('quick-order-dichvu');
  const dvctEl = document.getElementById('quick-order-dvct');
  if (!dvEl || !dvctEl) return;
  const val = dvEl.value;
  const cod = parseFloat(document.getElementById('quick-order-tiencod')?.value) || 0;
  if (val === 'VTK' || val === 'CP tiết kiệm thỏa thuận') {
    let dvct = dvctEl.value.replace(/\bCOD,\s*/i, '').replace(/,\s*\bCOD\b/i, '').replace(/\bCOD\b/i, '').trim();
    if (!dvct || dvct === 'PXD') dvct = 'GKN, PXD';
    dvctEl.value = dvct;
  } else if (val === 'LCOD' || val === 'TMĐT Tiết Kiệm thỏa thuận' || val === 'NCOD') {
    if (!dvctEl.value.includes('COD')) {
      dvctEl.value = 'COD, PXD, GKN';
    }
  } else if (val === 'PHS' || val === 'Nội tỉnh tiết kiệm' || val.includes('Nội tỉnh')) {
    // Auto tắt SMS khi chọn nội tỉnh tiết kiệm
    let dvct = dvctEl.value.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
    if (!dvct) dvct = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
    dvctEl.value = dvct;
    showToast('Đã chọn Nội tỉnh tiết kiệm & tự động tắt SMS thông báo', 'info');
  }
}

function debouncedQuickOrderCustomerLookup() {
  clearTimeout(window._quickOrderLookupTimer);
  window._quickOrderLookupTimer = setTimeout(() => {
    const sdt = document.getElementById('quick-order-sdtkhach')?.value.trim();
    if (!sdt || sdt.length < 8) return;
    const normPhone = normalizeCustomerPhone_(sdt);
    
    // Find in allRows
    const found = allRows.find(r => normalizeCustomerPhone_(r.sdtKhach) === normPhone && (r.tenKhach || r.diaChi));
    if (found) {
      const nameInput = document.getElementById('quick-order-tenkhach');
      const addrInput = document.getElementById('quick-order-diachi');
      if (nameInput && !nameInput.value && found.tenKhach) {
        nameInput.value = found.tenKhach;
      }
      if (addrInput && !addrInput.value && found.diaChi) {
        addrInput.value = found.diaChi;
        showToast('Khách quen! Đã tự động điền địa chỉ giao hàng.', 'info');
      }
    }
  }, 350);
}

function saveQuickOrder() {
  const rowIdx = document.getElementById('quick-order-row-index')?.value;
  let rowSheet = document.getElementById('quick-order-sheet-name')?.value || 'SalesData';
  const maSPInput = (document.getElementById('quick-order-masp-input')?.value || '').trim();
  const maspHidden = (document.getElementById('quick-order-masp')?.value || '').trim();
  const maSP = maspHidden || maSPInput;

  // 1. RÀNG BUỘC MÃ SẢN PHẨM: Bắt buộc phải có mã và mã phải tồn tại trong Sheet
  if (!maSP) {
    showToast('Lỗi: Chưa có Mã sản phẩm trong Sheet, không thể tạo đơn!', 'error');
    return;
  }
  let existingRow = allRows.find(r => isSameMaSPForSearch_(r.maSP, maSP)) || allReportRows.find(r => isSameMaSPForSearch_(r.maSP, maSP));
  if (!existingRow) {
    existingRow = findEditableRowByIndex(rowIdx, rowSheet);
  }
  if (!existingRow) {
    showToast(`Lỗi: Mã sản phẩm [${maSP}] không tồn tại trong sheet! Không cho phép tạo đơn.`, 'error');
    return;
  }
  if (existingRow.sheetName) rowSheet = existingRow.sheetName;

  // 2. Validate thông tin gửi hàng
  const tenKhach = (document.getElementById('quick-order-tenkhach')?.value || '').trim();
  const sdtKhach = (document.getElementById('quick-order-sdtkhach')?.value || '').trim();
  const diaChi   = (document.getElementById('quick-order-diachi')?.value || '').trim();
  const hinhThuc = document.getElementById('quick-order-hinhthuc')?.value || 'COD';
  const khoiLuong = parseInt(document.getElementById('quick-order-khoiluong')?.value) || 200;
  let giaBan    = parseFloat(document.getElementById('quick-order-giaban')?.value) || 0;
  if (giaBan <= 0 && existingRow.giaBan > 0) giaBan = existingRow.giaBan;

  let khachCoc  = parseFloat(document.getElementById('quick-order-khachcoc')?.value) || 0;
  if (hinhThuc === 'Freeship' && khachCoc <= 0 && giaBan > 0) {
    khachCoc = giaBan;
  }

  let rawQuickCod = parseFloat(document.getElementById('quick-order-tiencod')?.value);
  let tienCOD = 0;
  if (hinhThuc === 'COD') {
    if (!isNaN(rawQuickCod)) {
      tienCOD = Math.max(0, rawQuickCod);
    } else if (khachCoc > 0 && khachCoc < giaBan) {
      tienCOD = Math.max(0, giaBan - khachCoc);
    } else {
      tienCOD = 0;
    }
  } else {
    tienCOD = 0;
  }
  if (khachCoc > 0 && giaBan > 0 && khachCoc >= giaBan) {
    tienCOD = 0;
  }

  const ghiChu    = (document.getElementById('quick-order-ghichu')?.value || 'CHO HÀNG XEM').trim();
  const aiChot    = (document.getElementById('quick-order-aichot')?.value || '').trim();
  const nguonKhach = document.getElementById('quick-order-nguonkhach')?.value || 'TikTok Live';

  if (!tenKhach) {
    showToast('Vui lòng nhập Tên người nhận!', 'warning');
    document.getElementById('quick-order-tenkhach')?.focus();
    return;
  }
  if (!sdtKhach) {
    showToast('Vui lòng nhập Số điện thoại người nhận!', 'warning');
    document.getElementById('quick-order-sdtkhach')?.focus();
    return;
  }
  if (!/^[0-9+\-\s().]{8,20}$/.test(sdtKhach)) {
    showToast('Số điện thoại không hợp lệ!', 'warning');
    document.getElementById('quick-order-sdtkhach')?.focus();
    return;
  }
  if (!diaChi) {
    showToast('Vui lòng nhập Địa chỉ nhận hàng (Bắt buộc để Viettel Post in bill)!', 'warning');
    document.getElementById('quick-order-diachi')?.focus();
    return;
  }

  const btn = document.getElementById('btn-save-quick-order');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu đơn...';
  }

  const loaiHangHoa = document.getElementById('quick-order-loaihang')?.value || 'Bưu kiện';
  const tinhChatHangHoa = document.getElementById('quick-order-tinhchat')?.value || '';
  const dichVu = document.getElementById('quick-order-dichvu')?.value || (tienCOD > 0 ? 'TMĐT Tiết Kiệm thỏa thuận' : 'CP tiết kiệm thỏa thuận');
  let dichVuCongThem = (document.getElementById('quick-order-dvct')?.value || '').trim() || (tienCOD > 0 ? 'COD, PXD' : 'PXD');
  if (dichVu === 'Nội tỉnh tiết kiệm' || dichVu.includes('Nội tỉnh')) {
    dichVuCongThem = dichVuCongThem.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
    if (!dichVuCongThem) dichVuCongThem = tienCOD > 0 ? 'COD, PXD' : 'PXD';
  }

  const data = {
    maSP,
    giaBan,
    giaVon: existingRow.giaVon || 0,
    tenKhach,
    sdtKhach,
    aiChot,
    nguonKhach,
    diaChi,
    ngayChot: getTodayString_(),
    trangThai: 'Đã bán',
    hinhThuc,
    tienCOD,
    ghiChu,
    khachCoc,
    linkTiktok: existingRow.linkTiktok || '',
    khoiLuong,
    loaiHangHoa,
    tinhChatHangHoa,
    dichVu,
    dichVuCongThem
  };

  const handler = result => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-check"></i> Lưu & Chốt đơn';
    }
    if (result && result.success) {
      showToast(`Tạo đơn Viettel Post cho mã ${maSP} thành công!`, 'success');
      closeModal('modal-quick-order');

      // Optimistic update
      const localIdx = allRows.findIndex(r => isSameMaSPForSearch_(r.maSP, data.maSP));
      if (localIdx !== -1) {
        allRows[localIdx] = Object.assign({}, allRows[localIdx], data, {
          tienLoi: data.giaBan - data.giaVon
        });
      }
      filteredRows = [...allRows];
      applyFilters();

      const dailyPage = document.getElementById('page-daily');
      if (dailyPage && !dailyPage.classList.contains('hidden')) loadDailyOrders();

      const viettelPage = document.getElementById('page-viettel_orders');
      if (viettelPage && !viettelPage.classList.contains('hidden')) loadViettelOrdersPage(true);

      // Background sync
      setTimeout(() => {
        google.script.run
          .withSuccessHandler(res => {
            if (!res) return;
            crmSnapshot = res;
            allRows = (res.rows || []).reverse();
            allReportRows = res.reportRows || [];
            filteredRows = [...allRows];
            applyFilters();
            updateSyncStatusUI(res);
          })
          .getCrmSyncSnapshot({ forceRefresh: false });
      }, 2000);
    } else {
      showToast(result && result.message ? result.message : 'Lỗi khi lưu đơn!', 'error');
    }
  };

  const failHandler = e => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-check"></i> Lưu & Chốt đơn';
    }
    showToast('Lỗi kết nối: ' + e.message, 'error');
  };

  const targetRowIndex = Number(existingRow.rowIndex) || Number(rowIdx) || 0;
  google.script.run
    .withSuccessHandler(handler)
    .withFailureHandler(failHandler)
    .updateRow(targetRowIndex, data, rowSheet);
}

document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter') {
    const modal = document.getElementById('modal-quick-order');
    if (modal && !modal.classList.contains('hidden')) {
      if (e.target && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        saveQuickOrder();
      }
    }
  }
});

// ─────────────────────────────────────────────
// DELETE
// ──────────────────────────────────────────────
function openDeleteModal(rowIndex, maSP, sheetName) {
  deleteRowIndex = rowIndex;
  deleteRowMaSP  = maSP;
  deleteRowSheetName = sheetName || 'SalesData';
  document.getElementById('delete-masp-label').textContent = maSP;
  openModal('modal-delete');
}

function confirmDelete() {
  const rowIndex = deleteRowIndex;
  const maSP    = deleteRowMaSP;
  const rowSheet = deleteRowSheetName || 'SalesData';

  // Find row to allow undo restoration
  const rowToDelete = findEditableRowByIndex(rowIndex, rowSheet);

  // Close modal immediately
  closeModal('modal-delete');

  // Optimistic remove from table
  if (rowSheet === 'SalesData') allRows = allRows.filter(r => Number(r.rowIndex) !== Number(rowIndex));
  filteredRows = [...allRows];
  applyFilters();

  // F14: Show undo toast with countdown
  let cancelled = false;
  const container = document.getElementById('toast-container');
  const toastEl = document.createElement('div');
  toastEl.className = 'toast undo-toast';
  toastEl.innerHTML = `
    <div class="undo-toast-msg">Đã xóa <strong>${escapeHtml(maSP)}</strong></div>
    <span class="undo-secs" id="undo-secs-${rowIndex}">5</span>s
    <button class="btn-undo" id="undo-btn-${rowIndex}">↩ Hoàn tác</button>
  `;
  container.appendChild(toastEl);

  let secs = 5;
  const ticker = setInterval(() => {
    secs--;
    const el = document.getElementById(`undo-secs-${rowIndex}`);
    if (el) el.textContent = secs;
    if (secs <= 0) clearInterval(ticker);
  }, 1000);

  document.getElementById(`undo-btn-${rowIndex}`)?.addEventListener('click', () => {
    cancelled = true;
    clearInterval(ticker);
    toastEl.remove();
    if (rowToDelete) {
      if (rowSheet === 'SalesData') {
        allRows = [rowToDelete, ...allRows];
        filteredRows = [...allRows];
        applyFilters();
      } else {
        allReportRows = [rowToDelete, ...allReportRows];
      }
      showToast('Đã hoàn tác!', 'info');
    }
  });

  setTimeout(() => {
    if (!cancelled) {
      toastEl.classList.add('closing');
      setTimeout(() => { if (toastEl.parentNode) toastEl.remove(); }, 260);
      google.script.run
        .withSuccessHandler(() => {
          // Background sync after real delete
          setTimeout(() => {
            google.script.run
              .withSuccessHandler(payload => {
                if (!payload) return;
                const rows = payload.rows || (Array.isArray(payload) ? payload : null);
                if (rows) {
                  allRows = [...rows].reverse();
                  if (payload.reportRows) allReportRows = [...payload.reportRows].reverse();
                  filteredRows = [...allRows];
                  applyFilters();
                  const dailyPage = document.getElementById('page-daily');
                  if (dailyPage && !dailyPage.classList.contains('hidden')) loadDailyOrders();
                }
                if (payload && payload.notifications) {
                  renderNotifications(payload.notifications);
                }
              })
              .getRowsAndDashboardStats();
          }, 800);
        })
        .withFailureHandler(e => {
          showToast('Lỗi xóa: ' + e.message, 'error');
          if (rowToDelete && rowSheet === 'SalesData') { allRows = [rowToDelete, ...allRows]; filteredRows = [...allRows]; applyFilters(); }
        })
        .deleteRow(rowIndex, rowSheet);
    }
  }, 5000);
}

// ─────────────────────────────────────────────
// SEARCH MÃ SP (dedicated search page)
// ─────────────────────────────────────────────
function searchMaSPOnEnter(e) {
  if (e.key === 'Enter') doSearchMaSP();
}

function doSearchMaSP() {
  const keyword = document.getElementById('search-masp-input').value.trim();
  if (!keyword) { showToast('Vui lòng nhập mã SP cần tìm!', 'warning'); return; }

  const container = document.getElementById('search-results');
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="fas fa-spinner fa-spin fa-2x"></i><br><br>Đang tìm kiếm...</div>';

  google.script.run
    .withSuccessHandler(rows => {
      // Cập nhật cache client theo đúng sheet để modal sửa không nhầm rowIndex.
      if (rows && rows.length > 0) {
        rows.forEach(r => {
          const rowSheet = getRowSheetName_(r);
          const reportIdx = allReportRows.findIndex(a => Number(a.rowIndex) === Number(r.rowIndex) && getRowSheetName_(a) === rowSheet);
          if (reportIdx !== -1) allReportRows[reportIdx] = r;
          else allReportRows.unshift(r);

          if (rowSheet === 'SalesData') {
            const idx = allRows.findIndex(a => Number(a.rowIndex) === Number(r.rowIndex));
            if (idx !== -1) allRows[idx] = r;
            else allRows.unshift(r);
          }
        });
      }
      renderSearchResults(rows, keyword);
    })
    .withFailureHandler(e => {
      container.innerHTML = '';
      showToast('Lỗi tìm kiếm: ' + e.message, 'error');
    })
    .searchByMaSP(keyword);
}

function renderSearchResults(rows, keyword) {
  const container = document.getElementById('search-results');
  if (!rows || rows.length === 0) {
    container.innerHTML = `
      <div class="search-no-result">
        <div class="empty-icon"><i class="fas fa-search"></i></div>
        <h3>Không tìm thấy kết quả</h3>
        <p>Không có sản phẩm nào khớp với mã <strong>"${keyword}"</strong></p>
      </div>`;
    return;
  }

  const fmt  = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
  const dash = v => (v && String(v).trim()) ? v : '—';

  container.innerHTML = `<p style="font-size:0.8rem;color:var(--text-muted);margin-bottom:12px;">Tìm thấy <strong style="color:var(--primary-light)">${rows.length}</strong> kết quả cho "<strong>${keyword}</strong>"</p>`;

  rows.forEach(r => {
    const ttBadge = getStatusBadge(r.trangThai);

    const htBadge = getShippingBadge(r);

    const tienLoiClass = r.tienLoi >= 0 ? 'profit-positive' : 'profit-negative';
    const tienLoiSign  = r.tienLoi >= 0 ? '+' : '';

    const linkCell = r.linkTiktok
      ? `<a href="${r.linkTiktok}" target="_blank" rel="noopener" style="color:var(--primary-light);text-decoration:underline;word-break:break-all;">${r.linkTiktok}</a>`
      : '—';

    const rowSheet = getRowSheetName_(r);
    const safeSheet = escapeForInlineEdit(rowSheet);
    const isEditable = isClientEditableSheet_(rowSheet);
    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
      <div class="result-card-header">
        <span class="result-masp"><i class="fas fa-barcode"></i> ${r.maSP}</span>
        ${ttBadge}
      </div>

      <div style="margin-bottom:12px;">
        <p style="font-size:0.68rem;color:var(--primary-light);font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
          <i class="fas fa-tags"></i> Thông tin giá
        </p>
        <div class="result-grid">
          <div class="result-item"><div class="result-label">Giá bán</div><div class="result-value">${fmt(r.giaBan)}</div></div>
          <div class="result-item"><div class="result-label">Giá vốn</div><div class="result-value">${fmt(r.giaVon)}</div></div>
          <div class="result-item"><div class="result-label">Tiền lời</div><div class="result-value ${tienLoiClass}">${tienLoiSign}${fmt(r.tienLoi)}</div></div>
          <div class="result-item"><div class="result-label">Khách cọc</div><div class="result-value">${r.khachCoc ? fmt(r.khachCoc) : '—'}</div></div>
          <div class="result-item"><div class="result-label">Tiền COD</div><div class="result-value">${r.hinhThuc === 'COD' && r.tienCOD ? fmt(r.tienCOD) : '—'}</div></div>
          <div class="result-item"><div class="result-label">Giao hàng</div><div class="result-value">${htBadge}</div></div>
        </div>
      </div>

      <div style="margin-bottom:12px;padding:12px 14px;background:rgba(99,102,241,0.07);border:1px solid rgba(99,102,241,0.18);border-radius:10px;">
        <p style="font-size:0.68rem;color:var(--primary-light);font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
          <i class="fas fa-user-tag"></i> Thông tin khách hàng
        </p>
        <div class="result-grid">
          <div class="result-item">
            <div class="result-label">Tên khách hàng</div>
            <div class="result-value">${dash(r.tenKhach)}</div>
          </div>
          <div class="result-item">
            <div class="result-label">Ai chốt</div>
            <div class="result-value">${dash(r.aiChot)}</div>
          </div>
          <div class="result-item">
            <div class="result-label">Nguồn khách</div>
            <div class="result-value">${dash(r.nguonKhach)}</div>
          </div>
          <div class="result-item">
            <div class="result-label">SĐT</div>
            <div class="result-value">${dash(r.sdtKhach)}</div>
          </div>
          <div class="result-item">
            <div class="result-label">Ngày chốt</div>
            <div class="result-value">${dash(r.ngayChot)}</div>
          </div>
          <div class="result-item" style="grid-column:1/-1;">
            <div class="result-label">Địa chỉ</div>
            <div class="result-value">${dash(r.diaChi)}</div>
          </div>
        </div>
      </div>

      <!-- ③ Ghi chú & Link TikTok -->
      <div style="margin-bottom:12px;padding:12px 14px;background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.15);border-radius:10px;">
        <p style="font-size:0.68rem;color:var(--success);font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
          <i class="fas fa-sticky-note"></i> Ghi chú & Liên kết
        </p>
        <div class="result-grid">
          <div class="result-item" style="grid-column:1/-1;">
            <div class="result-label">Ghi chú</div>
            <div class="result-value" style="white-space:pre-wrap;">${dash(r.ghiChu)}</div>
          </div>
          <div class="result-item" style="grid-column:1/-1;">
            <div class="result-label">Link TikTok</div>
            <div class="result-value" style="font-size:0.82rem;">${linkCell}</div>
          </div>
        </div>
      </div>

      <!-- ④ Kiểm tra & Audit -->
      <div style="margin-bottom:14px;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;">
        <p style="font-size:0.68rem;color:var(--text-muted);font-weight:700;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">
          <i class="fas fa-history"></i> Lịch sử
        </p>
        <div class="result-grid">
          <div class="result-item">
            <div class="result-label">Ngày tạo</div>
            <div class="result-value" style="font-size:0.82rem;color:var(--text-muted);">${dash(r.createdAt)}</div>
          </div>
          <div class="result-item">
            <div class="result-label">Cập nhật lúc</div>
            <div class="result-value" style="font-size:0.82rem;color:var(--text-muted);">${dash(r.updatedAt)}</div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div style="display:${isEditable ? 'flex' : 'none'};gap:8px;">
        <button class="btn btn-sm" style="background:var(--info-light);color:var(--info);border:1px solid rgba(59,130,246,0.2);" onclick="openEditModal(${r.rowIndex}, '${safeSheet}')">
          <i class="fas fa-pencil-alt"></i> Sửa
        </button>
        <button class="btn btn-sm" style="background:rgba(16, 185, 129, 0.12);color:var(--success);border:1px solid rgba(16, 185, 129, 0.2);" onclick="copyOrderToClipboard(${r.rowIndex}, '${safeSheet}')">
          <i class="far fa-copy"></i> Copy
        </button>
        <button class="btn btn-sm" style="background:rgba(59, 130, 246, 0.12);color:var(--info);border:1px solid rgba(59, 130, 246, 0.2);" onclick="markAsShipped(${r.rowIndex}, '${safeSheet}')">
          <i class="fas fa-truck"></i> Giao
        </button>
        <button class="btn btn-sm btn-danger" onclick="openDeleteModal(${r.rowIndex}, '${r.maSP.replace(/'/g,"\\'")}', '${safeSheet}')">  
          <i class="fas fa-trash"></i> Xóa
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}


// Quick search from topbar
function quickSearch(e) {
  if (e.key === 'Enter') {
    const keyword = document.getElementById('topbar-quick-search').value.trim();
    if (!keyword) return;
    // Switch to search page and fill
    switchPage('search', document.getElementById('nav-search'));
    document.getElementById('search-masp-input').value = keyword;
    doSearchMaSP();
    document.getElementById('topbar-quick-search').value = '';
  }
}

// ─────────────────────────────────────────────
// ADVANCED STATISTICS & REPORTING PAGE
// ─────────────────────────────────────────────

function changeStatsPeriod(period, btnEl) {
  statsPeriod = period;
  
  document.querySelectorAll('.stats-filter-btn').forEach(btn => btn.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const customInputs = document.getElementById('stats-custom-range-inputs');
  if (period === 'custom') {
    customInputs.classList.remove('hidden');
    if (!document.getElementById('stats-date-start').value) {
      const today = getTodayLocal();
      document.getElementById('stats-date-start').value = today;
      document.getElementById('stats-date-end').value = today;
    }
  } else {
    customInputs.classList.add('hidden');
    loadAdvancedStats();
  }
}

function applyCustomPeriod() {
  const start = document.getElementById('stats-date-start').value;
  const end = document.getElementById('stats-date-end').value;
  if (start && end) {
    loadAdvancedStats();
  }
}

function debouncedLoadAdvancedStats() {
  clearTimeout(statsLoadTimer);
  statsLoadTimer = setTimeout(loadAdvancedStats, 350);
}

function getStatsFilters() {
  return {
    customer: document.getElementById('stats-customer-filter')?.value || '',
    status: document.getElementById('stats-status-filter')?.value || '',
    sheetName: document.getElementById('stats-sheet-filter')?.value || '',
    orderType: document.getElementById('stats-order-type-filter')?.value || ''
  };
}

function switchStatsTab(tab, btnEl) {
  statsSubTab = tab;
  
  document.querySelectorAll('.stats-tab-nav-btn').forEach(btn => btn.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  document.querySelectorAll('.stats-tab-content').forEach(content => content.classList.add('hidden'));
  document.getElementById(`stats-tab-${tab}`).classList.remove('hidden');

  if (statsDataCached) {
    renderStatsChartsForActiveTab();
  }
}

function loadAdvancedStats() {
  ['kpi-revenue', 'kpi-profit', 'kpi-orders', 'kpi-aov', 'kpi-customers', 'kpi-sold-products', 'kpi-pending-products'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = '<span class="skeleton skeleton-text" style="width: 80px; display: inline-block;"></span>';
  });

  const startVal = document.getElementById('stats-date-start').value;
  const endVal = document.getElementById('stats-date-end').value;

  google.script.run
    .withSuccessHandler(data => {
      statsDataCached = data;
      if (!allReportRows || allReportRows.length === 0) {
        allReportRows = data.orderRows || [];
      }
      renderAdvancedStatsKPIs(data);
      renderStatsChartsForActiveTab();
    })
    .withFailureHandler(e => {
      showToast('Lỗi tải dữ liệu báo cáo: ' + e.message, 'error');
    })
    .getAdvancedStats(statsPeriod, startVal, endVal, getStatsFilters());
}

function renderAdvancedStatsKPIs(data) {
  if (!data) return;
  const cur = (data.kpi && data.kpi.current) ? data.kpi.current : (data.kpi || {});
  const growth = (data.kpi && data.kpi.growth) ? data.kpi.growth : (data.growth || {});

  const fmt = n => new Intl.NumberFormat('vi-VN').format(Number(n) || 0) + ' ₫';
  const fmtNum = n => new Intl.NumberFormat('vi-VN').format(Number(n) || 0);

  const elRev = document.getElementById('kpi-revenue');
  if (elRev) elRev.textContent = fmt(cur.revenue);
  const elProf = document.getElementById('kpi-profit');
  if (elProf) elProf.textContent = fmt(cur.profit);
  const elOrd = document.getElementById('kpi-orders');
  if (elOrd) elOrd.textContent = fmtNum(cur.orders) + ' đơn';
  const elAov = document.getElementById('kpi-aov');
  if (elAov) elAov.textContent = fmt(cur.aov);
  
  const elCust = document.getElementById('kpi-customers');
  if (elCust) elCust.textContent = fmtNum(cur.customers);
  const elSold = document.getElementById('kpi-sold-products');
  if (elSold) elSold.textContent = fmtNum(cur.soldProducts);
  const elPend = document.getElementById('kpi-pending-products');
  if (elPend) elPend.textContent = fmtNum(cur.pendingProducts);

  renderGrowthBadge_('kpi-revenue-sub', growth.revenue);
  renderGrowthBadge_('kpi-profit-sub', growth.profit);
  renderGrowthBadge_('kpi-orders-sub', growth.orders);
  renderGrowthBadge_('kpi-aov-sub', growth.aov);

  const fmtDateLabel = dStr => {
    if (!dStr) return '';
    const [y, m, d] = String(dStr).split('-');
    return d && m && y ? `${d}/${m}/${y}` : dStr;
  };
  const periodLabelEl = document.getElementById('stats-period-display-label');
  if (periodLabelEl && data.ranges) {
    periodLabelEl.textContent = 
      `Chu kỳ: ${fmtDateLabel(data.ranges.currentStart)} ➔ ${fmtDateLabel(data.ranges.currentEnd)}`;
  }

  const bestCustomer = (data.customerBreakdown || [])[0];
  const bestDay = [...(data.dailyBreakdown || [])].sort((a, b) => (Number(b.revenue) || 0) - (Number(a.revenue) || 0))[0];
  const bestSheet = (data.sheetBreakdown || [])[0];

  const elBestCust = document.getElementById('insight-best-customer');
  if (elBestCust) {
    elBestCust.textContent = bestCustomer
      ? `${bestCustomer.name} · ${fmt(bestCustomer.revenue)}`
      : '—';
  }
  const elBestDay = document.getElementById('insight-best-day');
  if (elBestDay) {
    elBestDay.textContent = bestDay && bestDay.revenue
      ? `${fmtDateLabel(bestDay.date)} · ${fmt(bestDay.revenue)}`
      : '—';
  }
  const elBestSheet = document.getElementById('insight-best-sheet');
  if (elBestSheet) {
    elBestSheet.textContent = bestSheet
      ? `${bestSheet.sheetName} · ${fmt(bestSheet.revenue)}`
      : '—';
  }
  const elQuality = document.getElementById('insight-quality-issues');
  if (elQuality) {
    elQuality.textContent = fmtNum((data.dataQualityIssues || []).length);
  }
}

function renderGrowthBadge_(id, rate) {
  const el = document.getElementById(id);
  if (!el) return;

  if (rate > 0) {
    el.className = 'kpi-sub trend-up';
    el.innerHTML = `<i class="fas fa-arrow-trend-up"></i> +${rate}% so với kỳ trước`;
  } else if (rate < 0) {
    el.className = 'kpi-sub trend-down';
    el.innerHTML = `<i class="fas fa-arrow-trend-down"></i> ${rate}% so với kỳ trước`;
  } else {
    el.className = 'kpi-sub';
    el.innerHTML = `<i class="fas fa-arrows-left-right"></i> Không đổi so với kỳ trước`;
  }
}

function renderStatsChartsForActiveTab() {
  if (!statsDataCached) return;

  const data = statsDataCached;
  const labels = data.dailyBreakdown.map(d => {
    const [y, m, dPart] = d.date.split('-');
    return `${dPart}/${m}`;
  });

  Chart.defaults.color = '#94a3b8';
  Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';

  if (statsSubTab === 'overview') {
    if (chartRevenueAdvanced) chartRevenueAdvanced.destroy();
    
    const canvasAdv = document.getElementById('chart-revenue-advanced');
    let bgAdvRev = 'rgba(124, 58, 237, 0.05)';
    let bgAdvProf = 'rgba(6, 182, 212, 0.05)';
    if (canvasAdv) {
      const ctxAdv = canvasAdv.getContext('2d');
      if (ctxAdv) {
        const gradAdvRev = ctxAdv.createLinearGradient(0, 0, 0, 300);
        gradAdvRev.addColorStop(0, 'rgba(124, 58, 237, 0.35)');
        gradAdvRev.addColorStop(1, 'rgba(124, 58, 237, 0.0)');
        bgAdvRev = gradAdvRev;

        const gradAdvProf = ctxAdv.createLinearGradient(0, 0, 0, 300);
        gradAdvProf.addColorStop(0, 'rgba(6, 182, 212, 0.35)');
        gradAdvProf.addColorStop(1, 'rgba(6, 182, 212, 0.0)');
        bgAdvProf = gradAdvProf;
      }
    }

    chartRevenueAdvanced = new Chart(document.getElementById('chart-revenue-advanced'), {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Doanh thu',
            data: data.dailyBreakdown.map(d => d.revenue),
            borderColor: '#7c3aed',
            backgroundColor: bgAdvRev,
            borderWidth: 3,
            tension: 0.45,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: '#7c3aed'
          },
          {
            label: 'Lợi nhuận ròng',
            data: data.dailyBreakdown.map(d => d.profit),
            borderColor: '#06b6d4',
            backgroundColor: bgAdvProf,
            borderWidth: 3,
            tension: 0.45,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: '#06b6d4'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label: ctx => ' ' + ctx.dataset.label + ': ' + new Intl.NumberFormat('vi-VN').format(ctx.raw) + ' ₫'
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            ticks: {
              callback: v => new Intl.NumberFormat('vi-VN', { notation: 'compact' }).format(v)
            }
          }
        }
      }
    });
  }

  if (statsSubTab === 'revenue') {
    if (chartRevenueProfitBar) chartRevenueProfitBar.destroy();

    chartRevenueProfitBar = new Chart(document.getElementById('chart-revenue-profit-bar'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Doanh thu',
            data: data.dailyBreakdown.map(d => d.revenue),
            backgroundColor: 'rgba(124, 58, 237, 0.75)',
            borderRadius: 4
          },
          {
            label: 'Lợi nhuận',
            data: data.dailyBreakdown.map(d => d.profit),
            backgroundColor: 'rgba(6, 182, 212, 0.75)',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12 } },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              label: ctx => ' ' + ctx.dataset.label + ': ' + new Intl.NumberFormat('vi-VN').format(ctx.raw) + ' ₫'
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            ticks: {
              callback: v => new Intl.NumberFormat('vi-VN', { notation: 'compact' }).format(v)
            }
          }
        }
      }
    });

    renderStatsTableBreakdown();
  }

  if (statsSubTab === 'products') {
    if (chartTopProducts) chartTopProducts.destroy();
    if (chartTopCustomers) chartTopCustomers.destroy();
    if (chartStatsDelivery) chartStatsDelivery.destroy();
    if (chartStatsStatus) chartStatsStatus.destroy();

    const pNames = (data.topProducts || []).map(p => p.productName || p.maSP || p.name || 'Sản phẩm');
    const pQuantities = (data.topProducts || []).map(p => p.quantity ?? p.count ?? 0);
    chartTopProducts = new Chart(document.getElementById('chart-top-products'), {
      type: 'bar',
      data: {
        labels: pNames.length ? pNames : ['Chưa có đơn'],
        datasets: [{
          label: 'Số lượng bán',
          data: pQuantities.length ? pQuantities : [0],
          backgroundColor: 'rgba(245, 158, 11, 0.75)',
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              afterBody: (ctx) => {
                const idx = ctx[0].dataIndex;
                const pInfo = (data.topProducts || [])[idx];
                if (pInfo) {
                  return `Doanh thu: ${new Intl.NumberFormat('vi-VN').format(pInfo.revenue || 0)} ₫\nLợi nhuận: ${new Intl.NumberFormat('vi-VN').format(pInfo.profit || 0)} ₫`;
                }
                return '';
              }
            }
          }
        },
        scales: {
          x: { ticks: { stepSize: 1 } },
          y: { grid: { display: false } }
        }
      }
    });

    const cNames = (data.topCustomers || []).map(c => c.name || 'Khách hàng');
    const cRevenues = (data.topCustomers || []).map(c => c.revenue || 0);
    chartTopCustomers = new Chart(document.getElementById('chart-top-customers'), {
      type: 'bar',
      data: {
        labels: cNames.length ? cNames : ['Chưa có khách'],
        datasets: [{
          label: 'Tổng chi tiêu',
          data: cRevenues.length ? cRevenues : [0],
          backgroundColor: 'rgba(99, 102, 241, 0.75)',
          borderRadius: 4
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              label: ctx => ' Tổng chi tiêu: ' + new Intl.NumberFormat('vi-VN').format(ctx.raw || 0) + ' ₫',
              afterBody: (ctx) => {
                const idx = ctx[0].dataIndex;
                const cInfo = (data.topCustomers || [])[idx];
                if (cInfo) {
                  return `SĐT: ${cInfo.phone || '—'}\nSố đơn: ${cInfo.orders ?? cInfo.count ?? 0} đơn`;
                }
                return '';
              }
            }
          }
        },
        scales: {
          x: {
            ticks: {
              callback: v => new Intl.NumberFormat('vi-VN', { notation: 'compact' }).format(v)
            }
          },
          y: { grid: { display: false } }
        }
      }
    });

    const del = data.deliveryBreakdown || {};
    const delCod = del.cod || { count: 0, revenue: 0 };
    const delFree = del.freeship || { count: 0, revenue: 0 };
    chartStatsDelivery = new Chart(document.getElementById('chart-stats-delivery'), {
      type: 'doughnut',
      data: {
        labels: ['COD', 'Freeship'],
        datasets: [{
          data: [delCod.count || 0, delFree.count || 0],
          backgroundColor: ['rgba(245, 158, 11, 0.8)', 'rgba(59, 130, 246, 0.8)'],
          borderColor: 'rgba(26, 26, 46, 0)',
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'right', labels: { padding: 12 } },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              label: ctx => ` Số lượng: ${ctx.raw} đơn (${ctx.label})`,
              afterBody: (ctx) => {
                const isCod = ctx[0].label === 'COD';
                const rev = isCod ? (delCod.revenue || 0) : (delFree.revenue || 0);
                return `Doanh thu: ${new Intl.NumberFormat('vi-VN').format(rev)} ₫`;
              }
            }
          }
        }
      }
    });

    const sta = data.statusBreakdown || { sold: 0, pending: 0, inStock: 0 };
    chartStatsStatus = new Chart(document.getElementById('chart-stats-status'), {
      type: 'doughnut',
      data: {
        labels: ['Đã bán', 'Đợi CK', 'Còn hàng'],
        datasets: [{
          data: [sta.sold || 0, sta.pending || 0, sta.inStock || 0],
          backgroundColor: ['rgba(99, 102, 241, 0.8)', 'rgba(245, 158, 11, 0.8)', 'rgba(16, 185, 129, 0.8)'],
          borderColor: 'rgba(26, 26, 46, 0)',
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: { position: 'right', labels: { padding: 12 } },
          tooltip: {
            backgroundColor: 'rgba(26,26,46,0.95)',
            borderColor: 'rgba(99,102,241,0.3)',
            borderWidth: 1,
            callbacks: {
              label: ctx => ` Số lượng: ${ctx.raw} sản phẩm`
            }
          }
        }
      }
    });

    renderRevenueDetailTables(data);
  }
}

function renderRevenueDetailTables(data) {
  renderCustomerRevenueTable(data.customerBreakdown || []);
  renderSheetRevenueTable(data.sheetBreakdown || []);
  renderDataQualityTable(data.dataQualityIssues || []);
}

function renderCustomerRevenueTable(rows) {
  const tbody = document.getElementById('stats-customers-tbody');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">Chưa có khách hàng trong bộ lọc này</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><strong>${escapeHtml(r.name)}</strong></td>
      <td>${escapeHtml(r.phone || '—')}</td>
      <td><span class="vip-badge ${(r.vipTier && r.vipTier.key !== 'regular') ? r.vipTier.className : 'vip-regular'}">${escapeHtml(r.vipTier?.label || 'Khách hàng Thường')}</span></td>
      <td><div class="stats-customer-tags">${renderCustomerTagsHtml_(r.tags || [])}</div></td>
      <td>${fmtNum(r.orders)} đơn</td>
      <td><strong>${fmtVnd(r.revenue)}</strong></td>
      <td>${fmtVnd(r.aov)}</td>
      <td>${escapeHtml(r.sheetList || '—')}</td>
    </tr>
  `).join('');
}

function renderSheetRevenueTable(rows) {
  const tbody = document.getElementById('stats-sheets-tbody');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">Chưa có doanh thu theo sheet</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><span class="badge badge-info">${escapeHtml(r.sheetName)}</span></td>
      <td>${fmtNum(r.orders)} đơn</td>
      <td>${fmtNum(r.customerCount)}</td>
      <td><strong>${fmtVnd(r.revenue)}</strong></td>
      <td>${fmtVnd(r.aov)}</td>
    </tr>
  `).join('');
}

function renderDataQualityTable(rows) {
  const tbody = document.getElementById('stats-quality-tbody');
  if (!tbody) return;
  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--success);">Không phát hiện dòng thiếu dữ liệu quan trọng</td></tr>';
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(r.sourceSheet)}</td>
      <td>${fmtNum(r.rowIndex)}</td>
      <td>${escapeHtml(r.maSP)}</td>
      <td>${escapeHtml(r.tenKhach)}</td>
      <td>${escapeHtml(r.ngayChot)}</td>
      <td>${fmtVnd(r.revenue)}</td>
      <td>${r.issues.map(issue => `<span class="quality-chip">${escapeHtml(issue)}</span>`).join(' ')}</td>
    </tr>
  `).join('');
}

function changeStatsTableView(view) {
  statsTableView = view;
  
  document.querySelectorAll('.stats-view-btn').forEach(btn => btn.classList.remove('active'));
  const btn = document.getElementById(`btn-view-${view}`);
  if (btn) btn.classList.add('active');
  
  const thTime = document.getElementById('th-stats-time');
  if (thTime) {
    if (view === 'day') thTime.textContent = 'Ngày chốt';
    else if (view === 'week') thTime.textContent = 'Tuần';
    else if (view === 'month') thTime.textContent = 'Tháng';
  }
  
  renderStatsTableBreakdown();
}

function renderStatsTableBreakdown() {
  if (!statsDataCached) return;
  const data = statsDataCached;
  
  const tbody = document.getElementById('stats-table-daily-tbody');
  const tfoot = document.getElementById('stats-table-daily-tfoot');
  if (!tbody || !tfoot) return;

  const fmt = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
  const fmtNum = n => new Intl.NumberFormat('vi-VN').format(n);
  
  let list = [];
  if (statsTableView === 'day') list = data.dailyBreakdown || [];
  else if (statsTableView === 'week') list = data.weeklyBreakdown || [];
  else if (statsTableView === 'month') list = data.monthlyBreakdown || [];
  
  const listSorted = [...list].sort((a, b) => (b.revenue || 0) - (a.revenue || 0) || String(b.date || '').localeCompare(String(a.date || '')));
  
  let totalOrders = 0;
  let totalRevenue = 0;
  let totalCost = 0;
  let totalDeposit = 0;
  let totalCod = 0;
  let totalProfit = 0;
  
  if (listSorted.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;">Không phát sinh đơn hàng trong chu kỳ này</td></tr>`;
    tfoot.innerHTML = '';
    return;
  }
  
  tbody.innerHTML = listSorted.map(item => {
    totalOrders += item.orders || 0;
    totalRevenue += item.revenue || 0;
    totalCost += item.cost || 0;
    totalDeposit += item.deposit || 0;
    totalCod += item.cod || 0;
    totalProfit += item.profit || 0;
    
    let timeLabel = item.label;
    if (statsTableView === 'day' && item.date) {
      const [y, m, d] = item.date.split('-');
      timeLabel = `${d}/${m}/${y}`;
    }
    
    const profitVal = item.profit || 0;
    const profitSign = profitVal >= 0 ? '+' : '';
    const profitClass = profitVal >= 0 ? 'profit-positive' : 'profit-negative';
    
    return `<tr onclick="showStatsPeriodDetails('${item.date}', '${item.label.replace(/'/g, "\\'")}')" title="Nhấp để xem chi tiết các đơn hàng chốt">
      <td><strong>${timeLabel} <i class="fas fa-search-plus" style="font-size:0.75rem;color:var(--primary-light);margin-left:4px;"></i></strong></td>
      <td>${fmtNum(item.orders)} đơn</td>
      <td>${fmt(item.revenue)}</td>
      <td>${fmt(item.cost)}</td>
      <td>${item.deposit ? fmt(item.deposit) : '<span class="text-muted">—</span>'}</td>
      <td>${item.cod ? fmt(item.cod) : '<span class="text-muted">—</span>'}</td>
      <td class="${profitClass}">${profitSign}${fmt(profitVal)}</td>
    </tr>`;
  }).join('');
  
  tfoot.innerHTML = `
    <tr>
      <td>TỔNG CỘNG</td>
      <td>${fmtNum(totalOrders)} đơn</td>
      <td>${fmt(totalRevenue)}</td>
      <td>${fmt(totalCost)}</td>
      <td>${fmt(totalDeposit)}</td>
      <td>${fmt(totalCod)}</td>
      <td class="${totalProfit >= 0 ? 'profit-positive' : 'profit-negative'}" style="color: ${totalProfit >= 0 ? 'var(--success)' : 'var(--danger)'};">
        ${totalProfit >= 0 ? '+' : ''}${fmt(totalProfit)}
      </td>
    </tr>
  `;
}

function showStatsPeriodDetails(dateKey, label) {
  const tbody = document.getElementById('stats-detail-tbody');
  const title = document.getElementById('modal-stats-detail-title');
  if (!tbody || !title) return;

  title.innerHTML = `<i class="fas fa-search-plus"></i> Chi tiết đơn chốt: ${label}`;
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;"><i class="fas fa-spinner fa-spin"></i> Đang tải chi tiết...</td></tr>';
  openModal('modal-stats-detail');

  let filtered = [];
  const rowsPool = (statsDataCached && statsDataCached.orderRows) || allReportRows || [];
  
  if (statsTableView === 'day') {
    filtered = rowsPool.filter(r => {
      const isSold = String(r.trangThai).toLowerCase().includes('bán');
      const isWaiting = String(r.trangThai).toLowerCase().includes('đợi') || String(r.trangThai).toLowerCase().includes('ck');
      return (isSold || isWaiting || r.sourceSheet === 'THANH LÝ') && r.ngayChot === dateKey;
    });
  } 
  else if (statsTableView === 'week') {
    const start = new Date(dateKey);
    const end = new Date(start.getTime() + 6 * 24 * 60 * 60 * 1000);
    const startStr = dateKey;
    const endStr = Utilities_formatDateLocal_(end);
    
    filtered = rowsPool.filter(r => {
      const isSold = String(r.trangThai).toLowerCase().includes('bán');
      const isWaiting = String(r.trangThai).toLowerCase().includes('đợi') || String(r.trangThai).toLowerCase().includes('ck');
      return (isSold || isWaiting || r.sourceSheet === 'THANH LÝ') && r.ngayChot >= startStr && r.ngayChot <= endStr;
    });
  } 
  else if (statsTableView === 'month') {
    filtered = rowsPool.filter(r => {
      const isSold = String(r.trangThai).toLowerCase().includes('bán');
      const isWaiting = String(r.trangThai).toLowerCase().includes('đợi') || String(r.trangThai).toLowerCase().includes('ck');
      return (isSold || isWaiting || r.sourceSheet === 'THANH LÝ') && r.ngayChot && r.ngayChot.indexOf(dateKey) === 0;
    });
  }

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);">Không tìm thấy đơn hàng chi tiết nào</td></tr>';
    return;
  }

  const fmt = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
  const reportCustomerTotalsMap = buildCustomerTotalsMap_(filtered);
  
  tbody.innerHTML = filtered.map(r => {
    const profitVal = r.tienLoi || (r.giaBan - r.giaVon);
    const profitSign = profitVal >= 0 ? '+' : '';
    const profitClass = profitVal >= 0 ? 'profit-positive' : 'profit-negative';
    
    let ttBadge = '';
    if (r.trangThai === 'Còn hàng')     ttBadge = `<span class="badge badge-success" style="font-size:0.7rem;"><i class="fas fa-circle fa-xs"></i> Còn</span>`;
    else if (r.trangThai === 'Đã bán')  ttBadge = `<span class="badge badge-primary" style="font-size:0.7rem;"><i class="fas fa-check fa-xs"></i> Đã bán</span>`;
    else if (r.trangThai === 'Đợi CK')  ttBadge = `<span class="badge badge-warning" style="font-size:0.7rem;"><i class="fas fa-clock fa-xs"></i> Đợi CK</span>`;
    else if (r.trangThai === 'Đã xóa')  ttBadge = `<span class="badge badge-danger" style="font-size:0.7rem;"><i class="fas fa-trash-alt fa-xs"></i> Đã xóa</span>`;
    else                                 ttBadge = `<span class="badge badge-muted" style="font-size:0.7rem;">${r.trangThai || '—'}</span>`;

    const htBadge = getShippingBadge(r, 'font-size:0.7rem;', reportCustomerTotalsMap);

    return `<tr>
      <td><strong>${r.maSP}</strong></td>
      <td>${fmt(r.giaBan)}</td>
      <td>${fmt(r.giaVon)}</td>
      <td class="${profitClass}">${profitSign}${fmt(profitVal)}</td>
      <td title="${r.tenKhach || ''}">${r.tenKhach || '<span class="text-muted">—</span>'}</td>
      <td><span class="badge badge-info" style="font-size:0.7rem;">${escapeHtml(r.sourceSheet || 'SalesData')}</span></td>
      <td>${htBadge}</td>
      <td>${ttBadge}</td>
    </tr>`;
  }).join('');
}

function Utilities_formatDateLocal_(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

// ─────────────────────────────────────────────
// EXPORTING REPORTS (Excel, CSV, PDF, Print)
// ─────────────────────────────────────────────

function loadScript(url, callback) {
  const script = document.createElement("script");
  script.type = "text/javascript";
  script.src = url;
  script.onload = callback;
  document.head.appendChild(script);
}

function exportStatsReport(type) {
  if (!statsDataCached) {
    showToast('Chưa có dữ liệu để xuất báo cáo!', 'warning');
    return;
  }

  const data = statsDataCached;
  const startStr = data.ranges.currentStart;
  const endStr = data.ranges.currentEnd;

  if (type === 'csv') {
    const headers = ['Ngày chốt', 'Số đơn chốt', 'Tổng doanh thu (đ)', 'Giá trị TB đơn (đ)', 'Lợi nhuận ròng (đ)'];
    const rows = data.dailyBreakdown.map(d => {
      const aov = d.orders > 0 ? Math.round(d.revenue / d.orders) : 0;
      return [d.date, d.orders, d.revenue, aov, d.profit];
    });

    const csvContent = "\ufeff" + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.setAttribute("download", `BaoCaoDoanhSo_Tu_${startStr}_Den_${endStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Tải xuống file CSV báo cáo thành công!', 'success');
  }

  if (type === 'excel') {
    showLoading('Đang khởi tạo file Excel...');
    loadScript("https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js", () => {
      try {
        const kpi = data.kpi.current;

        const kpiRows = [
          ['CHỈ SỐ THỐNG KÊ DOANH SỐ', ''],
          ['Khoảng thời gian báo cáo:', `${startStr} đến ${endStr}`],
          ['', ''],
          ['Chỉ số KPI', 'Giá trị'],
          ['Tổng doanh thu (₫)', kpi.revenue],
          ['Tổng lợi nhuận ròng (₫)', kpi.profit],
          ['Tổng số đơn hàng', kpi.orders],
          ['Giá trị trung bình đơn - AOV (₫)', kpi.aov],
          ['Khách hàng phát sinh đơn', kpi.customers],
          ['Sản phẩm đã bán', kpi.soldProducts],
          ['Sản phẩm đợi chuyển khoản', kpi.pendingProducts],
          ['Tổng tiền COD đã tính (₫)', kpi.cod],
          ['Tổng tiền khách cọc (₫)', kpi.deposit]
        ];

        const wsKPI = XLSX.utils.aoa_to_sheet(kpiRows);

        const dailyHeaders = [['Ngày chốt', 'Số đơn chốt', 'Doanh thu (₫)', 'Lợi nhuận ròng (₫)', 'AOV (₫)']];
        const dailyRows = data.dailyBreakdown.map(d => {
          const aov = d.orders > 0 ? Math.round(d.revenue / d.orders) : 0;
          return [d.date, d.orders, d.revenue, d.profit, aov];
        });
        const wsDaily = XLSX.utils.aoa_to_sheet([...dailyHeaders, ...dailyRows]);

        const prodHeaders = [['Mã sản phẩm', 'Số lượng bán', 'Doanh thu (₫)', 'Lợi nhuận (₫)']];
        const prodRows = data.topProducts.map(p => [p.maSP, p.quantity, p.revenue, p.profit]);
        const wsProd = XLSX.utils.aoa_to_sheet([...prodHeaders, ...prodRows]);

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, wsKPI, "KPI Tổng Quan");
        XLSX.utils.book_append_sheet(wb, wsDaily, "Báo Cáo Chi Tiết Ngày");
        XLSX.utils.book_append_sheet(wb, wsProd, "Top Sản Phẩm");

        XLSX.writeFile(wb, `BaoCao_KinhDoanh_Tu_${startStr}_Den_${endStr}.xlsx`);
        hideLoading();
        showToast('Tải xuống file Excel báo cáo thành công!', 'success');
      } catch (e) {
        hideLoading();
        showToast('Lỗi xuất Excel: ' + e.message, 'error');
      }
    });
  }

  if (type === 'print' || type === 'pdf') {
    const kpi = data.kpi.current;
    const fmt = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
    const fmtNum = n => new Intl.NumberFormat('vi-VN').format(n);
    
    const [startY, startM, startD] = startStr.split('-');
    const [endY, endM, endD] = endStr.split('-');

    const printContainer = document.getElementById('print-report-template');
    printContainer.innerHTML = `
      <div class="print-header">
        <div>
          <h1>BÁO CÁO THỐNG KÊ DOANH THU</h1>
          <p>Hệ thống Quản lý Bán hàng Sales Admin System</p>
        </div>
        <div style="text-align:right;">
          <p><strong>Chu kỳ lọc:</strong> ${startD}/${startM}/${startY} đến ${endD}/${endM}/${endY}</p>
          <p>Ngày in báo cáo: ${new Date().toLocaleDateString('vi-VN')}</p>
        </div>
      </div>

      <div class="print-meta">
        <div><strong>Tổng doanh thu chu kỳ:</strong> ${fmt(kpi.revenue)}</div>
        <div><strong>Lợi nhuận ròng thu về:</strong> ${fmt(kpi.profit)}</div>
        <div><strong>Đơn hàng hoàn tất:</strong> ${fmtNum(kpi.orders)} đơn</div>
        <div><strong>Giá trị trung bình đơn (AOV):</strong> ${fmt(kpi.aov)}</div>
      </div>

      <h3 class="print-section-title">Chỉ số KPI chính</h3>
      <div class="print-kpi-grid">
        <div class="print-kpi-card">
          <h4>Tổng doanh thu</h4>
          <h2>${fmt(kpi.revenue)}</h2>
        </div>
        <div class="print-kpi-card">
          <h4>Lợi nhuận ròng</h4>
          <h2>${fmt(kpi.profit)}</h2>
        </div>
        <div class="print-kpi-card">
          <h4>Số đơn chốt</h4>
          <h2>${fmtNum(kpi.orders)} đơn</h2>
        </div>
        <div class="print-kpi-card">
          <h4>Giá trị TB đơn</h4>
          <h2>${fmt(kpi.aov)}</h2>
        </div>
      </div>

      <h3 class="print-section-title">Chi tiết doanh số theo ngày chốt</h3>
      <table class="print-table">
        <thead>
          <tr>
            <th>Ngày chốt</th>
            <th>Số đơn chốt</th>
            <th>Doanh thu</th>
            <th>Giá trị TB đơn</th>
            <th>Lợi nhuận ròng</th>
          </tr>
        </thead>
        <tbody>
          ${data.dailyBreakdown.map(d => {
            const [y, m, dayPart] = d.date.split('-');
            const aov = d.orders > 0 ? Math.round(d.revenue / d.orders) : 0;
            return `<tr>
              <td><strong>${dayPart}/${m}/${y}</strong></td>
              <td>${d.orders} đơn</td>
              <td>${fmt(d.revenue)}</td>
              <td>${fmt(aov)}</td>
              <td style="color:${d.profit >= 0 ? '#10b981' : '#ef4444'}; font-weight:bold;">
                ${d.profit >= 0 ? '+' : ''}${fmt(d.profit)}
              </td>
            </tr>`;
          }).join('')}
        </tbody>
      </table>

      <h3 class="print-section-title" style="page-break-before: always;">Top 10 sản phẩm bán chạy nhất</h3>
      <table class="print-table">
        <thead>
          <tr>
            <th>Mã sản phẩm</th>
            <th>Số lượng bán</th>
            <th>Doanh thu phát sinh</th>
            <th>Lợi nhuận gộp</th>
          </tr>
        </thead>
        <tbody>
          ${data.topProducts.map(p => `
            <tr>
              <td><strong>${p.maSP}</strong></td>
              <td>${p.quantity} sản phẩm</td>
              <td>${fmt(p.revenue)}</td>
              <td>${fmt(p.profit)}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>

      <div class="print-footer">
        <p>Báo cáo này được tự động xuất bởi Sales Admin Web App.</p>
        <p>Bản quyền thuộc về © Anta Sales Admin System. Trình in ấn của trình duyệt.</p>
      </div>
    `;

    setTimeout(() => {
      window.print();
    }, 300);
  }
}

// ─────────────────────────────────────────────
// VIETTEL POST GROUPED ORDERS MODULE (GỘP ĐƠN THEO KHÁCH)
// ─────────────────────────────────────────────

function formatDateDisplay(dateStr) {
  if (!dateStr) return '';
  const str = String(dateStr).trim();
  const m = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  const m2 = str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
  if (m2) return `${m2[1].padStart(2, '0')}/${m2[2].padStart(2, '0')}/${m2[3]}`;
  return str;
}

function dash(v) {
  return (v && String(v).trim()) ? escapeHtml(String(v).trim()) : '—';
}

function getViettelDateRange() {
  const fromEl = document.getElementById('viettel-date-from');
  const toEl   = document.getElementById('viettel-date-to');
  let start = fromEl ? fromEl.value : '';
  let end   = toEl   ? toEl.value   : '';
  if (!start || !end) {
    const dailyFrom = document.getElementById('daily-date-from')?.value;
    const dailyTo = document.getElementById('daily-date-to')?.value;
    if (dailyFrom && dailyTo) {
      start = dailyFrom;
      end = dailyTo;
    } else {
      const today = getTodayLocal();
      start = today;
      end = today;
    }
    if (fromEl) fromEl.value = start;
    if (toEl) toEl.value = end;
  }
  if (start && end && start > end) {
    const tmp = start;
    start = end;
    end = tmp;
    if (fromEl) fromEl.value = start;
    if (toEl) toEl.value = end;
  }
  return { start, end };
}

function setViettelToday() {
  const today = getTodayLocal();
  const fromEl = document.getElementById('viettel-date-from');
  const toEl   = document.getElementById('viettel-date-to');
  if (fromEl) fromEl.value = today;
  if (toEl) toEl.value = today;
  loadViettelOrdersPage();
}


function isGiauBaLe_(name) {
  if (!name) return false;
  const norm = normalizeVnText_(name).replace(/\s+/g, '');
  return norm.includes('giaubale') || (norm.includes('giau') && norm.includes('bale'));
}

function isViettelFreeship_(pkg) {
  if (!pkg) return false;
  const tenKhach = pkg.tenKhach || '';
  // Ngoài trừ Giaubale ra là còn lại phải đúng theo rule nhé., Giaubale thì auto freeship
  if (isGiauBaLe_(tenKhach)) {
    return true;
  }

  const ht = String(pkg.hinhThuc || '').toUpperCase();
  const giaTri = Number(pkg.tongGiaBan || pkg.giaBan || 0);
  const khachCoc = Number(pkg.tongKhachCoc || pkg.khachCoc || 0);
  const cod = (pkg.tongTienCOD !== undefined && pkg.tongTienCOD !== null && pkg.tongTienCOD !== '')
    ? Number(pkg.tongTienCOD) 
    : ((pkg.tienCOD !== undefined && pkg.tienCOD !== null && pkg.tienCOD !== '') ? Number(pkg.tienCOD) : null);

  // Khách cọc đủ hoặc thanh toán đủ = tiền hàng
  const isPaidFull = (khachCoc > 0 && giaTri > 0 && khachCoc >= giaTri) || (cod !== null && cod <= 0) || ht.includes('CK') || ht.includes('CHUYEN KHOAN');
  
  // Rule chuẩn: đơn hàng > 500k mà cọc đủ thanh toán đủ = tiền hàng thì mới Freeship
  if (giaTri > 500000 && isPaidFull) {
    return true;
  }
  return false;
}

function getViettelPayer_(pkg) {
  const tenKhach = pkg?.tenKhach || '';
  // Chỉ có anh Giau Ba Le thì auto người gửi trả cước
  if (isGiauBaLe_(tenKhach)) {
    return 'Người gửi';
  }

  // Đơn thỏa điều kiện Freeship (> 500k và cọc đủ) -> Người gửi trả cước
  if (isViettelFreeship_(pkg)) {
    return 'Người gửi';
  }

  // Còn lại tất cả các trường hợp (đơn <= 500k, hoặc đơn có COD > 0) -> Người nhận trả cước (chịu ship)
  return 'Người nhận';
}

function getViettelServiceAndDvct_(pkg) {
  const isFreeship = isViettelFreeship_(pkg);
  const giaTri = Number(pkg?.tongGiaBan || pkg?.giaBan || 0);
  const khachCoc = Number(pkg?.tongKhachCoc || pkg?.khachCoc || 0);
  let codAmount = 0;
  if (isFreeship) {
    codAmount = 0;
  } else if (pkg?.tongTienCOD !== undefined && pkg?.tongTienCOD !== null) {
    codAmount = Math.max(0, Number(pkg.tongTienCOD));
  } else if (pkg?.tienCOD !== undefined && pkg?.tienCOD !== null) {
    codAmount = Math.max(0, Number(pkg.tienCOD));
  } else if (khachCoc > 0 && khachCoc < giaTri) {
    codAmount = Math.max(0, giaTri - khachCoc);
  } else {
    codAmount = 0;
  }

  const userDv = String(pkg?.dichVu || '').trim();

  let dichVu = '';
  let dvct = '';

  if (codAmount <= 0) {
    // Thu hộ = 0: Dịch vụ VTK, dịch vụ cộng thêm: GKN, PXD
    if (userDv === 'PHS' || userDv === 'Nội tỉnh tiết kiệm' || userDv.toLowerCase().includes('nội tỉnh')) {
      dichVu = 'PHS';
    } else if (userDv === 'VCN' || userDv === 'CP nhanh thỏa thuận') {
      dichVu = 'VCN';
    } else if (userDv === 'VHT' || userDv === 'Hỏa tốc thỏa thuận') {
      dichVu = 'VHT';
    } else {
      dichVu = 'VTK';
    }
    dvct = 'GKN, PXD';
  } else {
    // Có thu hộ: Dịch vụ LCOD, dịch vụ cộng thêm: COD, PXD, GKN
    if (userDv === 'PHS' || userDv === 'Nội tỉnh tiết kiệm' || userDv.toLowerCase().includes('nội tỉnh')) {
      dichVu = 'PHS';
    } else if (userDv === 'VCN' || userDv === 'CP nhanh thỏa thuận') {
      dichVu = 'VCN';
    } else if (userDv === 'VHT' || userDv === 'Hỏa tốc thỏa thuận') {
      dichVu = 'VHT';
    } else {
      dichVu = 'LCOD';
    }
    dvct = 'COD, PXD, GKN';
  }

  // Tắt SMS khi chọn nội tỉnh tiết kiệm (PHS)
  if (dichVu === 'PHS' || dichVu === 'Nội tỉnh tiết kiệm') {
    dvct = dvct.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
  }

  return { dichVu, dvct, codAmount };
}

function normalizeCustomerPhone_(phone) {
  if (!phone) return '';
  let p = String(phone).trim();
  p = p.replace(/[\s\.\-\(\)]/g, '');
  if (p.startsWith('+84')) p = '0' + p.slice(3);
  else if (p.startsWith('84') && p.length >= 10) p = '0' + p.slice(2);
  if (/^\d{8,15}$/.test(p)) return p;
  return '';
}

function normalizeCustomerNameKey_(name) {
  if (!name) return '';
  let n = String(name).trim().toLowerCase();
  n = n.replace(/\s+/g, ' ');
  return n;
}

function groupOrdersByCustomer_(orders) {
  if (!Array.isArray(orders)) return [];
  
  // Pass 1: Build name-to-phone lookup for orders with valid phone and clean name
  const nameToPhoneMap = {};
  orders.forEach(r => {
    const ph = normalizeCustomerPhone_(r.sdtKhach);
    const nm = normalizeCustomerNameKey_(r.tenKhach);
    if (ph && nm && nm !== '-' && nm !== '—') {
      nameToPhoneMap[nm] = ph;
    }
  });

  // Pass 2: Group orders into packages
  const groupMap = {};
  orders.forEach(r => {
    let ph = normalizeCustomerPhone_(r.sdtKhach);
    const nm = normalizeCustomerNameKey_(r.tenKhach);
    if (!ph && nm && nameToPhoneMap[nm]) {
      ph = nameToPhoneMap[nm];
    }

    let groupKey = '';
    if (ph) {
      groupKey = 'phone_' + ph;
    } else if (nm && nm !== '-' && nm !== '—') {
      groupKey = 'name_' + nm;
    } else {
      groupKey = 'row_' + (r.rowIndex || Math.random().toString(36).slice(2));
    }

    if (!groupMap[groupKey]) {
      groupMap[groupKey] = {
        key: groupKey,
        tenKhach: String(r.tenKhach || '').trim(),
        sdtKhach: ph || String(r.sdtKhach || '').trim(),
        diaChi: String(r.diaChi || '').trim(),
        items: [],
        tongGiaBan: 0,
        tongGiaVon: 0,
        tongKhachCoc: 0,
        tongKhoiLuong: 0,
        ghiChu: String(r.ghiChu || 'CHO HÀNG XEM').trim(),
        hinhThuc: String(r.hinhThuc || 'COD').trim()
      };
    }

    const g = groupMap[groupKey];
    g.items.push(r);

    if (!g.diaChi && r.diaChi) g.diaChi = String(r.diaChi).trim();
    if (!g.sdtKhach && r.sdtKhach) g.sdtKhach = String(r.sdtKhach).trim();

    // Auto-lookup from customer book or previous records if missing
    if (!g.diaChi || !g.sdtKhach) {
      const hist = lookupCustomerFromViettelBook(g.sdtKhach, g.tenKhach);
      if (hist) {
        if (!g.diaChi && hist.address) g.diaChi = hist.address;
        if (!g.sdtKhach && hist.phone) g.sdtKhach = hist.phone;
      }
    }
    if (String(r.tenKhach || '').trim().length > g.tenKhach.length) {
      g.tenKhach = String(r.tenKhach).trim();
    }
    g.tongGiaBan += Number(r.giaBan) || 0;
    g.tongGiaVon += Number(r.giaVon) || 0;
    g.tongKhachCoc += Number(r.khachCoc) || 0;
    g.tongKhoiLuong += Number(r.khoiLuong) || 200;
  });

  const packages = Object.values(groupMap).map(g => {
    const isFreeship = isViettelFreeship_(g);
    const anyExplicitCod = g.items.some(it => it.tienCOD !== undefined && it.tienCOD !== null && it.tienCOD !== '');
    
    // Tính tổng tiền COD cần thu hàng
    if (g.tongKhachCoc > 0 && g.tongKhachCoc >= g.tongGiaBan) {
      // Khách đã cọc/chuyển khoản đủ 100% tiền hàng -> Tiền COD hàng = 0
      g.tongTienCOD = 0;
    } else if (anyExplicitCod) {
      g.tongTienCOD = Math.max(0, g.items.reduce((sum, it) => sum + (Number(it.tienCOD) || 0), 0));
    } else if (g.tongKhachCoc > 0 && g.tongKhachCoc < g.tongGiaBan) {
      g.tongTienCOD = Math.max(0, g.tongGiaBan - g.tongKhachCoc);
    } else {
      g.tongTienCOD = 0;
    }

    // Xác định hình thức đơn:
    if (isFreeship) {
      g.hinhThuc = 'Freeship';
    } else if (g.tongTienCOD > 0) {
      g.hinhThuc = 'COD';
    } else {
      // Khách đã thanh toán đủ nhưng đơn <= 500k -> Khách chịu ship
      g.hinhThuc = 'Chịu ship';
    }

    g.itemCount = g.items.length;
    g.maSPList = g.items.map(it => String(it.maSP || '').trim()).filter(Boolean);
    g.hasValidMaSP = g.maSPList.length === g.items.length && g.items.length > 0;
    g.hasValidPhone = Boolean(g.sdtKhach && g.sdtKhach.replace(/\D/g, '').length >= 8);
    g.hasValidAddress = Boolean(g.diaChi && g.diaChi.length >= 5);

    const firstLoaiHang = g.items.find(it => it.loaiHangHoa)?.loaiHangHoa;
    const firstTinhChat = g.items.find(it => it.tinhChatHangHoa)?.tinhChatHangHoa;
    const firstDichVu = g.items.find(it => it.dichVu)?.dichVu;
    const firstDvct = g.items.find(it => it.dichVuCongThem)?.dichVuCongThem;

    g.loaiHangHoa = firstLoaiHang || 'Bưu kiện';
    g.tinhChatHangHoa = firstTinhChat || '';

    const svcInfo = getViettelServiceAndDvct_({
      hinhThuc: g.hinhThuc,
      tongGiaBan: g.tongGiaBan,
      tongKhachCoc: g.tongKhachCoc,
      tongTienCOD: g.tongTienCOD,
      dichVu: firstDichVu,
      dichVuCongThem: firstDvct
    });
    g.dichVu = svcInfo.dichVu;
    g.dichVuCongThem = svcInfo.dvct;
    g.nguoiTraCuoc = getViettelPayer_(g);
    
    g.missingFields = [];
    if (!g.hasValidAddress) g.missingFields.push('Địa chỉ');
    if (!g.hasValidPhone) g.missingFields.push('SĐT');
    if (!g.hasValidMaSP) g.missingFields.push('Mã SP');

    g.isReady = g.hasValidMaSP && g.hasValidPhone && g.hasValidAddress && Boolean(g.tenKhach);
    return g;
  });

  return packages;
}

function loadViettelOrdersPage(forceRefresh) {
  const range = getViettelDateRange();
  const subtitleEl = document.getElementById('viettel-orders-subtitle');
  if (subtitleEl) subtitleEl.textContent = `Đang tải dữ liệu từ ${formatDateDisplay(range.start)} đến ${formatDateDisplay(range.end)}...`;

  const doRender = rows => {
    const validRows = (rows || []).filter(r => r && r.trangThai !== 'Đã hủy' && r.trangThai !== 'Đã xóa');
    const packages = groupOrdersByCustomer_(validRows);
    window._currentViettelPackages = packages;
    renderViettelOrders(packages, range);
  };

  const cachedRows = (crmSnapshot?.dailyRows && crmSnapshot.dailyRows.length > 0)
    ? crmSnapshot.dailyRows
    : ((allReportRows && allReportRows.length > 0) ? allReportRows : null);

  if (!forceRefresh && cachedRows) {
    const filtered = filterDailyOrders(cachedRows, range);
    doRender(filtered);
    return;
  }

  showLoading('Đang tải dữ liệu đơn chốt...');
  google.script.run
    .withSuccessHandler(res => {
      hideLoading();
      if (!res) return;
      crmSnapshot = res;
      if (res.rows) allRows = res.rows;
      if (res.reportRows) allReportRows = res.reportRows;
      const targetRows = (res.dailyRows && res.dailyRows.length > 0) ? res.dailyRows : (res.reportRows || allReportRows || []);
      const filtered = filterDailyOrders(targetRows, range);
      doRender(filtered);
    })
    .withFailureHandler(err => {
      hideLoading();
      showToast('Lỗi tải dữ liệu: ' + err.message, 'error');
    })
    .getCrmSyncSnapshot({ forceRefresh: Boolean(forceRefresh) });
}

function renderViettelOrders(packages, range) {
  const subtitleEl = document.getElementById('viettel-orders-subtitle');
  if (subtitleEl) {
    const rangeText = range.start === range.end 
      ? `Ngày ${formatDateDisplay(range.start)}`
      : `Từ ${formatDateDisplay(range.start)} đến ${formatDateDisplay(range.end)}`;
    subtitleEl.textContent = `${rangeText} • ${packages.length} kiện hàng gộp theo khách`;
  }

  const totalItems = packages.reduce((acc, p) => acc + p.itemCount, 0);
  const readyCount = packages.filter(p => p.isReady).length;
  const missingCount = packages.length - readyCount;
  const totalCOD = packages.reduce((acc, p) => acc + p.tongTienCOD, 0);
  const totalWeight = packages.reduce((acc, p) => acc + p.tongKhoiLuong, 0);
  const totalRevenue = packages.reduce((acc, p) => acc + p.tongGiaBan, 0);
  const totalDeposit = packages.reduce((acc, p) => acc + p.tongKhachCoc, 0);

  const elPackages = document.getElementById('viettel-pill-packages');
  if (elPackages) elPackages.textContent = packages.length;
  const elTotalItems = document.getElementById('viettel-pill-total-items');
  if (elTotalItems) elTotalItems.textContent = `Từ ${totalItems} sản phẩm`;
  const elReady = document.getElementById('viettel-pill-ready');
  if (elReady) elReady.textContent = `${readyCount} kiện`;
  const elMissing = document.getElementById('viettel-pill-missing');
  if (elMissing) elMissing.textContent = `${missingCount} kiện`;
  const elCOD = document.getElementById('viettel-pill-cod');
  if (elCOD) elCOD.textContent = fmtVnd(totalCOD);
  const elWeight = document.getElementById('viettel-pill-weight');
  if (elWeight) elWeight.textContent = `Tổng: ${new Intl.NumberFormat('vi-VN').format(totalWeight)}g`;

  const navBadge = document.getElementById('nav-badge-viettel');
  if (navBadge) {
    navBadge.textContent = packages.length;
    navBadge.style.display = packages.length > 0 ? 'inline-block' : 'none';
  }

  const emptyEl = document.getElementById('viettel-empty');
  const tableEl = document.getElementById('viettel-orders-table');
  const tbodyEl = document.getElementById('viettel-orders-tbody');
  const tfootEl = document.getElementById('viettel-orders-tfoot');

  if (packages.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    if (tableEl) tableEl.style.display = 'none';
    return;
  }

  if (emptyEl) emptyEl.style.display = 'none';
  if (tableEl) tableEl.style.display = 'table';

  tbodyEl.innerHTML = packages.map((pkg, idx) => {
    const multiBadge = pkg.itemCount > 1 
      ? `<span class="badge" style="background:rgba(224,44,27,0.15); color:#ff6b6b; font-weight:700; margin-left:6px; font-size:0.75rem;"><i class="fas fa-layer-group"></i> Gộp ${pkg.itemCount} SP</span>`
      : '';

    const custBadge = getCustomerBadgeHtml(pkg.tenKhach, pkg.sdtKhach);

    const skusHtml = pkg.items.map(it => {
      const ma = escapeHtml(it.maSP || 'Chưa có mã');
      const pr = fmtVnd(it.giaBan || 0);
      return `<span class="badge badge-info" style="font-size:0.75rem; font-weight:600; padding:2px 6px; margin:2px;" title="${ma} - Giá bán: ${pr}">${ma}</span>`;
    }).join(' ');

    const addressHtml = pkg.diaChi 
      ? `<span title="${escapeHtml(pkg.diaChi)}" style="display:inline-block; max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${escapeHtml(pkg.diaChi)}</span>`
      : `<span class="badge badge-danger" style="font-size:0.75rem;"><i class="fas fa-map-marker-alt"></i> Chưa có địa chỉ</span>`;

    const phoneHtml = pkg.sdtKhach
      ? escapeHtml(pkg.sdtKhach)
      : `<span class="badge badge-warning" style="font-size:0.75rem;">Thiếu SĐT</span>`;

    let statusHtml = '';
    if (pkg.isReady) {
      statusHtml = `<span class="badge badge-success" style="font-size:0.75rem;"><i class="fas fa-check-circle"></i> Đủ ĐK in bill</span>`;
    } else if (pkg.missingFields.length > 0) {
      statusHtml = `<span class="badge badge-warning" style="font-size:0.75rem;" title="Thiếu: ${pkg.missingFields.join(', ')}"><i class="fas fa-exclamation-triangle"></i> Thiếu ${pkg.missingFields.join(', ')}</span>`;
    } else {
      statusHtml = `<span class="badge badge-danger" style="font-size:0.75rem;"><i class="fas fa-times-circle"></i> Chưa đủ điều kiện</span>`;
    }

    const safeKey = escapeForInlineEdit(pkg.key);

    return `<tr>
      <td>${idx + 1}</td>
      <td>
        <div style="display:flex; align-items:center; flex-wrap:wrap; gap:4px;">
          <strong>${dash(pkg.tenKhach)}</strong>${custBadge}${multiBadge}
        </div>
      </td>
      <td>${phoneHtml}</td>
      <td>${addressHtml}</td>
      <td>
        <div style="display:flex; flex-wrap:wrap; gap:4px; max-width:220px;">
          ${skusHtml}
        </div>
      </td>
      <td style="text-align:center; font-size:0.85rem; color:var(--text-muted); font-weight:600;">${pkg.tongKhoiLuong}g</td>
      <td style="font-weight:600;">${fmtVnd(pkg.tongGiaBan)}</td>
      <td style="color:var(--text-muted);">${pkg.tongKhachCoc ? fmtVnd(pkg.tongKhachCoc) : '—'}</td>
      <td style="font-weight:700; color:var(--warning);">${pkg.hinhThuc === 'Freeship' ? '<span class="badge badge-success"><i class="fas fa-shipping-fast fa-xs"></i> Freeship</span>' : (pkg.tongTienCOD > 0 ? fmtVnd(pkg.tongTienCOD) : '<span class="badge badge-warning" style="font-size:0.75rem;"><i class="fas fa-motorcycle fa-xs"></i> 0 ₫ (Chịu ship)</span>')}</td>
      <td style="font-size:0.82rem; color:var(--text-muted);" title="${escapeHtml(pkg.ghiChu)}">${escapeHtml(pkg.ghiChu || 'CHO HÀNG XEM')}</td>
      <td>${statusHtml}</td>
      <td style="text-align:center; white-space:nowrap;">
        <button class="btn btn-sm btn-primary" onclick="openViettelPackageModal('${safeKey}')" title="Tạo đơn / Bổ sung thông tin gửi hàng Viettel Post" style="background:#e02c1b; border-color:#e02c1b; color:#fff; font-weight:600; padding:5px 10px; border-radius:6px; display:inline-flex; align-items:center; gap:5px; margin-right:4px;">
          <i class="fas fa-shipping-fast"></i> Tạo đơn
        </button>
        <button class="btn btn-sm btn-ghost" onclick="exportSingleViettelPackage('${safeKey}')" style="border:1px solid var(--border); padding:5px 8px; border-radius:6px;" title="Xuất file Excel cho riêng kiện này">
          <i class="fas fa-file-excel" style="color:#10b981;"></i>
        </button>
      </td>
    </tr>`;
  }).join('');

  if (tfootEl) {
    tfootEl.innerHTML = `
      <tr>
        <td></td>
        <td><strong>TỔNG: ${packages.length} kiện (${totalItems} SP)</strong></td>
        <td></td>
        <td></td>
        <td></td>
        <td style="text-align:center; font-weight:700;">${new Intl.NumberFormat('vi-VN').format(totalWeight)}g</td>
        <td style="font-weight:700;">${fmtVnd(totalRevenue)}</td>
        <td style="font-weight:700;">${fmtVnd(totalDeposit)}</td>
        <td style="font-weight:700; color:var(--warning);">${fmtVnd(totalCOD)}</td>
        <td></td>
        <td style="font-size:0.82rem;"><strong>${readyCount} đủ / ${packages.length} kiện</strong></td>
        <td></td>
      </tr>
    `;
  }
}

// ══════════════════════════════════════════════════════
// VIETNAM ADMINISTRATIVE DIVISIONS & ADDRESS PARSER
// ══════════════════════════════════════════════════════
const VN_ADMIN_DIVISIONS = [
  { name: 'Hà Nội', isNoiTinh: true, aliases: ['ha noi', 'hanoi', 'hn', 'tp ha noi', 'thanh pho ha noi', 'ha tay'],
    districts: ['Ba Đình', 'Hoàn Kiếm', 'Tây Hồ', 'Long Biên', 'Cầu Giấy', 'Đống Đa', 'Hai Bà Trưng', 'Hoàng Mai', 'Thanh Xuân', 'Sóc Sơn', 'Đông Anh', 'Gia Lâm', 'Nam Từ Liêm', 'Thanh Trì', 'Bắc Từ Liêm', 'Mê Linh', 'Hà Đông', 'Sơn Tây', 'Ba Vì', 'Phúc Thọ', 'Đan Phượng', 'Hoài Đức', 'Quốc Oai', 'Thạch Thất', 'Chương Mỹ', 'Thanh Oai', 'Thường Tín', 'Phú Xuyên', 'Ứng Hòa', 'Mỹ Đức'] },
  { name: 'TP Hồ Chí Minh', aliases: ['tp hcm', 'tp.hcm', 'ho chi minh', 'hcm', 'sai gon', 'saigon', 'thanh pho ho chi minh'],
    districts: ['Quận 1', 'Quận 3', 'Quận 4', 'Quận 5', 'Quận 6', 'Quận 7', 'Quận 8', 'Quận 10', 'Quận 11', 'Quận 12', 'Bình Tân', 'Bình Thạnh', 'Gò Vấp', 'Phú Nhuận', 'Tân Bình', 'Tân Phú', 'TP Thủ Đức', 'Thủ Đức', 'Bình Chánh', 'Cần Giờ', 'Củ Chi', 'Hóc Môn', 'Nhà Bè'] },
  { name: 'Hải Phòng', aliases: ['hai phong', 'hp'],
    districts: ['Hồng Bàng', 'Ngô Quyền', 'Lê Chân', 'Hải An', 'Kiến An', 'Đồ Sơn', 'Dương Kinh', 'Thuỷ Nguyên', 'An Dương', 'An Lão', 'Kiến Thuỵ', 'Tiên Lãng', 'Vĩnh Bảo', 'Cát Hải', 'Bạch Long Vĩ'] },
  { name: 'Đà Nẵng', aliases: ['da nang', 'dn'],
    districts: ['Hải Châu', 'Thanh Khê', 'Sơn Trà', 'Ngũ Hành Sơn', 'Liên Chiểu', 'Cẩm Lệ', 'Hòa Vang', 'Hoàng Sa'] },
  { name: 'Cần Thơ', aliases: ['can tho', 'ct'],
    districts: ['Ninh Kiều', 'Ô Môn', 'Bình Thuỷ', 'Cái Răng', 'Thốt Nốt', 'Vĩnh Thạnh', 'Cờ Đỏ', 'Phong Điền', 'Thới Lai'] },
  { name: 'An Giang', aliases: ['an giang'],
    districts: ['Long Xuyên', 'Châu Đốc', 'Tân Châu', 'Tịnh Biên', 'An Phú', 'Châu Phú', 'Châu Thành', 'Chợ Mới', 'Phú Tân', 'Thoại Sơn', 'Tri Tôn'] },
  { name: 'Bà Rịa - Vũng Tàu', aliases: ['ba ria vung tau', 'vung tau', 'brvt'],
    districts: ['Vũng Tàu', 'Bà Rịa', 'Phú Mỹ', 'Châu Đức', 'Xuyên Mộc', 'Long Điền', 'Đất Đỏ', 'Côn Đảo'] },
  { name: 'Bắc Giang', aliases: ['bac giang'],
    districts: ['Bắc Giang', 'Hiệp Hòa', 'Lạng Giang', 'Lục Nam', 'Lục Ngạn', 'Sơn Động', 'Tân Yên', 'Việt Yên', 'Yên Dũng', 'Yên Thế'] },
  { name: 'Bắc Kạn', aliases: ['bac kan', 'bac can'],
    districts: ['Bắc Kạn', 'Ba Bể', 'Bạch Thông', 'Chợ Đồn', 'Chợ Mới', 'Na Rì', 'Ngân Sơn', 'Pác Nặm'] },
  { name: 'Bạc Liêu', aliases: ['bac lieu'],
    districts: ['Bạc Liêu', 'Giá Rai', 'Đông Hải', 'Hòa Bình', 'Hồng Dân', 'Phước Long', 'Vĩnh Lợi'] },
  { name: 'Bắc Ninh', aliases: ['bac ninh', 'bn'],
    districts: ['Bắc Ninh', 'Từ Sơn', 'Yên Phong', 'Quế Võ', 'Tiên Du', 'Thuận Thành', 'Gia Bình', 'Lương Tài'] },
  { name: 'Bến Tre', aliases: ['ben tre'],
    districts: ['Bến Tre', 'Ba Tri', 'Bình Đại', 'Châu Thành', 'Chợ Lách', 'Giồng Trôm', 'Mỏ Cày Bắc', 'Mỏ Cày Nam', 'Thạnh Phú'] },
  { name: 'Bình Định', aliases: ['binh dinh', 'quy nhon'],
    districts: ['Quy Nhơn', 'An Nhơn', 'Hoài Nhơn', 'An Lão', 'Hoài Ân', 'Phù Cát', 'Phù Mỹ', 'Tuy Phước', 'Tây Sơn', 'Vân Canh', 'Vĩnh Thạnh'] },
  { name: 'Bình Dương', aliases: ['binh duong', 'bd'],
    districts: ['Thủ Dầu Một', 'Dĩ An', 'Thuận An', 'Tân Uyên', 'Bến Cát', 'Bàu Bàng', 'Dầu Tiếng', 'Phú Giáo', 'Bắc Tân Uyên'] },
  { name: 'Bình Phước', aliases: ['binh phuoc'],
    districts: ['Đồng Xoài', 'Bình Long', 'Phước Long', 'Bù Đăng', 'Bù Đốp', 'Bù Gia Mập', 'Chơn Thành', 'Đồng Phú', 'Hớn Quản', 'Lộc Ninh', 'Phú Riềng'] },
  { name: 'Bình Thuận', aliases: ['binh thuan', 'phan thiet'],
    districts: ['Phan Thiết', 'La Gi', 'Bắc Bình', 'Đức Linh', 'Hàm Tân', 'Hàm Thuận Bắc', 'Hàm Thuận Nam', 'Phú Quý', 'Tánh Linh', 'Tuy Phong'] },
  { name: 'Cà Mau', aliases: ['ca mau'],
    districts: ['Cà Mau', 'Cái Nước', 'Đầm Dơi', 'Năm Căn', 'Ngọc Hiển', 'Phú Tân', 'Thới Bình', 'Trần Văn Thời', 'U Minh'] },
  { name: 'Cao Bằng', aliases: ['cao bang'],
    districts: ['Cao Bằng', 'Bảo Lạc', 'Bảo Lâm', 'Hạ Lang', 'Hà Quảng', 'Hòa An', 'Nguyên Bình', 'Quảng Hòa', 'Thạch An', 'Trùng Khánh'] },
  { name: 'Đắk Lắk', aliases: ['dak lak', 'dac lac', 'buon ma thuot', 'bmt'],
    districts: ['Buôn Ma Thuột', 'Buôn Hồ', 'Buôn Đôn', 'Cư Kuin', 'Cư M\'gar', 'Ea H\'leo', 'Ea Kar', 'Ea Súp', 'Krông Ana', 'Krông Bông', 'Krông Búk', 'Krông Năng', 'Krông Pắc', 'Lắk', 'M\'Drắk'] },
  { name: 'Đắk Nông', aliases: ['dak nong', 'dac nong', 'gia nghia'],
    districts: ['Gia Nghĩa', 'Cư Jút', 'Đắk Glong', 'Đắk Mil', 'Đắk R\'Lấp', 'Đắk Song', 'Krông Nô', 'Tuy Đức'] },
  { name: 'Điện Biên', aliases: ['dien bien', 'dien bien phu'],
    districts: ['Điện Biên Phủ', 'Mường Lay', 'Điện Biên', 'Điện Biên Đông', 'Mường Ảng', 'Mường Chà', 'Mường Nhé', 'Nậm Pồ', 'Tủa Chùa', 'Tuần Giáo'] },
  { name: 'Đồng Nai', aliases: ['dong nai', 'bien hoa'],
    districts: ['Biên Hòa', 'Long Khánh', 'Cẩm Mỹ', 'Định Quán', 'Long Thành', 'Nhơn Trạch', 'Tân Phú', 'Thống Nhất', 'Trảng Bom', 'Vĩnh Cửu', 'Xuân Lộc'] },
  { name: 'Đồng Tháp', aliases: ['dong thap', 'cao lanh'],
    districts: ['Cao Lãnh', 'Sa Đéc', 'Hồng Ngự', 'Châu Thành', 'Lai Vung', 'Lấp Vò', 'Tam Nông', 'Tân Hồng', 'Thanh Bình', 'Tháp Mười'] },
  { name: 'Gia Lai', aliases: ['gia lai', 'pleiku'],
    districts: ['Pleiku', 'An Khê', 'Ayun Pa', 'Chư Păh', 'Chư Prông', 'Chư Pưh', 'Chư Sê', 'Đắk Đoa', 'Đắk Pơ', 'Đức Cơ', 'Ia Grai', 'Ia Pa', 'K\'Bang', 'Kông Chro', 'Krông Pa', 'Mang Yang', 'Phú Thiện'] },
  { name: 'Hà Giang', aliases: ['ha giang'],
    districts: ['Hà Giang', 'Bắc Mê', 'Bắc Quang', 'Đồng Văn', 'Hoàng Su Phì', 'Mèo Vạc', 'Quản Bạ', 'Quang Bình', 'Vị Xuyên', 'Xín Mần', 'Yên Minh'] },
  { name: 'Hà Nam', aliases: ['ha nam', 'phu ly'],
    districts: ['Phủ Lý', 'Duy Tiên', 'Bình Lục', 'Kim Bảng', 'Lý Nhân', 'Thanh Liêm'] },
  { name: 'Hà Tĩnh', aliases: ['ha tinh'],
    districts: ['Hà Tĩnh', 'Hồng Lĩnh', 'Kỳ Anh', 'Cẩm Xuyên', 'Can Lộc', 'Đức Thọ', 'Hương Khê', 'Hương Sơn', 'Lộc Hà', 'Nghi Xuân', 'Thạch Hà', 'Vũ Quang'] },
  { name: 'Hải Dương', aliases: ['hai duong'],
    districts: ['Hải Dương', 'Chí Linh', 'Kinh Môn', 'Bình Giang', 'Cẩm Giàng', 'Gia Lộc', 'Kim Thành', 'Nam Sách', 'Ninh Giang', 'Thanh Hà', 'Thanh Miện', 'Tứ Kỳ'] },
  { name: 'Hậu Giang', aliases: ['hau giang', 'vi thanh'],
    districts: ['Vị Thanh', 'Ngã Bảy', 'Châu Thành', 'Châu Thành A', 'Long Mỹ', 'Phụng Hiệp', 'Vị Thủy'] },
  { name: 'Hòa Bình', aliases: ['hoa binh'],
    districts: ['Hòa Bình', 'Cao Phong', 'Đà Bắc', 'Kim Bôi', 'Lạc Sơn', 'Lạc Thủy', 'Lương Sơn', 'Mai Châu', 'Tân Lạc', 'Yên Thủy'] },
  { name: 'Hưng Yên', aliases: ['hung yen'],
    districts: ['Hưng Yên', 'Mỹ Hào', 'Ân Thi', 'Khoái Châu', 'Kim Động', 'Phù Cừ', 'Tiên Lữ', 'Văn Giang', 'Văn Lâm', 'Yên Mỹ'] },
  { name: 'Khánh Hòa', aliases: ['khanh hoa', 'nha trang', 'cam ranh'],
    districts: ['Nha Trang', 'Cam Ranh', 'Ninh Hòa', 'Cam Lâm', 'Diên Khánh', 'Khánh Sơn', 'Khánh Vĩnh', 'Trường Sa', 'Vạn Ninh'] },
  { name: 'Kiên Giang', aliases: ['kien giang', 'rach gia', 'phu quoc'],
    districts: ['Rạch Giá', 'Hà Tiên', 'Phú Quốc', 'An Biên', 'An Minh', 'Châu Thành', 'Giang Thành', 'Giồng Riềng', 'Gò Quao', 'Hòn Đất', 'Kiên Hải', 'Kiên Lương', 'Tân Hiệp', 'U Minh Thượng', 'Vĩnh Thuận'] },
  { name: 'Kon Tum', aliases: ['kon tum'],
    districts: ['Kon Tum', 'Đắk Glei', 'Đắk Hà', 'Đắk Tô', 'Ia H\'Drai', 'Kon Plông', 'Kon Rẫy', 'Ngọc Hồi', 'Sa Thầy', 'Tu Mơ Rông'] },
  { name: 'Lai Châu', aliases: ['lai chau'],
    districts: ['Lai Châu', 'Mường Tè', 'Nậm Nhùn', 'Phong Thổ', 'Sìn Hồ', 'Tam Đường', 'Tân Uyên', 'Than Uyên'] },
  { name: 'Lâm Đồng', aliases: ['lam dong', 'da lat', 'bao loc'],
    districts: ['Đà Lạt', 'Bảo Lộc', 'Bảo Lâm', 'Cát Tiên', 'Di Linh', 'Đạ Huoai', 'Đạ Tẻh', 'Đam Rông', 'Đơn Dương', 'Đức Trọng', 'Lạc Dương', 'Lâm Hà'] },
  { name: 'Lạng Sơn', aliases: ['lang son'],
    districts: ['Lạng Sơn', 'Bắc Sơn', 'Bình Gia', 'Cao Lộc', 'Chi Lăng', 'Đình Lập', 'Hữu Lũng', 'Lộc Bình', 'Tràng Định', 'Văn Lãng', 'Văn Quan'] },
  { name: 'Lào Cai', aliases: ['lao cai', 'sa pa', 'sapa'],
    districts: ['Lào Cai', 'Sa Pa', 'Bát Xát', 'Bảo Thắng', 'Bảo Yên', 'Bắc Hà', 'Mường Khương', 'Si Ma Cai', 'Văn Bàn'] },
  { name: 'Long An', aliases: ['long an', 'tan an'],
    districts: ['Tân An', 'Kiến Tường', 'Bến Lức', 'Cần Đước', 'Cần Giuộc', 'Châu Thành', 'Đức Hòa', 'Đức Huệ', 'Mộc Hóa', 'Tân Hưng', 'Tân Thạnh', 'Tân Trụ', 'Thạnh Hóa', 'Thủ Thừa', 'Vĩnh Hưng'] },
  { name: 'Nam Định', aliases: ['nam dinh'],
    districts: ['Nam Định', 'Giao Thủy', 'Hải Hậu', 'Mỹ Lộc', 'Nam Trực', 'Nghĩa Hưng', 'Trực Ninh', 'Vụ Bản', 'Xuân Trường', 'Ý Yên'] },
  { name: 'Nghệ An', aliases: ['nghe an', 'vinh', 'cua lo'],
    districts: ['Vinh', 'Cửa Lò', 'Hoàng Mai', 'Thái Hòa', 'Anh Sơn', 'Con Cuông', 'Diễn Châu', 'Đô Lương', 'Hưng Nguyên', 'Kỳ Sơn', 'Nam Đàn', 'Nghi Lộc', 'Nghĩa Đàn', 'Quế Phong', 'Quỳ Châu', 'Quỳ Hợp', 'Quỳnh Lưu', 'Tân Kỳ', 'Thanh Chương', 'Tương Dương', 'Yên Thành'] },
  { name: 'Ninh Bình', aliases: ['ninh binh'],
    districts: ['Ninh Bình', 'Tam Điệp', 'Gia Viễn', 'Hoa Lư', 'Kim Sơn', 'Nho Quan', 'Yên Khánh', 'Yên Mô'] },
  { name: 'Ninh Thuận', aliases: ['ninh thuan', 'phan rang'],
    districts: ['Phan Rang - Tháp Chàm', 'Bác Ái', 'Ninh Hải', 'Ninh Phước', 'Ninh Sơn', 'Thuận Bắc', 'Thuận Nam'] },
  { name: 'Phú Thọ', aliases: ['phu tho', 'viet tri'],
    districts: ['Việt Trì', 'Phú Thọ', 'Cẩm Khê', 'Đoan Hùng', 'Hạ Hòa', 'Lâm Thao', 'Phù Ninh', 'Tam Nông', 'Tân Sơn', 'Thanh Ba', 'Thanh Sơn', 'Thanh Thủy', 'Yên Lập'] },
  { name: 'Phú Yên', aliases: ['phu yen', 'tuy hoa'],
    districts: ['Tuy Hòa', 'Sông Cầu', 'Đông Hòa', 'Đồng Xuân', 'Phú Hòa', 'Sơn Hòa', 'Sông Hinh', 'Tây Hòa', 'Tuy An'] },
  { name: 'Quảng Bình', aliases: ['quang binh', 'dong hoi'],
    districts: ['Đồng Hới', 'Ba Đồn', 'Bố Trạch', 'Lệ Thủy', 'Minh Hóa', 'Quảng Ninh', 'Quảng Trạch', 'Tuyên Hóa'] },
  { name: 'Quảng Nam', aliases: ['quang nam', 'tam ky', 'hoi an'],
    districts: ['Tam Kỳ', 'Hội An', 'Điện Bàn', 'Bắc Trà My', 'Đại Lộc', 'Đông Giang', 'Duy Xuyên', 'Hiệp Đức', 'Nam Giang', 'Nam Trà My', 'Nông Sơn', 'Núi Thành', 'Phú Ninh', 'Phước Sơn', 'Quế Sơn', 'Tây Giang', 'Thăng Bình', 'Tiên Phước'] },
  { name: 'Quảng Ngãi', aliases: ['quang ngai'],
    districts: ['Quảng Ngãi', 'Đức Phổ', 'Ba Tơ', 'Bình Sơn', 'Lý Sơn', 'Minh Long', 'Mộ Đức', 'Nghĩa Hành', 'Sơn Hà', 'Sơn Tây', 'Sơn Tịnh', 'Trà Bồng', 'Tư Nghĩa'] },
  { name: 'Quảng Ninh', aliases: ['quang ninh', 'ha long', 'cam pha', 'uong bi'],
    districts: ['Hạ Long', 'Cẩm Phả', 'Uông Bí', 'Móng Cái', 'Đông Triều', 'Quảng Yên', 'Ba Chẽ', 'Bình Liêu', 'Cô Tô', 'Đầm Hà', 'Hải Hà', 'Tiên Yên', 'Vân Đồn'] },
  { name: 'Quảng Trị', aliases: ['quang tri', 'dong ha'],
    districts: ['Đông Hà', 'Quảng Trị', 'Cam Lộ', 'Cồn Cỏ', 'Đakrông', 'Gio Linh', 'Hải Lăng', 'Hướng Hóa', 'Triệu Phong', 'Vĩnh Linh'] },
  { name: 'Sóc Trăng', aliases: ['soc trang'],
    districts: ['Sóc Trăng', 'Ngã Năm', 'Vĩnh Châu', 'Châu Thành', 'Cù Lao Dung', 'Kế Sách', 'Long Phú', 'Mỹ Tú', 'Mỹ Xuyên', 'Thạnh Trị', 'Trần Đề'] },
  { name: 'Sơn La', aliases: ['son la', 'moc chau'],
    districts: ['Sơn La', 'Mộc Châu', 'Bắc Yên', 'Mai Sơn', 'Mường La', 'Phù Yên', 'Quỳnh Nhai', 'Sông Mã', 'Sốp Cộp', 'Thuận Châu', 'Vân Hồ', 'Yên Châu'] },
  { name: 'Tây Ninh', aliases: ['tay ninh'],
    districts: ['Tây Ninh', 'Hòa Thành', 'Trảng Bàng', 'Bến Cầu', 'Châu Thành', 'Dương Minh Châu', 'Gò Dầu', 'Tân Biên', 'Tân Châu'] },
  { name: 'Thái Bình', aliases: ['thai binh'],
    districts: ['Thái Bình', 'Đông Hưng', 'Hưng Hà', 'Kiến Xương', 'Quỳnh Phụ', 'Thái Thụy', 'Tiền Hải', 'Vũ Thư'] },
  { name: 'Thái Nguyên', aliases: ['thai nguyen', 'song cong'],
    districts: ['Thái Nguyên', 'Sông Công', 'Phổ Yên', 'Đại Từ', 'Định Hóa', 'Đồng Hỷ', 'Phú Bình', 'Phú Lương', 'Võ Nhai'] },
  { name: 'Thanh Hóa', aliases: ['thanh hoa', 'sam son'],
    districts: ['Thanh Hóa', 'Sầm Sơn', 'Bỉm Sơn', 'Nghi Sơn', 'Bá Thước', 'Cẩm Thủy', 'Đông Sơn', 'Hà Trung', 'Hậu Lộc', 'Hoằng Hóa', 'Lang Chánh', 'Mường Lát', 'Nga Sơn', 'Ngọc Lặc', 'Như Thanh', 'Như Xuân', 'Nông Cống', 'Quan Hóa', 'Quan Sơn', 'Quảng Xương', 'Thạch Thành', 'Thiệu Hóa', 'Thọ Xuân', 'Thường Xuân', 'Triệu Sơn', 'Vĩnh Lộc', 'Yên Định'] },
  { name: 'Thừa Thiên Huế', aliases: ['thua thien hue', 'hue'],
    districts: ['Huế', 'Hương Thủy', 'Hương Trà', 'A Lưới', 'Nam Đông', 'Phong Điền', 'Phú Lộc', 'Phú Vang', 'Quảng Điền'] },
  { name: 'Tiền Giang', aliases: ['tien giang', 'my tho'],
    districts: ['Mỹ Tho', 'Cai Lậy', 'Gò Công', 'Cái Bè', 'Châu Thành', 'Chợ Gạo', 'Gò Công Đông', 'Gò Công Tây', 'Tân Phú Đông', 'Tân Phước'] },
  { name: 'Trà Vinh', aliases: ['tra vinh'],
    districts: ['Trà Vinh', 'Duyên Hải', 'Càng Long', 'Cầu Kè', 'Cầu Ngang', 'Châu Thành', 'Tiểu Cần', 'Trà Cú'] },
  { name: 'Tuyên Quang', aliases: ['tuyen quang'],
    districts: ['Tuyên Quang', 'Chiêm Hóa', 'Hàm Yên', 'Lâm Bình', 'Na Hang', 'Sơn Dương', 'Yên Sơn'] },
  { name: 'Vĩnh Long', aliases: ['vinh long'],
    districts: ['Vĩnh Long', 'Bình Minh', 'Bình Tân', 'Long Hồ', 'Mang Thít', 'Tam Bình', 'Trà Ôn', 'Vũng Liêm'] },
  { name: 'Vĩnh Phúc', aliases: ['vinh phuc', 'vinh yen'],
    districts: ['Vĩnh Yên', 'Phúc Yên', 'Bình Xuyên', 'Lập Thạch', 'Sông Lô', 'Tam Đảo', 'Tam Dương', 'Vĩnh Tường', 'Yên Lạc'] },
  { name: 'Yên Bái', aliases: ['yen bai', 'nghia lo'],
    districts: ['Yên Bái', 'Nghĩa Lộ', 'Lục Yên', 'Mù Cang Chải', 'Trạm Tấu', 'Trấn Yên', 'Văn Chấn', 'Văn Yên', 'Yên Bình']}
];

function normalizeVnText_(s) {
  return String(s || '').toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd').replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ').trim();
}

function extractWardFromAddress(addr) {
  if (!addr || !String(addr).trim()) return null;
  const m = String(addr).match(/(?:phường|phuong|p\.|xã|xa|thị trấn|thi tran|tt\.)\s*([0-9a-zA-Z\u00C0-\u1EF9\s]+?)(?:,|$|\.|\/)/i);
  if (m && m[1]) {
    return m[0].replace(/[,.\/]+$/, '').trim();
  }
  return null;
}

function extractStreetFromAddress(addr, ward, dist, prov) {
  if (!addr || !String(addr).trim()) return '';
  const str = String(addr).trim();
  if (str.includes(',')) {
    const parts = str.split(',').map(s => s.trim()).filter(Boolean);
    let cutoffIdx = parts.length;
    for (let i = 0; i < parts.length; i++) {
      const p = parts[i].toLowerCase();
      if ((ward && p.includes(ward.toLowerCase())) ||
          (dist && p.includes(dist.toLowerCase())) ||
          (prov && p.includes(prov.toLowerCase())) ||
          /^(phường|phuong|p\.|xã|xa|thị trấn|thi tran|tt\.|quận|quan|q\.|huyện|huyen|tỉnh|tinh|tp\.)/i.test(p)) {
        cutoffIdx = i;
        break;
      }
    }
    if (cutoffIdx > 0) {
      return parts.slice(0, cutoffIdx).join(', ').trim();
    }
  }
  let remaining = str;
  if (prov) remaining = remaining.replace(new RegExp(prov, 'gi'), '');
  if (dist) remaining = remaining.replace(new RegExp(dist, 'gi'), '');
  if (ward) remaining = remaining.replace(new RegExp(ward, 'gi'), '');
  return remaining.replace(/^[,.\s\-/]+|[,.\s\-/]+$/g, '').trim();
}

function detectVietnamAddress(addr) {
  if (!addr || !String(addr).trim()) return { matchedProv: null, matchedDist: null, matchedWard: null, matchedStreet: '', isNoiTinh: false };
  const norm = ' ' + normalizeVnText_(addr) + ' ';
  let matchedProv = null;
  let matchedDist = null;

  for (const p of VN_ADMIN_DIVISIONS) {
    const pNorm = normalizeVnText_(p.name);
    if (norm.includes(' ' + pNorm + ' ') || (p.aliases && p.aliases.some(a => norm.includes(' ' + normalizeVnText_(a) + ' ')))) {
      matchedProv = p;
      break;
    }
  }

  if (matchedProv) {
    for (const d of matchedProv.districts) {
      const dNorm = normalizeVnText_(d).replace(/^(tp|quan|huyen|thanh pho|thi xa|tx)\s+/g, '');
      if (norm.includes(' ' + dNorm + ' ')) {
        matchedDist = d;
        break;
      }
    }
  } else {
    for (const p of VN_ADMIN_DIVISIONS) {
      for (const d of p.districts) {
        const dNorm = normalizeVnText_(d).replace(/^(tp|quan|huyen|thanh pho|thi xa|tx)\s+/g, '');
        if (norm.includes(' ' + dNorm + ' ')) {
          matchedProv = p;
          matchedDist = d;
          break;
        }
      }
      if (matchedProv) break;
    }
  }

  const provName = matchedProv ? matchedProv.name : null;
  const matchedWard = extractWardFromAddress(addr);
  const matchedStreet = extractStreetFromAddress(addr, matchedWard, matchedDist, provName);

  return {
    matchedProv: provName,
    matchedDist: matchedDist || null,
    matchedWard: matchedWard || null,
    matchedStreet: matchedStreet || '',
    isNoiTinh: Boolean(matchedProv && matchedProv.isNoiTinh)
  };
}

let _viettelAddrInited = false;
function initViettelAddressSelectors() {
  const provEl = document.getElementById('viettel-pkg-tinh');
  const distEl = document.getElementById('viettel-pkg-huyen');
  const wardEl = document.getElementById('viettel-pkg-xa');
  if (!provEl || !distEl) return;

  if (provEl.options.length <= 1) {
    provEl.innerHTML = '<option value="">-- Chọn Tỉnh / Thành phố --</option>' +
      VN_ADMIN_DIVISIONS.map(p => `<option value="${escapeHtml(p.name)}">${escapeHtml(p.name)}</option>`).join('');
  }

  const addrInput = document.getElementById('viettel-pkg-diachi');
  if (addrInput && !_viettelAddrInited) {
    _viettelAddrInited = true;
    let debounceTimer = null;
    addrInput.addEventListener('input', function() {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        onViettelAddressInput(this.value, false);
      }, 150);
    });
    addrInput.addEventListener('blur', function() {
      onViettelAddressInput(this.value, true);
    });
  }
}

window._viettelWardsCache = window._viettelWardsCache || {};

function fetchViettelWards(distName, selectWardName) {
  const wardEl = document.getElementById('viettel-pkg-xa');
  if (!wardEl) return;

  if (!distName) {
    wardEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>';
    return;
  }

  if (selectWardName) {
    let hasOption = Array.from(wardEl.options).some(o => o.value.toLowerCase() === selectWardName.toLowerCase());
    if (!hasOption) {
      const opt = document.createElement('option');
      opt.value = selectWardName;
      opt.textContent = selectWardName;
      opt.selected = true;
      wardEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>';
      wardEl.appendChild(opt);
    } else {
      wardEl.value = selectWardName;
    }
  }

  if (window._viettelWardsCache[distName]) {
    renderViettelWardOptions(wardEl, window._viettelWardsCache[distName], selectWardName);
    return;
  }

  const cleanDist = distName.replace(/^(Quận|Huyện|Thị xã|TP|Thành phố)\s+/i, '').trim();
  const searchUrl = `https://provinces.open-api.vn/api/v1/d/search/?q=${encodeURIComponent(cleanDist)}`;

  fetch(searchUrl)
    .then(r => r.json())
    .then(list => {
      if (!Array.isArray(list) || list.length === 0) return;
      const normD = normalizeVnText_(cleanDist);
      const matched = list.find(item => normalizeVnText_(item.name).includes(normD)) || list[0];
      if (!matched || !matched.code) return;

      return fetch(`https://provinces.open-api.vn/api/v1/d/${matched.code}?depth=2`)
        .then(r => r.json())
        .then(detail => {
          if (detail && Array.isArray(detail.wards)) {
            window._viettelWardsCache[distName] = detail.wards.map(w => w.name);
            renderViettelWardOptions(wardEl, window._viettelWardsCache[distName], selectWardName);
          }
        });
    })
    .catch(() => {});
}

function renderViettelWardOptions(selectEl, wardsList, selectWardName) {
  if (!selectEl || !Array.isArray(wardsList)) return;
  const currentVal = selectWardName || selectEl.value;
  selectEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>' +
    wardsList.map(w => `<option value="${escapeHtml(w)}">${escapeHtml(w)}</option>`).join('');

  if (currentVal) {
    const normCur = normalizeVnText_(currentVal).replace(/^(phuong|xa|thi tran|p|tt)\s+/g, '');
    const matched = wardsList.find(w => {
      const normW = normalizeVnText_(w).replace(/^(phuong|xa|thi tran|p|tt)\s+/g, '');
      return normW === normCur || w.toLowerCase() === currentVal.toLowerCase();
    });
    if (matched) {
      selectEl.value = matched;
    } else {
      const opt = document.createElement('option');
      opt.value = currentVal;
      opt.textContent = currentVal;
      opt.selected = true;
      selectEl.appendChild(opt);
    }
  }
}

function onViettelAddressInput(rawAddr, isBlur) {
  if (!rawAddr || !String(rawAddr).trim()) {
    const badge = document.getElementById('viettel-pkg-addr-detected');
    if (badge) badge.style.display = 'none';
    return;
  }
  const detected = detectVietnamAddress(rawAddr);
  const provEl = document.getElementById('viettel-pkg-tinh');
  const distEl = document.getElementById('viettel-pkg-huyen');
  const streetEl = document.getElementById('viettel-pkg-thonxom');
  const badge = document.getElementById('viettel-pkg-addr-detected');
  const badgeText = document.getElementById('viettel-pkg-addr-detected-text');

  if (detected.matchedProv && provEl) {
    provEl.value = detected.matchedProv;
    populateViettelDistricts(detected.matchedProv, detected.matchedDist);

    if (detected.matchedDist) {
      fetchViettelWards(detected.matchedDist, detected.matchedWard);
    }

    if (detected.matchedStreet && streetEl && (!streetEl.value || isBlur)) {
      streetEl.value = detected.matchedStreet;
    }

    if (badge && badgeText) {
      const locStr = [detected.matchedStreet, detected.matchedWard, detected.matchedDist, detected.matchedProv].filter(Boolean).join(', ');
      badgeText.textContent = `Tự động nhận diện: ${locStr}`;
      badge.style.display = 'inline-flex';
    }

    const dvEl = document.getElementById('viettel-pkg-dichvu');
    if (dvEl) {
      const cod = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value) || 0;
      if (detected.isNoiTinh) {
        dvEl.value = 'Nội tỉnh tiết kiệm';
        const dvctEl = document.getElementById('viettel-pkg-dvct');
        if (dvctEl) {
          let dvct = (dvctEl.value || '').replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
          if (!dvct) dvct = cod > 0 ? 'COD, PXD' : 'PXD';
          dvctEl.value = dvct;
        }
      } else {
        dvEl.value = cod > 0 ? 'TMĐT Tiết Kiệm thỏa thuận' : 'CP tiết kiệm thỏa thuận';
      }
    }
  } else {
    if (badge) badge.style.display = 'none';
  }
}

function populateViettelDistricts(provName, selectDistName) {
  const distEl = document.getElementById('viettel-pkg-huyen');
  const wardEl = document.getElementById('viettel-pkg-xa');
  if (!distEl) return;
  const prov = VN_ADMIN_DIVISIONS.find(p => p.name === provName);
  if (!prov) {
    distEl.innerHTML = '<option value="">-- Chọn Huyện / Quận --</option>';
    if (wardEl) wardEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>';
    return;
  }
  distEl.innerHTML = '<option value="">-- Chọn Huyện / Quận --</option>' +
    prov.districts.map(d => `<option value="${escapeHtml(d)}">${escapeHtml(d)}</option>`).join('');

  if (selectDistName) {
    distEl.value = selectDistName;
  }
}

function syncViettelAddressFromParts() {
  const street = document.getElementById('viettel-pkg-thonxom')?.value.trim() || '';
  const ward = document.getElementById('viettel-pkg-xa')?.value.trim() || '';
  const dist = document.getElementById('viettel-pkg-huyen')?.value.trim() || '';
  const prov = document.getElementById('viettel-pkg-tinh')?.value.trim() || '';
  const fullAddr = [street, ward, dist, prov].filter(Boolean).join(', ');
  const addrEl = document.getElementById('viettel-pkg-diachi');
  if (addrEl && fullAddr) {
    addrEl.value = fullAddr;
  }

  const badge = document.getElementById('viettel-pkg-addr-detected');
  const badgeText = document.getElementById('viettel-pkg-addr-detected-text');
  if (badge && badgeText) {
    const locParts = [ward, dist, prov].filter(Boolean);
    if (locParts.length > 0) {
      badgeText.textContent = `Đã chọn: ${locParts.join(', ')}`;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }
  }
}

function onViettelProvinceChange() {
  const provEl = document.getElementById('viettel-pkg-tinh');
  const provName = provEl ? provEl.value : '';
  populateViettelDistricts(provName);

  const wardEl = document.getElementById('viettel-pkg-xa');
  if (wardEl) wardEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>';

  const dvEl = document.getElementById('viettel-pkg-dichvu');
  if (dvEl) {
    const cod = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value) || 0;
    if (provName === 'Hà Nội') {
      dvEl.value = 'Nội tỉnh tiết kiệm';
      const dvctEl = document.getElementById('viettel-pkg-dvct');
      if (dvctEl) {
        let dvct = (dvctEl.value || '').replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
        if (!dvct) dvct = cod > 0 ? 'COD, PXD' : 'PXD';
        dvctEl.value = dvct;
      }
    } else if (provName) {
      dvEl.value = cod > 0 ? 'TMĐT Tiết Kiệm thỏa thuận' : 'CP tiết kiệm thỏa thuận';
    }
  }

  syncViettelAddressFromParts();
}

function onViettelDistrictChange() {
  const distEl = document.getElementById('viettel-pkg-huyen');
  const distName = distEl ? distEl.value : '';
  fetchViettelWards(distName, '');
  syncViettelAddressFromParts();
}

function onViettelWardChange() {
  syncViettelAddressFromParts();
}

function onViettelStreetChange() {
  syncViettelAddressFromParts();
}



// ══════════════════════════════════════════════════════
// PERSISTENT CUSTOMER ADDRESS BOOK & VIETTEL SERVICES
// ══════════════════════════════════════════════════════
function getViettelCustomerBook() {
  try {
    const raw = localStorage.getItem('VIETTEL_CUSTOMER_BOOK');
    return raw ? JSON.parse(raw) : {};
  } catch (e) {
    return {};
  }
}

function saveCustomerToViettelBook(cust) {
  if (!cust || (!cust.phone && !cust.name)) return;
  try {
    const book = getViettelCustomerBook();
    const normPhone = cust.phone ? normalizeCustomerPhone_(cust.phone) : '';
    const normName = cust.name ? normalizeVnText_(cust.name) : '';
    const entry = {
      name: cust.name || '',
      phone: cust.phone || '',
      address: cust.address || '',
      province: cust.province || '',
      district: cust.district || '',
      ward: cust.ward || cust.phuongXa || '',
      street: cust.street || cust.thonXom || '',
      updatedAt: Date.now()
    };
    if (normPhone) book['phone_' + normPhone] = entry;
    if (normName) book['name_' + normName] = entry;
    localStorage.setItem('VIETTEL_CUSTOMER_BOOK', JSON.stringify(book));
  } catch (e) {}
}

function lookupCustomerFromViettelBook(phone, name) {
  const book = getViettelCustomerBook();
  if (phone) {
    const normPhone = normalizeCustomerPhone_(phone);
    if (book['phone_' + normPhone] && (book['phone_' + normPhone].address || book['phone_' + normPhone].phone)) {
      return book['phone_' + normPhone];
    }
  }
  if (name) {
    const normName = normalizeVnText_(name);
    if (book['name_' + normName] && (book['name_' + normName].address || book['name_' + normName].phone)) {
      return book['name_' + normName];
    }
  }
  // Fallback to allRows in memory
  if (phone) {
    const normPhone = normalizeCustomerPhone_(phone);
    const r = (window.allRows || []).find(x => normalizeCustomerPhone_(x.sdtKhach) === normPhone && (x.diaChi || x.tenKhach));
    if (r) return { name: r.tenKhach, phone: r.sdtKhach, address: r.diaChi, province: r.tinhThanh || '', district: r.quanHuyen || '', ward: r.phuongXa || '', street: r.thonXom || '' };
  }
  if (name) {
    const normName = normalizeVnText_(name);
    const r = (window.allRows || []).find(x => normalizeVnText_(x.tenKhach) === normName && (x.diaChi || x.sdtKhach));
    if (r) return { name: r.tenKhach, phone: r.sdtKhach, address: r.diaChi, province: r.tinhThanh || '', district: r.quanHuyen || '', ward: r.phuongXa || '', street: r.thonXom || '' };
  }
  return null;
}

function onViettelServiceChange() {
  const dvEl = document.getElementById('viettel-pkg-dichvu');
  const dvctEl = document.getElementById('viettel-pkg-dvct');
  if (!dvEl || !dvctEl) return;
  const val = dvEl.value;
  const cod = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value) || 0;
  if (val === 'VTK' || val === 'CP tiết kiệm thỏa thuận') {
    let dvct = dvctEl.value.replace(/\bCOD,\s*/i, '').replace(/,\s*\bCOD\b/i, '').replace(/\bCOD\b/i, '').trim();
    if (!dvct || dvct === 'PXD') dvct = 'GKN, PXD';
    dvctEl.value = dvct;
  } else if (val === 'LCOD' || val === 'TMĐT Tiết Kiệm thỏa thuận' || val === 'NCOD') {
    if (!dvctEl.value.includes('COD')) {
      dvctEl.value = 'COD, PXD, GKN';
    }
  } else if (val === 'PHS' || val === 'Nội tỉnh tiết kiệm' || val.includes('Nội tỉnh')) {
    // Auto tắt SMS khi chọn nội tỉnh tiết kiệm
    let dvct = dvctEl.value.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
    if (!dvct) dvct = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
    dvctEl.value = dvct;
    showToast('Đã chọn Nội tỉnh tiết kiệm & tự động tắt SMS thông báo', 'info');
  }
}

function openViettelPackageModal(groupKey) {
  const packages = window._currentViettelPackages || [];
  const pkg = packages.find(p => p.key === groupKey);
  if (!pkg) {
    showToast('Không tìm thấy thông tin kiện hàng!', 'error');
    return;
  }

  initViettelAddressSelectors();
  // Auto-lookup address and phone from customer history if missing
  if (!pkg.sdtKhach || !pkg.diaChi) {
    const hist = lookupCustomerFromViettelBook(pkg.sdtKhach, pkg.tenKhach);
    if (hist) {
      if (!pkg.sdtKhach && hist.phone) pkg.sdtKhach = hist.phone;
      if (!pkg.diaChi && hist.address) pkg.diaChi = hist.address;
      if (!pkg.tinhThanh && hist.province) pkg.tinhThanh = hist.province;
      if (!pkg.quanHuyen && hist.district) pkg.quanHuyen = hist.district;
      if (!pkg.phuongXa && hist.ward) pkg.phuongXa = hist.ward;
      if (!pkg.thonXom && hist.street) pkg.thonXom = hist.street;
    }
  }

  document.getElementById('viettel-pkg-group-key').value = pkg.key;
  document.getElementById('viettel-pkg-tenkhach').value = pkg.tenKhach || '';
  document.getElementById('viettel-pkg-sdtkhach').value = pkg.sdtKhach || '';
  document.getElementById('viettel-pkg-diachi').value = pkg.diaChi || '';
  if (document.getElementById('viettel-pkg-thonxom')) {
    document.getElementById('viettel-pkg-thonxom').value = pkg.thonXom || '';
  }
  const isFreeshipPkg = isViettelFreeship_(pkg);
  document.getElementById('viettel-pkg-hinhthuc').value = isFreeshipPkg ? 'Freeship' : (pkg.hinhThuc || 'COD');
  document.getElementById('viettel-pkg-khoiluong').value = pkg.tongKhoiLuong || (pkg.items.length * 200);
  document.getElementById('viettel-pkg-giaban').value = pkg.tongGiaBan || 0;
  document.getElementById('viettel-pkg-khachcoc').value = pkg.tongKhachCoc || 0;
  document.getElementById('viettel-pkg-ghichu').value = pkg.ghiChu || 'Cho xem hàng không cho thử';

  const initialPkgCod = pkg.tongTienCOD !== undefined && pkg.tongTienCOD !== null 
    ? Number(pkg.tongTienCOD) 
    : (isFreeshipPkg ? 0 : (pkg.tongKhachCoc > 0 ? Math.max(0, (pkg.tongGiaBan || 0) - (pkg.tongKhachCoc || 0)) : 0));
  const pkgCodEl = document.getElementById('viettel-pkg-tiencod');
  if (pkgCodEl) pkgCodEl.value = initialPkgCod;

  if (document.getElementById('viettel-pkg-loaihang')) {
    document.getElementById('viettel-pkg-loaihang').value = pkg.loaiHangHoa || 'Bưu kiện';
  }
  if (document.getElementById('viettel-pkg-tinhchat')) {
    document.getElementById('viettel-pkg-tinhchat').value = pkg.tinhChatHangHoa || '';
  }

  let mappedDichVu = pkg.dichVu || '';
  if (mappedDichVu === 'NCOD' || mappedDichVu === 'TMĐT Tiết Kiệm thỏa thuận') mappedDichVu = 'LCOD';
  else if (mappedDichVu === 'CP tiết kiệm thỏa thuận') mappedDichVu = 'VTK';
  else if (mappedDichVu.startsWith('PHS') || mappedDichVu === 'Nội tỉnh tiết kiệm') mappedDichVu = 'PHS';
  else if (mappedDichVu === 'CP nhanh thỏa thuận') mappedDichVu = 'VCN';
  else if (mappedDichVu === 'Hỏa tốc thỏa thuận') mappedDichVu = 'VHT';

  const cod = Number(pkg.tongTienCOD) || 0;
  if (!mappedDichVu || mappedDichVu === 'LCOD' || mappedDichVu === 'VTK') {
    mappedDichVu = cod > 0 ? 'LCOD' : 'VTK';
  }
  if (document.getElementById('viettel-pkg-dichvu')) {
    document.getElementById('viettel-pkg-dichvu').value = mappedDichVu;
  }

  const dvctEl = document.getElementById('viettel-pkg-dvct');
  const dvctHint = document.getElementById('viettel-pkg-dvct-hint');
  if (dvctEl) {
    let dvctVal = pkg.dichVuCongThem;
    if (dvctVal === undefined || dvctVal === null || dvctVal === 'Khai giá' || !String(dvctVal).trim()) {
      dvctVal = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
    }
    if (mappedDichVu === 'PHS' || mappedDichVu === 'Nội tỉnh tiết kiệm' || mappedDichVu.includes('Nội tỉnh') || (pkg.diaChi && pkg.diaChi.includes('Hà Nội'))) {
      dvctVal = String(dvctVal).replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
      if (!dvctVal) dvctVal = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
    }
    dvctEl.value = dvctVal;
    if (dvctHint) {
      dvctHint.style.display = cod > 0 ? 'inline-flex' : 'none';
      if (cod > 0) dvctHint.innerHTML = '<i class="fas fa-check-circle"></i> Đơn có COD: Auto COD, PXD, GKN';
    }
  }

  if (pkg.diaChi) {
    onViettelAddressInput(pkg.diaChi, true);
    if (pkg.phuongXa && document.getElementById('viettel-pkg-xa')) {
      document.getElementById('viettel-pkg-xa').value = pkg.phuongXa;
    }
    if (pkg.thonXom && document.getElementById('viettel-pkg-thonxom')) {
      document.getElementById('viettel-pkg-thonxom').value = pkg.thonXom;
    }
  } else {
    const badge = document.getElementById('viettel-pkg-addr-detected');
    if (badge) badge.style.display = 'none';
    const provEl = document.getElementById('viettel-pkg-tinh');
    if (provEl) provEl.value = '';
    const distEl = document.getElementById('viettel-pkg-huyen');
    if (distEl) distEl.innerHTML = '<option value="">-- Chọn Huyện / Quận --</option>';
    const wardEl = document.getElementById('viettel-pkg-xa');
    if (wardEl) wardEl.innerHTML = '<option value="">-- Chọn Xã / Phường --</option>';
    const streetEl = document.getElementById('viettel-pkg-thonxom');
    if (streetEl) streetEl.value = '';
  }

  updateViettelPkgNoteActiveTag(pkg.ghiChu || 'Cho xem hàng không cho thử');
  calcViettelPkgCOD();

  const countBadge = document.getElementById('viettel-pkg-item-count');
  if (countBadge) countBadge.textContent = `${pkg.items.length} sản phẩm gộp`;

  const chipsContainer = document.getElementById('viettel-pkg-items-chips');
  if (chipsContainer) {
    chipsContainer.innerHTML = pkg.items.map(it => {
      return `<div style="display:inline-flex; align-items:center; gap:6px; background:var(--bg-card); border:1px solid var(--border); padding:4px 10px; border-radius:6px; font-size:0.82rem;">
        <strong style="color:var(--primary-light);">${escapeHtml(it.maSP || 'Chưa có mã')}</strong>
        <span style="color:var(--text-muted);">${fmtVnd(it.giaBan || 0)}</span>
      </div>`;
    }).join('');
  }

  openModal('modal-viettel-package');
  setTimeout(() => {
    if (!pkg.sdtKhach) document.getElementById('viettel-pkg-sdtkhach')?.focus();
    else if (!pkg.diaChi) document.getElementById('viettel-pkg-diachi')?.focus();
  }, 150);
}

function onViettelPkgCodInput() {
  const codInput = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value) || 0;
  const htEl = document.getElementById('viettel-pkg-hinhthuc');
  if (htEl) {
    htEl.value = codInput > 0 ? 'COD' : 'Freeship';
  }
  const dvEl = document.getElementById('viettel-pkg-dichvu');
  const dvctEl = document.getElementById('viettel-pkg-dvct');
  const dvctHint = document.getElementById('viettel-pkg-dvct-hint');
  if (dvEl) {
    if (codInput > 0) {
      if (!dvEl.value || dvEl.value === 'VTK' || dvEl.value === 'CP tiết kiệm thỏa thuận') {
        dvEl.value = 'LCOD';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'PXD' || dvctEl.value === 'GKN, PXD' || dvctEl.value === 'COD, PXD')) {
        dvctEl.value = 'COD, PXD, GKN';
      }
      if (dvctHint) {
        dvctHint.style.display = 'inline-flex';
        dvctHint.innerHTML = '<i class="fas fa-check-circle"></i> Đơn có COD: Auto COD, PXD, GKN';
      }
    } else {
      if (!dvEl.value || dvEl.value === 'LCOD' || dvEl.value === 'TMĐT Tiết Kiệm thỏa thuận' || dvEl.value === 'NCOD') {
        dvEl.value = 'VTK';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'COD, PXD' || dvctEl.value === 'COD, PXD, GKN' || dvctEl.value === 'PXD')) {
        dvctEl.value = 'GKN, PXD';
      }
      if (dvctHint) dvctHint.style.display = 'none';
    }
    if (dvEl.value === 'PHS' || dvEl.value === 'Nội tỉnh tiết kiệm' || dvEl.value.includes('Nội tỉnh')) {
      if (dvctEl) {
        dvctEl.value = dvctEl.value.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
        if (!dvctEl.value) dvctEl.value = codInput > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
      }
    }
  }
}

function calcViettelPkgCOD() {
  const giaBan = parseFloat(document.getElementById('viettel-pkg-giaban')?.value) || 0;
  const hinhThuc = document.getElementById('viettel-pkg-hinhthuc')?.value || 'COD';
  const khachCoc = parseFloat(document.getElementById('viettel-pkg-khachcoc')?.value) || 0;
  let cod = 0;
  if (hinhThuc === 'COD') {
    if (khachCoc > 0 && khachCoc >= giaBan) {
      cod = 0;
      const htEl = document.getElementById('viettel-pkg-hinhthuc');
      if (htEl && giaBan > 500000) htEl.value = 'Freeship';
    } else if (khachCoc > 0) {
      cod = Math.max(0, giaBan - khachCoc);
    } else {
      const curCod = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value);
      cod = !isNaN(curCod) ? curCod : 0;
    }
  } else {
    cod = 0;
  }
  const codEl = document.getElementById('viettel-pkg-tiencod');
  if (codEl) codEl.value = cod;

  const dvEl = document.getElementById('viettel-pkg-dichvu');
  const dvctEl = document.getElementById('viettel-pkg-dvct');
  const dvctHint = document.getElementById('viettel-pkg-dvct-hint');
  if (dvEl) {
    if (cod > 0) {
      if (!dvEl.value || dvEl.value === 'VTK' || dvEl.value === 'CP tiết kiệm thỏa thuận') {
        dvEl.value = 'LCOD';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'PXD' || dvctEl.value === 'GKN, PXD' || dvctEl.value === 'COD, PXD')) {
        dvctEl.value = 'COD, PXD, GKN';
      }
      if (dvctHint) {
        dvctHint.style.display = 'inline-flex';
        dvctHint.innerHTML = '<i class="fas fa-check-circle"></i> Đơn có COD: Auto COD, PXD, GKN';
      }
    } else {
      if (!dvEl.value || dvEl.value === 'LCOD' || dvEl.value === 'TMĐT Tiết Kiệm thỏa thuận' || dvEl.value === 'NCOD') {
        dvEl.value = 'VTK';
      }
      if (dvctEl && (!dvctEl.value || dvctEl.value === 'COD, PXD' || dvctEl.value === 'COD, PXD, GKN' || dvctEl.value === 'PXD')) {
        dvctEl.value = 'GKN, PXD';
      }
      if (dvctHint) dvctHint.style.display = 'none';
    }
    if (dvEl.value === 'PHS' || dvEl.value === 'Nội tỉnh tiết kiệm' || dvEl.value.includes('Nội tỉnh')) {
      if (dvctEl) {
        dvctEl.value = dvctEl.value.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
        if (!dvctEl.value) dvctEl.value = cod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
      }
    }
  }
}

function setViettelPkgNote(noteText) {
  const input = document.getElementById('viettel-pkg-ghichu');
  if (input) input.value = noteText;
  updateViettelPkgNoteActiveTag(noteText);
}

function updateViettelPkgNoteActiveTag(noteText) {
  const tags = document.querySelectorAll('#modal-viettel-package .qnote-tag');
  tags.forEach(tag => {
    if (tag.textContent.trim() === String(noteText || '').trim()) {
      tag.classList.add('active');
    } else {
      tag.classList.remove('active');
    }
  });
}

function saveViettelPackage() {
  const groupKey = document.getElementById('viettel-pkg-group-key').value;
  const packages = window._currentViettelPackages || [];
  const pkg = packages.find(p => p.key === groupKey);
  if (!pkg) {
    showToast('Không tìm thấy kiện hàng!', 'error');
    return;
  }

  const tenKhach = document.getElementById('viettel-pkg-tenkhach').value.trim();
  const sdtKhach = document.getElementById('viettel-pkg-sdtkhach').value.trim();
  let diaChi = document.getElementById('viettel-pkg-diachi').value.trim();
  const tinhThanh = document.getElementById('viettel-pkg-tinh')?.value || '';
  const quanHuyen = document.getElementById('viettel-pkg-huyen')?.value || '';
  const phuongXa = document.getElementById('viettel-pkg-xa')?.value || '';
  const thonXom = document.getElementById('viettel-pkg-thonxom')?.value.trim() || '';
  const hinhThuc = document.getElementById('viettel-pkg-hinhthuc').value;
  const khoiLuong = parseInt(document.getElementById('viettel-pkg-khoiluong').value) || (pkg.items.length * 200);
  const khachCoc = parseFloat(document.getElementById('viettel-pkg-khachcoc').value) || 0;
  const ghiChu = document.getElementById('viettel-pkg-ghichu').value.trim() || 'Cho xem hàng không cho thử';
  const loaiHangHoa = document.getElementById('viettel-pkg-loaihang')?.value || 'Bưu kiện';
  const tinhChatHangHoa = document.getElementById('viettel-pkg-tinhchat')?.value || '';

  // Calculate final COD
  let finalCod = 0;
  const rawCodInput = parseFloat(document.getElementById('viettel-pkg-tiencod')?.value);
  if (hinhThuc === 'COD') {
    if (!isNaN(rawCodInput)) {
      finalCod = Math.max(0, rawCodInput);
    } else if (khachCoc > 0 && khachCoc < (pkg.tongGiaBan || 0)) {
      finalCod = Math.max(0, (pkg.tongGiaBan || 0) - khachCoc);
    } else {
      finalCod = 0;
    }
  } else {
    finalCod = 0;
  }
  if (khachCoc > 0 && (pkg.tongGiaBan || 0) > 0 && khachCoc >= (pkg.tongGiaBan || 0)) {
    finalCod = 0;
  }

  let dichVu = document.getElementById('viettel-pkg-dichvu')?.value || (finalCod > 0 ? 'LCOD' : 'VTK');
  let dichVuCongThem = (document.getElementById('viettel-pkg-dvct')?.value || '').trim() || (finalCod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD');
  if (dichVu === 'PHS' || dichVu === 'Nội tỉnh tiết kiệm' || dichVu.includes('Nội tỉnh')) {
    dichVuCongThem = dichVuCongThem.replace(/\bSMS\b[^\,]*\,?/gi, '').replace(/,\s*,/g, ',').replace(/^[\s,]+|[\s,]+$/g, '').trim();
    if (!dichVuCongThem) dichVuCongThem = finalCod > 0 ? 'COD, PXD, GKN' : 'GKN, PXD';
  }

  // UPDATE PKG DIRECTLY IN MEMORY
  pkg.tenKhach = tenKhach;
  pkg.sdtKhach = sdtKhach;
  pkg.diaChi = diaChi;
  pkg.tinhThanh = tinhThanh;
  pkg.quanHuyen = quanHuyen;
  pkg.phuongXa = phuongXa;
  pkg.thonXom = thonXom;
  pkg.hinhThuc = hinhThuc;
  pkg.tongKhoiLuong = khoiLuong;
  pkg.tongKhachCoc = khachCoc;
  pkg.tongTienCOD = finalCod;
  pkg.loaiHangHoa = loaiHangHoa;
  pkg.tinhChatHangHoa = tinhChatHangHoa;
  pkg.dichVu = dichVu;
  pkg.dichVuCongThem = dichVuCongThem;
  pkg.ghiChu = ghiChu;
  pkg.nguoiTraCuoc = getViettelPayer_(pkg);

  const structuredParts = [thonXom, phuongXa, quanHuyen, tinhThanh].filter(Boolean);
  if (structuredParts.length >= 2 && (!diaChi || !diaChi.toLowerCase().includes((tinhThanh || '').toLowerCase()))) {
    diaChi = structuredParts.join(', ');
    document.getElementById('viettel-pkg-diachi').value = diaChi;
  }

  // Persist customer address & phone into permanent local storage book
  saveCustomerToViettelBook({
    name: tenKhach,
    phone: sdtKhach,
    address: diaChi,
    province: tinhThanh,
    district: quanHuyen,
    ward: phuongXa,
    street: thonXom
  });

  if (tinhThanh && !diaChi.toLowerCase().includes(tinhThanh.toLowerCase())) {
    const parts = [diaChi];
    if (quanHuyen && !diaChi.toLowerCase().includes(quanHuyen.toLowerCase())) {
      parts.push(quanHuyen);
    }
    parts.push(tinhThanh);
    diaChi = parts.filter(Boolean).join(', ');
    document.getElementById('viettel-pkg-diachi').value = diaChi;
  }

  if (!tenKhach) {
    showToast('Vui lòng nhập Tên người nhận!', 'warning');
    document.getElementById('viettel-pkg-tenkhach')?.focus();
    return;
  }
  if (!/^[0-9+\-\s().]{8,20}$/.test(sdtKhach)) {
    showToast('Số điện thoại không hợp lệ!', 'warning');
    document.getElementById('viettel-pkg-sdtkhach')?.focus();
    return;
  }
  if (!diaChi) {
    showToast('Vui lòng nhập Địa chỉ nhận hàng (Bắt buộc để Viettel Post in bill)!', 'warning');
    document.getElementById('viettel-pkg-diachi')?.focus();
    return;
  }

  const btn = document.getElementById('btn-save-viettel-pkg');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu kiện hàng...';
  }

  const itemWeight = Math.round(khoiLuong / Math.max(1, pkg.items.length));
  const itemDeposit = Math.round(khachCoc / Math.max(1, pkg.items.length));
  const itemCod = pkg.items.length === 1 ? finalCod : Math.round(finalCod / pkg.items.length);

  pkg.items.forEach(it => {
    it.tenKhach = tenKhach;
    it.sdtKhach = sdtKhach;
    it.diaChi = diaChi;
    it.tinhThanh = tinhThanh;
    it.quanHuyen = quanHuyen;
    it.phuongXa = phuongXa;
    it.thonXom = thonXom;
    it.hinhThuc = hinhThuc;
    it.ghiChu = ghiChu;
    it.khoiLuong = itemWeight;
    it.khachCoc = itemDeposit;
    it.tienCOD = itemCod;
    it.loaiHangHoa = loaiHangHoa;
    it.tinhChatHangHoa = tinhChatHangHoa;
    it.dichVu = dichVu;
    it.dichVuCongThem = dichVuCongThem;

    const rowSheet = getRowSheetName_(it);
    const syncInList = (list) => {
      if (!Array.isArray(list)) return;
      const idx = list.findIndex(r => Number(r.rowIndex) === Number(it.rowIndex) && getRowSheetName_(r) === rowSheet);
      if (idx !== -1) {
        list[idx] = Object.assign({}, list[idx], {
          tenKhach, sdtKhach, diaChi, tinhThanh, quanHuyen, phuongXa, thonXom,
          hinhThuc, ghiChu, khoiLuong: itemWeight, khachCoc: itemDeposit, tienCOD: itemCod,
          loaiHangHoa, tinhChatHangHoa, dichVu, dichVuCongThem
        });
      }
    };
    syncInList(window.allRows);
    syncInList(window.allReportRows);
    if (window.crmSnapshot && window.crmSnapshot.dailyRows) syncInList(window.crmSnapshot.dailyRows);
    if (window.crmSnapshot && window.crmSnapshot.reportRows) syncInList(window.crmSnapshot.reportRows);

    const updatePayload = {
      maSP: it.maSP,
      giaBan: it.giaBan,
      giaVon: it.giaVon || 0,
      tenKhach,
      sdtKhach,
      diaChi,
      tinhThanh,
      quanHuyen,
      phuongXa,
      thonXom,
      hinhThuc,
      khoiLuong: itemWeight,
      khachCoc: itemDeposit,
      tienCOD: itemCod,
      loaiHangHoa,
      tinhChatHangHoa,
      dichVu,
      dichVuCongThem,
      ghiChu,
      ngayChot: it.ngayChot || getTodayString_(),
      trangThai: it.trangThai || 'Đã bán'
    };

    if (typeof google !== 'undefined' && google.script && google.script.run) {
      google.script.run.updateRow(Number(it.rowIndex), updatePayload, rowSheet);
    } else {
      // Vercel / standalone mode
      fetch('/api/update-row', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rowIndex: Number(it.rowIndex), sheetName: rowSheet, rowData: updatePayload })
      }).catch(e => console.error('Error saving row:', e));
    }
  });

  if (btn) {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check"></i> Lưu thông tin kiện hàng';
  }

  closeModal('modal-viettel-package');
  showToast(`Đã lưu kiện hàng cho ${tenKhach} (${pkg.items.length} SP)!`, 'success');
  renderViettelOrders(packages, getViettelDateRange());
}

// ══════════════════════════════════════════════════════════
// XUẤT EXCEL CHUẨN VIETTELPOST TỪ QUẢN LÝ SẢN PHẨM & ĐƠN NGÀY
// ══════════════════════════════════════════════════════════

function exportViettelPostFromProducts() {
  const rows = (typeof filteredRows !== 'undefined' && Array.isArray(filteredRows) && filteredRows.length > 0)
    ? filteredRows
    : (window.allRows || []);
  if (!rows || !rows.length) {
    showToast('Không có dữ liệu sản phẩm để xuất!', 'warning');
    return;
  }

  const orders = rows.filter(r => {
    const hasCustomer = (r.tenKhach && String(r.tenKhach).trim()) || (r.sdtKhach && String(r.sdtKhach).trim());
    return hasCustomer && r.trangThai !== 'Đã xóa';
  });

  if (!orders.length) {
    showToast('Không tìm thấy đơn hàng nào có thông tin khách hàng (Tên/SĐT) trong danh sách đang lọc!', 'warning');
    return;
  }

  const packages = (typeof groupOrdersByCustomer_ === 'function')
    ? groupOrdersByCustomer_(orders)
    : orders.map((o, i) => ({
        key: 'pkg_' + i,
        tenKhach: o.tenKhach || '',
        sdtKhach: o.sdtKhach || '',
        diaChi: o.diaChi || '',
        maSPList: [o.maSP || ''],
        tongGiaBan: Number(o.giaBan) || 0,
        tongTienCOD: Number(o.tienCOD) || 0,
        tongKhachCoc: Number(o.khachCoc) || 0,
        tongKhoiLuong: Number(o.khoiLuong) || 300,
        items: [o]
      }));

  if (!packages || !packages.length) {
    showToast('Không tạo được kiện hàng hợp lệ!', 'warning');
    return;
  }

  const missingAddress = packages.filter(p => !p.diaChi || !String(p.diaChi).trim());
  if (missingAddress.length > 0) {
    const listNames = missingAddress.slice(0, 5).map(p => `${p.tenKhach || 'Khách'} (${(p.maSPList || []).join('+')})`).join(', ') + (missingAddress.length > 5 ? '...' : '');
    if (!confirm(`Cảnh báo: Có ${missingAddress.length} kiện hàng chưa có Địa chỉ nhận hàng (${listNames})!\nViettel Post sẽ từ chối tạo đơn nếu thiếu địa chỉ.\n\nBạn có muốn tiếp tục xuất file Excel không?`)) {
      return;
    }
  }

  generateViettelExcelFile(packages, 'ViettelPost_SanPham');
  showToast(`Đã xuất ${packages.length} kiện hàng Viettel Post từ ${orders.length} sản phẩm!`, 'success');
}

function exportViettelPostFromDaily() {
  const range = (typeof getDailyDateRange === 'function')
    ? getDailyDateRange()
    : { start: (typeof getTodayString_ === 'function' ? getTodayString_() : new Date().toISOString().slice(0, 10)), end: (typeof getTodayString_ === 'function' ? getTodayString_() : new Date().toISOString().slice(0, 10)) };

  let orders = [];
  if (window.crmSnapshot?.dailyRows && window.crmSnapshot.dailyRows.length > 0) {
    orders = window.crmSnapshot.dailyRows;
  } else if (window.allReportRows && window.allReportRows.length > 0) {
    orders = window.allReportRows;
  } else if (window.allRows && window.allRows.length > 0) {
    orders = window.allRows;
  }

  if (typeof filterDailyOrders === 'function') {
    orders = filterDailyOrders(orders, range);
  }

  if (!orders || !orders.length) {
    showToast(`Không có đơn hàng nào trong khoảng ngày ${range.start || ''} đến ${range.end || ''}!`, 'warning');
    return;
  }

  const validOrders = orders.filter(r => r.trangThai !== 'Đã xóa' && ((r.tenKhach && String(r.tenKhach).trim()) || (r.sdtKhach && String(r.sdtKhach).trim())));
  if (!validOrders.length) {
    showToast('Không có đơn hàng nào có thông tin người nhận để gửi Viettel Post!', 'warning');
    return;
  }

  const packages = (typeof groupOrdersByCustomer_ === 'function')
    ? groupOrdersByCustomer_(validOrders)
    : validOrders.map((o, i) => ({
        key: 'pkg_' + i,
        tenKhach: o.tenKhach || '',
        sdtKhach: o.sdtKhach || '',
        diaChi: o.diaChi || '',
        maSPList: [o.maSP || ''],
        tongGiaBan: Number(o.giaBan) || 0,
        tongTienCOD: Number(o.tienCOD) || 0,
        tongKhachCoc: Number(o.khachCoc) || 0,
        tongKhoiLuong: Number(o.khoiLuong) || 300,
        items: [o]
      }));

  const missingAddress = packages.filter(p => !p.diaChi || !String(p.diaChi).trim());
  if (missingAddress.length > 0) {
    const listNames = missingAddress.slice(0, 5).map(p => `${p.tenKhach || 'Khách'} (${(p.maSPList || []).join('+')})`).join(', ') + (missingAddress.length > 5 ? '...' : '');
    if (!confirm(`Cảnh báo: Có ${missingAddress.length} kiện hàng chưa có Địa chỉ nhận hàng (${listNames})!\nViettel Post sẽ từ chối tạo đơn nếu thiếu địa chỉ.\n\nBạn có muốn tiếp tục xuất file Excel không?`)) {
      return;
    }
  }

  generateViettelExcelFile(packages, `ViettelPost_DonNgay_${range.start || 'today'}`);
  showToast(`Đã xuất ${packages.length} kiện hàng Viettel Post từ ${validOrders.length} đơn hàng!`, 'success');
}

function exportViettelGroupedExcel() {
  const packages = window._currentViettelPackages || [];
  if (packages.length === 0) {
    showToast('Không có kiện hàng nào để xuất!', 'warning');
    return;
  }

  const missingAddress = packages.filter(p => !p.diaChi || !String(p.diaChi).trim());
  if (missingAddress.length > 0) {
    const listNames = missingAddress.slice(0, 5).map(p => `${p.tenKhach} (${p.maSPList.join('+')})`).join(', ') + (missingAddress.length > 5 ? '...' : '');
    if (!confirm(`Cảnh báo: Có ${missingAddress.length} kiện hàng chưa có Địa chỉ nhận hàng (${listNames})!\nViettel Post sẽ từ chối in đơn nếu thiếu địa chỉ.\n\nBạn có chắc chắn vẫn muốn xuất file Excel không?`)) {
      return;
    }
  }

  generateViettelExcelFile(packages, 'ViettelPost_GopDon');
}

function exportSingleViettelPackage(groupKey) {
  const packages = window._currentViettelPackages || [];
  const pkg = packages.find(p => p.key === groupKey);
  if (!pkg) {
    showToast('Không tìm thấy kiện hàng!', 'error');
    return;
  }
  if (!pkg.diaChi) {
    if (!confirm(`Kiện hàng của [${pkg.tenKhach}] chưa có Địa chỉ nhận hàng! Bạn có chắc vẫn muốn xuất không?`)) {
      return;
    }
  }
  generateViettelExcelFile([pkg], `ViettelPost_${pkg.tenKhach.replace(/[^a-zA-Z0-9]/g, '_')}`);
}

function formatViettelPhone_(phone) {
  let p = String(phone || '').trim().replace(/[\s().-]/g, '');
  if (p.startsWith('+84')) {
    p = '0' + p.slice(3);
  } else if (p.startsWith('84') && p.length >= 11) {
    p = '0' + p.slice(2);
  } else if (!p.startsWith('0') && p.length === 9) {
    p = '0' + p;
  }
  return p;
}

function generateViettelExcelFile(packages, filePrefix) {
  showLoading('Đang chuẩn bị file Excel Viettel Post...');
  loadScript("https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js", () => {
    try {
      const headers = [
        'STT',
        'Mã đơn hàng ',
        'Tên người nhận (*)',
        'Số ĐT người nhận (*)',
        'Địa chỉ nhận (*)',
        'Tên hàng hóa (*)',
        'Số lượng',
        'Trọng lượng (gram)  (*)',
        'Giá trị hàng (VND) (*)',
        'Tiền thu hộ COD (VND)',
        'Loại hàng hóa (*)',
        'Tính chất hàng hóa đặc biệt',
        'Dịch vụ  (*)',
        'Dịch vụ cộng thêm ',
        'Thu tiền xem hàng',
        'Dài (cm)',
        'Rộng (cm)',
        'Cao (cm)',
        'Người trả cước',
        'Yêu cầu khác',
        'Thời gian hẹn lấy',
        'Thời gian giao'
      ];

      const dataRows = packages.map((pkg, idx) => {
        const isFreeship = isViettelFreeship_(pkg);
        const giaTriHangRaw = Number(pkg.tongGiaBan || 0);
        const khachCoc = Number(pkg.tongKhachCoc || 0);
        let codAmount = 0;
        if (pkg.tongTienCOD !== undefined && pkg.tongTienCOD !== null && pkg.tongTienCOD !== '') {
          codAmount = Math.max(0, Number(pkg.tongTienCOD));
        } else if (khachCoc > 0 && khachCoc >= giaTriHangRaw) {
          codAmount = 0;
        } else if (khachCoc > 0 && khachCoc < giaTriHangRaw) {
          codAmount = Math.max(0, giaTriHangRaw - khachCoc);
        } else {
          codAmount = 0;
        }
        if (codAmount <= 0) codAmount = 0;

        // Đảm bảo Cột I Giá trị hàng (*) luôn > 0 để tránh Viettel Post chặn lỗi thiếu trường bắt buộc
        const giaTriHang = giaTriHangRaw > 0 ? giaTriHangRaw : (codAmount > 0 ? codAmount : 100000);

        // Quy tắc Viettel Post:
        // khi chọn 0 thì dịch vụ sẽ ăn là VTK và dịch vụ cộng thêm là GKN, PXD
        // còn khi thu hộ thì dịch vụ sẽ là LCOD và dịch vụ cộng thêm sẽ là COD,PXD,GKN
        const svcInfo = getViettelServiceAndDvct_({
          hinhThuc: codAmount > 0 ? 'COD' : (isFreeship ? 'Freeship' : 'Chịu ship'),
          tongGiaBan: giaTriHangRaw,
          tongKhachCoc: khachCoc,
          tongTienCOD: codAmount,
          dichVu: pkg.dichVu,
          dichVuCongThem: pkg.dichVuCongThem
        });
        const dichVu = svcInfo.dichVu;
        const dvct = svcInfo.dvct;

        // Quy tắc Người trả cước:
        // nếu đơn > 500k và khách đã ck đủ thì chỗ người trả cước là Người gửi
        // còn cod cứ auto là Người nhận trả cước
        // chỉ có anh Giau Ba Le thì auto Người gửi trả cước
        const payer = getViettelPayer_({
          tenKhach: pkg.tenKhach,
          hinhThuc: codAmount > 0 ? 'COD' : (isFreeship ? 'Freeship' : 'Chịu ship'),
          tongGiaBan: giaTriHangRaw,
          tongKhachCoc: khachCoc,
          tongTienCOD: codAmount
        });

        let orderCode = pkg.maSPList.join('+') || `VS_${idx + 1}`;
        if (orderCode.length > 40) orderCode = orderCode.slice(0, 40);
        const productName = `Phụ kiện kèm ${pkg.maSPList.join('+') || 'hàng hóa'}`;
        const loaiHang = pkg.loaiHangHoa || 'Bưu kiện';
        const tinhChat = pkg.tinhChatHangHoa || '';
        const cleanPhone = formatViettelPhone_(pkg.sdtKhach);

        let finalAddr = String(pkg.diaChi || '').trim();
        const thonXom = pkg.thonXom || '';
        const phuongXa = pkg.phuongXa || '';
        const quanHuyen = pkg.quanHuyen || '';
        const tinhThanh = pkg.tinhThanh || '';

        if (tinhThanh && !finalAddr.toLowerCase().includes(tinhThanh.toLowerCase())) {
          const parts = [finalAddr];
          if (phuongXa && !finalAddr.toLowerCase().includes(phuongXa.toLowerCase())) {
            parts.push(phuongXa);
          }
          if (quanHuyen && !finalAddr.toLowerCase().includes(quanHuyen.toLowerCase())) {
            parts.push(quanHuyen);
          }
          parts.push(tinhThanh);
          finalAddr = parts.filter(Boolean).join(', ');
        } else if (!finalAddr && (thonXom || phuongXa || quanHuyen || tinhThanh)) {
          finalAddr = [thonXom, phuongXa, quanHuyen, tinhThanh].filter(Boolean).join(', ');
        }

        const packageWeight = (pkg.tongKhoiLuong && Number(pkg.tongKhoiLuong) > 0) ? Number(pkg.tongKhoiLuong) : 300;
        const finalNote = (pkg.ghiChu && String(pkg.ghiChu).trim() && pkg.ghiChu !== 'CHO HÀNG XEM')
          ? ('Cho xem hàng không cho thử - ' + String(pkg.ghiChu).trim())
          : 'Cho xem hàng không cho thử';

        return [
          idx + 1,                                       // STT (Cột A)
          orderCode,                                     // Mã đơn hàng (Cột B)
          pkg.tenKhach || '',                            // Tên người nhận (*) (Cột C)
          cleanPhone,                                    // Số ĐT người nhận (*) (Cột D)
          finalAddr,                                     // Địa chỉ nhận (*) (Cột E)
          productName,                                   // Tên hàng hóa (*) (Cột F)
          1,                                             // Số lượng (Cột G)
          packageWeight,                                 // Trọng lượng (gram) (*) (Cột H) - Mặc định 300g
          giaTriHang,                                    // Giá trị hàng (VND) (*) (Cột I) - Luôn > 0
          codAmount,                                     // Tiền thu hộ COD (VND) (Cột J)
          loaiHang,                                      // Loại hàng hóa (*) (Cột K)
          tinhChat,                                      // Tính chất hàng hóa đặc biệt (Cột L)
          dichVu,                                        // Dịch vụ (*) (Cột M)
          dvct,                                          // Dịch vụ cộng thêm (Cột N)
          '',                                            // Thu tiền xem hàng (Cột O)
          1,                                             // Dài (cm) (Cột P)
          1,                                             // Rộng (cm) (Cột Q)
          1,                                             // Cao (cm) (Cột R)
          payer,                                         // Người trả cước (Cột S)
          finalNote,                                     // Yêu cầu khác (Cột T) - Luôn có Cho xem hàng
          '',                                            // Thời gian hẹn lấy (Cột U)
          'Cả ngày'                                      // Thời gian giao (Cột V)
        ];
      });

      const sheetData = [
        [],
        ['', 'TẬP ĐOÀN CÔNG NGHIỆP - VIỄN THÔNG QUÂN ĐỘI'],
        ['', 'TỔNG CÔNG TY CỔ PHẦN BƯU CHÍNH VIETTEL'],
        [],
        ['', '', '', '', 'DANH SÁCH ĐƠN HÀNG'],
        ['(*) là các trường bắt buộc nhập'],
        headers,
        ...dataRows
      ];

      const ws = XLSX.utils.aoa_to_sheet(sheetData);

      // CRITICAL FOR VIETTEL POST: Force Column D (Phone) to Text type '@' to prevent loss of leading 0
      for (let r = 7; r < 7 + dataRows.length; r++) {
        const phoneCellRef = XLSX.utils.encode_cell({ r: r, c: 3 }); // Column D
        if (ws[phoneCellRef]) {
          ws[phoneCellRef].t = 's'; // Force String type
          ws[phoneCellRef].z = '@'; // Force Text format
        }
        const priceCellRef = XLSX.utils.encode_cell({ r: r, c: 8 }); // Column I
        if (ws[priceCellRef]) {
          ws[priceCellRef].t = 'n';
          ws[priceCellRef].z = '#,##0';
        }
        const codCellRef = XLSX.utils.encode_cell({ r: r, c: 9 }); // Column J
        if (ws[codCellRef]) {
          ws[codCellRef].t = 'n';
          ws[codCellRef].z = '#,##0';
        }
      }

      ws['!cols'] = [
        { wch: 6 },  // STT
        { wch: 18 }, // Mã đơn hàng
        { wch: 22 }, // Tên người nhận
        { wch: 15 }, // Số ĐT
        { wch: 45 }, // Địa chỉ nhận (rộng rãi để xem đủ 4 cấp)
        { wch: 25 }, // Tên hàng hóa
        { wch: 8 },  // Số lượng
        { wch: 12 }, // Trọng lượng
        { wch: 14 }, // Giá trị hàng
        { wch: 14 }, // Tiền thu hộ COD
        { wch: 12 }, // Loại hàng
        { wch: 12 }, // Tính chất
        { wch: 28 }, // Dịch vụ
        { wch: 18 }, // DV cộng thêm
        { wch: 12 }, // Thu tiền cước
        { wch: 8 },  // Dài
        { wch: 8 },  // Rộng
        { wch: 8 },  // Cao
        { wch: 15 }, // Người trả cước
        { wch: 25 }, // Yêu cầu khác
        { wch: 20 }, // Hẹn lấy
        { wch: 15 }  // Hẹn giao
      ];
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "DANH SÁCH ĐƠN HÀNG");

      const dateRange = getViettelDateRange();
      const dateSuffix = dateRange.start && dateRange.end ? `${dateRange.start}_to_${dateRange.end}` : new Date().toISOString().slice(0, 10);

      XLSX.writeFile(wb, `${filePrefix}_${dateSuffix}.xlsx`);
      hideLoading();
      showToast(`Xuất ${packages.length} kiện hàng Viettel Post thành công!`, 'success');
    } catch (e) {
      hideLoading();
      showToast('Lỗi xuất Excel Viettel Post: ' + e.message, 'error');
    }
  });
}

// ─────────────────────────────────────────────
function exportViettelPostExcel() {
  const orders = window._currentDailyOrders || [];
  // Filter out deleted/cancelled orders
  const validOrders = orders.filter(r => r.maSP && r.trangThai !== 'Đã hủy' && r.trangThai !== 'Đã xóa');
  
  if (validOrders.length === 0) {
    showToast('Không có đơn hàng hợp lệ để xuất!', 'warning');
    return;
  }

  // Pre-export validation: cảnh báo nếu có đơn thiếu địa chỉ nhận hàng
  const missingAddress = validOrders.filter(r => !r.diaChi || !String(r.diaChi).trim());
  if (missingAddress.length > 0) {
    const listCodes = missingAddress.slice(0, 5).map(r => r.maSP).join(', ') + (missingAddress.length > 5 ? '...' : '');
    if (!confirm(`Cảnh báo: Có ${missingAddress.length} đơn hàng chưa có Địa chỉ nhận hàng (${listCodes})!\nViettel Post sẽ từ chối in đơn nếu thiếu địa chỉ.\n\nBạn có chắc chắn vẫn muốn xuất file Excel không?`)) {
      return;
    }
  }

  showLoading('Đang chuẩn bị file Excel Viettel Post...');
  loadScript("https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js", () => {
    try {
      // Define Viettel Post columns matching the template exactly
      const headers = [
        'STT',
        'Mã đơn hàng (*)',
        'Tên người nhận (*)',
        'Số ĐT người nhận (*)',
        'Địa chỉ nhận (*)',
        'Tên hàng hóa (*)',
        'Số lượng',
        'Trọng lượng (gram) (*)',
        'Giá trị hàng (VND) (*)',
        'Tiền thu hộ COD (VND)',
        'Loại hàng hóa (*)',
        'Tính chất hàng hóa đặc biệt',
        'Dịch vụ (*)',
        'Dịch vụ cộng thêm',
        'Thu tiền xem hàng',
        'Dài (cm)',
        'Rộng (cm)',
        'Cao (cm)',
        'Người trả cước',
        'Yêu cầu khác',
        'Thời gian hẹn lấy',
        'Thời gian giao'
      ];
      
            const dataRows = validOrders.map((r, index) => {
        const isFreeship = isViettelFreeship_(r);
        const giaTriBanDau = Number(r.giaBan || 0);
        const khachCoc = Number(r.khachCoc || 0);
        let codAmount = 0;
        if (r.tienCOD !== undefined && r.tienCOD !== null && r.tienCOD !== '') {
          codAmount = Math.max(0, Number(r.tienCOD));
        } else if (khachCoc > 0 && khachCoc >= giaTriBanDau) {
          codAmount = 0;
        } else if (khachCoc > 0 && khachCoc < giaTriBanDau) {
          codAmount = Math.max(0, giaTriBanDau - khachCoc);
        } else {
          codAmount = 0;
        }
        if (codAmount <= 0) codAmount = 0;

        // Nếu COD = 0 (khách đã CK đủ / Freeship) -> Cột I Giá trị hàng để 0 để Viettel Post không nhận 2tr7 và không tính phí bảo hiểm
        const giaTriHang = codAmount > 0 ? (giaTriBanDau || codAmount) : 0;
        
        const svcInfo = getViettelServiceAndDvct_({
          hinhThuc: codAmount > 0 ? 'COD' : (isFreeship ? 'Freeship' : 'Chịu ship'),
          giaBan: giaTriBanDau,
          khachCoc: khachCoc,
          tienCOD: codAmount,
          dichVu: r.dichVu,
          dichVuCongThem: r.dichVuCongThem
        });
        const dichVu = svcInfo.dichVu;
        const dvct = svcInfo.dvct;

        const payer = getViettelPayer_({
          tenKhach: r.tenKhach,
          hinhThuc: codAmount > 0 ? 'COD' : (isFreeship ? 'Freeship' : 'Chịu ship'),
          giaBan: giaTriBanDau,
          khachCoc: khachCoc,
          tienCOD: codAmount
        });

        const loaiHang = r.loaiHangHoa || 'Bưu kiện';
        const tinhChat = r.tinhChatHangHoa || '';
        
        return [
          index + 1,                                     // STT (Cột A)
          r.maSP || '',                                  // Mã đơn hàng (*) (Cột B)
          r.tenKhach || '',                              // Tên người nhận (*) (Cột C)
          r.sdtKhach || '',                              // Số ĐT người nhận (*) (Cột D)
          r.diaChi || '',                                // Địa chỉ nhận (*) (Cột E)
          r.maSP || 'Hàng hóa',                         // Tên hàng hóa (*) (Cột F)
          1,                                             // Số lượng (Cột G)
          Number(r.khoiLuong) || 200,                    // Trọng lượng (gram) (*) (Cột H)
          giaTriHang,                                    // Giá trị hàng (VND) (*) (Cột I)
          codAmount,                                     // Tiền thu hộ COD (VND) (Cột J)
          loaiHang,                                      // Loại hàng hóa (*) (Cột K)
          tinhChat,                                      // Tính chất hàng hóa đặc biệt (Cột L) - để trống
          dichVu,                                        // Dịch vụ (*) (Cột M)
          dvct,                                          // Dịch vụ cộng thêm (Cột N)
          '',                                            // Thu tiền xem hàng (Cột O) - để trống
          1,                                             // Dài (cm) (Cột P)
          1,                                             // Rộng (cm) (Cột Q)
          1,                                             // Cao (cm) (Cột R)
          payer,                                         // Người trả cước (Cột S)
          (r.ghiChu && r.ghiChu !== 'CHO HÀNG XEM') ? r.ghiChu : 'Cho xem hàng không cho thử', // Yêu cầu khác (Cột T)
          '',                                            // Thời gian hẹn lấy (Cột U) - để trống
          'Cả ngày'                                      // Thời gian giao (Cột V)
        ];
      });

      // Construct sheet data including metadata headers at the top
      const sheetData = [
        [],
        ['', 'TẬP ĐOÀN CÔNG NGHIỆP - VIỄN THÔNG QUÂN ĐỘI'],
        ['', 'TỔNG CÔNG TY CỔ PHẦN BƯU CHÍNH VIETTEL'],
        [],
        ['', '', '', '', 'DANH SÁCH ĐƠN HÀNG'],
        headers,
        ...dataRows
      ];

      const ws = XLSX.utils.aoa_to_sheet(sheetData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "ViettelPost_Import");

      // Format filename with current date range or today
      const datePickFrom = document.getElementById('daily-date-from')?.value || '';
      const datePickTo = document.getElementById('daily-date-to')?.value || '';
      const dateSuffix = datePickFrom && datePickTo ? `${datePickFrom}_to_${datePickTo}` : new Date().toISOString().slice(0, 10);

      XLSX.writeFile(wb, `ViettelPost_Import_${dateSuffix}.xlsx`);
      hideLoading();
      showToast(`Xuất ${validOrders.length} đơn hàng Viettel Post thành công!`, 'success');
    } catch (e) {
      hideLoading();
      showToast('Lỗi xuất Excel Viettel Post: ' + e.message, 'error');
    }
  });
}

// ─────────────────────────────────────────────

// ─────────────────────────────────────────────
// DAILY ORDERS (Đơn chốt theo ngày)
// ─────────────────────────────────────────────

function getTodayLocal() {
  const now = new Date();
  const y   = now.getFullYear();
  const m   = String(now.getMonth() + 1).padStart(2, '0');
  const d   = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function getDailyDateRange() {
  const fromEl = document.getElementById('daily-date-from');
  const toEl   = document.getElementById('daily-date-to');
  const from   = fromEl?.value || '';
  const to     = toEl?.value || '';
  const start  = from || to;
  const end    = to || from;

  if (start && end && start > end) {
    return { start: end, end: start };
  }
  return { start, end };
}

function filterDailyOrders(rows, range) {
  if (!range?.start || !range?.end) return [];
  return rows.filter(r => r.ngayChot && r.ngayChot >= range.start && r.ngayChot <= range.end);
}

const dailySortCollator = new Intl.Collator('vi-VN', { numeric: true, sensitivity: 'base' });

function normalizeDailySortText(value) {
  return String(value || '').normalize('NFC').replace(/\s+/g, ' ').trim();
}

function getDailySortValue(row, key) {
  if (key === 'tenKhach') return normalizeDailySortText(row.tenKhach || row.sdtKhach || '');
  if (key === 'maSP') return normalizeDailySortText(row.maSP || '');
  return normalizeDailySortText(row[key] || '');
}

function compareDailySortValue(a, b, key, dir) {
  const av = getDailySortValue(a, key);
  const bv = getDailySortValue(b, key);

  if (!av && bv) return 1;
  if (av && !bv) return -1;

  const base = dailySortCollator.compare(av, bv);
  return dir === 'desc' ? -base : base;
}

function compareDailyRows(a, b) {
  const primary = compareDailySortValue(a, b, dailySort.key, dailySort.dir);
  if (primary !== 0) return primary;

  if (dailySort.key === 'tenKhach') {
    const byPhone = compareDailySortValue(a, b, 'sdtKhach', 'asc');
    if (byPhone !== 0) return byPhone;
    return compareDailySortValue(a, b, 'maSP', 'asc');
  }

  const byCustomer = compareDailySortValue(a, b, 'tenKhach', 'asc');
  if (byCustomer !== 0) return byCustomer;
  return String(a.rowIndex || '').localeCompare(String(b.rowIndex || ''), 'vi-VN', { numeric: true });
}

function sortDailyOrders(rows) {
  return [...(rows || [])].sort(compareDailyRows);
}

function setDailySort(key) {
  if (dailySort.key === key) {
    dailySort.dir = dailySort.dir === 'asc' ? 'desc' : 'asc';
  } else {
    dailySort = { key, dir: 'asc' };
  }

  const range = getDailyDateRange();
  if (allReportRows.length && range.start && range.end) {
    renderDailyOrders(filterDailyOrders(allReportRows, range), range);
  } else {
    loadDailyOrders();
  }
}

function updateDailySortIndicators() {
  const icons = {
    maSP: document.getElementById('daily-sort-masp'),
    tenKhach: document.getElementById('daily-sort-tenkhach')
  };

  Object.keys(icons).forEach((key) => {
    const icon = icons[key];
    if (!icon) return;
    icon.className = key === dailySort.key
      ? 'fas ' + (dailySort.dir === 'asc' ? 'fa-sort-up' : 'fa-sort-down')
      : 'fas fa-sort';
  });
}

function formatDailyDateLabel(dateStr) {
  const [y, m, d] = dateStr.split('-');
  return `${d}/${m}/${y}`;
}

function isDailyCodOrder_(row) {
  return String(row?.hinhThuc || '').trim().toUpperCase() === 'COD';
}

function getDailyCustomerCodKey_(row) {
  const key = getCustomerKey_(row?.tenKhach, row?.sdtKhach);
  return key || `row:${row?.sourceSheet || row?.sheetName || 'SalesData'}:${row?.rowIndex || row?.maSP || ''}`;
}

function buildDailyCustomerCodSummary_(rows) {
  return (rows || []).reduce((map, row) => {
    const key = getDailyCustomerCodKey_(row);
    if (!key) return map;

    if (!map[key]) map[key] = { orders: 0, codOrders: 0, cod: 0 };
    map[key].orders += 1;

    if (isDailyCodOrder_(row)) {
      map[key].codOrders += 1;
      map[key].cod += Number(row.tienCOD || 0);
    }

    return map;
  }, {});
}

function getDailyCustomerCodBadgeHtml_(summary, rowCod, fmt) {
  if (!summary || summary.orders < 2 || summary.cod <= 0) return '';
  const isTotalDifferent = Number(summary.cod || 0) !== Number(rowCod || 0);
  const badgeTitle = `Tổng COD khách này: ${fmt(summary.cod)} / ${summary.codOrders} mã COD`;
  const badgeClass = isTotalDifferent ? 'daily-customer-cod-badge is-grouped' : 'daily-customer-cod-badge';
  return `<span class="${badgeClass}" title="${badgeTitle}">
    <i class="fas fa-calculator"></i> Tổng COD: ${fmt(summary.cod)}
  </span>`;
}

function setDailyToday() {
  const today = getTodayLocal();
  document.getElementById('daily-date-from').value = today;
  document.getElementById('daily-date-to').value = today;
  loadDailyOrders();
}

function loadDailyOrders(forceRefresh) {
  const range = getDailyDateRange();
  if (!range.start || !range.end) return;

  lastSyncRequestTime = Date.now();

  const btnRefresh = document.querySelector('#page-daily button[onclick*="loadDailyOrders"]');
  if (btnRefresh) {
    btnRefresh.disabled = true;
    btnRefresh.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải';
  }

  const reqId = ++currentSyncRequestId;
  showLoading(forceRefresh ? 'Đang xóa cache & tải dữ liệu mới từ Sheet...' : 'Đang tải đơn chốt...');
  
  const handleSuccess = res => {
    if (reqId !== currentSyncRequestId) return;
    if (btnRefresh) {
      btnRefresh.disabled = false;
      btnRefresh.innerHTML = '<i class="fas fa-sync-alt"></i> Làm mới';
    }
    hideLoading();
    if (!res) return;

    crmSnapshot = res;
    allRows = res.rows || [];
    allReportRows = res.reportRows || [];
    buildCustomerHistoryMap();

    // Filter dailyRows based on range
    const dailyFiltered = (res.dailyRows || []).filter(r => r.ngayChot && r.ngayChot >= range.start && r.ngayChot <= range.end);
    renderDailyOrders(dailyFiltered.reverse(), range);
    updateSyncStatusUI(res);

    if (forceRefresh) showToast('Đã làm mới dữ liệu từ Google Sheet!', 'success');
  };

  const handleFailure = e => {
    if (reqId !== currentSyncRequestId) return;
    if (btnRefresh) {
      btnRefresh.disabled = false;
      btnRefresh.innerHTML = '<i class="fas fa-sync-alt"></i> Làm mới';
    }
    hideLoading();
    showToast('Không tải được đơn chốt: ' + e.message, 'error');
  };

  google.script.run
    .withSuccessHandler(handleSuccess)
    .withFailureHandler(handleFailure)
    .getCrmSyncSnapshot({ forceRefresh: !!forceRefresh });
}

// ─────────────────────────────────────────────
// CUSTOM FORMULA CALCULATION FOR DAILY ORDERS
// ──────────────────────────────────────────────
const DEFAULT_CUSTOM_FORMULA = '(von - cod) + loi * 30%';

function evaluateCustomFormula(formulaStr, totals) {
  let expr = String(formulaStr || '').toLowerCase().trim();
  if (!expr) return 0;
  
  // Replace variables
  expr = expr.replace(/vốn|von/g, totals.cost);
  expr = expr.replace(/cod/g, totals.cod);
  expr = expr.replace(/lời|loi/g, totals.profit);
  expr = expr.replace(/bán|ban/g, totals.revenue);
  expr = expr.replace(/cọc|coc/g, totals.deposit);
  
  // Convert percentage sign: e.g. 30% -> (30/100)
  expr = expr.replace(/(\d+(?:\.\d+)?)\s*%/g, "($1/100)");
  
  // Sanitize math string: only allow numbers, operators, dots, spaces, parenthesis
  expr = expr.replace(/[^0-9+\-*/().\s]/g, '');
  
  try {
    const fn = new Function('return ' + (expr || '0'));
    const val = fn();
    return (typeof val === 'number' && !isNaN(val) && isFinite(val)) ? val : 0;
  } catch (e) {
    return 0;
  }
}

function updateCustomFormulaResult(formulaVal) {
  const resultDisplay = document.getElementById('custom-formula-result-display');
  const hintDisplay = document.getElementById('custom-formula-calculation-hint');
  if (!resultDisplay) return;

  const totals = window._currentDailyTotals || { cost: 0, cod: 0, profit: 0, revenue: 0, deposit: 0 };
  
  let hintStr = String(formulaVal || '').toLowerCase();
  hintStr = hintStr.replace(/vốn|von/g, fmtNum(totals.cost));
  hintStr = hintStr.replace(/cod/g, fmtNum(totals.cod));
  hintStr = hintStr.replace(/lời|loi/g, fmtNum(totals.profit));
  hintStr = hintStr.replace(/bán|ban/g, fmtNum(totals.revenue));
  hintStr = hintStr.replace(/cọc|coc/g, fmtNum(totals.deposit));
  
  if (hintDisplay) {
    hintDisplay.textContent = `(${hintStr})`;
  }
  
  const val = evaluateCustomFormula(formulaVal, totals);
  resultDisplay.textContent = fmtVnd(val);
}

function saveCustomFormula(formulaVal) {
  localStorage.setItem('DAILY_CUSTOM_FORMULA', formulaVal);
  updateCustomFormulaResult(formulaVal);
}

function resetCustomFormula() {
  const inputEl = document.getElementById('custom-formula-input');
  if (inputEl) {
    inputEl.value = DEFAULT_CUSTOM_FORMULA;
    saveCustomFormula(DEFAULT_CUSTOM_FORMULA);
  }
}

function renderDailyOrders(rows, dateRange) {
  const fmt  = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
  const dash = v => (v && String(v).trim()) ? v : '—';
  const sortedRows = sortDailyOrders(rows || []);
  window._currentDailyOrders = sortedRows;
  const customerCodSummary = buildDailyCustomerCodSummary_(sortedRows);
  updateDailySortIndicators();

  // Format date display
  const range = typeof dateRange === 'string' ? { start: dateRange, end: dateRange } : dateRange;
  const today = getTodayLocal();
  const isSingleDay = range.start === range.end;
  const isToday = isSingleDay && range.start === today;
  const dateLabel = isToday
    ? `Hôm nay — ${formatDailyDateLabel(range.start)}`
    : isSingleDay
      ? formatDailyDateLabel(range.start)
      : `${formatDailyDateLabel(range.start)} - ${formatDailyDateLabel(range.end)}`;

  document.getElementById('daily-orders-subtitle').textContent =
    sortedRows.length > 0
      ? `${dateLabel} · ${sortedRows.length} đơn · sắp theo ${dailySort.key === 'tenKhach' ? 'tên khách' : 'MÃ SP'}`
      : `${dateLabel} · Không có đơn nào`;

  // Summary computations
  const totals = sortedRows.reduce((a, r) => {
    a.orders  += 1;
    a.revenue += r.giaBan   || 0;
    a.cost    += r.giaVon   || 0;
    a.profit  += r.tienLoi  || 0;
    a.deposit += r.khachCoc || 0;
    a.cod     += isDailyCodOrder_(r) ? (r.tienCOD || 0) : 0;
    return a;
  }, { orders: 0, revenue: 0, cost: 0, profit: 0, deposit: 0, cod: 0 });
  window._currentDailyTotals = totals;

  // Compute previous range performance for growth rate
  const startMs = new Date(range.start).getTime();
  const endMs = new Date(range.end).getTime();
  const diffMs = endMs - startMs;
  const prevStart = new Date(startMs - diffMs - 24 * 60 * 60 * 1000);
  const prevEnd = new Date(startMs - 24 * 60 * 60 * 1000);
  const prevStartStr = prevStart.toISOString().slice(0, 10);
  const prevEndStr = prevEnd.toISOString().slice(0, 10);

  const prevRows = allReportRows.filter(r => r.ngayChot && r.ngayChot >= prevStartStr && r.ngayChot <= prevEndStr);
  const prevTotals = prevRows.reduce((a, r) => {
    a.orders  += 1;
    a.revenue += r.giaBan   || 0;
    a.profit  += r.tienLoi  || 0;
    a.deposit += r.khachCoc || 0;
    a.cod     += isDailyCodOrder_(r) ? (r.tienCOD || 0) : 0;
    return a;
  }, { orders: 0, revenue: 0, profit: 0, deposit: 0, cod: 0 });

  const getGrowth = (cur, prev) => {
    if (prev === 0) return cur > 0 ? 100 : 0;
    return Math.round(((cur - prev) / prev) * 100);
  };

  const growth = {
    orders: getGrowth(totals.orders, prevTotals.orders),
    revenue: getGrowth(totals.revenue, prevTotals.revenue),
    profit: getGrowth(totals.profit, prevTotals.profit),
    deposit: getGrowth(totals.deposit, prevTotals.deposit),
    cod: getGrowth(totals.cod, prevTotals.cod)
  };

  // Shipping breakdowns
  let codCount = 0, freeCount = 0;
  let codRevenue = 0, freeRevenue = 0;
  sortedRows.forEach(r => {
    if (isDailyCodOrder_(r)) {
      codCount++;
      codRevenue += r.giaBan || 0;
    } else {
      freeCount++;
      freeRevenue += r.giaBan || 0;
    }
  });

  // Populate card values
  document.getElementById('daily-pill-orders').textContent  = totals.orders;
  document.getElementById('daily-pill-revenue').textContent = new Intl.NumberFormat('vi-VN').format(totals.revenue) + ' ₫';
  document.getElementById('daily-pill-profit').textContent  = (totals.profit >= 0 ? '+' : '') + new Intl.NumberFormat('vi-VN').format(totals.profit) + ' ₫';
  document.getElementById('daily-pill-deposit').textContent = new Intl.NumberFormat('vi-VN').format(totals.deposit) + ' ₫';
  document.getElementById('daily-pill-cod').textContent     = new Intl.NumberFormat('vi-VN').format(totals.cod) + ' ₫';

  // Render trend texts
  const renderTrend = (elId, pct) => {
    const el = document.getElementById(elId);
    if (!el) return;
    if (pct > 0) {
      el.className = 'daily-card-trend trend-up';
      el.innerHTML = `<i class="fas fa-arrow-trend-up"></i> +${pct}% so với kỳ trước`;
    } else if (pct < 0) {
      el.className = 'daily-card-trend trend-down';
      el.innerHTML = `<i class="fas fa-arrow-trend-down"></i> ${pct}% so với kỳ trước`;
    } else {
      el.className = 'daily-card-trend';
      el.innerHTML = `<i class="fas fa-arrows-left-right"></i> Không đổi`;
    }
  };

  renderTrend('daily-trend-orders', growth.orders);
  renderTrend('daily-trend-revenue', growth.revenue);
  renderTrend('daily-trend-profit', growth.profit);
  renderTrend('daily-trend-deposit', growth.deposit);
  renderTrend('daily-trend-cod', growth.cod);

  // Render breakdowns
  document.getElementById('daily-breakdown-orders').textContent = `COD: ${codCount} · Free: ${freeCount}`;
  document.getElementById('daily-breakdown-revenue').textContent = `COD: ${fmtVnd(codRevenue)} · Free: ${fmtVnd(freeRevenue)}`;
  document.getElementById('daily-breakdown-profit').textContent = `T.Lợi nhuận gộp`;
  document.getElementById('daily-breakdown-deposit').textContent = `Tổng cọc khách gửi`;
  document.getElementById('daily-breakdown-cod').textContent = `Tổng COD cần thu`;

  const table = document.getElementById('daily-orders-table');
  const tbody = document.getElementById('daily-orders-tbody');
  const empty = document.getElementById('daily-empty');

  if (sortedRows.length === 0) {
    table.style.display = 'none';
    empty.style.display = 'block';
    return;
  }

  table.style.display = '';
  empty.style.display = 'none';

  const dailyCustomerTotalsMap = buildCustomerTotalsMap_(sortedRows);

  tbody.innerHTML = sortedRows.map((r, i) => {
    // Stagger animation delay
    const delay = (i * 40) + 'ms';
    const hasAnomaly = checkAnomaly(r);
    const ttBadge = getStatusBadge(r.trangThai, true);

    const htBadge = getShippingBadge(r, 'font-size:0.68rem;', dailyCustomerTotalsMap);

    const tienLoiClass = r.tienLoi >= 0 ? 'profit-positive' : 'profit-negative';
    const tienLoiSign  = r.tienLoi >= 0 ? '+' : '';

    const linkCell = r.linkTiktok
      ? `<a href="${r.linkTiktok}" target="_blank" rel="noopener" title="${r.linkTiktok}" style="color:var(--primary-light)"><i class="fas fa-external-link-alt"></i></a>`
      : '<span style="color:var(--text-muted)">—</span>';

    const customerBadge = getCustomerBadgeHtml(r.tenKhach, r.sdtKhach);
    const rowClass = hasAnomaly ? 'row-anomaly' : '';
    const rowSheet = getRowSheetName_(r);
    const safeSheet = escapeForInlineEdit(rowSheet);
    const isEditable = isClientEditableSheet_(rowSheet);
    const customerSummary = customerCodSummary[getDailyCustomerCodKey_(r)];
    const customerCodBadge = getDailyCustomerCodBadgeHtml_(customerSummary, isDailyCodOrder_(r) ? r.tienCOD : 0, fmt);

    return `<tr class="${rowClass}" style="animation-delay:${delay}">
      <td>${i + 1}</td>
      <td title="${r.maSP}">${r.maSP}</td>
      <td>${fmt(r.giaBan)}</td>
      <td class="cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'giaVon',${r.giaVon},'${safeSheet}')" title="Click để sửa giá vốn">${fmt(r.giaVon)}</td>
      <td class="${tienLoiClass}">${tienLoiSign}${fmt(r.tienLoi)}</td>
      <td>${r.khachCoc ? fmt(r.khachCoc) : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td>${isDailyCodOrder_(r) ? fmt(r.tienCOD) : '<span style="color:var(--text-muted)">—</span>'}</td>
      <td title="${r.tenKhach || ''}">
        <div class="daily-customer-cell">
          <div class="daily-customer-main">
            <strong class="customer-name-clickable" onclick="openCustomerProfileModal('${escapeForInlineEdit(r.tenKhach)}', '${escapeForInlineEdit(r.sdtKhach)}')" title="Xem hồ sơ khách hàng">${dash(r.tenKhach)}</strong>${customerBadge}
          </div>
          ${customerCodBadge}
        </div>
      </td>
      <td>${dash(r.sdtKhach)}</td>
      <td>${htBadge}</td>
      <td style="text-align:center;font-size:0.82rem;color:var(--text-muted);">${r.khoiLuong || 200}g</td>
      <td class="note-cell col-ghichu cell-editable" onclick="startInlineEdit(this,${r.rowIndex},'ghiChu','${escapeForInlineEdit(r.ghiChu)}','${safeSheet}')" title="Click để sửa ghi chú">${dash(r.ghiChu)}</td>
      <td>
        <div class="action-btns" style="${isEditable ? '' : 'display:none;'}">
          <button class="btn-action btn-edit" onclick="openEditModal(${r.rowIndex}, '${safeSheet}')" title="Sửa"><i class="fas fa-pencil-alt"></i></button>
          <button class="btn-action btn-copy" onclick="copyOrderToClipboard(${r.rowIndex}, '${safeSheet}')" title="Sao chép thông tin"><i class="far fa-copy"></i></button>
          <button class="btn-action btn-ship" onclick="markAsShipped(${r.rowIndex}, '${safeSheet}')" title="Đã giao"><i class="fas fa-truck"></i></button>
          <button class="btn-action btn-cancel" onclick="markAsCancelled(${r.rowIndex}, '${safeSheet}')" title="Hủy"><i class="fas fa-ban"></i></button>
        </div>
      </td>
    </tr>`;
  }).join('');

  // Daily orders table footer
  const dailyTfoot = document.getElementById('daily-orders-tfoot');
  if (dailyTfoot) {
    const DEFAULT_CUSTOM_FORMULA = '(von - cod) + loi * 30%';
    const customFormula = localStorage.getItem('DAILY_CUSTOM_FORMULA') || DEFAULT_CUSTOM_FORMULA;
    const calculatedResult = evaluateCustomFormula(customFormula, totals);
    const fNum = n => new Intl.NumberFormat('vi-VN').format(n);
    let hintStr = customFormula.toLowerCase();
    hintStr = hintStr.replace(/vốn|von/g, fNum(totals.cost));
    hintStr = hintStr.replace(/cod/g, fNum(totals.cod));
    hintStr = hintStr.replace(/lời|loi/g, fNum(totals.profit));
    hintStr = hintStr.replace(/bán|ban/g, fNum(totals.revenue));
    hintStr = hintStr.replace(/cọc|coc/g, fNum(totals.deposit));

    dailyTfoot.innerHTML = `
      <tr>
        <td></td>
        <td><strong>TỔNG</strong></td>
        <td><strong>${fmt(totals.revenue)}</strong></td>
        <td><strong>${fmt(totals.cost)}</strong></td>
        <td class="${totals.profit >= 0 ? 'profit-positive' : 'profit-negative'}"><strong>${totals.profit >= 0 ? '+' : ''}${fmt(totals.profit)}</strong></td>
        <td><strong>${fmt(totals.deposit)}</strong></td>
        <td><strong>${fmt(totals.cod)}</strong></td>
        <td><strong>${totals.orders} đơn</strong></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr class="custom-formula-row">
        <td></td>
        <td style="vertical-align: middle;"><strong>VỐN + LỜI</strong></td>
        <td colspan="11" style="vertical-align: middle; text-align: left; padding: 10px 14px;">
          <div class="custom-formula-container" style="display: flex; align-items: center; gap: 12px; flex-wrap: nowrap; white-space: nowrap;">
            <div style="position: relative; display: inline-flex; align-items: center; flex-shrink: 0;">
              <input type="text" id="custom-formula-input" value="${escapeForInlineEdit(customFormula)}" 
                     class="custom-formula-field" 
                     oninput="updateCustomFormulaResult(this.value)"
                     onchange="saveCustomFormula(this.value)" 
                     title="Cách tính mặc định: (von - cod) + loi * 30% &#10;Ký hiệu: von (Giá vốn), cod (Tiền COD), loi (Tiền lời), ban (Giá bán), coc (Khách cọc)" />
              <button onclick="resetCustomFormula()" style="background: none; border: none; color: var(--text-muted); cursor: pointer; position: absolute; right: 8px; font-size: 0.75rem; padding: 2px;" title="Khôi phục mặc định"><i class="fas fa-undo"></i></button>
            </div>
            <div style="display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0; white-space: nowrap;">
              <span style="color: var(--text-muted); font-size: 0.85rem;" id="custom-formula-calculation-hint">(${hintStr})</span>
              <span style="color: var(--text-muted); font-size: 0.85rem; font-weight: bold;">=</span>
              <strong style="color: #34D399; font-size: 1.1rem; letter-spacing: 0.02em;" id="custom-formula-result-display">${fmtVnd(calculatedResult)}</strong>
            </div>
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">
            <i class="fas fa-info-circle fa-xs"></i> Biến khả dụng: <strong>von</strong> (Vốn), <strong>cod</strong> (COD), <strong>loi</strong> (Lời), <strong>ban</strong> (Bán), <strong>coc</strong> (Cọc). Hỗ trợ phần trăm (ví dụ: <code>30%</code> hoặc <code>* 30%</code>).
          </div>
        </td>
      </tr>
    `;
  }
}

// ══════════════════════════════════════════════
// F9: REVENUE GOAL TRACKER
// ══════════════════════════════════════════════
const GOALS_STORAGE_KEY = 'SALES_GOALS_V1';

function getGoals() {
  try { return JSON.parse(localStorage.getItem(GOALS_STORAGE_KEY) || '{"daily":0,"monthly":0}'); }
  catch(e) { return { daily: 0, monthly: 0 }; }
}

function openGoalModal() {
  const g = getGoals();
  const di = document.getElementById('goal-input-daily');
  const mi = document.getElementById('goal-input-monthly');
  if (di) di.value = g.daily || '';
  if (mi) mi.value = g.monthly || '';
  openModal('modal-goal');
}

function saveGoals() {
  const daily   = parseFloat(document.getElementById('goal-input-daily').value)   || 0;
  const monthly = parseFloat(document.getElementById('goal-input-monthly').value) || 0;
  localStorage.setItem(GOALS_STORAGE_KEY, JSON.stringify({ daily, monthly }));
  closeModal('modal-goal');
  showToast('Lưu mục tiêu thành công!', 'success');
  if (window._lastGoalStats) updateGoalTracker(window._lastGoalStats);
}

function getCustomerVipTierRuleByKey_(key) {
  return CUSTOMER_VIP_TIERS.find(tier => tier.key === key) ||
    DEFAULT_CUSTOMER_VIP_TIERS.find(tier => tier.key === key) ||
    null;
}

function openVipTierModal() {
  ['bronze', 'silver', 'gold', 'diamond'].forEach(key => {
    const labelInput = document.getElementById('vip-label-' + key);
    const moneyInput = document.getElementById('vip-money-' + key);
    const tier = getCustomerVipTierRuleByKey_(key);
    if (labelInput && tier) labelInput.value = tier.label;
    if (moneyInput && tier) moneyInput.value = tier.minLtv || '';
  });
  openModal('modal-vip-tier');
}

function refreshVipTierDisplays_() {
  if (allReportRows && allReportRows.length) buildCustomerHistoryMap();

  const productsPage = document.getElementById('page-products');
  if (productsPage && !productsPage.classList.contains('hidden')) renderTable();

  const dailyPage = document.getElementById('page-daily');
  if (dailyPage && !dailyPage.classList.contains('hidden')) {
    const range = getDailyDateRange();
    if (range.start && range.end) renderDailyOrders(filterDailyOrders(allReportRows, range), range);
  }

  const statsPage = document.getElementById('page-stats');
  if (statsPage && !statsPage.classList.contains('hidden')) loadAdvancedStats();
}

function saveVipTierLabels() {
  const labels = {};
  const minLtvs = {};
  ['bronze', 'silver', 'gold', 'diamond'].forEach(key => {
    const tier = getCustomerVipTierRuleByKey_(key);
    labels[key] = (document.getElementById('vip-label-' + key)?.value || '').trim();
    minLtvs[key] = parseMoneyInput_(document.getElementById('vip-money-' + key)?.value, tier ? tier.minLtv : 0);
  });

  const btn = document.getElementById('vip-label-save-btn');
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
  }

  google.script.run
    .withSuccessHandler(res => {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }

      if (!res || res.success === false) {
        showToast('Không lưu được hạng VIP.', 'error');
        return;
      }

      setCustomerVipTierSettings_(res);
      closeModal('modal-vip-tier');
      showToast('Đã lưu hạng VIP!', 'success');
      refreshVipTierDisplays_();
    })
    .withFailureHandler(e => {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
      showToast('Lỗi lưu hạng VIP: ' + (e && e.message ? e.message : e), 'error');
    })
    .saveVipTierLabels({ labels, minLtvs });
}

function updateGoalTracker(s) {
  window._lastGoalStats = s;
  const g = getGoals();
  const month = new Date().toISOString().slice(0, 7);
  const fmtC = n => new Intl.NumberFormat('vi-VN', { notation: 'compact', maximumFractionDigits: 1 }).format(n);

  // Daily
  const daily = s.doanhThuHomNay || 0;
  const dPct  = g.daily > 0 ? Math.min(100, Math.round(daily / g.daily * 100)) : 0;
  const dBar  = document.getElementById('goal-bar-daily');
  const dVal  = document.getElementById('goal-daily-val');
  const dPctEl= document.getElementById('goal-daily-pct');
  if (dBar) { dBar.style.width = dPct + '%'; dBar.className = 'goal-bar daily' + (dPct >= 100 ? ' over' : ''); }
  if (dVal) dVal.textContent = fmtC(daily) + ' / ' + (g.daily > 0 ? fmtC(g.daily) : '?') + ' ₫';
  if (dPctEl) dPctEl.textContent = g.daily > 0 ? dPct + '%' + (dPct >= 100 ? ' 🎉 Đạt!' : '') : 'Chưa đặt mục tiêu';

  // Monthly: sum chartDoanhThu for current month
  let monthly = 0;
  (s.chartLabels || []).forEach((lbl, i) => {
    if (String(lbl).startsWith(month)) monthly += (s.chartDoanhThu || [])[i] || 0;
  });
  const mPct = g.monthly > 0 ? Math.min(100, Math.round(monthly / g.monthly * 100)) : 0;
  const mBar  = document.getElementById('goal-bar-monthly');
  const mVal  = document.getElementById('goal-monthly-val');
  const mPctEl= document.getElementById('goal-monthly-pct');
  if (mBar) { mBar.style.width = mPct + '%'; mBar.className = 'goal-bar monthly' + (mPct >= 100 ? ' over' : ''); }
  if (mVal) mVal.textContent = fmtC(monthly) + ' / ' + (g.monthly > 0 ? fmtC(g.monthly) : '?') + ' ₫';
  if (mPctEl) mPctEl.textContent = g.monthly > 0 ? mPct + '%' + (mPct >= 100 ? ' 🎉 Đạt!' : '') : 'Chưa đặt mục tiêu';
}

// ══════════════════════════════════════════════
// F10: COD PENDING BADGE
// ══════════════════════════════════════════════
function updateCODBadge() {
  const today = new Date().toISOString().slice(0, 10);
  const pending = (allRows || []).filter(r =>
    r.trangThai === 'Đã bán' && r.hinhThuc === 'COD' && (r.tienCOD || 0) > 0 && r.ngayChot === today
  );
  const total = pending.reduce((s, r) => s + (r.tienCOD || 0), 0);
  const pill   = document.getElementById('cod-topbar-pill');
  const amount = document.getElementById('cod-topbar-amount');
  if (!pill) return;
  if (pending.length > 0) {
    pill.classList.add('visible');
    if (amount) amount.textContent = new Intl.NumberFormat('vi-VN').format(total) + ' ₫';
    pill.title = pending.length + ' đơn COD hôm nay cần thu: ' + new Intl.NumberFormat('vi-VN').format(total) + ' ₫';
  } else {
    pill.classList.remove('visible');
  }
}

// ═══════════════════════════════════───══════════
// F11: EXPORT CSV (CLIENT-SIDE)
// ══════════════════════════════════════════════
function exportToCSV() {
  const rows = filteredRows || [];
  if (!rows.length) { showToast('Không có dữ liệu để xuất!', 'warning'); return; }
  const headers = ['MÃ SP','Giá bán','Giá vốn','Tiền lời','Tên khách','SĐT',
                   'Ngày chốt','Trạng thái','Giao hàng','Tiền COD','Khách cọc',
                   'Ai chốt','Nguồn khách','Địa chỉ','Ghi chú','Link TikTok'];
  const data = rows.map(r => [
    r.maSP, r.giaBan, r.giaVon, r.tienLoi, r.tenKhach, r.sdtKhach,
    r.ngayChot, r.trangThai, r.hinhThuc, r.tienCOD, r.khachCoc,
    r.aiChot, r.nguonKhach, r.diaChi, r.ghiChu, r.linkTiktok
  ]);
  const csv = [headers, ...data]
    .map(row => row.map(c => '"' + String(c == null ? '' : c).replace(/"/g,'""') + '"').join(','))
    .join('\r\n');
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = 'SalesData_' + new Date().toISOString().slice(0,10) + '.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast('Đã xuất ' + rows.length + ' dòng CSV!', 'success');
}

// ══════════════════════════════════════════════
// F12: INLINE QUICK-EDIT
// ══════════════════════════════════════════════
function startInlineEdit(cell, rowIndex, field, currentValue, sheetName) {
  if (cell.classList.contains('inline-saving')) return;
  if (cell.querySelector('.inline-input,.inline-select')) return;
  cell._origHTML = cell.innerHTML;

  if (field === 'trangThai') {
    const opts = ['Còn hàng','Đã bán','Đợi CK','Đã xóa']
      .map(v => `<option value="${v}" ${v === currentValue ? 'selected' : ''}>${v}</option>`).join('');
    cell.innerHTML = `<select class="inline-select">${opts}</select>`;
    const sel = cell.querySelector('.inline-select');
    sel.focus();
    sel.onblur  = () => saveInlineEdit(sel, cell, rowIndex, field, currentValue, sheetName);
    sel.onkeydown = e => {
      if (e.key === 'Enter') { e.preventDefault(); saveInlineEdit(sel, cell, rowIndex, field, currentValue, sheetName); }
      if (e.key === 'Escape') { cell.innerHTML = cell._origHTML; }
    };
  } else if (field === 'giaBan' || field === 'giaVon') {
    const formattedVal = new Intl.NumberFormat('vi-VN').format(Number(currentValue || 0));
    cell.innerHTML = `<input class="inline-input" type="text" value="${formattedVal}" style="width:100%; box-sizing:border-box; text-align:right; font-weight:600;">`;
    const inp = cell.querySelector('.inline-input');
    inp.focus(); inp.select();
    inp.oninput = () => {
      let clean = inp.value.replace(/\D/g, '');
      inp.value = clean ? new Intl.NumberFormat('vi-VN').format(parseInt(clean, 10)) : '';
    };
    inp.onblur  = () => saveInlineEdit(inp, cell, rowIndex, field, currentValue, sheetName);
    inp.onkeydown = e => {
      if (e.key === 'Enter') { e.preventDefault(); saveInlineEdit(inp, cell, rowIndex, field, currentValue, sheetName); }
      if (e.key === 'Escape') { cell.innerHTML = cell._origHTML; }
    };
  } else if (field === 'ghiChu' || field === 'linkTiktok') {
    cell.innerHTML = `<input class="inline-input" type="text" value="${escapeHtml(currentValue)}" style="width:100%; box-sizing:border-box;">`;
    const inp = cell.querySelector('.inline-input');
    inp.focus(); inp.select();
    inp.onblur  = () => saveInlineEdit(inp, cell, rowIndex, field, currentValue, sheetName);
    inp.onkeydown = e => {
      if (e.key === 'Enter') { e.preventDefault(); saveInlineEdit(inp, cell, rowIndex, field, currentValue, sheetName); }
      if (e.key === 'Escape') { cell.innerHTML = cell._origHTML; }
    };
  }
}

function saveInlineEdit(el, cell, rowIndex, field, origValue, sheetName) {
  const newVal = el.value;
  let parsedVal;
  if (field === 'giaBan' || field === 'giaVon') {
    const clean = String(newVal).replace(/\D/g, '');
    parsedVal = parseFloat(clean) || 0;
  } else {
    parsedVal = newVal;
  }
  if (String(parsedVal) === String(origValue)) { cell.innerHTML = cell._origHTML; return; }
  cell.classList.add('inline-saving');
  const patch = {};
  patch[field] = parsedVal;
  const rowSheet = sheetName || 'SalesData';
  google.script.run
    .withSuccessHandler(res => {
      if (res && res.success) {
        if (rowSheet === 'SalesData') {
          const idx = allRows.findIndex(r => Number(r.rowIndex) === Number(rowIndex));
          if (idx !== -1) {
            allRows[idx] = Object.assign({}, allRows[idx], patch);
            if (field === 'giaBan' || field === 'giaVon') allRows[idx].tienLoi = (allRows[idx].giaBan || 0) - (allRows[idx].giaVon || 0);
          }
          filteredRows = [...allRows];
          applyFilters();
        }
        const dailyPage = document.getElementById('page-daily');
        if (dailyPage && !dailyPage.classList.contains('hidden')) loadDailyOrders();
        showToast('Đã cập nhật!', 'success');
      } else {
        cell.classList.remove('inline-saving');
        cell.innerHTML = cell._origHTML;
        showToast('Lỗi cập nhật!', 'error');
      }
    })
    .withFailureHandler(e => {
      cell.classList.remove('inline-saving');
      cell.innerHTML = cell._origHTML;
      showToast('Lỗi: ' + e.message, 'error');
    })
    .quickUpdateRow(parseInt(rowIndex), patch, rowSheet);
}

// ══════════════════════════════════════════════
// F13: SKELETON TABLE LOADING
// ══════════════════════════════════════════════
function showSkeletonTable(count) {
  const tbody = document.getElementById('products-tbody');
  const table = document.getElementById('products-table');
  const empty = document.getElementById('empty-state-products');
  if (!tbody || !table) return;
  table.style.display = '';
  if (empty) empty.classList.add('hidden');
  tbody.innerHTML = Array(count || 6).fill(0).map(() =>
    '<tr class="skeleton-row">' +
    Array(12).fill(0).map(() => '<td><span class="skel"></span></td>').join('') +
    '</tr>'
  ).join('');
}

// ══════════════════════════════════════════════
// F15: SWIPE-TO-EDIT (MOBILE)
// ══════════════════════════════════════════════
function attachSwipeHandlers() {
  if (window.innerWidth > 900) return;
  const rows = document.querySelectorAll('#products-tbody tr[data-rowindex]');
  rows.forEach(row => {
    let startX = 0, startY = 0;
    row.addEventListener('touchstart', e => {
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      row.classList.remove('swipe-hint-edit','swipe-hint-delete');
    }, { passive: true });
    row.addEventListener('touchmove', e => {
      const dx = e.touches[0].clientX - startX;
      const dy = e.touches[0].clientY - startY;
      if (Math.abs(dy) > Math.abs(dx)) return;
      if (dx < -40) { row.classList.add('swipe-hint-edit'); row.classList.remove('swipe-hint-delete'); }
      else if (dx > 40) { row.classList.add('swipe-hint-delete'); row.classList.remove('swipe-hint-edit'); }
      else { row.classList.remove('swipe-hint-edit','swipe-hint-delete'); }
    }, { passive: true });
    row.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - startX;
      const dy = e.changedTouches[0].clientY - startY;
      row.classList.remove('swipe-hint-edit','swipe-hint-delete');
      if (Math.abs(dy) > Math.abs(dx) || Math.abs(dx) < 70) return;
      const ri = row.dataset.rowindex;
      const ms = row.dataset.masp;
      if (!ri) return;
      if (dx < -70) openEditModal(Number(ri));
      else if (dx > 70) openDeleteModal(Number(ri), ms);
    }, { passive: true });
  });
}

function checkAnomaly(r) {
  const tt = String(r.trangThai || '').toLowerCase();
  const isSold = tt.includes('bán');
  const isWaiting = tt.includes('đợi') || tt.includes('ck') || tt.includes('chờ');
  if (isSold || isWaiting) {
    const cod = Number(r.tienCOD || 0);
    const coc = Number(r.khachCoc || 0);
    const gia = Number(r.giaBan || 0);
    if (cod === 0 && coc < gia) {
      return true;
    }
  }
  return false;
}

function escapeForInlineEdit(str) {
  return String(str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function updateAISummary(s) {
  const listEl = document.getElementById('ai-summary-text');
  if (!listEl) return;

  if (!s || s.donBanHomNay === 0) {
    listEl.innerHTML = `
      <div style="display:flex; align-items:center; gap:10px; color:var(--text-muted);">
        <i class="fas fa-info-circle"></i> Hôm nay chưa phát sinh đơn chốt nào để phân tích. Hệ thống sẽ tự động tổng hợp khi có đơn mới!
      </div>
    `;
    return;
  }

  const tzDate = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Ho_Chi_Minh' }));
  const todayStr = tzDate.getFullYear() + '-' + String(tzDate.getMonth() + 1).padStart(2, '0') + '-' + String(tzDate.getDate()).padStart(2, '0');

  const salesLikeRows = (allReportRows && allReportRows.length ? allReportRows : allRows)
    .filter(r => String(r.sourceSheet || r.sheetName || 'SalesData') !== 'THANH LÝ');
  const todayOrders = salesLikeRows.filter(r => {
    const tt = String(r.trangThai || '').toLowerCase();
    const isSoldOrWait = tt.includes('bán') || tt.includes('đợi') || tt.includes('ck') || tt.includes('chờ');
    return isSoldOrWait && r.ngayChot === todayStr;
  });

  // 1. COD percentage share of today's revenue
  let todayCODRevenue = 0;
  todayOrders.forEach(o => {
    if (o.hinhThuc === 'COD') {
      todayCODRevenue += Number(o.giaBan || 0);
    }
  });
  const codPercent = s.doanhThuHomNay > 0 ? Math.round((todayCODRevenue / s.doanhThuHomNay) * 100) : 0;

  // 2. Best selling product base today
  const todayProductCounts = {};
  todayOrders.forEach(o => {
    const code = String(o.maSP || '').trim();
    const parts = code.split('-');
    const key = parts.length > 1 ? parts[0] + '-' + parts[1] : code;
    if (key) {
      todayProductCounts[key] = (todayProductCounts[key] || 0) + 1;
    }
  });
  let bestSeller = '';
  let maxProductSales = 0;
  for (let k in todayProductCounts) {
    if (todayProductCounts[k] > maxProductSales) {
      maxProductSales = todayProductCounts[k];
      bestSeller = k;
    }
  }

  // 3. Multi-purchase customers of today
  const todayCustomerCounts = {};
  todayOrders.forEach(o => {
    const name = String(o.tenKhach || '').trim();
    if (name) {
      todayCustomerCounts[name] = (todayCustomerCounts[name] || 0) + 1;
    }
  });
  const multiPurchaseArr = Object.keys(todayCustomerCounts)
    .filter(name => todayCustomerCounts[name] >= 2)
    .map(name => `Khách <b>${name}</b> mua ${todayCustomerCounts[name]} lần hôm nay`);
  const multiPurchaseText = multiPurchaseArr.length > 0 
    ? multiPurchaseArr.join(', ') 
    : 'Chưa có khách mua trùng lặp';

  // 4. Growth text
  const growthDirection = s.growthDoanhThu >= 0 ? 'tăng' : 'giảm';
  const growthValText = `Doanh thu ${growthDirection} <b>${Math.abs(s.growthDoanhThu)}%</b>`;

  listEl.innerHTML = `
    <div style="font-weight: 700; color: #c084fc; margin-bottom: 8px;"><i class="fas fa-brain"></i> 🤖 AI nhận thấy hôm nay:</div>
    <ul>
      <li>${multiPurchaseText}</li>
      <li>COD chiếm <b>${codPercent}%</b></li>
      <li>${bestSeller ? `Mẫu <b>${bestSeller}</b> bán chạy nhất` : 'Chưa có sản phẩm nổi bật'}</li>
      <li>${growthValText} so với hôm qua</li>
    </ul>
  `;
}

// ─────────────────────────────────────────────
// PRO ADDITIONAL HELPERS
// ─────────────────────────────────────────────

function getStatusBadge(status, compact = false) {
  const s = String(status || '').trim();
  const l = s.toLowerCase();
  const styleStr = compact ? 'style="font-size:0.68rem;"' : '';
  
  if (l.includes('bán') || l === 'ban') {
    return `<span class="badge badge-success" ${styleStr}><i class="fas fa-check fa-xs"></i> ${compact ? 'Bán' : 'Đã bán'}</span>`;
  }
  if (l.includes('giữ') || l.includes('con') || l.includes('còn')) {
    return `<span class="badge badge-warning" ${styleStr}><i class="fas fa-circle fa-xs"></i> ${compact ? 'Còn' : 'Còn hàng'}</span>`;
  }
  if (l.includes('đợi') || l.includes('ck') || l.includes('chờ') || l.includes('thanh toán')) {
    return `<span class="badge badge-orange" ${styleStr}><i class="fas fa-clock fa-xs"></i> ${compact ? 'CK' : 'Đợi CK'}</span>`;
  }
  if (l.includes('hủy') || l.includes('xóa') || l.includes('huy') || l.includes('xoa')) {
    return `<span class="badge badge-danger" ${styleStr}><i class="fas fa-times fa-xs"></i> ${compact ? 'Hủy' : 'Đã xóa'}</span>`;
  }
  if (l.includes('hoàn') || l.includes('hoanthanh') || l.includes('hoàn thành')) {
    return `<span class="badge badge-info" ${styleStr}><i class="fas fa-flag-checkered fa-xs"></i> ${compact ? 'X.Dương' : 'Hoàn thành'}</span>`;
  }
  return `<span class="badge badge-secondary" ${styleStr}>${s || '-'}</span>`;
}

function buildCustomerTotalsMap_(rowsPool) {
  try {
    const pool = rowsPool || [];
    const map = {};
    (pool || []).forEach(r => {
      if (!r) return;
      const tt = String(r.trangThai || '').toLowerCase();
      if (tt.includes('xóa') || tt.includes('huy')) return;
      
      const phone = typeof normalizeCustomerPhone_ === 'function' ? normalizeCustomerPhone_(r.sdtKhach) : '';
      const name = String(r.tenKhach || '').trim();
      const key = typeof getCustomerKey_ === 'function' ? getCustomerKey_(name, phone) : '';
      if (!key) return;

      if (!map[key]) {
        map[key] = { totalGiaBan: 0, totalKhachCoc: 0, count: 0 };
      }
      map[key].totalGiaBan += Number(r.giaBan || 0);
      map[key].totalKhachCoc += Number(r.khachCoc || 0);
      map[key].count += 1;
    });
    return map;
  } catch (e) {
    console.error('buildCustomerTotalsMap_ error:', e);
    return {};
  }
}

function getShippingBadge(r, extraStyle, customerTotalsMap) {
  try {
    if (!r) return '';
    const price   = Number(r.giaBan)   || 0;
    const deposit = Number(r.khachCoc) || 0;
    const htUpper = String(r.hinhThuc || '').toUpperCase();

    let isFreeShip = htUpper === 'FREESHIP' || htUpper === 'FREE';

    if (!isFreeShip) {
      const key = typeof getCustomerKey_ === 'function' ? getCustomerKey_(r.tenKhach, r.sdtKhach) : '';
      const cTotals = (key && customerTotalsMap) ? customerTotalsMap[key] : null;

      if (cTotals) {
        if (Number(cTotals.totalGiaBan || 0) >= 500000 && Number(cTotals.totalKhachCoc || 0) >= Number(cTotals.totalGiaBan || 0)) {
          isFreeShip = true;
        }
      } else {
        if (price >= 500000 && deposit >= price) {
          isFreeShip = true;
        }
      }
    }

    const s = extraStyle ? ` style="${extraStyle}"` : '';
    return isFreeShip
      ? `<span class="badge badge-success"${s}><i class="fas fa-shipping-fast fa-xs"></i> Freeship</span>`
      : `<span class="badge badge-warning"${s}><i class="fas fa-motorcycle fa-xs"></i> Khách chịu ship</span>`;
  } catch (err) {
    console.error('getShippingBadge error:', err);
    const s = extraStyle ? ` style="${extraStyle}"` : '';
    return `<span class="badge badge-warning"${s}><i class="fas fa-motorcycle fa-xs"></i> Khách chịu ship</span>`;
  }
}

let customerOrderCountMap = {};
let customerVIPMap = {};
let customerHistoryMap = {};

function isWaitingInternal_(s) {
  const l = String(s || '').toLowerCase();
  return l.includes('đợi') || l.includes('ck') || l.includes('chờ') || l.includes('thanh toán');
}

function normalizeCustomerPhone_(value) {
  return String(value || '').replace(/[^\d]/g, '').replace(/^84/, '0');
}

function getCustomerKey_(name, phoneInput) {
  const phone = normalizeCustomerPhone_(phoneInput);
  const cleanName = String(name || '').trim().toLowerCase();
  if (phone.length >= 8) return 'phone:' + phone;
  if (cleanName) return 'name:' + cleanName;
  return '';
}

function isRevenueOrder_(row) {
  const tt = row ? row.trangThai : '';
  return isSoldInternal_(tt) || isWaitingInternal_(tt) || row?.sourceSheet === 'THANH LÝ' || row?.sheetName === 'THANH LÝ';
}

function getCustomerOrderDate_(row) {
  return String(row?.ngayChot || row?.updatedAt || row?.createdAt || '').trim();
}

function compareCustomerOrders_(a, b) {
  return getCustomerOrderDate_(b).localeCompare(getCustomerOrderDate_(a));
}

function getCustomerRowsPool_() {
  const seen = {};
  return [...(allReportRows || []), ...(allRows || [])].filter(row => {
    if (!row) return false;
    const key = [
      row.sourceSheet || row.sheetName || 'SalesData',
      row.rowIndex || '',
      row.maSP || '',
      row.ngayChot || ''
    ].join('|');
    if (seen[key]) return false;
    seen[key] = true;
    return true;
  });
}

function getCustomerInitials_(name) {
  const clean = String(name || '').trim();
  if (!clean) return 'KH';
  const parts = clean.split(/\s+/).filter(Boolean);
  const first = parts[0] ? parts[0][0] : '';
  const last = parts.length > 1 ? parts[parts.length - 1][0] : '';
  return (first + last).toUpperCase();
}

function normalizeCustomerSignalText_(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'd')
    .toLowerCase();
}

function getCustomerVipTier_(ltv, orderCount) {
  const safeLtv = Number(ltv || 0);
  return CUSTOMER_VIP_TIERS.find(tier => safeLtv >= tier.minLtv) || {
    key: 'regular',
    label: 'Khách hàng Thường',
    minLtv: 0,
    minOrders: 0,
    className: 'vip-regular'
  };
}

function addCustomerTag_(hist, tag) {
  if (!hist || !tag) return;
  hist.tagMap[tag] = true;
}

function collectCustomerTagsFromRow_(hist, row, flags) {
  const sourceText = normalizeCustomerSignalText_([
    row.tenKhach,
    row.nguonKhach,
    row.ghiChu,
    row.diaChi
  ].join(' '));

  if (flags && flags.isDeleted) addCustomerTag_(hist, 'Bom hàng');
  if (sourceText.includes('bom') || sourceText.includes('boom') || sourceText.includes('hoan') ||
      sourceText.includes('huy') || sourceText.includes('tra hang') || sourceText.includes('tu choi nhan')) {
    addCustomerTag_(hist, 'Bom hàng');
  }
  if (sourceText.includes('kho tinh') || sourceText.includes('phan nan') || sourceText.includes('khieu nai') ||
      sourceText.includes('can than') || sourceText.includes('doi hoi')) {
    addCustomerTag_(hist, 'Khó tính');
  }
  if (sourceText.includes('dai ly') || sourceText.includes('daily') || sourceText.includes('agency')) {
    addCustomerTag_(hist, 'Đại lý');
  }
  if (sourceText.includes('ban si') || sourceText.includes('khach si') || sourceText.includes('lay si') ||
      sourceText.includes('si ') || sourceText.endsWith(' si') || sourceText.includes('wholesale')) {
    addCustomerTag_(hist, 'Sỉ');
  }
}

function getCustomerTags_(hist) {
  if (!hist) return [];
  const tags = Object.keys(hist.tagMap || {});
  const preferredOrder = ['VIP', 'Khách cũ', 'Đại lý', 'Sỉ', 'Khó tính', 'Bom hàng'];
  return preferredOrder.filter(tag => tags.includes(tag)).concat(tags.filter(tag => !preferredOrder.includes(tag)));
}

function getCustomerTagClass_(tag) {
  const key = normalizeCustomerSignalText_(tag).replace(/\s+/g, '-');
  if (key.includes('vip')) return 'customer-tag-vip';
  if (key.includes('bom')) return 'customer-tag-danger';
  if (key.includes('kho-tinh')) return 'customer-tag-warning';
  if (key.includes('dai-ly') || key.includes('si')) return 'customer-tag-info';
  if (key.includes('khach-cu')) return 'customer-tag-success';
  return '';
}

function renderCustomerTagsHtml_(tags) {
  if (!tags || !tags.length) {
    return '<span class="customer-tag customer-tag-muted">Chưa có tag</span>';
  }
  return tags.map(tag => `<span class="customer-tag ${getCustomerTagClass_(tag)}">${escapeHtml(tag)}</span>`).join('');
}

function buildCustomerHistoryMap() {
  customerOrderCountMap = {};
  customerVIPMap = {};
  customerHistoryMap = {};
  
  const rows = getCustomerRowsPool_();
  
  rows.forEach(r => {
    const tt = r.trangThai;
    const phone = normalizeCustomerPhone_(r.sdtKhach);
    const name = String(r.tenKhach || '').trim();
    const key = getCustomerKey_(name, phone);
    
    if (!key) return;
    
    customerOrderCountMap[key] = (customerOrderCountMap[key] || 0) + 1;
    
    const isSold = isSoldInternal_(tt);
    const isWaiting = isWaitingInternal_(tt);
    const isDeleted = isDeletedInternal_(tt);
    const isRevenue = isRevenueOrder_(r);

    if (isRevenue) {
      if (!customerVIPMap[key]) {
        customerVIPMap[key] = { count: 0, revenue: 0 };
      }
      customerVIPMap[key].count += 1;
      customerVIPMap[key].revenue += Number(r.giaBan || 0);
    }
    
    // Build rich customer profile data
    if (!customerHistoryMap[key]) {
      customerHistoryMap[key] = {
        name: name,
        phone: r.sdtKhach || '',
        totalOrders: 0,
        totalSpending: 0,
        totalProfit: 0,
        totalDeposit: 0,
        totalCod: 0,
        successfulOrders: 0,
        pendingOrders: 0,
        deletedOrders: 0,
        lastDate: '',
        firstDate: '',
        source: '',
        address: '',
        isVip: false,
        vipTier: null,
        tagMap: {},
        tags: [],
        orders: [],
        warnings: [],
        notes: []
      };
    }
    
    const hist = customerHistoryMap[key];
    if (!hist.name && name) hist.name = name;
    if (!hist.phone && r.sdtKhach) hist.phone = r.sdtKhach;
    if (!hist.source && r.nguonKhach) hist.source = r.nguonKhach;
    if (!hist.address && r.diaChi) hist.address = r.diaChi;
    collectCustomerTagsFromRow_(hist, r, { isDeleted });

    hist.totalOrders += 1;
    hist.orders.push(r);
    
    if (isRevenue) {
      hist.totalSpending += Number(r.giaBan || 0);
      hist.totalProfit += Number(r.tienLoi || 0);
      hist.totalDeposit += Number(r.khachCoc || 0);
      if (r.hinhThuc === 'COD') hist.totalCod += Number(r.tienCOD || 0);
    }

    if (isSold) hist.successfulOrders += 1;
    if (isWaiting) hist.pendingOrders += 1;
    if (isDeleted) hist.deletedOrders += 1;
    
    const orderDate = getCustomerOrderDate_(r);
    if (orderDate && (!hist.lastDate || orderDate > hist.lastDate)) {
      hist.lastDate = orderDate;
    }
    if (orderDate && (!hist.firstDate || orderDate < hist.firstDate)) {
      hist.firstDate = orderDate;
    }
    
    const note = String(r.ghiChu || '').trim();
    if (note) {
      const lowerNote = note.toLowerCase();
      hist.notes.push({
        maSP: r.maSP,
        ngayChot: r.ngayChot,
        note: note
      });

      const isImportant = lowerNote.includes('ship thứ 7') || lowerNote.includes('ship t7') ||
                          lowerNote.includes('giữ') || lowerNote.includes('hứa') ||
                          lowerNote.includes('gấp') || lowerNote.includes('hẹn') ||
                          lowerNote.includes('vip') || lowerNote.includes('bom') ||
                          lowerNote.includes('boom') || lowerNote.includes('hoàn') ||
                          lowerNote.includes('hoan') || lowerNote.includes('hủy') ||
                          lowerNote.includes('huy') || lowerNote.includes('trả') ||
                          lowerNote.includes('tra');
      if (isImportant) {
        hist.warnings.push({
          maSP: r.maSP,
          ngayChot: r.ngayChot,
          note: note,
          type: 'note'
        });
      }
    }

    if (isDeleted) {
      hist.warnings.push({
        maSP: r.maSP,
        ngayChot: r.ngayChot,
        note: 'Có đơn bị hủy/xóa trong lịch sử.',
        type: 'cancel'
      });
    }

    if (checkAnomaly(r)) {
      hist.warnings.push({
        maSP: r.maSP,
        ngayChot: r.ngayChot,
        note: 'COD = 0 nhưng cọc nhỏ hơn giá bán.',
        type: 'payment'
      });
    }

    if (isRevenue && !phone) {
      hist.warnings.push({
        maSP: r.maSP,
        ngayChot: r.ngayChot,
        note: 'Thiếu số điện thoại trên đơn.',
        type: 'missing'
      });
    }
  });
  
  for (let key in customerHistoryMap) {
    const hist = customerHistoryMap[key];
    const vipInfo = customerVIPMap[key];
    hist.orders.sort(compareCustomerOrders_);
    hist.notes = hist.notes.slice(0, 8);
    hist.warnings = hist.warnings.slice(0, 8);
    hist.avgOrderValue = hist.successfulOrders || hist.pendingOrders
      ? Math.round(hist.totalSpending / Math.max(1, hist.successfulOrders + hist.pendingOrders))
      : 0;
    hist.ltv = hist.totalSpending;
    hist.riskScore = Math.min(100, (hist.deletedOrders * 28) + (hist.warnings.length * 12) + (hist.pendingOrders * 4));
    hist.riskLevel = hist.riskScore >= 60 ? 'Cao' : hist.riskScore >= 25 ? 'Vừa' : 'Thấp';
    hist.vipTier = getCustomerVipTier_(hist.ltv, hist.successfulOrders + hist.pendingOrders);
    hist.isVip = hist.vipTier.key !== 'regular';
    if (hist.isVip) addCustomerTag_(hist, 'VIP');
    if (hist.totalOrders > 1) addCustomerTag_(hist, 'Khách cũ');
    hist.tags = getCustomerTags_(hist);
    if (vipInfo) vipInfo.tier = hist.vipTier;
  }
}

function getCustomerBadgeHtml(name, phoneInput) {
  const phone = normalizeCustomerPhone_(phoneInput);
  const cleanName = String(name || '').trim();
  const key = getCustomerKey_(cleanName, phone);
  
  if (!key) return '';
  
  let html = '';
  const count = customerOrderCountMap[key] || 0;
  const vipInfo = customerVIPMap[key];
  const vipTier = vipInfo && vipInfo.tier ? vipInfo.tier : getCustomerVipTier_(vipInfo?.revenue || 0, vipInfo?.count || 0);
  const isVip = vipTier.key !== 'regular';
  
  if (isVip) {
    const safeLabel = escapeHtml(vipTier.label);
    const countVal = vipInfo ? vipInfo.count : 0;
    const revVal = vipInfo ? vipInfo.revenue : 0;
    html += `<span class="vip-badge ${vipTier.className}" title="${safeLabel}: ${countVal} đơn chốt, LTV ${fmtVnd(revVal)}"><i class="fas fa-crown"></i> ${safeLabel} (${countVal}đ/${Math.round(revVal/1000)}k)</span>`;
  } else if (count > 1) {
    html += `<span class="repeat-badge" title="Đã mua ${count} lần">(${count} đơn)</span>`;
  }
  
  return html;
}

function isSoldInternal_(s) {
  const l = String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase().trim();
  if (l.includes('chua ban') || l.includes('chuaban') || l.includes('con hang')) return false;
  return l === 'da ban' || l.includes('da ban') || l === 'ban' || l === 'het hang';
}
function isDeletedInternal_(s) { return String(s || '').toLowerCase().includes('xóa'); }

function copyOrderToClipboard(rowIndex, sheetName) {
  const row = findEditableRowByIndex(rowIndex, sheetName);
  if (!row) return;
  
  const text = `Mã SP: ${row.maSP}\nKhách: ${row.tenKhach || 'Khách'}\nSĐT: ${row.sdtKhach || '—'}\nĐịa chỉ: ${row.diaChi || '—'}\nTiền COD: ${new Intl.NumberFormat('vi-VN').format(row.tienCOD)} ₫\nKhách cọc: ${new Intl.NumberFormat('vi-VN').format(row.khachCoc)} ₫\nGhi chú: ${row.ghiChu || '—'}`;
  
  navigator.clipboard.writeText(text).then(() => {
    showToast('Đã sao chép thông tin đơn hàng!', 'success');
  }).catch(() => {
    showToast('Lỗi sao chép!', 'error');
  });
}

function refreshAfterRowAction_(rowIndex, sheetName, patch) {
  const rowSheet = sheetName || 'SalesData';
  if (rowSheet === 'SalesData') {
    const idx = allRows.findIndex(r => Number(r.rowIndex) === Number(rowIndex));
    if (idx !== -1) allRows[idx] = Object.assign({}, allRows[idx], patch || {});
    filteredRows = [...allRows];
    applyFilters();
  }

  const dailyPage = document.getElementById('page-daily');
  if (dailyPage && !dailyPage.classList.contains('hidden')) loadDailyOrders();
}

function markAsShipped(rowIndex, sheetName) {
  const rowSheet = sheetName || 'SalesData';
  showLoading('Đang cập nhật trạng thái...');
  google.script.run
    .withSuccessHandler(res => {
      hideLoading();
      if (res && res.success) {
        refreshAfterRowAction_(rowIndex, rowSheet, { trangThai: 'Đã bán' });
        showToast('Đã đánh dấu Đã bán!', 'success');
      } else {
        showToast('Lỗi cập nhật!', 'error');
      }
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Lỗi: ' + e.message, 'error');
    })
    .quickUpdateRow(parseInt(rowIndex), { trangThai: 'Đã bán' }, rowSheet);
}

function markAsCancelled(rowIndex, sheetName) {
  const rowSheet = sheetName || 'SalesData';
  showLoading('Đang hủy đơn...');
  google.script.run
    .withSuccessHandler(res => {
      hideLoading();
      if (res && res.success) {
        refreshAfterRowAction_(rowIndex, rowSheet, { trangThai: 'Đã xóa' });
        showToast('Đã hủy đơn thành công!', 'success');
      } else {
        showToast('Lỗi cập nhật!', 'error');
      }
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Lỗi: ' + e.message, 'error');
    })
    .quickUpdateRow(parseInt(rowIndex), { trangThai: 'Đã xóa' }, rowSheet);
}

let sparklines = {};
function renderSparkline(canvasId, data, color) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;
  
  if (sparklines[canvasId]) {
    sparklines[canvasId].destroy();
  }
  
  sparklines[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array(data.length).fill(''),
      datasets: [{
        data: data,
        borderColor: color,
        borderWidth: 2.5,
        pointRadius: 0,
        tension: 0.4,
        fill: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { enabled: false }
      },
      scales: {
        x: { display: false },
        y: { display: false }
      }
    }
  });
}

function updateColumnVisibility() {
  const table = document.getElementById('products-table');
  if (!table) return;
  const wrapper = table.parentElement;
  if (!wrapper) return;
  
  const sdtChecked = document.getElementById('toggle-col-sdt')?.checked ?? true;
  const khoiluongChecked = document.getElementById('toggle-col-khoiluong')?.checked ?? true;
  const ghichuChecked = document.getElementById('toggle-col-ghichu')?.checked ?? true;
  const linktiktokChecked = document.getElementById('toggle-col-linktiktok')?.checked ?? true;
  const giavonChecked = document.getElementById('toggle-col-giavon')?.checked ?? true;
  
  wrapper.classList.toggle('hide-col-sdt', !sdtChecked);
  wrapper.classList.toggle('hide-col-khoiluong', !khoiluongChecked);
  wrapper.classList.toggle('hide-col-ghichu', !ghichuChecked);
  wrapper.classList.toggle('hide-col-linktiktok', !linktiktokChecked);
  wrapper.classList.toggle('hide-col-giavon', !giavonChecked);
  
  localStorage.setItem('col_visibility_sdt', sdtChecked);
  localStorage.setItem('col_visibility_khoiluong', khoiluongChecked);
  localStorage.setItem('col_visibility_ghichu', ghichuChecked);
  localStorage.setItem('col_visibility_linktiktok', linktiktokChecked);
  localStorage.setItem('col_visibility_giavon', giavonChecked);
}

function openCustomerProfileModal(name, phoneInput, allowFetch) {
  const modal = document.getElementById('customer-profile-modal');
  if (!modal) return;
  
  if (!Object.keys(customerHistoryMap || {}).length) buildCustomerHistoryMap();

  const phone = normalizeCustomerPhone_(phoneInput);
  const cleanName = String(name || '').trim();
  const key = getCustomerKey_(cleanName, phone);
  
  const hist = customerHistoryMap[key];
  if (!hist) {
    if (allowFetch !== false) {
      showToast('Đang tải Customer 360...', 'info', 1800);
      google.script.run
        .withSuccessHandler(rows => {
          allReportRows = rows || [];
          buildCustomerHistoryMap();
          openCustomerProfileModal(name, phoneInput, false);
        })
        .withFailureHandler(e => {
          showToast('Không tải được Customer 360: ' + e.message, 'error');
        })
        .getAllReportRows();
      return;
    }
    showToast('Không có dữ liệu chi tiết cho khách hàng này!', 'error');
    return;
  }
  
  const fmtMoney = n => new Intl.NumberFormat('vi-VN').format(n) + ' ₫';
  const fmtDate = d => {
    if (!d) return '—';
    const parts = d.split('-');
    if (parts.length === 3) return `${parts[2]}/${parts[1]}`;
    return d;
  };

  const pct = (value, total) => total ? Math.round((value / total) * 100) : 0;
  const revenueOrders = Math.max(1, hist.successfulOrders + hist.pendingOrders);
  const riskClass = hist.riskLevel === 'Cao' ? 'badge-danger' : hist.riskLevel === 'Vừa' ? 'badge-orange' : 'badge-success';
  
  document.getElementById('profile-name').textContent = hist.name || 'Khách ẩn danh';
  document.getElementById('profile-phone').textContent = hist.phone ? `SĐT: ${hist.phone}` : 'Không có SĐT';

  const avatar = document.getElementById('profile-avatar');
  if (avatar) avatar.textContent = getCustomerInitials_(hist.name);

  const sourceEl = document.getElementById('profile-source');
  if (sourceEl) sourceEl.textContent = 'Nguồn: ' + (hist.source || '—');
  const addressEl = document.getElementById('profile-address');
  if (addressEl) addressEl.textContent = 'Địa chỉ: ' + (hist.address || '—');
  
  const rankEl = document.getElementById('profile-rank');
  if (hist.isVip) {
    rankEl.className = `badge badge-warning ${hist.vipTier?.className || ''}`;
    rankEl.innerHTML = `<i class="fas fa-crown"></i> ${escapeHtml(hist.vipTier?.label || 'Khách VIP')}`;
  } else if (hist.totalOrders > 1) {
    rankEl.className = 'badge badge-info';
    rankEl.textContent = 'Khách quay lại';
  } else {
    rankEl.className = 'badge badge-secondary';
    rankEl.textContent = 'Khách hàng Thường';
  }

  const tagsList = document.getElementById('profile-tags-list');
  if (tagsList) tagsList.innerHTML = renderCustomerTagsHtml_(hist.tags || []);
  
  document.getElementById('profile-total-orders').textContent = hist.totalOrders;
  document.getElementById('profile-total-spending').textContent = fmtMoney(hist.totalSpending);
  const ltvEl = document.getElementById('profile-ltv');
  if (ltvEl) ltvEl.textContent = fmtMoney(hist.ltv || hist.totalSpending);
  const profitEl = document.getElementById('profile-total-profit');
  if (profitEl) {
    profitEl.textContent = (hist.totalProfit >= 0 ? '+' : '') + fmtMoney(hist.totalProfit);
    profitEl.className = hist.totalProfit >= 0 ? 'profit-positive' : 'profit-negative';
  }
  document.getElementById('profile-last-date').textContent = fmtDate(hist.lastDate);
  const riskEl = document.getElementById('profile-risk-score');
  if (riskEl) {
    riskEl.textContent = hist.riskLevel;
    riskEl.className = riskClass;
  }

  const infoList = document.getElementById('profile-info-list');
  if (infoList) {
    infoList.innerHTML = [
      ['SĐT', hist.phone || '—'],
      ['Hạng VIP', hist.vipTier?.label || 'Khách hàng Thường'],
      ['Nguồn chính', hist.source || '—'],
      ['Địa chỉ gần nhất', hist.address || '—'],
      ['Đơn đã bán', `${hist.successfulOrders} (${pct(hist.successfulOrders, hist.totalOrders)}%)`],
      ['Đơn chờ CK', `${hist.pendingOrders} (${pct(hist.pendingOrders, hist.totalOrders)}%)`],
      ['Đơn hủy/xóa', `${hist.deletedOrders} (${pct(hist.deletedOrders, hist.totalOrders)}%)`],
      ['Giá trị TB', fmtMoney(hist.avgOrderValue || 0)],
      ['Tổng cọc', fmtMoney(hist.totalDeposit || 0)],
      ['COD còn lại', fmtMoney(hist.totalCod || 0)],
      ['Lần đầu', fmtDate(hist.firstDate)],
      ['Lần gần nhất', fmtDate(hist.lastDate)]
    ].map(([label, value]) => `
      <div class="profile-info-item">
        <span>${label}</span>
        <strong>${value}</strong>
      </div>
    `).join('');
  }
  
  const warningsList = document.getElementById('profile-warnings-list');
  warningsList.innerHTML = '';
  
  if (hist.isVip) {
    warningsList.innerHTML += `
      <div class="profile-warning-item vip">
        <i class="fas fa-crown" style="color:gold;"></i>
        <span><b>Lưu ý:</b> ${escapeHtml(hist.vipTier?.label || 'Khách VIP')} có LTV ${fmtMoney(hist.ltv || 0)} và ${hist.successfulOrders + hist.pendingOrders} đơn. Ưu tiên phản hồi và giao hàng!</span>
      </div>
    `;
  }
  
  if (hist.warnings.length > 0) {
    hist.warnings.forEach(w => {
      warningsList.innerHTML += `
        <div class="profile-warning-item">
          <span><b>[Đơn ${w.maSP} - ${fmtDate(w.ngayChot)}]:</b> ${escapeHtml(w.note)}</span>
        </div>
      `;
    });
  } else if (!hist.isVip) {
    warningsList.innerHTML = '<div style="color:var(--text-muted); font-size:0.85rem; padding: 10px 0; text-align:center;">Không có ghi chú bất thường nào trong lịch sử</div>';
  }

  const riskList = document.getElementById('profile-risk-list');
  if (riskList) {
    if (hist.warnings.length) {
      riskList.innerHTML = hist.warnings.map(w => `
        <div class="profile-signal-item ${w.type || ''}">
          <span><b>${escapeHtml(w.maSP || 'Đơn')}</b> ${fmtDate(w.ngayChot)} - ${escapeHtml(w.note)}</span>
        </div>
      `).join('');
    } else {
      riskList.innerHTML = '<div class="profile-empty-line">Không có tín hiệu rủi ro đáng chú ý.</div>';
    }
  }

  const notesList = document.getElementById('profile-notes-list');
  if (notesList) {
    if (hist.notes.length) {
      notesList.innerHTML = hist.notes.map(n => `
        <div class="profile-signal-item note">
          <i class="fas fa-note-sticky"></i>
          <span><b>${escapeHtml(n.maSP || 'Đơn')}</b> ${fmtDate(n.ngayChot)} - ${escapeHtml(n.note)}</span>
        </div>
      `).join('');
    } else {
      notesList.innerHTML = '<div class="profile-empty-line">Chưa có ghi chú trong lịch sử mua.</div>';
    }
  }
  
  const tbody = document.getElementById('profile-orders-tbody');
  tbody.innerHTML = hist.orders.map(o => {
    const paySum = Number(o.khachCoc || 0) + (o.hinhThuc === 'COD' ? Number(o.tienCOD || 0) : 0);
    return `
      <tr>
        <td><b>${escapeHtml(o.maSP || '—')}</b></td>
        <td>${fmtDate(o.ngayChot)}</td>
        <td>${fmtMoney(o.giaBan)}</td>
        <td class="${Number(o.tienLoi || 0) >= 0 ? 'profit-positive' : 'profit-negative'}">${Number(o.tienLoi || 0) >= 0 ? '+' : ''}${fmtMoney(o.tienLoi)}</td>
        <td>${escapeHtml(o.hinhThuc || '—')}</td>
        <td>${getStatusBadge(o.trangThai, true)}</td>
      </tr>
    `;
  }).join('');
  
  // Save global customer identity for the Lucky Wheel
  wheelCustomerPhone = hist.phone;
  wheelCustomerName = hist.name;
  
  openModal('customer-profile-modal');
  
  // Initialize VIP components (Radar Chart & Lucky Wheel check)
  setTimeout(() => {
    initCustomerVIPModules(hist);
  }, 150);
}

function closeCustomerProfileModal() {
  closeModal('customer-profile-modal');
}

function initColumnVisibility() {
  const getStored = (key, def) => {
    const val = localStorage.getItem(key);
    return val !== null ? val === 'true' : def;
  };
  
  const sdtEl = document.getElementById('toggle-col-sdt');
  const khoiluongEl = document.getElementById('toggle-col-khoiluong');
  const ghichuEl = document.getElementById('toggle-col-ghichu');
  const linktiktokEl = document.getElementById('toggle-col-linktiktok');
  const giavonEl = document.getElementById('toggle-col-giavon');
  
  if (sdtEl) sdtEl.checked = getStored('col_visibility_sdt', true);
  if (khoiluongEl) khoiluongEl.checked = getStored('col_visibility_khoiluong', true);
  if (ghichuEl) ghichuEl.checked = getStored('col_visibility_ghichu', true);
  if (linktiktokEl) linktiktokEl.checked = getStored('col_visibility_linktiktok', true);
  if (giavonEl) giavonEl.checked = getStored('col_visibility_giavon', true);
  
  updateColumnVisibility();
}

// ─────────────────────────────────────────────
// THEME SWITCHER (Light/Dark Mode)
// ──────────────────────────────────────────────
function initTheme() {
  const savedTheme = localStorage.getItem('sales_admin_theme') || 'dark';
  const body = document.body;
  const icon = document.getElementById('theme-toggle-icon');
  
  if (savedTheme === 'light') {
    body.classList.add('light-theme');
    if (icon) {
      icon.className = 'fas fa-sun';
      icon.style.color = '#eab308';
    }
  } else {
    body.classList.remove('light-theme');
    if (icon) {
      icon.className = 'fas fa-moon';
      icon.style.color = '';
    }
  }
}

function toggleTheme() {
  const body = document.body;
  const icon = document.getElementById('theme-toggle-icon');
  
  if (body.classList.contains('light-theme')) {
    body.classList.remove('light-theme');
    localStorage.setItem('sales_admin_theme', 'dark');
    if (icon) {
      icon.className = 'fas fa-moon';
      icon.style.color = '';
    }
    showToast('Đã chuyển sang giao diện Tối!', 'info');
  } else {
    body.classList.add('light-theme');
    localStorage.setItem('sales_admin_theme', 'light');
    if (icon) {
      icon.className = 'fas fa-sun';
      icon.style.color = '#eab308';
    }
    showToast('Đã chuyển sang giao diện Sáng!', 'info');
  }
}

// ─────────────────────────────────────────────
// ACTIVITY LOGS PAGE
// ─────────────────────────────────────────────
let allActivityLogs = [];
let filteredActivityLogs = [];

function loadActivityLogs() {
  showLoading('Đang tải nhật ký hoạt động...');
  google.script.run
    .withSuccessHandler(logs => {
      hideLoading();
      allActivityLogs = logs || [];
      filteredActivityLogs = [...allActivityLogs];
      applyActivityFilters();
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Lỗi tải nhật ký hoạt động: ' + e.message, 'error');
    })
    .getActivityLogs();
}

function renderActivityLogs(logs) {
  const tbody = document.getElementById('activity-tbody');
  const emptyState = document.getElementById('empty-state-activity');
  const countLabel = document.getElementById('activity-count-label');
  
  if (countLabel) countLabel.textContent = `${logs.length} hoạt động`;
  
  if (!logs || !logs.length) {
    tbody.innerHTML = '';
    emptyState.classList.remove('hidden');
    return;
  }
  
  emptyState.classList.add('hidden');
  tbody.innerHTML = logs.map(l => {
    const timeStr = l.time ? String(l.time) : '—';
    const rowStr = l.rowIndex ? String(l.rowIndex) : '—';
    const actionClass = getActionClass(l.action);
    return `
      <tr>
        <td style="color: var(--text-secondary); font-size: 0.85rem;">${escapeHtml(timeStr)}</td>
        <td>${escapeHtml(rowStr)}</td>
        <td><strong style="color: var(--primary-light);">${escapeHtml(l.maSP || '—')}</strong></td>
        <td><span class="badge ${actionClass}">${escapeHtml(l.action || '—')}</span></td>
        <td style="font-size: 0.875rem; text-align: left; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(l.details || '')}">${escapeHtml(l.details || '—')}</td>
      </tr>
    `;
  }).join('');
}

function getActionClass(action) {
  const act = String(action || '').trim();
  if (act.includes('Thêm')) return 'badge-success';
  if (act.includes('Xóa')) return 'badge-danger';
  if (act.includes('Lỗi')) return 'badge-danger';
  if (act.includes('Cập nhật')) return 'badge-info';
  return 'badge-secondary';
}

function applyActivityFilters() {
  const q = String(document.getElementById('activity-search-input')?.value || '').toLowerCase().trim();
  const act = document.getElementById('activity-action-filter')?.value || '';
  
  filteredActivityLogs = allActivityLogs.filter(l => {
    const matchQ = !q || 
      (l.maSP && l.maSP.toLowerCase().includes(q)) || 
      (l.action && l.action.toLowerCase().includes(q)) || 
      (l.details && l.details.toLowerCase().includes(q));
    const matchAct = !act || (l.action && l.action === act);
    return matchQ && matchAct;
  });
  
  renderActivityLogs(filteredActivityLogs);
}

function clearActivityFilters() {
  const input = document.getElementById('activity-search-input');
  const filter = document.getElementById('activity-action-filter');
  if (input) input.value = '';
  if (filter) filter.value = '';
  applyActivityFilters();
}

// ─────────────────────────────────────────────
// SYSTEM SETTINGS PAGE
// ─────────────────────────────────────────────
let cachedSystemSettings = null;

function loadSystemSettings() {
  showLoading('Đang tải cấu hình...');
  google.script.run
    .withSuccessHandler(settings => {
      hideLoading();
      cachedSystemSettings = settings;
      if (settings) {
        document.getElementById('settings-tg-token').value = settings.telegramBotToken || '';
        document.getElementById('settings-tg-chatid').value = settings.telegramChatId || '';
        document.getElementById('settings-gemini-key').value = settings.geminiApiKey || '';
        document.getElementById('settings-gemini-model').value = settings.geminiModel || 'gemini-3.5-flash';
      }
    })
    .withFailureHandler(e => {
      hideLoading();
      showToast('Lỗi tải cấu hình: ' + e.message, 'error');
    })
    .getSystemSettings();
}

function saveTelegramSettings(e) {
  e.preventDefault();
  const token = document.getElementById('settings-tg-token').value.trim();
  const chatId = document.getElementById('settings-tg-chatid').value.trim();
  
  const btn = document.getElementById('btn-save-tg');
  btn.disabled = true;
  btn.textContent = 'Đang lưu...';
  
  const settings = {
    telegramBotToken: token,
    telegramChatId: chatId,
    geminiApiKey: document.getElementById('settings-gemini-key').value.trim(),
    geminiModel: document.getElementById('settings-gemini-model').value
  };
  
  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.textContent = 'Lưu cấu hình Telegram';
      showToast('Lưu cấu hình Telegram thành công!', 'success');
      cachedSystemSettings = settings;
    })
    .withFailureHandler(e => {
      btn.disabled = false;
      btn.textContent = 'Lưu cấu hình Telegram';
      showToast('Lỗi lưu cấu hình: ' + e.message, 'error');
    })
    .saveSystemSettings(settings);
}

function saveGeminiSettings(e) {
  e.preventDefault();
  const key = document.getElementById('settings-gemini-key').value.trim();
  const model = document.getElementById('settings-gemini-model').value;
  
  const btn = document.getElementById('btn-save-gemini');
  btn.disabled = true;
  btn.textContent = 'Đang lưu...';
  
  const settings = {
    telegramBotToken: document.getElementById('settings-tg-token').value.trim(),
    telegramChatId: document.getElementById('settings-tg-chatid').value.trim(),
    geminiApiKey: key,
    geminiModel: model
  };
  
  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.textContent = 'Lưu cấu hình Gemini';
      showToast('Lưu cấu hình Gemini thành công!', 'success');
      cachedSystemSettings = settings;
    })
    .withFailureHandler(e => {
      btn.disabled = false;
      btn.textContent = 'Lưu cấu hình Gemini';
      showToast('Lỗi lưu cấu hình: ' + e.message, 'error');
    })
    .saveSystemSettings(settings);
}

function testTelegramIntegration() {
  const btn = document.getElementById('btn-test-tg');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang gửi...';
  
  google.script.run
    .withSuccessHandler(success => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Gửi thử tin nhắn test';
      if (success) {
        showToast('Đã gửi tin nhắn kiểm tra tới Telegram của bạn!', 'success');
      } else {
        showToast('Gửi tin nhắn test thất bại! Hãy lưu cấu hình Telegram trước hoặc kiểm tra token/chatId.', 'error');
      }
    })
    .withFailureHandler(e => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-paper-plane"></i> Gửi thử tin nhắn test';
      showToast('Lỗi kết nối kiểm tra: ' + e.message, 'error');
    })
    .testTelegramNotify();
}

function triggerManualBackup() {
  const btn = document.getElementById('btn-trigger-backup');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang sao lưu...';
  
  google.script.run
    .withSuccessHandler(res => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-copy"></i> Tạo bản sao lưu ngay bây giờ';
      if (res && res.success) {
        showToast(`Sao lưu thành công! File: ${res.fileName} trong thư mục ${res.folderName}`, 'success');
      } else {
        showToast('Sao lưu thất bại: ' + (res ? res.error : 'Lỗi không rõ'), 'error');
      }
    })
    .withFailureHandler(e => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fas fa-copy"></i> Tạo bản sao lưu ngay bây giờ';
      showToast('Lỗi thực hiện sao lưu: ' + e.message, 'error');
    })
    .createBackupSpreadsheet();
}

// ============================================================
// VIP FEATURES: RADAR CHART, AI PREDICTOR & LUCKY WHEEL
// ============================================================

let profileRadarChartInstance = null;
let wheelCustomerPhone = '';
let wheelCustomerName = '';
let currentAngle = 0;
let isSpinning = false;

const wheelPrizes = [
  "Voucher 20k",
  "Voucher 50k",
  "May mắn",
  "Voucher 100k",
  "Free Ship",
  "Quà Cốc ANTA"
];

const wheelColors = [
  "#7c3aed", // Purple
  "#3b82f6", // Blue
  "#475569", // Slate
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#f43f5e"  // Rose
];

function initCustomerVIPModules(hist) {
  // 1. Render Radar Chart and Prediction
  renderCustomerRadarAndPredictor(hist);

  // 2. Initialize Lucky Wheel Gacha UI
  const btn = document.getElementById('btn-spin-wheel');
  const info = document.getElementById('lucky-wheel-info');
  const wheelMascotContainer = document.getElementById('wheel-mascot-container');
  if (!btn || !info) return;

  btn.disabled = true;
  info.textContent = 'Đang kiểm tra lượt quay...';
  
  if (wheelMascotContainer) {
    wheelMascotContainer.innerHTML = getMascotSvg('idle');
  }

  // Set initial canvas drawing
  drawLuckyWheel(currentAngle);

  if (!hist.phone) {
    info.innerHTML = '<span style="color:var(--text-muted);"><i class="fas fa-info-circle"></i> Thiếu số điện thoại để quay thưởng.</span>';
    if (wheelMascotContainer) {
      wheelMascotContainer.innerHTML = getMascotSvg('sad');
    }
    return;
  }

  google.script.run
    .withSuccessHandler(res => {
      if (res && res.success && res.available) {
        btn.disabled = false;
        info.innerHTML = `<span style="color:var(--success);"><i class="fas fa-check-circle"></i> Có 1 lượt quay tháng này!</span><br><span style="font-size:0.75rem;color:var(--text-muted);">${res.vipLabel} | Hạng tích lũy đơn: ${res.totalOrders}</span>`;
        if (wheelMascotContainer) {
          wheelMascotContainer.innerHTML = getMascotSvg('happy');
        }
      } else {
        btn.disabled = true;
        info.innerHTML = `<span style="color:var(--text-muted); font-size:0.8rem;"><i class="fas fa-lock"></i> ${res.reason || 'Chưa đủ điều kiện'}</span>`;
        if (wheelMascotContainer) {
          wheelMascotContainer.innerHTML = getMascotSvg('sad');
        }
      }
    })
    .withFailureHandler(err => {
      btn.disabled = true;
      info.textContent = 'Lỗi kiểm tra lượt quay: ' + err.message;
      if (wheelMascotContainer) {
        wheelMascotContainer.innerHTML = getMascotSvg('sad');
      }
    })
    .checkCustomerWheelAvailability(hist.phone);
}

function renderCustomerRadarAndPredictor(hist) {
  // Calculate Radar Axes Score (1-5 scale)
  // F (Frequency): total orders
  const F = Math.min(5, Math.max(1, Math.ceil(hist.totalOrders / 2.5)));
  // M (Monetary): total spending (LTV)
  const M = hist.totalSpending >= 100000000 ? 5 : hist.totalSpending >= 50000000 ? 4 : hist.totalSpending >= 20000000 ? 3 : hist.totalSpending >= 5000000 ? 2 : 1;
  // R (Recency): how recent was the last order
  let R = 1;
  if (hist.lastDate) {
    const diffDays = Math.round((new Date() - new Date(hist.lastDate)) / (24 * 60 * 60 * 1000));
    if (diffDays <= 10) R = 5;
    else if (diffDays <= 30) R = 4;
    else if (diffDays <= 90) R = 3;
    else if (diffDays <= 180) R = 2;
  }
  // Rel (Reliability): successful order ratio
  const successRate = hist.totalOrders > 0 ? (hist.successfulOrders / hist.totalOrders) : 0;
  const Rel = Math.min(5, Math.max(1, Math.round(successRate * 5)));
  // Safety: anti-boom score (derived from inverse risk score)
  const safety = Math.min(5, Math.max(1, Math.round((100 - hist.riskScore) / 20)));

  const radarCtx = document.getElementById('profile-radar-chart');
  if (!radarCtx) return;

  if (profileRadarChartInstance) {
    profileRadarChartInstance.destroy();
  }

  // Set default configurations matching dark/light themes
  const isLight = document.body.classList.contains('light-theme');
  const labelColor = isLight ? '#475569' : '#cbd5e1';
  const gridColor = isLight ? 'rgba(15,23,42,0.06)' : 'rgba(255,255,255,0.06)';

  profileRadarChartInstance = new Chart(radarCtx, {
    type: 'radar',
    data: {
      labels: ['Tần suất', 'Chi tiêu', 'Độ mới', 'Tỷ lệ nhận', 'Độ an toàn'],
      datasets: [{
        label: 'Khách hàng',
        data: [F, M, R, Rel, safety],
        backgroundColor: isLight ? 'rgba(99, 102, 241, 0.15)' : 'rgba(167, 139, 250, 0.15)',
        borderColor: isLight ? 'rgba(99, 102, 241, 0.85)' : 'rgba(167, 139, 250, 0.85)',
        borderWidth: 2,
        pointBackgroundColor: isLight ? '#6366f1' : '#a78bfa',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: isLight ? '#6366f1' : '#a78bfa'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        r: {
          angleLines: { color: gridColor },
          grid: { color: gridColor },
          pointLabels: { color: labelColor, font: { family: 'Inter', size: 9, weight: 'bold' } },
          ticks: { display: false },
          min: 0,
          max: 5
        }
      }
    }
  });

  // Calculate purchase intervals and predict next purchase date
  let nextDateStr = 'Cần thêm đơn hàng thứ 2';
  let suggestedSp = 'Chưa đủ lịch sử giày';

  const revenueOrders = hist.orders
    .filter(o => isRevenueOrder_(o) && o.ngayChot)
    .sort((a, b) => String(a.ngayChot).localeCompare(String(b.ngayChot)));

  if (revenueOrders.length >= 2) {
    let totalDiffDays = 0;
    for (let i = 1; i < revenueOrders.length; i++) {
      const d1 = new Date(revenueOrders[i - 1].ngayChot);
      const d2 = new Date(revenueOrders[i].ngayChot);
      const diff = Math.max(1, Math.round((d2 - d1) / (24 * 60 * 60 * 1000)));
      totalDiffDays += diff;
    }
    const avgInterval = Math.round(totalDiffDays / (revenueOrders.length - 1));
    
    const lastOrderDate = new Date(revenueOrders[revenueOrders.length - 1].ngayChot);
    const predictedDate = new Date(lastOrderDate.getTime() + avgInterval * 24 * 60 * 60 * 1000);
    
    const year = predictedDate.getFullYear();
    const month = String(predictedDate.getMonth() + 1).padStart(2, '0');
    const day = String(predictedDate.getDate()).padStart(2, '0');
    nextDateStr = `${day}/${month}/${year} (Chu kỳ ~${avgInterval} ngày)`;
  } else if (revenueOrders.length === 1) {
    nextDateStr = 'Cần thêm đơn hàng thứ 2 để dự báo';
  }

  // Guess best shoe models based on previous orders
  const spCounts = {};
  revenueOrders.forEach(o => {
    const code = String(o.maSP || '').trim();
    if (code) {
      const base = code.split('-')[0].toUpperCase();
      spCounts[base] = (spCounts[base] || 0) + 1;
    }
  });
  let bestBase = '';
  let maxCount = 0;
  for (let base in spCounts) {
    if (spCounts[base] > maxCount) {
      maxCount = spCounts[base];
      bestBase = base;
    }
  }
  if (bestBase) {
    suggestedSp = `Dòng ANTA ${bestBase}`;
  }

  document.getElementById('pred-next-date').textContent = nextDateStr;
  document.getElementById('pred-suggested-sp').textContent = suggestedSp;
}

function drawLuckyWheel(angle) {
  const canvas = document.getElementById('lucky-wheel-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const center = size / 2;
  const radius = center - 10;
  
  ctx.clearRect(0, 0, size, size);

  // Outer glossy ring
  ctx.beginPath();
  ctx.arc(center, center, radius + 4, 0, 2 * Math.PI);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 6;
  ctx.stroke();

  const sliceAngle = (2 * Math.PI) / wheelPrizes.length;

  for (let i = 0; i < wheelPrizes.length; i++) {
    const startAngle = angle + i * sliceAngle;
    const endAngle = startAngle + sliceAngle;

    // Draw segment slice
    ctx.beginPath();
    ctx.moveTo(center, center);
    ctx.arc(center, center, radius, startAngle, endAngle);
    ctx.closePath();
    ctx.fillStyle = wheelColors[i];
    ctx.fill();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw text segment label
    ctx.save();
    ctx.translate(center, center);
    ctx.rotate(startAngle + sliceAngle / 2);
    ctx.textAlign = 'right';
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 11px Inter, system-ui, sans-serif';
    
    // Draw text drop shadow
    ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
    ctx.shadowBlur = 4;
    ctx.shadowOffsetX = 1;
    ctx.shadowOffsetY = 1;

    ctx.fillText(wheelPrizes[i], radius - 18, 4);
    ctx.restore();
  }

  // Draw central inner pin
  ctx.beginPath();
  ctx.arc(center, center, 24, 0, 2 * Math.PI);
  ctx.fillStyle = '#ffffff';
  ctx.shadowColor = 'rgba(0,0,0,0.15)';
  ctx.shadowBlur = 8;
  ctx.fill();
  
  ctx.beginPath();
  ctx.arc(center, center, 18, 0, 2 * Math.PI);
  ctx.strokeStyle = 'rgba(0,0,0,0.06)';
  ctx.lineWidth = 2;
  ctx.stroke();
}

function spinLoyaltyWheel() {
  if (isSpinning || !wheelCustomerPhone) return;

  const btn = document.getElementById('btn-spin-wheel');
  const info = document.getElementById('lucky-wheel-info');
  const wheelMascotContainer = document.getElementById('wheel-mascot-container');
  btn.disabled = true;
  isSpinning = true;
  info.innerHTML = '<span style="color:var(--primary-light);"><i class="fas fa-spinner fa-spin"></i> Đang tính toán giải thưởng...</span>';
  
  if (wheelMascotContainer) {
    wheelMascotContainer.innerHTML = getMascotSvg('thinking');
  }

  google.script.run
    .withSuccessHandler(res => {
      if (res && res.success) {
        info.innerHTML = '<span style="color:#fbbf24;"><i class="fas fa-sync fa-spin"></i> Đang quay vòng quay...</span>';
        
        // Trigger wheel animation based on index
        animateWheelSpin(res.winnerIndex, () => {
          // Play confetti
          showCustomConfetti();
          
          // Display reward information
          info.innerHTML = `<strong style="color:#fbbf24; font-size:0.95rem;"><i class="fas fa-trophy"></i> Trúng: ${res.winnerLabel}</strong><br><span style="font-size:0.75rem;color:var(--text-muted);">Đã lưu vào Ghi chú đơn cuối của khách trên Google Sheet!</span>`;
          showToast(`Chúc mừng! Trúng giải: ${res.winnerLabel}`, 'success', 5000);

          if (wheelMascotContainer) {
            const label = String(res.winnerLabel || '').toLowerCase();
            if (label.includes('may mắn') || label.includes('sau')) {
              wheelMascotContainer.innerHTML = getMascotSvg('sad');
            } else {
              wheelMascotContainer.innerHTML = getMascotSvg('happy');
            }
          }

          // Force background updates to reload cache
          const key = getCustomerKey_(wheelCustomerName, wheelCustomerPhone);
          google.script.run
            .withSuccessHandler(rows => {
              allReportRows = rows || [];
              buildCustomerHistoryMap();
              
              // If the profile modal is still open, refresh order history table to show updated notes
              const updatedHist = customerHistoryMap[key];
              if (updatedHist) {
                const tbody = document.getElementById('profile-orders-tbody');
                if (tbody) {
                  tbody.innerHTML = updatedHist.orders.map(o => {
                    return `
                      <tr>
                        <td><b>${escapeHtml(o.maSP || '—')}</b></td>
                        <td>${fmtDate(o.ngayChot)}</td>
                        <td>${fmtMoney(o.giaBan)}</td>
                        <td class="${Number(o.tienLoi || 0) >= 0 ? 'profit-positive' : 'profit-negative'}">${Number(o.tienLoi || 0) >= 0 ? '+' : ''}${fmtMoney(o.tienLoi)}</td>
                        <td>${escapeHtml(o.hinhThuc || '—')}</td>
                        <td>${getStatusBadge(o.trangThai, true)}</td>
                      </tr>
                    `;
                  }).join('');
                }
              }
            })
            .getAllReportRows();
        });
      } else {
        isSpinning = false;
        btn.disabled = false;
        info.innerHTML = `<span style="color:var(--danger); font-size:0.8rem;"><i class="fas fa-times-circle"></i> Lỗi: ${res.error || 'Yêu cầu thất bại'}</span>`;
        showToast(res.error || 'Quay thưởng thất bại.', 'error');
        if (wheelMascotContainer) {
          wheelMascotContainer.innerHTML = getMascotSvg('sad');
        }
      }
    })
    .withFailureHandler(err => {
      isSpinning = false;
      btn.disabled = false;
      info.innerHTML = `<span style="color:var(--danger); font-size:0.8rem;"><i class="fas fa-times-circle"></i> Lỗi kết nối: ${err.message}</span>`;
      showToast('Lỗi: ' + err.message, 'error');
      if (wheelMascotContainer) {
        wheelMascotContainer.innerHTML = getMascotSvg('sad');
      }
    })
    .spinLoyaltyWheelBackend(wheelCustomerPhone, wheelCustomerName);
}

function animateWheelSpin(winnerIndex, onComplete) {
  const sliceCount = wheelPrizes.length;
  const sliceAngle = (2 * Math.PI) / sliceCount;
  
  // Angle calculations: Arrow is pointing down at top center (-Math.PI/2)
  const baseAngle = -Math.PI / 2 - winnerIndex * sliceAngle - sliceAngle / 2;
  const spins = 6;
  const targetAngle = baseAngle + 2 * Math.PI * spins;
  
  const startAngle = currentAngle % (2 * Math.PI);
  const distance = targetAngle - startAngle;
  const duration = 4200; // 4.2 seconds
  const startTimestamp = performance.now();

  function tick(timestamp) {
    const elapsed = timestamp - startTimestamp;
    const progress = Math.min(elapsed / duration, 1);
    
    // Cubic ease-out
    const easeProgress = 1 - Math.pow(1 - progress, 3);
    
    currentAngle = startAngle + distance * easeProgress;
    drawLuckyWheel(currentAngle);

    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      isSpinning = false;
      onComplete();
    }
  }

  requestAnimationFrame(tick);
}

function showCustomConfetti() {
  const canvas = document.createElement('canvas');
  canvas.style.position = 'fixed';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '999999';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let width = canvas.width = window.innerWidth;
  let height = canvas.height = window.innerHeight;

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const colors = ['#f43f5e', '#3b82f6', '#10b981', '#fbbf24', '#7c3aed', '#06b6d4'];
  const confettiCount = 100;
  const particles = Array(confettiCount).fill(0).map(() => ({
    x: Math.random() * width,
    y: Math.random() * height - height,
    r: Math.random() * 6 + 4,
    d: Math.random() * height,
    color: colors[Math.floor(Math.random() * colors.length)],
    tilt: Math.random() * 10 - 5,
    tiltAngleIncremental: Math.random() * 0.08 + 0.02,
    tiltAngle: 0
  }));

  const startTime = Date.now();
  let animationId;

  function render() {
    ctx.clearRect(0, 0, width, height);
    let hasRunning = false;

    particles.forEach(p => {
      p.tiltAngle += p.tiltAngleIncremental;
      p.y += (Math.cos(p.d) + 3 + p.r / 2) / 2;
      p.x += Math.sin(p.tiltAngle);
      p.tilt = Math.sin(p.tiltAngle - (p.r / 3)) * 12;

      if (p.y < height) {
        hasRunning = true;
      }

      ctx.beginPath();
      ctx.lineWidth = p.r;
      ctx.strokeStyle = p.color;
      ctx.moveTo(p.x + p.tilt + p.r / 2, p.y);
      ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r / 2);
      ctx.stroke();
    });

    if (hasRunning && Date.now() - startTime < 3800) {
      animationId = requestAnimationFrame(render);
    } else {
      cancelAnimationFrame(animationId);
      canvas.remove();
    }
  }

  render();
}

// ─────────────────────────────────────────────
// NOTIFICATION CENTER CLIENT (Module 9)
// ─────────────────────────────────────────────
let allNotifications = [];
let readNotifications = [];

try {
  readNotifications = JSON.parse(localStorage.getItem('read_notifications') || '[]');
} catch (e) {
  readNotifications = [];
}

function toggleNotificationDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById('notification-dropdown');
  if (dropdown) {
    dropdown.classList.toggle('hidden');
  }
}

function renderNotifications(notifications) {
  if (notifications) allNotifications = notifications;
  
  const bodyEl = document.getElementById('notification-body');
  const badgeEl = document.getElementById('notification-badge');
  const bellBtn = document.querySelector('.btn-notification');
  
  if (!bodyEl) return;
  
  // Clean up read list by keeping only active notification IDs
  const activeIds = allNotifications.map(n => n.id);
  readNotifications = readNotifications.filter(id => activeIds.includes(id));
  try {
    localStorage.setItem('read_notifications', JSON.stringify(readNotifications));
  } catch (e) {}

  // Filter list
  const filterType = document.getElementById('notification-filter-type')?.value || '';
  const filtered = allNotifications.filter(n => {
    return !filterType || n.type === filterType;
  });
  
  // Calculate unread count
  const unreadCount = allNotifications.filter(n => !readNotifications.includes(n.id)).length;
  
  // Update badge
  if (badgeEl && bellBtn) {
    if (unreadCount > 0) {
      badgeEl.textContent = unreadCount;
      badgeEl.classList.remove('hidden');
      
      const prevUnread = parseInt(bellBtn.dataset.unread || '0', 10);
      if (unreadCount > prevUnread) {
        bellBtn.classList.add('shake');
        setTimeout(() => bellBtn.classList.remove('shake'), 600);
      }
      bellBtn.dataset.unread = unreadCount;
    } else {
      badgeEl.classList.add('hidden');
      bellBtn.dataset.unread = '0';
    }
  }
  
  if (filtered.length === 0) {
    bodyEl.innerHTML = `
      <div class="notification-empty">
        <i class="fas fa-bell-slash"></i>
        <span>Không có cảnh báo nào.</span>
      </div>
    `;
    return;
  }
  
  const iconMap = {
    wait_ck: 'fa-money-bill-wave',
    late_ship: 'fa-shipping-fast',
    cod_reconcile: 'fa-file-invoice-dollar',
    call_back: 'fa-phone-volume',
    low_stock: 'fa-boxes',
    late_task: 'fa-tasks',
    rev_decrease: 'fa-chart-line',
    vip_order: 'fa-crown',
    order_cancelled: 'fa-ban',
    backup_fail: 'fa-exclamation-triangle'
  };
  
  bodyEl.innerHTML = filtered.map(item => {
    const isRead = readNotifications.includes(item.id);
    const icon = iconMap[item.type] || 'fa-bell';
    const dateStr = item.date ? item.date : '';
    
    return `
      <div class="notification-item type-${item.type} ${isRead ? '' : 'unread'}" 
           onclick="handleNotificationClick('${item.id}')">
        <div class="notification-icon-wrapper">
          <i class="fas ${icon}"></i>
        </div>
        <div class="notification-content">
          <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
            <span class="notification-title">${item.title}</span>
            ${isRead ? '' : `<button class="btn-mark-single-read" onclick="markAsRead('${item.id}', event)" title="Đánh dấu đã đọc" style="font-size:0.7rem; color:var(--text-muted); background:none; border:none; padding:2px 4px; cursor:pointer;"><i class="fas fa-check"></i></button>`}
          </div>
          <p class="notification-msg">${item.message}</p>
          <div class="notification-time">
            <i class="far fa-clock"></i>
            <span>${dateStr}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function markAsRead(id, event) {
  if (event) event.stopPropagation();
  if (!readNotifications.includes(id)) {
    readNotifications.push(id);
    try {
      localStorage.setItem('read_notifications', JSON.stringify(readNotifications));
    } catch (e) {}
    renderNotifications();
  }
}

function markAllNotificationsAsRead() {
  allNotifications.forEach(n => {
    if (!readNotifications.includes(n.id)) {
      readNotifications.push(n.id);
    }
  });
  try {
    localStorage.setItem('read_notifications', JSON.stringify(readNotifications));
  } catch (e) {}
  renderNotifications();
  showToast('Đã đánh dấu tất cả thông báo là đã đọc!', 'success');
}

function filterNotifications() {
  renderNotifications();
}

function handleNotificationClick(id) {
  const item = allNotifications.find(n => n.id === id);
  if (!item) return;
  
  markAsRead(id);
  
  if (item.type === 'late_task') {
    document.getElementById('task-detail-name').textContent = item.taskName || 'Không tên';
    document.getElementById('task-detail-deadline').textContent = item.deadline || 'Không có';
    document.getElementById('task-detail-status').textContent = item.status || 'Chưa hoàn thành';
    document.getElementById('task-detail-assignee').textContent = item.assignee || 'Chủ shop';
    document.getElementById('task-detail-desc').textContent = item.desc || 'Không có mô tả chi tiết.';
    openModal('modal-task-detail');
  } 
  else if (item.type === 'vip_order' || item.type === 'call_back') {
    openCustomerProfileModal(item.tenKhach, item.sdtKhach);
  }
  else if (item.maSP) {
    switchPage('search', document.getElementById('nav-search'));
    const searchInput = document.getElementById('search-masp-input');
    if (searchInput) {
      searchInput.value = item.maSP;
      doSearchMaSP();
    }
  }
  
  const dropdown = document.getElementById('notification-dropdown');
  if (dropdown) dropdown.classList.add('hidden');
}

// ─────────────────────────────────────────────
// SHOP PULSE: NHỊP VẬN HÀNH TRỰC TIẾP
// ─────────────────────────────────────────────
let shopPulseTimer = null;

function loadShopPulseData() {
  google.script.run
    .withSuccessHandler((res) => {
      if (!res) return;
      renderShopPulse(res);
      if (res.liveEvents) {
        renderLiveEvents(res.liveEvents);
      }
    })
    .getShopPulseData();
}

function renderShopPulse(data) {
  if (!data) return;
  const healthVal = data.healthScore || 95;
  const progressVal = data.todayProgress || 0;

  const healthEl = document.getElementById('pulse-center-health');
  if (healthEl) healthEl.textContent = healthVal;

  const targetEl = document.getElementById('pulse-center-target');
  if (targetEl) targetEl.textContent = `Mục tiêu: ${progressVal}%`;

  const revEl = document.getElementById('pulse-val-revenue');
  if (revEl) revEl.textContent = fmtVnd(data.todayRevenue || 0);

  const colEl = document.getElementById('pulse-val-collected');
  if (colEl) colEl.textContent = fmtVnd(data.todayCollected || 0);

  const codEl = document.getElementById('pulse-val-cod');
  if (codEl) codEl.textContent = fmtVnd(data.todayCodPending || 0);

  const actEl = document.getElementById('pulse-val-actions');
  if (actEl) actEl.textContent = `${data.todayActionItems || 0} việc`;

  // Status badge & ring color
  const statusBadge = document.getElementById('shop-pulse-badge');
  const radialBar = document.getElementById('pulse-radial-bar');
  const ringCard = document.getElementById('pulse-ring-card');

  const status = data.pulseStatus || 'green';
  if (ringCard) {
    ringCard.className = `pulse-ring-card pulse-status-${status}`;
  }

  const statusMap = {
    green:  { text: 'Vận hành tốt', stroke: 'url(#pulse-grad-green)', class: 'status-green', icon: 'fa-circle-check' },
    yellow: { text: 'Cần chú ý', stroke: 'url(#pulse-grad-yellow)', class: 'status-yellow', icon: 'fa-triangle-exclamation' },
    red:    { text: 'Có vấn đề cần xử lý', stroke: 'url(#pulse-grad-red)', class: 'status-red', icon: 'fa-circle-exclamation' },
    purple: { text: 'Cơ hội tăng trưởng', stroke: 'url(#pulse-grad-purple)', class: 'status-purple', icon: 'fa-rocket' }
  };

  const st = statusMap[status] || statusMap.green;
  if (statusBadge) {
    statusBadge.className = `shop-pulse-status-badge ${st.class}`;
    statusBadge.innerHTML = `<i class="fas ${st.icon}"></i> <span>${st.text}</span>`;
  }

  if (radialBar) {
    radialBar.style.stroke = st.stroke;
    // Circumference = 2 * PI * 50 = 314.159
    const offset = 314.159 - (314.159 * Math.min(100, healthVal)) / 100;
    radialBar.style.strokeDashoffset = offset;
  }
}

function renderLiveEvents(events) {
  const container = document.getElementById('pulse-events-feed');
  if (!container) return;

  if (!events || !events.length) {
    container.innerHTML = '<div class="pulse-event-empty">Chưa có sự kiện mới hôm nay.</div>';
    return;
  }

  container.innerHTML = events.map((e) => `
    <div class="pulse-event-item event-${e.type || 'info'}">
      <div class="pulse-event-icon"><i class="fas ${e.icon || 'fa-circle-info'}"></i></div>
      <div class="pulse-event-content">
        <div class="pulse-event-title-row">
          <strong class="pulse-event-action">${escapeHtml(e.action)}</strong>
          ${e.maSP && e.maSP !== '—' ? `<span class="pulse-event-masp"><code>${escapeHtml(e.maSP)}</code></span>` : ''}
          <span class="pulse-event-time">${escapeHtml(e.time)}</span>
        </div>
        <p class="pulse-event-desc">${escapeHtml(e.details || '')}</p>
      </div>
    </div>
  `).join('');
}

function pollShopPulseRealtime() {
  if (document.getElementById('page-dashboard')?.classList.contains('hidden')) return;
  loadShopPulseData();
}

// Đã TẮT polling Shop Pulse định kỳ (trước đây mỗi 45 giây); dữ liệu chỉ tải khi mở Dashboard hoặc bấm làm mới.

// ─────────────────────────────────────────────
// TRUNG TÂM KIỂM TRA HỆ THỐNG (SYSTEM AUDIT)
// ─────────────────────────────────────────────
let currentAuditData = null;
let currentAuditFilter = 'all';

function loadSystemAudit(forceRefresh) {
  showLoading('Đang quét toàn bộ hệ thống & dữ liệu...');
  google.script.run
    .withSuccessHandler((res) => {
      hideLoading();
      if (!res) {
        showToast('Không lấy được dữ liệu kiểm toán!', 'error');
        return;
      }
      currentAuditData = res;
      renderSystemAudit(res);
      if (forceRefresh) {
        showToast('Đã hoàn tất quét kiểm toán hệ thống!', 'success');
      }
    })
    .withFailureHandler((err) => {
      hideLoading();
      showToast('Lỗi kiểm toán hệ thống: ' + err.message, 'error');
    })
    .getSystemFullAudit();
}

function renderSystemAudit(data) {
  if (!data) return;

  // 1. Điểm sức khỏe tổng & Kết luận
  const scoreEl = document.getElementById('audit-total-score');
  if (scoreEl) scoreEl.textContent = data.healthScore || 0;

  const badgeEl = document.getElementById('audit-conclusion-badge');
  if (badgeEl) {
    badgeEl.className = `audit-conclusion-badge badge-${data.healthBadgeColor || 'info'}`;
    badgeEl.textContent = data.healthConclusion || 'Hoạt động tốt';
  }

  const descEl = document.getElementById('audit-conclusion-desc');
  if (descEl) {
    const descMap = {
      success: 'Hệ thống vận hành tối ưu, dữ liệu đồng bộ và không có sai sót nghiêm trọng.',
      info:    'Hệ thống hoạt động ổn định, có một vài cảnh báo nhỏ bạn có thể hoàn thiện.',
      warning: 'Phát hiện một số lỗi dữ liệu hoặc cấu hình cần kiểm tra và xử lý sớm.',
      danger:  'Cảnh báo: Có lỗi nghiêm trọng về dữ liệu hoặc cấu hình ảnh hưởng đến vận hành.'
    };
    descEl.textContent = descMap[data.healthBadgeColor] || descMap.info;
  }

  // Update navbar badge
  const navBadge = document.getElementById('nav-badge-health');
  if (navBadge) {
    navBadge.textContent = data.healthScore || 100;
    navBadge.style.background = data.healthScore >= 90 ? '#10b981' : (data.healthScore >= 75 ? '#3b82f6' : (data.healthScore >= 50 ? '#f59e0b' : '#ef4444'));
  }

  // 2. 5 Nhóm trọng số
  const weightsContainer = document.getElementById('audit-weight-components');
  if (weightsContainer && data.scoreComponents) {
    weightsContainer.innerHTML = data.scoreComponents.map((c) => `
      <div class="audit-weight-item">
        <div class="audit-weight-header">
          <span><i class="fas ${c.icon}" style="color:${c.color};"></i> ${escapeHtml(c.name)} <small>(${c.weight})</small></span>
          <strong>${c.score}/100</strong>
        </div>
        <div class="audit-weight-bar">
          <div class="audit-weight-fill" style="width:${Math.max(5, c.score)}%; background:${c.color};"></div>
        </div>
      </div>
    `).join('');
  }

  // 3. Top 3 việc quan trọng nhất cần làm trước
  const topActionsList = document.getElementById('audit-top-actions-list');
  if (topActionsList) {
    if (!data.topActionItems || !data.topActionItems.length) {
      topActionsList.innerHTML = '<div class="top-action-empty"><i class="fas fa-circle-check" style="color:#10b981;"></i> Tuyệt vời! Không có việc khẩn cấp nào cần xử lý.</div>';
    } else {
      topActionsList.innerHTML = data.topActionItems.map((item, idx) => `
        <div class="top-action-card priority-${item.priority || idx + 1}">
          <div class="top-action-num">${idx + 1}</div>
          <div class="top-action-body">
            <h4>${escapeHtml(item.title)}</h4>
            <p>${escapeHtml(item.action)}</p>
          </div>
        </div>
      `).join('');
    }
  }

  // 4. Khối kiểm tra cấu trúc 4 Sheet
  const sheetsGrid = document.getElementById('audit-sheets-grid');
  if (sheetsGrid && data.sheets) {
    sheetsGrid.innerHTML = data.sheets.map((s) => {
      const isOk = s.exists && s.missingColumns.length === 0 && s.duplicateHeaders.length === 0;
      return `
        <div class="audit-sheet-card ${s.exists ? (isOk ? 'sheet-ok' : 'sheet-warning') : 'sheet-missing'}">
          <div class="audit-sheet-header">
            <div>
              <h4><i class="fas fa-file-excel"></i> ${escapeHtml(s.sheetName)}</h4>
              <span class="sheet-status-tag ${s.exists ? 'tag-active' : 'tag-missing'}">
                ${s.exists ? 'Đang hoạt động' : 'Không tồn tại'}
              </span>
            </div>
            <div class="sheet-rows-pill">
              <strong>${s.validRows}</strong> / ${s.totalRows} dòng
            </div>
          </div>
          <div class="audit-sheet-details">
            <div class="sheet-detail-row">
              <span>Dòng bị bỏ qua:</span>
              <strong style="${s.skippedCount > 0 ? 'color:#f59e0b;' : ''}">${s.skippedCount || 0} dòng</strong>
            </div>
            <div class="sheet-detail-row">
              <span>Cột thiếu (so với 23 cột):</span>
              <strong style="${s.missingColumns.length > 0 ? 'color:#ef4444;' : ''}">${s.missingColumns.length ? s.missingColumns.join(', ') : 'Đầy đủ'}</strong>
            </div>
            <div class="sheet-detail-row">
              <span>Header bị trùng:</span>
              <strong style="${s.duplicateHeaders.length > 0 ? 'color:#ef4444;' : ''}">${s.duplicateHeaders.length ? s.duplicateHeaders.join(', ') : 'Không có'}</strong>
            </div>
            <div class="sheet-detail-row">
              <span>Cột chứa công thức:</span>
              <strong>${s.formulaColumns.length ? s.formulaColumns.join(', ') : 'Không có'}</strong>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // 5. Cập nhật số đếm trên bộ lọc
  const cAll = document.getElementById('count-issue-all');
  if (cAll) cAll.textContent = data.totalIssues || 0;
  const cCrit = document.getElementById('count-issue-critical');
  if (cCrit) cCrit.textContent = data.criticalCount || 0;
  const cWarn = document.getElementById('count-issue-warning');
  if (cWarn) cWarn.textContent = data.warningCount || 0;
  const cInfo = document.getElementById('count-issue-info');
  if (cInfo) cInfo.textContent = data.infoCount || 0;

  // 6. Render bảng lỗi chất lượng dữ liệu
  renderDataQualityTable(data.issues, currentAuditFilter);
}

function filterAuditIssues(level, btn) {
  currentAuditFilter = level;
  document.querySelectorAll('.audit-filter-pill').forEach((b) => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  if (currentAuditData) {
    renderDataQualityTable(currentAuditData.issues, level);
  }
}

function renderDataQualityTable(issues, filterLevel) {
  const tbody = document.getElementById('audit-issues-tbody');
  if (!tbody) return;

  const filtered = (issues || []).filter((i) => {
    if (!filterLevel || filterLevel === 'all') return true;
    return i.level === filterLevel;
  });

  if (!filtered.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; padding:40px; color:var(--text-muted);">
          <i class="fas fa-circle-check" style="font-size:2rem; color:#10b981; margin-bottom:10px; display:block;"></i>
          Không phát hiện lỗi dữ liệu nào trong nhóm này!
        </td>
      </tr>
    `;
    return;
  }

  const levelBadgeMap = {
    critical: '<span class="level-badge badge-critical"><i class="fas fa-triangle-exclamation"></i> Nghiêm trọng</span>',
    warning:  '<span class="level-badge badge-warning"><i class="fas fa-circle-exclamation"></i> Cần kiểm tra</span>',
    info:     '<span class="level-badge badge-info"><i class="fas fa-circle-info"></i> Gợi ý</span>'
  };

  tbody.innerHTML = filtered.map((i) => `
    <tr class="issue-row-${i.level}">
      <td>${levelBadgeMap[i.level] || levelBadgeMap.info}</td>
      <td><span class="sheet-name-badge">${escapeHtml(i.sourceSheet)}</span></td>
      <td><strong style="color:var(--text-primary);">#${i.rowIndex || '—'}</strong></td>
      <td><code>${escapeHtml(i.maSP || '—')}</code></td>
      <td><span class="issue-message-text">${escapeHtml(i.message)}</span></td>
      <td style="text-align:center;">
        <button class="btn btn-sm btn-ghost btn-audit-fix" onclick="openAuditRowEdit('${escapeHtml(i.sourceSheet)}', ${i.rowIndex}, '${escapeHtml(i.maSP)}')">
          <i class="fas fa-pen-to-square"></i> Mở đơn sửa
        </button>
      </td>
    </tr>
  `).join('');
}

function openAuditRowEdit(sheetName, rowIndex, maSP) {
  const match = (allReportRows || []).find((r) => r.sourceSheet === sheetName && r.rowIndex === Number(rowIndex)) ||
                (allRows || []).find((r) => r.sourceSheet === sheetName && r.rowIndex === Number(rowIndex)) ||
                (allReportRows || []).find((r) => r.maSP === maSP);

  if (match) {
    openEditModal(match, sheetName);
  } else {
    openEditModal({
      rowIndex: Number(rowIndex),
      sourceSheet: sheetName,
      maSP: maSP && maSP !== '—' ? maSP : ''
    }, sheetName);
  }
}

window.addEventListener('click', function(e) {
  const dropdown = document.getElementById('notification-dropdown');
  const container = document.getElementById('topbar-notification');
  if (dropdown && !dropdown.classList.contains('hidden') && container && !container.contains(e.target)) {
    dropdown.classList.add('hidden');
  }
});



// ═══════════════════════════════════════════════
// MODULE: SALES COMBAT ARENA & 3D REVENUE RADAR
// ═══════════════════════════════════════════════

// 1. CONFETTI 3D ENGINE (Zero Dependencies)
function fireConfetti3D() {
  const canvas = document.getElementById('confetti-canvas-overlay');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const particles = [];
  const colors = ['#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#10b981', '#3b82f6', '#fbbf24'];

  for (let i = 0; i < 90; i++) {
    particles.push({
      x: 30 + Math.random() * 60,
      y: canvas.height - 20,
      vx: (Math.random() * 8 + 5),
      vy: -(Math.random() * 15 + 11),
      size: Math.random() * 8 + 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      tilt: Math.random() * 10,
      tiltSpeed: Math.random() * 0.1 + 0.05,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10,
      opacity: 1
    });
    particles.push({
      x: canvas.width - 30 - Math.random() * 60,
      y: canvas.height - 20,
      vx: -(Math.random() * 8 + 5),
      vy: -(Math.random() * 15 + 11),
      size: Math.random() * 8 + 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      tilt: Math.random() * 10,
      tiltSpeed: Math.random() * 0.1 + 0.05,
      rotation: Math.random() * 360,
      rotationSpeed: (Math.random() - 0.5) * 10,
      opacity: 1
    });
  }

  let step = 0;
  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    step++;
    let alive = false;

    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.35;
      p.vx *= 0.98;
      p.rotation += p.rotationSpeed;
      p.tilt += p.tiltSpeed;
      if (step > 40) p.opacity -= 0.015;

      if (p.opacity > 0 && p.y < canvas.height + 50) {
        alive = true;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.scale(Math.sin(p.tilt), 1);
        ctx.globalAlpha = Math.max(0, p.opacity);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
        ctx.restore();
      }
    });

    if (alive && step < 140) {
      requestAnimationFrame(render);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
  render();
}

// 2. WEB AUDIO SYNTHESIZER (Ka-Ching & Lo-Fi Floor)
let audioCtx = null;
function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContext();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playKaChingSound() {
  try {
    const ctx = getAudioContext();
    const now = ctx.currentTime;

    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(987.77, now);
    gain1.gain.setValueAtTime(0.35, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.5);

    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(1318.51, now + 0.08);
    gain2.gain.setValueAtTime(0.4, now + 0.08);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.08);
    osc2.stop(now + 0.65);
  } catch (e) {
    console.warn('playKaChingSound error:', e);
  }
}

let isLoFiPlaying = false;
let loFiNodes = null;

function toggleLoFiFloorAsmr() {
  const btn = document.getElementById('btn-lofi-toggle');
  const label = document.getElementById('lofi-label');
  const icon = document.getElementById('lofi-icon');

  if (isLoFiPlaying) {
    stopLoFiFloorAsmr();
    isLoFiPlaying = false;
    if (btn) btn.classList.remove('active');
    if (label) label.textContent = 'Lo-Fi Floor';
    if (icon) icon.className = 'fas fa-headphones';
    showToast('Đã tắt Lo-Fi Trading Floor ASMR', 'info');
  } else {
    startLoFiFloorAsmr();
    isLoFiPlaying = true;
    if (btn) btn.classList.add('active');
    if (label) label.textContent = 'Đang Phát 🎧';
    if (icon) icon.className = 'fas fa-volume-high';
    showToast('Đang phát âm thanh Lo-Fi Trading Floor ASMR thư thái 🎧', 'success');
  }
}

function startLoFiFloorAsmr() {
  try {
    const ctx = getAudioContext();
    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.08, ctx.currentTime);
    masterGain.connect(ctx.destination);

    const chordFreqs = [130.81, 196.00, 246.94, 293.66];
    const chordOscs = chordFreqs.map(f => {
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(f, ctx.currentTime);
      g.gain.setValueAtTime(0.2, ctx.currentTime);
      osc.connect(g);
      g.connect(masterGain);
      osc.start();
      return osc;
    });

    const bufferSize = ctx.sampleRate * 2;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      output[i] = (b0 + b1 + b2) * 0.15;
    }
    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;
    const filter = ctx.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.setValueAtTime(320, ctx.currentTime);
    noiseSource.connect(filter);
    filter.connect(masterGain);
    noiseSource.start();

    loFiNodes = { chordOscs, noiseSource, masterGain };
  } catch (e) {
    console.warn('startLoFiFloorAsmr error:', e);
  }
}

function stopLoFiFloorAsmr() {
  if (!loFiNodes) return;
  try {
    loFiNodes.chordOscs.forEach(osc => osc.stop());
    loFiNodes.noiseSource.stop();
    loFiNodes.masterGain.disconnect();
    loFiNodes = null;
  } catch (e) {}
}
