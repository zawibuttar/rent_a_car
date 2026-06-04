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

  save(location) {
    this.state = location ? {
      label: location.label || location.query || '',
      query: location.query || location.label || '',
      lat: location.lat != null ? Number(location.lat) : null,
      lon: location.lon != null ? Number(location.lon) : null,
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
    const address = result.address || {};
    const city = address.city || address.town || address.village || address.municipality || address.county || address.state || result.display_name || '';
    const label = city ? String(city).trim() : String(result.display_name || '').split(',')[0].trim();
    const lat = result.lat != null ? parseFloat(result.lat) : null;
    const lon = result.lon != null ? parseFloat(result.lon) : null;
    if (!label) return null;
    return {
      label: label,
      query: label,
      displayName: result.display_name || '',
      lat: isNaN(lat) ? null : lat,
      lon: isNaN(lon) ? null : lon,
      source: 'map',
    };
  },

  async geocode(query) {
    const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=8&countrycodes=pk&q=' + encodeURIComponent(query);
    const res = await fetch(url, {
      headers: { 'Accept-Language': 'en' },
    });
    if (!res.ok) {
      throw new Error('City lookup failed.');
    }
    const data = await res.json();
    return Array.isArray(data) ? data.map((item) => this.normalizeResult(item)).filter(Boolean) : [];
  },

  async reverseGeocode(lat, lon) {
    const url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&addressdetails=1&lat=' + encodeURIComponent(lat) + '&lon=' + encodeURIComponent(lon);
    const res = await fetch(url, {
      headers: { 'Accept-Language': 'en' },
    });
    if (!res.ok) {
      throw new Error('Could not detect your city.');
    }
    const data = await res.json();
    return this.normalizeResult(data);
  },

  renderResults(results) {
    const wrap = document.getElementById('cityResults');
    if (!wrap) return;

    const selected = this.getLabel().toLowerCase();
    const cityButtons = this.popularCities.map(function (city) {
      const active = selected && selected.indexOf(city.toLowerCase()) >= 0 ? ' is-active' : '';
      return '<button type="button" class="location-result location-result--preset' + active + '" data-location-city="' + UI.escHtml(city) + '">'
        + '<span class="location-result__title">' + UI.escHtml(city) + '</span>'
        + '<span class="location-result__meta">Popular city</span>'
        + '</button>';
    }).join('');

    const cityResults = results.map(function (result) {
      const label = result.label || result.query;
      const meta = result.display_name || 'OpenStreetMap result';
      return '<button type="button" class="location-result" data-location-query="' + UI.escHtml(result.query || label) + '"'
        + (result.lat != null ? ' data-location-lat="' + UI.escHtml(result.lat) + '"' : '')
        + (result.lon != null ? ' data-location-lon="' + UI.escHtml(result.lon) + '"' : '')
        + '>'
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
        const lat = btn.getAttribute('data-location-lat');
        const lon = btn.getAttribute('data-location-lon');
        this.save({
          label: query,
          query: query,
          lat: lat ? parseFloat(lat) : null,
          lon: lon ? parseFloat(lon) : null,
          source: 'search',
        });
        if (lat && lon) this.centerMap(parseFloat(lat), parseFloat(lon), 11);
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
      const active = current && current.label ? ' location-toggle--active' : '';
      btn.classList.toggle('location-toggle--active', !!(current && current.label));
      btn.innerHTML = UI.icon('pin', 'icon icon-sm') + '<span class="location-toggle__text">' + UI.escHtml(label) + '</span>';
      btn.setAttribute('aria-label', current && current.label ? 'Change city to ' + current.label : 'Choose your city');
    });

    document.querySelectorAll('[data-location-city]').forEach((card) => {
      const city = (card.getAttribute('data-location-city') || '').toLowerCase();
      const isActive = current && current.label && current.label.toLowerCase().indexOf(city) >= 0;
      card.classList.toggle('is-active', !!isActive);
      card.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });

    const status = document.getElementById('locationStatus');
    if (status) {
      status.textContent = current && current.label
        ? 'Current city: ' + current.label + '. Listings are filtered automatically.'
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
        picked.lat = lat;
        picked.lon = lon;
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
    const current = this.get();
    if (current && current.lat != null && current.lon != null) {
      this.centerMap(current.lat, current.lon, 11);
    }
  },

  bindEvents() {
    const toggleBtn = document.querySelector('[data-location-toggle]');
    if (toggleBtn && !toggleBtn.dataset.locationBound) {
      toggleBtn.dataset.locationBound = '1';
      toggleBtn.addEventListener('click', () => {
        this.open();
      });
    }

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

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('locationModal')) {
    LocationState.init();
  }
});

window.LocationState = LocationState;
