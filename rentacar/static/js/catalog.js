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
      location: typeof LocationState !== 'undefined' && LocationState.getQuery ? LocationState.getQuery() : '',
    };
  },

  buildApiUrl(page) {
    const f = Catalog.getFilterState();
    let url = '/api/cars/?ordering=' + encodeURIComponent(f.sort) + '&page=' + page;
    if (f.search) url += '&search=' + encodeURIComponent(f.search);
    if (f.type) url += '&car_type=' + encodeURIComponent(f.type);
    if (f.min) url += '&min_price=' + encodeURIComponent(f.min);
    if (f.max) url += '&max_price=' + encodeURIComponent(f.max);
    if (f.location) url += '&location=' + encodeURIComponent(f.location);
    return url;
  },

  renderActiveFilterChips() {
    const wrap = document.getElementById('activeFilters');
    if (!wrap) return;
    const f = Catalog.getFilterState();
    const chips = [];

    if (f.search) chips.push('<span class="filter-chip">Search: ' + UI.escHtml(f.search) + '</span>');
    if (f.type) chips.push('<span class="filter-chip">' + UI.escHtml(Catalog.typeLabels[f.type] || f.type) + '</span>');
    if (f.min && f.max) chips.push('<span class="filter-chip">$' + UI.escHtml(f.min) + '–$' + UI.escHtml(f.max) + '/day</span>');
    else if (f.min) chips.push('<span class="filter-chip">Min $' + UI.escHtml(f.min) + '/day</span>');
    else if (f.max) chips.push('<span class="filter-chip">Max $' + UI.escHtml(f.max) + '/day</span>');
    if (f.location) {
      chips.push(
        '<span class="filter-chip filter-chip--location">City: ' + UI.escHtml(f.location)
        + '<button type="button" class="filter-chip-dismiss" id="clearCityFilter" aria-label="Clear city filter">×</button></span>'
      );
    }
    if (f.sort && f.sort !== '-created_at') {
      chips.push('<span class="filter-chip">' + UI.escHtml(Catalog.sortLabels[f.sort] || f.sort) + '</span>');
    }

    if (!chips.length) {
      wrap.hidden = true;
      wrap.innerHTML = '';
      return;
    }

    wrap.hidden = false;
    wrap.innerHTML =
      '<span class="active-filters__label">Active filters</span>'
      + chips.join('')
      + '<button type="button" class="filter-chip-clear" id="clearFilterChips">Reset listing filters</button>';

    const clearBtn = document.getElementById('clearFilterChips');
    if (clearBtn) clearBtn.addEventListener('click', Catalog.resetFilters);
    const clearCityBtn = document.getElementById('clearCityFilter');
    if (clearCityBtn) clearCityBtn.addEventListener('click', Catalog.clearCityFilter);
  },

  async loadCars(page) {
    if (page === undefined) page = Catalog.page;
    Catalog.page = page;

    const grid = document.getElementById('carsGrid');
    const countEl = document.getElementById('carCount');
    if (!grid) return;

    grid.classList.remove('cars-grid--reveal');
    grid.innerHTML = UI.listingSkeletonCards(
      Math.min(UI_PAGE.catalog, 6)
    );

    try {
      const data = await API.get(Catalog.buildApiUrl(page));
      const meta = UI.parseListResponse(data, page, UI_PAGE.catalog);

      if (countEl) {
        countEl.innerHTML = UI.resultsSummary({
          total: meta.count,
          label: meta.count === 1 ? 'car' : 'cars',
        });
        UI.animateResultsCount(countEl);
      }

      Catalog.renderActiveFilterChips();

      if (!meta.items.length) {
        const f = Catalog.getFilterState();
        const hint = f.search || f.type || f.min || f.max || f.location
          ? 'Try another city or adjust the listing filters.'
          : 'Check back later for new listings.';
        const hasFilters = f.search || f.type || f.min || f.max || f.location
          || (f.sort && f.sort !== '-created_at');
        const actions = [];
        if (f.location) {
          actions.push('<button type="button" class="btn btn-outline" id="catalogEmptyCity">Change city</button>');
        }
        if (hasFilters) {
          actions.push('<button type="button" class="btn btn-primary" id="catalogEmptyReset">Reset listing filters</button>');
        }
        grid.innerHTML = '<div class="grid-span-full">'
          + UI.emptyState('No cars found', hint, actions.join(''))
          + '</div>';
        const emptyCity = document.getElementById('catalogEmptyCity');
        if (emptyCity && typeof LocationState !== 'undefined' && LocationState.open) {
          emptyCity.addEventListener('click', function () {
            LocationState.open();
          });
        }
        const emptyReset = document.getElementById('catalogEmptyReset');
        if (emptyReset) emptyReset.addEventListener('click', Catalog.resetFilters);
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

      UI.animateListingGrid(grid);

      UI.mountPagination('carsPagination', meta, function (p) {
        Catalog.loadCars(p);
        UI.scrollToEl('carsGrid');
      }, { label: 'cars' });

    } catch (err) {
      grid.innerHTML = '<div class="grid-span-full">'
        + UI.emptyState('Failed to load cars', err.message,
          '<button type="button" class="btn btn-outline" onclick="Catalog.loadCars(1)">Try again</button>')
        + '</div>';
      const pag = document.getElementById('carsPagination');
      if (pag) pag.hidden = true;
    }
  },

  clearCityFilter() {
    if (typeof LocationState !== 'undefined' && LocationState.clear) {
      LocationState.clear();
    }
    Catalog.page = 1;
    Catalog.loadCars(1);
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

    document.addEventListener('location:changed', function (event) {
      Catalog.page = 1;
      Catalog.loadCars(1);
      if (event.detail && document.getElementById('carsGrid')) {
        UI.scrollToEl('carsGrid');
      }
    });

    Catalog.loadCars(1);
  },
};

window.Catalog = Catalog;

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('carsGrid')) {
    Catalog.init();
  }
});
