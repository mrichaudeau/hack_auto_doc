#!/bin/bash
# API proxy integration tests

set -e

echo "=== API Proxy Tests ==="

# Test 1: Health endpoint via proxy
echo "[TEST 1] API health endpoint via proxy"
response=$(curl -s http://localhost:3000/api/health/)
if echo "$response" | grep -q '"status"'; then
    echo "✓ API proxy forwarding works"
    echo "  Response: $response"
else
    echo "✗ API proxy not working"
    echo "  Response: $response"
    exit 1
fi

# Test 2: Proxy latency
echo "[TEST 2] Proxy latency measurement"
start=$(date +%s%3N 2>/dev/null || echo $(($(date +%s) * 1000)))
curl -s http://localhost:3000/api/health/ > /dev/null
end=$(date +%s%3N 2>/dev/null || echo $(($(date +%s) * 1000)))
latency=$((end - start))
echo "  Proxy latency: ${latency}ms"
if [ $latency -lt 100 ]; then
    echo "✓ Latency acceptable (< 100ms)"
else
    echo "⚠ Latency high: ${latency}ms"
fi

# Test 3: Backend connectivity
echo "[TEST 3] Backend service connectivity"
if docker-compose ps backend | grep -q "Up"; then
    echo "✓ Backend service is running"
else
    echo "✗ Backend service is not running"
    exit 1
fi

echo ""
echo "=== All Proxy Tests Passed ==="
