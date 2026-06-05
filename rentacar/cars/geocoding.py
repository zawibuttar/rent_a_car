"""OpenStreetMap Nominatim proxy with cache and usage-policy User-Agent."""
import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.cache import cache

NOMINATIM_SEARCH = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_REVERSE = 'https://nominatim.openstreetmap.org/reverse'
USER_AGENT = 'RentACar/1.0 (https://github.com/moeezashraf/rent_a_car; location search)'
CACHE_TTL = 3600


def _cache_key(prefix, payload):
    digest = hashlib.md5(payload.encode('utf-8')).hexdigest()
    return f'geo:{prefix}:{digest}'


def _fetch_json(url):
    req = Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
        'Accept-Language': 'en',
    })
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))


def normalize_result(result):
    if not result:
        return None
    address = result.get('address') or {}
    city = (
        address.get('city')
        or address.get('town')
        or address.get('village')
        or address.get('municipality')
        or address.get('county')
        or address.get('state')
        or result.get('display_name')
        or ''
    )
    label = str(city).strip() if city else str(result.get('display_name', '')).split(',')[0].strip()
    if not label:
        return None
    try:
        lat = float(result['lat']) if result.get('lat') is not None else None
    except (TypeError, ValueError):
        lat = None
    try:
        lon = float(result['lon']) if result.get('lon') is not None else None
    except (TypeError, ValueError):
        lon = None
    return {
        'label': label,
        'query': label,
        'displayName': result.get('display_name') or '',
        'lat': lat,
        'lon': lon,
        'source': 'map',
    }


def search_cities(query, limit=8):
    query = (query or '').strip()
    if len(query) < 2:
        return []

    cache_key = _cache_key('search', query.lower())
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = urlencode({
        'format': 'jsonv2',
        'addressdetails': 1,
        'limit': limit,
        'countrycodes': 'pk',
        'q': query,
    })
    data = _fetch_json(f'{NOMINATIM_SEARCH}?{params}')
    if not isinstance(data, list):
        results = []
    else:
        results = [r for r in (normalize_result(item) for item in data) if r]

    cache.set(cache_key, results, CACHE_TTL)
    return results


def reverse_geocode(lat, lon):
    cache_key = _cache_key('reverse', f'{lat:.5f},{lon:.5f}')
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    params = urlencode({
        'format': 'jsonv2',
        'addressdetails': 1,
        'lat': lat,
        'lon': lon,
    })
    data = _fetch_json(f'{NOMINATIM_REVERSE}?{params}')
    result = normalize_result(data) if isinstance(data, dict) else None
    if result:
        result['lat'] = lat
        result['lon'] = lon
        result['source'] = 'geolocation'
    cache.set(cache_key, result, CACHE_TTL)
    return result
