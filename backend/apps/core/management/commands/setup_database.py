"""
Django management command to initialize or update database schema.

This command wraps common migration operations into a single developer-friendly
command that checks database connectivity, shows pending migrations, applies them,
and displays the final status.

Usage:
    python manage.py setup_database              # Apply migrations
    python manage.py setup_database --dry-run    # Preview without applying
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
import sys


class Command(BaseCommand):
    """
    Initialize or update database schema (run migrations).

    This command performs the following operations:
    1. Checks database connectivity
    2. Shows pending migrations
    3. Applies migrations (unless --dry-run is used)
    4. Displays final migration status
    5. Warns if any migrations remain unapplied
    """

    help = 'Initialize or update database schema (run migrations)'

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what migrations would be applied without applying them',
        )

    def handle(self, *args, **options):
        """
        Main command execution handler.

        Args:
            options (dict): Command options including 'dry_run' flag
        """
        dry_run = options['dry_run']

        # Display header
        self.stdout.write(self.style.MIGRATE_HEADING('Database Setup'))
        self.stdout.write('=' * 70)

        # Step 1: Check database connectivity
        self.stdout.write('\n[1/4] Checking database connectivity...')
        if not self._check_database_connection():
            self.stdout.write(self.style.ERROR('\nDatabase setup failed. Please check your database configuration.'))
            sys.exit(1)

        # Step 2: Show pending migrations
        self.stdout.write('\n[2/4] Checking migration status...')
        pending_count = self._show_migration_status()

        # Step 3: Apply migrations (or skip if dry-run)
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[3/4] --dry-run mode: No migrations will be applied'))
            if pending_count > 0:
                self.stdout.write(self.style.WARNING(f'      {pending_count} migration(s) would be applied'))
            else:
                self.stdout.write('      No migrations to apply')
        else:
            self.stdout.write('\n[3/4] Applying migrations...')
            if not self._apply_migrations():
                self.stdout.write(self.style.ERROR('\nMigration application failed.'))
                sys.exit(1)

        # Step 4: Display final status
        self.stdout.write('\n[4/4] Final migration status:')
        final_pending = self._show_migration_status()

        # Summary
        self.stdout.write('\n' + '=' * 70)
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run completed. No changes were made.'))
        elif final_pending == 0:
            self.stdout.write(self.style.SUCCESS('Database setup completed successfully!'))
            self.stdout.write(self.style.SUCCESS('All migrations have been applied.'))
        else:
            self.stdout.write(self.style.WARNING(f'Database setup completed with {final_pending} pending migration(s).'))
            self.stdout.write(self.style.WARNING('Some migrations may require manual intervention.'))

    def _check_database_connection(self):
        """
        Check if database connection is working.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('      Database connection successful'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'      Database connection failed: {e}'))
            self.stdout.write(self.style.ERROR('      Please ensure the database service is running.'))
            return False

    def _show_migration_status(self):
        """
        Display migration status and count pending migrations.

        Returns:
            int: Number of pending migrations
        """
        try:
            # Use MigrationExecutor to check for unapplied migrations
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

            # Display detailed status
            self.stdout.write('')
            call_command('showmigrations', verbosity=1, stdout=self.stdout)

            # Count and report pending migrations
            pending_count = len(plan)
            if pending_count > 0:
                self.stdout.write(self.style.WARNING(f'\n      {pending_count} migration(s) pending'))
            else:
                self.stdout.write(self.style.SUCCESS(f'\n      All migrations applied'))

            return pending_count
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'      Error checking migration status: {e}'))
            return 0

    def _apply_migrations(self):
        """
        Apply all pending migrations.

        Returns:
            bool: True if migrations applied successfully, False otherwise
        """
        try:
            # Apply migrations with verbosity level 2 for detailed output
            call_command('migrate', verbosity=2, stdout=self.stdout)
            self.stdout.write(self.style.SUCCESS('\n      All migrations applied successfully'))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n      Migration failed: {e}'))
            return False
