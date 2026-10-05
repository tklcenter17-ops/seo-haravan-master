/**
 * HAMACO BRANCH & NETWORK LOCATOR MODULE
 * Sync branch list with area filter and copy address functionality
 */

import { showToast } from './form.js';

export function initMap() {
  const branchList = document.querySelector('[data-branch-list]');
  const areaFilter = document.querySelector('[data-branch-filter]');
  const copyButtons = document.querySelectorAll('[data-copy-address]');

  if (areaFilter && branchList) {
    areaFilter.addEventListener('change', (e) => {
      const selectedArea = e.target.value;
      const items = branchList.querySelectorAll('.branch-item');

      items.forEach((item) => {
        const itemArea = item.getAttribute('data-area');
        if (selectedArea === 'all' || itemArea === selectedArea) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
      });
    });
  }

  copyButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const address = btn.getAttribute('data-copy-address');
      if (address && navigator.clipboard) {
        navigator.clipboard.writeText(address).then(() => {
          showToast('Đã sao chép địa chỉ vào bộ nhớ tạm!');
        });
      }
    });
  });
}
