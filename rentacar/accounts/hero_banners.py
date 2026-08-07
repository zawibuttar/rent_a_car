import random

from django.templatetags.static import static

from .models import HeroBanner


def get_random_hero_banner_url(request=None):
    banners = list(
        HeroBanner.objects.filter(is_active=True).exclude(image='').only('image')
    )
    if not banners:
        return None
    banner = random.choice(banners)
    url = banner.image.url
    if request is not None:
        return request.build_absolute_uri(url)
    return url


def get_hero_banner_fallback_url():
    return static('images/hero-bg.jpg')
