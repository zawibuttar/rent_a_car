"""Proxy OpenStreetMap tiles for location message previews."""
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.cache import cache
from django.http import HttpResponse

from cars.geocoding import USER_AGENT

TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
CACHE_TTL = 86400


def _tile_coords(lat, lng, zoom):
    lat = float(lat)
    lng = float(lng)
    zoom = int(zoom)
    n = 2 ** zoom
    x = int((lng + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return zoom, x, y


def map_preview_path(lat, lng, zoom=14):
    return f'/api/messaging/map-preview/?lat={lat}&lng={lng}&z={zoom}'


def map_preview_absolute_url(lat, lng, request=None, zoom=14):
    path = map_preview_path(lat, lng, zoom=zoom)
    if request:
        return request.build_absolute_uri(path)
    return path


def fetch_map_tile(lat, lng, zoom=14):
    z, x, y = _tile_coords(lat, lng, zoom)
    cache_key = f'map-tile:{z}:{x}:{y}'
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = TILE_URL.format(z=z, x=x, y=y)
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(req, timeout=8) as resp:
            data = resp.read()
    except (HTTPError, URLError, TimeoutError):
        return None

    if data:
        cache.set(cache_key, data, CACHE_TTL)
    return data


def map_preview_response(lat, lng, zoom=14):
    data = fetch_map_tile(lat, lng, zoom)
    if not data:
        return HttpResponse(status=502)
    response = HttpResponse(data, content_type='image/png')
    response['Cache-Control'] = 'public, max-age=86400'
    return response
