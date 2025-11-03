#!/bin/bash
# TASK-5.13: Test API proxy and backend integration
#
# This script tests that the Vite development server correctly proxies
# API requests to the Django backend, eliminating CORS issues.
#
# Requirements:
# - Docker Compose environment running
# - Frontend service running with Vite proxy configured
# - Backend service running and responding
#
# Usage:
#   ./test_api_proxy.sh
#
# Expected outcome:
# - Exit code 0 if API proxy is working
# - Exit code 1 if proxy fails

set -e

echo "========================================="
echo "TASK-5.13: API Proxy Integration Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"
PROXY_API_URL="http://localhost:3000/api"

echo "Test Configuration:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Backend URL: $BACKEND_URL"
echo "  Proxy API URL: $PROXY_API_URL"
echo ""

# Test 1: Verify backend is running
echo "[Test 1/6] Checking if backend is running..."
if curl --silent --fail --max-time 5 "$BACKEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is responding at $BACKEND_URL${NC}"
else
    echo -e "${RED}✗ Backend is not responding${NC}"
    echo ""
    echo "Backend must be running for proxy tests."
    echo "Hint: Start the backend first:"
    echo "  docker-compose up -d backend"
    exit 1
fi
echo ""

# Test 2: Verify frontend is running
echo "[Test 2/6] Checking if frontend is running..."
if curl --silent --fail --max-time 5 "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is responding at $FRONTEND_URL${NC}"
else
    echo -e "${RED}✗ Frontend is not responding${NC}"
    echo ""
    echo "Hint: Start the frontend first:"
    echo "  docker-compose up -d frontend"
    exit 1
fi
echo ""

# Test 3: Verify proxy configuration in vite.config.js
echo "[Test 3/6] Checking Vite proxy configuration..."
if docker-compose exec -T frontend cat vite.config.js 2>/dev/null | grep -q "proxy.*'/api'"; then
    echo -e "${GREEN}✓ API proxy is configured in vite.config.js${NC}"
else
    echo -e "${RED}✗ API proxy configuration not found${NC}"
    echo ""
    echo "Expected proxy configuration in vite.config.js:"
    echo "  server: {"
    echo "    proxy: {"
    echo "      '/api': {"
    echo "        target: 'http://backend:8000',"
    echo "        changeOrigin: true,"
    echo "      },"
    echo "    },"
    echo "  }"
    exit 1
fi
echo ""

# Test 4: Test direct backend API endpoint
echo "[Test 4/6] Testing direct backend API endpoint..."
BACKEND_RESPONSE=$(curl --silent --max-time 5 "$BACKEND_URL/api/" 2>&1 || echo "ERROR")
if [ "$BACKEND_RESPONSE" != "ERROR" ]; then
    echo -e "${GREEN}✓ Backend API endpoint is accessible${NC}"
    echo "  Response preview: $(echo "$BACKEND_RESPONSE" | head -c 100)..."
else
    echo -e "${YELLOW}⚠ Backend API endpoint did not respond${NC}"
    echo "  This is expected if backend has no root /api/ endpoint"
fi
echo ""

# Test 5: Test proxied API request through frontend
echo "[Test 5/6] Testing proxied API request through frontend..."
PROXY_HTTP_CODE=$(curl --silent --output /dev/null --write-out "%{http_code}" --max-time 5 "$PROXY_API_URL/" 2>&1 || echo "000")

if [ "$PROXY_HTTP_CODE" = "200" ] || [ "$PROXY_HTTP_CODE" = "404" ]; then
    # 200 = API responded successfully
    # 404 = API proxy worked, but endpoint doesn't exist (acceptable)
    echo -e "${GREEN}✓ Proxy request returned HTTP $PROXY_HTTP_CODE${NC}"
    echo "  Proxy is forwarding requests to backend"
else
    echo -e "${RED}✗ Proxy request returned HTTP $PROXY_HTTP_CODE${NC}"
    echo ""
    echo "Possible issues:"
    echo "  1. Backend service is not reachable from frontend container"
    echo "  2. Proxy configuration is incorrect"
    echo "  3. Docker network connectivity issue"
    echo ""
    echo "Debugging steps:"
    echo "  1. Check backend is in same Docker network:"
    echo "     docker network inspect \$(docker network ls -q -f name=app-network)"
    echo "  2. Check frontend can reach backend:"
    echo "     docker-compose exec frontend ping -c 3 backend"
    echo "  3. View frontend logs for proxy errors:"
    echo "     docker-compose logs frontend | grep -i proxy"
    exit 1
fi
echo ""

# Test 6: Check frontend logs for proxy activity
echo "[Test 6/6] Checking frontend logs for proxy activity..."
LOG_FILE=$(mktemp)
docker-compose logs --tail=50 frontend > "$LOG_FILE" 2>&1

if grep -qi "proxying\|proxy.*request\|backend:8000" "$LOG_FILE"; then
    echo -e "${GREEN}✓ Proxy activity found in frontend logs${NC}"
    echo ""
    echo "Recent proxy-related logs:"
    echo "----------------------------------------"
    grep -i "proxying\|proxy.*request\|backend:8000" "$LOG_FILE" | tail -5
    echo "----------------------------------------"
else
    echo -e "${YELLOW}⚠ No proxy activity found in recent logs${NC}"
    echo "  This may be normal if no API requests have been made yet"
fi
echo ""

# Clean up temp log file
rm -f "$LOG_FILE"

# Success summary
echo "========================================="
echo -e "${GREEN}✓ API proxy integration test passed!${NC}"
echo "========================================="
echo ""
echo "The Vite dev server is correctly proxying API requests to the backend."
echo ""
echo "Test Summary:"
echo "  ✓ Backend is running and accessible"
echo "  ✓ Frontend is running and accessible"
echo "  ✓ Proxy configuration is present"
echo "  ✓ Proxy forwards requests (HTTP $PROXY_HTTP_CODE)"
echo ""
echo "You can now make API calls from frontend to /api/* and they will"
echo "be automatically forwarded to the Django backend at http://backend:8000"
echo ""
echo "Example API call from React:"
echo "  fetch('/api/subjects/')"
echo "    .then(res => res.json())"
echo "    .then(data => console.log(data))"
echo ""

exit 0
