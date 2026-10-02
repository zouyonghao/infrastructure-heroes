/**
 * Maintainer directory filters (progressive enhancement).
 *
 * - Search by name/role, filter by project and status.
 * - Filter state persists in the URL hash: #q=…&project=…&status=…
 * - Without JavaScript every card stays visible.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-maintainer-directory]');
  if (!root) return;

  var cards = Array.prototype.slice.call(
    document.querySelectorAll('#maintainers-grid .maintainer-card')
  );
  var search = document.getElementById('maintainer-search');
  var project = document.getElementById('maintainer-project');
  var status = document.getElementById('maintainer-status');
  var reset = document.getElementById('maintainer-reset');
  var countEl = document.getElementById('maintainer-count');
  var empty = document.getElementById('maintainer-empty');
  if (!search || !project || !status || !countEl) return;

  var total = cards.length;

  function readHash() {
    var params = new URLSearchParams(window.location.hash.slice(1));
    return {
      q: params.get('q') || '',
      project: params.get('project') || '',
      status: params.get('status') || ''
    };
  }

  function writeHash(state) {
    var params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.project) params.set('project', state.project);
    if (state.status) params.set('status', state.status);
    var hash = params.toString();
    history.replaceState(
      null,
      '',
      window.location.pathname + window.location.search + (hash ? '#' + hash : '')
    );
  }

  function apply(updateHash) {
    var q = search.value.trim().toLowerCase();
    var p = project.value;
    var s = status.value;
    var visible = 0;

    cards.forEach(function (card) {
      var name = card.getAttribute('data-name') || '';
      var role = card.getAttribute('data-role') || '';
      var projects = (card.getAttribute('data-projects') || '').split('|');
      var cardStatus = card.getAttribute('data-status') || 'unknown';
      var matches =
        (!q || name.indexOf(q) !== -1 || role.indexOf(q) !== -1) &&
        (!p || projects.indexOf(p) !== -1) &&
        (!s || cardStatus === s);
      card.hidden = !matches;
      if (matches) visible += 1;
    });

    countEl.textContent =
      visible === total
        ? total + ' maintainers'
        : 'Showing ' + visible + ' of ' + total + ' maintainers';
    if (empty) empty.hidden = visible !== 0;
    if (updateHash) writeHash({ q: q, project: p, status: s });
  }

  var initial = readHash();
  if (initial.q || initial.project || initial.status) {
    search.value = initial.q;
    project.value = initial.project;
    status.value = initial.status;
  }

  search.addEventListener('input', function () { apply(true); });
  project.addEventListener('change', function () { apply(true); });
  status.addEventListener('change', function () { apply(true); });
  if (reset) {
    reset.addEventListener('click', function () {
      search.value = '';
      project.value = '';
      status.value = '';
      apply(true);
    });
  }

  // Support back/forward and in-page hash changes.
  window.addEventListener('hashchange', function () {
    var state = readHash();
    search.value = state.q;
    project.value = state.project;
    status.value = state.status;
    apply(false);
  });

  apply(false);
})();
