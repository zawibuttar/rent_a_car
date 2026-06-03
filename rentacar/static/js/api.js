const API = {

  token()  { return localStorage.getItem('token');  },
  role()   { return localStorage.getItem('role');   },
  getUser(){ return JSON.parse(localStorage.getItem('user') || 'null'); },

  headers(multipart) {
    const h = {};
    if (this.token()) h['Authorization'] = 'Token ' + this.token();
    if (!multipart)   h['Content-Type']  = 'application/json';
    return h;
  },

  shouldBypassCache(url) {
    return /\/api\/cars\//.test(url)
      || /\/admin\//.test(url)
      || /\/my-cars\//.test(url)
      || /\/my-bookings\//.test(url)
      || /\/bookings\/owner\//.test(url)
      || /\/profile\//.test(url);
  },

  async req(method, url, body, multipart) {
    const opts = { method, headers: this.headers(multipart) };
    if (body) opts.body = multipart ? body : JSON.stringify(body);
    if (method === 'GET' && this.shouldBypassCache(url)) {
      opts.cache = 'no-store';
    }
    const res  = await fetch(url, opts);
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msgs = [];
      for (const k in json) {
        const v = json[k];
        if (Array.isArray(v)) v.forEach(m => msgs.push(k === 'non_field_errors' ? m : k + ': ' + m));
        else msgs.push(String(v));
      }
      throw new Error(msgs.join('\n') || 'Error ' + res.status);
    }
    return json;
  },

  get(url)            { return this.req('GET',    url); },
  post(url, data)     { return this.req('POST',   url, data); },
  patch(url, data)    { return this.req('PATCH',  url, data); },
  put(url, data)      { return this.req('PUT',    url, data); },
  del(url)            { return this.req('DELETE', url); },
  upload(url, fd)     { return this.req('POST',   url, fd, true); },
  uploadPatch(url,fd) { return this.req('PATCH',  url, fd, true); },

  save(token, user) {
    localStorage.setItem('token', token);
    localStorage.setItem('role',  user.role);
    localStorage.setItem('user',  JSON.stringify(user));
  },
  clear() {
    ['token','role','user'].forEach(k => localStorage.removeItem(k));
  },
  loggedIn() { return !!this.token(); },
};

/* ── Toast ──────────────────────── */
function toast(msg, type) {
  type = type || 'info';
  let wrap = document.getElementById('toast-wrap');
  if (!wrap) {
    wrap = document.createElement('div');
    wrap.id = 'toast-wrap';
    document.body.appendChild(wrap);
  }
  const t = document.createElement('div');
  t.className = 'toast toast-' + type;
  t.textContent = msg;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

/* ── Status badge ───────────────── */
function statusBadge(s) {
  const map = { pending:'badge-amber', approved:'badge-green', rejected:'badge-red', cancelled:'badge-gray', completed:'badge-blue' };
  return '<span class="badge ' + (map[s] || 'badge-gray') + '">' + s + '</span>';
}

/* ── Initials ───────────────────── */
function initials(name) {
  return (name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);
}

/* ── Modal ──────────────────────── */
function openModal(id)  { document.getElementById(id).classList.add('open');    }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

/* ── Tabs ───────────────────────── */
function switchTab(tabId) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.s-item').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById('tab-' + tabId);
  if (panel) panel.classList.add('active');
}

/* ── Navbar ─────────────────────── */
function initNav() {
  const user  = API.getUser();
  const guest = document.getElementById('nav-guest');
  const auth  = document.getElementById('nav-auth');
  const uname = document.getElementById('nav-uname');
  const avEl  = document.getElementById('nav-av');
  if (API.loggedIn() && user) {
    if (guest) guest.style.display = 'none';
    if (auth)  auth.style.display  = 'flex';
    if (uname) uname.textContent   = user.username;
    if (avEl)  avEl.textContent    = initials(user.username);
  } else {
    if (guest) guest.style.display = 'flex';
    if (auth)  auth.style.display  = 'none';
  }
}

async function doLogout() {
  try { await API.post('/api/accounts/logout/', {}); } catch(_) {}
  API.clear();
  window.location.href = '/login/';
}

document.addEventListener('DOMContentLoaded', initNav);