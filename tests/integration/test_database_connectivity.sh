#!/bin/bash
# test_database_connectivity.sh
# Integration tests for PostgreSQL database connectivity
# Verifies database service, health checks, connections, queries, and concurrent connections

set -e

# Color output for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to print test results
print_test() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}[PASS]${NC} $test_name: $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}[FAIL]${NC} $test_name: $message"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

echo "=========================================="
echo "Database Connectivity Integration Tests"
echo "=========================================="
echo ""

# Test 1: Service is running
echo "Test 1: Verifying database service is running..."
if docker-compose ps db | grep -q "Up"; then
    print_test "Service Running" "PASS" "Database service is up and running"
else
    print_test "Service Running" "FAIL" "Database service is not running"
    echo "ERROR: Database service must be started with 'docker-compose up -d'"
    exit 1
fi

# Test 2: Health check passes
echo ""
echo "Test 2: Verifying database health check..."
HEALTH=$(docker inspect veille_tech_db --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health")
if [ "$HEALTH" = "healthy" ]; then
    print_test "Health Check" "PASS" "Database health check status: healthy"
else
    print_test "Health Check" "FAIL" "Database health check status: $HEALTH (expected: healthy)"
    echo "Hint: Wait a few seconds for health checks to stabilize, or check logs: docker-compose logs db"
    exit 1
fi

# Test 3: Connection from host (direct)
echo ""
echo "Test 3: Testing direct database connection..."
if docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db -c "SELECT 1;" > /dev/null 2>&1; then
    print_test "Direct Connection" "PASS" "Successfully connected to database from host"
else
    print_test "Direct Connection" "FAIL" "Failed to connect to database"
    echo "ERROR: Database connection failed. Check credentials in .env.backend"
    exit 1
fi

# Test 4: Query execution and PostgreSQL version
echo ""
echo "Test 4: Testing SQL query execution..."
VERSION_OUTPUT=$(docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db -t -c "SELECT version();" 2>/dev/null || echo "query-failed")
if [[ "$VERSION_OUTPUT" == *"PostgreSQL 15"* ]]; then
    print_test "Query Execution" "PASS" "Query executed successfully, PostgreSQL 15 detected"
    echo "   PostgreSQL Version: $(echo $VERSION_OUTPUT | grep -oP 'PostgreSQL \d+\.\d+')"
else
    print_test "Query Execution" "FAIL" "Unexpected PostgreSQL version or query failed"
    echo "   Output: $VERSION_OUTPUT"
    exit 1
fi

# Test 5: Connection from backend container
echo ""
echo "Test 5: Testing connection from backend container..."
# Check if backend container is running
if docker-compose ps backend | grep -q "Up"; then
    # Try to connect from backend container using DATABASE_URL
    if docker-compose exec -T backend python -c "import psycopg2; import os; conn = psycopg2.connect(os.getenv('DATABASE_URL')); conn.close(); print('Connection successful')" 2>/dev/null | grep -q "Connection successful"; then
        print_test "Backend Connection" "PASS" "Backend container can connect to database"
    else
        print_test "Backend Connection" "FAIL" "Backend container cannot connect to database"
        echo "WARNING: Backend connection failed. Check DATABASE_URL in .env.backend"
    fi
else
    echo -e "${YELLOW}[SKIP]${NC} Backend Connection: Backend container not running, skipping test"
fi

# Test 6: Connection pooling test
echo ""
echo "Test 6: Testing connection pooling..."
POOL_TEST=$(docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' ')
if [ ! -z "$POOL_TEST" ] && [ "$POOL_TEST" -gt 0 ]; then
    print_test "Connection Pooling" "PASS" "max_connections = $POOL_TEST (connection pooling supported)"
else
    print_test "Connection Pooling" "FAIL" "Could not retrieve max_connections setting"
fi

# Test 7: Concurrent connections (10+ connections)
echo ""
echo "Test 7: Testing concurrent connections (10 connections)..."
# Create a temporary SQL file for concurrent tests
TEMP_SQL="/tmp/test_concurrent_$$"
echo "SELECT pg_sleep(1); SELECT 'Connection OK';" > "$TEMP_SQL"

# Start 10 concurrent connections
CONCURRENT_SUCCESS=0
for i in {1..10}; do
    docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db -f /dev/stdin < "$TEMP_SQL" > /dev/null 2>&1 &
    PIDS[$i]=$!
done

# Wait for all connections to complete
for i in {1..10}; do
    if wait ${PIDS[$i]} 2>/dev/null; then
        CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS + 1))
    fi
done

# Cleanup
rm -f "$TEMP_SQL"

if [ "$CONCURRENT_SUCCESS" -eq 10 ]; then
    print_test "Concurrent Connections" "PASS" "Successfully handled 10 concurrent connections"
else
    print_test "Concurrent Connections" "FAIL" "Only $CONCURRENT_SUCCESS/10 concurrent connections succeeded"
fi

# Test 8: Database extensions (pgvector)
echo ""
echo "Test 8: Verifying pgvector extension..."
EXTENSIONS=$(docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db -t -c "SELECT extname FROM pg_extension WHERE extname = 'vector';" 2>/dev/null | tr -d ' ')
if [ "$EXTENSIONS" = "vector" ]; then
    print_test "pgvector Extension" "PASS" "pgvector extension is installed and available"
else
    print_test "pgvector Extension" "FAIL" "pgvector extension not found"
    echo "WARNING: pgvector extension may not be initialized. Check backend/init-db.sql"
fi

# Test 9: Data persistence (check volume)
echo ""
echo "Test 9: Verifying data volume persistence..."
VOLUME_EXISTS=$(docker volume ls | grep "veille_tech_postgres_data" || echo "")
if [ ! -z "$VOLUME_EXISTS" ]; then
    VOLUME_SIZE=$(docker volume inspect veille_tech_postgres_data --format '{{.Mountpoint}}' 2>/dev/null || echo "")
    if [ ! -z "$VOLUME_SIZE" ]; then
        print_test "Data Persistence" "PASS" "Named volume veille_tech_postgres_data exists"
    else
        print_test "Data Persistence" "FAIL" "Could not inspect volume details"
    fi
else
    print_test "Data Persistence" "FAIL" "Named volume veille_tech_postgres_data not found"
fi

# Test 10: Resource limits
echo ""
echo "Test 10: Verifying resource limits..."
MEMORY_LIMIT=$(docker inspect veille_tech_db --format='{{.HostConfig.Memory}}' 2>/dev/null || echo "0")
if [ "$MEMORY_LIMIT" -gt 0 ]; then
    MEMORY_MB=$((MEMORY_LIMIT / 1024 / 1024))
    print_test "Resource Limits" "PASS" "Memory limit configured: ${MEMORY_MB}MB"
else
    print_test "Resource Limits" "FAIL" "Memory limit not configured"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: $TESTS_TOTAL"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
else
    echo "Failed: $TESTS_FAILED"
fi
echo "=========================================="

# Exit with non-zero code if any tests failed
if [ $TESTS_FAILED -gt 0 ]; then
    echo ""
    echo -e "${RED}ERROR: Some tests failed. See details above.${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}SUCCESS: All database connectivity tests passed!${NC}"
    exit 0
fi
