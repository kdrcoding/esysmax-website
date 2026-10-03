// E-Sys MAX website: menu, buying, the order page, finding a licence, the download.
(function () {
  'use strict';

  var API = 'https://licence.esysmax.com/api/';
  var BOT = 'EsysMaxbot';
  var SERVER_PROBLEM = 'The licence server had a problem; please try again in a minute.';
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
    }).then(function (r) {
      // An answer that is not JSON (an error page from the server) means the server was reached but had a problem;
      // only a failed connection ends in the caller's catch (not reachable, check the internet).
      return r.json().then(function (j) {
        if (!j || typeof j !== 'object') throw new Error();
        j.status = r.status; return j;
      }).catch(function () { return { ok: false, status: r.status, reason: SERVER_PROBLEM }; });
    });
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
    var setMenu = function (open) {
      head.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Menu');
    };
    toggle.addEventListener('click', function () { setMenu(!head.classList.contains('open')); });
    // A tap on a menu link (also /#faq on the home page) closes the menu; so does Escape.
    head.querySelectorAll('.nav a, .head-cta a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && head.classList.contains('open')) { setMenu(false); toggle.focus(); } });
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
      if (!m || !m.installer || !m.version) throw new Error();
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
    // ?plan=month|year|lifetime picks that plan; without it lifetime stays chosen (checked in the page).
    if (plan === 'month' || plan === 'year' || plan === 'lifetime') { var radio = $('#plan-' + plan); if (radio) radio.checked = true; }
    var tg = $('#buy-telegram');
    var updateTelegram = function () { if (tg) tg.href = telegramLink(pcId(pcInput.value)); };
    pcInput.addEventListener('input', updateTelegram);
    updateTelegram();
    var buyButton = $('button[type="submit"]', buy);
    // Back from Stripe: the browser may show this page from its cache, with the button still busy.
    window.addEventListener('pageshow', function (e) { if (e.persisted) busy(buyButton, false); });
    buy.addEventListener('submit', function (event) {
      event.preventDefault();
      var pc = pcId(pcInput.value);
      var chosen = $('input[name="plan"]:checked', buy);
      if (!pc) { say(note, 'Enter your PC ID: 32 letters and digits from the E-Sys MAX launcher, Help > Licence > Copy this PC\'s ID.', 'bad'); pcInput.focus(); return; }
      if (!chosen) { say(note, 'Choose a plan: 1 month, 1 year or lifetime.', 'bad'); return; }
      if (!$('#accept-terms').checked || !$('#accept-risk').checked || !$('#accept-delivery').checked) {
        say(note, 'Please tick the three boxes: the Terms, the coding risk and the delivery of your licence.', 'bad');
        return;
      }
      var button = buyButton;
      busy(button, true, 'Opening secure payment');
      say(note, '');
      // The Terms version comes from the page (tools/build.py writes it from one place).
      post('checkout', { machine: pc, plan: chosen.value, terms: buy.getAttribute('data-terms') || '', risk: 'yes', delivery: 'yes' }).then(function (answer) {
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
        if (answer.pending) {
          if (tries++ < 40) { say(state, answer.reason); setTimeout(ask, 3000); return; }
          say(state, 'Your payment is still being processed. Refresh this page in a minute, or ask @' + BOT + '.');
          return;
        }
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
      // A new search starts clean: no licence from the last search under a new answer.
      var found = $('#find-licence');
      if (found) { found.hidden = true; var box = $('.licence-box', found); if (box) box.textContent = ''; }
      say(findNote, '');
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

  // ------------------------------------------------------------ contact form (for people without Telegram)
  var contact = $('#contact-form');
  if (contact) {
    var cNote = $('#contact-note');
    var cTopic = $('#c-topic');
    var cPc = $('#c-pc');
    var cLicence = $('#c-licence');
    var cMessage = $('#c-message');
    var cCount = $('#c-count');
    var cParams = new URLSearchParams(location.search);
    if (pcId(cParams.get('pc'))) cPc.value = pcId(cParams.get('pc'));
    if (/^(question|move|licence)$/.test(cParams.get('topic') || '')) cTopic.value = cParams.get('topic');
    // A move needs the new PC's ID, the licence ID, the e-mail of the order and a reason (one move per licence).
    var cReason = $('#c-reason');
    var cDetails = $('#c-details');
    var showTopic = function () {
      var move = cTopic.value === 'move';
      $('#c-move').hidden = !move;
      $('#c-pc-opt').textContent = move ? '(of the new PC)' : '(optional)';
    };
    cReason.addEventListener('change', function () {
      $('#c-details-opt').textContent = cReason.value === 'other' ? '(needed)' : '(optional)';
    });
    var count = function () { cCount.textContent = cMessage.value.length; };
    cTopic.addEventListener('change', showTopic);
    cMessage.addEventListener('input', count);
    showTopic();
    count();
    var fail = function (field, text) {
      say(cNote, text, 'bad');
      if (field) { field.setAttribute('aria-invalid', 'true'); field.focus(); }
    };
    contact.addEventListener('submit', function (event) {
      event.preventDefault();
      contact.querySelectorAll('[aria-invalid]').forEach(function (el) { el.removeAttribute('aria-invalid'); });
      var email = $('#c-email').value.trim();
      var pcText = cPc.value.trim();
      var pc = pcId(pcText);
      var licence = cLicence.value.trim().toUpperCase();
      var message = cMessage.value.trim();
      var move = cTopic.value === 'move';
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { fail($('#c-email'), 'Enter your e-mail address: we answer by e-mail.'); return; }
      if (move && !pcText) { fail(cPc, 'For a move, enter the PC ID of the new PC: E-Sys MAX launcher, Help > Licence > Copy this PC\'s ID.'); return; }
      if (pcText && !pc) { fail(cPc, 'The PC ID is 32 letters and digits: E-Sys MAX launcher, Help > Licence > Copy this PC\'s ID.'); return; }
      if (licence && !/^[A-Z0-9][A-Z0-9-]{3,39}$/.test(licence)) { fail(cLicence, 'The licence ID looks like EMX-0123456789ABCDEF: Help > Licence in E-Sys MAX.'); return; }
      if (move && !licence) { fail(cLicence, 'For a move, add your licence ID: Help > Licence in E-Sys MAX on the old PC, or your order page. No licence ID at hand? Choose the topic "A question".'); return; }
      if (move && !cReason.value) { fail(cReason, 'Choose why the licence has to move.'); return; }
      if (move && cReason.value === 'other' && cDetails.value.trim().length < 10) { fail(cDetails, 'Please explain in a few words (at least 10 characters) why the licence has to move.'); return; }
      if (message.length < 10) { fail(cMessage, 'Please write a little more: at least 10 characters.'); return; }
      if (message.length > 3000) { fail(cMessage, 'Please keep the message to 3000 characters.'); return; }
      var button = $('button[type="submit"]', contact);
      busy(button, true, 'Sending');
      say(cNote, '');
      post('contact', {
        name: $('#c-name').value.trim().slice(0, 60), email: email, machine: pc || '', licence: licence,
        topic: cTopic.value, message: message, website: $('#c-website').value,
        reason: move ? cReason.value : '', details: move ? cDetails.value.trim().slice(0, 300) : ''
      }).then(function (answer) {
        busy(button, false);
        if (answer.ok) {
          contact.hidden = true;
          var done = $('#contact-done');
          done.hidden = false;
          done.focus();
          return;
        }
        say(cNote, answer.reason || 'Could not send just now. Try again in a minute, or write on Telegram: @' + BOT + '.', 'bad');
      }).catch(function () {
        busy(button, false);
        say(cNote, 'Could not send just now. Try again in a minute, or write on Telegram: @' + BOT + '.', 'bad');
      });
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
