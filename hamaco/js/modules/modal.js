/**
 * HAMACO ACCESSIBLE MODAL & LIGHTBOX MODULE
 */

export function initModal() {
  const openButtons = document.querySelectorAll('[data-modal-open]');
  const closeButtons = document.querySelectorAll('[data-modal-close]');
  let lastFocusedElement = null;

  const openModal = (modalId) => {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    lastFocusedElement = document.activeElement;
    modal.classList.add('is-active');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    // Focus close button or first focusable
    const focusable = modal.querySelector('button, [href], input, select, textarea');
    if (focusable) focusable.focus();
  };

  const closeModal = (modal) => {
    if (!modal) return;
    modal.classList.remove('is-active');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    // Stop video if iframe or video tag present
    const video = modal.querySelector('video');
    if (video) video.pause();

    const iframe = modal.querySelector('iframe');
    if (iframe) {
      const src = iframe.src;
      iframe.src = src; // reset video playback
    }

    if (lastFocusedElement) {
      lastFocusedElement.focus();
    }
  };

  openButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-modal-open');
      openModal(targetId);

      // If it's a lightbox button with image data
      const imgSrc = btn.getAttribute('data-image-src');
      const imgCaption = btn.getAttribute('data-image-caption');
      if (imgSrc) {
        const lightboxImg = document.getElementById('lightbox-image');
        const lightboxCap = document.getElementById('lightbox-caption');
        if (lightboxImg) lightboxImg.src = imgSrc;
        if (lightboxCap) lightboxCap.textContent = imgCaption || '';
      }

      // If it's a video modal with video data
      const videoTitle = btn.getAttribute('data-video-title');
      if (videoTitle) {
        const titleEl = document.getElementById('video-modal-title');
        if (titleEl) titleEl.textContent = videoTitle;
      }
    });
  });

  closeButtons.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const modal = btn.closest('.modal-overlay');
      closeModal(modal);
    });
  });

  // Close when clicking overlay backdrop
  document.querySelectorAll('.modal-overlay').forEach((overlay) => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const activeModal = document.querySelector('.modal-overlay.is-active');
      if (activeModal) closeModal(activeModal);
    }
  });
}
