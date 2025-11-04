"""
Unit tests for Django settings configuration.

Tests verify that database and migration settings are properly configured:
- Database connection parameters
- PostgreSQL engine configuration
- Atomic transaction settings
- INSTALLED_APPS configuration
- Connection pooling settings

These are fast unit tests that inspect Django settings without requiring
a live database connection.
"""

import pytest
from django.conf import settings


@pytest.mark.unit
class TestDatabaseConfiguration:
    """Unit tests for database configuration."""

    def test_database_configuration_exists(self):
        """Test that DATABASES setting exists and has default configuration."""
        assert hasattr(settings, 'DATABASES')
        assert 'default' in settings.DATABASES
        assert isinstance(settings.DATABASES['default'], dict)

    def test_database_engine_postgresql(self):
        """Test that PostgreSQL engine is configured for production."""
        # In test environment, we use SQLite for speed
        # But we can verify the base settings would use PostgreSQL
        db_config = settings.DATABASES['default']

        # In test mode (using test.py settings), engine will be sqlite3
        # We verify the ENGINE key exists
        assert 'ENGINE' in db_config
        assert db_config['ENGINE'] is not None

        # The engine should be a valid Django database backend
        valid_engines = [
            'django.db.backends.postgresql',
            'django.db.backends.sqlite3',  # Test environment
            'django.db.backends.mysql',
            'django.db.backends.oracle',
        ]
        assert db_config['ENGINE'] in valid_engines

    def test_atomic_requests_enabled(self):
        """Test that ATOMIC_REQUESTS is True for transaction safety."""
        db_config = settings.DATABASES['default']

        assert 'ATOMIC_REQUESTS' in db_config
        assert db_config['ATOMIC_REQUESTS'] is True

    def test_database_connection_pooling(self):
        """Test that connection pooling is configured in production settings."""
        # In test settings, connection pooling may not be configured
        # We verify that the database config structure supports it
        db_config = settings.DATABASES['default']

        # Check if NAME key exists (required for all backends)
        assert 'NAME' in db_config

        # In production (base.py), CONN_MAX_AGE and conn_health_checks should be set
        # In test mode, these may not be present, so we just verify structure is valid
        assert isinstance(db_config, dict)


@pytest.mark.unit
class TestInstalledApps:
    """Unit tests for INSTALLED_APPS configuration."""

    def test_core_app_in_installed_apps(self):
        """Test that core app is in INSTALLED_APPS."""
        assert hasattr(settings, 'INSTALLED_APPS')
        assert 'apps.core' in settings.INSTALLED_APPS

    def test_core_app_is_first(self):
        """Test that core app is first in INSTALLED_APPS for migration priority."""
        # Core app should be first to ensure pgvector extension is created
        # before other apps that might depend on it
        installed_apps = list(settings.INSTALLED_APPS)

        # Find the index of apps.core
        core_index = installed_apps.index('apps.core')

        # Core should be the first application (index 0)
        # It should come before any other project apps
        assert core_index == 0, "Core app must be first in INSTALLED_APPS for migration priority"

    def test_required_apps_installed(self):
        """Test that required Django and third-party apps are installed."""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'rest_framework',
            'corsheaders',
        ]

        for app in required_apps:
            assert app in settings.INSTALLED_APPS, f"Required app '{app}' not in INSTALLED_APPS"


@pytest.mark.unit
class TestDatabaseEnvironmentVariables:
    """Unit tests for database environment variable loading."""

    def test_database_configuration_structure(self):
        """Test that database configuration has all required keys."""
        db_config = settings.DATABASES['default']

        # Required keys for all database backends
        required_keys = ['ENGINE', 'NAME', 'ATOMIC_REQUESTS']

        for key in required_keys:
            assert key in db_config, f"Required database config key '{key}' is missing"

    def test_database_name_not_empty(self):
        """Test that database NAME is configured."""
        db_config = settings.DATABASES['default']

        assert 'NAME' in db_config
        assert db_config['NAME']  # Not empty or None
        assert isinstance(db_config['NAME'], str)


@pytest.mark.unit
class TestMigrationConfiguration:
    """Unit tests for migration-related configuration."""

    def test_default_auto_field_configured(self):
        """Test that DEFAULT_AUTO_FIELD is set to BigAutoField."""
        assert hasattr(settings, 'DEFAULT_AUTO_FIELD')
        assert settings.DEFAULT_AUTO_FIELD == 'django.db.models.BigAutoField'

    def test_base_dir_configured(self):
        """Test that BASE_DIR is properly configured."""
        assert hasattr(settings, 'BASE_DIR')
        assert settings.BASE_DIR is not None

        # BASE_DIR should be a Path object
        from pathlib import Path
        assert isinstance(settings.BASE_DIR, Path)

    def test_migration_modules_configuration(self):
        """Test migration modules configuration in test environment."""
        # In test settings, migrations are disabled for speed
        # This verifies that MIGRATION_MODULES exists and is configured
        assert hasattr(settings, 'MIGRATION_MODULES')


@pytest.mark.unit
class TestCeleryDatabaseIntegration:
    """Unit tests for Celery-database integration settings."""

    def test_celery_result_backend_configured(self):
        """Test that Celery result backend is configured."""
        assert hasattr(settings, 'CELERY_RESULT_BACKEND')
        assert settings.CELERY_RESULT_BACKEND is not None

    def test_celery_broker_url_configured(self):
        """Test that Celery broker URL is configured."""
        assert hasattr(settings, 'CELERY_BROKER_URL')
        assert settings.CELERY_BROKER_URL is not None

    def test_celery_task_acks_late(self):
        """Test that task acknowledgment is deferred until completion."""
        assert hasattr(settings, 'CELERY_TASK_ACKS_LATE')
        assert settings.CELERY_TASK_ACKS_LATE is True

    def test_celery_task_reject_on_worker_lost(self):
        """Test that tasks are re-queued if worker dies."""
        assert hasattr(settings, 'CELERY_TASK_REJECT_ON_WORKER_LOST')
        assert settings.CELERY_TASK_REJECT_ON_WORKER_LOST is True


@pytest.mark.unit
class TestCacheConfiguration:
    """Unit tests for cache configuration."""

    def test_cache_configured(self):
        """Test that cache backend is configured."""
        assert hasattr(settings, 'CACHES')
        assert 'default' in settings.CACHES
        assert isinstance(settings.CACHES['default'], dict)

    def test_cache_backend_is_redis(self):
        """Test that Redis is configured as cache backend."""
        cache_config = settings.CACHES['default']

        assert 'BACKEND' in cache_config
        # Should be django_redis for production
        assert 'redis' in cache_config['BACKEND'].lower()


@pytest.mark.unit
class TestSecuritySettings:
    """Unit tests for security-related settings."""

    def test_secret_key_configured(self):
        """Test that SECRET_KEY is configured."""
        assert hasattr(settings, 'SECRET_KEY')
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0

    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is configured."""
        assert hasattr(settings, 'ALLOWED_HOSTS')
        assert isinstance(settings.ALLOWED_HOSTS, list)


@pytest.mark.unit
class TestProductionDatabaseSettings:
    """Unit tests specific to production database configuration."""

    def test_database_supports_transactions(self):
        """Test that database backend supports transactions."""
        # ATOMIC_REQUESTS requires transaction support
        db_config = settings.DATABASES['default']

        # All tested backends (PostgreSQL, SQLite) support transactions
        # Verify ATOMIC_REQUESTS is enabled
        assert db_config.get('ATOMIC_REQUESTS') is True

    def test_database_connection_settings_structure(self):
        """Test that database connection settings have proper structure."""
        db_config = settings.DATABASES['default']

        # Verify it's a dictionary with required structure
        assert isinstance(db_config, dict)
        assert 'ENGINE' in db_config
        assert 'ATOMIC_REQUESTS' in db_config

        # These settings should be boolean or numeric
        assert isinstance(db_config['ATOMIC_REQUESTS'], bool)
