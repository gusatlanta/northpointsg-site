/* HUMAN_CHECK_v1 — Cloudflare Turnstile's "Verify you are human" box for this site's forms.
   Gus 11-27: bot requests full of random letters were reaching the team. 100X checks the box's
   token on /api/public/inquiry (INQUIRY_HUMAN_CHECK_v1 in the hundredx app.py) for every site on
   its list. The same file runs on Staff Financial, LawStaff, NorthPoint, Hire School Staff and
   IEP Staff (MedPoint has the same code inline in its js/main.js).

   The key is 100X's public Turnstile site key. This site's domain has to be on that key's hostname
   list in Cloudflare (the "100X sign-up" widget), or the box shows error 110200.

   In a form's submit handler:
     if (window.HumanCheck && HumanCheck.blocked(form)) return;   // box loaded, not passed: says so
     body.cf_turnstile_response = window.HumanCheck ? HumanCheck.token(form) : '';
     ...once the answer is read:
     if (window.HumanCheck && HumanCheck.refused(form, json)) { put the button back; return; }
   HumanCheck.attach(form) puts the box above the form's submit button, plus a hidden hp_website
   honeypot when the form has none. A form with data-human-check gets it on page load.
   The page never blocks more than the server: if the box can't load, the form still sends and
   100X decides. refused() also resets the box, because a token works only once. */
(function () {
  if (window.HumanCheck) return;
  var SITE_KEY = '0x4AAAAAAFVLCgI7uu3nWXEb';
  // Local testing only: ?tskey= swaps in one of Cloudflare's published test keys on localhost.
  try {
    if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) {
      SITE_KEY = new URLSearchParams(location.search).get('tskey') || SITE_KEY;
    }
  } catch (e) {}
  var WAIT_MSG = 'Please complete the "Verify you are human" box above, then send again.';
  var LOAD_MSG = 'The "Verify you are human" box didn\'t load. Please refresh the page and try again.';
  var checks = [];
  var started = false;

  function find(form) {
    for (var i = 0; i < checks.length; i++) if (checks[i].form === form) return checks[i];
    return null;
  }
  function render(c) {
    if (c.id != null || !window.turnstile) return;
    try {
      c.id = window.turnstile.render(c.box, {
        sitekey: SITE_KEY, theme: 'light', 'response-field': false,
        callback: function () { c.failed = null; c.msg.hidden = true; },
        'error-callback': function (code) { c.failed = code || 'error'; }
      });
    } catch (e) { c.failed = 'render'; }
  }
  function start() {
    if (started) return;
    started = true;
    window.__humanCheckReady = function () { checks.forEach(render); };
    if (window.turnstile) { window.__humanCheckReady(); return; }
    var s = document.createElement('script');
    s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit&onload=__humanCheckReady';
    s.async = true;
    s.defer = true;
    s.onerror = function () { checks.forEach(function (c) { c.failed = c.failed || 'script'; }); };
    document.head.appendChild(s);
  }
  function show(c, text) { c.msg.textContent = text; c.msg.hidden = false; }

  function attach(form, opts) {
    if (!form) return null;
    var had = find(form);
    if (had) return had;
    opts = opts || {};
    if (!form.querySelector('input[name="hp_website"]')) {
      var hp = document.createElement('div');
      hp.setAttribute('aria-hidden', 'true');
      hp.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;';
      hp.innerHTML = '<label>Leave this empty <input type="text" name="hp_website" tabindex="-1" autocomplete="off"></label>';
      form.appendChild(hp);
    }
    var before = opts.before
      || form.querySelector('button[type="submit"], input[type="submit"], button:not([type])')
      || null;
    var box = document.createElement('div');
    box.className = 'human-check';
    box.style.cssText = 'margin:4px 0 14px;min-height:65px;';
    var msg = document.createElement('p');
    msg.className = 'human-check-msg';
    msg.setAttribute('role', 'alert');
    msg.hidden = true;
    msg.style.cssText = 'color:#b42318;font-size:.88rem;font-weight:500;margin:-6px 0 12px;';
    var parent = before ? before.parentNode : form;
    parent.insertBefore(box, before);
    parent.insertBefore(msg, before);
    var c = { form: form, box: box, msg: msg, id: null, failed: null };
    checks.push(c);
    start();
    if (window.turnstile) render(c);
    return c;
  }
  function token(form) {
    var c = find(form);
    try { return (c && c.id != null && window.turnstile && window.turnstile.getResponse(c.id)) || ''; }
    catch (e) { return ''; }
  }
  function blocked(form) {
    var c = find(form);
    if (!c) return false;
    if (!token(form) && c.id != null && !c.failed) { show(c, WAIT_MSG); return true; }
    c.msg.hidden = true;
    return false;
  }
  function refused(form, json) {
    var c = find(form);
    if (!c) return false;
    try { if (c.id != null && window.turnstile) window.turnstile.reset(c.id); } catch (e) {}
    if (json && json.error === 'human_check') {
      show(c, c.failed ? LOAD_MSG : (json.message || WAIT_MSG));
      return true;
    }
    return false;
  }

  window.HumanCheck = { attach: attach, token: token, blocked: blocked, refused: refused };
  function auto() {
    var forms = document.querySelectorAll('form[data-human-check]');
    for (var i = 0; i < forms.length; i++) attach(forms[i]);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto);
  else auto();
})();
