/**
 * HAMACO FRONTEND SUITE — MAIN APP ENTRY POINT
 * Initializes all vanilla JS modules
 */

import { initHeader } from './modules/header.js';
import { initTabs } from './modules/tabs.js';
import { initAccordion } from './modules/accordion.js';
import { initModal } from './modules/modal.js';
import { initFilter } from './modules/filter.js';
import { initForms } from './modules/form.js';
import { initTimeline } from './modules/timeline.js';
import { initIRWidget } from './modules/ir-widget.js';
import { initMap } from './modules/map.js';

document.addEventListener('DOMContentLoaded', () => {
  try {
    initHeader();
    initTabs();
    initAccordion();
    initModal();
    initFilter();
    initForms();
    initTimeline();
    initIRWidget();
    initMap();
  } catch (err) {
    console.error('HAMACO UI initialization error:', err);
  }
});
