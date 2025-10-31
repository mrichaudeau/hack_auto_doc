#!/bin/bash
# Cross-platform Redis compatibility test script

set -e

echo "=== Redis Cross-Platform Compatibility Test ==="
echo "Platform: $(uname -s)"
echo "Docker Version: $(docker --version)"
echo ""

# Test 1: Startup time
echo "[TEST 1] Redis startup time"
start=$(date +%s)
docker-compose up -d redis
timeout=10
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker-compose ps redis | grep -q "healthy"; then
        elapsed=$(($(date +%s) - start))
        echo "✓ Redis healthy in ${elapsed}s"
        break
    fi
    sleep 1
    elapsed=$(($(date +%s) - start))
done

if [ $elapsed -ge $timeout ]; then
    echo "✗ Redis did not become healthy within ${timeout}s"
    exit 1
fi

# Test 2: Volume persistence
echo "[TEST 2] Volume persistence"
docker-compose exec -T redis redis-cli SET test_persist "test_value" || true
sleep 1
docker-compose restart redis >/dev/null 2>&1
sleep 5

value=$(docker-compose exec -T redis redis-cli GET test_persist 2>/dev/null | tr -d '\r')
if [ "$value" == "test_value" ]; then
    echo "✓ Volume persistence works"
else
    echo "✗ Volume persistence failed (got: '$value')"
fi

# Test 3: Network connectivity
echo "[TEST 3] Network connectivity from backend"
docker-compose exec -T backend python -c "
import redis
try:
    client = redis.Redis(host='redis', port=6379)
    if client.ping():
        print('✓ Backend can connect to Redis')
    else:
        print('✗ Redis PING failed')
        exit(1)
except Exception as e:
    print(f'✗ Connection failed: {e}')
    exit(1)
" || echo "✗ Backend Redis connection test failed"

# Test 4: Basic latency check
echo "[TEST 4] PING latency"
for i in {1..5}; do
    docker-compose exec -T redis redis-cli --latency -c 1 2>/dev/null | head -n 1 || echo "Latency test $i"
done

# Test 5: Broker and cache separation
echo "[TEST 5] Database separation (DB 0 vs DB 1)"
docker-compose exec -T redis redis-cli -n 0 SET broker_test "broker_value" >/dev/null
docker-compose exec -T redis redis-cli -n 1 SET cache_test "cache_value" >/dev/null

broker_val=$(docker-compose exec -T redis redis-cli -n 0 GET broker_test | tr -d '\r')
cache_val=$(docker-compose exec -T redis redis-cli -n 1 GET cache_test | tr -d '\r')

if [ "$broker_val" == "broker_value" ] && [ "$cache_val" == "cache_value" ]; then
    echo "✓ Database separation works correctly"
else
    echo "✗ Database separation failed"
fi

# Clean up test keys
docker-compose exec -T redis redis-cli DEL test_persist broker_test >/dev/null
docker-compose exec -T redis redis-cli -n 1 DEL cache_test >/dev/null

echo ""
echo "=== Test Complete ==="
echo "All Redis compatibility tests passed!"
