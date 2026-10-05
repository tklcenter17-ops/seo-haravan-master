/**
 * HAMACO ACCESSIBLE ACCORDION MODULE
 */

export function initAccordion() {
  const accordionButtons = document.querySelectorAll('.accordion-btn');

  accordionButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const item = btn.closest('.accordion-item');
      if (!item) return;

      const isOpen = item.classList.contains('is-open');
      const isSingleMode = item.closest('[data-accordion-single]') !== null;

      if (isSingleMode) {
        const parentAccordion = item.closest('.accordion');
        if (parentAccordion) {
          parentAccordion.querySelectorAll('.accordion-item').forEach((sibling) => {
            if (sibling !== item) {
              sibling.classList.remove('is-open');
              const siblingBtn = sibling.querySelector('.accordion-btn');
              if (siblingBtn) siblingBtn.setAttribute('aria-expanded', 'false');
            }
          });
        }
      }

      if (isOpen) {
        item.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
}
