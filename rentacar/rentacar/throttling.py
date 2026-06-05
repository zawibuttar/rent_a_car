from rest_framework.throttling import ScopedRateThrottle


class AuthRateThrottle(ScopedRateThrottle):
    scope = 'auth'


class BookingRateThrottle(ScopedRateThrottle):
    scope = 'booking'


class LocationRateThrottle(ScopedRateThrottle):
    scope = 'location'


class AdminRateThrottle(ScopedRateThrottle):
    """Higher limit for platform-admin list APIs (replaces default user throttle)."""
    scope = 'admin'
