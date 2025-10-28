#!/usr/bin/env python3
"""
test_database_connectivity.py
Integration tests for PostgreSQL database connectivity using pytest

Tests database connections, queries, concurrent connections, and pgvector extension.
Can be run with: pytest tests/integration/test_database_connectivity.py -v
"""

import os
import time
import pytest
import psycopg2
from psycopg2 import pool
from concurrent.futures import ThreadPoolExecutor, as_completed


# Database connection parameters from environment
def get_db_connection_params():
    """Extract database connection parameters from environment or DATABASE_URL."""
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Parse DATABASE_URL: postgresql://user:password@host:port/database
        return database_url
    else:
        # Fallback to individual environment variables
        return {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'veille_tech_db'),
            'user': os.getenv('POSTGRES_USER', 'veille_tech_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }


@pytest.fixture(scope='module')
def db_connection():
    """Fixture to create a database connection for tests."""
    conn_params = get_db_connection_params()

    if isinstance(conn_params, str):
        # Connection string
        conn = psycopg2.connect(conn_params)
    else:
        # Connection parameters
        conn = psycopg2.connect(**conn_params)

    yield conn
    conn.close()


@pytest.fixture(scope='module')
def db_cursor(db_connection):
    """Fixture to create a database cursor for tests."""
    cursor = db_connection.cursor()
    yield cursor
    cursor.close()


class TestDatabaseConnection:
    """Test suite for basic database connection functionality."""

    def test_connection_succeeds(self):
        """Test 1: Verify database connection can be established."""
        conn_params = get_db_connection_params()

        if isinstance(conn_params, str):
            conn = psycopg2.connect(conn_params)
        else:
            conn = psycopg2.connect(**conn_params)

        assert conn is not None, "Database connection should be established"
        assert conn.closed == 0, "Connection should be open"

        conn.close()
        assert conn.closed == 1, "Connection should be closed after close()"

    def test_connection_with_context_manager(self):
        """Test 2: Verify connection works with context manager."""
        conn_params = get_db_connection_params()

        if isinstance(conn_params, str):
            with psycopg2.connect(conn_params) as conn:
                assert conn is not None
                assert conn.closed == 0
        else:
            with psycopg2.connect(**conn_params) as conn:
                assert conn is not None
                assert conn.closed == 0


class TestDatabaseQueries:
    """Test suite for database query execution."""

    def test_simple_select_query(self, db_cursor):
        """Test 3: Verify simple SELECT query executes successfully."""
        db_cursor.execute("SELECT 1 AS test_value;")
        result = db_cursor.fetchone()

        assert result is not None, "Query should return a result"
        assert result[0] == 1, "Query should return value 1"

    def test_postgresql_version(self, db_cursor):
        """Test 4: Verify PostgreSQL version is 15+."""
        db_cursor.execute("SELECT version();")
        version_string = db_cursor.fetchone()[0]

        assert version_string is not None, "Version query should return a result"
        assert "PostgreSQL 15" in version_string, f"Expected PostgreSQL 15, got: {version_string}"

    def test_current_database(self, db_cursor):
        """Test 5: Verify connected to correct database."""
        db_cursor.execute("SELECT current_database();")
        current_db = db_cursor.fetchone()[0]

        expected_db = os.getenv('POSTGRES_DB', 'veille_tech_db')
        assert current_db == expected_db, f"Expected database '{expected_db}', got '{current_db}'"

    def test_current_user(self, db_cursor):
        """Test 6: Verify connected with correct user."""
        db_cursor.execute("SELECT current_user;")
        current_user = db_cursor.fetchone()[0]

        expected_user = os.getenv('POSTGRES_USER', 'veille_tech_user')
        assert current_user == expected_user, f"Expected user '{expected_user}', got '{current_user}'"

    def test_table_creation_and_cleanup(self, db_connection):
        """Test 7: Verify ability to create and drop tables."""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connectivity_temp (
                id SERIAL PRIMARY KEY,
                test_value TEXT
            );
        """)
        db_connection.commit()

        # Insert test data
        cursor.execute("INSERT INTO test_connectivity_temp (test_value) VALUES ('test');")
        db_connection.commit()

        # Verify insertion
        cursor.execute("SELECT test_value FROM test_connectivity_temp LIMIT 1;")
        result = cursor.fetchone()
        assert result[0] == 'test', "Inserted data should match"

        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS test_connectivity_temp;")
        db_connection.commit()
        cursor.close()


class TestConnectionPooling:
    """Test suite for connection pooling functionality."""

    def test_connection_pool_creation(self):
        """Test 8: Verify connection pool can be created."""
        conn_params = get_db_connection_params()

        if isinstance(conn_params, str):
            # For connection string, we need to parse it
            # psycopg2.pool requires separate parameters
            # Skip pool test if using connection string
            pytest.skip("Connection pool test requires individual connection parameters")

        # Create connection pool with minimum 1 and maximum 10 connections
        connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **conn_params)

        assert connection_pool is not None, "Connection pool should be created"

        # Get a connection from pool
        conn = connection_pool.getconn()
        assert conn is not None, "Should get connection from pool"

        # Return connection to pool
        connection_pool.putconn(conn)

        # Close all connections in pool
        connection_pool.closeall()

    def test_max_connections_setting(self, db_cursor):
        """Test 9: Verify max_connections is configured."""
        db_cursor.execute("SHOW max_connections;")
        max_connections = int(db_cursor.fetchone()[0])

        assert max_connections > 0, "max_connections should be greater than 0"
        assert max_connections >= 10, f"max_connections should be at least 10, got {max_connections}"


class TestConcurrentConnections:
    """Test suite for concurrent connection handling."""

    def test_concurrent_connections(self):
        """Test 10: Verify database handles 10+ concurrent connections."""
        conn_params = get_db_connection_params()
        num_connections = 10

        def create_connection_and_query(connection_id):
            """Create a connection and execute a simple query."""
            try:
                if isinstance(conn_params, str):
                    conn = psycopg2.connect(conn_params)
                else:
                    conn = psycopg2.connect(**conn_params)

                cursor = conn.cursor()
                cursor.execute("SELECT 1 AS connection_test;")
                result = cursor.fetchone()[0]
                cursor.close()
                conn.close()

                return (connection_id, True, result)
            except Exception as e:
                return (connection_id, False, str(e))

        # Execute concurrent connections using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [
                executor.submit(create_connection_and_query, i)
                for i in range(num_connections)
            ]

            results = [future.result() for future in as_completed(futures)]

        # Verify all connections succeeded
        successful = [r for r in results if r[1] is True]
        failed = [r for r in results if r[1] is False]

        assert len(successful) == num_connections, \
            f"Expected {num_connections} successful connections, got {len(successful)}. Failed: {failed}"

    def test_concurrent_transactions(self, db_connection):
        """Test 11: Verify database handles concurrent transactions."""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_concurrent_temp (
                id SERIAL PRIMARY KEY,
                value INTEGER
            );
        """)
        db_connection.commit()
        cursor.close()

        conn_params = get_db_connection_params()
        num_transactions = 5

        def execute_transaction(transaction_id):
            """Execute a transaction that inserts data."""
            try:
                if isinstance(conn_params, str):
                    conn = psycopg2.connect(conn_params)
                else:
                    conn = psycopg2.connect(**conn_params)

                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO test_concurrent_temp (value) VALUES (%s);",
                    (transaction_id,)
                )
                conn.commit()
                cursor.close()
                conn.close()

                return (transaction_id, True, None)
            except Exception as e:
                return (transaction_id, False, str(e))

        # Execute concurrent transactions
        with ThreadPoolExecutor(max_workers=num_transactions) as executor:
            futures = [
                executor.submit(execute_transaction, i)
                for i in range(num_transactions)
            ]

            results = [future.result() for future in as_completed(futures)]

        # Verify all transactions succeeded
        successful = [r for r in results if r[1] is True]
        assert len(successful) == num_transactions, \
            f"Expected {num_transactions} successful transactions, got {len(successful)}"

        # Verify all rows were inserted
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM test_concurrent_temp;")
        count = cursor.fetchone()[0]
        assert count == num_transactions, \
            f"Expected {num_transactions} rows in table, got {count}"

        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS test_concurrent_temp;")
        db_connection.commit()
        cursor.close()


class TestPgvectorExtension:
    """Test suite for pgvector extension functionality."""

    def test_pgvector_extension_installed(self, db_cursor):
        """Test 12: Verify pgvector extension is installed."""
        db_cursor.execute("""
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'vector';
        """)
        result = db_cursor.fetchone()

        assert result is not None, "pgvector extension should be installed"
        assert result[0] == 'vector', "Extension name should be 'vector'"

        print(f"\npgvector extension version: {result[1]}")

    def test_vector_type_available(self, db_cursor):
        """Test 13: Verify vector data type is available."""
        db_cursor.execute("""
            SELECT typname
            FROM pg_type
            WHERE typname = 'vector';
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Vector type should be available"
        assert result[0] == 'vector', "Type name should be 'vector'"

    def test_vector_operations(self, db_connection):
        """Test 14: Verify vector operations work correctly."""
        cursor = db_connection.cursor()

        # Create test table with vector column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vector_temp (
                id SERIAL PRIMARY KEY,
                embedding vector(3)
            );
        """)
        db_connection.commit()

        # Insert vector data
        cursor.execute("""
            INSERT INTO test_vector_temp (embedding)
            VALUES ('[1,2,3]'), ('[4,5,6]');
        """)
        db_connection.commit()

        # Test vector similarity (cosine distance)
        cursor.execute("""
            SELECT embedding <=> '[1,2,3]' AS distance
            FROM test_vector_temp
            ORDER BY distance
            LIMIT 1;
        """)
        result = cursor.fetchone()

        assert result is not None, "Vector similarity query should return result"
        assert result[0] >= 0, "Cosine distance should be non-negative"

        # Cleanup
        cursor.execute("DROP TABLE IF EXISTS test_vector_temp;")
        db_connection.commit()
        cursor.close()


class TestDatabasePerformance:
    """Test suite for database performance metrics."""

    def test_connection_time(self):
        """Test 15: Verify connection time is acceptable (<1 second)."""
        conn_params = get_db_connection_params()

        start_time = time.time()

        if isinstance(conn_params, str):
            conn = psycopg2.connect(conn_params)
        else:
            conn = psycopg2.connect(**conn_params)

        connection_time = time.time() - start_time
        conn.close()

        assert connection_time < 1.0, \
            f"Connection time should be < 1 second, got {connection_time:.3f}s"

        print(f"\nConnection established in {connection_time:.3f}s")

    def test_query_performance(self, db_cursor):
        """Test 16: Verify simple query performance (<100ms)."""
        # Warm up
        db_cursor.execute("SELECT 1;")
        db_cursor.fetchone()

        # Measure query time
        start_time = time.time()
        db_cursor.execute("SELECT COUNT(*) FROM pg_database;")
        db_cursor.fetchone()
        query_time = time.time() - start_time

        assert query_time < 0.1, \
            f"Query time should be < 100ms, got {query_time*1000:.1f}ms"

        print(f"\nQuery executed in {query_time*1000:.1f}ms")


if __name__ == "__main__":
    """Run tests with pytest when executed directly."""
    import sys

    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    sys.exit(exit_code)
