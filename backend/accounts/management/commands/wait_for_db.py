# -*- coding: utf-8 -*-
"""
Django management command to wait for database to be available.
This is used in Docker to ensure database is ready before running migrations.
"""
import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database to be available."""

    help = 'Wait for database to be available'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Maximum time to wait for database (seconds). Default: 30'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=1,
            help='Time between connection attempts (seconds). Default: 1'
        )

    def handle(self, *args, **options):
        """Handle the command execution."""
        timeout = options['timeout']
        interval = options['interval']

        self.stdout.write('Waiting for database...')

        db_ready = False
        start_time = time.time()

        while not db_ready and (time.time() - start_time) < timeout:
            try:
                # Attempt to connect to database
                connection.ensure_connection()
                db_ready = True
                self.stdout.write(
                    self.style.SUCCESS('✓ Database available!')
                )
            except OperationalError:
                elapsed = int(time.time() - start_time)
                self.stdout.write(
                    f'Database unavailable, waiting... ({elapsed}s/{timeout}s)'
                )
                time.sleep(interval)

        if not db_ready:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Database not available after {timeout} seconds'
                )
            )
            raise OperationalError(
                f'Could not connect to database after {timeout} seconds'
            )
