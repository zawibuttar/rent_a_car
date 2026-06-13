/**
 * Per-booking in-app messaging — professional chat UX (poll-based).
 */
const Messaging = {
  threads: [],
  activeBookingId: null,
  activeContext: null,
  searchQuery: '',
  inboxFilter: 'all',
  pollThreadsTimer: null,
  pollMessagesTimer: null,
  pollUnreadTimer: null,
  mounted: false,
  isActive: false,
  mobileOpenThread: false,
  lastRenderedMessageId: null,
  lastMessageCount: 0,
  pendingMessages: [],
  threadContextShown: {},

  THREAD_POLL_MS: 15000,
  MESSAGE_POLL_MS: 3000,
  UNREAD_POLL_MS: 30000,
  MOBILE_BREAKPOINT: 768,

  isMobile() {
    return window.innerWidth < Messaging.MOBILE_BREAKPOINT;
  },

  roleAvatarClass(role) {
    if (role === 'owner') return 'messages-avatar--owner';
    if (role === 'admin') return 'messages-avatar--admin';
    return 'messages-avatar--customer';
  },

  formatTime(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    var now = new Date();
    var diffMin = Math.floor((now - d) / 60000);
    if (diffMin < 1) return 'now';
    if (diffMin < 60) return diffMin + 'm';
    var diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return diffHr + 'h';
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  },

  formatFullTime(dateStr) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
    });
  },

  formatDayLabel(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    var now = new Date();
    var startToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    var startMsg = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    var diffDays = Math.round((startToday - startMsg) / 86400000);
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  },

  statusBadge(status) {
    var map = {
      pending: 'badge-amber',
      approved: 'badge-green',
      rejected: 'badge-red',
      cancelled: 'badge-gray',
      completed: 'badge-blue',
    };
    var cls = map[status] || 'badge-gray';
    var label = status ? status.charAt(0).toUpperCase() + status.slice(1) : '';
    return '<span class="badge ' + cls + '">' + UI.escHtml(label) + '</span>';
  },

  systemIcon(body) {
    var text = (body || '').toLowerCase();
    if (text.indexOf('approved') !== -1) return 'check';
    if (text.indexOf('rejected') !== -1 || text.indexOf('cancelled') !== -1) return 'x';
    if (text.indexOf('submitted') !== -1 || text.indexOf('booking') !== -1) return 'calendar';
    return 'message';
  },

  getThread(bookingId) {
    var id = parseInt(bookingId, 10);
    return Messaging.threads.find(function (t) { return t.booking_id === id; }) || null;
  },

  async fetchThreads() {
    var res = await API.get('/api/messaging/threads/');
    Messaging.threads = res.data || [];
    return Messaging.threads;
  },

  async fetchMessages(bookingId) {
    var res = await API.get('/api/messaging/threads/' + bookingId + '/messages/');
    return res.data || { messages: [], is_open: false, booking_status: '', context: null };
  },

  async fetchUnreadCount() {
    var res = await API.get('/api/messaging/unread-count/');
    return (res.data && res.data.count) || 0;
  },

  filteredThreads() {
    var q = Messaging.searchQuery.trim().toLowerCase();
    return Messaging.threads.filter(function (t) {
      if (Messaging.inboxFilter === 'unread' && !(t.unread_count > 0)) return false;
      if (Messaging.inboxFilter === 'active' && !t.is_open) return false;
      if (!q) return true;
      return (t.other_party_name || '').toLowerCase().indexOf(q) !== -1
        || (t.car_label || '').toLowerCase().indexOf(q) !== -1
        || (t.car_location || '').toLowerCase().indexOf(q) !== -1
        || (t.last_message || '').toLowerCase().indexOf(q) !== -1;
    });
  },

  setInboxFilter(filter) {
    Messaging.inboxFilter = filter;
    document.querySelectorAll('.messages-filter').forEach(function (btn) {
      var active = btn.getAttribute('data-filter') === filter;
      btn.classList.toggle('messages-filter--active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    Messaging.renderThreadList();
  },

  showInbox() {
    Messaging.mobileOpenThread = false;
    var panel = document.getElementById('messagesPanel');
    if (panel) panel.classList.remove('messages-layout--thread-open');
  },

  showThreadPane() {
    Messaging.mobileOpenThread = true;
    var panel = document.getElementById('messagesPanel');
    if (panel) panel.classList.add('messages-layout--thread-open');
  },

  renderThreadList() {
    var list = document.getElementById('msgThreadList');
    var skeleton = document.getElementById('msgInboxSkeleton');
    if (!list) return;
    if (skeleton) skeleton.hidden = true;

    var threads = Messaging.filteredThreads();
    if (!threads.length) {
      var emptyTitle = Messaging.inboxFilter === 'unread'
        ? 'No unread messages'
        : (Messaging.inboxFilter === 'active' ? 'No active conversations' : 'No conversations yet');
      var emptyMsg = Messaging.searchQuery
        ? 'Try a different search term.'
        : 'Messages appear when you have booking requests.';
      list.innerHTML = '<div class="messages-empty messages-empty--inbox">'
        + UI.emptyState(emptyTitle, emptyMsg)
        + '</div>';
      return;
    }

    list.innerHTML = threads.map(function (t) {
      var active = Messaging.activeBookingId === t.booking_id ? ' messages-thread-item--active' : '';
      var unreadCls = t.unread_count > 0 ? ' messages-thread-item--unread' : '';
      var unread = t.unread_count > 0
        ? '<span class="messages-unread">' + (t.unread_count > 99 ? '99+' : t.unread_count) + '</span>'
        : '';
      var preview = UI.escHtml(t.last_message || 'No messages yet');
      var meta = UI.escHtml(t.car_label || '') + ' · ' + UI.escHtml(t.rental_period || '');
      var roleCls = Messaging.roleAvatarClass(t.other_party_role);
      return '<button type="button" class="messages-thread-item' + active + unreadCls + '" role="listitem"'
        + ' data-booking-id="' + t.booking_id + '" aria-current="'
        + (Messaging.activeBookingId === t.booking_id ? 'true' : 'false') + '"'
        + ' onclick="Messaging.selectThread(' + t.booking_id + ')">'
        + '<div class="messages-thread-item__avatar ' + roleCls + '">'
        + UI.escHtml((t.other_party_name || '?').slice(0, 2).toUpperCase())
        + '</div>'
        + '<div class="messages-thread-item__body">'
        + '<div class="messages-thread-item__top">'
        + '<span class="messages-thread-item__name">' + UI.escHtml(t.other_party_name || 'User') + '</span>'
        + '<span class="messages-thread-item__time">' + Messaging.formatTime(t.last_message_at) + '</span>'
        + '</div>'
        + '<div class="messages-thread-item__meta">' + meta + '</div>'
        + '<div class="messages-thread-item__preview">' + preview + '</div>'
        + '</div>'
        + unread
        + '</button>';
    }).join('');
  },

  renderThreadHeader(thread, meta) {
    var head = document.getElementById('msgThreadHead');
    var placeholder = document.getElementById('msgThreadPlaceholder');
    if (!head || !thread) return;
    if (placeholder) placeholder.hidden = true;

    var ctx = meta.context || Messaging.activeContext || {};
    var roleLabel = (ctx.other_party_role || thread.other_party_role || 'user');
    roleLabel = roleLabel.charAt(0).toUpperCase() + roleLabel.slice(1);
    var subtitle = thread.other_party_subtitle
      ? '<div class="messages-thread__subtitle">' + UI.escHtml(thread.other_party_subtitle) + '</div>'
      : '';
    var backBtn = Messaging.isMobile()
      ? '<button type="button" class="messages-thread__back btn btn-ghost btn-icon" onclick="Messaging.showInbox()" aria-label="Back to inbox">'
        + UI.icon('arrow-left', 'icon') + '</button>'
      : '';
    var avatarCls = Messaging.roleAvatarClass(ctx.other_party_role || thread.other_party_role);

    head.innerHTML = '<div class="messages-thread__header">'
      + backBtn
      + '<div class="messages-thread__avatar ' + avatarCls + '">'
      + UI.escHtml((ctx.other_party_name || thread.other_party_name || '?').slice(0, 2).toUpperCase())
      + '</div>'
      + '<div class="messages-thread__info">'
      + '<h3 class="messages-thread__title">' + UI.escHtml(thread.car_label) + '</h3>'
      + '<div class="messages-thread__meta">'
      + UI.escHtml(ctx.other_party_name || thread.other_party_name) + ' · ' + roleLabel
      + ' · ' + UI.escHtml(thread.rental_period || '')
      + '</div>'
      + subtitle
      + '</div>'
      + '<div class="messages-thread__actions">'
      + Messaging.statusBadge(meta.booking_status || thread.booking_status)
      + '<button type="button" class="btn btn-ghost btn-sm" onclick="Messaging.viewBooking(' + thread.booking_id + ')">View booking</button>'
      + '</div>'
      + '</div>';
  },

  renderThreadContext(context) {
    var el = document.getElementById('msgThreadContext');
    if (!el || !context) {
      if (el) el.hidden = true;
      return;
    }
    if (Messaging.threadContextShown[context.booking_id]) {
      el.hidden = true;
      return;
    }

    var img = context.car_image_url
      ? '<img class="messages-context__img" src="' + UI.escHtml(context.car_image_url) + '" alt="" loading="lazy" />'
      : '<div class="messages-context__img messages-context__img--placeholder">' + UI.icon('car', 'icon') + '</div>';

    el.innerHTML = '<div class="messages-context">'
      + img
      + '<div class="messages-context__body">'
      + '<div class="messages-context__title">' + UI.escHtml(context.car_label) + '</div>'
      + '<div class="messages-context__meta">'
      + UI.icon('pin', 'icon icon-inline') + ' ' + UI.escHtml(context.car_location || '')
      + ' · ' + UI.escHtml(context.rental_period || '')
      + '</div>'
      + '<div class="messages-context__cost">$' + parseFloat(context.total_cost || 0).toFixed(2) + ' total</div>'
      + '<div class="messages-quick-replies">'
      + '<button type="button" class="messages-quick-reply" onclick="Messaging.insertQuickReply(\'What time works for pickup?\')">Pickup time?</button>'
      + '<button type="button" class="messages-quick-reply" onclick="Messaging.insertQuickReply(\'I\\\'m on my way.\')">On my way</button>'
      + '<button type="button" class="messages-quick-reply" onclick="Messaging.insertQuickReply(\'I have arrived.\')">I have arrived</button>'
      + '</div>'
      + '</div>'
      + '<button type="button" class="messages-context__dismiss btn btn-ghost btn-icon" onclick="Messaging.dismissContext(' + context.booking_id + ')" aria-label="Dismiss booking details">'
      + UI.icon('x', 'icon icon-sm') + '</button>'
      + '</div>';
    el.hidden = false;
  },

  dismissContext(bookingId) {
    Messaging.threadContextShown[bookingId] = true;
    var el = document.getElementById('msgThreadContext');
    if (el) el.hidden = true;
  },

  insertQuickReply(text) {
    var input = document.getElementById('msgInput');
    if (!input) return;
    input.value = text;
    Messaging.syncComposeState();
    input.focus();
  },

  buildMessageHtml(m, opts) {
    opts = opts || {};
    var showSender = opts.showSender !== false;
    var pending = m._pending ? ' messages-bubble--pending' : '';
    var failed = m._failed ? ' messages-bubble--failed' : '';

    if (m.message_type === 'system') {
      return '<div class="messages-bubble messages-bubble--system" role="article">'
        + '<span class="messages-system__icon">' + UI.icon(Messaging.systemIcon(m.body), 'icon icon-sm') + '</span>'
        + '<span>' + UI.escHtml(m.body) + '</span>'
        + '<time class="messages-bubble__time" datetime="' + UI.escHtml(m.created_at || '') + '">'
        + Messaging.formatTime(m.created_at) + '</time>'
        + '</div>';
    }

    if (m.message_type === 'location') {
      var ownLoc = m.is_own ? ' messages-bubble--own' : ' messages-bubble--other';
      var readMarkLoc = Messaging.readReceiptHtml(m);
      var meta = m.metadata || {};
      var label = UI.escHtml(m.body || meta.label || 'Current location');
      var mapImg = '';
      if (m.map_preview_url || m.maps_url) {
        var previewSrc = m.map_preview_url || '';
        mapImg = '<a class="messages-location__map" href="' + UI.escHtml(m.maps_url || '#') + '" target="_blank" rel="noopener noreferrer">'
          + (previewSrc
            ? '<img src="' + UI.escHtml(previewSrc) + '" alt="" role="presentation" loading="lazy" '
              + 'onerror="this.closest(\'.messages-location__map\').classList.add(\'messages-location__map--fallback\'); this.remove();" />'
            : '')
          + '<span class="messages-location__pin" aria-hidden="true">' + UI.icon('pin', 'icon') + '</span>'
          + '</a>';
      }
      var mapsBtn = m.maps_url
        ? '<a class="messages-location__btn btn btn-sm" href="' + UI.escHtml(m.maps_url) + '" target="_blank" rel="noopener noreferrer">Open in Maps</a>'
        : '';
      return '<div class="messages-bubble messages-bubble--location' + ownLoc + pending + failed + '" role="article" data-message-id="' + UI.escHtml(String(m.id)) + '">'
        + (m.is_own || !showSender ? '' : '<div class="messages-bubble__sender">' + UI.escHtml(m.sender_name) + '</div>')
        + '<div class="messages-location-card">'
        + mapImg
        + '<div class="messages-location-card__body">'
        + '<div class="messages-location-card__label">' + UI.icon('pin', 'icon icon-inline') + ' ' + label + '</div>'
        + mapsBtn
        + '</div></div>'
        + Messaging.messageFootHtml(m, readMarkLoc)
        + (m._failed ? Messaging.failedActionsHtml(m) : '')
        + '</div>';
    }

    var own = m.is_own ? ' messages-bubble--own' : ' messages-bubble--other';
    var readMark = Messaging.readReceiptHtml(m);
    return '<div class="messages-bubble' + own + pending + failed + '" role="article" data-message-id="' + UI.escHtml(String(m.id)) + '">'
      + (m.is_own || !showSender ? '' : '<div class="messages-bubble__sender">' + UI.escHtml(m.sender_name) + '</div>')
      + '<div class="messages-bubble__text">' + UI.escHtml(m.body) + '</div>'
      + Messaging.messageFootHtml(m, readMark)
      + (m._failed ? Messaging.failedActionsHtml(m) : '')
      + '</div>';
  },

  readReceiptHtml(m) {
    if (!m.is_own) return '';
    if (m._pending) return '<span class="messages-read messages-read--pending" title="Sending">◷</span>';
    if (m._failed) return '<span class="messages-read messages-read--failed" title="Failed">!</span>';
    return m.is_read
      ? '<span class="messages-read messages-read--read" title="Read">✓✓</span>'
      : '<span class="messages-read" title="Sent">✓</span>';
  },

  messageFootHtml(m, readMark) {
    return '<div class="messages-bubble__foot">'
      + '<time class="messages-bubble__time" datetime="' + UI.escHtml(m.created_at || '') + '" title="' + UI.escHtml(Messaging.formatFullTime(m.created_at)) + '">'
      + Messaging.formatTime(m.created_at) + '</time>'
      + readMark
      + '</div>';
  },

  failedActionsHtml(m) {
    return '<div class="messages-bubble__retry">'
      + '<button type="button" class="btn btn-ghost btn-sm" onclick="Messaging.retryMessage(\'' + UI.escHtml(String(m.id)) + '\')">Retry</button>'
      + '<button type="button" class="btn btn-ghost btn-sm" onclick="Messaging.removePending(\'' + UI.escHtml(String(m.id)) + '\')">Delete</button>'
      + '</div>';
  },

  groupMessagesForRender(messages) {
    var all = (messages || []).concat(Messaging.pendingMessages);
    all.sort(function (a, b) {
      var ta = new Date(a.created_at || 0).getTime();
      var tb = new Date(b.created_at || 0).getTime();
      return ta - tb;
    });

    var html = '';
    var lastDay = '';
    var lastSender = null;

    all.forEach(function (m) {
      var day = Messaging.formatDayLabel(m.created_at);
      if (day && day !== lastDay) {
        html += '<div class="messages-day-divider"><span>' + UI.escHtml(day) + '</span></div>';
        lastDay = day;
        lastSender = null;
      }

      var sameSender = !m.is_own
        && m.message_type !== 'system'
        && m.message_type !== 'location'
        && m.sender_id
        && m.sender_id === lastSender;
      var bubble = Messaging.buildMessageHtml(m, { showSender: !sameSender });
      if (m.message_type === 'system') {
        html += '<div class="messages-row messages-row--system">' + bubble + '</div>';
      } else {
        html += '<div class="messages-row' + (m.is_own ? ' messages-row--own' : ' messages-row--other') + '">' + bubble + '</div>';
      }

      if (m.message_type !== 'system' && m.sender_id) {
        lastSender = m.sender_id;
      } else {
        lastSender = null;
      }
    });

    return html;
  },

  isNearBottom(el, threshold) {
    if (!el) return true;
    threshold = threshold || 80;
    return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  },

  renderMessages(messages, opts) {
    opts = opts || {};
    var body = document.getElementById('msgThreadBody');
    if (!body) return;

    if (!messages.length && !Messaging.pendingMessages.length) {
      body.innerHTML = '<div class="messages-empty messages-empty--thread">'
        + UI.emptyState('No messages yet', 'Say hello or share your pickup location to get started.')
        + '</div>';
      Messaging.lastRenderedMessageId = null;
      Messaging.lastMessageCount = 0;
      return;
    }

    var wasNearBottom = Messaging.isNearBottom(body);
    var prevHeight = body.scrollHeight;
    var prevTop = body.scrollTop;
    var lastMsg = messages[messages.length - 1];
    var newLastId = lastMsg ? lastMsg.id : null;
    var hasNew = opts.forceScroll
      || (newLastId && newLastId !== Messaging.lastRenderedMessageId && !wasNearBottom);

    body.innerHTML = Messaging.groupMessagesForRender(messages);
    Messaging.lastRenderedMessageId = newLastId;
    Messaging.lastMessageCount = messages.length;

    if (opts.forceScroll || wasNearBottom) {
      body.scrollTop = body.scrollHeight;
      Messaging.hideNewChip();
    } else if (hasNew) {
      body.scrollTop = prevTop + (body.scrollHeight - prevHeight);
      Messaging.showNewChip();
    }
  },

  showNewChip() {
    var chip = document.getElementById('msgNewChip');
    if (chip) chip.hidden = false;
  },

  hideNewChip() {
    var chip = document.getElementById('msgNewChip');
    if (chip) chip.hidden = true;
  },

  scrollToBottom() {
    var body = document.getElementById('msgThreadBody');
    if (body) {
      body.scrollTop = body.scrollHeight;
      Messaging.hideNewChip();
    }
  },

  renderInboxSkeleton() {
    var list = document.getElementById('msgThreadList');
    var skeleton = document.getElementById('msgInboxSkeleton');
    if (list && skeleton) {
      list.innerHTML = '';
      list.appendChild(skeleton);
      skeleton.hidden = false;
    }
  },

  renderThreadSkeleton() {
    var body = document.getElementById('msgThreadBody');
    if (!body) return;
    body.innerHTML = '<div class="messages-skeleton messages-skeleton--thread">'
      + '<div class="messages-skeleton__bubble messages-skeleton__bubble--other"></div>'
      + '<div class="messages-skeleton__bubble messages-skeleton__bubble--own"></div>'
      + '<div class="messages-skeleton__bubble messages-skeleton__bubble--other"></div>'
      + '</div>';
  },

  updateCompose(isOpen) {
    var compose = document.getElementById('msgCompose');
    var closed = document.getElementById('msgClosed');
    var pane = document.getElementById('msgThreadPane');
    var input = document.getElementById('msgInput');
    var locBtn = document.getElementById('msgLocationBtn');
    var sendBtn = document.getElementById('msgSendBtn');
    var open = !!isOpen;

    if (pane) {
      pane.classList.toggle('messages-thread--composable', open);
      pane.classList.toggle('messages-thread--closed', !open);
    }
    if (closed) closed.hidden = open;
    if (!compose) return;

    if (open) {
      compose.hidden = false;
      if (input) input.disabled = false;
      if (locBtn) locBtn.disabled = false;
      if (sendBtn) sendBtn.disabled = !((input && input.value.trim()));
    } else {
      compose.hidden = true;
      if (input) {
        input.value = '';
        input.disabled = true;
      }
      if (locBtn) locBtn.disabled = true;
      if (sendBtn) sendBtn.disabled = true;
    }
    Messaging.autoResizeInput();
  },

  syncComposeState() {
    var input = document.getElementById('msgInput');
    var sendBtn = document.getElementById('msgSendBtn');
    if (sendBtn && input) {
      sendBtn.disabled = !input.value.trim() || input.disabled;
    }
    Messaging.autoResizeInput();
  },

  autoResizeInput() {
    var input = document.getElementById('msgInput');
    if (!input) return;
    input.style.height = 'auto';
    var max = 120;
    input.style.height = Math.min(input.scrollHeight, max) + 'px';
  },

  async loadThread(bookingId, silent) {
    var thread = Messaging.getThread(bookingId);
    if (!thread && !silent) {
      await Messaging.fetchThreads();
      thread = Messaging.getThread(bookingId);
    }
    if (!thread) return;

    Messaging.activeBookingId = bookingId;
    Messaging.renderThreadList();
    if (Messaging.isMobile()) Messaging.showThreadPane();

    if (!silent) {
      Messaging.renderThreadSkeleton();
    }

    try {
      var data = await Messaging.fetchMessages(bookingId);
      Messaging.activeContext = data.context || null;
      Messaging.renderThreadHeader(thread, data);
      Messaging.renderThreadContext(data.context);
      Messaging.renderMessages(data.messages || [], { forceScroll: !silent });
      Messaging.updateCompose(!!data.is_open);
      if (!data.is_open) {
        var ctx = document.getElementById('msgThreadContext');
        if (ctx) ctx.hidden = true;
      }
      if (!silent) Messaging.updateUnreadBadge();
      await Messaging.fetchThreads();
      Messaging.renderThreadList();
    } catch (err) {
      var bodyEl = document.getElementById('msgThreadBody');
      if (bodyEl) {
        bodyEl.innerHTML = '<div class="messages-empty">' + UI.escHtml(err.message) + '</div>';
      }
      Messaging.updateCompose(false);
    }
  },

  selectThread(bookingId) {
    Messaging.pendingMessages = [];
    Messaging.loadThread(bookingId, false);
  },

  addPendingMessage(payload) {
    var tempId = 'pending-' + Date.now() + '-' + Math.random().toString(36).slice(2, 7);
    var msg = Object.assign({
      id: tempId,
      created_at: new Date().toISOString(),
      is_own: true,
      is_read: false,
      _pending: true,
      _payload: payload,
    }, payload);
    Messaging.pendingMessages.push(msg);
    return msg;
  },

  removePending(tempId) {
    Messaging.pendingMessages = Messaging.pendingMessages.filter(function (m) {
      return String(m.id) !== String(tempId);
    });
    Messaging.loadThread(Messaging.activeBookingId, true);
  },

  async retryMessage(tempId) {
    var pending = Messaging.pendingMessages.find(function (m) { return String(m.id) === String(tempId); });
    if (!pending || !pending._payload) return;
    pending._failed = false;
    pending._pending = true;
    Messaging.renderMessages((await Messaging.fetchMessages(Messaging.activeBookingId)).messages || [], { forceScroll: true });
    try {
      await API.post('/api/messaging/threads/' + Messaging.activeBookingId + '/messages/', pending._payload);
      Messaging.pendingMessages = Messaging.pendingMessages.filter(function (m) { return String(m.id) !== String(tempId); });
      await Messaging.loadThread(Messaging.activeBookingId, true);
      await Messaging.fetchThreads();
      Messaging.renderThreadList();
      Messaging.updateUnreadBadge();
    } catch (err) {
      pending._pending = false;
      pending._failed = true;
      toast(err.message, 'error');
      Messaging.loadThread(Messaging.activeBookingId, true);
    }
  },

  async sendMessage() {
    var input = document.getElementById('msgInput');
    var btn = document.getElementById('msgSendBtn');
    if (!input || !Messaging.activeBookingId) return;
    var body = input.value.trim();
    if (!body) return;

    var payload = { body: body };
    var pending = Messaging.addPendingMessage({
      message_type: 'text',
      body: body,
      sender_name: 'You',
    });
    input.value = '';
    Messaging.syncComposeState();

    var current = await Messaging.fetchMessages(Messaging.activeBookingId).catch(function () { return { messages: [] }; });
    Messaging.renderMessages(current.messages || [], { forceScroll: true });

    if (btn) btn.disabled = true;
    try {
      await API.post('/api/messaging/threads/' + Messaging.activeBookingId + '/messages/', payload);
      Messaging.pendingMessages = Messaging.pendingMessages.filter(function (m) { return m.id !== pending.id; });
      await Messaging.loadThread(Messaging.activeBookingId, true);
      await Messaging.fetchThreads();
      Messaging.renderThreadList();
      Messaging.updateUnreadBadge();
    } catch (err) {
      pending._pending = false;
      pending._failed = true;
      toast(err.message, 'error');
      Messaging.renderMessages(current.messages || [], { forceScroll: true });
    } finally {
      if (btn) btn.disabled = false;
      if (input) input.focus();
    }
  },

  sendCurrentLocation() {
    if (!Messaging.activeBookingId) return;
    if (!navigator.geolocation) {
      toast('Geolocation is not supported in this browser.', 'error');
      return;
    }
    var btn = document.getElementById('msgLocationBtn');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('messages-compose__tool--loading');
    }

    navigator.geolocation.getCurrentPosition(function (position) {
      var lat = Number(position.coords.latitude.toFixed(6));
      var lng = Number(position.coords.longitude.toFixed(6));
      var accuracy = position.coords.accuracy;
      var label = 'Current location';

      function postLocation(finalLabel) {
        var payload = {
          message_type: 'location',
          latitude: lat,
          longitude: lng,
          label: finalLabel,
          accuracy: accuracy,
        };
        API.post('/api/messaging/threads/' + Messaging.activeBookingId + '/messages/', payload)
          .then(function () {
            return Messaging.loadThread(Messaging.activeBookingId, true);
          })
          .then(function () {
            return Messaging.fetchThreads();
          })
          .then(function () {
            Messaging.renderThreadList();
            Messaging.updateUnreadBadge();
          })
          .catch(function (err) {
            toast(err.message, 'error');
          })
          .finally(function () {
            if (btn) {
              btn.disabled = false;
              btn.classList.remove('messages-compose__tool--loading');
            }
          });
      }

      if (typeof LocationState !== 'undefined' && LocationState.reverseGeocode) {
        LocationState.reverseGeocode(lat, lng).then(function (picked) {
          postLocation((picked && picked.label) ? picked.label : label);
        }).catch(function () {
          postLocation(label);
        });
      } else {
        postLocation(label);
      }
    }, function () {
      toast('Location permission was denied.', 'error');
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('messages-compose__tool--loading');
      }
    }, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 60000,
    });
  },

  viewBooking(bookingId) {
    var btn = document.getElementById('btn-bookings') || document.getElementById('btn-requests');
    var tab = document.getElementById('btn-requests') && btn && btn.id === 'btn-requests' ? 'requests' : 'bookings';
    if (typeof showTab === 'function' && btn) {
      showTab(tab, btn);
    }
    window.setTimeout(function () {
      var row = document.querySelector('[data-booking-row="' + bookingId + '"]');
      if (row) {
        row.classList.add('table-row--highlight');
        row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        window.setTimeout(function () { row.classList.remove('table-row--highlight'); }, 2500);
      }
    }, 400);
  },

  async updateUnreadBadge() {
    var badges = document.querySelectorAll('[data-msg-unread-badge]');
    if (!badges.length) return;
    try {
      var count = await Messaging.fetchUnreadCount();
      badges.forEach(function (el) {
        if (count > 0) {
          el.textContent = count > 99 ? '99+' : String(count);
          el.hidden = false;
        } else {
          el.hidden = true;
        }
      });
    } catch (err) {
      /* ignore */
    }
  },

  startPolling() {
    Messaging.stopPolling();
    Messaging.pollThreadsTimer = setInterval(function () {
      if (!Messaging.isActive) return;
      Messaging.fetchThreads().then(function () {
        Messaging.renderThreadList();
      }).catch(function () {});
    }, Messaging.THREAD_POLL_MS);

    Messaging.pollMessagesTimer = setInterval(function () {
      if (!Messaging.isActive || !Messaging.activeBookingId) return;
      Messaging.loadThread(Messaging.activeBookingId, true);
    }, Messaging.MESSAGE_POLL_MS);

    Messaging.pollUnreadTimer = setInterval(function () {
      Messaging.updateUnreadBadge();
    }, Messaging.UNREAD_POLL_MS);
  },

  stopPolling() {
    if (Messaging.pollThreadsTimer) clearInterval(Messaging.pollThreadsTimer);
    if (Messaging.pollMessagesTimer) clearInterval(Messaging.pollMessagesTimer);
    if (Messaging.pollUnreadTimer) clearInterval(Messaging.pollUnreadTimer);
    Messaging.pollThreadsTimer = null;
    Messaging.pollMessagesTimer = null;
    Messaging.pollUnreadTimer = null;
  },

  activate() {
    Messaging.isActive = true;
    Messaging.renderInboxSkeleton();
    Messaging.fetchThreads().then(function (threads) {
      Messaging.renderThreadList();
      var params = new URLSearchParams(window.location.search);
      var threadParam = params.get('thread');
      if (threadParam) {
        Messaging.loadThread(parseInt(threadParam, 10), false);
      } else if (!Messaging.activeBookingId && threads.length && !Messaging.isMobile()) {
        Messaging.loadThread(threads[0].booking_id, false);
      } else if (!Messaging.activeBookingId && Messaging.isMobile()) {
        Messaging.showInbox();
      }
    }).catch(function (err) {
      var list = document.getElementById('msgThreadList');
      if (list) {
        list.innerHTML = '<div class="messages-empty">' + UI.escHtml(err.message) + '</div>';
      }
    });
    Messaging.startPolling();
  },

  deactivate() {
    Messaging.isActive = false;
    Messaging.stopPolling();
  },

  mount() {
    if (Messaging.mounted) return;
    Messaging.mounted = true;

    var search = document.getElementById('msgSearch');
    if (search) {
      search.addEventListener('input', function () {
        Messaging.searchQuery = search.value;
        Messaging.renderThreadList();
      });
    }

    document.querySelectorAll('.messages-filter').forEach(function (btn) {
      btn.addEventListener('click', function () {
        Messaging.setInboxFilter(btn.getAttribute('data-filter') || 'all');
      });
    });

    var sendBtn = document.getElementById('msgSendBtn');
    if (sendBtn) sendBtn.addEventListener('click', Messaging.sendMessage);

    var locBtn = document.getElementById('msgLocationBtn');
    if (locBtn) locBtn.addEventListener('click', Messaging.sendCurrentLocation);

    var input = document.getElementById('msgInput');
    if (input) {
      input.addEventListener('input', Messaging.syncComposeState);
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          Messaging.sendMessage();
        }
      });
    }

    var newChip = document.getElementById('msgNewChip');
    if (newChip) newChip.addEventListener('click', Messaging.scrollToBottom);

    window.addEventListener('resize', function () {
      if (!Messaging.isMobile() && Messaging.activeBookingId) {
        Messaging.showInbox();
        var panel = document.getElementById('messagesPanel');
        if (panel) panel.classList.remove('messages-layout--thread-open');
      }
      if (Messaging.activeBookingId) {
        var thread = Messaging.getThread(Messaging.activeBookingId);
        if (thread) Messaging.renderThreadHeader(thread, { booking_status: thread.booking_status, context: Messaging.activeContext });
      }
    });

    Messaging.updateUnreadBadge();
    Messaging.pollUnreadTimer = setInterval(function () {
      Messaging.updateUnreadBadge();
    }, Messaging.UNREAD_POLL_MS);
  },

  openThread(bookingId) {
    var btn = document.getElementById('btn-messages');
    if (typeof showTab === 'function') {
      showTab('messages', btn);
    }
    Messaging.activeBookingId = parseInt(bookingId, 10);
    Messaging.activate();
    Messaging.loadThread(bookingId, false);
  },

  threadPreviewHtml(bookingId) {
    var t = Messaging.getThread(bookingId);
    if (!t) return '—';
    var preview = UI.escHtml(t.last_message || 'No messages');
    var unread = t.unread_count > 0
      ? ' <span class="badge badge-red">' + t.unread_count + '</span>'
      : '';
    return '<button type="button" class="btn btn-ghost btn-sm" onclick="Messaging.openThread(' + bookingId + ')">'
      + 'View' + unread + '</button>'
      + '<div class="text-caption messages-preview-text">' + preview + '</div>';
  },
};

window.Messaging = Messaging;
