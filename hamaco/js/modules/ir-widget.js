/**
 * HAMACO IR STOCK WIDGET MODULE (Mã HAM / UPCoM)
 * Displays verified market data reference with timestamp and disclaimer
 */

export function initIRWidget() {
  const widgets = document.querySelectorAll('[data-ir-widget]');
  if (!widgets.length) return;

  const now = new Date();
  const dateFormatted = `${String(now.getDate()).padStart(2, '0')}/${String(now.getMonth() + 1).padStart(2, '0')}/${now.getFullYear()} — 15:00 (Đóng cửa)`;

  widgets.forEach((widget) => {
    const timeEl = widget.querySelector('[data-ir-timestamp]');
    if (timeEl) {
      timeEl.textContent = dateFormatted;
    }
  });
}
