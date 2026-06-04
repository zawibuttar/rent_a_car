"""
API caching utilities: HTTP cache headers, Redis response cache, and invalidation.
"""

import hashlib
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from rest_framework.response import Response

# Fixed keys for admin list endpoints
ADMIN_CARS_KEY = 'list:admin:cars'
ADMIN_BOOKINGS_KEY = 'list:admin:bookings'
ADMIN_OWNERS_KEY = 'list:admin:owners'
PUBLIC_CAR_LIST_VERSION_KEY = 'version:public:car_list'


def admin_cars_key():
    return ADMIN_CARS_KEY


def admin_bookings_key():
    return ADMIN_BOOKINGS_KEY


def admin_owners_key():
    return ADMIN_OWNERS_KEY


def public_car_list_key(query_string=''):
    version = cache.get(PUBLIC_CAR_LIST_VERSION_KEY, 0)
    digest = hashlib.md5(query_string.encode('utf-8')).hexdigest()[:16]
    return f'list:public:cars:v{version}:{digest}'


def owner_bookings_key(user_id):
    return f'list:owner:bookings:{user_id}'


def customer_bookings_key(user_id):
    return f'list:customer:bookings:{user_id}'


def owner_cars_key(user_id):
    return f'list:owner:cars:{user_id}'


def invalidate_admin_lists():
    cache.delete_many([
        admin_cars_key(),
        admin_bookings_key(),
        admin_owners_key(),
    ])


def invalidate_public_car_lists():
    try:
        current = cache.get(PUBLIC_CAR_LIST_VERSION_KEY, 0)
        cache.set(PUBLIC_CAR_LIST_VERSION_KEY, int(current) + 1, timeout=None)
    except (TypeError, ValueError):
        cache.set(PUBLIC_CAR_LIST_VERSION_KEY, 1, timeout=None)


def invalidate_car_caches():
    invalidate_admin_lists()
    invalidate_public_car_lists()


def invalidate_booking_caches(user_id=None, owner_id=None):
    invalidate_admin_lists()
    keys = []
    if user_id:
        keys.append(customer_bookings_key(user_id))
    if owner_id:
        keys.append(owner_bookings_key(owner_id))
    if keys:
        cache.delete_many(keys)


def invalidate_owner_caches(user_id=None):
    invalidate_admin_lists()
    if user_id:
        cache.delete(owner_cars_key(user_id))


def cache_api_response(cache_timeout=300):
    """Decorator to cache API responses for a specified duration."""

    def decorator(view_func):
        @wraps(view_func)
        @cache_page(cache_timeout)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def add_cache_headers(response, max_age=300):
    response['Cache-Control'] = f'public, max-age={max_age}'
    return response


class PublicCacheHeadersMixin:
    """Short public HTTP cache for anonymous browse endpoints."""

    cache_timeout = 600

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.method == 'GET' and response.status_code == 200:
            response['Cache-Control'] = f'public, max-age={self.cache_timeout}'
        return response


class NoCacheMixin:
    """Prevent browser/CDN caching of admin and user-specific API responses."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if request.method == 'GET':
            response['Cache-Control'] = 'no-store, max-age=0, must-revalidate'
        return response


# Backwards compatibility alias
CacheHeadersMixin = PublicCacheHeadersMixin


class RedisListCacheMixin:
    """
    Cache serialized list responses in Django cache (Redis or LocMem).
    Set redis_cache_key on the view, or override get_redis_cache_key().
    """

    redis_cache_key = None
    redis_cache_ttl = None

    def get_redis_cache_key(self):
        if self.redis_cache_key:
            return self.redis_cache_key
        params = '&'.join(
            f'{k}={v}' for k, v in sorted(self.request.query_params.items())
        )
        return f'{self.__class__.__name__}:{params}'

    def get_redis_cache_ttl(self):
        if self.redis_cache_ttl is not None:
            return self.redis_cache_ttl
        return getattr(settings, 'CACHE_TTL_ADMIN_LIST', 120)

    def list(self, request, *args, **kwargs):
        if not getattr(settings, 'CACHE_ENABLED', False):
            return super().list(request, *args, **kwargs)

        key = self.get_redis_cache_key()
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        response = super().list(request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(key, response.data, self.get_redis_cache_ttl())
        return response
