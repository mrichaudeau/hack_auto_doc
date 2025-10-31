import redis
import time
from django.conf import settings


def check_redis_health():
    """
    Check Redis connectivity for broker and cache databases.

    Returns:
        dict: Status information for broker (DB 0) and cache (DB 1) including
              connectivity status, latency in milliseconds, and any error messages.
    """
    results = {
        'broker': {'connected': False, 'latency_ms': None, 'error': None},
        'cache': {'connected': False, 'latency_ms': None, 'error': None}
    }

    # Test broker (DB 0)
    try:
        broker_client = redis.from_url(settings.CELERY_BROKER_URL)
        start = time.time()
        broker_client.ping()
        latency = (time.time() - start) * 1000
        results['broker'] = {
            'connected': True,
            'latency_ms': round(latency, 2),
            'error': None
        }
        broker_client.close()
    except Exception as e:
        results['broker']['error'] = str(e)

    # Test cache (DB 1)
    try:
        cache_url = settings.CACHES['default']['LOCATION']
        cache_client = redis.from_url(cache_url)
        start = time.time()
        cache_client.ping()
        latency = (time.time() - start) * 1000
        results['cache'] = {
            'connected': True,
            'latency_ms': round(latency, 2),
            'error': None
        }
        cache_client.close()
    except Exception as e:
        results['cache']['error'] = str(e)

    return results
