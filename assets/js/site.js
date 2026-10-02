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

    var all = Array.prototype.slice.call(rotator.querySelectorAll('.rotator-item'));
    if (all.length < 2) return;

    // Static server-rendered pair when the user prefers reduced motion.
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var interval = parseInt(rotator.getAttribute('data-interval'), 10) || 4200;
    var size = parseInt(rotator.getAttribute('data-rotation-size'), 10) || 12;
    var queue = [];
    var index = 0;
    var timer = null;

    function activate(element) {
      all.forEach(function (item) { item.classList.remove('is-active'); });
      element.classList.add('is-active');
    }

    function shuffled(list) {
      var copy = list.slice();
      for (var i = copy.length - 1; i > 0; i -= 1) {
        var j = Math.floor(Math.random() * (i + 1));
        var swap = copy[i];
        copy[i] = copy[j];
        copy[j] = swap;
      }
      return copy;
    }

    // Pick a fresh random selection; never open with the pair just shown.
    function reselect(previous) {
      var pool = shuffled(all);
      if (previous && pool.length > 1 && pool[0] === previous) {
        var swap = pool[0];
        pool[0] = pool[pool.length - 1];
        pool[pool.length - 1] = swap;
      }
      queue = pool.slice(0, Math.min(size, pool.length));
      index = 0;
      activate(queue[0]);
    }

    function advance() {
      var shown = queue[index];
      index += 1;
      if (index >= queue.length) {
        reselect(shown);
        return;
      }
      activate(queue[index]);
    }

    function start() {
      if (!timer) timer = setInterval(advance, interval);
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

    reselect(null);

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
