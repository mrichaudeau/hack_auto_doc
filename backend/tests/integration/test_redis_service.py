"""
Integration tests for Redis service startup and health.

Tests verify that:
1. Redis container is running
2. Redis health check passes within expected timeframe
3. Redis responds to PING command
4. Redis named volume exists
"""

import pytest
import subprocess
import time


class TestRedisService:
    """Integration tests for Redis service startup and health."""

    def test_redis_container_running(self):
        """Verify Redis container is running."""
        result = subprocess.run(
            ["docker-compose", "ps", "-q", "redis"],
            capture_output=True,
            text=True,
            cwd="../../",
        )
        assert result.stdout.strip(), "Redis container is not running"

    def test_redis_health_check_passes(self):
        """Verify Redis health check passes within expected timeframe."""
        start_time = time.time()
        timeout = 10  # 10 seconds timeout

        while time.time() - start_time < timeout:
            result = subprocess.run(
                ["docker-compose", "ps", "redis"],
                capture_output=True,
                text=True,
                cwd="../../",
            )
            if "healthy" in result.stdout:
                elapsed = time.time() - start_time
                print(f"Redis became healthy in {elapsed:.2f}s")
                assert (
                    elapsed < 5
                ), f"Redis took {elapsed:.2f}s to become healthy (expected < 5s)"
                return
            time.sleep(0.5)

        pytest.fail("Redis health check did not pass within 10 seconds")

    def test_redis_ping_response(self):
        """Verify Redis responds to PING command."""
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            cwd="../../",
        )
        assert (
            "PONG" in result.stdout
        ), f"Redis did not respond to PING. Output: {result.stdout}"

    def test_redis_volume_exists(self):
        """Verify Redis data volume exists."""
        result = subprocess.run(
            ["docker", "volume", "ls", "-q"], capture_output=True, text=True
        )
        volumes = result.stdout.strip().split("\n")
        redis_volumes = [v for v in volumes if "redis_data" in v]
        assert (
            len(redis_volumes) > 0
        ), f"Redis volume does not exist. Found volumes: {volumes}"

    def test_redis_maxmemory_configured(self):
        """Verify Redis maxmemory is configured to 256MB."""
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "redis",
                "redis-cli",
                "CONFIG",
                "GET",
                "maxmemory",
            ],
            capture_output=True,
            text=True,
            cwd="../../",
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            maxmemory = int(lines[1])
            expected = 268435456  # 256MB in bytes
            assert (
                maxmemory == expected
            ), f"Redis maxmemory is {maxmemory}, expected {expected}"

    def test_redis_eviction_policy_configured(self):
        """Verify Redis maxmemory-policy is set to allkeys-lru."""
        result = subprocess.run(
            [
                "docker-compose",
                "exec",
                "-T",
                "redis",
                "redis-cli",
                "CONFIG",
                "GET",
                "maxmemory-policy",
            ],
            capture_output=True,
            text=True,
            cwd="../../",
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            policy = lines[1]
            assert (
                policy == "allkeys-lru"
            ), f"Redis maxmemory-policy is {policy}, expected allkeys-lru"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
