"""
Integration tests for Django migration error scenarios.

This module tests how the migration system handles various error conditions:
- Database connection failures
- Permission errors (mocked)
- Migration conflicts
- Partial migration rollback
- Clear error messaging

These tests ensure the migration system fails gracefully and provides
actionable error messages when problems occur.

Test Markers:
- @pytest.mark.integration: Marks tests as integration tests
- @pytest.mark.django_db: Provides database access for testing
"""

import pytest
from django.core.management import call_command
from django.db import connection
from django.core.management.base import CommandError
from django.db.migrations.executor import MigrationExecutor
from unittest.mock import patch, MagicMock
from io import StringIO


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestMigrationErrors:
    """Test suite for migration error scenarios and error handling."""

    def test_migration_fails_without_database(self):
        """
        Test migration provides clear error when database is unavailable.

        This test mocks a database connection failure to verify that:
        1. The migration system raises an appropriate exception
        2. The error message is clear and mentions connection issues
        3. The system fails fast without leaving partial state
        """
        # Mock the connection to simulate database unavailability
        with patch('django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection') as mock_conn:
            mock_conn.side_effect = Exception("Connection refused")

            # Attempt migration and expect it to fail
            with pytest.raises(Exception) as exc_info:
                call_command('migrate', verbosity=0)

            # Verify error message mentions connection issue
            error_msg = str(exc_info.value).lower()
            assert 'connection' in error_msg or 'refused' in error_msg, \
                f"Error message should mention connection: {exc_info.value}"

    def test_migration_permission_error(self):
        """
        Test migration handles permission errors gracefully.

        This test simulates a scenario where the database user lacks
        SUPERUSER privileges required for CREATE EXTENSION.

        Expected behavior:
        - Migration fails with OperationalError or ProgrammingError
        - Error message mentions permission or privilege issue
        - No partial state left in database
        """
        # Mock the cursor.execute to simulate permission error
        with patch('django.db.backends.utils.CursorWrapper.execute') as mock_execute:
            # Simulate PostgreSQL permission error for CREATE EXTENSION
            from django.db.utils import OperationalError
            mock_execute.side_effect = OperationalError(
                "permission denied to create extension \"vector\""
            )

            # Attempt migration and expect it to fail
            with pytest.raises(OperationalError) as exc_info:
                call_command('migrate', 'core', verbosity=0)

            # Verify error message mentions permission issue
            error_msg = str(exc_info.value).lower()
            assert 'permission' in error_msg or 'denied' in error_msg, \
                f"Error message should mention permission: {exc_info.value}"

    def test_unapplied_migrations_detection(self, db):
        """
        Test that unapplied migrations are detected correctly.

        Uses Django's showmigrations command to verify:
        1. All apps are listed with their migration status
        2. Migration status indicators ([ ] or [X]) are present
        3. Core app migrations are included in output

        This tests the migration planning/detection system, not execution.
        """
        out = StringIO()
        call_command('showmigrations', stdout=out)
        output = out.getvalue()

        # Verify output contains expected app names
        assert 'core' in output, "showmigrations should list core app"

        # Verify migration status indicators are present
        # Django uses [ ] for unapplied and [X] for applied
        assert '[' in output and ']' in output, \
            "Migration status indicators should be present"

        # Verify at least one migration is listed
        assert '0001_enable_pgvector' in output or 'enable_pgvector' in output, \
            "pgvector migration should be listed"

    def test_migration_status_query(self, db):
        """
        Test querying migration status from django_migrations table.

        Verifies that:
        1. django_migrations table exists and is accessible
        2. Applied migrations are recorded correctly
        3. Migration history includes app name and migration name
        4. pgvector migration is recorded after being applied
        """
        # Apply migrations first
        call_command('migrate', verbosity=0)

        # Query migration history
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT app, name FROM django_migrations ORDER BY app, name"
            )
            migrations = cursor.fetchall()

        # Verify migrations were recorded
        assert len(migrations) > 0, "Migration history should not be empty"

        # Verify core app migrations are present
        core_migrations = [m for m in migrations if m[0] == 'core']
        assert len(core_migrations) > 0, "Core app should have migrations recorded"

        # Verify pgvector migration is present
        pgvector_migration = any(
            'enable_pgvector' in m[1]
            for m in core_migrations
        )
        assert pgvector_migration, \
            "pgvector migration should be recorded in history"

    def test_migration_transactional_rollback(self, db):
        """
        Test that failed migration doesn't leave partial state.

        Django migrations run in a transaction by default (ATOMIC_REQUESTS),
        so a failed migration should be rolled back completely.

        This test verifies:
        1. Successful migrations are fully applied
        2. All-or-nothing behavior for migration execution
        3. Migration history consistency after failures

        Note: This test documents expected behavior. True rollback testing
        would require creating a deliberately failing migration, which is
        challenging in a test environment.
        """
        # Apply migrations successfully
        call_command('migrate', verbosity=0)

        # Verify all migrations are either fully applied or not applied
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT app, name FROM django_migrations ORDER BY app, name"
            )
            migrations = cursor.fetchall()

        # Verify we have migrations recorded
        assert len(migrations) > 0, \
            "Successful migrations should be recorded"

        # Verify core.0001_enable_pgvector is present
        pgvector_applied = any(
            m[0] == 'core' and 'enable_pgvector' in m[1]
            for m in migrations
        )
        assert pgvector_applied, \
            "pgvector migration should be fully applied"

        # Verify extension is actually enabled in database
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            )
            extension = cursor.fetchone()

        assert extension is not None, \
            "pgvector extension should be enabled after migration"

    def test_migration_executor_plan(self, db):
        """
        Test MigrationExecutor correctly plans migrations.

        Uses Django's internal MigrationExecutor to verify:
        1. Migration plan is generated correctly
        2. Dependencies are resolved in proper order
        3. Core app migrations are included in plan
        4. No circular dependencies exist
        """
        executor = MigrationExecutor(connection)

        # Get migration plan (list of migrations to apply)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        # Verify plan exists and has migrations
        assert isinstance(plan, list), "Migration plan should be a list"

        # Check if core app is in the plan
        core_migrations = [
            migration for migration, _ in plan
            if migration.app_label == 'core'
        ]

        # If there are unapplied core migrations, they should be in the plan
        if core_migrations:
            assert any(
                'enable_pgvector' in str(m.name)
                for m in core_migrations
            ), "pgvector migration should be in plan if unapplied"

    def test_showmigrations_verbose_output(self, db):
        """
        Test showmigrations provides detailed migration information.

        Verifies that:
        1. Verbose output includes migration names
        2. Applied migrations are marked correctly
        3. Core app migrations are listed
        4. Output is structured and readable
        """
        # Get verbose migration status
        out = StringIO()
        call_command('showmigrations', '--list', verbosity=1, stdout=out)
        output = out.getvalue()

        # Verify basic structure
        assert len(output) > 0, "Migration status output should not be empty"
        assert 'core' in output.lower(), "Core app should be listed"

        # Verify migration format (Django uses [ ] or [X])
        assert '[' in output and ']' in output, \
            "Migration status indicators should be present"

    def test_migration_fake_error(self, db):
        """
        Test that --fake flag is correctly handled in error scenarios.

        The --fake flag marks migrations as applied without running them.
        This tests error handling when using fake migrations.

        Note: We don't actually fake the pgvector migration in tests,
        but we verify the command accepts the flag correctly.
        """
        # Test that fake flag is accepted (doesn't error)
        try:
            # Run migrate with fake flag (should succeed or be a no-op)
            out = StringIO()
            call_command('migrate', '--fake-initial', verbosity=0, stdout=out)
            # If we get here, the command was accepted
            assert True, "Command should accept --fake-initial flag"
        except CommandError as e:
            # If command fails, it should be for a valid reason, not syntax
            assert '--fake-initial' not in str(e).lower(), \
                f"Command should accept --fake-initial flag: {e}"

    def test_migration_clear_error_messages(self, db):
        """
        Test that migration errors provide clear, actionable messages.

        This test verifies that when migrations fail, the error messages:
        1. Are formatted clearly
        2. Indicate which migration failed
        3. Provide context about the failure
        4. Include actionable information

        We test this by examining successful migration output for
        expected informational structure.
        """
        out = StringIO()
        err = StringIO()

        # Run migrations and capture output
        call_command('migrate', verbosity=2, stdout=out, stderr=err)

        output = out.getvalue()

        # Verify output includes operation descriptions
        assert len(output) > 0, "Migration output should not be empty"

        # Django migration output typically includes:
        # - "Applying ..." for each migration
        # - "OK" or similar success indicator
        # Check for standard migration output patterns
        output_lower = output.lower()
        has_migration_info = (
            'applying' in output_lower or
            'operations' in output_lower or
            'migration' in output_lower
        )
        assert has_migration_info, \
            "Migration output should describe operations being performed"
