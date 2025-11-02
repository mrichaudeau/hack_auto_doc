"""
Test settings for veille_tech project.

This configuration optimizes for fast test execution by:
- Using in-memory SQLite database
- Enabling Celery eager mode (synchronous task execution)
- Disabling migrations
- Using fast password hashing
- Using separate Redis database for tests (DB 15)
"""

from .base import *

# Use in-memory SQLite database for faster tests
# For integration tests requiring PostgreSQL features, override in conftest.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
    }
}

# Celery Configuration for Tests
# Run tasks synchronously in tests (no worker needed for unit tests)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use separate Redis database for tests to avoid conflicts
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/15')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/15')

# Cache configuration for tests (Redis DB 15)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL', default='redis://redis:6379/15'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'test_techwatch',
        }
    }
}

# Disable migrations for faster test database setup
class DisableMigrations:
    """Disable migrations during test execution."""
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Speed up password hashing in tests (NEVER use in production)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug mode for consistent test behavior
DEBUG = False
TEMPLATE_DEBUG = False

# Test email backend (no actual emails sent)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Logging configuration for tests (reduced verbosity)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',  # Only show warnings and errors in tests
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Disable CSRF protection in tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Make tests run faster by using weaker security
SECRET_KEY = 'test-secret-key-not-for-production'
