from accounts.models import SocialMediaLink


def social_links(request):
    """
    Inject social_links into every template so the footer can render icons
    without per-view changes.
    """
    try:
        db_links = list(SocialMediaLink.objects.all())
    except Exception:
        db_links = []

    standard_platforms = {
        'Facebook': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-facebook',
            'name': 'Facebook',
        },
        'Instagram': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-instagram',
            'name': 'Instagram',
        },
        'Twitter/X': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-x',
            'name': 'Twitter/X',
        },
        'LinkedIn': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-linkedin',
            'name': 'LinkedIn',
        },
        'YouTube': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-youtube',
            'name': 'YouTube',
        },
    }

    def get_standard_key(name):
        n = (name or '').lower().strip()
        if 'facebook' in n:
            return 'Facebook'
        if 'instagram' in n:
            return 'Instagram'
        if 'twitter' in n or n == 'x' or 'twitter/x' in n:
            return 'Twitter/X'
        if 'linkedin' in n:
            return 'LinkedIn'
        if 'youtube' in n:
            return 'YouTube'
        return None

    custom_links = []
    for link in db_links:
        active = bool(link.url) and link.is_active
        key = get_standard_key(link.platform_name)
        if key:
            standard_platforms[key]['url'] = link.url
            standard_platforms[key]['is_active'] = active
            if link.icon:
                standard_platforms[key]['icon'] = link.icon
        else:
            custom_links.append({
                'url': link.url,
                'is_active': active,
                'icon': link.icon,
                'name': link.platform_name,
            })

    return {'social_links': list(standard_platforms.values()) + custom_links}
