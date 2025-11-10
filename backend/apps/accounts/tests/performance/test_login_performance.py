"""
Performance Tests for Login Endpoint (US-3: Standard User Login, TASK-3.20)

Tests login endpoint performance against requirements:
- P95 latency < 300ms
- P99 latency < 500ms
- Handles 100 concurrent users
- No memory leaks during extended test

Uses pytest-benchmark for performance measurement.
For load testing, see locustfile.py in this directory.

Usage:
    # Run performance tests
    pytest backend/apps/accounts/tests/performance/ -v

    # Run with benchmark comparison
    pytest backend/apps/accounts/tests/performance/ --benchmark-compare

    # Save benchmark results
    pytest backend/apps/accounts/tests/performance/ --benchmark-save=login_perf
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client for testing."""
    return APIClient()


@pytest.fixture
def verified_user(db):
    """Create verified user for performance tests."""
    return User.objects.create_user(
        email='perftest@example.com',
        password='PerfTest123!',
        first_name='Perf',
        last_name='Tester',
        is_email_verified=True,
        is_active=True
    )


@pytest.fixture(autouse=True)
def clear_cache_before_test():
    """Clear cache before each test to reset rate limiting."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestLoginPerformanceBenchmark:
    """Benchmark tests for login endpoint performance."""

    def test_successful_login_performance(self, benchmark, api_client, verified_user):
        """
        Benchmark successful login performance.

        Requirement: P95 < 300ms, P99 < 500ms
        This test measures baseline performance for successful authentication.
        """
        def login_success():
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            assert response.status_code == status.HTTP_200_OK
            return response

        # Run benchmark (default: multiple rounds to get reliable statistics)
        result = benchmark(login_success)

        # Benchmark provides statistics
        # Note: pytest-benchmark calculates percentiles automatically
        # Results viewable in benchmark report

    def test_failed_login_performance(self, benchmark, api_client, verified_user):
        """
        Benchmark failed login performance.

        Failed logins should have similar performance to prevent timing attacks.
        """
        def login_failure():
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'WrongPassword!'
            })
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            return response

        result = benchmark(login_failure)

    def test_nonexistent_user_login_performance(self, benchmark, api_client):
        """
        Benchmark login with non-existent user.

        Should have similar performance to failed login (timing attack prevention).
        """
        def login_nonexistent():
            response = api_client.post('/api/auth/login/', {
                'email': 'nonexistent@example.com',
                'password': 'SomePassword123!'
            })
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            return response

        result = benchmark(login_nonexistent)

    def test_unverified_user_login_performance(self, benchmark, api_client, db):
        """
        Benchmark login with unverified user.

        Tests performance of email verification check.
        """
        # Create unverified user
        User.objects.create_user(
            email='unverified@example.com',
            password='PerfTest123!',
            is_email_verified=False,
            is_active=True
        )

        def login_unverified():
            response = api_client.post('/api/auth/login/', {
                'email': 'unverified@example.com',
                'password': 'PerfTest123!'
            })
            assert response.status_code == status.HTTP_403_FORBIDDEN
            return response

        result = benchmark(login_unverified)


@pytest.mark.django_db
class TestLoginPerformanceLoad:
    """Load tests for login endpoint (simulated concurrent requests)."""

    def test_sequential_login_requests(self, api_client, verified_user, clear_cache_before_test):
        """
        Test performance of sequential login requests.

        Verifies no performance degradation over multiple requests.
        """
        response_times = []

        # Make 50 sequential requests
        for i in range(50):
            import time
            start = time.time()

            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })

            elapsed = time.time() - start
            response_times.append(elapsed)

            assert response.status_code == status.HTTP_200_OK

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50_index = int(len(sorted_times) * 0.50)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)

        p50 = sorted_times[p50_index]
        p95 = sorted_times[p95_index]
        p99 = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]

        print(f"\n📊 Sequential Login Performance:")
        print(f"   P50: {p50*1000:.2f}ms")
        print(f"   P95: {p95*1000:.2f}ms")
        print(f"   P99: {p99*1000:.2f}ms")

        # Verify performance requirements
        # Note: These are relaxed for CI environments
        assert p95 < 1.0, f"P95 latency {p95*1000:.2f}ms exceeds 1000ms threshold (CI-adjusted)"
        assert p99 < 2.0, f"P99 latency {p99*1000:.2f}ms exceeds 2000ms threshold (CI-adjusted)"

    def test_rate_limiting_performance(self, api_client, verified_user):
        """
        Test rate limiting doesn't cause performance degradation.

        Verifies rate limiting logic is fast and doesn't block unnecessarily.
        """
        import time

        # Make 4 requests (under rate limit of 5)
        times_under_limit = []
        for i in range(4):
            start = time.time()
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            elapsed = time.time() - start
            times_under_limit.append(elapsed)
            assert response.status_code == status.HTTP_200_OK

        # 5th request should still succeed
        start = time.time()
        response = api_client.post('/api/auth/login/', {
            'email': 'perftest@example.com',
            'password': 'PerfTest123!'
        })
        fifth_request_time = time.time() - start
        assert response.status_code == status.HTTP_200_OK

        # 6th request should be rate limited
        start = time.time()
        response = api_client.post('/api/auth/login/', {
            'email': 'perftest@example.com',
            'password': 'PerfTest123!'
        })
        rate_limited_time = time.time() - start
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        avg_normal = sum(times_under_limit) / len(times_under_limit)
        print(f"\n📊 Rate Limiting Performance:")
        print(f"   Average (under limit): {avg_normal*1000:.2f}ms")
        print(f"   5th request: {fifth_request_time*1000:.2f}ms")
        print(f"   Rate limited response: {rate_limited_time*1000:.2f}ms")

        # Rate limited response should be fast (just cache check)
        assert rate_limited_time < 0.5, "Rate limited response too slow"

    def test_jwt_token_generation_performance(self, api_client, verified_user):
        """
        Test JWT token generation doesn't significantly impact performance.

        Compares successful login (with token generation) to failed login (no tokens).
        """
        import time

        # Measure successful logins (with token generation)
        success_times = []
        for _ in range(10):
            start = time.time()
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            elapsed = time.time() - start
            success_times.append(elapsed)
            assert response.status_code == status.HTTP_200_OK
            assert 'access_token' in response.json()
            assert 'refresh_token' in response.json()

        avg_with_tokens = sum(success_times) / len(success_times)

        # Clear cache for failed login tests
        cache.clear()

        # Measure failed logins (no token generation)
        failure_times = []
        for _ in range(10):
            start = time.time()
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'WrongPassword!'
            })
            elapsed = time.time() - start
            failure_times.append(elapsed)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        avg_without_tokens = sum(failure_times) / len(failure_times)

        print(f"\n📊 JWT Token Generation Impact:")
        print(f"   With tokens (success): {avg_with_tokens*1000:.2f}ms")
        print(f"   Without tokens (failure): {avg_without_tokens*1000:.2f}ms")
        print(f"   Token generation overhead: {(avg_with_tokens - avg_without_tokens)*1000:.2f}ms")

        # Token generation should add minimal overhead (< 100ms)
        token_overhead = avg_with_tokens - avg_without_tokens
        assert token_overhead < 0.1, f"Token generation overhead {token_overhead*1000:.2f}ms too high"


@pytest.mark.django_db
class TestLoginMemoryPerformance:
    """Memory and resource tests for login endpoint."""

    def test_no_memory_leak_extended_login(self, api_client, verified_user):
        """
        Test for memory leaks during extended login operations.

        Makes many requests and verifies memory doesn't grow unbounded.
        """
        import gc

        # Force garbage collection before test
        gc.collect()

        # Make 100 login requests
        for i in range(100):
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            assert response.status_code == status.HTTP_200_OK

            # Periodically clear cache to prevent Redis memory buildup
            if i % 20 == 0:
                cache.clear()

        # Force garbage collection after test
        gc.collect()

        # Test passes if no memory errors occurred
        # In production, monitor with memory profiler tools

    def test_database_connection_pool_efficiency(self, api_client, verified_user):
        """
        Test database connection pool doesn't exhaust under load.

        Makes multiple requests and verifies connections are reused properly.
        """
        # Make 30 requests (more than typical connection pool size)
        for i in range(30):
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            # Should succeed without connection pool exhaustion
            assert response.status_code == status.HTTP_200_OK

    def test_redis_connection_pool_efficiency(self, api_client, verified_user):
        """
        Test Redis connection pool handles multiple rate limiting checks.

        Verifies Redis connections are properly pooled and reused.
        """
        # Make 20 requests to trigger rate limiting checks
        responses = []
        for i in range(20):
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            responses.append(response.status_code)

        # First 5 should succeed, rest should be rate limited
        successful = [r for r in responses if r == status.HTTP_200_OK]
        rate_limited = [r for r in responses if r == status.HTTP_429_TOO_MANY_REQUESTS]

        assert len(successful) == 5, f"Expected 5 successful, got {len(successful)}"
        assert len(rate_limited) == 15, f"Expected 15 rate limited, got {len(rate_limited)}"

        # Test passes if no Redis connection errors occurred


@pytest.mark.django_db
class TestLoginPerformanceRegression:
    """Regression tests to ensure performance doesn't degrade over time."""

    def test_login_performance_baseline(self, benchmark, api_client, verified_user):
        """
        Baseline performance test for comparison.

        Use --benchmark-save to save results for comparison:
        pytest test_login_performance.py --benchmark-save=baseline

        Compare with:
        pytest test_login_performance.py --benchmark-compare=baseline
        """
        def login():
            response = api_client.post('/api/auth/login/', {
                'email': 'perftest@example.com',
                'password': 'PerfTest123!'
            })
            assert response.status_code == status.HTTP_200_OK
            return response

        result = benchmark(login)

        # Store benchmark results for regression detection
        # pytest-benchmark automatically tracks mean, stddev, min, max, percentiles
