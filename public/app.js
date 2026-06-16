'use strict';

function tradition() {
  const el = document.querySelector('input[name="tradition"]:checked');
  return el ? el.value : 'phugpa';
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function annotations(d) {
  const parts = [];
  if (d.is_leap_month) parts.push('leap month');
  if (d.is_leap_day) parts.push('leap day');
  return parts;
}

function renderTibetan(box, r) {
  const yn = r.year_name;
  const notes = annotations(r);
  box.innerHTML = `
    <div class="big">${escapeHtml(yn.label)} Year</div>
    <dl>
      <div><dt>Tibetan month</dt><dd>${r.month}${r.is_leap_month ? ' <span class="tag">leap</span>' : ''}</dd></div>
      <div><dt>Tibetan day</dt><dd>${r.day}${r.is_leap_day ? ' <span class="tag">leap</span>' : ''}</dd></div>
      <div><dt>Tibetan royal year</dt><dd>${yn.royal_year}</dd></div>
      <div><dt>Rabjung</dt><dd>${yn.rabjung_cycle}</dd></div>
    </dl>
    ${notes.length ? `<p class="note">This is a ${notes.join(' and ')}.</p>` : ''}
  `;
}

function renderWestern(box, g) {
  box.hidden = false;
  box.classList.remove('error');
  box.innerHTML = `<div class="big">${escapeHtml(g.display)}</div>`;
}

function showResult(box, html) {
  box.hidden = false;
  box.classList.remove('error');
  box.innerHTML = html;
}

function showError(box, msg) {
  box.hidden = false;
  box.classList.add('error');
  box.innerHTML = `<p class="note">${escapeHtml(msg)}</p>`;
}

function setBusy(box) {
  box.hidden = false;
  box.classList.remove('error');
  box.innerHTML = '<p class="note">Converting…</p>';
}

async function request(form, mode) {
  const params = new URLSearchParams(new FormData(form));
  params.set('mode', mode);
  params.set('tradition', tradition());
  const res = await fetch('api.php', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  return res.json();
}

// --- ambiguous Tibetan dates -----------------------------------------------
// A day/month number can occur twice (a leap day or leap month duplicates it).
// Show every match labelled by its Tibetan distinction — the user reads the one
// they meant rather than choosing between Western dates they don't know yet.

function renderWesternMulti(box, cands) {
  const unit = cands.some((c) => c.is_leap_day) ? 'day' : 'month';
  const rows = cands.map((c) => {
    const tag = (c.is_leap_day || c.is_leap_month) ? `leap ${unit}` : `regular ${unit}`;
    return '<div class="multi-row">' +
      `<span class="choice-label">${tag}</span>` +
      `<span class="choice-date">${escapeHtml(c.result.display)}</span>` +
      '</div>';
  }).join('');
  box.hidden = false;
  box.classList.remove('error');
  box.innerHTML =
    `<p class="note">This Tibetan date occurs twice this year — both matches:</p>` +
    `<div class="multi">${rows}</div>`;
}

// --- Western -> Tibetan ----------------------------------------------------

document.getElementById('form-g2t').addEventListener('submit', async (e) => {
  e.preventDefault();
  const box = document.getElementById('result-g2t');
  setBusy(box);
  try {
    const data = await request(e.currentTarget, 'g2t');
    if (!data.ok) { showError(box, data.error || 'Conversion failed.'); return; }
    box.classList.remove('error');
    renderTibetan(box, data.result);
  } catch (err) {
    showError(box, 'Could not reach the converter. Please try again.');
  }
});

// --- Tibetan -> Western ----------------------------------------------------

document.getElementById('form-t2g').addEventListener('submit', async (e) => {
  e.preventDefault();
  const box = document.getElementById('result-t2g');
  setBusy(box);
  try {
    const data = await request(e.currentTarget, 't2g');
    if (!data.ok) { showError(box, data.error || 'Conversion failed.'); return; }

    const cands = data.candidates || [];
    if (cands.length === 0) {
      showError(box,
        'No such Tibetan day. This date does not exist this year — it may be ' +
        'a skipped day, or that month/day number does not occur.');
    } else if (cands.length === 1) {
      renderWestern(box, cands[0].result);
    } else {
      renderWesternMulti(box, cands);
    }
  } catch (err) {
    showError(box, 'Could not reach the converter. Please try again.');
  }
});

// Assemble the feedback email from its parts so the literal address never
// appears in the page source for scrapers to harvest.
const feedback = document.getElementById('feedback');
if (feedback) {
  const addr = feedback.dataset.user + '@' + feedback.dataset.domain;
  feedback.href = 'mailto:' + addr + '?subject=' +
    encodeURIComponent('Tibetan calendar converter — feedback');
}

// Switching tradition invalidates any shown result (Phugpa and Tsurphu can
// differ by a day), so clear both panels rather than leave a stale answer.
document.querySelectorAll('input[name="tradition"]').forEach((el) => {
  el.addEventListener('change', () => {
    ['result-g2t', 'result-t2g'].forEach((id) => {
      const b = document.getElementById(id);
      b.hidden = true;
      b.classList.remove('error');
      b.innerHTML = '';
    });
  });
});
