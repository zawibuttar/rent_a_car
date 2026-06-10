(function () {
  function socialPlatformIcon(name) {
    var key = (name || '').toLowerCase().replace(/\s+/g, '');
    if (key.indexOf('facebook') !== -1) return 'facebook';
    if (key.indexOf('instagram') !== -1) return 'instagram';
    if (key.indexOf('twitter') !== -1 || key === 'x') return 'twitter';
    if (key.indexOf('linkedin') !== -1) return 'linkedin';
    if (key.indexOf('youtube') !== -1) return 'youtube';
    if (key.indexOf('tiktok') !== -1) return 'tiktok';
    return 'share';
  }

  async function loadFooterSocialLinks() {
    var container = document.getElementById('footerSocial');
    if (!container || typeof API === 'undefined') return;

    try {
      var data = await API.get('/api/accounts/social-media/');
      var links = Array.isArray(data) ? data : (data.results || []);
      if (!links.length) {
        container.innerHTML = '';
        return;
      }

      container.innerHTML = links.map(function (link) {
        var icon = socialPlatformIcon(link.platform_name);
        var label = (typeof UI !== 'undefined' && UI.escHtml)
          ? UI.escHtml(link.platform_name)
          : link.platform_name;
        var url = (typeof UI !== 'undefined' && UI.escHtml)
          ? UI.escHtml(link.url)
          : link.url;
        return '<a class="footer-social-link" href="' + url + '" target="_blank" rel="noopener noreferrer"'
          + ' aria-label="' + label + '">'
          + '<svg class="icon" aria-hidden="true"><use href="#icon-' + icon + '"/></svg>'
          + '</a>';
      }).join('');
    } catch (_) {
      container.innerHTML = '';
    }
  }

  document.addEventListener('DOMContentLoaded', loadFooterSocialLinks);
})();
