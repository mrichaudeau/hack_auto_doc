from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache


def health_check(request):
    """Health check endpoint for Docker and monitoring."""
    status = {
        'status': 'healthy',
        'database': 'unknown',
        'redis': 'unknown'
    }
    http_status = 200

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        status['database'] = 'ok'
    except Exception as e:
        status['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        http_status = 503

    # Check Redis
    try:
        cache.set('health_check', 'ok', timeout=10)
        if cache.get('health_check') == 'ok':
            status['redis'] = 'ok'
        else:
            raise Exception('Cache set/get failed')
    except Exception as e:
        status['redis'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
        http_status = 503

    return JsonResponse(status, status=http_status)
