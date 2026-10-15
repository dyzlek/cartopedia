// Aucun script en ligne (CSP). Deux comportements :
// 1. Copier le jeton Cap dans le champ caché du formulaire.
// 2. Rafraîchir le compte à rebours du paquet gratuit une fois par minute (pas de aria-live).
(function () {
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
