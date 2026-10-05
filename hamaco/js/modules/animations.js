/**
 * HAMACO INDUSTRIAL SUITE — ANIMATION & INTERACTION ENGINE
 * Scroll reveals, number counters, glassmorphic headers, card tilts, ticker marquee
 * Standards: /ui-ux-pro-max (Trust & Authority) & /ui-styling
 */

export function initAnimations() {
  initScrollReveal();
  initCounters();
  initHeaderScroll();
  initCardShine();
}

/**
 * Scroll Reveal with Automatic Grid Stagger
 */
function initScrollReveal() {
  // Target both explicitly marked elements and key visual components
  const elements = document.querySelectorAll(
    '.reveal-on-scroll, .section-header, .stat-box, .stat-card, .pillar-card, .product-card, .card-hover, .timeline-item, .bento-col-4, .bento-col-8'
  );
  if (!elements.length) return;

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.08, rootMargin: '0px 0px -30px 0px' }
  );

  elements.forEach((el) => {
    el.classList.add('reveal-on-scroll');
    // Automatic staggered delay for siblings inside grids
    if (!el.style.transitionDelay && (el.parentElement?.classList.contains('grid') || el.parentElement?.classList.contains('stats-grid'))) {
      const sibIndex = Array.from(el.parentElement.children).indexOf(el);
      el.style.transitionDelay = `${Math.min(sibIndex * 90, 450)}ms`;
    }
    observer.observe(el);
  });
}

/**
 * Animated Number Counters
 */
function initCounters() {
  const counters = document.querySelectorAll('[data-counter], .stat-number, .stat-counter-number');
  if (!counters.length) return;

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          obs.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );

  counters.forEach(counter => observer.observe(counter));
}

function animateCounter(el) {
  // If already animated, skip
  if (el.getAttribute('data-animated') === 'true') return;
  el.setAttribute('data-animated', 'true');

  const targetStr = (el.getAttribute('data-counter') || el.innerText || '').trim();
  const match = targetStr.match(/([0-9.,]+)/);
  if (!match) return;

  const targetNum = parseFloat(match[1].replace(/,/g, ''));
  if (isNaN(targetNum)) return;

  const prefix = targetStr.slice(0, match.index);
  const suffix = targetStr.slice(match.index + match[0].length);
  const isDecimal = match[1].includes('.');
  const duration = 1500; // ms
  const startTime = performance.now();

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const currentVal = easeOutCubic(progress) * targetNum;

    let displayVal;
    if (isDecimal) {
      displayVal = currentVal.toFixed(1);
    } else if (targetNum >= 1000) {
      displayVal = Math.round(currentVal).toLocaleString('en-US');
    } else {
      displayVal = Math.round(currentVal);
    }

    el.innerText = `${prefix}${displayVal}${suffix}`;

    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      el.innerText = targetStr; // Snap to exact target string
    }
  }

  requestAnimationFrame(update);
}

/**
 * Glassmorphic Sticky Header Transition on Scroll
 */
function initHeaderScroll() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
    if (currentScroll > 25) {
      header.classList.add('is-scrolled');
    } else {
      header.classList.remove('is-scrolled');
    }
  }, { passive: true });
}

/**
 * Tactile Button & Card Dynamic Shine Effect
 */
function initCardShine() {
  const cards = document.querySelectorAll('.card, .card-interactive, .btn-primary, .btn-navy, .pillar-card');
  cards.forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    });
  });
}
