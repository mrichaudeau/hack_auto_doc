import pytest
import redis
import time
from django.core.cache import cache
from django.conf import settings


class TestCacheOperations:
    """Integration tests for Django cache operations with Redis."""

    def setup_method(self):
        """Clear cache before each test."""
        cache.clear()

    def test_cache_set_get(self):
        """Verify cache set and get operations."""
        cache.set('test_key', 'test_value', timeout=60)
        value = cache.get('test_key')
        assert value == 'test_value', "Cache get did not return expected value"

    def test_cache_ttl_expiration(self):
        """Verify cache TTL expires correctly."""
        cache.set('expire_key', 'value', timeout=2)
        assert cache.get('expire_key') == 'value', "Key should exist before expiration"

        time.sleep(3)
        assert cache.get('expire_key') is None, "Key should expire after TTL"

    def test_cache_delete(self):
        """Verify cache delete removes keys."""
        cache.set('delete_key', 'value', timeout=60)
        assert cache.get('delete_key') == 'value', "Key should exist before delete"

        cache.delete('delete_key')
        assert cache.get('delete_key') is None, "Key should be deleted"

    def test_cache_keys_in_correct_db(self):
        """Verify cache keys are stored in Redis DB 1, not DB 0."""
        cache.set('db_test_key', 'value', timeout=60)

        # Check DB 1 (cache)
        cache_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)
        db1_keys = cache_client.keys('*')
        assert len(db1_keys) > 0, "No keys found in Redis DB 1 (cache)"

        # Check DB 0 (broker) - should not have cache keys
        broker_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        db0_keys = broker_client.keys('*db_test_key*')
        assert len(db0_keys) == 0, "Cache keys should not exist in DB 0 (broker)"

        cache_client.close()
        broker_client.close()

    def test_cache_key_prefix(self):
        """Verify cache key prefix is applied."""
        cache.set('prefix_test', 'value', timeout=60)

        cache_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)
        keys = cache_client.keys('*')

        # Check if any key contains the configured prefix
        prefix = settings.CACHES['default']['OPTIONS'].get('KEY_PREFIX', 'techwatch')
        prefixed_keys = [k for k in keys if prefix in k]
        assert len(prefixed_keys) > 0, f"No keys with prefix '{prefix}' found"

        cache_client.close()

    def test_cache_operation_latency(self):
        """Verify cache operations are fast enough."""
        start = time.time()
        cache.set('latency_test', 'value', timeout=60)
        set_latency_ms = (time.time() - start) * 1000

        start = time.time()
        cache.get('latency_test')
        get_latency_ms = (time.time() - start) * 1000

        assert set_latency_ms < 10, f"Cache SET latency too high: {set_latency_ms}ms"
        assert get_latency_ms < 10, f"Cache GET latency too high: {get_latency_ms}ms"

    def test_cache_clear(self):
        """Verify cache clear removes all keys."""
        cache.set('clear_test_1', 'value1', timeout=60)
        cache.set('clear_test_2', 'value2', timeout=60)

        cache.clear()

        assert cache.get('clear_test_1') is None, "Key should be cleared"
        assert cache.get('clear_test_2') is None, "Key should be cleared"
