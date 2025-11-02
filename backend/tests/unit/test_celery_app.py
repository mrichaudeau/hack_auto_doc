"""
Unit tests for Celery app initialization and configuration.

Tests verify that the Celery app is properly configured with:
- Correct broker and result backend URLs
- Task autodiscovery enabled
- Retry policy settings
- Queue configuration
- Worker pool and concurrency settings

These are fast unit tests that don't require a running worker.
"""

import pytest
from celery import Celery


@pytest.mark.unit
class TestCeleryAppInitialization:
    """Unit tests for Celery app initialization."""

    def test_celery_app_exists(self, celery_app):
        """Test that Celery app instance is created."""
        assert celery_app is not None
        assert isinstance(celery_app, Celery)
        assert celery_app.main == 'veille_tech'

    def test_celery_broker_url_configured(self, celery_app):
        """Test that broker URL is configured correctly."""
        broker_url = celery_app.conf.broker_url

        assert broker_url is not None
        assert 'redis://' in broker_url
        # Broker URL should point to Redis (either DB 0 for production or DB 15 for tests)
        assert ':6379/' in broker_url

    def test_celery_result_backend_configured(self, celery_app):
        """Test that result backend is configured correctly."""
        result_backend = celery_app.conf.result_backend

        assert result_backend is not None
        assert 'redis://' in result_backend
        # Result backend should point to Redis
        assert ':6379/' in result_backend

    def test_celery_task_serializer_json(self, celery_app):
        """Test that task serializer is set to JSON."""
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert 'json' in celery_app.conf.accept_content

    def test_celery_timezone_utc(self, celery_app):
        """Test that timezone is set to UTC."""
        assert celery_app.conf.timezone == 'UTC'

    def test_celery_task_autodiscovery(self, celery_app):
        """Test that task autodiscovery is enabled."""
        # Verify that tasks from veille_tech.tasks are discovered
        task_names = list(celery_app.tasks.keys())

        # Check for our defined tasks
        assert 'veille_tech.tasks.test_task' in task_names
        assert 'veille_tech.tasks.health_check_task' in task_names

        # Debug task should also be registered
        assert 'veille_tech.celery.debug_task' in task_names

    def test_celery_retry_configuration(self, celery_app):
        """Test that retry policy is configured correctly."""
        # Test default retry settings
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True
        assert celery_app.conf.task_default_retry_delay == 10

        # Test exponential backoff settings
        assert celery_app.conf.task_retry_backoff is True
        assert celery_app.conf.task_retry_backoff_max == 600  # 10 minutes
        assert celery_app.conf.task_retry_jitter is True

    def test_celery_time_limits_configured(self, celery_app):
        """Test that task time limits are configured."""
        assert celery_app.conf.task_soft_time_limit == 300  # 5 minutes
        assert celery_app.conf.task_time_limit == 600  # 10 minutes

    def test_celery_queue_configuration(self, celery_app):
        """Test that task queues are configured correctly."""
        # Test default queue
        assert celery_app.conf.task_default_queue == 'default'

        # Test queue priority settings
        assert celery_app.conf.task_queue_max_priority == 10
        assert celery_app.conf.task_default_priority == 5

        # Test task routing
        task_routes = celery_app.conf.task_routes

        assert task_routes is not None
        assert 'veille_tech.tasks.test_task' in task_routes
        assert task_routes['veille_tech.tasks.test_task']['queue'] == 'default'
        assert task_routes['veille_tech.tasks.test_task']['priority'] == 5

        assert 'veille_tech.tasks.health_check_task' in task_routes
        assert task_routes['veille_tech.tasks.health_check_task']['queue'] == 'default'
        assert task_routes['veille_tech.tasks.health_check_task']['priority'] == 3

    def test_celery_worker_configuration(self, celery_app):
        """Test that worker pool and concurrency are configured."""
        # Worker pool type (prefork, gevent, eventlet)
        worker_pool = celery_app.conf.worker_pool
        assert worker_pool in ['prefork', 'gevent', 'eventlet', 'solo']

        # Worker concurrency
        worker_concurrency = celery_app.conf.worker_concurrency
        assert isinstance(worker_concurrency, int)
        assert worker_concurrency > 0

        # Worker prefetch multiplier
        assert celery_app.conf.worker_prefetch_multiplier == 4

        # Max tasks per child (memory management)
        max_tasks = celery_app.conf.worker_max_tasks_per_child
        assert isinstance(max_tasks, int)
        assert max_tasks >= 0  # 0 means unlimited

    def test_celery_result_expiration(self, celery_app):
        """Test that task results have expiration configured."""
        result_expires = celery_app.conf.result_expires

        assert result_expires is not None
        assert isinstance(result_expires, int)
        assert result_expires == 3600  # 1 hour

    def test_celery_broker_connection_retry(self, celery_app):
        """Test that broker connection retry is enabled."""
        assert celery_app.conf.broker_connection_retry_on_startup is True


@pytest.mark.unit
class TestCeleryTaskRegistration:
    """Unit tests for task registration."""

    def test_test_task_registered(self, celery_app):
        """Test that test_task is registered correctly."""
        task = celery_app.tasks.get('veille_tech.tasks.test_task')

        assert task is not None
        assert task.name == 'veille_tech.tasks.test_task'
        assert task.max_retries == 3
        assert task.default_retry_delay == 10

    def test_health_check_task_registered(self, celery_app):
        """Test that health_check_task is registered correctly."""
        task = celery_app.tasks.get('veille_tech.tasks.health_check_task')

        assert task is not None
        assert task.name == 'veille_tech.tasks.health_check_task'
        assert task.max_retries == 3

    def test_debug_task_registered(self, celery_app):
        """Test that debug_task is registered correctly."""
        task = celery_app.tasks.get('veille_tech.celery.debug_task')

        assert task is not None
        assert task.name == 'veille_tech.celery.debug_task'


@pytest.mark.unit
class TestCeleryConfiguration:
    """Unit tests for Celery configuration loading."""

    def test_celery_loads_django_settings(self, celery_app):
        """Test that Celery loads configuration from Django settings."""
        # Verify that configuration is loaded from Django settings
        # by checking that settings match expected values from base.py

        # Check serialization settings
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'

        # Check timezone
        assert celery_app.conf.timezone == 'UTC'

        # Check retry settings
        assert celery_app.conf.task_acks_late is True
        assert celery_app.conf.task_reject_on_worker_lost is True

    def test_celery_namespace_prefix(self, celery_app):
        """Test that Celery uses CELERY_ namespace prefix."""
        # The config_from_object with namespace='CELERY' means
        # Django settings like CELERY_BROKER_URL are mapped to
        # Celery config broker_url

        # Verify broker_url is set (proves namespace mapping works)
        assert celery_app.conf.broker_url is not None

        # Verify result_backend is set
        assert celery_app.conf.result_backend is not None
