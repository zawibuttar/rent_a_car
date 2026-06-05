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

  resolveUrl(url) {
    if (!url) return null;
    try {
      const resolved = url.startsWith('http')
        ? new URL(url)
        : new URL(url, window.location.origin);
      return window.location.origin + resolved.pathname + resolved.search;
    } catch (_) {
      return url.startsWith('/') ? window.location.origin + url : url;
    }
  },

  async req(method, url, body, multipart) {
    const opts = { method, headers: this.headers(multipart) };
    if (body) opts.body = multipart ? body : JSON.stringify(body);
    const requestUrl = method === 'GET' ? this.resolveUrl(url) : url;
    if (method === 'GET' && this.shouldBypassCache(requestUrl)) {
      opts.cache = 'no-store';
    }
    let res;
    try {
      res = await fetch(requestUrl, opts);
    } catch (_) {
      throw new Error('Could not reach the server. Make sure it is running and refresh the page.');
    }
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msgs = [];
      const pushValue = (key, val) => {
        if (Array.isArray(val)) val.forEach(m => msgs.push(key === 'non_field_errors' ? m : key + ': ' + m));
        else if (val && typeof val === 'object') {
          for (const k2 in val) pushValue(k2, val[k2]);
        } else msgs.push(String(val));
      };
      for (const k in json) pushValue(k, json[k]);
      throw new Error(msgs.join('\n') || 'Error ' + res.status);
    }
    return json;
  },

  async fetchAllPages(url) {
    let nextUrl = this.resolveUrl(url);
    const all = [];
    while (nextUrl) {
      const data = await this.get(nextUrl);
      if (Array.isArray(data)) return data;
      const page = data.results || [];
      all.push.apply(all, page);
      if (!data.next) break;
      nextUrl = this.resolveUrl(data.next);
    }
    return all;
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
function openModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  if (typeof UI !== 'undefined' && UI.initModal) UI.initModal(el);
  el.hidden = false;
  el.classList.add('open');
  el.setAttribute('aria-hidden', 'false');
  const focusable = el.querySelector(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusable) focusable.focus();
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.remove('open');
  el.hidden = true;
  el.setAttribute('aria-hidden', 'true');
}

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
    if (guest) guest.classList.add('is-hidden');
    if (auth)  auth.classList.remove('is-hidden');
    if (uname) uname.textContent   = user.username;
    if (avEl)  avEl.textContent    = initials(user.username);
  } else {
    if (guest) guest.classList.remove('is-hidden');
    if (auth)  auth.classList.add('is-hidden');
  }
}

async function doLogout() {
  try { await API.post('/api/accounts/logout/', {}); } catch(_) {}
  API.clear();
  window.location.href = '/login/';
}

document.addEventListener('DOMContentLoaded', initNav);