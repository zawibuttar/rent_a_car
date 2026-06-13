/**
 * User-facing announcements: banner + inbox tab.
 */
const Announcements = {
  items: [],
  activeId: null,
  bannerItem: null,
  isActive: false,
  pollTimer: null,
  POLL_MS: 60000,

  formatDate(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit',
    });
  },

  async fetchList() {
    var res = await API.get('/api/announcements/');
    Announcements.items = res.data || [];
    return Announcements.items;
  },

  async fetchBanner() {
    var res = await API.get('/api/announcements/banner/');
    Announcements.bannerItem = res.data || null;
    return Announcements.bannerItem;
  },

  async fetchUnreadCount() {
    var res = await API.get('/api/announcements/unread-count/');
    return (res.data && res.data.count) || 0;
  },

  updateUnreadBadge() {
    Announcements.fetchUnreadCount().then(function (count) {
      document.querySelectorAll('[data-ann-unread-badge]').forEach(function (el) {
        if (count > 0) {
          el.textContent = count > 99 ? '99+' : String(count);
          el.hidden = false;
        } else {
          el.hidden = true;
        }
      });
    }).catch(function () {});
  },

  renderBanner() {
    var el = document.getElementById('announcementBanner');
    if (!el) return;
    var item = Announcements.bannerItem;
    if (!item) {
      el.hidden = true;
      el.innerHTML = '';
      return;
    }
    el.hidden = false;
    el.innerHTML = '<div class="announcement-banner__inner">'
      + '<div class="announcement-banner__icon" aria-hidden="true">' + UI.icon('megaphone', 'icon') + '</div>'
      + '<div class="announcement-banner__body">'
      + '<div class="announcement-banner__title">' + UI.escHtml(item.title) + '</div>'
      + '<div class="announcement-banner__text">' + UI.escHtml(item.body.length > 160 ? item.body.slice(0, 160) + '…' : item.body) + '</div>'
      + '</div>'
      + '<div class="announcement-banner__actions">'
      + '<button type="button" class="btn btn-ghost btn-sm" onclick="Announcements.openFromBanner(' + item.id + ')">View all</button>'
      + '<button type="button" class="btn btn-ghost btn-icon" onclick="Announcements.dismissBanner(' + item.id + ')" aria-label="Dismiss announcement">'
      + UI.icon('x', 'icon icon-sm') + '</button>'
      + '</div></div>';
  },

  setDetailOpen(open) {
    var layout = document.getElementById('announcementsPanel');
    if (layout) layout.classList.toggle('announcements-layout--detail-open', !!open);
  },

  renderList() {
    var list = document.getElementById('announcementsList');
    if (!list) return;
    if (!Announcements.items.length) {
      list.innerHTML = '<div class="announcements-empty">'
        + UI.emptyState('No announcements', 'You are all caught up.')
        + '</div>';
      return;
    }
    list.innerHTML = Announcements.items.map(function (a) {
      var active = Announcements.activeId === a.id ? ' announcements-list-item--active' : '';
      var unread = !a.is_read ? ' announcements-list-item--unread' : '';
      var excerpt = UI.escHtml((a.body || '').slice(0, 80) + ((a.body || '').length > 80 ? '…' : ''));
      return '<button type="button" class="announcements-list-item' + active + unread + '" role="listitem"'
        + ' onclick="Announcements.select(' + a.id + ')">'
        + '<div class="announcements-list-item__top">'
        + '<span class="announcements-list-item__title">' + UI.escHtml(a.title) + '</span>'
        + '<span class="announcements-list-item__time">' + Announcements.formatDate(a.published_at) + '</span>'
        + '</div>'
        + '<div class="announcements-list-item__preview">' + excerpt + '</div>'
        + '</button>';
    }).join('');
  },

  renderDetail(item) {
    var detail = document.getElementById('announcementsDetail');
    if (!detail || !item) return;
    detail.innerHTML = '<article class="announcements-detail__article">'
      + '<header class="announcements-detail__head">'
      + '<h3>' + UI.escHtml(item.title) + '</h3>'
      + '<time class="announcements-detail__time">' + UI.escHtml(Announcements.formatDate(item.published_at)) + '</time>'
      + '</header>'
      + '<div class="announcements-detail__body">' + UI.escHtml(item.body).replace(/\n/g, '<br>') + '</div>'
      + '</article>';
  },

  async select(id) {
    Announcements.activeId = id;
    Announcements.setDetailOpen(true);
    var item = Announcements.items.find(function (a) { return a.id === id; });
    if (!item) return;
    Announcements.renderList();
    Announcements.renderDetail(item);
    if (!item.is_read) {
      try {
        await API.post('/api/announcements/' + id + '/read/');
        item.is_read = true;
        Announcements.renderList();
        Announcements.updateUnreadBadge();
        Announcements.fetchBanner().then(function () { Announcements.renderBanner(); });
      } catch (err) {
        /* ignore */
      }
    }
  },

  async dismissBanner(id) {
    try {
      await API.post('/api/announcements/' + id + '/dismiss-banner/');
      Announcements.bannerItem = null;
      Announcements.renderBanner();
      Announcements.updateUnreadBadge();
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  openFromBanner(id) {
    var btn = document.getElementById('btn-announcements');
    if (typeof showTab === 'function' && btn) {
      showTab('announcements', btn);
    }
    Announcements.activate();
    Announcements.select(id);
  },

  startPolling() {
    Announcements.stopPolling();
    Announcements.pollTimer = setInterval(function () {
      if (!Announcements.isActive) {
        Announcements.fetchBanner().then(function () { Announcements.renderBanner(); });
        Announcements.updateUnreadBadge();
      }
    }, Announcements.POLL_MS);
  },

  stopPolling() {
    if (Announcements.pollTimer) clearInterval(Announcements.pollTimer);
    Announcements.pollTimer = null;
  },

  activate() {
    Announcements.isActive = true;
    var list = document.getElementById('announcementsList');
    if (list) list.innerHTML = '<div class="announcements-empty"><span class="spinner"></span></div>';
    Announcements.fetchList().then(function (items) {
      Announcements.renderList();
      if (!Announcements.activeId && items.length) {
        Announcements.select(items[0].id);
      } else if (Announcements.activeId) {
        var item = items.find(function (a) { return a.id === Announcements.activeId; });
        if (item) Announcements.renderDetail(item);
      }
    }).catch(function (err) {
      if (list) list.innerHTML = '<div class="announcements-empty">' + UI.escHtml(err.message) + '</div>';
    });
  },

  deactivate() {
    Announcements.isActive = false;
    Announcements.setDetailOpen(false);
  },

  mount() {
    Announcements.fetchBanner().then(function () {
      Announcements.renderBanner();
    }).catch(function () {});
    Announcements.updateUnreadBadge();
    Announcements.startPolling();
  },
};

window.Announcements = Announcements;
