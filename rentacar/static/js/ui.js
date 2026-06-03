/* Shared UI helpers — icons, theme, stat cards, listing badges, pagination */

const UI_PAGE = {
  catalog: 12,
  table: 10,
  grid: 9,
};

const UI = {
  escHtml(s) {
    if (s == null || s === undefined) return '';
    const d = document.createElement('div');
    d.textContent = String(s);
    return d.innerHTML;
  },

  icon(name, className) {
    className = className || 'icon';
    return '<svg class="' + className + '" aria-hidden="true"><use href="#icon-' + name + '"/></svg>';
  },

  initTheme() {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    this.updateThemeToggle(theme);
  },

  toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    this.updateThemeToggle(next);
  },

  updateThemeToggle(theme) {
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      const isDark = theme === 'dark';
      btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
      btn.innerHTML = isDark ? UI.icon('sun', 'icon icon-sm') : UI.icon('moon', 'icon icon-sm');
    });
  },

  statCard(variant, value, label) {
    const icons = {
      cars: 'car',
      bookings: 'calendar',
      active: 'check',
      pending: 'calendar',
      earnings: 'dollar',
      revenue: 'dollar',
      owners: 'users',
      verified: 'shield',
    };
    const iconName = icons[variant] || 'chart';
    return '<div class="stat-card">'
      + '<div class="stat-icon stat-icon--' + variant + '">' + UI.icon(iconName, 'icon') + '</div>'
      + '<div class="stat-val">' + UI.escHtml(value) + '</div>'
      + '<div class="stat-lbl">' + UI.escHtml(label) + '</div>'
      + '</div>';
  },

  statCardButton(variant, value, label, onClickJs) {
    const icons = {
      cars: 'car',
      bookings: 'calendar',
      active: 'check',
      pending: 'calendar',
      earnings: 'dollar',
      revenue: 'dollar',
      owners: 'users',
      verified: 'shield',
    };
    const iconName = icons[variant] || 'chart';
    return '<button type="button" class="stat-card stat-card--btn" onclick="' + onClickJs + '">'
      + '<div class="stat-icon stat-icon--' + variant + '">' + UI.icon(iconName, 'icon') + '</div>'
      + '<div class="stat-val">' + UI.escHtml(value) + '</div>'
      + '<div class="stat-lbl">' + UI.escHtml(label) + '</div>'
      + '</button>';
  },

  emptyState(title, message, actionHtml) {
    actionHtml = actionHtml || '';
    return '<div class="empty">'
      + '<h3>' + UI.escHtml(title) + '</h3>'
      + '<p>' + UI.escHtml(message) + '</p>'
      + (actionHtml ? '<div class="empty-actions">' + actionHtml + '</div>' : '')
      + '</div>';
  },

  refreshTableScrollHints() {
    document.querySelectorAll('.table-wrap table').forEach(function (table) {
      const wrap = table.closest('.table-wrap');
      if (!wrap) return;
      if (table.scrollWidth > wrap.clientWidth + 2) {
        wrap.classList.add('table-wrap--scroll-hint');
      } else {
        wrap.classList.remove('table-wrap--scroll-hint');
      }
    });
  },

  carThumb(imageUrl, staticNoImage) {
    if (imageUrl) {
      return '<img src="' + UI.escHtml(imageUrl) + '" alt="" loading="lazy"/>';
    }
    return '<img src="' + UI.escHtml(staticNoImage) + '" alt="No photo" class="thumb-placeholder"/>';
  },

  formatCarType(type) {
    if (!type) return '';
    return type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
  },

  listingCard(car, opts) {
    opts = opts || {};
    const ctaLabel = opts.ctaLabel || 'View details';
    const title = ((car.brand || '') + ' ' + (car.model || '')).trim();
    const year = car.year ? String(car.year) : '';
    const type = UI.formatCarType(car.car_type);
    const price = parseFloat(car.price_per_day || 0).toFixed(2);
    const avail = car.is_available;
    const statusClass = avail ? 'badge-green' : 'badge-gray';
    const statusText = avail ? 'Available' : 'Unavailable';
    const img = UI.carThumb(car.primary_image, window.STATIC_NO_IMAGE);
    const location = car.location || 'Location not set';
    const ownerHtml = car.owner_name
      ? '<span class="listing-card-owner">' + UI.escHtml(car.owner_name) + '</span>'
      : '';

    return '<a class="listing-card" href="/cars/' + encodeURIComponent(car.id) + '/">'
      + '<div class="listing-card-media">'
      + '<div class="listing-card-thumb">' + img + '</div>'
      + '<span class="listing-card-chip listing-card-chip--type">' + UI.escHtml(type) + '</span>'
      + '<span class="listing-card-chip listing-card-chip--status badge ' + statusClass + '">'
      + UI.escHtml(statusText) + '</span>'
      + '</div>'
      + '<div class="listing-card-body">'
      + '<div class="listing-card-head">'
      + '<h3 class="listing-card-title">' + UI.escHtml(title) + '</h3>'
      + (year ? '<span class="listing-card-year">' + UI.escHtml(year) + '</span>' : '')
      + '</div>'
      + '<p class="listing-card-loc">'
      + UI.icon('pin', 'icon icon-inline')
      + '<span>' + UI.escHtml(location) + '</span>'
      + ownerHtml
      + '</p>'
      + '<div class="listing-card-foot">'
      + '<div class="listing-card-price">'
      + '<span class="listing-card-price-val">$' + price + '</span>'
      + '<span class="listing-card-price-unit">per day</span>'
      + '</div>'
      + '<span class="listing-card-cta">'
      + ctaLabel
      + UI.icon('arrow-left', 'icon icon-cta')
      + '</span>'
      + '</div>'
      + '</div>'
      + '</a>';
  },

  listingStatusBadge(car) {
    if (!car.is_approved) {
      return '<span class="badge badge-red">Removed by admin</span>';
    }
    if (!car.is_available) {
      return '<span class="badge badge-gray">Hidden</span>';
    }
    return '<span class="badge badge-green">Live on marketplace</span>';
  },

  locationLine(location, ownerName) {
    let html = '<span class="car-loc">' + UI.icon('pin', 'icon icon-inline') + ' ' + UI.escHtml(location || '');
    if (ownerName) html += ' · ' + UI.escHtml(ownerName);
    return html + '</span>';
  },

  switchDashLegacy(opts) {
    document.querySelectorAll('.' + opts.panelClass).forEach(function (p) {
      p.classList.remove('active');
    });
    document.querySelectorAll('.' + opts.navClass).forEach(function (b) {
      b.classList.remove('active');
    });
    const panel = document.getElementById(opts.panelPrefix + opts.tabId);
    if (panel) panel.classList.add('active');
    if (opts.btn) opts.btn.classList.add('active');
    if (opts.onActivate) opts.onActivate(opts.tabId);
    UI.closeSidebarDrawer();
  },

  closeSidebarDrawer() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    const toggle = document.getElementById('sidebarToggle');
    if (sidebar) sidebar.classList.remove('sidebar-open');
    if (backdrop) backdrop.classList.remove('is-visible');
    document.body.classList.remove('sidebar-drawer-open');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
    }
  },

  openSidebarDrawer() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    let backdrop = document.querySelector('.sidebar-backdrop');
    if (!backdrop) {
      backdrop = document.createElement('button');
      backdrop.type = 'button';
      backdrop.className = 'sidebar-backdrop';
      backdrop.setAttribute('aria-label', 'Close menu');
      backdrop.addEventListener('click', function () {
        UI.closeSidebarDrawer();
      });
      document.body.appendChild(backdrop);
    }
    sidebar.classList.add('sidebar-open');
    backdrop.classList.add('is-visible');
    document.body.classList.add('sidebar-drawer-open');
    const toggle = document.getElementById('sidebarToggle');
    if (toggle) {
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close menu');
    }
  },

  initSidebarDrawer() {
    const menuBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (!menuBtn || !sidebar || menuBtn.dataset.sidebarInit) return;
    menuBtn.dataset.sidebarInit = '1';
    menuBtn.addEventListener('click', function () {
      if (sidebar.classList.contains('sidebar-open')) {
        UI.closeSidebarDrawer();
      } else {
        UI.openSidebarDrawer();
      }
    });
    document.querySelectorAll('.sidebar .s-item').forEach(function (item) {
      item.addEventListener('click', function () {
        if (window.matchMedia('(max-width: 860px)').matches) {
          UI.closeSidebarDrawer();
        }
      });
    });
  },

  switchDashTab(navRoot, tabId, onActivate) {
    const root = typeof navRoot === 'string' ? document.querySelector(navRoot) : navRoot;
    if (!root) return;
    root.querySelectorAll('[data-tab]').forEach(function (btn) {
      const active = btn.getAttribute('data-tab') === tabId;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    document.querySelectorAll('[data-panel]').forEach(function (panel) {
      const show = panel.getAttribute('data-panel') === tabId;
      panel.hidden = !show;
      panel.classList.toggle('active', show);
    });
    if (typeof onActivate === 'function') onActivate(tabId);
  },

  initModal(modalEl, options) {
    options = options || {};
    if (!modalEl || modalEl.dataset.modalInit) return;
    modalEl.dataset.modalInit = '1';
    modalEl.setAttribute('role', 'dialog');
    modalEl.setAttribute('aria-modal', 'true');
    const closeBtns = modalEl.querySelectorAll('[data-modal-close]');
    function closeModal() {
      modalEl.classList.remove('open');
      modalEl.hidden = true;
      if (options.onClose) options.onClose();
    }
    closeBtns.forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });
    modalEl.addEventListener('click', function (e) {
      if (e.target === modalEl) closeModal();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && modalEl.classList.contains('open')) closeModal();
    });
    modalEl.openModal = function () {
      modalEl.hidden = false;
      modalEl.classList.add('open');
      const focusable = modalEl.querySelector(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable) focusable.focus();
    };
    modalEl.closeModal = closeModal;
  },

  tdId(id) {
    return '<td class="td-id">#' + id + '</td>';
  },

  tdMeta(html, extraClass) {
    extraClass = extraClass || '';
    return '<td class="td-meta' + (extraClass ? ' ' + extraClass : '') + '">' + html + '</td>';
  },

  subline(html) {
    return '<div class="text-subline">' + html + '</div>';
  },

  tableEmpty() {
    return '<span class="table-empty">—</span>';
  },

  parseListResponse(data, currentPage, pageSize) {
    pageSize = pageSize || UI_PAGE.catalog;
    currentPage = currentPage || 1;
    if (Array.isArray(data)) {
      return {
        items: data,
        count: data.length,
        page: 1,
        pageSize: data.length || pageSize,
        totalPages: 1,
        hasNext: false,
        hasPrev: false,
        isPaginated: false,
      };
    }
    const items = data.results || [];
    const count = typeof data.count === 'number' ? data.count : items.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    return {
      items: items,
      count: count,
      page: currentPage,
      pageSize: pageSize,
      totalPages: totalPages,
      hasNext: !!data.next,
      hasPrev: !!data.previous,
      isPaginated: count > pageSize,
    };
  },

  paginateSlice(list, page, pageSize) {
    pageSize = pageSize || UI_PAGE.table;
    const count = list.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const safePage = Math.min(Math.max(1, page), totalPages);
    const start = (safePage - 1) * pageSize;
    const end = Math.min(start + pageSize, count);
    return {
      items: list.slice(start, end),
      count: count,
      page: safePage,
      pageSize: pageSize,
      totalPages: totalPages,
      hasNext: safePage < totalPages,
      hasPrev: safePage > 1,
      isPaginated: count > pageSize,
      rangeStart: count ? start + 1 : 0,
      rangeEnd: end,
    };
  },

  renderPagination(meta, opts) {
    opts = opts || {};
    const label = opts.label || 'results';
    if (!meta.count || meta.totalPages <= 1) return '';

    const prevDisabled = meta.page <= 1;
    const nextDisabled = meta.page >= meta.totalPages;
    const range = meta.rangeStart != null
      ? meta.rangeStart + '–' + meta.rangeEnd
      : ((meta.page - 1) * meta.pageSize + 1) + '–'
        + Math.min(meta.page * meta.pageSize, meta.count);

    let html = '<nav class="pagination" role="navigation" aria-label="Pagination">';
    html += '<button type="button" class="pagination-btn" data-page="' + (meta.page - 1)
      + '" aria-label="Previous page"' + (prevDisabled ? ' disabled' : '') + '>';
    html += UI.icon('arrow-left', 'icon icon-sm') + '<span>Previous</span></button>';

    html += '<div class="pagination-meta">';
    html += '<span class="pagination-pages">Page <strong>' + meta.page + '</strong> of '
      + meta.totalPages + '</span>';
    html += '<span class="pagination-range text-caption">Showing ' + range + ' of '
      + meta.count + ' ' + label + '</span>';
    html += '</div>';

    html += '<button type="button" class="pagination-btn" data-page="' + (meta.page + 1)
      + '" aria-label="Next page"' + (nextDisabled ? ' disabled' : '') + '>';
    html += '<span>Next</span>' + UI.icon('arrow-left', 'icon icon-sm icon-flip') + '</button>';
    html += '</nav>';
    return html;
  },

  mountPagination(containerId, meta, onPageChange, opts) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!meta.count || meta.totalPages <= 1) {
      el.innerHTML = '';
      el.hidden = true;
      return;
    }
    el.hidden = false;
    el.innerHTML = UI.renderPagination(meta, opts);
    el.querySelectorAll('.pagination-btn[data-page]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (btn.disabled) return;
        const next = parseInt(btn.getAttribute('data-page'), 10);
        if (!next || next < 1 || next > meta.totalPages) return;
        onPageChange(next);
      });
    });
  },

  scrollToEl(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  },

  /**
   * Activate a filter tab within a tablist container.
   * @param {HTMLElement|string} container - .filter-tabs element or id
   * @param {HTMLButtonElement} activeBtn - clicked button
   */
  setFilterTabActive(container, activeBtn) {
    const root = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    if (!root) return;
    root.querySelectorAll('.ftab').forEach(function (btn) {
      const on = btn === activeBtn;
      btn.classList.toggle('active', on);
      btn.setAttribute('aria-selected', on ? 'true' : 'false');
    });
  },

  /**
   * Wire filter tabs: click sets active state and calls onSelect(filterValue, btn).
   */
  initFilterTabs(container, onSelect) {
    const root = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    if (!root || root.dataset.filterTabsInit) return root;
    root.dataset.filterTabsInit = '1';
    if (!root.getAttribute('role')) root.setAttribute('role', 'tablist');
    root.querySelectorAll('.ftab').forEach(function (btn) {
      if (!btn.hasAttribute('aria-selected')) {
        btn.setAttribute('aria-selected', btn.classList.contains('active') ? 'true' : 'false');
      }
      btn.addEventListener('click', function () {
        UI.setFilterTabActive(root, btn);
        const value = btn.getAttribute('data-filter');
        if (typeof onSelect === 'function') {
          onSelect(value != null ? value : '', btn);
        }
      });
    });
    return root;
  },

  /**
   * Human-readable result line for list toolbars.
   */
  resultsSummary(opts) {
    opts = opts || {};
    const filtered = opts.filtered;
    const total = opts.total;
    const label = opts.label || 'results';
    const filterLabel = opts.filterLabel || '';

    if (total == null || total === 0) {
      return 'No ' + label + ' found';
    }
    if (filtered != null && filtered !== total && filterLabel) {
      return 'Showing <strong>' + filtered + '</strong> of <strong>' + total
        + '</strong> ' + label + ' (' + UI.escHtml(filterLabel) + ')';
    }
    if (filtered != null && filtered !== total) {
      return 'Showing <strong>' + filtered + '</strong> of <strong>' + total
        + '</strong> ' + label;
    }
    return '<strong>' + total + '</strong> ' + label;
  },

  updateResultsCount(elementId, opts) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = UI.resultsSummary(opts);
  },

  bookingStatusLabel(status) {
    const map = {
      pending: 'Pending',
      approved: 'Approved',
      completed: 'Completed',
      cancelled: 'Cancelled',
      rejected: 'Rejected',
    };
    return status ? (map[status] || status) : '';
  },

  carFilterLabel(filter) {
    const map = {
      all: '',
      live: 'Live on marketplace',
      hidden: 'Hidden from browse',
      available: 'Available',
      unavailable: 'Unavailable',
    };
    return map[filter] || '';
  },

  filterCarList(cars, filter) {
    if (!filter || filter === 'all') return cars;
    if (filter === 'live') {
      return cars.filter(function (c) { return c.is_approved && c.is_available; });
    }
    if (filter === 'hidden') {
      return cars.filter(function (c) { return !c.is_approved; });
    }
    if (filter === 'available') {
      return cars.filter(function (c) { return c.is_available; });
    }
    if (filter === 'unavailable') {
      return cars.filter(function (c) { return !c.is_available; });
    }
    return cars;
  },
};

function carListingBadges(car) {
  let html = UI.listingStatusBadge(car);
  if (car.is_approved && car.is_available) {
    html += ' <span class="badge badge-blue">Available</span>';
  }
  return html;
}

document.addEventListener('DOMContentLoaded', function () {
  UI.initTheme();
  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () { UI.toggleTheme(); });
  });
  UI.initSidebarDrawer();
  UI.refreshTableScrollHints();
  window.addEventListener('resize', function () {
    UI.refreshTableScrollHints();
  });
});
