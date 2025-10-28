"""
pgvector Extension Verification Tests (Python)
Purpose: Verify pgvector extension functionality using Python and psycopg2
Dependencies: psycopg2-binary, pgvector
Usage: pytest tests/integration/test_pgvector_extension.py -v
"""

import os
import psycopg2
import pytest
from typing import Generator

# Try to import pgvector, but don't fail if not available
try:
    from pgvector.psycopg2 import register_vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    print("Warning: pgvector package not installed. Install with: pip install pgvector")


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Create database connection using environment variables.

    Returns:
        psycopg2 connection object

    Raises:
        psycopg2.Error: If connection fails
    """
    # Try DATABASE_URL first, then construct from individual vars
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        conn = psycopg2.connect(database_url)
    else:
        # Fallback to individual environment variables
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'veille_tech_db'),
            user=os.getenv('POSTGRES_USER', 'veille_tech_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )

    # Register vector type if pgvector package is available
    if PGVECTOR_AVAILABLE:
        register_vector(conn)

    return conn


@pytest.fixture
def db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """
    Pytest fixture for database connection with automatic cleanup.

    Yields:
        Database connection
    """
    conn = get_db_connection()
    yield conn
    conn.close()


@pytest.fixture
def db_cursor(db_connection) -> Generator[psycopg2.extensions.cursor, None, None]:
    """
    Pytest fixture for database cursor with transaction rollback.

    Yields:
        Database cursor
    """
    cursor = db_connection.cursor()
    yield cursor
    db_connection.rollback()  # Rollback any changes made during test
    cursor.close()


class TestPgvectorExtension:
    """Test suite for pgvector extension functionality."""

    def test_extension_installed(self, db_cursor):
        """Test 1: Verify pgvector extension is installed."""
        db_cursor.execute(
            "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
        )
        result = db_cursor.fetchone()

        assert result is not None, "pgvector extension is not installed"
        assert result[0] == 'vector', f"Expected 'vector', got '{result[0]}'"
        assert result[1] is not None, "pgvector version is NULL"

        print(f"pgvector extension installed: version {result[1]}")

    def test_vector_column_creation(self, db_connection, db_cursor):
        """Test 2: Verify vector column can be created."""
        # Create test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3),
                description text
            );
        """)
        db_connection.commit()

        # Verify table exists with vector column
        db_cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'test_vectors_py' AND column_name = 'embedding';
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Vector column not created"
        assert result[0] == 'embedding', f"Expected 'embedding', got '{result[0]}'"

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_vector_insert_and_retrieval(self, db_connection, db_cursor):
        """Test 3: Verify vector data can be inserted and retrieved."""
        # Create test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3),
                description text
            );
        """)
        db_connection.commit()

        # Insert test vectors
        db_cursor.execute("""
            INSERT INTO test_vectors_py (embedding, description)
            VALUES ('[1,2,3]', 'test vector 1'),
                   ('[4,5,6]', 'test vector 2'),
                   ('[7,8,9]', 'test vector 3');
        """)
        db_connection.commit()

        # Retrieve vectors
        db_cursor.execute("SELECT COUNT(*) FROM test_vectors_py;")
        count = db_cursor.fetchone()[0]

        assert count == 3, f"Expected 3 vectors, found {count}"

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_cosine_distance_search(self, db_connection, db_cursor):
        """Test 4: Verify cosine distance search (<=> operator)."""
        # Create and populate test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3),
                description text
            );
        """)
        db_cursor.execute("""
            INSERT INTO test_vectors_py (embedding, description)
            VALUES ('[1,2,3]', 'test vector 1'),
                   ('[4,5,6]', 'test vector 2'),
                   ('[7,8,9]', 'test vector 3');
        """)
        db_connection.commit()

        # Perform cosine distance search
        db_cursor.execute("""
            SELECT id, description, embedding <=> '[1,2,3]' AS distance
            FROM test_vectors_py
            ORDER BY embedding <=> '[1,2,3]'
            LIMIT 1;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "No result from cosine distance search"
        assert result[1] == 'test vector 1', f"Expected 'test vector 1', got '{result[1]}'"
        assert result[2] >= 0, f"Distance should be non-negative, got {result[2]}"

        print(f"Nearest vector: {result[1]}, distance: {result[2]}")

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_l2_distance_search(self, db_connection, db_cursor):
        """Test 5: Verify L2 distance search (<-> operator)."""
        # Create and populate test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3),
                description text
            );
        """)
        db_cursor.execute("""
            INSERT INTO test_vectors_py (embedding, description)
            VALUES ('[1,2,3]', 'test vector 1'),
                   ('[4,5,6]', 'test vector 2'),
                   ('[7,8,9]', 'test vector 3');
        """)
        db_connection.commit()

        # Perform L2 distance search
        db_cursor.execute("""
            SELECT id, description, embedding <-> '[1,2,3]' AS distance
            FROM test_vectors_py
            ORDER BY embedding <-> '[1,2,3]'
            LIMIT 1;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "No result from L2 distance search"
        assert result[1] == 'test vector 1', f"Expected 'test vector 1', got '{result[1]}'"
        assert result[2] >= 0, f"Distance should be non-negative, got {result[2]}"

        print(f"Nearest vector (L2): {result[1]}, distance: {result[2]}")

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_inner_product_search(self, db_connection, db_cursor):
        """Test 6: Verify negative inner product search (<#> operator)."""
        # Create and populate test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3),
                description text
            );
        """)
        db_cursor.execute("""
            INSERT INTO test_vectors_py (embedding, description)
            VALUES ('[1,2,3]', 'test vector 1'),
                   ('[4,5,6]', 'test vector 2'),
                   ('[7,8,9]', 'test vector 3');
        """)
        db_connection.commit()

        # Perform inner product search
        db_cursor.execute("""
            SELECT id, description, embedding <#> '[1,2,3]' AS neg_inner_product
            FROM test_vectors_py
            ORDER BY embedding <#> '[1,2,3]'
            LIMIT 1;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "No result from inner product search"
        # Inner product result can be negative
        assert isinstance(result[2], (int, float)), f"Expected numeric result, got {type(result[2])}"

        print(f"Highest inner product: {result[1]}, value: {-result[2]}")

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_vector_dimension_enforcement(self, db_connection, db_cursor):
        """Test 7: Verify vector dimension is enforced."""
        # Create test table with vector(3)
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3)
            );
        """)
        db_connection.commit()

        # Try to insert vector with wrong dimensions (should fail)
        with pytest.raises(psycopg2.Error) as exc_info:
            db_cursor.execute("""
                INSERT INTO test_vectors_py (embedding)
                VALUES ('[1,2]');
            """)
            db_connection.commit()

        assert "expected 3" in str(exc_info.value).lower(), \
            "Expected dimension mismatch error"

        # Cleanup
        db_connection.rollback()
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py;")
        db_connection.commit()

    def test_vector_arithmetic(self, db_cursor):
        """Test 8: Verify vector arithmetic operations."""
        # Test vector addition
        db_cursor.execute("""
            SELECT '[1,2,3]'::vector + '[1,1,1]'::vector AS result;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Vector addition failed"
        # Result should be [2,3,4]
        assert '[2,3,4]' in str(result[0]), f"Expected [2,3,4], got {result[0]}"

        # Test vector subtraction
        db_cursor.execute("""
            SELECT '[4,5,6]'::vector - '[1,2,3]'::vector AS result;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Vector subtraction failed"
        # Result should be [3,3,3]
        assert '[3,3,3]' in str(result[0]), f"Expected [3,3,3], got {result[0]}"

    def test_multiple_vector_columns(self, db_connection, db_cursor):
        """Test 9: Verify table can have multiple vector columns."""
        # Create table with multiple vector columns of different dimensions
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_multi_vectors_py (
                id serial PRIMARY KEY,
                vec_3d vector(3),
                vec_5d vector(5),
                description text
            );
        """)
        db_connection.commit()

        # Insert data
        db_cursor.execute("""
            INSERT INTO test_multi_vectors_py (vec_3d, vec_5d, description)
            VALUES ('[1,2,3]', '[1,2,3,4,5]', 'multi-vector test');
        """)
        db_connection.commit()

        # Retrieve and verify
        db_cursor.execute("""
            SELECT vec_3d, vec_5d FROM test_multi_vectors_py LIMIT 1;
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Failed to retrieve multi-vector data"
        assert '[1,2,3]' in str(result[0]), "3D vector mismatch"
        assert '[1,2,3,4,5]' in str(result[1]), "5D vector mismatch"

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_multi_vectors_py;")
        db_connection.commit()

    def test_vector_index_creation(self, db_connection, db_cursor):
        """Test 10: Verify vector index can be created (for performance)."""
        # Create test table
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_vectors_py (
                id serial PRIMARY KEY,
                embedding vector(3)
            );
        """)
        db_connection.commit()

        # Create IVFFlat index (for approximate nearest neighbor search)
        # Note: Requires some data for clustering
        db_cursor.execute("""
            INSERT INTO test_vectors_py (embedding)
            SELECT CONCAT('[', x, ',', y, ',', z, ']')::vector
            FROM generate_series(1, 10) x,
                 generate_series(1, 10) y,
                 generate_series(1, 10) z
            LIMIT 100;
        """)
        db_connection.commit()

        # Create index
        db_cursor.execute("""
            CREATE INDEX IF NOT EXISTS test_vectors_py_embedding_idx
            ON test_vectors_py
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10);
        """)
        db_connection.commit()

        # Verify index exists
        db_cursor.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'test_vectors_py'
            AND indexname = 'test_vectors_py_embedding_idx';
        """)
        result = db_cursor.fetchone()

        assert result is not None, "Vector index not created"

        print(f"Vector index created: {result[0]}")

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_vectors_py CASCADE;")
        db_connection.commit()


class TestPgvectorIntegration:
    """Integration tests for pgvector with actual use cases."""

    def test_semantic_search_simulation(self, db_connection, db_cursor):
        """Test 11: Simulate semantic search for recommendations."""
        # Create test table simulating report embeddings
        db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_report_embeddings (
                id serial PRIMARY KEY,
                report_title text,
                subject text,
                embedding vector(3)
            );
        """)
        db_connection.commit()

        # Insert sample report embeddings
        db_cursor.execute("""
            INSERT INTO test_report_embeddings (report_title, subject, embedding)
            VALUES
                ('AI in Healthcare', 'AI/ML', '[0.8, 0.2, 0.1]'),
                ('Machine Learning Trends', 'AI/ML', '[0.9, 0.3, 0.05]'),
                ('Blockchain Technology', 'Blockchain', '[0.1, 0.9, 0.8]'),
                ('Cloud Computing', 'Cloud', '[0.3, 0.1, 0.9]');
        """)
        db_connection.commit()

        # Simulate user profile vector (interested in AI/ML)
        user_profile = '[0.85, 0.25, 0.08]'

        # Find top 3 recommendations using cosine similarity
        db_cursor.execute(f"""
            SELECT report_title, subject, embedding <=> '{user_profile}' AS similarity_score
            FROM test_report_embeddings
            ORDER BY embedding <=> '{user_profile}'
            LIMIT 3;
        """)
        results = db_cursor.fetchall()

        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        # First result should be AI/ML related (most similar)
        assert 'AI' in results[0][1] or 'ML' in results[0][1], \
            f"Expected AI/ML subject, got {results[0][1]}"

        print("Semantic search results:")
        for title, subject, score in results:
            print(f"  - {title} ({subject}): score={score:.4f}")

        # Cleanup
        db_cursor.execute("DROP TABLE IF EXISTS test_report_embeddings;")
        db_connection.commit()


if __name__ == "__main__":
    """
    Run tests standalone (without pytest).
    Usage: python test_pgvector_extension.py
    """
    print("=" * 60)
    print("pgvector Extension Verification Tests (Python)")
    print("=" * 60)
    print("")

    if not PGVECTOR_AVAILABLE:
        print("WARNING: pgvector package not available.")
        print("Install with: pip install pgvector psycopg2-binary")
        print("Tests will run with limited functionality.")
        print("")

    # Run basic connection test
    try:
        conn = get_db_connection()
        print("[PASS] Database connection successful")

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"[INFO] PostgreSQL version: {version.split(',')[0]}")

        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print(f"[PASS] pgvector extension installed: version {result[0]}")
        else:
            print("[FAIL] pgvector extension NOT installed")

        cursor.close()
        conn.close()

        print("")
        print("For full test suite, run: pytest tests/integration/test_pgvector_extension.py -v")

    except Exception as e:
        print(f"[FAIL] Connection test failed: {e}")
        print("")
        print("Troubleshooting:")
        print("  1. Ensure database service is running: docker-compose ps db")
        print("  2. Check environment variables are set correctly")
        print("  3. Verify connection string: echo $DATABASE_URL")
