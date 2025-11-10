# Redis Configuration for Rate Limiting

## Overview

This document describes the Redis configuration used for rate limiting in the authentication system, specifically for protecting the login endpoint from brute force attacks (US-3: Standard User Login).

## Architecture

### Redis Service

**Location:** `docker-compose.yml` (lines 29-57)

```yaml
redis:
  image: redis:latest
  container_name: redis
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
```

**Key Configuration:**
- **Memory Limit:** 256MB
- **Eviction Policy:** `allkeys-lru` (Least Recently Used)
- **Port:** 6379 (internal network only)
- **Health Check:** Redis PING command every 10 seconds
- **Data Persistence:** Named volume `redis_data`

### Database Allocation

Redis uses multiple databases (0-15 by default):

- **DB 0:** Celery broker and task results
- **DB 1:** Application cache and rate limiting (configured below)
- **DB 2-15:** Available for future use

### Django Cache Configuration

**Location:** `backend/veille_tech/settings/base.py` (lines 138-154)

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',  # DB 1 for caching
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'techwatch',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}
```

**Key Features:**
- **Backend:** `django-redis` with RedisCache backend
- **Connection Pool:** Up to 50 concurrent connections
- **Retry Logic:** Automatic retry on timeout
- **Timeouts:** 5 seconds for connect and socket operations
- **Key Prefix:** `techwatch` (prevents key collisions)

### Rate Limiting Configuration

**Location:** `backend/veille_tech/settings/base.py` (lines 156-160)

```python
RATELIMIT_USE_CACHE = 'default'  # Use default Redis cache (DB 1)
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_VIEW = 'veille_tech.views.ratelimit_error_view'
```

**Dependencies:**
- **Package:** `django-ratelimit` v4.1+ (in `pyproject.toml`)
- **Cache Backend:** Uses the `default` cache configured above
- **Environment Variable:** `RATELIMIT_ENABLE` (default: `True`)

## Rate Limiting for Login Endpoint

### Implementation (TASK-3.3)

The login endpoint will use Redis-based rate limiting to prevent brute force attacks:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/5m', block=True, method='POST')
def login_view(request):
    # Login logic here
    pass
```

**Rate Limit Parameters:**
- **Key:** IP address (`key='ip'`)
- **Rate:** 5 attempts per 5 minutes (`rate='5/5m'`)
- **Action:** Block request if limit exceeded (`block=True`)
- **Method:** Only POST requests (`method='POST'`)

### How It Works

1. **Request Arrives:** Client makes POST request to `/api/auth/login/`
2. **Rate Limit Check:**
   - Decorator extracts client IP address
   - Checks Redis for key: `techwatch:rl:ip:{ip_address}`
   - Increments counter with 5-minute TTL
3. **Decision:**
   - **Under Limit:** Request proceeds to login logic
   - **Over Limit:** Returns 429 Too Many Requests
4. **Cleanup:** Redis automatically removes expired keys (TTL)

### Redis Key Structure

```
techwatch:rl:ip:192.168.1.100  →  Counter: 3, TTL: 180s
techwatch:rl:ip:10.0.0.5       →  Counter: 5, TTL: 120s (BLOCKED)
```

## Performance Characteristics

### Memory Usage

**Per Rate Limit Key:**
- Key size: ~40 bytes (prefix + IP address)
- Value size: ~8 bytes (counter)
- TTL overhead: ~8 bytes
- **Total per IP:** ~56 bytes

**Capacity:**
- 256MB Redis memory limit
- ~4.5 million concurrent rate limit keys
- Realistically: ~100,000 concurrent IPs with other cache data

### Latency

- **Cache GET:** < 1ms (local network)
- **Cache INCR:** < 1ms (local network)
- **Total overhead:** < 2ms per request

### High Availability

**Connection Pooling:**
- 50 max connections shared across all backend instances
- Automatic reconnection on failure
- Retry logic for transient errors

**Graceful Degradation:**
- If Redis is unavailable, rate limiting fails open (allows requests)
- Monitor Redis health via healthcheck in docker-compose.yml

## Testing

### Manual Testing

```bash
# Connect to Redis CLI
docker exec -it redis redis-cli

# Select application cache database
SELECT 1

# Check rate limit keys
KEYS techwatch:rl:*

# View specific rate limit counter
GET techwatch:rl:ip:192.168.1.100

# Check TTL (time to live)
TTL techwatch:rl:ip:192.168.1.100

# Clear all rate limit keys (for testing)
KEYS techwatch:rl:* | xargs redis-cli -n 1 DEL
```

### Automated Testing

See `backend/apps/accounts/tests/test_rate_limiting.py` (TASK-3.15) for:
- Unit tests for rate limit decorator
- Integration tests for login endpoint rate limiting
- Tests for distributed rate limiting across multiple instances

## Monitoring

### Key Metrics to Monitor

1. **Redis Memory Usage:**
   ```bash
   docker exec redis redis-cli INFO memory
   ```

2. **Connection Count:**
   ```bash
   docker exec redis redis-cli INFO clients
   ```

3. **Rate Limit Hits:**
   ```bash
   docker exec redis redis-cli -n 1 KEYS "techwatch:rl:*" | wc -l
   ```

4. **Blocked IPs:**
   ```bash
   docker exec redis redis-cli -n 1 KEYS "techwatch:rl:*" | \
     xargs redis-cli -n 1 MGET | grep "^5$" | wc -l
   ```

### Health Checks

- **Docker:** `docker exec redis redis-cli ping` (should return `PONG`)
- **Django:** Test cache access in worker healthcheck (line 156 in docker-compose.yml)

## Environment Variables

### Backend (.env.backend)

```bash
# Redis Cache URL
REDIS_CACHE_URL=redis://redis:6379/1

# Celery Broker (separate DB)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Rate Limiting
RATELIMIT_ENABLE=True  # Set to False to disable in tests
```

## Troubleshooting

### Issue: Rate Limiting Not Working

**Symptoms:** Login endpoint allows unlimited requests

**Diagnosis:**
1. Check Redis is running: `docker ps | grep redis`
2. Check Redis connectivity: `docker exec backend redis-cli -h redis ping`
3. Check `RATELIMIT_ENABLE` is `True` in settings
4. Check decorator is applied to login view

**Solution:**
- Restart Redis: `docker-compose restart redis`
- Check logs: `docker-compose logs redis`

### Issue: Too Many Connections

**Symptoms:** `ConnectionError: max_connections exceeded`

**Diagnosis:**
```bash
docker exec redis redis-cli CLIENT LIST | wc -l
```

**Solution:**
- Increase `max_connections` in CACHES settings (currently 50)
- Check for connection leaks in application code

### Issue: High Memory Usage

**Symptoms:** Redis memory near 256MB limit

**Diagnosis:**
```bash
docker exec redis redis-cli INFO memory | grep used_memory_human
docker exec redis redis-cli -n 1 INFO keyspace
```

**Solution:**
- Monitor eviction stats: `docker exec redis redis-cli INFO stats | grep evicted`
- LRU policy will automatically evict old keys
- Consider increasing maxmemory in docker-compose.yml

## Security Considerations

1. **Network Isolation:**
   - Redis only accessible via internal `app-network`
   - No external port exposure (6379 not published)

2. **IP-Based Rate Limiting:**
   - Prevents brute force from single IP
   - Does NOT prevent distributed attacks (multiple IPs)
   - Consider adding email-based rate limiting for additional protection

3. **Key Expiration:**
   - All rate limit keys have TTL (5 minutes)
   - Prevents indefinite storage of rate limit data
   - No manual cleanup required

4. **Data Persistence:**
   - Rate limit data persists across container restarts
   - Consider adding `FLUSHDB` on production deployment

## References

- **Django-Redis Documentation:** https://github.com/jazzband/django-redis
- **Django-Ratelimit Documentation:** https://django-ratelimit.readthedocs.io/
- **Redis Best Practices:** https://redis.io/docs/management/optimization/

---

**Related Tasks:**
- TASK-3.3: Implement Redis-Based Rate Limiting
- TASK-3.5: Implement Login API Endpoint (uses rate limiting)
- TASK-3.15: Unit Tests for Rate Limiting

**Last Updated:** 2025-01-09
