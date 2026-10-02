/**
 * Site-wide progressive enhancements.
 *
 * - Mobile navigation toggle (aria-expanded / aria-controls aware)
 * - Smooth in-page scrolling, scoped to anchors whose target actually exists
 */
(function () {
  'use strict';

  function initMobileNav() {
    var toggle = document.querySelector('.nav-mobile-toggle');
    var menu = document.querySelector('.nav-menu');
    if (!toggle || !menu) return;

    if (!menu.id) menu.id = 'primary-navigation';
    toggle.setAttribute('aria-controls', menu.id);
    toggle.setAttribute('aria-expanded', 'false');

    function setOpen(open) {
      menu.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    // Close the menu once a navigation link is followed.
    menu.addEventListener('click', function (event) {
      if (event.target.closest && event.target.closest('a')) setOpen(false);
    });

    // Escape closes the menu and returns focus to the toggle.
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && menu.classList.contains('is-open')) {
        setOpen(false);
        toggle.focus();
      }
    });
  }

  function initSmoothScroll() {
    var prefersReducedMotion =
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      // Leave the skip link to the browser so it also moves focus.
      if (anchor.classList.contains('skip-link')) return;

      anchor.addEventListener('click', function (event) {
        var href = anchor.getAttribute('href');
        if (!href || href === '#') return;

        var target;
        try {
          target = document.querySelector(href);
        } catch (err) {
          return; // Not a valid selector — let the browser handle it.
        }
        if (!target) return;

        event.preventDefault();
        target.scrollIntoView({
          behavior: prefersReducedMotion ? 'auto' : 'smooth',
          block: 'start'
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initMobileNav();
    initSmoothScroll();
  });
})();
