# Integration Tests

This directory contains integration tests for the Docker Compose service orchestration.

## Database Connectivity Tests

Comprehensive tests to verify PostgreSQL database connectivity, health checks, concurrent connections, and basic operations.

### Shell Script Tests (`test_database_connectivity.sh`)

**Purpose:** Bash-based tests that verify database service connectivity and health using Docker Compose.

**Requirements:**
- Docker and Docker Compose running
- Database service healthy (`docker-compose ps db` shows "Up (healthy)")
- `.env.backend` file configured with database credentials

**Running the tests:**

```bash
# Make the script executable (Linux/macOS)
chmod +x tests/integration/test_database_connectivity.sh

# Run the tests
./tests/integration/test_database_connectivity.sh

# Or run with bash directly (Windows Git Bash)
bash tests/integration/test_database_connectivity.sh
```

**What it tests:**
1. Service Running - Verifies database service is up
2. Health Check - Validates health check status is "healthy"
3. Direct Connection - Tests connection from host to database
4. Query Execution - Executes SQL query and verifies PostgreSQL 15
5. Backend Connection - Tests connection from backend container (if running)
6. Connection Pooling - Verifies max_connections configuration
7. Concurrent Connections - Tests 10 concurrent connections
8. pgvector Extension - Verifies pgvector extension is installed
9. Data Persistence - Checks named volume exists
10. Resource Limits - Validates memory limits are configured

**Expected output:**
```
==========================================
Database Connectivity Integration Tests
==========================================

Test 1: Verifying database service is running...
[PASS] Service Running: Database service is up and running

Test 2: Verifying database health check...
[PASS] Health Check: Database health check status: healthy

... (more tests)

==========================================
Test Summary
==========================================
Total Tests: 9
Passed: 9
Failed: 0
==========================================

SUCCESS: All database connectivity tests passed!
```

**Exit codes:**
- `0`: All tests passed
- `1`: One or more tests failed

### Python Tests (`test_database_connectivity.py`)

**Purpose:** Python-based tests using pytest for programmatic database connectivity verification.

**Requirements:**
- Python 3.13+
- psycopg2-binary package
- pytest

**Installation:**

```bash
# Install required packages
pip install psycopg2-binary pytest

# Or using Poetry (from backend directory)
cd backend
poetry add --group dev psycopg2-binary pytest
```

**Running the tests:**

The Python tests require database connectivity. Since the database port is not exposed to the host by default (for security), you have two options:

**Option 1: Run from within the backend container (RECOMMENDED):**

```bash
# Install test dependencies in backend container (once backend is set up)
docker-compose exec backend pip install psycopg2-binary pytest

# Run all tests with verbose output
docker-compose exec backend pytest tests/integration/test_database_connectivity.py -v

# Run specific test class
docker-compose exec backend pytest tests/integration/test_database_connectivity.py::TestDatabaseConnection -v

# Run standalone (without pytest)
docker-compose exec backend python tests/integration/test_database_connectivity.py
```

**Option 2: Expose database port temporarily (for local development only):**

1. Add port mapping to `docker-compose.yml` db service:
   ```yaml
   ports:
     - "5432:5432"
   ```

2. Restart database service:
   ```bash
   docker-compose restart db
   ```

3. Run tests from host:
   ```bash
   # Install packages locally
   pip install psycopg2-binary pytest

   # Set environment variables (from .env.backend)
   export DATABASE_URL=postgresql://veille_tech_user:your_password@localhost:5432/veille_tech_db

   # Run tests
   pytest tests/integration/test_database_connectivity.py -v
   ```

**IMPORTANT:** Never expose database ports in production. Remove port mapping after testing.

**Test classes:**

1. **TestDatabaseConnection**: Basic connection tests
   - Connection establishment
   - Context manager usage

2. **TestDatabaseQueries**: Query execution tests
   - Simple SELECT queries
   - PostgreSQL version verification
   - Database and user verification
   - Table creation and cleanup

3. **TestConnectionPooling**: Connection pool tests
   - Pool creation and management
   - max_connections configuration

4. **TestConcurrentConnections**: Concurrent access tests
   - 10+ concurrent connections
   - Concurrent transactions

5. **TestPgvectorExtension**: pgvector functionality tests
   - Extension installation
   - Vector data type availability
   - Vector operations (cosine distance)

6. **TestDatabasePerformance**: Performance validation
   - Connection time (<1 second)
   - Query performance (<100ms)

**Expected output:**

```
============================= test session starts ==============================
platform win32 -- Python 3.13.0, pytest-8.0.0, pluggy-1.4.0
collected 16 items

tests/integration/test_database_connectivity.py::TestDatabaseConnection::test_connection_succeeds PASSED [  6%]
tests/integration/test_database_connectivity.py::TestDatabaseConnection::test_connection_with_context_manager PASSED [ 12%]
... (more tests)
tests/integration/test_database_connectivity.py::TestDatabasePerformance::test_query_performance PASSED [100%]

=================== 16 tests passed in 5.42s ===================
```

## pgvector Extension Tests

Comprehensive tests to verify the pgvector extension is properly installed and functional.

### Shell Script Tests (`test_pgvector_extension.sh`)

**Purpose:** Bash-based tests that verify pgvector functionality using Docker Compose.

**Requirements:**
- Docker and Docker Compose running
- Database service healthy (`docker-compose ps db` shows "Up (healthy)")

**Running the tests:**

```bash
# Make the script executable (Linux/macOS)
chmod +x tests/integration/test_pgvector_extension.sh

# Run the tests
./tests/integration/test_pgvector_extension.sh

# Or run with bash directly (Windows Git Bash)
bash tests/integration/test_pgvector_extension.sh
```

**What it tests:**
1. Extension installation verification
2. Extension version check
3. Vector column creation (vector(3) type)
4. Vector data insertion
5. Data retrieval verification
6. Cosine distance search (`<=>` operator)
7. L2 distance search (`<->` operator)
8. Inner product search (`<#>` operator)
9. Vector dimension enforcement
10. Distance calculation accuracy
11. Vector arithmetic operations
12. Multiple vector columns support

**Expected output:**
```
========================================
pgvector Extension Verification Tests
========================================

[INFO] Checking Docker Compose services...
[INFO] Database service is running

[INFO] Test 1: Verify pgvector extension is installed
[PASS] pgvector extension is installed

[INFO] Test 2: Verify pgvector extension version
[PASS] pgvector version: 0.5.1

... (more tests)

========================================
Test Summary
========================================
Total tests run:    12
Tests passed:       12
Tests failed:       0

[INFO] All pgvector extension tests passed!
```

**Exit codes:**
- `0`: All tests passed
- `1`: One or more tests failed

### Python Tests (`test_pgvector_extension.py`)

**Purpose:** Python-based tests using pytest for programmatic verification.

**Requirements:**
- Python 3.13+
- psycopg2-binary package
- pgvector package (optional but recommended)
- pytest

**Installation:**

```bash
# Install required packages
pip install psycopg2-binary pgvector pytest

# Or using Poetry (from backend directory)
cd backend
poetry add --group dev psycopg2-binary pgvector pytest
```

**Running the tests:**

The Python tests require database connectivity. Since the database port is not exposed to the host by default (for security), you have two options:

**Option 1: Run from within the backend container (RECOMMENDED):**

```bash
# Install test dependencies in backend container
docker-compose exec backend pip install psycopg2-binary pgvector pytest

# Run all tests with verbose output
docker-compose exec backend pytest tests/integration/test_pgvector_extension.py -v

# Run specific test class
docker-compose exec backend pytest tests/integration/test_pgvector_extension.py::TestPgvectorExtension -v

# Run standalone (without pytest)
docker-compose exec backend python tests/integration/test_pgvector_extension.py
```

**Option 2: Expose database port temporarily (for local development only):**

1. Add port mapping to `docker-compose.yml` db service:
   ```yaml
   ports:
     - "5432:5432"
   ```

2. Restart database service:
   ```bash
   docker-compose restart db
   ```

3. Run tests from host:
   ```bash
   # Install packages locally
   pip install psycopg2-binary pgvector pytest

   # Set environment variables
   export DATABASE_URL=postgresql://veille_tech_user:your_password@localhost:5432/veille_tech_db

   # Run tests
   pytest tests/integration/test_pgvector_extension.py -v
   ```

**IMPORTANT:** Never expose database ports in production. Remove port mapping after testing.

**Environment variables:**

The tests use these environment variables (from `.env.backend`):

```bash
DATABASE_URL=postgresql://veille_tech_user:password@localhost:5432/veille_tech_db

# Or individual variables:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=veille_tech_db
POSTGRES_USER=veille_tech_user
POSTGRES_PASSWORD=your_password
```

**Test classes:**

1. **TestPgvectorExtension**: Core functionality tests
   - Extension installation
   - Vector columns and data types
   - Distance operators (cosine, L2, inner product)
   - Dimension enforcement
   - Vector arithmetic
   - Index creation

2. **TestPgvectorIntegration**: Real-world use case tests
   - Semantic search simulation
   - Recommendation engine patterns
   - Report embedding searches

**Expected output:**

```
============================= test session starts ==============================
platform win32 -- Python 3.13.0, pytest-8.0.0, pluggy-1.4.0
collected 11 items

tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_extension_installed PASSED [  9%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_vector_column_creation PASSED [ 18%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_vector_insert_and_retrieval PASSED [ 27%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_cosine_distance_search PASSED [ 36%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_l2_distance_search PASSED [ 45%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_inner_product_search PASSED [ 54%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_vector_dimension_enforcement PASSED [ 63%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_vector_arithmetic PASSED [ 72%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_multiple_vector_columns PASSED [ 81%]
tests/integration/test_pgvector_extension.py::TestPgvectorExtension::test_vector_index_creation PASSED [ 90%]
tests/integration/test_pgvector_extension.py::TestPgvectorIntegration::test_semantic_search_simulation PASSED [100%]

============================== 11 tests passed in 2.34s =============================
```

## Troubleshooting

### Database service not running

**Error:** `Database service is not running`

**Solution:**
```bash
docker-compose up -d db
docker-compose ps db
```

### Connection refused

**Error:** `connection refused connecting to localhost:5432`

**Solution:**
1. Check if database port is exposed: `docker-compose ps`
2. If running tests from container, use `db` as host instead of `localhost`
3. Check `.env.backend` configuration

### pgvector extension not found

**Error:** `pgvector extension is NOT installed`

**Solution:**
1. Verify init-db.sql is mounted: `docker-compose exec db ls -la /docker-entrypoint-initdb.d/`
2. Check database logs: `docker-compose logs db | grep vector`
3. Manually create extension:
   ```bash
   docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "CREATE EXTENSION vector;"
   ```
4. Restart database with volume removal:
   ```bash
   docker-compose down -v
   docker-compose up -d db
   ```

### Permission denied on shell script

**Error:** `Permission denied: ./test_pgvector_extension.sh`

**Solution:**
```bash
chmod +x tests/integration/test_pgvector_extension.sh
```

Or run with bash directly:
```bash
bash tests/integration/test_pgvector_extension.sh
```

### Python package not found

**Error:** `ModuleNotFoundError: No module named 'pgvector'`

**Solution:**
```bash
pip install pgvector psycopg2-binary
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Start database service
  run: docker-compose up -d db

- name: Wait for database
  run: docker-compose exec -T db pg_isready -U veille_tech_user

- name: Run pgvector tests
  run: bash tests/integration/test_pgvector_extension.sh

- name: Run Python tests
  run: |
    pip install -r requirements-test.txt
    pytest tests/integration/test_pgvector_extension.py -v
```

## What These Tests Validate

These tests ensure that the AI-powered Technology Watch Platform can:

1. **Store embeddings** (Bloc 3: AI Content Pipeline)
   - Text embeddings from Google AI `text-embedding-004`
   - Vector dimensions matching model output (e.g., 768D)

2. **Perform similarity searches** (Bloc 5: Recommendation Engine)
   - Cosine similarity for user profile matching
   - Finding similar reports based on embeddings
   - Efficient ANN (Approximate Nearest Neighbor) searches

3. **Support indexing strategies**
   - IVFFlat indexes for approximate search
   - HNSW indexes for high-performance queries
   - Different distance metrics for various use cases

4. **Handle production workloads**
   - Multiple vector columns per table
   - High-dimensional vectors (up to 16,000 dimensions)
   - Concurrent read/write operations

## Next Steps

After these tests pass:
1. Implement Django models with vector fields
2. Create recommendation engine queries
3. Add indexing for performance optimization
4. Benchmark query performance with real embeddings
