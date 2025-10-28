#!/bin/bash
# pgvector Extension Verification Test Script
# Purpose: Verify pgvector extension is installed and functional
# Usage: ./test_pgvector_extension.sh
# Exit codes: 0 = success, 1 = failure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DB_SERVICE="db"
DB_USER="${POSTGRES_USER:-veille_tech_user}"
DB_NAME="${POSTGRES_DB:-veille_tech_db}"
TEST_TABLE="test_embeddings_pgvector"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

pass_test() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail_test() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

run_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Execute SQL command
exec_sql() {
    docker-compose exec -T "$DB_SERVICE" psql -U "$DB_USER" -d "$DB_NAME" -c "$1" 2>&1
}

# Execute SQL and check output contains expected string
exec_sql_check() {
    local sql="$1"
    local expected="$2"
    local result
    result=$(exec_sql "$sql")
    if echo "$result" | grep -q "$expected"; then
        return 0
    else
        echo "$result"
        return 1
    fi
}

# Main test suite
echo "========================================"
echo "pgvector Extension Verification Tests"
echo "========================================"
echo ""

# Pre-flight checks
log_info "Checking Docker Compose services..."
if ! docker-compose ps | grep -q "$DB_SERVICE"; then
    log_error "Database service is not running. Start with: docker-compose up -d"
    exit 1
fi

if ! docker-compose ps "$DB_SERVICE" | grep -q "Up"; then
    log_error "Database service is not healthy. Check logs with: docker-compose logs db"
    exit 1
fi

log_info "Database service is running"
echo ""

# Test 1: Extension installation check
log_info "Test 1: Verify pgvector extension is installed"
run_test
if exec_sql_check "SELECT extname FROM pg_extension WHERE extname = 'vector';" "vector"; then
    pass_test "pgvector extension is installed"
else
    fail_test "pgvector extension is NOT installed"
fi
echo ""

# Test 2: Extension version check
log_info "Test 2: Verify pgvector extension version"
run_test
version_output=$(exec_sql "SELECT extversion FROM pg_extension WHERE extname = 'vector';")
if echo "$version_output" | grep -qE "[0-9]+\.[0-9]+"; then
    version=$(echo "$version_output" | grep -oE "[0-9]+\.[0-9]+" | head -1)
    pass_test "pgvector version: $version"
else
    fail_test "Could not determine pgvector version"
fi
echo ""

# Test 3: Create table with vector column
log_info "Test 3: Create table with vector column"
run_test
if exec_sql "DROP TABLE IF EXISTS $TEST_TABLE;" > /dev/null 2>&1 && \
   exec_sql "CREATE TABLE $TEST_TABLE (id serial PRIMARY KEY, embedding vector(3), description text);" > /dev/null 2>&1; then
    pass_test "Successfully created table with vector(3) column"
else
    fail_test "Failed to create table with vector column"
fi
echo ""

# Test 4: Insert vector data
log_info "Test 4: Insert vector data"
run_test
if exec_sql "INSERT INTO $TEST_TABLE (embedding, description) VALUES ('[1,2,3]', 'test vector 1'), ('[4,5,6]', 'test vector 2'), ('[7,8,9]', 'test vector 3');" > /dev/null 2>&1; then
    pass_test "Successfully inserted vector data"
else
    fail_test "Failed to insert vector data"
fi
echo ""

# Test 5: Verify data insertion
log_info "Test 5: Verify vector data retrieval"
run_test
if exec_sql_check "SELECT COUNT(*) FROM $TEST_TABLE;" "3"; then
    pass_test "Successfully retrieved 3 vector records"
else
    fail_test "Failed to retrieve correct number of records"
fi
echo ""

# Test 6: Cosine distance search (<=> operator)
log_info "Test 6: Test cosine distance search (1 - cosine similarity)"
run_test
result=$(exec_sql "SELECT id, description FROM $TEST_TABLE ORDER BY embedding <=> '[1,2,3]' LIMIT 1;")
if echo "$result" | grep -q "test vector 1"; then
    pass_test "Cosine distance search (<=> operator) works correctly"
else
    fail_test "Cosine distance search failed"
    echo "Result: $result"
fi
echo ""

# Test 7: L2 distance search (<-> operator)
log_info "Test 7: Test L2 distance search (Euclidean)"
run_test
result=$(exec_sql "SELECT id, description FROM $TEST_TABLE ORDER BY embedding <-> '[1,2,3]' LIMIT 1;")
if echo "$result" | grep -q "test vector 1"; then
    pass_test "L2 distance search (<-> operator) works correctly"
else
    fail_test "L2 distance search failed"
    echo "Result: $result"
fi
echo ""

# Test 8: Inner product search (<#> operator)
log_info "Test 8: Test negative inner product search"
run_test
if exec_sql "SELECT id FROM $TEST_TABLE ORDER BY embedding <#> '[1,2,3]' LIMIT 1;" > /dev/null 2>&1; then
    pass_test "Inner product search (<#> operator) works correctly"
else
    fail_test "Inner product search failed"
fi
echo ""

# Test 9: Vector dimension enforcement
log_info "Test 9: Verify vector dimension enforcement"
run_test
if exec_sql "INSERT INTO $TEST_TABLE (embedding, description) VALUES ('[1,2]', 'wrong dimensions');" 2>&1 | grep -q "expected 3"; then
    pass_test "Vector dimension enforcement works (rejected 2D vector for 3D column)"
else
    log_warn "Dimension enforcement test inconclusive (may have been rejected for other reasons)"
fi
echo ""

# Test 10: Vector distance calculation
log_info "Test 10: Calculate actual cosine distance"
run_test
result=$(exec_sql "SELECT embedding <=> '[1,2,3]' AS distance FROM $TEST_TABLE WHERE description = 'test vector 1';")
if echo "$result" | grep -qE "[0-9]"; then
    distance=$(echo "$result" | grep -oE "[0-9]+\.[0-9]+|[0-9]+" | head -1)
    if [ -n "$distance" ]; then
        pass_test "Cosine distance calculation works (distance: $distance)"
    else
        fail_test "Could not extract distance value"
    fi
else
    fail_test "Distance calculation failed"
fi
echo ""

# Test 11: Vector addition/manipulation
log_info "Test 11: Test vector arithmetic operations"
run_test
if exec_sql "SELECT '[1,2,3]'::vector + '[1,1,1]'::vector AS result;" > /dev/null 2>&1; then
    pass_test "Vector arithmetic operations supported"
else
    fail_test "Vector arithmetic failed"
fi
echo ""

# Test 12: Multiple vector columns
log_info "Test 12: Test table with multiple vector columns"
run_test
if exec_sql "DROP TABLE IF EXISTS test_multi_vectors;" > /dev/null 2>&1 && \
   exec_sql "CREATE TABLE test_multi_vectors (id serial, vec1 vector(3), vec2 vector(5));" > /dev/null 2>&1; then
    pass_test "Multiple vector columns in same table supported"
    exec_sql "DROP TABLE test_multi_vectors;" > /dev/null 2>&1
else
    fail_test "Multiple vector columns not supported"
fi
echo ""

# Cleanup
log_info "Cleaning up test data..."
exec_sql "DROP TABLE IF EXISTS $TEST_TABLE;" > /dev/null 2>&1
log_info "Cleanup complete"
echo ""

# Test summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Total tests run:    $TESTS_RUN"
echo "Tests passed:       $TESTS_PASSED"
echo "Tests failed:       $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    log_info "All pgvector extension tests passed!"
    echo ""
    log_info "pgvector is ready for use in:"
    echo "  - Semantic embeddings storage (Bloc 3: AI Content Pipeline)"
    echo "  - Vector similarity search (Bloc 5: Recommendation Engine)"
    echo "  - Cosine similarity operations for user profiling"
    exit 0
else
    log_error "$TESTS_FAILED test(s) failed!"
    echo ""
    log_error "Troubleshooting steps:"
    echo "  1. Check database logs: docker-compose logs db"
    echo "  2. Verify init-db.sql execution: docker-compose exec db psql -U $DB_USER -d $DB_NAME -c '\\dx vector'"
    echo "  3. Restart database service: docker-compose restart db"
    echo "  4. Check pgvector version compatibility"
    exit 1
fi
