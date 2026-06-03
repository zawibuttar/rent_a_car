/**
 * Shared catalog browse logic for home and /cars/ pages.
 */
const Catalog = {
  page: 1,
  searchTimer: null,
  sortLabels: {
    '-created_at': 'Newest first',
    price_per_day: 'Price: low to high',
    '-price_per_day': 'Price: high to low',
    '-year': 'Newest year',
    year: 'Oldest year',
  },
  typeLabels: {
    sedan: 'Sedan',
    suv: 'SUV',
    luxury: 'Luxury',
    hatchback: 'Hatchback',
    truck: 'Truck',
    van: 'Van',
  },

  getSearchText() {
    const hero = document.getElementById('heroInput');
    const inline = document.getElementById('fSearch');
    if (inline) return inline.value.trim();
    if (hero) return hero.value.trim();
    return '';
  },

  setSearchText(value) {
    const hero = document.getElementById('heroInput');
    const inline = document.getElementById('fSearch');
    if (inline) inline.value = value;
    if (hero) hero.value = value;
  },

  getFilterState() {
    const typeEl = document.getElementById('fType');
    const minEl = document.getElementById('fMin');
    const maxEl = document.getElementById('fMax');
    const sortEl = document.getElementById('fSort');
    return {
      search: Catalog.getSearchText(),
      type: typeEl ? typeEl.value : '',
      min: minEl ? minEl.value : '',
      max: maxEl ? maxEl.value : '',
      sort: sortEl ? sortEl.value : '-created_at',
    };
  },

  buildApiUrl(page) {
    const f = Catalog.getFilterState();
    let url = '/api/cars/?ordering=' + encodeURIComponent(f.sort) + '&page=' + page;
    if (f.search) url += '&search=' + encodeURIComponent(f.search);
    if (f.type) url += '&car_type=' + encodeURIComponent(f.type);
    if (f.min) url += '&min_price=' + encodeURIComponent(f.min);
    if (f.max) url += '&max_price=' + encodeURIComponent(f.max);
    return url;
  },

  renderActiveFilterChips() {
    const wrap = document.getElementById('activeFilters');
    if (!wrap) return;
    const f = Catalog.getFilterState();
    const chips = [];

    if (f.search) chips.push('Search: ' + f.search);
    if (f.type) chips.push(Catalog.typeLabels[f.type] || f.type);
    if (f.min && f.max) chips.push('$' + f.min + '–$' + f.max + '/day');
    else if (f.min) chips.push('Min $' + f.min + '/day');
    else if (f.max) chips.push('Max $' + f.max + '/day');
    if (f.sort && f.sort !== '-created_at') {
      chips.push(Catalog.sortLabels[f.sort] || f.sort);
    }

    if (!chips.length) {
      wrap.hidden = true;
      wrap.innerHTML = '';
      return;
    }

    wrap.hidden = false;
    wrap.innerHTML =
      '<span class="active-filters__label">Active filters</span>'
      + chips.map(function (c) {
        return '<span class="filter-chip">' + UI.escHtml(c) + '</span>';
      }).join('')
      + '<button type="button" class="filter-chip-clear" id="clearFilterChips">Clear all</button>';

    const clearBtn = document.getElementById('clearFilterChips');
    if (clearBtn) clearBtn.addEventListener('click', Catalog.resetFilters);
  },

  async loadCars(page) {
    if (page === undefined) page = Catalog.page;
    Catalog.page = page;

    const grid = document.getElementById('carsGrid');
    const countEl = document.getElementById('carCount');
    if (!grid) return;

    grid.innerHTML =
      '<div class="loading" style="grid-column:1/-1">'
      + '<span class="spinner spinner-lg"></span> Loading cars...</div>';

    try {
      const data = await API.get(Catalog.buildApiUrl(page));
      const meta = UI.parseListResponse(data, page, UI_PAGE.catalog);

      if (countEl) {
        countEl.innerHTML = UI.resultsSummary({
          total: meta.count,
          label: meta.count === 1 ? 'car' : 'cars',
        });
      }

      Catalog.renderActiveFilterChips();

      if (!meta.items.length) {
        const f = Catalog.getFilterState();
        const hint = f.search || f.type || f.min || f.max
          ? 'Try different search terms or reset filters.'
          : 'Check back later for new listings.';
        grid.innerHTML =
          '<div class="empty" style="grid-column:1/-1">'
          + '<h3>No cars found</h3>'
          + '<p>' + UI.escHtml(hint) + '</p>'
          + '</div>';
        UI.mountPagination('carsPagination', {
          count: 0,
          totalPages: 1,
          page: 1,
          pageSize: UI_PAGE.catalog,
        }, function () {});
        return;
      }

      grid.innerHTML = meta.items.map(function (car) {
        return UI.listingCard(car, { ctaLabel: 'View details' });
      }).join('');

      UI.mountPagination('carsPagination', meta, function (p) {
        Catalog.loadCars(p);
        UI.scrollToEl('carsGrid');
      }, { label: 'cars' });

    } catch (err) {
      grid.innerHTML =
        '<div class="empty" style="grid-column:1/-1">'
        + '<h3>Failed to load cars</h3>'
        + '<p>' + UI.escHtml(err.message) + '</p>'
        + '</div>';
      const pag = document.getElementById('carsPagination');
      if (pag) pag.hidden = true;
    }
  },

  resetFilters() {
    Catalog.setSearchText('');
    const typeEl = document.getElementById('fType');
    const minEl = document.getElementById('fMin');
    const maxEl = document.getElementById('fMax');
    const sortEl = document.getElementById('fSort');
    if (typeEl) typeEl.value = '';
    if (minEl) minEl.value = '';
    if (maxEl) maxEl.value = '';
    if (sortEl) sortEl.value = '-created_at';
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  debouncedSearch() {
    clearTimeout(Catalog.searchTimer);
    Catalog.searchTimer = setTimeout(function () {
      const hero = document.getElementById('heroInput');
      const inline = document.getElementById('fSearch');
      if (hero && inline) inline.value = hero.value.trim();
      Catalog.page = 1;
      Catalog.loadCars(1);
    }, 400);
  },

  onFilterChange() {
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  heroSearch() {
    const hero = document.getElementById('heroInput');
    const inline = document.getElementById('fSearch');
    if (hero && inline) inline.value = hero.value.trim();
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  init() {
    const typeEl = document.getElementById('fType');
    const minEl = document.getElementById('fMin');
    const maxEl = document.getElementById('fMax');
    const sortEl = document.getElementById('fSort');
    const searchEl = document.getElementById('fSearch');
    const hero = document.getElementById('heroInput');
    const resetBtn = document.getElementById('catalogResetBtn');

    if (typeEl) typeEl.addEventListener('change', Catalog.onFilterChange);
    if (minEl) minEl.addEventListener('change', Catalog.onFilterChange);
    if (maxEl) maxEl.addEventListener('change', Catalog.onFilterChange);
    if (sortEl) sortEl.addEventListener('change', Catalog.onFilterChange);
    if (searchEl) searchEl.addEventListener('input', Catalog.debouncedSearch);
    if (resetBtn) resetBtn.addEventListener('click', Catalog.resetFilters);

    if (hero) {
      hero.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          Catalog.heroSearch();
        }
      });
    }

    const heroBtn = document.getElementById('heroSearchBtn');
    if (heroBtn) heroBtn.addEventListener('click', Catalog.heroSearch);

    Catalog.loadCars(1);
  },
};

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('carsGrid')) {
    Catalog.init();
  }
});
