/* ================================================================
   K9 Technologies — Calendar / appointment booking
================================================================ */

let CAL_SLOTS = [];
let CAL_DAYS  = [];
let CAL_PAGE  = 0;
let CAL_SELECTED_DAY = null;
let CAL_SELECTED_SLOT = null;

async function loadSlots(){
  try{
    const r = await fetch('/appointments/slots');
    const d = await r.json();
    CAL_SLOTS = d.slots || [];
    groupSlots();
    renderCalendar();
  } catch {
    document.getElementById('cal-slots').innerHTML =
      '<div class="cal-empty">Could not load slots. Please refresh.</div>';
  }
}

function groupSlots(){
  const map = {};
  CAL_SLOTS.forEach(iso => {
    const key = new Date(iso).toISOString().slice(0,10);
    (map[key] = map[key] || []).push(iso);
  });
  CAL_DAYS = Object.keys(map).sort().map(k => ({
    key:k, date:new Date(k+'T00:00:00'), slots:map[k]
  }));
}

function renderCalendar(){
  const container = document.getElementById('cal-days');
  const start = CAL_PAGE * 7;
  const view = CAL_DAYS.slice(start, start + 7);
  if(!view.length){
    container.innerHTML = '<div class="cal-empty" style="grid-column:1/-1">No more dates available.</div>';
    document.getElementById('cal-slots').innerHTML = '';
    return;
  }
  const dows = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const fmt = new Intl.DateTimeFormat(undefined, {month:'short', day:'numeric'});
  document.getElementById('cal-week-label').textContent =
    fmt.format(view[0].date) + ' – ' + fmt.format(view[view.length-1].date);

  container.innerHTML = view.map(d => {
    const active = d.key === CAL_SELECTED_DAY ? 'active' : '';
    return `<div class="cal-day ${active}" data-key="${d.key}">
              <div class="dow">${dows[d.date.getDay()]}</div>
              <div class="dom">${d.date.getDate()}</div>
            </div>`;
  }).join('');

  container.querySelectorAll('.cal-day').forEach(el => el.onclick = () => {
    CAL_SELECTED_DAY  = el.dataset.key;
    CAL_SELECTED_SLOT = null;
    renderCalendar(); renderSlots(); updateSelected();
  });

  document.getElementById('cal-prev').disabled = CAL_PAGE === 0;
  document.getElementById('cal-next').disabled = start + 7 >= CAL_DAYS.length;

  if(!CAL_SELECTED_DAY || !view.find(d => d.key === CAL_SELECTED_DAY)){
    CAL_SELECTED_DAY = view[0].key;
  }
  renderSlots();
}

function renderSlots(){
  const day = CAL_DAYS.find(d => d.key === CAL_SELECTED_DAY);
  const wrap = document.getElementById('cal-slots');
  if(!day || !day.slots.length){
    wrap.innerHTML = '<div class="cal-empty">No times available on this day.</div>';
    return;
  }
  const fmt = new Intl.DateTimeFormat(undefined, {hour:'numeric', minute:'2-digit'});
  wrap.innerHTML = day.slots.map(iso => {
    const active = iso === CAL_SELECTED_SLOT ? 'active' : '';
    return `<button type="button" class="cal-slot ${active}" data-iso="${iso}">${fmt.format(new Date(iso))}</button>`;
  }).join('');
  wrap.querySelectorAll('.cal-slot').forEach(b => b.onclick = () => {
    CAL_SELECTED_SLOT = b.dataset.iso;
    renderSlots(); updateSelected();
  });
}

function updateSelected(){
  const sel = document.getElementById('cal-selected');
  const btn = document.getElementById('b-submit');
  if(!CAL_SELECTED_SLOT){
    sel.textContent = 'No time selected yet — pick a slot on the left.';
    sel.classList.remove('has-slot');
    btn.disabled = true;
    return;
  }
  const fmt = new Intl.DateTimeFormat(undefined, {weekday:'long', month:'long', day:'numeric', hour:'numeric', minute:'2-digit'});
  sel.textContent = 'Selected: ' + fmt.format(new Date(CAL_SELECTED_SLOT));
  sel.classList.add('has-slot');
  btn.disabled = false;
}

document.getElementById('cal-prev').onclick = () => { if(CAL_PAGE > 0){ CAL_PAGE--; renderCalendar(); } };
document.getElementById('cal-next').onclick = () => { if((CAL_PAGE+1)*7 < CAL_DAYS.length){ CAL_PAGE++; renderCalendar(); } };

/* Tabs */
document.querySelectorAll('.cal-tab').forEach(t => t.onclick = () => {
  document.querySelectorAll('.cal-tab').forEach(x => x.classList.toggle('active', x === t));
  document.querySelectorAll('.cal-tab-pane').forEach(p => p.classList.toggle('active', p.id === 'tab-'+t.dataset.tab));
});

/* Booking */
document.getElementById('book-form').addEventListener('submit', async e => {
  e.preventDefault();
  const err = document.getElementById('book-err'); err.classList.remove('show');
  const ok  = document.getElementById('book-ok');  ok.classList.remove('show');
  if(!CAL_SELECTED_SLOT){
    err.textContent = 'Please select a time first.'; err.classList.add('show'); return;
  }
  const body = {
    name:  document.getElementById('b-name').value.trim(),
    email: document.getElementById('b-email').value.trim(),
    phone: document.getElementById('b-phone').value.trim(),
    topic: document.getElementById('b-topic').value.trim() || 'Discovery call',
    notes: document.getElementById('b-notes').value.trim(),
    slot_iso: CAL_SELECTED_SLOT
  };
  try{
    const r = await fetch('/appointments', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const d = await r.json();
    if(!d.ok){ err.textContent = d.error || 'Could not book that slot.'; err.classList.add('show'); return; }
    ok.classList.add('show');
    document.getElementById('book-form').reset();
    CAL_SELECTED_SLOT = null; updateSelected();
    await loadSlots();
  } catch { err.textContent = 'Network error — please try again.'; err.classList.add('show'); }
});

/* Manage booking */
async function lookupBooking(){
  const email = document.getElementById('m-email').value.trim();
  const out = document.getElementById('m-result');
  if(!email){ out.innerHTML = '<div class="cal-empty">Enter your email above.</div>'; return; }
  out.innerHTML = '<div class="cal-empty">Searching…</div>';
  try{
    const r = await fetch('/appointments?email=' + encodeURIComponent(email));
    const list = await r.json();
    if(!list.length){ out.innerHTML = '<div class="cal-empty">No bookings found for that email.</div>'; return; }
    const fmt = new Intl.DateTimeFormat(undefined, {weekday:'long', month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});
    out.innerHTML = list.map(a => `
      <div class="m-booking">
        <h4>${a.topic||'Discovery call'} <span style="font-size:.7rem;color:var(--text2);font-weight:500">[${a.status}]</span></h4>
        <p><strong>When:</strong> ${fmt.format(new Date(a.slot_iso))}</p>
        <p><strong>Name:</strong> ${a.name}</p>
        ${a.phone ? `<p><strong>Phone:</strong> ${a.phone}</p>` : ''}
        ${a.status === 'booked' ? `<div class="m-actions">
          <button onclick="rescheduleBooking('${a.id}')">Reschedule</button>
          <button class="danger" onclick="cancelBooking('${a.id}')">Cancel</button>
        </div>` : ''}
      </div>`).join('');
  } catch { out.innerHTML = '<div class="cal-empty">Lookup failed. Try again.</div>'; }
}

async function cancelBooking(id){
  if(!confirm('Cancel this booking?')) return;
  await fetch('/appointments/' + id, {method:'DELETE'});
  await loadSlots();
  lookupBooking();
}

async function rescheduleBooking(id){
  if(!CAL_SELECTED_SLOT){ alert('Pick a new time on the Book tab first, then come back here.'); return; }
  await fetch('/appointments/' + id, {
    method:'PATCH',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({slot_iso: CAL_SELECTED_SLOT})
  });
  CAL_SELECTED_SLOT = null; updateSelected();
  await loadSlots();
  lookupBooking();
}

loadSlots();
