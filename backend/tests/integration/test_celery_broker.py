import pytest
import redis
import time
from celery import Celery
from django.conf import settings


class TestCeleryBroker:
    """Integration tests for Celery broker connectivity."""

    def test_broker_connection(self):
        """Verify Celery can connect to Redis broker."""
        app = Celery(broker=settings.CELERY_BROKER_URL)
        try:
            with app.connection_or_acquire() as conn:
                assert conn.connected, "Celery broker connection failed"
        except Exception as e:
            pytest.fail(f"Failed to connect to Celery broker: {str(e)}")

    def test_broker_keys_exist(self):
        """Verify Celery can write to Redis DB 0."""
        # Create a Redis client for DB 0 (broker)
        client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

        # Set a test key
        test_key = f'celery_test_{int(time.time())}'
        client.set(test_key, 'test_value', ex=60)

        # Verify the key exists
        value = client.get(test_key)
        assert value == 'test_value', "Failed to write/read from Redis DB 0"

        # Clean up
        client.delete(test_key)
        client.close()

    def test_broker_latency(self):
        """Verify broker connection latency is acceptable."""
        client = redis.Redis(host='redis', port=6379, db=0)

        start = time.time()
        client.ping()
        latency_ms = (time.time() - start) * 1000

        client.close()
        assert latency_ms < 50, f"Broker latency too high: {latency_ms}ms"

    def test_broker_separate_from_cache(self):
        """Verify broker (DB 0) is separate from cache (DB 1)."""
        # Write to broker (DB 0)
        broker_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        broker_key = f'broker_test_{int(time.time())}'
        broker_client.set(broker_key, 'broker_value', ex=60)

        # Verify it doesn't exist in cache (DB 1)
        cache_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)
        cache_value = cache_client.get(broker_key)

        assert cache_value is None, "Broker keys should not appear in cache DB"

        # Clean up
        broker_client.delete(broker_key)
        broker_client.close()
        cache_client.close()
