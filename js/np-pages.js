/* Inner pages: mobile menu, nav shadow, and the Get Started form (same 100X inquiry API as the homepage form). */
(function () {
  var hb = document.getElementById('hamburger'), mob = document.getElementById('mobNav');
  if (hb && mob) {
    hb.addEventListener('click', function () { mob.classList.toggle('open'); });
    mob.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { mob.classList.remove('open'); }); });
  }
  var nav = document.getElementById('navbar');
  if (nav) window.addEventListener('scroll', function () { nav.classList.toggle('scrolled', window.scrollY > 8); }, { passive: true });
  var form = document.getElementById('getStartedForm');
  if (!form) return;
  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var v = function (id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; };
    var msg = document.getElementById('form-msg'), btn = document.getElementById('submitBtn');
    var first = v('firstName'), last = v('lastName'), co = v('company'), em = v('email');
    if (!first || !last || !co || !em) { msg.className = 'err'; msg.textContent = 'Please fill in all required fields.'; return; }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)) { msg.className = 'err'; msg.textContent = 'Please enter a valid email address.'; return; }
    btn.disabled = true; btn.textContent = 'Sending…'; msg.className = ''; msg.textContent = '';
    var notes = [v('role') && ('Role: ' + v('role')), 'Location: ' + form.getAttribute('data-location'), v('message')].filter(Boolean).join('\n');
    var body = { name: first + ' ' + last, employer_name: first + ' ' + last, company: co, employer_company: co,
      email: em, employer_email: em, phone: v('phone'), inquiry_type: v('division') || form.getAttribute('data-inquiry') || 'general',
      notes: notes, message: notes, source: 'northpointsearchgroup.com' + window.location.pathname };
    try {
      var res = await fetch('https://100xrecruiting.com/api/public/inquiry', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      var data = {}; try { data = await res.json(); } catch (_) {}
      if (res.ok && data.ok) { msg.className = 'ok'; msg.textContent = 'Request sent. We will be in touch within one business day.'; form.reset(); }
      else { msg.className = 'err'; msg.textContent = 'Something went wrong. Please call us at 678.777.5627.'; }
    } catch (err) { msg.className = 'err'; msg.textContent = 'Network error. Please call us at 678.777.5627.'; }
    finally { btn.disabled = false; btn.textContent = 'Get Started'; }
  });
})();
