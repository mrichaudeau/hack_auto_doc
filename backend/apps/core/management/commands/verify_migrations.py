"""
Django management command to verify database migrations are applied correctly.

This command performs comprehensive checks on the migration state:
- Database connectivity
- pgvector extension installation
- Unapplied migrations detection
- Migration history validation

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
import sys


class Command(BaseCommand):
    help = 'Verify database migrations are applied correctly'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Migration Verification'))
        self.stdout.write('=' * 70)

        errors = []

        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
            sys.exit(1)

        # Check pgvector extension
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                result = cursor.fetchone()
                if result:
                    self.stdout.write(self.style.SUCCESS('✓ pgvector extension enabled'))
                else:
                    self.stdout.write(self.style.ERROR('✗ pgvector extension not enabled'))
                    errors.append('pgvector extension missing')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ pgvector check failed: {e}'))
            errors.append('pgvector check error')

        # Check for unapplied migrations
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if plan:
            self.stdout.write(self.style.ERROR(f'✗ {len(plan)} unapplied migrations found'))
            for migration, backwards in plan:
                self.stdout.write(f'  - {migration}')
            errors.append('unapplied migrations')
        else:
            self.stdout.write(self.style.SUCCESS('✓ All migrations applied'))

        # Check django_migrations table
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f'✓ Migration history: {count} records'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration history check failed: {e}'))
            errors.append('migration history error')

        # Summary
        self.stdout.write('\n' + '=' * 70)
        if errors:
            self.stdout.write(self.style.ERROR(f'✗ Verification failed: {len(errors)} issues found'))
            sys.exit(1)
        else:
            self.stdout.write(self.style.SUCCESS('✓ All checks passed'))
            sys.exit(0)
