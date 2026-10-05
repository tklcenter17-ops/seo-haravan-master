/**
 * HAMACO TIMELINE MODULE (1976 - 2026)
 * Horizontal tab-switcher with touch friendly swipe support
 */

export function initTimeline() {
  const timelineContainer = document.querySelector('[data-timeline]');
  if (!timelineContainer) return;

  const yearButtons = timelineContainer.querySelectorAll('.timeline-year-btn');
  const contentPanels = timelineContainer.querySelectorAll('.timeline-panel');

  yearButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetYear = btn.getAttribute('data-year');

      yearButtons.forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');

      contentPanels.forEach((panel) => {
        if (panel.getAttribute('data-year') === targetYear) {
          panel.style.display = 'block';
        } else {
          panel.style.display = 'none';
        }
      });
    });
  });
}
