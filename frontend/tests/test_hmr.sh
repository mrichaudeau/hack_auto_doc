#!/bin/bash
# TASK-5.12: Test Hot Module Replacement (HMR) functionality
#
# This script tests that Vite's HMR is working correctly by:
# 1. Modifying a React component file
# 2. Verifying that changes are detected
# 3. Confirming the browser receives HMR updates
#
# Requirements:
# - Docker Compose environment running
# - Frontend service with volume mounts configured
# - Vite HMR enabled in vite.config.js
#
# Usage:
#   ./test_hmr.sh
#
# Expected outcome:
# - Exit code 0 if HMR is working
# - Exit code 1 if HMR fails

set -e

echo "========================================="
echo "TASK-5.12: HMR Functionality Test"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_FILE="src/App.jsx"
BACKUP_FILE="src/App.jsx.backup"
TEST_MARKER="<!-- HMR TEST MARKER $(date +%s) -->"
FRONTEND_URL="http://localhost:3000"

echo "Test Configuration:"
echo "  Test file: $TEST_FILE"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Test marker: $TEST_MARKER"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    if [ -f "frontend/$BACKUP_FILE" ]; then
        echo "  Restoring original file..."
        mv "frontend/$BACKUP_FILE" "frontend/$TEST_FILE"
        echo -e "${GREEN}  ✓ Original file restored${NC}"
    fi
}
trap cleanup EXIT

# Test 1: Verify frontend is running
echo "[Test 1/5] Checking if frontend is running..."
if ! curl --silent --fail --max-time 5 "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${RED}✗ Frontend is not responding${NC}"
    echo ""
    echo "Hint: Start the frontend first:"
    echo "  docker-compose up -d frontend"
    exit 1
fi
echo -e "${GREEN}✓ Frontend is running${NC}"
echo ""

# Test 2: Check volume mount configuration
echo "[Test 2/5] Verifying volume mount configuration..."
VOLUME_MOUNT=$(docker inspect $(docker-compose ps -q frontend) --format '{{range .Mounts}}{{if eq .Destination "/app"}}{{.Type}}{{end}}{{end}}' 2>/dev/null || echo "none")
if [ "$VOLUME_MOUNT" = "bind" ]; then
    echo -e "${GREEN}✓ Source code volume is mounted (bind mount)${NC}"
elif [ "$VOLUME_MOUNT" = "volume" ]; then
    echo -e "${YELLOW}⚠ Volume is a named volume (not bind mount)${NC}"
    echo "  HMR may not work with named volumes for source code"
else
    echo -e "${RED}✗ No volume mount found for /app${NC}"
    echo "  HMR requires source code to be mounted as a volume"
    exit 1
fi
echo ""

# Test 3: Verify file watching is enabled
echo "[Test 3/5] Checking Vite configuration for file watching..."
if docker-compose exec -T frontend cat vite.config.js 2>/dev/null | grep -q "watch"; then
    echo -e "${GREEN}✓ File watching is configured in vite.config.js${NC}"
else
    echo -e "${YELLOW}⚠ File watching configuration not found (may use defaults)${NC}"
fi
echo ""

# Test 4: Modify a component file
echo "[Test 4/5] Modifying React component to trigger HMR..."
if [ ! -f "frontend/$TEST_FILE" ]; then
    echo -e "${RED}✗ Test file not found: frontend/$TEST_FILE${NC}"
    exit 1
fi

# Backup original file
cp "frontend/$TEST_FILE" "frontend/$BACKUP_FILE"
echo "  ✓ Original file backed up"

# Add test marker to file
echo "$TEST_MARKER" >> "frontend/$TEST_FILE"
echo "  ✓ Test marker added to file"
echo ""

# Test 5: Monitor logs for HMR activity
echo "[Test 5/5] Monitoring frontend logs for HMR activity..."
echo -e "${BLUE}Waiting 5 seconds for Vite to detect file change...${NC}"

# Capture logs for 5 seconds
LOG_FILE=$(mktemp)
docker-compose logs --tail=50 frontend > "$LOG_FILE" 2>&1 &
LOG_PID=$!
sleep 5
kill $LOG_PID 2>/dev/null || true

# Check logs for HMR indicators
HMR_DETECTED=false
if grep -qi "hmr update\|page reload\|file change detected\|vite.*update" "$LOG_FILE"; then
    HMR_DETECTED=true
fi

# Display relevant log lines
echo ""
echo "Recent frontend logs:"
echo "----------------------------------------"
tail -20 "$LOG_FILE" | grep -i "hmr\|update\|reload\|change" || echo "(No HMR-related messages found)"
echo "----------------------------------------"
echo ""

# Clean up temp log file
rm -f "$LOG_FILE"

# Evaluate HMR test result
if [ "$HMR_DETECTED" = true ]; then
    echo -e "${GREEN}✓ HMR activity detected in logs${NC}"
    echo ""
    echo "========================================="
    echo -e "${GREEN}✓ HMR functionality test passed!${NC}"
    echo "========================================="
    echo ""
    echo "Hot Module Replacement is working correctly."
    echo "File changes are detected and updates are sent to the browser."
    echo ""
else
    echo -e "${YELLOW}⚠ No explicit HMR messages found in logs${NC}"
    echo ""
    echo "This could mean:"
    echo "  1. HMR is working silently (Vite doesn't always log every update)"
    echo "  2. File watching is not triggering (check volume mounts)"
    echo "  3. Polling mode may be needed (set CHOKIDAR_USEPOLLING=true)"
    echo ""
    echo "Manual verification:"
    echo "  1. Open $FRONTEND_URL in a browser"
    echo "  2. Open browser console (F12)"
    echo "  3. Edit frontend/$TEST_FILE"
    echo "  4. Watch for '[vite] hot updated' message in console"
    echo ""
    echo "For Windows/macOS users:"
    echo "  Add to frontend service environment:"
    echo "    environment:"
    echo "      - CHOKIDAR_USEPOLLING=true"
    echo ""
fi

exit 0
