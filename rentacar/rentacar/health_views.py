from django.conf import settings
from django.core.cache import cache
from django.db import connection
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_ok = True
        try:
            connection.ensure_connection()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception:
            db_ok = False

        cache_ok = True
        if settings.CACHE_ENABLED:
            try:
                cache.set('health_check', 'ok', 5)
                cache_ok = cache.get('health_check') == 'ok'
            except Exception:
                cache_ok = False

        payload = {
            'status': 'ok' if db_ok else 'degraded',
            'database': db_ok,
            'cache': cache_ok if settings.CACHE_ENABLED else 'disabled',
        }
        code = 200 if db_ok else 503
        return Response(payload, status=code)
