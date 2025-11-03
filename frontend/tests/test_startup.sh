#!/bin/bash
# TASK-5.11: Test frontend service startup
#
# This script tests that the frontend service starts correctly and responds
# to health check requests.
#
# Requirements:
# - Docker Compose environment running
# - Frontend service defined in docker-compose.yml
#
# Usage:
#   ./test_startup.sh
#
# Expected outcome:
# - Exit code 0 if frontend is healthy
# - Exit code 1 if startup fails

set -e

echo "========================================="
echo "TASK-5.11: Frontend Service Startup Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
MAX_RETRIES=30
RETRY_INTERVAL=2
FRONTEND_URL="http://localhost:3000"

echo "Test Configuration:"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Max retries: $MAX_RETRIES"
echo "  Retry interval: ${RETRY_INTERVAL}s"
echo ""

# Function to check if frontend is responding
check_frontend() {
    if curl --silent --fail --max-time 5 "$FRONTEND_URL" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Test 1: Check if frontend container is running
echo "[Test 1/4] Checking if frontend container is running..."
if docker-compose ps frontend | grep -q "Up"; then
    echo -e "${GREEN}✓ Frontend container is running${NC}"
else
    echo -e "${RED}✗ Frontend container is not running${NC}"
    echo ""
    echo "Container status:"
    docker-compose ps frontend
    echo ""
    echo "Hint: Start the frontend with:"
    echo "  docker-compose up -d frontend"
    exit 1
fi
echo ""

# Test 2: Wait for frontend to be ready
echo "[Test 2/4] Waiting for frontend to be ready..."
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if check_frontend; then
        echo -e "${GREEN}✓ Frontend is responding (attempt $((RETRY_COUNT + 1)))${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}✗ Frontend did not respond after $MAX_RETRIES attempts${NC}"
            echo ""
            echo "Frontend logs:"
            docker-compose logs --tail=50 frontend
            exit 1
        fi
        echo -e "${YELLOW}⏳ Waiting for frontend... (attempt $RETRY_COUNT/$MAX_RETRIES)${NC}"
        sleep $RETRY_INTERVAL
    fi
done
echo ""

# Test 3: Verify HTTP response
echo "[Test 3/4] Verifying HTTP response..."
HTTP_CODE=$(curl --silent --output /dev/null --write-out "%{http_code}" --max-time 5 "$FRONTEND_URL")
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Frontend returned HTTP $HTTP_CODE (OK)${NC}"
else
    echo -e "${RED}✗ Frontend returned HTTP $HTTP_CODE (Expected 200)${NC}"
    exit 1
fi
echo ""

# Test 4: Verify HTML content contains React
echo "[Test 4/4] Verifying HTML content contains React..."
RESPONSE=$(curl --silent --max-time 5 "$FRONTEND_URL")
if echo "$RESPONSE" | grep -q "root"; then
    echo -e "${GREEN}✓ HTML contains root element (React mount point)${NC}"
else
    echo -e "${RED}✗ HTML does not contain expected React root element${NC}"
    echo ""
    echo "Response preview:"
    echo "$RESPONSE" | head -20
    exit 1
fi
echo ""

# Success summary
echo "========================================="
echo -e "${GREEN}✓ All frontend startup tests passed!${NC}"
echo "========================================="
echo ""
echo "Frontend service is running correctly at $FRONTEND_URL"
echo ""

# Optional: Display service info
echo "Service Information:"
echo "  Container: $(docker-compose ps -q frontend)"
echo "  Health: $(docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q frontend) 2>/dev/null || echo 'N/A')"
echo "  Uptime: $(docker inspect --format='{{.State.StartedAt}}' $(docker-compose ps -q frontend) 2>/dev/null || echo 'N/A')"
echo ""

exit 0
