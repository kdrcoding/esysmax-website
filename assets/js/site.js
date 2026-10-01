// E-Sys MAX website: menu, buying, the order page, finding a licence, the download.
(function () {
  'use strict';

  var API = 'https://licence.esysmax.com/api/';
  var BOT = 'EsysMaxbot';
  var $ = function (sel, root) { return (root || document).querySelector(sel); };

  function pcId(text) {
    var clean = String(text || '').replace(/[\s-]/g, '').toUpperCase();
    return /^[0-9A-F]{32}$/.test(clean) ? clean : null;
  }
  function say(el, text, kind) {
    if (!el) return;
    el.className = 'note' + (kind ? ' ' + kind : '');
    el.textContent = text || '';
  }
  function busy(button, on, label) {
    if (!button) return;
    if (on) {
      button.dataset.label = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<span class="spinner" aria-hidden="true"></span> ' + (label || 'Please wait');
    } else {
      button.disabled = false;
      if (button.dataset.label) button.innerHTML = button.dataset.label;
    }
  }
  function post(path, body) {
    return fetch(API + path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(body).toString()
    }).then(function (r) { return r.json().then(function (j) { j.status = r.status; return j; }); });
  }
  function telegramLink(pc) { return 'https://t.me/' + BOT + (pc ? '?start=' + pc : ''); }
  function copy(text, button) {
    var done = function () { if (button) { var old = button.textContent; button.textContent = 'Copied'; setTimeout(function () { button.textContent = old; }, 1800); } };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, function () {});
    else {
      var area = document.createElement('textarea');
      area.value = text; document.body.appendChild(area); area.select();
      try { document.execCommand('copy'); done(); } catch (e) { /* select it by hand */ }
      document.body.removeChild(area);
    }
  }
  function showLicence(box, certificate) {
    var text = $('.licence-box', box);
    if (text) text.textContent = certificate;
    var button = $('[data-copy-licence]', box);
    if (button) button.onclick = function () { copy(certificate, button); };
    box.hidden = false;
  }

  // ------------------------------------------------------------ menu, year, reveal
  var head = $('.site-head');
  var toggle = $('.menu-toggle');
  if (toggle && head) {
    toggle.addEventListener('click', function () {
      var open = head.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
  if ('IntersectionObserver' in window) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); seen.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -60px 0px' });
    document.querySelectorAll('.reveal').forEach(function (el) { seen.observe(el); });
  } else {
    document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in'); });
  }

  // ------------------------------------------------------------ download: the newest version from the update feed
  var download = $('[data-download]');
  if (download) {
    fetch('/updates/latest.json', { cache: 'no-store' }).then(function (r) { if (!r.ok) throw new Error(); return r.json(); }).then(function (m) {
      var url = /^https:\/\//.test(m.installer) ? m.installer : '/updates/' + encodeURIComponent(m.installer);
      document.querySelectorAll('[data-download-link]').forEach(function (a) { a.href = url; a.removeAttribute('aria-disabled'); });
      var set = function (key, value) { document.querySelectorAll('[data-dl="' + key + '"]').forEach(function (el) { el.textContent = value; }); };
      set('version', m.version);
      set('size', m.size ? (m.size / 1048576).toFixed(1) + ' MB' : '');
      set('date', String(m.published || '').slice(0, 10));
      set('sha256', m.sha256 || '');
      download.hidden = false;
      var waiting = $('[data-download-waiting]'); if (waiting) waiting.hidden = true;
    }).catch(function () {
      var waiting = $('[data-download-waiting]'); if (waiting) waiting.hidden = false;
    });
  }

  // ------------------------------------------------------------ buy
  var buy = $('#buy-form');
  if (buy) {
    var params = new URLSearchParams(location.search);
    var pcInput = $('#pc');
    var note = $('#buy-note');
    if (pcId(params.get('pc'))) pcInput.value = pcId(params.get('pc'));
    var plan = params.get('plan');
    if (plan === 'year' || plan === 'lifetime') { var radio = $('#plan-' + plan); if (radio) radio.checked = true; }
    var tg = $('#buy-telegram');
    var updateTelegram = function () { if (tg) tg.href = telegramLink(pcId(pcInput.value)); };
    pcInput.addEventListener('input', updateTelegram);
    updateTelegram();
    buy.addEventListener('submit', function (event) {
      event.preventDefault();
      var pc = pcId(pcInput.value);
      var chosen = $('input[name="plan"]:checked', buy);
      if (!pc) { say(note, 'Enter your PC ID: 32 letters and digits from the E-Sys MAX launcher, Help > Licence > Copy this PC\'s ID.', 'bad'); pcInput.focus(); return; }
      if (!chosen) { say(note, 'Choose 1 year or lifetime.', 'bad'); return; }
      var button = $('button[type="submit"]', buy);
      busy(button, true, 'Opening secure payment');
      say(note, '');
      post('checkout', { machine: pc, plan: chosen.value }).then(function (answer) {
        if (answer.ok && answer.url) { location.href = answer.url; return; }
        busy(button, false);
        say(note, answer.reason || 'The payment page could not be opened. Buy on Telegram instead.', 'bad');
      }).catch(function () {
        busy(button, false);
        say(note, 'The payment page could not be reached. Check the internet connection, or buy on Telegram.', 'bad');
      });
    });
  }

  // ------------------------------------------------------------ thank you: the licence of the order
  var order = $('#order');
  if (order) {
    var session = new URLSearchParams(location.search).get('session_id');
    var state = $('#order-state');
    var tries = 0;
    var ask = function () {
      if (!session) { say(state, 'No order was given. If you paid, open the link from the payment page again, or ask @' + BOT + '.', 'bad'); return; }
      fetch(API + 'order?session_id=' + encodeURIComponent(session), { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (answer) {
        if (answer.ok) {
          say(state, 'Payment received. Your licence for PC ' + answer.pc + (answer.until === 'never' ? ' (lifetime)' : ', until ' + answer.until) + ':', 'ok');
          showLicence($('#order-licence'), answer.certificate);
          return;
        }
        if (answer.pending && tries++ < 40) { say(state, answer.reason); setTimeout(ask, 3000); return; }
        say(state, answer.reason || 'The order could not be read. Refresh this page in a minute.', 'bad');
      }).catch(function () {
        if (tries++ < 40) { setTimeout(ask, 3000); return; }
        say(state, 'The order could not be read. Refresh this page in a minute.', 'bad');
      });
    };
    ask();
  }

  // ------------------------------------------------------------ find my licence
  var find = $('#find-form');
  if (find) {
    var findNote = $('#find-note');
    find.addEventListener('submit', function (event) {
      event.preventDefault();
      var pc = pcId($('#find-pc').value);
      var email = $('#find-email').value.trim();
      if (!pc || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { say(findNote, 'Enter the e-mail of your order and your PC ID.', 'bad'); return; }
      var button = $('button[type="submit"]', find);
      busy(button, true, 'Looking');
      post('lookup', { machine: pc, email: email }).then(function (answer) {
        busy(button, false);
        if (answer.ok) { say(findNote, 'Found it. Paste it into Help > Licence in the launcher.', 'ok'); showLicence($('#find-licence'), answer.certificate); }
        else say(findNote, answer.reason || 'Nothing found.', 'bad');
      }).catch(function () { busy(button, false); say(findNote, 'Not reachable just now. Try again in a minute.', 'bad'); });
    });
  }

  // Telegram links that carry a PC ID typed on the page.
  document.querySelectorAll('[data-telegram-from]').forEach(function (a) {
    var input = $(a.getAttribute('data-telegram-from'));
    var update = function () { a.href = telegramLink(input && pcId(input.value)); };
    if (input) input.addEventListener('input', update);
    update();
  });
})();
