// Endpoint paths follow the README; adjust here only if your routers differ.
const CFG = {
  API: '', // same origin: FastAPI serves this frontend
  EP: {
    login: '/auth/login', register: '/auth/register', me: '/auth/me',
    tickets: '/tickets', ticket: id => `/tickets/${id}`, escalate: id => `/tickets/${id}/escalate`,
    messages: id => `/tickets/${id}/messages`,
    stats: '/admin/stats', users: '/admin/users', user: id => `/admin/users/${id}`,
    chat: '/ai/chat', suggest: '/ai/suggest-response', classify: '/ai/classify-ticket'
  },
  STATUSES: ['Open', 'In Progress', 'Waiting for Customer', 'Resolved', 'Closed'],
  PRIORITIES: ['Low', 'Medium', 'High', 'Critical'],
  CATEGORIES: ['Technical Issue', 'Account Issue', 'Billing', 'Product Issue', 'General Inquiry']
};
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const enumVal = v => (v && typeof v === 'object') ? (v.value ?? v.name) : v;
const badge = v => `<span class="badge b-${esc(enumVal(v)).replace(/ /g,'')}">${esc(enumVal(v))}</span>`;
const fmt = d => d ? new Date(d).toLocaleString() : '—';
function toast(msg, err) {
  const d = document.createElement('div'); d.textContent = msg; if (err) d.className = 'err';
  $('#toast').appendChild(d); setTimeout(() => d.remove(), 4000);
}
async function api(path, { method = 'GET', body, form, noAuth } = {}) {
  const h = {}; const t = localStorage.getItem('token');
  if (t && !noAuth) h.Authorization = 'Bearer ' + t;
  let payload;
  if (form) { h['Content-Type'] = 'application/x-www-form-urlencoded'; payload = new URLSearchParams(form); }
  else if (body) { h['Content-Type'] = 'application/json'; payload = JSON.stringify(body); }
  const r = await fetch(CFG.API + path, { method, headers: h, body: payload });
  if (r.status === 401 && !noAuth) { logout(); throw new Error('Session expired'); }
  const data = await r.json().catch(() => null);
  if (!r.ok) {
    const d = data && data.detail;
    const e = new Error(Array.isArray(d) ? d.map(x => x.msg).join(', ') : (d || 'Request failed'));
    e.status = r.status; throw e;
  }
  return data;
}
const list = d => Array.isArray(d) ? d : (d?.items || d?.tickets || d?.users || d?.data || []);
