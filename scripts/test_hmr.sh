#!/bin/bash
# Hot Module Replacement test script

set -e

echo "=== HMR Functionality Test ==="

# Backup original file
cp frontend/src/App.jsx frontend/src/App.jsx.backup

# Modify file
echo "[TEST] Modifying App.jsx..."
sed -i.bak 's/Plateforme de Veille Technologique IA/HMR Test - Modified/g' frontend/src/App.jsx 2>/dev/null || \
  sed -i '' 's/Plateforme de Veille Technologique IA/HMR Test - Modified/g' frontend/src/App.jsx

# Wait for HMR
echo "[TEST] Waiting for HMR update (max 5 seconds)..."
sleep 3

# Check logs for HMR message
if docker-compose logs --tail=20 frontend | grep -q "hot updated\|hmr update"; then
    echo "✓ HMR detected and processed file change"
else
    echo "⚠ HMR message not found in logs"
fi

# Verify change reflected (would need headless browser for full test)
echo "[TEST] Verify change at http://localhost:3000 (manual check)"

# Restore original
echo "[TEST] Restoring original file..."
mv frontend/src/App.jsx.backup frontend/src/App.jsx
rm -f frontend/src/App.jsx.bak

sleep 2
echo ""
echo "✓ HMR test complete - Check browser for instant updates"
