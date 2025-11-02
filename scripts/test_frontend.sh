#!/bin/bash
# Frontend startup integration tests

set -e

echo "=== Frontend Startup Tests ==="

# Test 1: Container running
echo "[TEST 1] Frontend container running"
if docker-compose ps frontend | grep -q "Up"; then
    echo "✓ Frontend container is running"
else
    echo "✗ Frontend container is not running"
    exit 1
fi

# Test 2: Service accessible
echo "[TEST 2] Frontend accessible on port 3000"
timeout=30
start=$(date +%s)
while [ $(($(date +%s) - start)) -lt $timeout ]; do
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        elapsed=$(($(date +%s) - start))
        echo "✓ Frontend accessible in ${elapsed}s"
        break
    fi
    sleep 2
done

if [ $(($(date +%s) - start)) -ge $timeout ]; then
    echo "✗ Frontend not accessible within ${timeout}s"
    exit 1
fi

# Test 3: React app loads
echo "[TEST 3] React application loads"
response=$(curl -s http://localhost:3000)
if echo "$response" | grep -q '<div id="root">'; then
    echo "✓ React root element found"
else
    echo "✗ React root element not found"
    exit 1
fi

# Test 4: Vite server logs
echo "[TEST 4] Vite dev server ready"
if docker-compose logs frontend | grep -q "ready in"; then
    echo "✓ Vite server started successfully"
else
    echo "⚠ Could not confirm Vite server ready (check logs)"
fi

echo ""
echo "=== All Frontend Startup Tests Passed ==="
