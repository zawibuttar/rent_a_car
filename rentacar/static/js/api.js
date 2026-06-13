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
    const role = (user.role === 'admin' || user.is_superuser) ? 'admin' : user.role;
    localStorage.setItem('token', token);
    localStorage.setItem('role', role);
    localStorage.setItem('user', JSON.stringify(user));
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
function isAdminUser(user) {
  if (!user) return false;
  return user.role === 'admin' || !!user.is_superuser;
}

function navRole(user) {
  if (isAdminUser(user)) return 'admin';
  return (user && user.role) || API.role() || '';
}

function dashboardProfileUrl(role) {
  if (role === 'owner') return '/dashboard/owner/#profile';
  if (role === 'admin') return '/dashboard/admin/#overview';
  return '/dashboard/customer/#profile';
}

function updateNavProfileLink(user) {
  const profileLink = document.getElementById('navProfileLink');
  if (!profileLink) return;

  const labelEl = profileLink.querySelector('span');
  const iconUse = profileLink.querySelector('use');
  const role = navRole(user);
  const isAdmin = role === 'admin';

  profileLink.href = dashboardProfileUrl(role);
  profileLink.hidden = false;

  if (labelEl) {
    labelEl.textContent = isAdmin ? 'Admin Panel' : 'View Profile';
  }
  if (iconUse) {
    iconUse.setAttribute('href', isAdmin ? '#icon-chart' : '#icon-user');
  }
}

function closeNavProfileMenu() {
  const menu = document.getElementById('navProfileMenu');
  const btn = document.getElementById('navAvBtn');
  if (!menu) return;
  menu.hidden = true;
  menu.classList.remove('is-open');
  if (btn) btn.setAttribute('aria-expanded', 'false');
}

function openNavProfileMenu() {
  const menu = document.getElementById('navProfileMenu');
  const btn = document.getElementById('navAvBtn');
  if (!menu || !btn) return;
  menu.hidden = false;
  menu.classList.add('is-open');
  btn.setAttribute('aria-expanded', 'true');
}

function toggleNavProfileMenu() {
  const menu = document.getElementById('navProfileMenu');
  if (!menu) return;
  if (menu.classList.contains('is-open')) {
    closeNavProfileMenu();
  } else {
    openNavProfileMenu();
  }
}

function initNavProfileMenu() {
  const btn = document.getElementById('navAvBtn');
  const menu = document.getElementById('navProfileMenu');
  if (!btn || !menu || btn.dataset.navProfileInit) return;
  btn.dataset.navProfileInit = '1';

  btn.addEventListener('click', function (event) {
    event.stopPropagation();
    toggleNavProfileMenu();
  });

  document.addEventListener('click', function (event) {
    if (menu.classList.contains('is-open')
      && !menu.contains(event.target)
      && !btn.contains(event.target)) {
      closeNavProfileMenu();
    }
  });

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') closeNavProfileMenu();
  });

  const profileLink = document.getElementById('navProfileLink');
  if (profileLink) {
    profileLink.addEventListener('click', function (event) {
      const href = profileLink.getAttribute('href') || '';
      const hashIdx = href.indexOf('#');
      const path = hashIdx >= 0 ? href.slice(0, hashIdx) : href;
      const tab = hashIdx >= 0 ? href.slice(hashIdx + 1) : '';
      const currentPath = window.location.pathname.replace(/\/$/, '');
      const targetPath = path.replace(/\/$/, '');
      if (tab && document.querySelector('.dash-layout') && currentPath === targetPath) {
        event.preventDefault();
        if (location.hash !== '#' + tab) {
          location.hash = tab;
        }
        if (typeof UI !== 'undefined' && UI.openDashboardTabFromHash) {
          UI.openDashboardTabFromHash();
        }
        closeNavProfileMenu();
      }
    });
  }

  menu.querySelectorAll('.nav-profile-item').forEach(function (item) {
    if (item.id === 'navProfileLink') return;
    item.addEventListener('click', function () {
      closeNavProfileMenu();
    });
  });
}

function initNav() {
  const user  = API.getUser();
  const guest = document.getElementById('nav-guest');
  const auth  = document.getElementById('nav-auth');
  const avEl  = document.getElementById('nav-av');
  const menuAv = document.getElementById('navMenuAv');
  const menuName = document.getElementById('navMenuName');
  const profileLink = document.getElementById('navProfileLink');
  const dashLink = document.getElementById('nav-dash-link');

  if (API.loggedIn() && user) {
    if (guest) guest.classList.add('is-hidden');
    if (auth)  auth.classList.remove('is-hidden');
    const label = user.username || '';
    const avText = initials(label);
    if (avEl) avEl.textContent = avText;
    if (menuAv) menuAv.textContent = avText;
    if (menuName) menuName.textContent = label;
    const role = navRole(user);
    updateNavProfileLink(user);
    if (dashLink && role) {
      if (role === 'owner') dashLink.href = '/dashboard/owner/';
      else if (role === 'admin') dashLink.href = '/dashboard/admin/';
      else dashLink.href = '/dashboard/customer/';
    }
    initNavProfileMenu();
  } else {
    if (guest) guest.classList.remove('is-hidden');
    if (auth)  auth.classList.add('is-hidden');
    closeNavProfileMenu();
  }
}

async function doLogout() {
  try { await API.post('/api/accounts/logout/', {}); } catch(_) {}
  API.clear();
  window.location.href = '/login/';
}

document.addEventListener('DOMContentLoaded', initNav);