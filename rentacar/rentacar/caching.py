"""
API caching utilities to reduce database queries and improve page load times.
"""

from functools import wraps
from django.views.decorators.cache import cache_page
from rest_framework.response import Response


def cache_api_response(cache_timeout=300):
    """
    Decorator to cache API responses for a specified duration.
    
    Usage:
        @cache_api_response(cache_timeout=600)  # 10 minutes
        class MyListView(generics.ListAPIView):
            ...
    
    Args:
        cache_timeout: Duration in seconds to cache the response (default: 5 minutes)
    """
    def decorator(view_func):
        @wraps(view_func)
        @cache_page(cache_timeout)
        def wrapper(*args, **kwargs):
            return view_func(*args, **kwargs)
        return wrapper
    return decorator


def add_cache_headers(response, max_age=300):
    """
    Add HTTP Cache-Control headers to a response.
    
    Args:
        response: Django response object
        max_age: Max age in seconds for browser/CDN cache
    """
    response['Cache-Control'] = f'public, max-age={max_age}'
    return response


class CacheHeadersMixin:
    """
    Mixin for DRF views to automatically add Cache-Control headers.
    Set cache_timeout (in seconds) on the view class.
    """
    cache_timeout = 300  # Default: 5 minutes
    
    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        
        # Only cache successful GET requests
        if request.method == 'GET' and response.status_code == 200:
            response['Cache-Control'] = f'public, max-age={self.cache_timeout}'
        
        return response
