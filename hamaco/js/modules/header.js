/**
 * HAMACO HEADER & NAVIGATION MODULE
 * Sticky header behavior, mobile drawer toggle, keyboard escape & active links
 */

export function initHeader() {
  const header = document.querySelector('.site-header');
  const toggleBtn = document.querySelector('[data-drawer-toggle]');
  const closeBtn = document.querySelector('[data-drawer-close]');
  const overlay = document.querySelector('.mobile-drawer-overlay');
  const drawer = document.querySelector('.mobile-drawer');

  // Sticky header on scroll
  if (header) {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        header.classList.add('is-scrolled');
      } else {
        header.classList.remove('is-scrolled');
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  // Open drawer
  const openDrawer = () => {
    document.body.classList.add('drawer-open');
    if (toggleBtn) toggleBtn.setAttribute('aria-expanded', 'true');
    if (drawer) {
      const firstFocusable = drawer.querySelector('a, button');
      if (firstFocusable) firstFocusable.focus();
    }
  };

  // Close drawer
  const closeDrawer = () => {
    document.body.classList.remove('drawer-open');
    if (toggleBtn) {
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.focus();
    }
  };

  if (toggleBtn) {
    toggleBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const isOpen = document.body.classList.contains('drawer-open');
      if (isOpen) closeDrawer();
      else openDrawer();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', (e) => {
      e.preventDefault();
      closeDrawer();
    });
  }

  if (overlay) {
    overlay.addEventListener('click', closeDrawer);
  }

  // Close on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && document.body.classList.contains('drawer-open')) {
      closeDrawer();
    }
  });

  // Highlight active nav item
  const currentPath = window.location.pathname.replace(/\/$/, '');
  const navLinks = document.querySelectorAll('.nav-link, .drawer-link');
  navLinks.forEach((link) => {
    const href = link.getAttribute('href');
    if (!href) return;
    const cleanHref = href.split('#')[0].replace(/\/$/, '');
    if (cleanHref && currentPath.endsWith(cleanHref) && cleanHref !== '') {
      link.classList.add('is-active');
    }
  });
}
