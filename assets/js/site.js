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

  function initRelativeTimes() {
    var now = Date.now();
    document.querySelectorAll('time[data-relative-time]').forEach(function (el) {
      var raw = el.getAttribute('datetime');
      if (!raw) return;
      var then = Date.parse(raw);
      if (isNaN(then)) return;
      var days = Math.max(0, Math.floor((now - then) / 86400000));
      var label;
      if (days === 0) label = 'today';
      else if (days === 1) label = 'yesterday';
      else if (days < 30) label = days + ' days ago';
      else if (days < 60) label = '1 month ago';
      else label = Math.floor(days / 30) + ' months ago';
      el.textContent = label;
    });
  }

  function initMaintainerRotator() {
    var rotator = document.querySelector('[data-maintainer-rotator]');
    if (!rotator) return;

    var items = rotator.querySelectorAll('.rotator-item');
    if (items.length < 2) return;

    // Static first pair when the user prefers reduced motion.
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var index = 0;
    var timer = null;
    var interval = parseInt(rotator.getAttribute('data-interval'), 10) || 4200;

    function show(next) {
      items[index].classList.remove('is-active');
      index = (next + items.length) % items.length;
      items[index].classList.add('is-active');
    }

    function start() {
      if (!timer) timer = setInterval(function () { show(index + 1); }, interval);
    }

    function stop() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
    }

    // Pause while the visitor is reading, interacting, or away.
    rotator.addEventListener('mouseenter', stop);
    rotator.addEventListener('mouseleave', start);
    rotator.addEventListener('focusin', stop);
    rotator.addEventListener('focusout', function (event) {
      if (!rotator.contains(event.relatedTarget)) start();
    });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop();
      else start();
    });

    // Only cycle while the section is on screen.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) start();
          else stop();
        });
      }, { threshold: 0.25 }).observe(rotator);
    } else {
      start();
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    initMobileNav();
    initSmoothScroll();
    initRelativeTimes();
    initMaintainerRotator();
  });
})();
