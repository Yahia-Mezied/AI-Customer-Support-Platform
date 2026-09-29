let USER = null;
function logout() { localStorage.removeItem('token'); USER = null; $('#chat-root').innerHTML = ''; route(); }
async function login(email, password) {
  let res;
  try { res = await api(CFG.EP.login, { method: 'POST', body: { email, password }, noAuth: true }); }
  catch (e) { if (e.status !== 422) throw e; res = await api(CFG.EP.login, { method: 'POST', form: { username: email, password }, noAuth: true }); }
  localStorage.setItem('token', res.access_token || res.token);
}
function authView(mode = 'login') {
  const reg = mode === 'register';
  $('#nav').innerHTML = '';
  $('#app').innerHTML = `<div class="hero"><div class="wrap"><p>Welcome</p><h1>When support meets<br>intelligence</h1></div></div>
  <div class="card" style="max-width:440px;margin:0 auto"><h2>${reg ? 'Create account' : 'Sign in'}</h2>
  <form id="af">${reg ? '<label>Name</label><input id="an" required>' : ''}
  <label>Email</label><input id="ae" type="email" required><label>Password</label><input id="ap" type="password" required>
  <button class="btn w-full mt-4" style="width:100%">${reg ? 'Register' : 'Login'}</button></form>
  <p class="mt-4 text-sm"><a href="#" id="sw" style="color:var(--purple);font-weight:600">${reg ? 'Have an account? Sign in' : 'New customer? Register'}</a></p></div>`;
  $('#sw').onclick = e => { e.preventDefault(); authView(reg ? 'login' : 'register'); };
  $('#af').onsubmit = async e => {
    e.preventDefault();
    try {
      const em = $('#ae').value, pw = $('#ap').value;
      if (reg) await api(CFG.EP.register, { method: 'POST', body: { name: $('#an').value, email: em, password: pw }, noAuth: true });
      await login(em, pw); route();
    } catch (err) { toast(err.message, true); }
  };
}
function renderNav() {
  const links = { customer: 'My Tickets', agent: 'Workspace', admin: 'Dashboard' }[USER.role];
  $('#nav').innerHTML = `<a href="#" onclick="route();return false">${links}</a><span class="badge">${esc(USER.name)} · ${esc(USER.role)}</span><button class="btn btn-o btn-sm" onclick="logout()">Logout</button>`;
}
async function route() {
  if (!localStorage.getItem('token')) return authView();
  try { USER = await api(CFG.EP.me); USER.role = String(enumVal(USER.role)).toLowerCase(); }
  catch (e) { return authView(); }
  renderNav();
  if (USER.role === 'admin') renderAdmin();
  else if (USER.role === 'agent') renderAgent();
  else renderCustomer();
  if (USER.role === 'customer') initChat();
}
route();
