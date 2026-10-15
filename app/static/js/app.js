// Aucun script en ligne (CSP). Comportements :
// 1. Révélation des cartes d'un paquet, une par une (amélioration progressive).
// 2. Copier le jeton Cap dans le champ caché du formulaire.
// 3. Rafraîchir le compte à rebours du paquet gratuit une fois par minute (pas de aria-live).
(function () {
  document.documentElement.classList.add('js');

  // Ouverture d'un paquet : une carte à la fois, de la moins rare à la plus rare.
  var list = document.querySelector('[data-reveal]');
  if (list) {
    var items = Array.prototype.slice.call(list.querySelectorAll('[data-reveal-item]'));
    var next = document.getElementById('reveal-next');
    var all = document.getElementById('reveal-all');
    var progress = document.getElementById('reveal-progress');
    var status = document.getElementById('reveal-status');
    var count = progress.querySelector('[data-count]');
    var shown = 0;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    next.hidden = all.hidden = progress.hidden = false;

    var reveal = function () {
      if (shown >= items.length) return;
      var li = items[shown++];
      li.classList.add('is-revealed');
      if (!reduce) li.querySelector('.card-face').classList.add('animate-reveal');
      count.textContent = shown;
      status.textContent = 'Carte ' + shown + ' sur ' + items.length + ' : ' + li.dataset.title +
        ', ' + li.dataset.rarityLabel + '.';
      if (shown >= items.length) {
        next.hidden = all.hidden = true;
        status.textContent += ' Toutes les cartes sont révélées.';
      } else if (shown === items.length - 1) {
        next.textContent = 'Révéler la dernière carte';
      }
    };
    next.addEventListener('click', reveal);
    all.addEventListener('click', function () { while (shown < items.length) reveal(); });
  }

  var widget = document.getElementById('cap');
  var field = document.getElementById('cap-token');
  if (widget && field) {
    widget.addEventListener('solve', function (e) {
      field.value = (e.detail && e.detail.token) || '';
    });
  }

  function format(ms) {
    var m = Math.max(0, Math.ceil(ms / 60000));
    var h = Math.floor(m / 60);
    return h > 0 ? h + ' h ' + (m % 60) + ' min' : m + ' min';
  }
  function tick() {
    document.querySelectorAll('time[data-countdown]').forEach(function (el) {
      var target = Date.parse(el.dataset.countdown);
      if (isNaN(target)) return;
      var left = target - Date.now();
      el.textContent = left <= 0 ? 'quelques secondes (recharge la page)' : format(left);
    });
  }
  tick();
  setInterval(tick, 60000);
})();
