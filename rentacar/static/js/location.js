const LocationState = {
  storageKey: 'rentacar.selectedLocation',
  modalId: 'locationModal',
  searchTimer: null,
  popularCities: ['Lahore', 'Karachi', 'Islamabad', 'Peshawar', 'Multan', 'Muzaffarabad', 'Quetta'],
  state: null,

  load() {
    if (this.state !== null) return this.state;
    try {
      this.state = JSON.parse(localStorage.getItem(this.storageKey) || 'null');
    } catch (err) {
      this.state = null;
    }
    return this.state;
  },

  get() {
    return this.load();
  },

  getLabel() {
    const current = this.load();
    return current && current.label ? current.label : '';
  },

  getQuery() {
    const current = this.load();
    return current && current.query ? current.query : this.getLabel();
  },

  isCityActive(cityName, selectedLabel) {
    if (!cityName || !selectedLabel) return false;
    return selectedLabel.trim().toLowerCase() === String(cityName).trim().toLowerCase();
  },

  save(location) {
    this.state = location ? {
      label: location.label || location.query || '',
      query: location.query || location.label || '',
      source: location.source || 'manual',
    } : null;

    if (this.state) {
      localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    } else {
      localStorage.removeItem(this.storageKey);
    }

    this.refreshUI();
    document.dispatchEvent(new CustomEvent('location:changed', { detail: this.state }));
    return this.state;
  },

  clear() {
    this.save(null);
    this.showMessage('City cleared. Showing all available listings.');
    this.renderResults([]);
  },

  normalizeResult(result) {
    if (!result) return null;
    const label = (result.label || result.query || '').trim();
    if (!label) return null;
    return {
      label: label,
      query: result.query || label,
      displayName: result.displayName || result.display_name || '',
      source: result.source || 'map',
    };
  },

  async geocode(query) {
    const res = await API.get(
      '/api/cars/location/search/?q=' + encodeURIComponent(query)
    );
    if (!Array.isArray(res)) return [];
    return res.map((item) => this.normalizeResult(item)).filter(Boolean);
  },

  async reverseGeocode(lat, lon) {
    const res = await API.get(
      '/api/cars/location/reverse/?lat=' + encodeURIComponent(lat)
      + '&lon=' + encodeURIComponent(lon)
    );
    return this.normalizeResult(res);
  },

  renderResults(results) {
    const wrap = document.getElementById('cityResults');
    if (!wrap) return;

    const selected = this.getLabel();
    const cityButtons = this.popularCities.map(function (city) {
      const active = LocationState.isCityActive(city, selected) ? ' is-active' : '';
      return '<button type="button" class="location-result location-result--preset' + active + '" data-location-city="' + UI.escHtml(city) + '">'
        + '<span class="location-result__title">' + UI.escHtml(city) + '</span>'
        + '<span class="location-result__meta">Popular city</span>'
        + '</button>';
    }).join('');

    const cityResults = results.map(function (result) {
      const label = result.label || result.query;
      const meta = result.displayName || 'Suggested city';
      return '<button type="button" class="location-result" data-location-query="' + UI.escHtml(result.query || label) + '">'
        + '<span class="location-result__title">' + UI.escHtml(label) + '</span>'
        + '<span class="location-result__meta">' + UI.escHtml(meta) + '</span>'
        + '</button>';
    }).join('');

    const empty = results.length ? '' : '<div class="location-results__empty text-small">Type a city name or pick one of the popular cities below.</div>';
    wrap.innerHTML = '<div class="location-results__section">'
      + '<div class="location-results__title">Search results</div>'
      + cityResults
      + empty
      + '</div>'
      + '<div class="location-results__section">'
      + '<div class="location-results__title">Popular cities</div>'
      + '<div class="location-results__grid">' + cityButtons + '</div>'
      + '</div>';

    wrap.querySelectorAll('[data-location-query]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const query = btn.getAttribute('data-location-query') || '';
        this.save({
          label: query,
          query: query,
          source: 'search',
        });
        this.close();
        toast('Showing listings for ' + query + '.', 'success');
      });
    });

    wrap.querySelectorAll('[data-location-city]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.selectCity(btn.getAttribute('data-location-city'));
      });
    });
  },

  showMessage(message) {
    const status = document.getElementById('locationStatus');
    if (status) status.textContent = message;
  },

  refreshUI() {
    const current = this.get();
    const label = current && current.label ? current.label : 'Choose city';

    document.querySelectorAll('[data-location-toggle]').forEach((btn) => {
      btn.classList.toggle('location-toggle--active', !!(current && current.label));
      btn.innerHTML = UI.icon('pin', 'icon icon-sm') + '<span class="location-toggle__text">' + UI.escHtml(label) + '</span>';
      btn.setAttribute('aria-label', current && current.label ? 'Change city to ' + current.label : 'Choose your city');
    });

    document.querySelectorAll('[data-location-city]').forEach((card) => {
      const city = card.getAttribute('data-location-city') || '';
      const isActive = this.isCityActive(city, current && current.label ? current.label : '');
      card.classList.toggle('is-active', isActive);
      card.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    const status = document.getElementById('locationStatus');
    if (status) {
      status.textContent = current && current.label
        ? 'Current city: ' + current.label + '. Listings are filtered by city name.'
        : 'No city selected yet. Choose one below or detect your current city.';
    }
  },

  close() {
    const modal = document.getElementById(this.modalId);
    if (modal && modal.closeModal) modal.closeModal();
  },

  async selectCity(query) {
    if (!query) return;
    try {
      this.showMessage('Finding ' + query + '...');
      const results = await this.geocode(query);
      const picked = results.length ? results[0] : { label: query, query: query, source: 'manual' };
      this.save(picked);
      this.close();
      toast('Showing listings for ' + picked.label + '.', 'success');
    } catch (err) {
      toast(err.message || 'Could not select city.', 'error');
      this.showMessage(err.message || 'Could not select city.');
    }
  },

  async detectCity() {
    if (!navigator.geolocation) {
      toast('Geolocation is not supported in this browser.', 'error');
      return;
    }
    this.showMessage('Detecting your city...');
    navigator.geolocation.getCurrentPosition(async (position) => {
      try {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const picked = await this.reverseGeocode(lat, lon);
        if (!picked) {
          throw new Error('Could not detect a city for your location.');
        }
        picked.source = 'geolocation';
        this.save(picked);
        this.close();
        toast('Detected ' + picked.label + '.', 'success');
      } catch (err) {
        toast(err.message || 'Could not detect your city.', 'error');
        this.showMessage(err.message || 'Could not detect your city.');
      }
    }, function () {
      toast('Location permission was denied.', 'error');
    }, {
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: 600000,
    });
  },

  async search(query) {
    const results = query ? await this.geocode(query) : [];
    this.renderResults(results);
  },

  bindEvents() {
    document.querySelectorAll('[data-location-toggle]').forEach((toggleBtn) => {
      if (toggleBtn.dataset.locationBound) return;
      toggleBtn.dataset.locationBound = '1';
      toggleBtn.addEventListener('click', () => {
        this.open();
      });
    });

    document.querySelectorAll('[data-location-city]').forEach((card) => {
      if (card.dataset.locationBound) return;
      card.dataset.locationBound = '1';
      card.addEventListener('click', () => {
        this.selectCity(card.getAttribute('data-location-city'));
      });
    });

    const detectBtn = document.getElementById('detectCityBtn');
    if (detectBtn && !detectBtn.dataset.locationBound) {
      detectBtn.dataset.locationBound = '1';
      detectBtn.addEventListener('click', () => this.detectCity());
    }

    const clearBtn = document.getElementById('clearCityBtn');
    if (clearBtn && !clearBtn.dataset.locationBound) {
      clearBtn.dataset.locationBound = '1';
      clearBtn.addEventListener('click', () => this.clear());
    }

    const searchInput = document.getElementById('citySearchInput');
    if (searchInput && !searchInput.dataset.locationBound) {
      searchInput.dataset.locationBound = '1';
      searchInput.addEventListener('input', () => {
        clearTimeout(this.searchTimer);
        const query = searchInput.value.trim();
        this.searchTimer = setTimeout(() => this.search(query), 350);
      });
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          this.search(searchInput.value.trim());
        }
      });
    }

    document.addEventListener('location:changed', () => {
      this.refreshUI();
    });
  },

  open() {
    const modal = document.getElementById(this.modalId);
    if (!modal) return;
    this.refreshUI();
    this.renderResults([]);
    const searchInput = document.getElementById('citySearchInput');
    if (searchInput) {
      searchInput.value = '';
      setTimeout(() => searchInput.focus(), 0);
    }
    if (modal.openModal) modal.openModal();
    else if (typeof openModal === 'function') openModal(this.modalId);
  },

  init() {
    this.load();
    this.bindEvents();
    this.refreshUI();
    this.renderResults([]);
  },
};

const LocationAutocomplete = {
  timers: {},

  dedupeResults(results) {
    const seen = {};
    const filtered = [];
    (results || []).forEach(function (item) {
      const label = (item.label || item.query || '').trim();
      const key = label.toLowerCase();
      if (!label || seen[key]) return;
      seen[key] = true;
      filtered.push(item);
    });
    return filtered;
  },

  attach(input, options) {
    if (!input || input.dataset.locationAutocompleteInit) return;
    options = options || {};
    input.dataset.locationAutocompleteInit = '1';

    const wrap = input.closest('[data-location-autocomplete-wrap]');
    const panel = options.panel || (wrap ? wrap.querySelector('[data-location-suggestions]') : null);
    if (!panel) return;

    const debounceMs = options.debounceMs || 250;
    const emptyMessage = options.emptyMessage || 'No matching cities found in Pakistan.';

    function closePanel() {
      panel.hidden = true;
      panel.innerHTML = '';
      input.setAttribute('aria-expanded', 'false');
    }

    function chooseSuggestion(item) {
      const value = item.label || item.query || '';
      input.value = value;
      input.dataset.locationSelected = value;
      closePanel();
    }

    function renderSuggestions(items, message) {
      if (!items.length) {
        panel.innerHTML = '<div class="location-suggestions__empty">'
          + UI.escHtml(message || emptyMessage)
          + '</div>';
        panel.hidden = false;
        input.setAttribute('aria-expanded', 'true');
        return;
      }

      panel.innerHTML = items.slice(0, 6).map(function (item) {
        const label = item.label || item.query || '';
        const meta = item.displayName || 'Suggested city';
        return '<button type="button" class="location-suggestion" data-location-choice="1">'
          + '<span class="location-suggestion__title">' + UI.escHtml(label) + '</span>'
          + '<span class="location-suggestion__meta">' + UI.escHtml(meta) + '</span>'
          + '</button>';
      }).join('');

      panel.querySelectorAll('[data-location-choice]').forEach(function (btn, index) {
        btn.addEventListener('mousedown', function (event) {
          event.preventDefault();
          chooseSuggestion(items[index]);
        });
      });

      panel.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    }

    function performSearch(query) {
      if (!query || query.length < 2) {
        closePanel();
        return;
      }
      if (typeof LocationState === 'undefined' || !LocationState.geocode) {
        renderSuggestions([], 'Location search is not available right now.');
        return;
      }

      const currentToken = Date.now();
      input.dataset.locationRequestToken = String(currentToken);

      LocationState.geocode(query).then(function (results) {
        if (input.dataset.locationRequestToken !== String(currentToken)) return;
        renderSuggestions(LocationAutocomplete.dedupeResults(results), emptyMessage);
      }).catch(function () {
        renderSuggestions([], 'Location search is not available right now.');
      });
    }

    input.addEventListener('input', function () {
      input.dataset.locationSelected = '';
      clearTimeout(LocationAutocomplete.timers[input.id]);
      const query = input.value.trim();
      if (query.length < 2) {
        closePanel();
        return;
      }
      LocationAutocomplete.timers[input.id] = setTimeout(function () {
        performSearch(query);
      }, debounceMs);
    });

    input.addEventListener('focus', function () {
      const query = input.value.trim();
      if (query.length >= 2 && panel.hidden) {
        performSearch(query);
      }
    });

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        closePanel();
      }
      if (event.key === 'Enter' && !panel.hidden) {
        event.preventDefault();
        const firstChoice = panel.querySelector('[data-location-choice]');
        if (firstChoice) firstChoice.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      }
    });

    input.addEventListener('blur', function () {
      setTimeout(closePanel, 160);
    });
  },

  validateInput(input, options) {
    options = options || {};
    if (!input) return null;
    const value = input.value.trim();
    const selected = (input.dataset.locationSelected || '').trim();
    if (!value) {
      return options.required ? 'Pickup location is required.' : null;
    }
    if (options.requireSelection && selected.toLowerCase() !== value.toLowerCase()) {
      return 'Select a city from the suggestions list.';
    }
    return null;
  },

  markSelected(input, value) {
    if (!input) return;
    input.value = value || '';
    input.dataset.locationSelected = value || '';
  },
};

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('locationModal')) {
    LocationState.init();
  }
});

window.LocationState = LocationState;
window.LocationAutocomplete = LocationAutocomplete;
