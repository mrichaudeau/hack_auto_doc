# Login Performance Tests

Performance testing suite for the login authentication endpoint (US-3: Standard User Login, TASK-3.20).

## Performance Requirements

- **P95 latency** < 300ms (95% of requests complete in under 300ms)
- **P99 latency** < 500ms (99% of requests complete in under 500ms)
- **Concurrent users**: Handle 100 concurrent users
- **Sustained load**: No degradation over 2+ minutes
- **Error rate**: < 5% (excluding expected rate limits)

## Test Suite Components

### 1. pytest-benchmark Tests (`test_login_performance.py`)

Detailed performance benchmarks using pytest-benchmark for precise measurements.

**Test Categories:**
- **Benchmark Tests**: Baseline performance measurements
- **Load Tests**: Sequential and concurrent request handling
- **Memory Tests**: Memory leak detection and connection pool efficiency
- **Regression Tests**: Compare performance over time

**Run Command:**
```bash
# Run all performance tests
pytest backend/apps/accounts/tests/performance/test_login_performance.py -v

# Run with benchmark statistics
pytest backend/apps/accounts/tests/performance/test_login_performance.py --benchmark-only

# Save baseline for comparison
pytest backend/apps/accounts/tests/performance/test_login_performance.py --benchmark-save=baseline

# Compare with baseline
pytest backend/apps/accounts/tests/performance/test_login_performance.py --benchmark-compare=baseline
```

### 2. Locust Load Tests (`locustfile.py`)

Realistic load testing with simulated concurrent users using Locust.

**User Profiles:**
- **LoginUser** (60% of traffic): Realistic login attempts (success + failures)
- **RateLimitTester** (20% of traffic): Tests rate limiting under load
- **PerformanceMonitor** (20% of traffic): Tracks response time requirements

**Run Commands:**

```bash
# Quick smoke test (10 users, 30 seconds)
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 10 \
       --spawn-rate 2 \
       --run-time 30s \
       --headless

# Standard load test (100 users, 2 minutes)
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 2m \
       --headless

# Stress test (200 users, 5 minutes)
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 200 \
       --spawn-rate 20 \
       --run-time 5m \
       --headless

# Interactive test with Web UI
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000
# Then open: http://localhost:8089

# Save results to CSV
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 2m \
       --headless \
       --csv=login_perf
```

## Prerequisites

### 1. Install Dependencies

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Install Locust
pip install locust

# Or install from requirements
cd backend
poetry add --group dev pytest-benchmark locust
```

### 2. Prepare Test Database

Create test users for load testing:

```python
# Django shell
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

# Create load test users
User.objects.create_user(
    email='loadtest@example.com',
    password='LoadTest123!',
    is_email_verified=True,
    is_active=True
)

User.objects.create_user(
    email='ratelimitest@example.com',
    password='RateLimit123!',
    is_email_verified=True,
    is_active=True
)

User.objects.create_user(
    email='perfmonitor@example.com',
    password='PerfMonitor123!',
    is_email_verified=True,
    is_active=True
)
```

### 3. Start Services

```bash
# Start Django development server
docker-compose up backend

# Or start all services
docker-compose up -d

# Verify services are running
curl http://localhost:8000/api/auth/login/
```

## Test Scenarios

### Scenario 1: Baseline Performance

Measure baseline performance without load:

```bash
pytest backend/apps/accounts/tests/performance/test_login_performance.py::TestLoginPerformanceBenchmark::test_successful_login_performance -v
```

**Expected Results:**
- Mean response time: 50-100ms
- Standard deviation: < 20ms

### Scenario 2: Rate Limiting Performance

Test rate limiting doesn't degrade performance:

```bash
pytest backend/apps/accounts/tests/performance/test_login_performance.py::TestLoginPerformanceLoad::test_rate_limiting_performance -v
```

**Expected Results:**
- Normal requests: < 100ms
- Rate limited response: < 50ms (faster, just cache check)

### Scenario 3: Sustained Load Test

Test performance under sustained load:

```bash
locust -f backend/apps/accounts/tests/performance/locustfile.py \
       --host=http://localhost:8000 \
       --users 100 \
       --spawn-rate 10 \
       --run-time 2m \
       --headless
```

**Expected Results:**
- Total requests: > 10,000
- P95: < 300ms
- P99: < 500ms
- Success rate: > 95%
- Requests/sec: > 80 RPS

### Scenario 4: Memory Leak Detection

Test for memory leaks over extended operation:

```bash
pytest backend/apps/accounts/tests/performance/test_login_performance.py::TestLoginMemoryPerformance::test_no_memory_leak_extended_login -v
```

**Expected Results:**
- No memory errors
- Stable memory usage over 100 requests

### Scenario 5: Connection Pool Testing

Verify database and Redis connection pools:

```bash
pytest backend/apps/accounts/tests/performance/test_login_performance.py::TestLoginMemoryPerformance -v
```

**Expected Results:**
- No connection pool exhaustion
- All requests complete successfully

## Interpreting Results

### pytest-benchmark Output

```
------------------- benchmark: 1 tests -------------------
Name (time in ms)          Mean    StdDev    Min      Max
----------------------------------------------------------
test_successful_login     52.34    3.21     48.12   58.91
----------------------------------------------------------
```

**Key Metrics:**
- **Mean**: Average response time (target: < 100ms)
- **StdDev**: Consistency (target: < 20ms)
- **Min/Max**: Range (target: Max < 200ms)

### Locust Output

```
📊 Login Endpoint Performance:
  Total Requests: 12,345
  Failures: 123 (1.0%)
  P50: 42ms
  P95: 285ms ✅ (Target: < 300ms)
  P99: 475ms ✅ (Target: < 500ms)

📈 Throughput: 102.87 requests/second
```

**Key Metrics:**
- **P95**: 95th percentile (target: < 300ms)
- **P99**: 99th percentile (target: < 500ms)
- **Throughput**: Requests per second (target: > 80 RPS)
- **Failure rate**: % of failed requests (target: < 5%)

## Performance Optimization Tips

If performance requirements are not met:

### 1. Database Optimization
```python
# Add database indexes
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True, db_index=True)  # Index for lookups
    is_email_verified = models.BooleanField(default=False, db_index=True)
```

### 2. Redis Configuration
```python
# Increase connection pool size
CACHES = {
    'default': {
        'OPTIONS': {
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,  # Increase from default
            }
        }
    }
}
```

### 3. JWT Configuration
```python
# Use faster algorithm (HS256 vs RS256)
SIMPLE_JWT = {
    'ALGORITHM': 'HS256',  # Faster than RS256
}
```

### 4. Password Hashing
```python
# Tune Argon2 parameters for speed
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# Argon2 settings (in environment)
ARGON2_TIME_COST = 2  # Lower for faster hashing (less secure)
ARGON2_MEMORY_COST = 512  # Lower for faster hashing
```

### 5. Enable Query Optimization
```python
# Use select_related for foreign keys
user = User.objects.select_related('profile').get(email=email)

# Add query logging in development
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',  # Log slow queries
        }
    }
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  performance-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev
          poetry add pytest-benchmark locust

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 10

      - name: Run pytest-benchmark tests
        run: |
          poetry run pytest backend/apps/accounts/tests/performance/test_login_performance.py \
            --benchmark-only \
            --benchmark-save=ci_baseline

      - name: Run Locust load test
        run: |
          poetry run locust \
            -f backend/apps/accounts/tests/performance/locustfile.py \
            --host=http://localhost:8000 \
            --users 50 \
            --spawn-rate 5 \
            --run-time 1m \
            --headless \
            --csv=ci_results

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: performance-results
          path: |
            ci_results_stats.csv
            .benchmarks/
```

## Troubleshooting

### Issue: Tests timing out

**Solution:**
```bash
# Increase pytest timeout
pytest test_login_performance.py --timeout=60

# Check if services are running
docker-compose ps
curl http://localhost:8000/api/auth/login/
```

### Issue: Rate limiting preventing tests

**Solution:**
```bash
# Clear Redis cache before tests
docker-compose exec redis redis-cli FLUSHDB

# Or disable rate limiting for tests
export TESTING=True  # Check if rate_limit decorator respects this
```

### Issue: Poor performance in CI

**Reason:** CI environments typically have limited resources.

**Solution:**
- Adjust performance thresholds for CI (see test_login_performance.py - already done)
- Use smaller load profiles in CI
- Run full load tests only on staging environment

### Issue: Locust connection errors

**Solution:**
```bash
# Check backend logs
docker-compose logs backend

# Verify endpoint is accessible
curl -X POST http://localhost:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email":"loadtest@example.com","password":"LoadTest123!"}'
```

## Further Reading

- [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/)
- [Locust documentation](https://docs.locust.io/)
- [Django performance optimization](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Load testing best practices](https://docs.locust.io/en/stable/what-is-locust.html)
