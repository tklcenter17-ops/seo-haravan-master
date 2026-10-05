/**
 * HAMACO CLIENT FILTER MODULE
 * Live filtering with URL parameter synchronization and empty states
 */

export function initFilter() {
  const filterContainers = document.querySelectorAll('[data-filter-container]');

  filterContainers.forEach((container) => {
    const filterButtons = container.querySelectorAll('[data-filter-key]');
    const filterItems = container.querySelectorAll('[data-filter-item]');
    const emptyState = container.querySelector('[data-filter-empty]');
    const paramName = container.getAttribute('data-filter-param') || 'category';

    const applyFilter = (filterVal, updateUrl = true) => {
      let visibleCount = 0;

      filterButtons.forEach((btn) => {
        if (btn.getAttribute('data-filter-key') === filterVal) {
          btn.classList.add('is-active');
        } else {
          btn.classList.remove('is-active');
        }
      });

      filterItems.forEach((item) => {
        const itemCategory = item.getAttribute('data-category');
        if (filterVal === 'all' || itemCategory === filterVal || (itemCategory && itemCategory.includes(filterVal))) {
          item.style.display = '';
          visibleCount++;
        } else {
          item.style.display = 'none';
        }
      });

      if (emptyState) {
        emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
      }

      if (updateUrl) {
        const url = new URL(window.location);
        if (filterVal === 'all') {
          url.searchParams.delete(paramName);
        } else {
          url.searchParams.set(paramName, filterVal);
        }
        window.history.replaceState({}, '', url);
      }
    };

    filterButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const filterVal = btn.getAttribute('data-filter-key');
        applyFilter(filterVal, true);
      });
    });

    // Initial filter from URL
    const urlParams = new URLSearchParams(window.location.search);
    const initialFilter = urlParams.get(paramName);
    if (initialFilter) {
      applyFilter(initialFilter, false);
    }
  });
}
