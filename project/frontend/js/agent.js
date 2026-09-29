let AGENTS = [];
async function renderAgent() {
  $('#app').innerHTML = `<div class="hero"><div class="wrap"><p>Support workspace</p><h1>Assigned tickets</h1></div></div><div class="section" id="ag"></div>`;
  try { TICKETS = list(await api(CFG.EP.tickets)); } catch (e) { toast(e.message, true); }
  try { AGENTS = list(await api(CFG.EP.users)).filter(u => String(enumVal(u.role)).toLowerCase() === 'agent'); } catch (e) { AGENTS = []; }
  $('#ag').innerHTML = `${filterBar()}<div class="card"><table><thead><tr><th>ID</th><th>Subject</th><th>Category</th><th>Priority</th><th>Status</th><th>Created</th><th>Update status</th>${AGENTS.length ? '<th>Reassign</th>' : ''}<th></th></tr></thead><tbody id="tb"></tbody></table></div>`;
  const draw = rows => {
    $('#tb').innerHTML = rows.map(t => `<tr class="row" data-id="${t.id}"><td>#${t.id}</td><td>${esc(t.subject)}</td><td>${esc(enumVal(t.category))}</td><td>${badge(t.priority)}</td><td>${badge(t.status)}</td><td>${fmt(t.created_at)}</td>
    <td><select data-st="${t.id}">${CFG.STATUSES.map(s => `<option ${s === enumVal(t.status) ? 'selected' : ''}>${s}</option>`).join('')}</select></td>
    ${AGENTS.length ? `<td><select data-as="${t.id}"><option value="">Unassigned</option>${AGENTS.map(a => `<option value="${a.id}" ${a.id === t.assigned_agent_id ? 'selected' : ''}>${esc(a.name)}</option>`).join('')}</select></td>` : ''}
    <td><button class="btn btn-o btn-sm" data-es="${t.id}">Escalate</button></td></tr>`).join('') || '<tr><td colspan="9">No tickets.</td></tr>';
    document.querySelectorAll('#tb tr.row').forEach(r => r.onclick = () => openTicket(r.dataset.id));
    document.querySelectorAll('#tb select,#tb button').forEach(el => el.onclick = e => e.stopPropagation());
    document.querySelectorAll('[data-st]').forEach(s => s.onchange = () => patch(s.dataset.st, { status: s.value }));
    document.querySelectorAll('[data-as]').forEach(s => s.onchange = () => patch(s.dataset.as, { assigned_agent_id: s.value ? +s.value : null }));
    document.querySelectorAll('[data-es]').forEach(b => b.onclick = async () => {
      try { await api(CFG.EP.escalate(b.dataset.es), { method: 'POST' }); toast('Ticket escalated'); renderAgent(); } catch (e) { toast(e.message, true); } });
  };
  $('#fs').onchange = $('#fp').onchange = () => applyFilters(draw); draw(TICKETS);
}
async function patch(id, body) {
  try { await api(CFG.EP.ticket(id), { method: 'PATCH', body }); toast('Ticket updated'); } catch (e) { toast(e.message, true); }
}
async function suggestResponse(id) {
  const btn = $('#ai'); btn.disabled = true; btn.textContent = 'Generating...';
  try {
    const r = await api(CFG.EP.suggest, { method: 'POST', body: { ticket_id: +id } });
    $('#mt').value = r.suggested_response || r.suggestion || r.response || r.reply || (typeof r === 'string' ? r : JSON.stringify(r));
    toast('Review and edit the draft before sending'); $('#mt').focus();
  } catch (e) { toast(e.message, true); }
  btn.disabled = false; btn.textContent = '✨ Suggest AI response';
}
