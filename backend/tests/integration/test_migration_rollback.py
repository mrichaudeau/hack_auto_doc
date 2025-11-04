"""
Integration tests for migration rollback functionality.

Tests verify that:
1. pgvector migration can be rolled back successfully
2. Extension is removed after rollback
3. Migration history is updated correctly after rollback
4. Migration can be reapplied after rollback (forward/backward/forward cycle)
"""

import pytest
from django.core.management import call_command
from django.db import connection


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
class TestMigrationRollback:
    """Integration tests for migration rollback functionality."""

    def test_pgvector_migration_rollback(self, db):
        """Test pgvector migration can be rolled back."""
        # Apply pgvector migration
        call_command('migrate', 'core', '0001_enable_pgvector', verbosity=0)

        # Verify extension enabled
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
        assert result is not None, "Extension should be enabled"

        # Rollback migration
        call_command('migrate', 'core', 'zero', verbosity=0)

        # Verify extension removed
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
        assert result is None, "Extension should be removed after rollback"

    def test_migration_history_after_rollback(self, db):
        """Test migration history is updated after rollback."""
        # Apply migration
        call_command('migrate', 'core', verbosity=0)

        # Check history
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core'")
            count_before = cursor.fetchone()[0]
        assert count_before > 0, "Migration history should have entries after apply"

        # Rollback
        call_command('migrate', 'core', 'zero', verbosity=0)

        # Check history after rollback
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core'")
            count_after = cursor.fetchone()[0]
        assert count_after == 0, "Migration history should be cleared after rollback to zero"

    def test_reapply_after_rollback(self, db):
        """Test migration can be reapplied after rollback."""
        # Apply -> Rollback -> Reapply cycle
        call_command('migrate', 'core', verbosity=0)
        call_command('migrate', 'core', 'zero', verbosity=0)
        call_command('migrate', 'core', verbosity=0)

        # Verify extension enabled after reapply
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
        assert result is not None, "Extension should be re-enabled after reapply"

        # Verify migration recorded
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core'")
            count = cursor.fetchone()[0]
        assert count > 0, "Migration history should be restored after reapply"

    def test_rollback_idempotency(self, db):
        """Test that rollback can be safely executed multiple times."""
        # Apply migration
        call_command('migrate', 'core', verbosity=0)

        # Rollback multiple times (should not error)
        call_command('migrate', 'core', 'zero', verbosity=0)
        call_command('migrate', 'core', 'zero', verbosity=0)  # Second rollback

        # Verify extension still removed
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
        assert result is None, "Extension should remain removed after multiple rollbacks"

    def test_partial_rollback(self, db):
        """Test rolling back to a specific migration (if more migrations exist)."""
        # Apply all migrations
        call_command('migrate', 'core', verbosity=0)

        # Get migration count
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core'")
            initial_count = cursor.fetchone()[0]

        # If only one migration exists, this test validates that migration is applied
        assert initial_count >= 1, "At least one migration should be applied"

        # Rollback to zero
        call_command('migrate', 'core', 'zero', verbosity=0)

        # Verify all migrations rolled back
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core'")
            final_count = cursor.fetchone()[0]
        assert final_count == 0, "All migrations should be rolled back"

    def test_extension_data_safety(self, db):
        """Test that rollback handles extension data appropriately."""
        # Apply migration to enable extension
        call_command('migrate', 'core', verbosity=0)

        # Create a test table with vector column (if extension supports it)
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_vectors (
                    id SERIAL PRIMARY KEY,
                    embedding vector(3)
                );
            """)
            # Insert test data
            cursor.execute("INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]');")

        # Verify data inserted
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM test_vectors;")
            count = cursor.fetchone()[0]
        assert count == 1, "Test data should be inserted"

        # Clean up test table before rollback
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS test_vectors;")

        # Rollback migration
        call_command('migrate', 'core', 'zero', verbosity=0)

        # Verify extension removed
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
        assert result is None, "Extension should be removed after rollback"
