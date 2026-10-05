/**
 * HAMACO FORM HANDLING & VALIDATION MODULE
 * Multi-step wizard, anti-double click protection, honeypot, toast feedback
 */

export function showToast(message, type = 'success') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      ${type === 'success' 
        ? '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>' 
        : '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>'}
    </svg>
    <span>${message}</span>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

export function initForms() {
  // 1. General Form Validation & Submission
  const forms = document.querySelectorAll('form[data-validate]');

  forms.forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      // Check honeypot field
      const honeypot = form.querySelector('input[name="website_hp"]');
      if (honeypot && honeypot.value.trim() !== '') {
        console.warn('Bot submission blocked');
        return;
      }

      // Check required fields
      let isValid = true;
      const requiredInputs = form.querySelectorAll('[required]');

      requiredInputs.forEach((input) => {
        const errorEl = input.parentElement.querySelector('.form-error');
        if (input.type === 'checkbox') {
          if (!input.checked) {
            isValid = false;
            if (errorEl) errorEl.style.display = 'block';
          } else {
            if (errorEl) errorEl.style.display = 'none';
          }
        } else {
          if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = 'var(--hamaco-danger)';
            if (errorEl) errorEl.style.display = 'block';
          } else {
            input.style.borderColor = '';
            if (errorEl) errorEl.style.display = 'none';
          }
        }
      });

      if (!isValid) {
        showToast('Vui lòng kiểm tra lại các trường bắt buộc.', 'error');
        return;
      }

      // Anti-double submission guard
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = `
          <svg class="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
            <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
            <path d="M12 2a10 10 0 0 1 10 10"/>
          </svg> Đang gửi yêu cầu...
        `;

        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
          form.reset();
          showToast('Yêu cầu đã được gửi thành công! Ban Quản Lý HAMACO sẽ phản hồi trong 24h làm việc.');
          
          // Close modal if form was inside a modal
          const modal = form.closest('.modal-overlay');
          if (modal) {
            modal.classList.remove('is-active');
            document.body.style.overflow = '';
          }
        }, 1200);
      }
    });
  });

  // 2. Multi-step Quote Wizard Logic
  const wizard = document.querySelector('[data-quote-wizard]');
  if (wizard) {
    let currentStep = 1;
    const totalSteps = 3;

    const stepPanes = wizard.querySelectorAll('.wizard-pane');
    const stepIndicators = wizard.querySelectorAll('.wizard-step-indicator');
    const nextButtons = wizard.querySelectorAll('[data-wizard-next]');
    const prevButtons = wizard.querySelectorAll('[data-wizard-prev]');

    const updateWizard = () => {
      stepPanes.forEach((pane) => {
        const stepNum = parseInt(pane.getAttribute('data-step'), 10);
        pane.style.display = stepNum === currentStep ? 'block' : 'none';
      });

      stepIndicators.forEach((ind) => {
        const stepNum = parseInt(ind.getAttribute('data-step-target'), 10);
        ind.classList.remove('is-active', 'is-completed');
        if (stepNum === currentStep) {
          ind.classList.add('is-active');
        } else if (stepNum < currentStep) {
          ind.classList.add('is-completed');
        }
      });
    };

    nextButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const currentPane = wizard.querySelector(`.wizard-pane[data-step="${currentStep}"]`);
        const requiredFields = currentPane ? currentPane.querySelectorAll('[required]') : [];
        let canProceed = true;

        requiredFields.forEach((field) => {
          if (!field.value.trim()) {
            canProceed = false;
            field.style.borderColor = 'var(--hamaco-danger)';
          } else {
            field.style.borderColor = '';
          }
        });

        if (!canProceed) {
          showToast('Vui lòng điền đầy đủ thông tin trước khi tiếp tục.', 'error');
          return;
        }

        if (currentStep < totalSteps) {
          currentStep++;
          updateWizard();
        }
      });
    });

    prevButtons.forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (currentStep > 1) {
          currentStep--;
          updateWizard();
        }
      });
    });

    updateWizard();
  }
}
