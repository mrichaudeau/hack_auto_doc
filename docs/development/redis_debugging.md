# Redis CLI Debugging Guide

## Accessing Redis CLI

### Connect to Redis Container

```bash
docker-compose exec redis redis-cli
```

### Connect to Specific Database

```bash
# DB 0 (Celery Broker)
docker-compose exec redis redis-cli -n 0

# DB 1 (Application Cache)
docker-compose exec redis redis-cli -n 1
```

## Basic Commands

### Test Connection

```bash
PING
# Expected: PONG
```

### Get Redis Information

```bash
# All information
INFO

# Specific sections
INFO memory
INFO stats
INFO server
INFO clients
INFO replication
```

### Key Operations

```bash
# List all keys (use with caution in production)
KEYS *

# Get specific key pattern
KEYS techwatch:*
KEYS celery*

# Get key value
GET key_name

# Set key value
SET key_name "value"

# Delete key
DEL key_name

# Check if key exists
EXISTS key_name

# Get key type
TYPE key_name

# Get key TTL (time to live)
TTL key_name
# Returns: seconds remaining, -1 (no expiry), -2 (key doesn't exist)
```

## Celery Broker Debugging (DB 0)

### View Task Queues

```bash
# List all Celery-related keys
docker-compose exec redis redis-cli -n 0 KEYS '*celery*'

# Common Celery keys:
# - celery: default queue
# - _kombu.binding.*: routing bindings
# - celery-task-meta-*: task results
```

### Check Queue Length

```bash
# Check number of pending tasks in default queue
docker-compose exec redis redis-cli -n 0 LLEN celery

# Check specific queue
docker-compose exec redis redis-cli -n 0 LLEN priority_queue
```

### View Pending Tasks

```bash
# View all tasks in default queue (0 = start, -1 = end)
docker-compose exec redis redis-cli -n 0 LRANGE celery 0 -1

# View first 10 tasks
docker-compose exec redis redis-cli -n 0 LRANGE celery 0 9
```

### View Task Results

```bash
# List task result keys
docker-compose exec redis redis-cli -n 0 KEYS 'celery-task-meta-*'

# Get specific task result
docker-compose exec redis redis-cli -n 0 GET celery-task-meta-<task-id>
```

### Monitor Commands in Real-Time

```bash
# Monitor all commands executed on Redis (DB 0)
docker-compose exec redis redis-cli -n 0 MONITOR
```

**Press Ctrl+C to exit monitoring**

### Clear Celery Queues

```bash
# Clear default queue (careful in production!)
docker-compose exec redis redis-cli -n 0 DEL celery

# Clear all Celery keys (careful!)
docker-compose exec redis redis-cli -n 0 EVAL "return redis.call('del', unpack(redis.call('keys', 'celery*')))" 0
```

## Cache Debugging (DB 1)

### View Cached Keys

```bash
# List all cache keys
docker-compose exec redis redis-cli -n 1 KEYS '*'

# View keys with specific prefix
docker-compose exec redis redis-cli -n 1 KEYS 'techwatch:*'

# Count cache keys
docker-compose exec redis redis-cli -n 1 DBSIZE
```

### Inspect Cache Values

```bash
# Get cache value
docker-compose exec redis redis-cli -n 1 GET 'techwatch:report:123'

# Get cache TTL
docker-compose exec redis redis-cli -n 1 TTL 'techwatch:report:123'
```

### Clear Cache

```bash
# Clear all cache keys (DB 1 only)
docker-compose exec redis redis-cli -n 1 FLUSHDB

# Delete specific cache key
docker-compose exec redis redis-cli -n 1 DEL 'techwatch:report:123'

# Delete keys matching pattern
docker-compose exec redis redis-cli -n 1 EVAL "return redis.call('del', unpack(redis.call('keys', 'techwatch:report:*')))" 0
```

## Performance Monitoring

### Monitor Latency

```bash
# Monitor latency continuously
docker-compose exec redis redis-cli --latency

# Monitor latency with history (samples every 15 seconds)
docker-compose exec redis redis-cli --latency-history

# Measure intrinsic latency (how fast Redis is internally)
docker-compose exec redis redis-cli --intrinsic-latency 100
```

### Monitor Memory Usage

```bash
# Get memory information
docker-compose exec redis redis-cli INFO memory

# Get human-readable memory usage
docker-compose exec redis redis-cli INFO memory | findstr used_memory_human
docker-compose exec redis redis-cli INFO memory | findstr maxmemory_human

# Windows alternative (PowerShell)
docker-compose exec redis redis-cli INFO memory | Select-String "used_memory"
```

### Monitor Connected Clients

```bash
# List all connected clients
docker-compose exec redis redis-cli CLIENT LIST

# Count connected clients
docker-compose exec redis redis-cli CLIENT LIST | wc -l

# Get client info
docker-compose exec redis redis-cli INFO clients
```

### Check Slow Queries

```bash
# View last 10 slow queries
docker-compose exec redis redis-cli SLOWLOG GET 10

# Get slowlog length
docker-compose exec redis redis-cli SLOWLOG LEN

# Reset slowlog
docker-compose exec redis redis-cli SLOWLOG RESET
```

## Common Workflows

### Verify Celery Broker Working

**Terminal 1: Monitor Redis commands**
```bash
docker-compose exec redis redis-cli -n 0 MONITOR
```

**Terminal 2: Send test task**
```bash
docker-compose exec backend python manage.py shell
>>> from celery import current_app
>>> current_app.send_task('test_task')
```

**Expected in Terminal 1:**
- LPUSH commands (task added to queue)
- RPOP commands (worker consuming task)

### Debug Cache Hit/Miss

**Step 1: Clear cache**
```bash
docker-compose exec redis redis-cli -n 1 FLUSHDB
```

**Step 2: Monitor cache operations**
```bash
docker-compose exec redis redis-cli -n 1 MONITOR
```

**Step 3: Make API request**
- First request: Observe SET command (cache miss, value stored)
- Second request: Observe GET command (cache hit)

### Verify Data Persistence

**Step 1: Write test data**
```bash
docker-compose exec redis redis-cli -n 1 SET test_persist "test_value"
```

**Step 2: Restart Redis**
```bash
docker-compose restart redis
sleep 5
```

**Step 3: Verify data still exists**
```bash
docker-compose exec redis redis-cli -n 1 GET test_persist
# Expected: "test_value"
```

## Troubleshooting

### No Keys Found

**Problem:** KEYS * returns empty list

**Solutions:**
```bash
# Verify you're connected to correct database
SELECT 0  # Switch to DB 0
SELECT 1  # Switch to DB 1

# Check if keys exist in other database
docker-compose exec redis redis-cli -n 0 DBSIZE
docker-compose exec redis redis-cli -n 1 DBSIZE

# Check if services are actually using Redis
docker-compose logs backend | findstr redis
docker-compose logs worker | findstr redis
```

### High Memory Usage

**Problem:** Redis consuming too much memory

**Check memory stats:**
```bash
docker-compose exec redis redis-cli INFO memory
```

**Key metrics:**
```bash
# used_memory: Current memory usage
# used_memory_peak: Maximum memory usage
# maxmemory: Configured limit (should be 268435456 = 256MB)
# evicted_keys: Number of keys evicted due to maxmemory limit
```

**Solutions:**
```bash
# Check eviction policy
docker-compose exec redis redis-cli CONFIG GET maxmemory-policy
# Should be: allkeys-lru

# Verify eviction is working
docker-compose exec redis redis-cli INFO stats | findstr evicted_keys
# If increasing, eviction is working (normal)

# Manual cleanup (if needed)
docker-compose exec redis redis-cli -n 1 FLUSHDB  # Clear cache only
```

### Slow Operations

**Check slow queries:**
```bash
docker-compose exec redis redis-cli SLOWLOG GET 10
```

**Common causes:**
- KEYS * command (use SCAN instead in production)
- Large data structures (lists, sets with millions of items)
- Blocking operations (BLPOP without timeout)

**Solutions:**
```bash
# Use SCAN instead of KEYS
docker-compose exec redis redis-cli --scan --pattern 'techwatch:*'

# Check for large keys
docker-compose exec redis redis-cli --bigkeys
```

### Connection Issues

**Problem:** Cannot connect to Redis

**Check Redis is running:**
```bash
docker-compose ps redis
# Should show "Up" and "healthy"
```

**Check logs:**
```bash
docker-compose logs redis
```

**Test connection:**
```bash
docker-compose exec redis redis-cli ping
# Expected: PONG
```

**Verify network:**
```bash
# From backend container
docker-compose exec backend ping redis
docker-compose exec backend telnet redis 6379
```

## Advanced Commands

### Database Management

```bash
# List all databases and their sizes
for i in {0..15}; do echo "DB $i:"; docker-compose exec redis redis-cli -n $i DBSIZE; done

# Switch between databases (inside redis-cli)
SELECT 0
SELECT 1

# Clear current database
FLUSHDB

# Clear ALL databases (use with extreme caution!)
FLUSHALL
```

### Bulk Operations

```bash
# Delete keys matching pattern (safe way using SCAN)
docker-compose exec redis redis-cli --scan --pattern 'temp:*' | xargs docker-compose exec redis redis-cli DEL

# Rename keys in bulk
docker-compose exec redis redis-cli --scan --pattern 'old:*' | while read key; do docker-compose exec redis redis-cli RENAME "$key" "${key/old:/new:}"; done
```

### Export/Import Data

```bash
# Export keys from DB 1
docker-compose exec redis redis-cli -n 1 --rdb /data/dump.rdb

# Backup with timestamp
docker-compose exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb ./backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Performance Testing

```bash
# Benchmark Redis performance
docker-compose exec redis redis-benchmark -t set,get -n 100000 -q

# Test specific operations
docker-compose exec redis redis-benchmark -t lpush,lpop -n 10000 -q
```

## Quick Reference

### Most Used Commands

| Command | Description |
|---------|-------------|
| `PING` | Test connection |
| `KEYS pattern` | Find keys matching pattern |
| `GET key` | Get key value |
| `SET key value` | Set key value |
| `DEL key` | Delete key |
| `TTL key` | Get key expiration time |
| `DBSIZE` | Count keys in current database |
| `FLUSHDB` | Clear current database |
| `INFO` | Get Redis server info |
| `MONITOR` | Monitor real-time commands |
| `CLIENT LIST` | List connected clients |

### Database Numbers

| DB | Purpose | Description |
|----|---------|-------------|
| 0 | Celery Broker | Task queues, results, routing |
| 1 | Application Cache | API responses, sessions |

### Connection Quick Tips

```bash
# Quick PING test
docker-compose exec redis redis-cli ping

# Quick memory check
docker-compose exec redis redis-cli INFO memory | findstr used_memory_human

# Quick queue length check
docker-compose exec redis redis-cli -n 0 LLEN celery

# Quick cache count
docker-compose exec redis redis-cli -n 1 DBSIZE
```

## Resources

- [Redis Commands Documentation](https://redis.io/commands)
- [Redis CLI Documentation](https://redis.io/docs/ui/cli/)
- [Celery Redis Broker](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/redis.html)
- [Django Redis Cache](https://github.com/jazzband/django-redis)

---

**Last Updated:** 2025-01-29
**Maintainer:** DevOps Team
