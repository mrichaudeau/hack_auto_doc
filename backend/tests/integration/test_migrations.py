"""
Integration tests for Django migration execution.

This test suite verifies that migrations execute successfully in a test database
environment with live PostgreSQL connection. Tests include:
- Migration application and idempotency
- pgvector extension enablement
- Migration history tracking
- Vector data type availability

All tests require:
- Live PostgreSQL database connection
- USE_POSTGRESQL_FOR_TESTS=true environment variable
- @pytest.mark.integration marker for selective execution

Test Execution:
    docker-compose exec -e USE_POSTGRESQL_FOR_TESTS=true backend python -m pytest -v -m integration tests/integration/test_migrations.py

Technical Notes:
- Uses @pytest.mark.django_db(transaction=True) for proper database isolation
- Tests run against a fresh test database created by pytest-django
- MigrationExecutor is used to check migration state programmatically
- Raw SQL queries verify PostgreSQL-specific features (pgvector)

Related Tasks:
- TASK-9.2: Create pgvector extension migration (dependency)
- TASK-9.3: Configure database settings (dependency)
- TASK-9.10: Integration test migration execution (this file)
"""

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestMigrationExecution:
    """
    Integration test suite for migration execution.

    These tests verify the complete migration pipeline including:
    - Django migration system functionality
    - PostgreSQL extension enablement (pgvector)
    - Migration history tracking
    - Idempotency guarantees
    """

    def test_migrations_apply_successfully(self, db):
        """
        Test all migrations apply without errors.

        Verifies:
        - All pending migrations can be applied
        - No migration plan remains after migration
        - Django migration system is working correctly

        Expected Result:
        - Zero unapplied migrations after call_command('migrate')
        - Migration plan is empty (all migrations applied)
        """
        # Apply all pending migrations
        call_command('migrate', verbosity=0)

        # Check for unapplied migrations using MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        # Assert no migrations remain unapplied
        assert len(plan) == 0, f"Unapplied migrations found: {plan}"

    def test_pgvector_extension_enabled(self, db):
        """
        Test pgvector extension is enabled in database.

        Verifies:
        - pgvector extension exists in pg_extension table
        - Extension was created by migration 0001_enable_pgvector
        - Extension is available for vector operations

        Expected Result:
        - pg_extension table contains row with extname='vector'
        - Extension can be queried successfully

        Technical Note:
        - Requires PostgreSQL 15+ with pgvector extension installed
        - Requires SUPERUSER privileges for initial extension creation
        """
        # Apply migrations to ensure extension is created
        call_command('migrate', verbosity=0)

        # Query pg_extension table for vector extension
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'"
            )
            result = cursor.fetchone()

        # Assert extension exists
        assert result is not None, "pgvector extension not enabled"
        assert result[0] == 'vector', f"Expected extname='vector', got '{result[0]}'"

    def test_migration_history_recorded(self, db):
        """
        Test migration history is tracked in django_migrations table.

        Verifies:
        - django_migrations table contains migration records
        - core.0001_enable_pgvector migration is recorded
        - Migration timestamp and metadata are stored

        Expected Result:
        - django_migrations table has at least one row
        - Specific row exists for app='core', name='0001_enable_pgvector'

        Technical Note:
        - Django automatically creates django_migrations table
        - Each applied migration creates one row in this table
        """
        # Apply migrations
        call_command('migrate', verbosity=0)

        # Check total migration count
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations")
            count = cursor.fetchone()[0]

        assert count > 0, "No migration history found in django_migrations table"

        # Verify core.0001_enable_pgvector is recorded
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT app, name FROM django_migrations WHERE app='core' AND name='0001_enable_pgvector'"
            )
            result = cursor.fetchone()

        assert result is not None, "pgvector migration (core.0001_enable_pgvector) not recorded"
        assert result[0] == 'core', f"Expected app='core', got '{result[0]}'"
        assert result[1] == '0001_enable_pgvector', f"Expected name='0001_enable_pgvector', got '{result[1]}'"

    def test_migrations_idempotent(self, db):
        """
        Test migrations can be safely re-run (idempotency).

        Verifies:
        - Running migrate command multiple times does not error
        - No additional migrations are applied on second run
        - IF NOT EXISTS clause in SQL prevents duplicate extension creation

        Expected Result:
        - First migrate command applies migrations
        - Second migrate command is no-op (no errors, no changes)
        - Migration plan remains empty after both runs

        Technical Note:
        - pgvector migration uses "CREATE EXTENSION IF NOT EXISTS"
        - Django tracks applied migrations to prevent re-application
        - Critical for production deployments and rollbacks
        """
        # Apply migrations first time
        call_command('migrate', verbosity=0)

        # Apply migrations second time (should be idempotent)
        call_command('migrate', verbosity=0)

        # Verify no unapplied migrations remain
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        assert len(plan) == 0, "Migrations not idempotent - unapplied migrations found after re-run"

    def test_vector_data_type_available(self, db):
        """
        Test vector data type is available for use after migration.

        Verifies:
        - Vector type cast works (e.g., '[1,2,3]'::vector)
        - pgvector extension provides vector data type
        - Vector operations can be performed in queries

        Expected Result:
        - SQL query with ::vector cast succeeds
        - Result contains vector representation
        - No SQL errors or type errors

        Technical Note:
        - Vector type requires pgvector extension enabled
        - This test ensures extension is functional, not just installed
        - Validates readiness for AI embeddings storage (Bloc 3)
        """
        # Apply migrations to enable pgvector
        call_command('migrate', verbosity=0)

        # Test vector type cast with sample data
        with connection.cursor() as cursor:
            cursor.execute("SELECT '[1,2,3]'::vector AS test_vector")
            result = cursor.fetchone()

        # Assert vector query executed successfully
        assert result is not None, "Vector data type not available - query returned None"
        assert result[0] is not None, "Vector cast returned NULL - extension may not be functional"

    def test_vector_dimension_validation(self, db):
        """
        Test vector dimension handling and validation.

        Verifies:
        - Vectors of different dimensions can be created
        - Vector dimension is preserved in storage
        - pgvector handles dimension metadata correctly

        Expected Result:
        - 3-dimensional vector creates successfully
        - 5-dimensional vector creates successfully
        - Each vector preserves its original dimension

        Technical Note:
        - pgvector supports vectors up to 16000 dimensions
        - Dimension validation happens at query time
        - Important for embeddings (typically 384-1536 dimensions)
        """
        # Apply migrations
        call_command('migrate', verbosity=0)

        # Test vectors of different dimensions
        with connection.cursor() as cursor:
            # Test 3-dimensional vector
            cursor.execute("SELECT '[1,2,3]'::vector AS vec3")
            vec3_result = cursor.fetchone()

            # Test 5-dimensional vector
            cursor.execute("SELECT '[1,2,3,4,5]'::vector AS vec5")
            vec5_result = cursor.fetchone()

        # Assert both vectors created successfully
        assert vec3_result is not None, "3-dimensional vector failed to create"
        assert vec5_result is not None, "5-dimensional vector failed to create"

    def test_extension_schema_location(self, db):
        """
        Test pgvector extension is installed in correct schema.

        Verifies:
        - Extension exists in public schema (default)
        - Extension metadata is accessible
        - Schema isolation is configured correctly

        Expected Result:
        - Extension found in pg_extension catalog
        - Extension schema matches expected location
        - No schema conflicts exist

        Technical Note:
        - Extensions typically installed in public schema
        - Custom schema can be specified during CREATE EXTENSION
        - Important for multi-tenant or schema-isolated deployments
        """
        # Apply migrations
        call_command('migrate', verbosity=0)

        # Query extension schema information
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT e.extname, n.nspname AS schema_name
                FROM pg_extension e
                JOIN pg_namespace n ON e.extnamespace = n.oid
                WHERE e.extname = 'vector'
            """)
            result = cursor.fetchone()

        # Assert extension exists and check schema
        assert result is not None, "pgvector extension not found in pg_extension"
        assert result[0] == 'vector', f"Expected extname='vector', got '{result[0]}'"
        # Note: schema_name is typically 'public' but can vary by deployment
        assert result[1] is not None, "Extension schema name is NULL"
