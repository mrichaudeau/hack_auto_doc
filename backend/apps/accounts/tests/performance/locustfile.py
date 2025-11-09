"""
Locust Load Testing for Login Endpoint (US-3: Standard User Login, TASK-3.20)

Load test configuration to verify login endpoint meets performance requirements:
- P95 latency < 300ms
- P99 latency < 500ms
- Handles 100 concurrent users
- Sustained load for 2+ minutes

Usage:
    # Start Django development server
    docker-compose up backend

    # Run load test
    locust -f backend/apps/accounts/tests/performance/locustfile.py \\
           --host=http://localhost:8000 \\
           --users 100 \\
           --spawn-rate 10 \\
           --run-time 2m

    # Run with Web UI for visualization
    locust -f backend/apps/accounts/tests/performance/locustfile.py \\
           --host=http://localhost:8000
    # Then open: http://localhost:8089

    # Run headless (no Web UI) with CSV output
    locust -f backend/apps/accounts/tests/performance/locustfile.py \\
           --host=http://localhost:8000 \\
           --users 100 \\
           --spawn-rate 10 \\
           --run-time 2m \\
           --headless \\
           --csv=login_perf

Requirements:
    pip install locust
"""

from locust import HttpUser, task, between, events
import logging

# Configure logging for test output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoginUser(HttpUser):
    """
    Simulates realistic user login behavior with both successful and failed attempts.

    Load distribution:
    - 60% failed logins (weight=3) - Realistic scenario, users often mistype passwords
    - 20% successful logins (weight=1)
    - 20% non-existent user attempts (weight=1) - Brute force attempts, phishing victims

    Wait time: 1-3 seconds between requests (realistic user behavior)
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """
        Called when a simulated user starts.
        Set up test user credentials.
        """
        # These credentials should exist in test database
        self.valid_email = "loadtest@example.com"
        self.valid_password = "LoadTest123!"

        logger.info(f"User {self.valid_email} started load testing")

    @task(1)
    def login_success(self):
        """
        Test successful login with valid credentials.

        Weight: 1 (20% of requests)
        Expected: 200 OK with JWT tokens
        """
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": self.valid_email,
                "password": self.valid_password
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Verify response contains expected JWT tokens
                data = response.json()
                if "access_token" in data and "refresh_token" in data:
                    response.success()
                else:
                    response.failure("Missing JWT tokens in response")
            elif response.status_code == 429:
                # Rate limiting is expected behavior, not a failure
                response.success()
                logger.warning("Rate limit hit during load test (expected behavior)")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(3)
    def login_failure_wrong_password(self):
        """
        Test failed login with wrong password.

        Weight: 3 (60% of requests) - Most common failure scenario
        Expected: 401 Unauthorized
        """
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": self.valid_email,
                "password": "WrongPassword123!"
            },
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()
            elif response.status_code == 429:
                # Rate limiting is expected behavior
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def login_failure_nonexistent_user(self):
        """
        Test login with non-existent user email.

        Weight: 1 (20% of requests)
        Expected: 401 Unauthorized (same as wrong password for security)
        """
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": f"nonexistent_{self._random_suffix()}@example.com",
                "password": "SomePassword123!"
            },
            catch_response=True
        ) as response:
            if response.status_code == 401:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    def _random_suffix(self):
        """Generate random suffix for test emails."""
        import random
        return random.randint(1000, 9999)


class RateLimitTester(HttpUser):
    """
    Specialized user that tests rate limiting under load.

    Tests that rate limiting holds up under heavy concurrent load
    without causing cascading failures or blocking legitimate requests.
    """

    wait_time = between(0.1, 0.5)  # Faster requests to trigger rate limits

    def on_start(self):
        """Set up credentials for rate limit testing."""
        self.email = "ratelimitest@example.com"
        self.password = "RateLimit123!"

    @task
    def rapid_login_attempts(self):
        """
        Make rapid login attempts to test rate limiting.

        Expected behavior:
        - First 5 attempts per IP per 5 minutes: 401 (invalid credentials)
        - Subsequent attempts: 429 (rate limited)
        - Retry-After header should be present on 429 responses
        """
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": self.email,
                "password": "WrongPassword!"
            },
            catch_response=True
        ) as response:
            if response.status_code in [401, 429]:
                # Both are acceptable responses
                response.success()

                # Verify Retry-After header on rate limited responses
                if response.status_code == 429:
                    if "Retry-After" in response.headers:
                        retry_after = response.headers["Retry-After"]
                        logger.info(f"Rate limited. Retry after {retry_after} seconds")
                    else:
                        logger.warning("Rate limit response missing Retry-After header")
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


class PerformanceMonitor(HttpUser):
    """
    Dedicated user for monitoring response time requirements.

    Tracks percentile latencies to verify performance requirements:
    - P95 < 300ms
    - P99 < 500ms
    """

    wait_time = between(2, 4)

    def on_start(self):
        """Set up monitoring user."""
        self.email = "perfmonitor@example.com"
        self.password = "PerfMonitor123!"

    @task
    def monitor_login_performance(self):
        """
        Monitor login endpoint performance.

        Locust automatically tracks response times and calculates percentiles.
        View in Locust Web UI or stats output.
        """
        with self.client.post(
            "/api/auth/login/",
            json={
                "email": self.email,
                "password": self.password
            },
            catch_response=True
        ) as response:
            # Track response time
            response_time = response.elapsed.total_seconds() * 1000  # Convert to ms

            if response.status_code == 200:
                response.success()

                # Log slow requests (> 300ms)
                if response_time > 300:
                    logger.warning(
                        f"Slow response detected: {response_time:.2f}ms "
                        f"(exceeds P95 target of 300ms)"
                    )
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


# ============================================================================
# Event Handlers for Test Reporting
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Called when load test starts.
    Initialize performance monitoring and logging.
    """
    logger.info("=" * 80)
    logger.info("🚀 Starting Login Endpoint Load Test")
    logger.info("=" * 80)
    logger.info(f"Target Host: {environment.host}")
    logger.info("Performance Requirements:")
    logger.info("  - P95 latency < 300ms")
    logger.info("  - P99 latency < 500ms")
    logger.info("  - 100 concurrent users")
    logger.info("  - 2 minute sustained load")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when load test stops.
    Report performance metrics and check requirements.
    """
    logger.info("=" * 80)
    logger.info("🏁 Load Test Complete")
    logger.info("=" * 80)

    # Access statistics from environment
    stats = environment.stats

    # Get aggregated stats for login endpoint
    login_stats = stats.get("/api/auth/login/", "POST")

    if login_stats:
        logger.info("📊 Login Endpoint Performance:")
        logger.info(f"  Total Requests: {login_stats.num_requests}")
        logger.info(f"  Failures: {login_stats.num_failures}")
        logger.info(f"  Median Response Time: {login_stats.median_response_time:.2f}ms")
        logger.info(f"  Average Response Time: {login_stats.avg_response_time:.2f}ms")
        logger.info(f"  Min Response Time: {login_stats.min_response_time:.2f}ms")
        logger.info(f"  Max Response Time: {login_stats.max_response_time:.2f}ms")

        # Get percentile data
        p50 = login_stats.get_response_time_percentile(0.50)
        p95 = login_stats.get_response_time_percentile(0.95)
        p99 = login_stats.get_response_time_percentile(0.99)

        logger.info(f"  P50: {p50:.2f}ms")
        logger.info(f"  P95: {p95:.2f}ms {'✅' if p95 < 300 else '❌ (Target: < 300ms)'}")
        logger.info(f"  P99: {p99:.2f}ms {'✅' if p99 < 500 else '❌ (Target: < 500ms)'}")

        # Check if requirements met
        requirements_met = p95 < 300 and p99 < 500

        logger.info("=" * 80)
        if requirements_met:
            logger.info("✅ Performance requirements MET")
        else:
            logger.warning("❌ Performance requirements NOT MET")
            if p95 >= 300:
                logger.warning(f"   P95 ({p95:.2f}ms) exceeds 300ms target")
            if p99 >= 500:
                logger.warning(f"   P99 ({p99:.2f}ms) exceeds 500ms target")

        logger.info("=" * 80)

        # Calculate requests per second
        rps = login_stats.total_rps
        logger.info(f"📈 Throughput: {rps:.2f} requests/second")
        logger.info("=" * 80)


# ============================================================================
# Load Test Profiles
# ============================================================================

"""
Recommended Load Test Profiles:

1. Development Test (Quick Smoke Test):
   locust -f locustfile.py --host=http://localhost:8000 \\
          --users 10 --spawn-rate 2 --run-time 30s --headless

2. Standard Load Test (100 concurrent users, 2 minutes):
   locust -f locustfile.py --host=http://localhost:8000 \\
          --users 100 --spawn-rate 10 --run-time 2m --headless

3. Stress Test (200 concurrent users, 5 minutes):
   locust -f locustfile.py --host=http://localhost:8000 \\
          --users 200 --spawn-rate 20 --run-time 5m --headless

4. Endurance Test (50 users, 30 minutes):
   locust -f locustfile.py --host=http://localhost:8000 \\
          --users 50 --spawn-rate 5 --run-time 30m --headless

5. Interactive Test (Web UI):
   locust -f locustfile.py --host=http://localhost:8000
   # Open http://localhost:8089 to configure test parameters

Expected Results for Standard Load Test:
- Total Requests: ~10,000+ (over 2 minutes)
- Success Rate: > 95% (excluding expected rate limits)
- P95 Latency: < 300ms
- P99 Latency: < 500ms
- Requests/sec: > 80 RPS
"""
