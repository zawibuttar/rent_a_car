/**
 * Shared catalog browse logic for home and /cars/ pages.
 * Default category: 'car'. Three tabs: Car | Luxury Car | Loader.
 */
const Catalog = {
  page: 1,
  searchTimer: null,
  /* Default category — always a category is active, never empty. */
  DEFAULT_CATEGORY: 'car',

  sortLabels: {
    '-created_at': 'Newest first',
    price_per_day: 'Price: low to high',
    '-price_per_day': 'Price: high to low',
    '-year': 'Newest year',
    year: 'Oldest year',
  },
  typeLabels: {
    // Car types
    hatchback: 'Hatchback',
    sedan: 'Sedan',
    suv: 'SUV',
    muv_mpv: 'MUV/MPV',
    crossover: 'Crossover',
    convertible: 'Convertible',
    coupe: 'Coupe',
    pickup_truck: 'Pickup Truck',
    // Luxury Car types
    luxury_sedan: 'Luxury Sedan',
    luxury_suv: 'Luxury SUV',
    sports_car: 'Sports Car',
    luxury_convertible: 'Luxury Convertible',
    luxury_coupe: 'Luxury Coupe',
    limousine: 'Limousine',
    electric_luxury: 'Electric Luxury',
    luxury_crossover: 'Luxury Crossover',
    // Loader types
    mini_truck: 'Mini Truck',
    pickup_loader: 'Pickup Loader',
    container_truck: 'Container Truck',
    tipper_dumper: 'Tipper/Dumper',
    flatbed_truck: 'Flatbed Truck',
    refrigerated_truck: 'Refrigerated Truck',
    tanker_truck: 'Tanker Truck',
    crane_truck: 'Crane Truck',
  },
  catLabels: {
    car: 'Cars',
    luxury_car: 'Luxury Cars',
    loader: 'Loaders',
  },

  CATEGORY_TYPES: {
    car: [
      { value: 'hatchback', label: 'Hatchback' },
      { value: 'sedan', label: 'Sedan' },
      { value: 'suv', label: 'SUV' },
      { value: 'muv_mpv', label: 'MUV/MPV' },
      { value: 'crossover', label: 'Crossover' },
      { value: 'convertible', label: 'Convertible' },
      { value: 'coupe', label: 'Coupe' },
      { value: 'pickup_truck', label: 'Pickup Truck' },
    ],
    luxury_car: [
      { value: 'luxury_sedan', label: 'Luxury Sedan' },
      { value: 'luxury_suv', label: 'Luxury SUV' },
      { value: 'sports_car', label: 'Sports Car' },
      { value: 'luxury_convertible', label: 'Luxury Convertible' },
      { value: 'luxury_coupe', label: 'Luxury Coupe' },
      { value: 'limousine', label: 'Limousine' },
      { value: 'electric_luxury', label: 'Electric Luxury' },
      { value: 'luxury_crossover', label: 'Luxury Crossover' },
    ],
    loader: [
      { value: 'mini_truck', label: 'Mini Truck' },
      { value: 'pickup_loader', label: 'Pickup Loader' },
      { value: 'container_truck', label: 'Container Truck' },
      { value: 'tipper_dumper', label: 'Tipper/Dumper' },
      { value: 'flatbed_truck', label: 'Flatbed Truck' },
      { value: 'refrigerated_truck', label: 'Refrigerated Truck' },
      { value: 'tanker_truck', label: 'Tanker Truck' },
      { value: 'crane_truck', label: 'Crane Truck' },
    ],
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

  getCategory() {
    const el = document.getElementById('fCategory');
    return el ? el.value : Catalog.DEFAULT_CATEGORY;
  },

  getType() {
    const el = document.getElementById('fType');
    return el ? el.value : '';
  },

  setCategory(value) {
    Catalog.setCategoryAndType(value || Catalog.DEFAULT_CATEGORY, '');
  },

  populateTypeDropdown(category) {
    const typeEl = document.getElementById('fType');
    if (!typeEl) return;
    
    // Clear options except first
    typeEl.innerHTML = '<option value="">Select Type</option>';
    
    const types = Catalog.CATEGORY_TYPES[category] || [];
    types.forEach(function (t) {
      const opt = document.createElement('option');
      opt.value = t.value;
      opt.textContent = t.label;
      typeEl.appendChild(opt);
    });
    
    const fTypeField = document.getElementById('fTypeField');
    if (fTypeField) {
      fTypeField.style.display = '';
    }
  },

  setCategoryAndType(category, type) {
    if (!category) category = Catalog.DEFAULT_CATEGORY;
    const catEl = document.getElementById('fCategory');
    if (catEl) catEl.value = category;

    Catalog.populateTypeDropdown(category);

    const typeEl = document.getElementById('fType');
    if (typeEl) typeEl.value = type || '';
  },

  getFilterState() {
    const typeEl = document.getElementById('fType');
    const minEl  = document.getElementById('fMin');
    const maxEl  = document.getElementById('fMax');
    const sortEl = document.getElementById('fSort');

    const sidebarType = Catalog.getType();
    const type = sidebarType || (typeEl ? typeEl.value : '');

    return {
      search  : Catalog.getSearchText(),
      type    : type,
      min     : minEl ? minEl.value : '',
      max     : maxEl ? maxEl.value : '',
      sort    : sortEl ? sortEl.value : '-created_at',
      location: typeof LocationState !== 'undefined' && LocationState.getQuery ? LocationState.getQuery() : '',
      category: Catalog.getCategory(),
    };
  },

  buildApiUrl(page) {
    const f = Catalog.getFilterState();
    let url = '/api/cars/?ordering=' + encodeURIComponent(f.sort) + '&page=' + page;
    if (f.search)   url += '&search='   + encodeURIComponent(f.search);
    if (f.type)     url += '&car_type=' + encodeURIComponent(f.type);
    if (f.min)      url += '&min_price=' + encodeURIComponent(f.min);
    if (f.max)      url += '&max_price=' + encodeURIComponent(f.max);
    if (f.location) url += '&location=' + encodeURIComponent(f.location);
    // category is always present — always filter
    url += '&category=' + encodeURIComponent(f.category);
    return url;
  },

  renderActiveFilterChips() {
    const wrap = document.getElementById('activeFilters');
    if (!wrap) return;
    const f = Catalog.getFilterState();
    const chips = [];

    if (f.search) chips.push('<span class="filter-chip">Search: ' + UI.escHtml(f.search) + '</span>');

    // Category chip — always shown (it's always active), but no dismiss button
    // since the user must always have one category selected.
    chips.push(
      '<span class="filter-chip filter-chip--category">'
      + UI.escHtml(Catalog.catLabels[f.category] || f.category)
      + '</span>'
    );

    if (f.type) chips.push('<span class="filter-chip">' + UI.escHtml(Catalog.typeLabels[f.type] || f.type) + '</span>');
    if (f.min && f.max) chips.push('<span class="filter-chip">$' + UI.escHtml(f.min) + '–$' + UI.escHtml(f.max) + '/day</span>');
    else if (f.min)     chips.push('<span class="filter-chip">Min $' + UI.escHtml(f.min) + '/day</span>');
    else if (f.max)     chips.push('<span class="filter-chip">Max $' + UI.escHtml(f.max) + '/day</span>');
    if (f.location) {
      chips.push(
        '<span class="filter-chip filter-chip--location">City: ' + UI.escHtml(f.location)
        + '<button type="button" class="filter-chip-dismiss" id="clearCityFilter" aria-label="Clear city filter">×</button></span>'
      );
    }
    if (f.sort && f.sort !== '-created_at') {
      chips.push('<span class="filter-chip">' + UI.escHtml(Catalog.sortLabels[f.sort] || f.sort) + '</span>');
    }

    // Determine if any *secondary* filters are active (beyond just the mandatory category)
    const hasSecondaryFilters = f.search || f.type || f.min || f.max || f.location
      || (f.sort && f.sort !== '-created_at');

    if (!hasSecondaryFilters) {
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

    const grid    = document.getElementById('carsGrid');
    const countEl = document.getElementById('carCount');
    if (!grid) return;

    grid.classList.remove('cars-grid--reveal');
    grid.innerHTML = UI.listingSkeletonCards(Math.min(UI_PAGE.catalog, 6));

    try {
      const data = await API.get(Catalog.buildApiUrl(page));
      const meta = UI.parseListResponse(data, page, UI_PAGE.catalog);

      if (countEl) {
        countEl.innerHTML = UI.resultsSummary({
          total: meta.count,
          label: meta.count === 1 ? 'vehicle' : 'vehicles',
        });
        UI.animateResultsCount(countEl);
      }

      Catalog.renderActiveFilterChips();

      if (!meta.items.length) {
        const f = Catalog.getFilterState();
        const hint = f.search || f.type || f.min || f.max || f.location
          ? 'Try adjusting the listing filters.'
          : 'No ' + (Catalog.catLabels[f.category] || 'vehicles') + ' available yet. Check back soon.';
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
          + UI.emptyState('No vehicles found', hint, actions.join(''))
          + '</div>';
        const emptyCity = document.getElementById('catalogEmptyCity');
        if (emptyCity && typeof LocationState !== 'undefined' && LocationState.open) {
          emptyCity.addEventListener('click', function () { LocationState.open(); });
        }
        const emptyReset = document.getElementById('catalogEmptyReset');
        if (emptyReset) emptyReset.addEventListener('click', Catalog.resetFilters);
        UI.mountPagination('carsPagination', {
          count: 0, totalPages: 1, page: 1, pageSize: UI_PAGE.catalog,
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
      }, { label: 'vehicles' });

    } catch (err) {
      grid.innerHTML = '<div class="grid-span-full">'
        + UI.emptyState('Failed to load vehicles', err.message,
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

  /* Category cannot be fully cleared — reset to default instead */
  clearCategoryFilter() {
    Catalog.setCategoryAndType(Catalog.DEFAULT_CATEGORY, '');
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  resetFilters() {
    Catalog.setSearchText('');
    // Reset to default category, not empty
    Catalog.setCategoryAndType(Catalog.DEFAULT_CATEGORY, '');
    const typeEl = document.getElementById('fType');
    const minEl  = document.getElementById('fMin');
    const maxEl  = document.getElementById('fMax');
    const sortEl = document.getElementById('fSort');
    if (typeEl) typeEl.value = '';
    if (minEl)  minEl.value  = '';
    if (maxEl)  maxEl.value  = '';
    if (sortEl) sortEl.value = '-created_at';
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  debouncedSearch() {
    clearTimeout(Catalog.searchTimer);
    Catalog.searchTimer = setTimeout(function () {
      const hero   = document.getElementById('heroInput');
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

  onTypeChange() {
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  heroSearch() {
    const hero   = document.getElementById('heroInput');
    const inline = document.getElementById('fSearch');
    if (hero && inline) inline.value = hero.value.trim();
    Catalog.page = 1;
    Catalog.loadCars(1);
  },

  init() {
    const typeEl   = document.getElementById('fType');
    const minEl    = document.getElementById('fMin');
    const maxEl    = document.getElementById('fMax');
    const sortEl   = document.getElementById('fSort');
    const searchEl = document.getElementById('fSearch');
    const hero     = document.getElementById('heroInput');
    const resetBtn = document.getElementById('catalogResetBtn');

    if (typeEl)   typeEl.addEventListener('change', Catalog.onTypeChange);
    if (minEl)    minEl.addEventListener('change', Catalog.onFilterChange);
    if (maxEl)    maxEl.addEventListener('change', Catalog.onFilterChange);
    if (sortEl)   sortEl.addEventListener('change', Catalog.onFilterChange);
    if (searchEl) searchEl.addEventListener('input', Catalog.debouncedSearch);
    if (resetBtn) resetBtn.addEventListener('click', Catalog.resetFilters);

    const catEl = document.getElementById('fCategory');
    if (catEl) {
      catEl.addEventListener('change', function () {
        Catalog.setCategoryAndType(catEl.value, '');
        Catalog.onFilterChange();
      });
    }

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

    // Initialise category from URL params — fall back to default if absent or unknown
    const urlParams       = new URLSearchParams(window.location.search);
    const initialCategory = urlParams.get('category') || '';
    const initialType     = urlParams.get('car_type') || urlParams.get('type') || '';
    const validCategories = ['car', 'luxury_car', 'loader'];

    if (initialCategory && validCategories.indexOf(initialCategory) !== -1) {
      Catalog.setCategoryAndType(initialCategory, initialType);
      if (typeEl && initialType) typeEl.value = initialType;
    } else {
      // Ensure the HTML default (Car) is respected; no URL param → Car active
      Catalog.setCategoryAndType(Catalog.DEFAULT_CATEGORY, '');
    }

    Catalog.loadCars(1);
  },
};

window.Catalog = Catalog;

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('carsGrid')) {
    Catalog.init();
  }
});
