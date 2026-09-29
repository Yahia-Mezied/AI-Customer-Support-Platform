let TICKETS = [];
const ticketRow = (t, extra = '') => `<tr class="row" data-id="${t.id}"><td>#${t.id}</td><td>${esc(t.subject)}</td><td>${esc(enumVal(t.category))}</td><td>${badge(t.priority)}</td><td>${badge(t.status)}</td><td>${fmt(t.created_at)}</td>${extra}</tr>`;
function filterBar() {
  return `<div class="grid grid-cols-2 gap-3 mb-3"><select id="fs"><option value="">All statuses</option>${CFG.STATUSES.map(s => `<option>${s}</option>`).join('')}</select>
  <select id="fp"><option value="">All priorities</option>${CFG.PRIORITIES.map(s => `<option>${s}</option>`).join('')}</select></div>`;
}
function applyFilters(draw) {
  const s = $('#fs').value, p = $('#fp').value;
  draw(TICKETS.filter(t => (!s || enumVal(t.status) === s) && (!p || enumVal(t.priority) === p)));
}
async function renderCustomer(tab = 'list') {
  $('#app').innerHTML = `<div class="hero"><div class="wrap"><p>Customer portal</p><h1>Hi ${esc(USER.name)}, how can we help?</h1></div></div>
  <div class="tabs mb-4"><button data-t="list" class="${tab === 'list' ? 'on' : ''}">My Tickets</button><button data-t="new" class="${tab === 'new' ? 'on' : ''}">Create Ticket</button></div><div id="pane"></div>`;
  document.querySelectorAll('.tabs button').forEach(b => b.onclick = () => renderCustomer(b.dataset.t));
  if (tab === 'new') return newTicketForm();
  try { TICKETS = list(await api(CFG.EP.tickets)); } catch (e) { toast(e.message, true); }
  $('#pane').innerHTML = `<div class="section">${filterBar()}<div class="card"><table><thead><tr><th>ID</th><th>Subject</th><th>Category</th><th>Priority</th><th>Status</th><th>Created</th></tr></thead><tbody id="tb"></tbody></table></div></div>`;
  const draw = rows => { $('#tb').innerHTML = rows.map(t => ticketRow(t)).join('') || '<tr><td colspan="6">No tickets found.</td></tr>';
    document.querySelectorAll('#tb tr.row').forEach(r => r.onclick = () => openTicket(r.dataset.id)); };
  $('#fs').onchange = $('#fp').onchange = () => applyFilters(draw); draw(TICKETS);
}
function newTicketForm() {
  $('#pane').innerHTML = `<div class="section"><div class="card"><h2>New ticket</h2><form id="nt"><label>Subject</label><input id="ts" required>
  <label>Category</label><select id="tc">${CFG.CATEGORIES.map(c => `<option>${c}</option>`).join('')}</select>
  <label>Description</label><textarea id="td" rows="5" required></textarea><button class="btn mt-4">Submit ticket</button></form></div><div id="aiout"></div></div>`;
  $('#nt').onsubmit = async e => {
    e.preventDefault();
    try {
      const t = await api(CFG.EP.tickets, { method: 'POST', body: { subject: $('#ts').value, description: $('#td').value, category: $('#tc').value } });
      toast('Ticket created'); $('#nt').reset();
      $('#aiout').innerHTML = `<div class="card mt-4" style="border-top:4px solid var(--teal)"><h2>AI classification for #${t.id}</h2>
      <p><b>Category:</b> ${esc(t.ai_category || '—')}</p><p><b>Priority:</b> ${esc(t.ai_priority || '—')}</p>
      <p><b>Summary:</b> ${esc(t.ai_summary || '—')}</p><p><b>Suggested action:</b> ${esc(t.ai_suggested_action || '—')}</p>
      <button class="btn btn-sm mt-3" onclick="openTicket(${t.id})">Open ticket</button></div>`;
    } catch (err) { toast(err.message, true); }
  };
}
async function openTicket(id) {
  const isStaff = USER.role !== 'customer';
  let t, msgs = [];
  try { t = await api(CFG.EP.ticket(id)); msgs = list(await api(CFG.EP.messages(id))); } catch (e) { return toast(e.message, true); }
  const thread = () => msgs.map(m => `<div class="msg ${m.sender_id === USER.id ? 'me' : ''}"><small>${esc(m.sender_name || m.sender?.name || 'User #' + m.sender_id)} · ${fmt(m.created_at)}</small>${esc(m.message)}</div>`).join('') || '<p>No messages yet.</p>';
  $('#app').innerHTML = `<div class="section mt-6"><button class="btn btn-o btn-sm mb-3" onclick="route()">← Back</button>
  <div class="card"><h2>#${t.id} ${esc(t.subject)}</h2><p>${badge(t.status)} ${badge(t.priority)} <span class="badge">${esc(enumVal(t.category))}</span></p><p class="mt-3">${esc(t.description)}</p>
  ${isStaff ? `<div class="mt-3 text-sm"><b>AI summary:</b> ${esc(t.ai_summary || '—')}<br><b>AI suggested action:</b> ${esc(t.ai_suggested_action || '—')}</div>` : ''}</div>
  <div class="card mt-4"><h2>Conversation</h2><div id="thread">${thread()}</div>
  <form id="mf" class="mt-3"><textarea id="mt" rows="3" placeholder="Write a reply..." required></textarea>
  <div class="flex gap-3 mt-3">${isStaff ? '<button type="button" id="ai" class="btn btn-o">✨ Suggest AI response</button>' : ''}<button class="btn">Send</button></div></form></div></div>`;
  if (isStaff) $('#ai').onclick = () => suggestResponse(id);
  $('#mf').onsubmit = async e => {
    e.preventDefault();
    try { const m = await api(CFG.EP.messages(id), { method: 'POST', body: { message: $('#mt').value } });
      msgs.push(m); $('#thread').innerHTML = thread(); $('#mt').value = ''; } catch (err) { toast(err.message, true); }
  };
}
function initChat() {
  $('#chat-root').innerHTML = `<button id="chat-btn">💬</button><div id="chat-box" class="card"><div style="background:var(--purple);color:#fff;padding:14px;font-weight:700">AI Support Assistant</div>
  <div id="chat-log"><div class="msg">Hi! Ask me about your tickets or tell me about a new issue.</div></div>
  <form id="cf" class="flex gap-2 p-3"><input id="ci" placeholder="Type a message..." required><button class="btn btn-sm">Send</button></form></div>`;
  $('#chat-btn').onclick = () => $('#chat-box').classList.toggle('open');
  $('#cf').onsubmit = async e => {
    e.preventDefault(); const text = $('#ci').value; $('#ci').value = '';
    const log = $('#chat-log'); log.innerHTML += `<div class="msg me">${esc(text)}</div>`;
    try { const r = await api(CFG.EP.chat, { method: 'POST', body: { message: text } });
      log.innerHTML += `<div class="msg">${esc(r.response || r.reply || r.message || r.answer || JSON.stringify(r))}</div>`; }
    catch (err) { log.innerHTML += `<div class="msg">⚠ ${esc(err.message)}</div>`; }
    log.scrollTop = log.scrollHeight;
  };
}
