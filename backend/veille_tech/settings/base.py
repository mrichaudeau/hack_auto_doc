"""
Django base settings for veille_tech project.
"""

import sys
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# Application definition
INSTALLED_APPS = [
    # Project apps - core must be first for infrastructure migrations (pgvector)
    'apps.core',  # Core infrastructure app (pgvector extension, cross-cutting concerns)

    # Main application
    'veille_tech.apps.VeilleTechConfig',  # Main app with config validation

    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'veille_tech.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'veille_tech.wsgi.application'

# Database configuration
# ============================================
# PostgreSQL Configuration for Migrations
# ============================================
# This configuration is optimized for database migrations and production use.
#
# Connection Pooling (CONN_MAX_AGE):
#   - Set to 60 seconds for persistent connections
#   - Reduces overhead of creating new connections for each request
#   - IMPORTANT: Connection pooling improves migration performance significantly
#
# Connection Health Checks (conn_health_checks):
#   - Enabled to verify connection validity before reuse
#   - Prevents "server closed the connection unexpectedly" errors
#   - Critical for long-running migrations and background tasks
#
# Atomic Requests (ATOMIC_REQUESTS):
#   - Enabled below for transaction safety
#   - Each request wrapped in database transaction
#   - Automatic rollback on exceptions
#   - IMPORTANT: Ensures data consistency during migrations
#
# Migration Privilege Requirements:
#   - pgvector extension creation requires SUPERUSER privilege
#   - Grant with: ALTER USER veille_tech_user WITH SUPERUSER;
#   - For production: Use restricted privilege user for app, superuser for migrations only
#   - See migration 0001_enable_pgvector.py for extension setup
#
# Environment Variables:
#   - DATABASE_URL (recommended): Full connection string (parsed by dj-database-url)
#     Example: postgresql://user:password@host:port/database
#   - Alternative: Individual variables (POSTGRES_USER, POSTGRES_PASSWORD, etc.)
#
# Connection String Format:
#   postgresql://[user[:password]@][host][:port][/dbname][?param1=value1&...]

# Try DATABASE_URL first (recommended), fall back to individual variables
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgresql://{config('POSTGRES_USER', default='veille_tech_user')}:"
                f"{config('POSTGRES_PASSWORD', default='postgres')}@"
                f"{config('POSTGRES_HOST', default='db')}:"
                f"{config('POSTGRES_PORT', default='5432')}/"
                f"{config('POSTGRES_DB', default='veille_tech_db')}",
        conn_max_age=60,  # 60 seconds connection pooling
        conn_health_checks=True,  # Verify connection validity before reuse
        ssl_require=False,  # Set to True in production for encrypted connections
    )
}

# Atomic Requests - Transaction Safety
# Wraps each request in a database transaction for data consistency
# Critical for migration safety and preventing partial data updates
DATABASES['default']['ATOMIC_REQUESTS'] = True

# Test database
if 'test' in sys.argv:
    DATABASES['default']['NAME'] = 'test_veille_tech'

# Cache Configuration (Redis DB 1)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL', default='redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'KEY_PREFIX': 'techwatch',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# Celery Configuration (Redis DB 0)
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour

# Task retry configuration
CELERY_TASK_ACKS_LATE = True  # Acknowledge task after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Re-queue if worker dies
CELERY_TASK_DEFAULT_RETRY_DELAY = 10  # 10 seconds
CELERY_TASK_MAX_RETRIES = 3  # Retry up to 3 times

# Exponential backoff retry configuration
CELERY_TASK_RETRY_BACKOFF = True  # Enable exponential backoff
CELERY_TASK_RETRY_BACKOFF_MAX = 600  # Max 10 minutes between retries
CELERY_TASK_RETRY_JITTER = True  # Add randomness to prevent thundering herd

# Task time limits and graceful shutdown
# Soft limit (300s): Raises SoftTimeLimitExceeded exception for graceful cleanup
# Hard limit (600s): Forcefully terminates task if cleanup doesn't complete
# Watchdog auto-reload: Monitors Python files for changes and restarts worker
#   - IMPORTANT: Windows users MUST use Docker Desktop with WSL2 backend (not Hyper-V)
#   - WSL2 provides proper filesystem events for file watching
#   - Without WSL2, watchdog may not detect file changes reliably
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes soft limit (allows cleanup)
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes hard limit (forced termination)

# Task queue configuration
# Two queues with different priorities for workload management:
#   - 'default': Standard tasks (e.g., test_task, health_check_task) - Priority 5
#   - 'high_priority': Urgent tasks (e.g., ai_pipeline, urgent_* patterns) - Priority 10
# Task routing automatically assigns tasks to queues based on name patterns
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUE_MAX_PRIORITY = 10  # Maximum priority value for task queuing
CELERY_TASK_DEFAULT_PRIORITY = 5  # Default priority for unspecified tasks

# Task routing rules
# Maps task name patterns to specific queues for workload segregation
# Example patterns:
#   - 'veille_tech.tasks.test_task' -> 'default' queue
#   - 'veille_tech.tasks.urgent_*' -> 'high_priority' queue
#   - 'ai_pipeline.*' -> 'high_priority' queue (AI processing tasks)
CELERY_TASK_ROUTES = {
    # Test and health check tasks go to default queue
    'veille_tech.tasks.test_task': {
        'queue': 'default',
        'priority': 5,
    },
    'veille_tech.tasks.health_check_task': {
        'queue': 'default',
        'priority': 3,
    },
    # AI pipeline tasks get high priority queue
    # Pattern matching: any task starting with 'ai_pipeline.' or 'urgent_'
    'ai_pipeline.*': {
        'queue': 'high_priority',
        'priority': 10,
    },
    'urgent_*': {
        'queue': 'high_priority',
        'priority': 10,
    },
}

# Worker prefetch multiplier
# Controls how many tasks each worker process prefetches from the queue
# Higher values improve throughput but reduce task distribution fairness
# Recommended: 4 for balanced performance/fairness (4 tasks per worker process)
CELERY_WORKER_PREFETCH_MULTIPLIER = 4

# Worker pool and concurrency configuration
# Pool Types:
#   - 'prefork' (default): Multiprocessing pool, best for CPU-bound tasks
#     Each worker is a separate process (fork), isolated memory space
#     Memory usage: ~200-500MB per worker process
#     Best for: AI pipeline tasks, data processing, CPU-intensive operations
#   - 'gevent': Greenlet-based async pool, best for I/O-bound tasks
#     Single process with lightweight greenlets (cooperative multitasking)
#     Memory usage: ~100-200MB total (shared memory)
#     Best for: HTTP requests, database queries, file I/O operations
#   - 'eventlet': Similar to gevent, alternative async implementation
#     Requires: pip install celery[eventlet]
#
# Concurrency Settings:
#   - Development: 2-4 workers (lower memory usage, easier debugging)
#   - Production: CPU cores for prefork, 100-500 for gevent/eventlet
#   - AI Pipeline: 4-8 workers (balance throughput vs memory for LLM calls)
CELERY_WORKER_POOL = config('CELERY_WORKER_POOL', default='prefork')
CELERY_WORKER_CONCURRENCY = config('CELERY_WORKER_CONCURRENCY', default=4, cast=int)

# Worker task limits for memory management
# Restart worker process after executing N tasks to prevent memory leaks
# Set to 0 to disable (worker never restarts based on task count)
# Recommended: 100-1000 for long-running workers with potential memory leaks
CELERY_WORKER_MAX_TASKS_PER_CHILD = config('CELERY_WORKER_MAX_TASKS_PER_CHILD', default=100, cast=int)

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000',
    cast=Csv()
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Additional static file finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AI/ML API Keys
GOOGLE_AI_STUDIO_API_KEY = config('GOOGLE_AI_STUDIO_API_KEY')
FIRECRAWL_API_KEY = config('FIRECRAWL_API_KEY')

# JWT Configuration
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ACCESS_TOKEN_LIFETIME_MINUTES = config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)
JWT_REFRESH_TOKEN_LIFETIME_DAYS = config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
JWT_ALGORITHM = config('JWT_ALGORITHM', default='HS256')

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@techwatch.local')

# Logging configuration
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
}
