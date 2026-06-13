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

  localDateInputValue(date) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return d.getFullYear() + '-' + m + '-' + day;
  },

  localTimeInputValue(date) {
    const d = date instanceof Date ? date : new Date(date);
    if (isNaN(d.getTime())) return '';
    const h = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return h + ':' + min;
  },

  todayLocalDateValue() {
    return UI.localDateInputValue(new Date());
  },

  isoFromLocalDateTime(dateStr, timeStr, defaultTime) {
    if (!dateStr) return null;
    const time = timeStr || defaultTime || '23:59';
    const parsed = new Date(dateStr + 'T' + time);
    if (isNaN(parsed.getTime())) return null;
    return parsed.toISOString();
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

  adminStatsGroup(title, iconName, cardsHtml) {
    return '<section class="admin-stats-section">'
      + '<h3 class="admin-stats-section__title">'
      + UI.icon(iconName, 'icon icon-sm')
      + UI.escHtml(title)
      + '</h3>'
      + '<div class="admin-stats-grid">' + cardsHtml + '</div>'
      + '</section>';
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
      hidden: 'x',
      paused: 'edit',
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
      hidden: 'x',
      paused: 'edit',
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
    if (typeof CarTaxonomy !== 'undefined' && CarTaxonomy.getTypeLabel) {
      return CarTaxonomy.getTypeLabel(type);
    }
    return type.charAt(0).toUpperCase() + type.slice(1).replace(/_/g, ' ');
  },

  formatCategoryLabel(category) {
    if (!category) return '';
    if (typeof CarTaxonomy !== 'undefined' && CarTaxonomy.getCategoryLabel) {
      return CarTaxonomy.getCategoryLabel(category);
    }
    return category.charAt(0).toUpperCase() + category.slice(1).replace(/_/g, ' ');
  },

  formatDisplayName(name) {
    if (!name) return '';
    return String(name).trim()
      .split(/[\s_\-]+/)
      .filter(Boolean)
      .map(function (w) {
        return w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();
      })
      .join(' ');
  },

  ownerDisplayName(carOrOwner) {
    if (!carOrOwner) return '';
    if (typeof carOrOwner === 'string') {
      return UI.formatDisplayName(carOrOwner);
    }
    if (carOrOwner.display_name) return carOrOwner.display_name;
    if (carOrOwner.owner_name) return carOrOwner.owner_name;
    if (carOrOwner.owner && carOrOwner.owner.display_name) {
      return carOrOwner.owner.display_name;
    }
    const raw = carOrOwner.owner_name
      || (carOrOwner.owner && carOrOwner.owner.username)
      || carOrOwner.username
      || '';
    return UI.formatDisplayName(raw);
  },

  rentalTypeLabel(type) {
    if (typeof CarTaxonomy !== 'undefined' && CarTaxonomy.getRentalDurationLabel) {
      return CarTaxonomy.getRentalDurationLabel(type) || type || '—';
    }
    const labels = {
      hourly: 'Hourly',
      daily: 'Daily',
      weekly: 'Weekly',
      monthly: 'Monthly',
    };
    return labels[type] || type || '—';
  },

  primaryRateDisplay(car) {
    if (!car) return { value: '0.00', unit: 'day', label: 'per day' };
    const dailyPrice = car.has_discount ? car.final_price : car.price_per_day;
    const types = [
      { on: car.rent_daily, price: dailyPrice, unit: 'day', label: 'per day' },
      { on: car.rent_hourly, price: car.price_per_hour, unit: 'hour', label: 'per hour' },
      { on: car.rent_weekly, price: car.price_per_week, unit: 'week', label: 'per week' },
      { on: car.rent_monthly, price: car.price_per_month, unit: 'month', label: 'per month' },
    ];
    for (let i = 0; i < types.length; i++) {
      const t = types[i];
      if (!t.on) continue;
      const n = parseFloat(t.price);
      if (!isNaN(n) && n > 0) {
        return { value: n.toFixed(2), unit: t.unit, label: t.label };
      }
    }
    return { value: '0.00', unit: 'day', label: 'per day' };
  },

  formatHourlyDuration(ms) {
    const totalMins = Math.max(0, Math.round(ms / 60000));
    const h = Math.floor(totalMins / 60);
    const m = totalMins % 60;
    if (h && m) return h + 'h ' + m + 'm';
    if (h) return h + 'h';
    return m + 'm';
  },

  inclusiveDays(start, end) {
    const s = new Date(start);
    const e = new Date(end);
    // Use UTC calendar dates so end-of-day (23:59:59Z) stays on the same rental day.
    const utcS = Date.UTC(s.getUTCFullYear(), s.getUTCMonth(), s.getUTCDate());
    const utcE = Date.UTC(e.getUTCFullYear(), e.getUTCMonth(), e.getUTCDate());
    return Math.floor((utcE - utcS) / 86400000) + 1;
  },

  computeRentalTotal(car, rentalType, startAt, endAt) {
    if (!car || !startAt || !endAt) return { error: 'Select dates and times.' };
    const start = new Date(startAt);
    const end = new Date(endAt);
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
      return { error: 'Invalid date or time.' };
    }

    if (rentalType === 'hourly') {
      if (!car.rent_hourly || !car.price_per_hour) {
        return { error: 'Hourly rental is not available for this car.' };
      }
      if (end <= start) return { error: 'Return must be after pick-up.' };
      const exactHours = (end - start) / 3600000;
      if (exactHours < 1) return { error: 'Minimum rental is 1 hour.' };
      const rate = parseFloat(car.price_per_hour);
      return {
        total: (exactHours * rate).toFixed(2),
        duration: UI.formatHourlyDuration(end - start),
        unitLabel: UI.formatHourlyDuration(end - start),
        rate: rate,
        originalRate: null,
      };
    }

    if (end < start) return { error: 'Return cannot be before pick-up.' };
    const startDay = start.toISOString().slice(0, 10);
    const todayDay = new Date().toISOString().slice(0, 10);
    if (startDay < todayDay) {
      return { error: 'Pick-up cannot be in the past.' };
    }
    const days = Math.max(1, UI.inclusiveDays(start, end));

    if (rentalType === 'daily') {
      if (!car.rent_daily || !car.price_per_day) {
        return { error: 'Daily rental is not available for this car.' };
      }
      const originalRate = parseFloat(car.price_per_day);
      const rate = car.has_discount ? parseFloat(car.final_price) : originalRate;
      return {
        total: (days * rate).toFixed(2),
        duration: days + ' day' + (days !== 1 ? 's' : ''),
        unitLabel: days + 'd',
        rate: rate,
        originalRate: car.has_discount ? originalRate : null,
      };
    }
    if (rentalType === 'weekly') {
      if (!car.rent_weekly || !car.price_per_week) {
        return { error: 'Weekly rental is not available for this car.' };
      }
      if (days < 7) return { error: 'Minimum weekly rental is 7 days.' };
      const weeks = Math.ceil(days / 7);
      const rate = parseFloat(car.price_per_week);
      return {
        total: (weeks * rate).toFixed(2),
        duration: weeks + ' week' + (weeks !== 1 ? 's' : ''),
        unitLabel: weeks + 'w',
        rate: rate,
        originalRate: null,
      };
    }
    if (rentalType === 'monthly') {
      if (!car.rent_monthly || !car.price_per_month) {
        return { error: 'Monthly rental is not available for this car.' };
      }
      if (days < 30) return { error: 'Minimum monthly rental is 30 days.' };
      const months = Math.ceil(days / 30);
      const rate = parseFloat(car.price_per_month);
      return {
        total: (months * rate).toFixed(2),
        duration: months + ' month' + (months !== 1 ? 's' : ''),
        unitLabel: months + 'mo',
        rate: rate,
        originalRate: null,
      };
    }
    return { error: 'Invalid rental type.' };
  },

  formatDateTimeLocal(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch (e) {
      return String(iso);
    }
  },

  formatDateLocal(iso) {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
      });
    } catch (e) {
      return String(iso).slice(0, 10);
    }
  },

  formatBookingPeriod(booking) {
    if (!booking) return '—';
    const type = booking.rental_type || 'daily';
    const start = booking.start_at;
    const end = booking.end_at;
    if (!start || !end) return booking.period_display || '—';
    if (type === 'hourly') {
      return UI.formatDateTimeLocal(start) + ' → ' + UI.formatDateTimeLocal(end);
    }
    return UI.formatDateLocal(start) + ' → ' + UI.formatDateLocal(end);
  },

  bookingDurationLabel(booking) {
    if (booking && booking.duration_label) return booking.duration_label;
    if (!booking || !booking.start_at || !booking.end_at) return '—';
    const r = UI.computeRentalTotal(
      booking.car || {},
      booking.rental_type,
      booking.start_at,
      booking.end_at
    );
    return r.unitLabel || '—';
  },

  renderStars(rating, opts) {
    opts = opts || {};
    const max = 5;
    const value = Math.max(0, Math.min(max, parseFloat(rating) || 0));
    const sizeClass = opts.size === 'sm' ? ' stars--sm' : (opts.size === 'lg' ? ' stars--lg' : '');
    const label = opts.ariaLabel || (value.toFixed(1) + ' out of 5 stars');
    let html = '<span class="stars' + sizeClass + '" role="img" aria-label="' + UI.escHtml(label) + '">';
    for (let i = 1; i <= max; i++) {
      const filled = i <= Math.round(value);
      html += '<span class="stars__star' + (filled ? ' stars__star--on' : '') + '">'
        + UI.icon('star', 'icon')
        + '</span>';
    }
    return html + '</span>';
  },

  formatReviewDate(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
      });
    } catch (e) {
      return '';
    }
  },

  bookedSlotStatusLabel(status) {
    if (status === 'pending') return 'Reserved (pending)';
    if (status === 'approved') return 'Booked';
    return UI.escHtml(status || 'Booked');
  },

  bookedSlotPeriod(slot) {
    if (!slot) return '—';
    return UI.formatBookingPeriod(slot);
  },

  bookedSlotEndShort(slot) {
    if (!slot || !slot.end_at) return '';
    if (slot.rental_type === 'hourly') {
      return UI.formatDateTimeLocal(slot.end_at);
    }
    return UI.formatDateLocal(slot.end_at);
  },

  bookedSlotsSummary(car) {
    const total = car.booked_slots_total || 0;
    const slots = car.booked_slots || [];
    if (!total && !slots.length) return '';

    if (car.is_currently_booked) {
      const endSlot = slots.find(function (s) { return s.is_active; }) || slots[0];
      const until = UI.bookedSlotEndShort(endSlot);
      let html = '<span class="booked-slots-summary booked-slots-summary--active">'
        + UI.icon('calendar', 'icon icon-inline')
        + '<span>Until <strong>' + UI.escHtml(until) + '</strong></span></span>';
      if (total > 1) {
        html += '<span class="booked-slots-summary__more">+' + (total - 1) + ' more</span>';
      }
      return html;
    }

    const next = slots[0];
    if (!next) return '';

    const period = UI.bookedSlotPeriod(next);
    const prefix = next.status === 'pending' ? 'Reserved' : 'Next booked';
    let line = '<span class="booked-slots-summary">'
      + UI.icon('calendar', 'icon icon-inline')
      + '<span>' + UI.escHtml(prefix) + ': ' + UI.escHtml(period);
    if (next.status === 'pending') {
      line += ' <span class="booked-slots-summary__pending">(pending)</span>';
    }
    line += '</span></span>';
    if (total > 1) {
      line += '<span class="booked-slots-summary__more">+' + (total - 1) + ' more</span>';
    }
    return line;
  },

  bookedSlotsListHtml(car) {
    const slots = car.booked_slots || [];
    if (!slots.length) return '';

    const items = slots.map(function (slot) {
      const badgeClass = slot.is_active
        ? 'badge-amber'
        : (slot.status === 'pending' ? 'badge-gray' : 'badge-blue');
      const badgeText = slot.is_active
        ? 'In progress'
        : UI.bookedSlotStatusLabel(slot.status);
      return '<li class="booked-slots-list__item">'
        + '<span class="badge ' + badgeClass + '">' + UI.escHtml(badgeText) + '</span>'
        + '<span class="booked-slots-list__period">' + UI.escHtml(UI.bookedSlotPeriod(slot)) + '</span>'
        + '</li>';
    }).join('');

    const more = (car.booked_slots_total || 0) > slots.length
      ? '<p class="booked-slots-list__more text-caption">'
        + UI.escHtml(String((car.booked_slots_total - slots.length))) + ' additional booking'
        + ((car.booked_slots_total - slots.length) !== 1 ? 's' : '') + ' not shown.</p>'
      : '';

    return '<ul class="booked-slots-list">' + items + '</ul>' + more;
  },

  reviewSummaryLine(carOrSummary) {
    const summary = carOrSummary && carOrSummary.review_summary
      ? carOrSummary.review_summary
      : {
        count: carOrSummary.review_count || 0,
        average_rating: carOrSummary.average_rating,
      };
    const count = summary.count || 0;
    if (!count) {
      return '<span class="review-summary review-summary--empty">No reviews yet</span>';
    }
    const avg = summary.average_rating != null
      ? Number(summary.average_rating).toFixed(1)
      : '—';
    return '<span class="review-summary">'
      + UI.renderStars(summary.average_rating, { size: 'sm', ariaLabel: avg + ' out of 5 from ' + count + ' reviews' })
      + '<span class="review-summary__text"><strong>' + UI.escHtml(avg) + '</strong>'
      + '<span class="review-summary__count">(' + count + ' review' + (count !== 1 ? 's' : '') + ')</span></span>'
      + '</span>';
  },

  listingRentalTypes(car) {
    if (car.enabled_rental_types && car.enabled_rental_types.length) {
      return car.enabled_rental_types.slice();
    }
    const types = [];
    if (car.rent_hourly) types.push('hourly');
    if (car.rent_daily) types.push('daily');
    if (car.rent_weekly) types.push('weekly');
    if (car.rent_monthly) types.push('monthly');
    return types;
  },

  listingRentalChipsHtml(car) {
    const types = UI.listingRentalTypes(car);
    if (!types.length) return '';
    return types.map(function (t) {
      return '<span class="listing-card-rental">' + UI.escHtml(UI.rentalTypeLabel(t)) + '</span>';
    }).join('');
  },

  listingStatusMeta(car) {
    const rentedNow = car.is_currently_booked;
    if (rentedNow) {
      return { modifier: 'rented', statusClass: 'is-rented', label: 'Rented' };
    }
    if (!car.is_available) {
      return { modifier: 'unavailable', statusClass: 'is-unavailable', label: 'Unavailable' };
    }
    return { modifier: '', statusClass: 'is-available', label: 'Available' };
  },

  listingAvailabilityHtml(car) {
    const summary = UI.bookedSlotsSummary(car);
    if (!summary) return '';
    return '<div class="listing-card-availability" role="note">'
      + summary
      + '</div>';
  },

  prefersReducedMotion() {
    return window.matchMedia
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },

  listingSkeletonCards(count) {
    count = count || 6;
    let html = '';
    for (let i = 0; i < count; i++) {
      html += '<div class="listing-skeleton" aria-hidden="true">'
        + '<div class="listing-skeleton__media"></div>'
        + '<div class="listing-skeleton__body">'
        + '<div class="listing-skeleton__line listing-skeleton__line--title"></div>'
        + '<div class="listing-skeleton__line listing-skeleton__line--short"></div>'
        + '<div class="listing-skeleton__line listing-skeleton__line--meta"></div>'
        + '<div class="listing-skeleton__foot">'
        + '<div class="listing-skeleton__line listing-skeleton__line--price"></div>'
        + '<div class="listing-skeleton__pill"></div>'
        + '</div>'
        + '</div>'
        + '</div>';
    }
    return html;
  },

  animateListingGrid(gridEl) {
    if (!gridEl) return;
    gridEl.classList.remove('cars-grid--reveal');
    const cards = gridEl.querySelectorAll('.listing-card');
    if (!cards.length) return;

    const reduced = UI.prefersReducedMotion();
    cards.forEach(function (card, i) {
      card.style.animationDelay = reduced ? '0ms' : (Math.min(i * 55, 440) + 'ms');
    });

    requestAnimationFrame(function () {
      gridEl.classList.add('cars-grid--reveal');
    });
  },

  animateResultsCount(el) {
    if (!el || UI.prefersReducedMotion()) return;
    el.classList.remove('results-bar__count--pop');
    void el.offsetWidth;
    el.classList.add('results-bar__count--pop');
  },

  discountMeta(car) {
    if (!car || !car.has_discount || !car.price_per_day) return null;
    const original = parseFloat(car.price_per_day);
    const final = parseFloat(car.final_price);
    if (isNaN(original) || isNaN(final) || final >= original) return null;
    let pct = null;
    if (car.discount_percentage != null && car.discount_percentage > 0) {
      pct = car.discount_percentage;
    } else {
      pct = Math.round((1 - final / original) * 100);
    }
    if (!pct || pct <= 0) return null;
    return {
      pct: pct,
      original: original,
      final: final,
      label: pct + '% OFF',
      shortLabel: '-' + pct + '%',
    };
  },

  listingDiscountBadgeHtml(car) {
    const d = UI.discountMeta(car);
    if (!d) return '';
    return '<span class="listing-card-badge listing-card-badge--discount" aria-label="'
      + UI.escHtml(d.label) + '">'
      + '<span class="listing-card-discount-pct">' + UI.escHtml(d.shortLabel) + '</span>'
      + '</span>';
  },

  listingDiscountPriceHtml(car, rate, showFrom) {
    const d = UI.discountMeta(car);
    if (!d || rate.unit !== 'day') {
      return '<div class="listing-card-price">'
        + (showFrom ? '<span class="listing-card-price-from">From</span>' : '')
        + '<span class="listing-card-price-line">'
        + '<span class="listing-card-price-val">$' + rate.value + '</span>'
        + '<span class="listing-card-price-unit">' + UI.escHtml(rate.label) + '</span>'
        + '</span></div>';
    }
    return '<div class="listing-card-price listing-card-price--discounted">'
      + (showFrom ? '<span class="listing-card-price-from">From</span>' : '')
      + '<span class="listing-card-price-line">'
      + '<span class="listing-card-price-val listing-card-price-val--old" aria-hidden="true">$'
      + d.original.toFixed(2) + '</span>'
      + '<span class="listing-card-price-val listing-card-price-val--sale">$'
      + d.final.toFixed(2) + '</span>'
      + '<span class="listing-card-price-unit">' + UI.escHtml(rate.label) + '</span>'
      + '</span>'
      + '<span class="listing-card-price-save">Save ' + d.pct + '%</span>'
      + '</div>';
  },

  detailDiscountPriceHtml(car, rate) {
    const d = UI.discountMeta(car);
    if (!d || rate.unit !== 'day') {
      return '<div class="detail-price">$' + rate.value + '<span> / ' + rate.unit + '</span></div>';
    }
    return '<div class="detail-price-wrap detail-price-wrap--discounted">'
      + '<span class="detail-discount-badge">' + UI.escHtml(d.label) + '</span>'
      + '<div class="detail-price detail-price--discounted">'
      + '<span class="detail-price-val detail-price-val--old" aria-hidden="true">$'
      + d.original.toFixed(2) + '</span>'
      + '<span class="detail-price-val detail-price-val--sale">$'
      + d.final.toFixed(2) + '</span>'
      + '<span class="detail-price-unit">/ ' + rate.unit + '</span>'
      + '</div>'
      + '<p class="detail-price-save">You save ' + d.pct + '% on the daily rate</p>'
      + '</div>';
  },

  detailGalleryDiscountBadgeHtml(car) {
    const d = UI.discountMeta(car);
    if (!d) return '';
    return '<span class="detail-gallery-discount" aria-label="' + UI.escHtml(d.label) + '">'
      + UI.escHtml(d.shortLabel) + '</span>';
  },

  listingCard(car, opts) {
    opts = opts || {};
    const ctaLabel = opts.ctaLabel || 'View details';
    const title = ((car.brand || '') + ' ' + (car.model || '')).trim() || 'Car listing';
    const year = car.year ? String(car.year) : '';
    const type = car.car_type_display || UI.formatCarType(car.car_type);
    const category = car.category;
    let badgeLabel = type;
    if (category && category !== 'car') {
      const catLabel = car.category_display || UI.formatCategoryLabel(category);
      badgeLabel = catLabel + (type ? ' · ' + type : '');
    }
    const rate = UI.primaryRateDisplay(car);
    const price = rate.value;
    const priceUnit = rate.label;
    const rentalTypes = UI.listingRentalTypes(car);
    const showFrom = rentalTypes.length > 1;
    const status = UI.listingStatusMeta(car);
    const availabilityHtml = UI.listingAvailabilityHtml(car);
    const rentalChips = UI.listingRentalChipsHtml(car);
    const img = UI.carThumb(car.primary_image, window.STATIC_NO_IMAGE);
    const location = car.location || 'Location not set';
    const ownerLabel = UI.ownerDisplayName(car);
    const ownerHtml = ownerLabel
      ? '<span class="listing-card-owner" title="Listed by ' + UI.escHtml(ownerLabel) + '">'
        + UI.escHtml(ownerLabel)
        + '</span>'
      : '';

    const ariaParts = [title, year, badgeLabel || type, location, 'from $' + price + ' ' + priceUnit];
    if (status.label) ariaParts.push(status.label);
    const discount = UI.discountMeta(car);

    const cardClass = 'listing-card'
      + (status.modifier ? ' listing-card--' + status.modifier : '')
      + (discount && rate.unit === 'day' ? ' listing-card--discounted' : '');

    return '<a class="' + cardClass + '" href="/cars/' + encodeURIComponent(car.id) + '/"'
      + ' aria-label="' + UI.escHtml(ariaParts.filter(Boolean).join(', ')) + '">'
      + '<div class="listing-card-media">'
      + '<div class="listing-card-thumb">' + img + '</div>'
      + (badgeLabel
        ? '<span class="listing-card-badge listing-card-badge--type">' + UI.escHtml(badgeLabel) + '</span>'
        : '')
      + (discount && rate.unit === 'day' ? UI.listingDiscountBadgeHtml(car) : '')
      + '<span class="listing-card-badge listing-card-badge--status ' + status.statusClass + '">'
      + '<span class="listing-card-status-dot" aria-hidden="true"></span>'
      + '<span>' + UI.escHtml(status.label) + '</span>'
      + '</span>'
      + '</div>'
      + '<div class="listing-card-body">'
      + '<div class="listing-card-head">'
      + '<h3 class="listing-card-title">' + UI.escHtml(title) + '</h3>'
      + (year ? '<span class="listing-card-year">' + UI.escHtml(year) + '</span>' : '')
      + '</div>'
      + '<p class="listing-card-loc" title="' + UI.escHtml(location) + '">'
      + UI.icon('pin', 'icon icon-inline')
      + '<span class="listing-card-loc-text">' + UI.escHtml(location) + '</span>'
      + ownerHtml
      + '</p>'
      + '<div class="listing-card-meta">'
      + '<div class="listing-card-rating">' + UI.reviewSummaryLine(car) + '</div>'
      + (rentalChips
        ? '<div class="listing-card-rentals" aria-label="Rental options">' + rentalChips + '</div>'
        : '')
      + '</div>'
      + availabilityHtml
      + '<div class="listing-card-foot">'
      + UI.listingDiscountPriceHtml(car, rate, showFrom)
      + '<span class="listing-card-cta">'
      + '<span class="listing-card-cta-text">' + UI.escHtml(ctaLabel) + '</span>'
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
      return '<span class="badge badge-amber">Paused by you</span>';
    }
    return '<span class="badge badge-green">Live on marketplace</span>';
  },

  locationLine(location, ownerName) {
    let html = '<span class="car-loc">' + UI.icon('pin', 'icon icon-inline') + ' ' + UI.escHtml(location || '');
    if (ownerName) html += ' · ' + UI.escHtml(UI.formatDisplayName(ownerName));
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
    UI.syncDashboardTabUrl(opts.tabId);
    UI.setDashboardMessagesLayout(opts.tabId === 'messages');
    if (opts.onActivate) opts.onActivate(opts.tabId);
    UI.closeSidebarDrawer();
  },

  getActiveDashboardTab() {
    const panel = document.querySelector('.tab-panel.active');
    if (!panel || !panel.id || panel.id.indexOf('tab-') !== 0) return '';
    return panel.id.replace(/^tab-/, '');
  },

  syncDashboardTabUrl(tabId) {
    if (!tabId || !document.querySelector('.dash-layout')) return;
    const url = new URL(window.location.href);
    url.searchParams.delete('tab');
    url.hash = tabId;
    const next = url.pathname + url.search + url.hash;
    const current = window.location.pathname + window.location.search + window.location.hash;
    if (next !== current) {
      history.replaceState(null, '', next);
    }
  },

  setDashboardMessagesLayout(isMessagesTab) {
    document.querySelectorAll('.dash-layout').forEach(function (layout) {
      layout.classList.toggle('dash-layout--messages-tab', !!isMessagesTab);
    });
  },

  openDashboardTabFromHash() {
    const hash = (location.hash || '').replace('#', '').trim();
    if (!hash || !document.querySelector('.dash-layout')) return false;
    if (UI.getActiveDashboardTab() === hash) return true;
    const btn = document.getElementById('btn-' + hash);
    if (!btn || typeof showTab !== 'function') return false;
    showTab(hash, btn);
    return true;
  },

  bootDashboardTab(fallbackTab) {
    if (UI.openDashboardTabFromHash()) return true;
    const tab = new URLSearchParams(window.location.search).get('tab') || fallbackTab || '';
    if (tab && document.getElementById('btn-' + tab) && typeof showTab === 'function') {
      showTab(tab, document.getElementById('btn-' + tab));
      return true;
    }
    return false;
  },

  initDashboardTabRouting() {
    if (UI._dashboardTabRoutingInit) return;
    UI._dashboardTabRoutingInit = true;
    window.addEventListener('hashchange', function () {
      UI.openDashboardTabFromHash();
    });
  },

  interceptDashboardNavLinks() {
    const currentPath = window.location.pathname.replace(/\/$/, '');
    const isDashboard = /^\/dashboard\/(admin|owner|customer)$/.test(currentPath);
    if (!isDashboard || !document.querySelector('.dash-layout')) return;

    function handleInPlaceNav(event, tabId) {
      event.preventDefault();
      const btn = document.getElementById('btn-' + tabId);
      if (btn && typeof showTab === 'function') {
        showTab(tabId, btn);
      }
    }

    const dashLink = document.getElementById('nav-dash-link');
    if (dashLink) {
      dashLink.addEventListener('click', function (event) {
        const targetPath = (dashLink.getAttribute('href') || '').replace(/\/$/, '').split('#')[0];
        if (targetPath && currentPath === targetPath.replace(/\/$/, '')) {
          handleInPlaceNav(event, 'overview');
        }
      });
    }
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

  tdSerial(n) {
    return '<td class="td-serial">' + UI.escHtml(String(n)) + '</td>';
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

  tableLoadingRow(colspan) {
    return '<tr><td colspan="' + colspan + '">'
      + '<div class="loading"><span class="spinner"></span></div>'
      + '</td></tr>';
  },

  mapStatusTabToQuery(variant, filterValue) {
    const val = filterValue || '';
    if (variant === 'admin_cars' || variant === 'owner_cars') {
      if (!val || val === 'all') return {};
      if (val === 'hidden' || val === 'admin_removed') return { listing: 'admin_removed' };
      if (val === 'unavailable' || val === 'paused') return { listing: 'paused' };
      if (val === 'live') return { listing: 'live' };
      return {};
    }
    if (variant === 'admin_owners') {
      if (val === 'pending') return { is_verified: 'false' };
      if (val === 'verified') return { is_verified: 'true' };
      return {};
    }
    if (!val) return {};
    return { status: val };
  },

  buildListQuery(baseUrl, state) {
    const params = new URLSearchParams();
    if (state.page) params.set('page', String(state.page));
    if (state.search) params.set('search', state.search);
    if (state.listing) params.set('listing', state.listing);
    if (state.status) params.set('status', state.status);
    if (state.is_verified != null && state.is_verified !== '') {
      params.set('is_verified', String(state.is_verified));
    }
    if (state.is_available != null && state.is_available !== '') {
      params.set('is_available', String(state.is_available));
    }
    if (state.car_type) params.set('car_type', state.car_type);
    if (state.rental_type) params.set('rental_type', state.rental_type);
    if (state.ordering) params.set('ordering', state.ordering);
    const qs = params.toString();
    if (!qs) return baseUrl;
    return baseUrl + (baseUrl.indexOf('?') >= 0 ? '&' : '?') + qs;
  },

  async fetchListPage(url, page, pageSize) {
    pageSize = pageSize || UI_PAGE.table;
    page = page || 1;
    const data = await API.get(url);
    return UI.parseListResponse(data, page, pageSize);
  },

  getTableFilterState(toolbarId, variant) {
    const root = document.getElementById(toolbarId);
    if (!root) {
      return { search: '', ordering: '', car_type: '', rental_type: '' };
    }
    const searchEl = document.getElementById(toolbarId + 'Search');
    const sortEl = document.getElementById(toolbarId + 'Sort');
    const typeEl = document.getElementById(toolbarId + 'Type');
    const rentalEl = document.getElementById(toolbarId + 'Rental');
    return {
      search: searchEl ? searchEl.value.trim() : '',
      ordering: sortEl ? sortEl.value : '',
      car_type: typeEl ? typeEl.value : '',
      rental_type: rentalEl ? rentalEl.value : '',
      variant: variant || root.getAttribute('data-variant') || '',
    };
  },

  resetTableFilters(toolbarId, statusTabsId) {
    const searchEl = document.getElementById(toolbarId + 'Search');
    const sortEl = document.getElementById(toolbarId + 'Sort');
    const typeEl = document.getElementById(toolbarId + 'Type');
    const rentalEl = document.getElementById(toolbarId + 'Rental');
    if (searchEl) searchEl.value = '';
    if (typeEl) typeEl.value = '';
    if (rentalEl) rentalEl.value = '';
    if (sortEl) {
      const first = sortEl.querySelector('option');
      if (first) sortEl.value = first.value;
    }
    if (statusTabsId) {
      const tabs = document.getElementById(statusTabsId);
      if (tabs) {
        const allTab = tabs.querySelector('[data-filter=""], [data-filter="all"]');
        if (allTab) UI.setFilterTabActive(tabs, allTab);
      }
    }
  },

  initTableFilters(opts) {
    opts = opts || {};
    const toolbarId = opts.toolbarId;
    const variant = opts.variant;
    const statusTabsId = opts.statusTabsId;
    const debounceMs = opts.debounceMs || 350;
    let timer = null;

    function emitChange() {
      if (typeof opts.onChange === 'function') opts.onChange();
    }

    const searchEl = document.getElementById(toolbarId + 'Search');
    if (searchEl && !searchEl.dataset.tableFilterBound) {
      searchEl.dataset.tableFilterBound = '1';
      searchEl.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(emitChange, debounceMs);
      });
    }

    ['Sort', 'Type', 'Rental'].forEach(function (suffix) {
      const el = document.getElementById(toolbarId + suffix);
      if (el && !el.dataset.tableFilterBound) {
        el.dataset.tableFilterBound = '1';
        el.addEventListener('change', emitChange);
      }
    });

    const resetEl = document.getElementById(toolbarId + 'Reset');
    if (resetEl && !resetEl.dataset.tableFilterBound) {
      resetEl.dataset.tableFilterBound = '1';
      resetEl.addEventListener('click', function () {
        UI.resetTableFilters(toolbarId, statusTabsId);
        emitChange();
      });
    }

    if (statusTabsId && opts.onStatusChange) {
      UI.initFilterTabs(statusTabsId, function (filterValue) {
        opts.onStatusChange(filterValue);
      });
    }

    return { toolbarId: toolbarId, variant: variant };
  },

  parseListResponse(data, currentPage, pageSize) {
    pageSize = pageSize || UI_PAGE.catalog;
    currentPage = currentPage || 1;
    if (Array.isArray(data)) {
      const count = data.length;
      return {
        items: data,
        count: count,
        page: 1,
        pageSize: data.length || pageSize,
        totalPages: 1,
        hasNext: false,
        hasPrev: false,
        isPaginated: false,
        rangeStart: count ? 1 : 0,
        rangeEnd: count,
      };
    }
    const items = data.results || [];
    const count = typeof data.count === 'number' ? data.count : items.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const rangeStart = count ? (currentPage - 1) * pageSize + 1 : 0;
    const rangeEnd = Math.min(currentPage * pageSize, count);
    return {
      items: items,
      count: count,
      page: currentPage,
      pageSize: pageSize,
      totalPages: totalPages,
      hasNext: !!data.next,
      hasPrev: !!data.previous,
      isPaginated: count > pageSize,
      rangeStart: rangeStart,
      rangeEnd: rangeEnd,
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
    const searchText = opts.searchText || '';

    if (filtered === 0) {
      if (searchText || filterLabel) {
        return 'No matching ' + label;
      }
      return 'No ' + label + ' found';
    }
    let parts = [];
    if (searchText) parts.push('search: “' + UI.escHtml(searchText) + '”');
    if (filterLabel) parts.push(UI.escHtml(filterLabel));
    const suffix = parts.length ? ' (' + parts.join(' · ') + ')' : '';
    if (filtered != null && total != null && filtered !== total) {
      return 'Showing <strong>' + filtered + '</strong> of <strong>' + total
        + '</strong> ' + label + suffix;
    }
    return '<strong>' + (filtered != null ? filtered : total) + '</strong> ' + label + suffix;
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

  carFilterLabel(filter, context) {
    context = context || 'admin';
    if (context === 'owner') {
      const ownerMap = {
        all: '',
        live: 'Live on marketplace',
        paused: 'Paused by you',
        admin_removed: 'Removed by admin',
        unavailable: 'Paused by you',
        hidden: 'Removed by admin',
      };
      return ownerMap[filter] || '';
    }
    const map = {
      all: '',
      live: 'Live on marketplace',
      hidden: 'Removed by admin',
      unavailable: 'Paused by owner',
      paused: 'Paused by owner',
      admin_removed: 'Removed by admin',
    };
    return map[filter] || '';
  },

  filterCarList(cars, filter) {
    if (!filter || filter === 'all') return cars;
    if (filter === 'live') {
      return cars.filter(function (c) { return c.is_approved && c.is_available; });
    }
    if (filter === 'hidden' || filter === 'admin_removed') {
      return cars.filter(function (c) { return !c.is_approved; });
    }
    if (filter === 'unavailable' || filter === 'paused') {
      return cars.filter(function (c) { return !c.is_available; });
    }
    return cars;
  },
};

function carListingBadges(car) {
  return UI.listingStatusBadge(car);
}

document.addEventListener('DOMContentLoaded', function () {
  UI.initTheme();
  document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () { UI.toggleTheme(); });
  });
  UI.initSidebarDrawer();
  UI.initDashboardTabRouting();
  UI.refreshTableScrollHints();
  window.addEventListener('resize', function () {
    UI.refreshTableScrollHints();
  });
});
