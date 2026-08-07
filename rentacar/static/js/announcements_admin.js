/**
 * Admin announcements management.
 */
const AnnouncementsAdmin = {
  items: [],
  editingId: null,
  removeImage: false,
  pendingPreviewUrl: null,

  audienceLabel(value) {
    var map = { all: 'All users', customers: 'Customers', owners: 'Owners' };
    return map[value] || value;
  },

  async fetchList() {
    var res = await API.get('/api/announcements/admin/');
    AnnouncementsAdmin.items = res.data || [];
    return AnnouncementsAdmin.items;
  },

  renderTable() {
    var tbody = document.getElementById('annAdminTable');
    if (!tbody) return;
    if (!AnnouncementsAdmin.items.length) {
      tbody.innerHTML = '<tr><td colspan="7">'
        + UI.emptyState('No announcements yet', 'Create one to broadcast updates to customers and owners.')
        + '</td></tr>';
      return;
    }
    tbody.innerHTML = AnnouncementsAdmin.items.map(function (a, i) {
      var status = a.is_active && !a.is_expired
        ? '<span class="badge badge-green">Active</span>'
        : '<span class="badge badge-gray">Inactive</span>';
      var expires = a.expires_at
        ? new Date(a.expires_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
        : '—';
      return '<tr>'
        + '<td>' + (i + 1) + '</td>'
        + '<td><strong>' + UI.escHtml(a.title) + '</strong></td>'
        + '<td>' + UI.escHtml(AnnouncementsAdmin.audienceLabel(a.audience)) + '</td>'
        + '<td>' + status + '</td>'
        + '<td class="td-meta">' + UI.escHtml(new Date(a.published_at).toLocaleDateString()) + '</td>'
        + '<td class="td-meta col-hide-sm">' + UI.escHtml(expires) + '</td>'
        + '<td><div class="table-actions">'
        + '<button type="button" class="btn btn-ghost btn-sm" onclick="AnnouncementsAdmin.startEdit(' + a.id + ')">Edit</button>'
        + '<button type="button" class="btn btn-danger btn-sm" onclick="AnnouncementsAdmin.remove(' + a.id + ')">Delete</button>'
        + '</div></td>'
        + '</tr>';
    }).join('');
  },

  showForm(show) {
    var form = document.getElementById('annAdminForm');
    if (form) form.hidden = !show;
  },

  resetExpiresFields() {
    var dateEl = document.getElementById('annExpiresDate');
    var timeEl = document.getElementById('annExpiresTime');
    if (dateEl) {
      dateEl.value = '';
      dateEl.min = UI.todayLocalDateValue();
    }
    if (timeEl) timeEl.value = '';
  },

  setExpiresFields(isoValue) {
    var dateEl = document.getElementById('annExpiresDate');
    var timeEl = document.getElementById('annExpiresTime');
    if (!dateEl || !timeEl) return;
    if (!isoValue) {
      AnnouncementsAdmin.resetExpiresFields();
      return;
    }
    var d = new Date(isoValue);
    dateEl.min = '';
    dateEl.value = UI.localDateInputValue(d);
    timeEl.value = UI.localTimeInputValue(d);
  },

  getExpiresValue() {
    var dateEl = document.getElementById('annExpiresDate');
    var timeEl = document.getElementById('annExpiresTime');
    if (!dateEl || !dateEl.value) return null;
    return UI.isoFromLocalDateTime(dateEl.value, timeEl ? timeEl.value : '', '23:59');
  },

  resetImageField() {
    AnnouncementsAdmin.removeImage = false;
    var input = document.getElementById('annImage');
    if (input) input.value = '';
    if (AnnouncementsAdmin.pendingPreviewUrl) {
      URL.revokeObjectURL(AnnouncementsAdmin.pendingPreviewUrl);
      AnnouncementsAdmin.pendingPreviewUrl = null;
    }
    AnnouncementsAdmin.setImagePreview('');
  },

  setImagePreview(url) {
    var wrap = document.getElementById('annImagePreview');
    var img = document.getElementById('annImagePreviewImg');
    if (!wrap || !img) return;
    if (url) {
      img.src = url;
      wrap.hidden = false;
    } else {
      img.removeAttribute('src');
      wrap.hidden = true;
    }
  },

  onImageSelected() {
    var input = document.getElementById('annImage');
    if (!input || !input.files || !input.files[0]) return;
    AnnouncementsAdmin.removeImage = false;
    if (AnnouncementsAdmin.pendingPreviewUrl) {
      URL.revokeObjectURL(AnnouncementsAdmin.pendingPreviewUrl);
    }
    AnnouncementsAdmin.pendingPreviewUrl = URL.createObjectURL(input.files[0]);
    AnnouncementsAdmin.setImagePreview(AnnouncementsAdmin.pendingPreviewUrl);
  },

  markImageForRemoval() {
    AnnouncementsAdmin.removeImage = true;
    var input = document.getElementById('annImage');
    if (input) input.value = '';
    if (AnnouncementsAdmin.pendingPreviewUrl) {
      URL.revokeObjectURL(AnnouncementsAdmin.pendingPreviewUrl);
      AnnouncementsAdmin.pendingPreviewUrl = null;
    }
    AnnouncementsAdmin.setImagePreview('');
  },

  buildFormData() {
    var title = document.getElementById('annTitle').value.trim();
    var body = document.getElementById('annBody').value.trim();
    var audience = document.getElementById('annAudience').value;
    var isActive = document.getElementById('annActive').checked;
    var expiresAt = AnnouncementsAdmin.getExpiresValue();
    var fd = new FormData();
    fd.append('title', title);
    fd.append('body', body);
    fd.append('audience', audience);
    fd.append('is_active', isActive ? 'true' : 'false');
    if (expiresAt) fd.append('expires_at', expiresAt);
    var imageInput = document.getElementById('annImage');
    if (imageInput && imageInput.files && imageInput.files[0]) {
      fd.append('image', imageInput.files[0]);
    }
    if (AnnouncementsAdmin.removeImage) {
      fd.append('remove_image', 'true');
    }
    return fd;
  },

  resetForm() {
    AnnouncementsAdmin.editingId = null;
    document.getElementById('annTitle').value = '';
    document.getElementById('annBody').value = '';
    document.getElementById('annAudience').value = 'all';
    document.getElementById('annActive').checked = true;
    AnnouncementsAdmin.resetExpiresFields();
    AnnouncementsAdmin.resetImageField();
    var label = document.getElementById('annFormTitle');
    if (label) label.textContent = 'New announcement';
  },

  startCreate() {
    AnnouncementsAdmin.resetForm();
    AnnouncementsAdmin.showForm(true);
    document.getElementById('annTitle').focus();
  },

  startEdit(id) {
    var item = AnnouncementsAdmin.items.find(function (a) { return a.id === id; });
    if (!item) return;
    AnnouncementsAdmin.editingId = id;
    document.getElementById('annTitle').value = item.title;
    document.getElementById('annBody').value = item.body;
    document.getElementById('annAudience').value = item.audience;
    document.getElementById('annActive').checked = !!item.is_active;
    AnnouncementsAdmin.setExpiresFields(item.expires_at || '');
    AnnouncementsAdmin.removeImage = false;
    var imageInput = document.getElementById('annImage');
    if (imageInput) imageInput.value = '';
    if (AnnouncementsAdmin.pendingPreviewUrl) {
      URL.revokeObjectURL(AnnouncementsAdmin.pendingPreviewUrl);
      AnnouncementsAdmin.pendingPreviewUrl = null;
    }
    AnnouncementsAdmin.setImagePreview(item.image_url || '');
    var label = document.getElementById('annFormTitle');
    if (label) label.textContent = 'Edit announcement';
    AnnouncementsAdmin.showForm(true);
  },

  cancelForm() {
    AnnouncementsAdmin.showForm(false);
    AnnouncementsAdmin.resetForm();
  },

  async save() {
    var title = document.getElementById('annTitle').value.trim();
    var body = document.getElementById('annBody').value.trim();
    if (!title || !body) {
      toast('Title and body are required.', 'error');
      return;
    }
    var fd = AnnouncementsAdmin.buildFormData();
    var btn = document.getElementById('annSaveBtn');
    if (btn) btn.disabled = true;
    try {
      if (AnnouncementsAdmin.editingId) {
        await API.uploadPatch('/api/announcements/admin/' + AnnouncementsAdmin.editingId + '/', fd);
        toast('Announcement updated.', 'success');
      } else {
        await API.upload('/api/announcements/admin/', fd);
        toast('Announcement published.', 'success');
      }
      AnnouncementsAdmin.cancelForm();
      await AnnouncementsAdmin.load();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async remove(id) {
    if (!confirm('Delete this announcement?')) return;
    try {
      await API.del('/api/announcements/admin/' + id + '/');
      toast('Announcement deleted.', 'success');
      await AnnouncementsAdmin.load();
    } catch (err) {
      toast(err.message, 'error');
    }
  },

  async load() {
    var tbody = document.getElementById('annAdminTable');
    if (tbody) tbody.innerHTML = '<tr><td colspan="7"><div class="loading"><span class="spinner"></span></div></td></tr>';
    try {
      await AnnouncementsAdmin.fetchList();
      AnnouncementsAdmin.renderTable();
    } catch (err) {
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7">' + UI.escHtml(err.message) + '</td></tr>';
      }
      toast(err.message, 'error');
    }
  },

  mount() {
    AnnouncementsAdmin.resetExpiresFields();
    var saveBtn = document.getElementById('annSaveBtn');
    if (saveBtn) saveBtn.addEventListener('click', AnnouncementsAdmin.save);
    var cancelBtn = document.getElementById('annCancelBtn');
    if (cancelBtn) cancelBtn.addEventListener('click', AnnouncementsAdmin.cancelForm);
    var createBtn = document.getElementById('annCreateBtn');
    if (createBtn) createBtn.addEventListener('click', AnnouncementsAdmin.startCreate);
    var imageInput = document.getElementById('annImage');
    if (imageInput) imageInput.addEventListener('change', AnnouncementsAdmin.onImageSelected);
    var imageRemoveBtn = document.getElementById('annImageRemoveBtn');
    if (imageRemoveBtn) imageRemoveBtn.addEventListener('click', AnnouncementsAdmin.markImageForRemoval);
  },
};

window.AnnouncementsAdmin = AnnouncementsAdmin;
