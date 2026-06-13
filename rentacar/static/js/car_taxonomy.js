/**
 * Vehicle taxonomy — single source from GET /api/cars/taxonomy/
 * Covers vehicle category, vehicle type, and rental duration labels.
 */
const CarTaxonomy = {
  loaded: false,
  loading: null,
  data: null,

  load() {
    if (CarTaxonomy.loaded) {
      return Promise.resolve(CarTaxonomy.data);
    }
    if (CarTaxonomy.loading) {
      return CarTaxonomy.loading;
    }
    CarTaxonomy.loading = fetch('/api/cars/taxonomy/')
      .then(function (res) {
        if (!res.ok) throw new Error('Failed to load taxonomy');
        return res.json();
      })
      .then(function (data) {
        CarTaxonomy.data = data;
        CarTaxonomy.loaded = true;
        CarTaxonomy.loading = null;
        return data;
      })
      .catch(function (err) {
        CarTaxonomy.loading = null;
        throw err;
      });
    return CarTaxonomy.loading;
  },

  getDefaultCategory() {
    return (CarTaxonomy.data && CarTaxonomy.data.default_category) || 'car';
  },

  getCategories() {
    return (CarTaxonomy.data && CarTaxonomy.data.categories) || [];
  },

  getRentalDurations() {
    return (CarTaxonomy.data && CarTaxonomy.data.rental_durations) || [];
  },

  getCategoryLabel(value) {
    if (!value) return '';
    var cats = CarTaxonomy.getCategories();
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].value === value) return cats[i].label;
    }
    return value;
  },

  getTypeLabel(value) {
    if (!value) return '';
    var cats = CarTaxonomy.getCategories();
    for (var c = 0; c < cats.length; c++) {
      var types = cats[c].types || [];
      for (var t = 0; t < types.length; t++) {
        if (types[t].value === value) return types[t].label;
      }
    }
    return value;
  },

  getRentalDurationLabel(value) {
    if (!value) return '';
    var durations = CarTaxonomy.getRentalDurations();
    for (var i = 0; i < durations.length; i++) {
      if (durations[i].value === value) return durations[i].label;
    }
    return value;
  },

  getTypesForCategory(category) {
    var cats = CarTaxonomy.getCategories();
    for (var i = 0; i < cats.length; i++) {
      if (cats[i].value === category) return cats[i].types || [];
    }
    return [];
  },

  populateCategorySelect(selectEl, selectedValue, includeEmpty) {
    if (!selectEl) return;
    var current = selectedValue != null ? selectedValue : selectEl.value;
    selectEl.innerHTML = '';
    if (includeEmpty) {
      var empty = document.createElement('option');
      empty.value = '';
      empty.textContent = 'All categories';
      selectEl.appendChild(empty);
    }
    CarTaxonomy.getCategories().forEach(function (cat) {
      var opt = document.createElement('option');
      opt.value = cat.value;
      opt.textContent = cat.label;
      if (cat.description) opt.title = cat.description;
      selectEl.appendChild(opt);
    });
    if (current) selectEl.value = current;
  },

  populateTypeSelect(selectEl, category, selectedValue, includeEmpty) {
    if (!selectEl) return;
    var current = selectedValue != null ? selectedValue : selectEl.value;
    selectEl.innerHTML = '';
    if (includeEmpty) {
      var empty = document.createElement('option');
      empty.value = '';
      empty.textContent = 'Select Type';
      selectEl.appendChild(empty);
    }
    CarTaxonomy.getTypesForCategory(category).forEach(function (t) {
      var opt = document.createElement('option');
      opt.value = t.value;
      opt.textContent = t.label;
      selectEl.appendChild(opt);
    });
    if (current) selectEl.value = current;
  },
};

window.CarTaxonomy = CarTaxonomy;
