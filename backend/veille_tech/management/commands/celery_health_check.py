"""
Django management command for Celery worker health checks.

This command verifies:
1. Celery app initialization
2. Redis broker connectivity
3. Active worker availability

Exit codes:
- 0: All health checks passed (healthy)
- 1: One or more health checks failed (unhealthy)

Usage:
    python manage.py celery_health_check
    poetry run python manage.py celery_health_check
    docker-compose exec backend python manage.py celery_health_check
"""

import sys
from django.core.management.base import BaseCommand
from django.core.cache import cache
import redis


class Command(BaseCommand):
    help = 'Check Celery worker health (app, broker, workers)'

    def handle(self, *args, **options):
        """Execute health check and return exit code based on results."""
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.WARNING('Celery Worker Health Check'))
        self.stdout.write('=' * 60)

        all_healthy = True

        # Check 1: Celery app initialization
        if not self._check_celery_app():
            all_healthy = False

        # Check 2: Broker connectivity (Redis ping)
        if not self._check_broker_connectivity():
            all_healthy = False

        # Check 3: Active workers
        if not self._check_active_workers():
            all_healthy = False

        # Summary
        self.stdout.write('=' * 60)
        if all_healthy:
            self.stdout.write(self.style.SUCCESS(
                'HEALTH CHECK PASSED: All systems operational'
            ))
            sys.exit(0)
        else:
            self.stdout.write(self.style.ERROR(
                'HEALTH CHECK FAILED: One or more systems unhealthy'
            ))
            sys.exit(1)

    def _check_celery_app(self):
        """Verify Celery app can be imported and initialized."""
        self.stdout.write('\n[1/3] Checking Celery app initialization...')

        try:
            from veille_tech.celery import app

            if app is None:
                self.stdout.write(self.style.ERROR(
                    '  X Celery app is None'
                ))
                return False

            # Verify app has expected configuration
            if not hasattr(app, 'conf'):
                self.stdout.write(self.style.ERROR(
                    '  X Celery app missing configuration'
                ))
                return False

            self.stdout.write(self.style.SUCCESS(
                f'  OK Celery app initialized: {app.main}'
            ))
            return True

        except ImportError as e:
            self.stdout.write(self.style.ERROR(
                f'  X Failed to import Celery app: {str(e)}'
            ))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'  X Celery app initialization error: {str(e)}'
            ))
            return False

    def _check_broker_connectivity(self):
        """Test Redis broker connectivity with ping command."""
        self.stdout.write('\n[2/3] Checking Redis broker connectivity...')

        try:
            from veille_tech.celery import app

            # Get broker URL from Celery config
            broker_url = app.conf.broker_url

            # Parse Redis connection from broker URL
            # Format: redis://host:port/db
            if not broker_url.startswith('redis://'):
                self.stdout.write(self.style.ERROR(
                    f'  X Unsupported broker type: {broker_url}'
                ))
                return False

            # Create Redis client
            redis_client = redis.from_url(broker_url)

            # Test connection with PING
            response = redis_client.ping()

            if response:
                self.stdout.write(self.style.SUCCESS(
                    f'  OK Redis broker reachable: {broker_url}'
                ))
                return True
            else:
                self.stdout.write(self.style.ERROR(
                    f'  X Redis PING failed: {broker_url}'
                ))
                return False

        except redis.ConnectionError as e:
            self.stdout.write(self.style.ERROR(
                f'  X Redis connection failed: {str(e)}'
            ))
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'  X Broker connectivity error: {str(e)}'
            ))
            return False

    def _check_active_workers(self):
        """Check for active Celery workers using inspect API."""
        self.stdout.write('\n[3/3] Checking active workers...')

        try:
            from veille_tech.celery import app

            # Create inspector to query worker stats
            inspector = app.control.inspect(timeout=5.0)

            # Get worker stats (returns None if no workers respond)
            stats = inspector.stats()

            if stats is None or len(stats) == 0:
                self.stdout.write(self.style.ERROR(
                    '  X No active workers found'
                ))
                self.stdout.write(
                    '    Hint: Start worker with: docker-compose up worker'
                )
                return False

            # Display active workers
            self.stdout.write(self.style.SUCCESS(
                f'  OK Found {len(stats)} active worker(s):'
            ))

            for worker_name, worker_stats in stats.items():
                pool_type = worker_stats.get('pool', {}).get('implementation', 'unknown')
                max_concurrency = worker_stats.get('pool', {}).get('max-concurrency', 'N/A')

                self.stdout.write(
                    f'    - {worker_name}'
                )
                self.stdout.write(
                    f'      Pool: {pool_type}, Concurrency: {max_concurrency}'
                )

            # Check active tasks
            active_tasks = inspector.active()
            if active_tasks:
                total_active = sum(len(tasks) for tasks in active_tasks.values())
                self.stdout.write(
                    f'    Active tasks: {total_active}'
                )

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'  X Worker inspection error: {str(e)}'
            ))
            self.stdout.write(
                '    Hint: Ensure Redis is running and workers are started'
            )
            return False
