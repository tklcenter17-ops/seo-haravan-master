/**
 * HAMACO ACCESSIBLE TABS MODULE
 */

export function initTabs() {
  const tabContainers = document.querySelectorAll('[data-tabs]');

  tabContainers.forEach((container) => {
    const tabButtons = container.querySelectorAll('[role="tab"]');
    const tabPanes = container.querySelectorAll('[role="tabpanel"]');

    tabButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = btn.getAttribute('data-target') || btn.getAttribute('aria-controls');

        // Reset all buttons in this container
        tabButtons.forEach((b) => {
          b.classList.remove('is-active');
          b.setAttribute('aria-selected', 'false');
        });

        // Hide all panes
        tabPanes.forEach((pane) => {
          pane.classList.remove('is-active');
          pane.hidden = true;
        });

        // Activate clicked
        btn.classList.add('is-active');
        btn.setAttribute('aria-selected', 'true');

        const activePane = container.querySelector(`#${targetId}`);
        if (activePane) {
          activePane.classList.add('is-active');
          activePane.hidden = false;
        }
      });
    });
  });
}
