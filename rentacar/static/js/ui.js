/* Shared UI helpers — icons, theme, stat cards, listing badges */

const UI = {
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
      + '<div class="stat-val">' + value + '</div>'
      + '<div class="stat-lbl">' + label + '</div>'
      + '</div>';
  },

  emptyState(title, message, actionHtml) {
    actionHtml = actionHtml || '';
    return '<div class="empty">'
      + '<h3>' + title + '</h3>'
      + '<p>' + message + '</p>'
      + actionHtml
      + '</div>';
  },

  carThumb(imageUrl, staticNoImage) {
    if (imageUrl) {
      return '<img src="' + imageUrl + '" alt="" loading="lazy"/>';
    }
    return '<img src="' + staticNoImage + '" alt="No photo" class="thumb-placeholder"/>';
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
    let html = '<span class="car-loc">' + UI.icon('pin', 'icon icon-inline') + ' ' + (location || '');
    if (ownerName) html += ' · ' + ownerName;
    return html + '</span>';
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
  const menuBtn = document.getElementById('sidebarToggle');
  const sidebar = document.querySelector('.sidebar');
  if (menuBtn && sidebar) {
    menuBtn.addEventListener('click', function () {
      sidebar.classList.toggle('sidebar-open');
    });
  }
});
