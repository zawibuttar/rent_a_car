from accounts.models import SocialMediaLink


def social_links(request):
    """
    Injects social_links into every template context so the footer
    can display active/inactive icons without any view changes.
    """
    try:
        db_links = list(SocialMediaLink.objects.all())
    except Exception:
        # Gracefully handle DB unavailability (e.g. before first migration)
        db_links = []

    # Standard platforms we want to guarantee are in the footer
    standard_platforms = {
        'Facebook': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-facebook',
            'name': 'Facebook'
        },
        'Instagram': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-instagram',
            'name': 'Instagram'
        },
        'Twitter/X': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-x',
            'name': 'Twitter/X'
        },
        'LinkedIn': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-linkedin',
            'name': 'LinkedIn'
        },
        'YouTube': {
            'url': '',
            'is_active': False,
            'icon': 'ti ti-brand-youtube',
            'name': 'YouTube'
        }
    }

    # Helper to map platform names to standard platform keys
    def get_standard_key(name):
        n = name.lower().strip()
        if 'facebook' in n: return 'Facebook'
        if 'instagram' in n: return 'Instagram'
        if 'twitter' in n or n == 'x' or 'twitter/x' in n: return 'Twitter/X'
        if 'linkedin' in n: return 'LinkedIn'
        if 'youtube' in n: return 'YouTube'
        return None

    # Track which db links map to standard ones, and keep custom ones separate
    custom_links = []
    
    for link in db_links:
        key = get_standard_key(link.platform_name)
        if key:
            standard_platforms[key]['url'] = link.url
            standard_platforms[key]['is_active'] = link.is_active
            # Keep standard icon class unless empty
            if link.icon:
                standard_platforms[key]['icon'] = link.icon
        else:
            custom_links.append({
                'url': link.url,
                'is_active': link.is_active,
                'icon': link.icon,
                'name': link.platform_name
            })

    # Combine: standard first (always shown), then custom ones
    combined = list(standard_platforms.values()) + custom_links
    return {'social_links': combined}

