function countBy(arr, f) { return arr.reduce((o, x) => { const k = f(x) || 'Unassigned'; o[k] = (o[k] || 0) + 1; return o; }, {}); }
function bars(obj) {
  const max = Math.max(1, ...Object.values(obj));
  return Object.entries(obj).map(([k, v]) => `<div class="mb-2 text-sm"><div class="flex justify-between"><span>${esc(k)}</span><b>${v}</b></div><div class="bar" style="width:${v / max * 100}%"></div></div>`).join('') || '<p>No data.</p>';
}
async function renderAdmin() {
  $('#app').innerHTML = `<div class="hero"><div class="wrap"><p>Administration</p><h1>Platform overview</h1></div></div><div id="ad"></div>`;
  let tickets = [], users = [], stats = {};
  try { tickets = list(await api(CFG.EP.tickets)); } catch (e) {}
  try { users = list(await api(CFG.EP.users)); } catch (e) { toast(e.message, true); }
  try { stats = await api(CFG.EP.stats) || {}; } catch (e) {}
  const st = s => tickets.filter(t => enumVal(t.status) === s).length;
  const pick = (k, alt) => stats[k] ?? stats[k.replace('_tickets', '')] ?? alt;
  const kpis = [['Total Tickets', pick('total_tickets', tickets.length)], ['Open', pick('open_tickets', st('Open'))], ['In Progress', pick('in_progress_tickets', st('In Progress'))],
    ['Resolved', pick('resolved_tickets', st('Resolved'))], ['Critical', pick('critical_tickets', tickets.filter(t => enumVal(t.priority) === 'Critical').length)]];
  const names = Object.fromEntries(users.map(u => [u.id, u.name]));
  $('#ad').innerHTML = `<div class="grid grid-cols-2 md:grid-cols-5 gap-4">${kpis.map(([l, v]) => `<div class="card kpi"><b>${v}</b>${l}</div>`).join('')}</div>
  <div class="section grid md:grid-cols-2 gap-4"><div class="card"><h2>By category</h2>${bars(countBy(tickets, t => enumVal(t.category)))}</div>
  <div class="card"><h2>Agent workload</h2>${bars(countBy(tickets, t => names[t.assigned_agent_id]))}</div></div>
  <div class="section"><div class="flex justify-between"><h2>Users & agents</h2><button class="btn btn-sm" id="na">+ New agent</button></div>
  <div class="card"><table><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead><tbody>
  ${users.map(u => { const on = String(enumVal(u.account_status)).toLowerCase() === 'active'; return `<tr><td>${esc(u.name)}</td><td>${esc(u.email)}</td><td>${badge(u.role)}</td><td>${badge(u.account_status)}</td>
  <td>
    <div class="flex gap-2">
      <button class="btn btn-o btn-sm" data-edit="${u.id}">Edit</button>
      ${u.id === USER.id ? '' : `<button class="btn btn-o btn-sm" data-u="${u.id}" data-on="${on}">${on ? 'Disable' : 'Enable'}</button>`}
    </div>
  </td></tr>`; }).join('')}</tbody></table></div>
  <div id="af2"></div></div>`;
  document.querySelectorAll('[data-u]').forEach(b => b.onclick = async () => {
    try { await api(CFG.EP.user(b.dataset.u), { method: 'PATCH', body: { account_status: b.dataset.on === 'true' ? 'disabled' : 'active' } }); renderAdmin(); } catch (e) { toast(e.message, true); } });
  document.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => {
    const targetUser = users.find(u => String(u.id) === String(b.dataset.edit));
    if (!targetUser) return;
    $('#af2').innerHTML = `<form id="ef" class="card mt-4" style="border-top:4px solid var(--purple)">
      <div class="flex justify-between items-center mb-3">
        <h2>Edit User / Agent: ${esc(targetUser.name)} (#${targetUser.id})</h2>
        <button type="button" class="btn btn-o btn-sm" onclick="$('#af2').innerHTML=''">Cancel</button>
      </div>
      <label>Name</label><input id="en" value="${esc(targetUser.name)}" required>
      <label>Email</label><input id="ee" type="email" value="${esc(targetUser.email)}" required>
      <label>Role</label>
      <select id="er">
        <option value="customer" ${targetUser.role === 'customer' ? 'selected' : ''}>Customer</option>
        <option value="agent" ${targetUser.role === 'agent' ? 'selected' : ''}>Agent</option>
        <option value="admin" ${targetUser.role === 'admin' ? 'selected' : ''}>Admin</option>
      </select>
      <div class="flex gap-3 mt-4">
        <button class="btn">Save changes</button>
      </div>
    </form>`;
    $('#ef').onsubmit = async e => {
      e.preventDefault();
      try {
        await api(CFG.EP.user(targetUser.id), {
          method: 'PATCH',
          body: { name: $('#en').value, email: $('#ee').value, role: $('#er').value }
        });
        toast('User updated successfully');
        if (targetUser.id === USER.id) {
          USER.name = $('#en').value;
          USER.email = $('#ee').value;
          USER.role = $('#er').value;
          renderNav();
        }
        renderAdmin();
      } catch (err) { toast(err.message, true); }
    };
  });
  $('#na').onclick = () => {
    $('#af2').innerHTML = `<form id="nf" class="card mt-4"><h2>Create support agent</h2><label>Name</label><input id="nn" required><label>Email</label><input id="ne" type="email" required>
    <label>Password</label><input id="np" type="password" required><button class="btn mt-4">Create agent</button></form>`;
    $('#nf').onsubmit = async e => { e.preventDefault();
      try { await api(CFG.EP.users, { method: 'POST', body: { name: $('#nn').value, email: $('#ne').value, password: $('#np').value, role: 'agent' } }); toast('Agent created'); renderAdmin(); } catch (err) { toast(err.message, true); } };
  };
}
