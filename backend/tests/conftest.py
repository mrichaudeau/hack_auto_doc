"""
Pytest configuration and shared fixtures for veille_tech tests.

This module provides reusable fixtures for:
- Celery app configuration
- Redis client with test database
- Database fixtures
- Mock configurations for external services
"""

import pytest
from typing import Generator
import redis
from django.contrib.auth.models import User


@pytest.fixture(scope='session')
def celery_config():
    """
    Celery configuration for testing.

    Uses eager mode for synchronous task execution in tests.
    """
    return {
        'task_always_eager': True,
        'task_eager_propagates': True,
        'broker_url': 'redis://redis:6379/15',
        'result_backend': 'redis://redis:6379/15',
    }


@pytest.fixture
def celery_app():
    """
    Provide Celery app configured for testing.

    Returns:
        Celery: Celery app instance with eager mode enabled
    """
    from veille_tech.celery import app

    # Store original config
    original_config = {
        'task_always_eager': app.conf.task_always_eager,
        'task_eager_propagates': app.conf.task_eager_propagates,
    }

    # Configure for testing
    app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )

    yield app

    # Restore original config
    app.conf.update(**original_config)


@pytest.fixture
def celery_app_non_eager():
    """
    Provide Celery app with eager mode disabled.

    Use this fixture for integration tests that need to test
    actual task queuing and worker execution.

    Returns:
        Celery: Celery app instance with eager mode disabled
    """
    from veille_tech.celery import app

    # Store original config
    original_config = {
        'task_always_eager': app.conf.task_always_eager,
        'task_eager_propagates': app.conf.task_eager_propagates,
    }

    # Configure for integration testing
    app.conf.update(
        task_always_eager=False,
        task_eager_propagates=False,
    )

    yield app

    # Restore original config
    app.conf.update(**original_config)


@pytest.fixture
def redis_client() -> Generator[redis.Redis, None, None]:
    """
    Provide Redis client connected to test database (DB 15).

    Automatically flushes the test database after each test to ensure isolation.

    Yields:
        redis.Redis: Redis client instance
    """
    client = redis.Redis(
        host='redis',
        port=6379,
        db=15,  # Test database
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    # Verify connection
    try:
        client.ping()
    except redis.ConnectionError as e:
        pytest.skip(f"Redis not available: {e}")

    yield client

    # Clean up after test
    try:
        client.flushdb()
    except redis.ConnectionError:
        pass  # Connection lost, cleanup not needed
    finally:
        client.close()


@pytest.fixture
def test_user(db) -> User:
    """
    Create a test user for authentication tests.

    Args:
        db: pytest-django database fixture

    Returns:
        User: Django user instance
    """
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
    )


@pytest.fixture
def admin_user(db) -> User:
    """
    Create an admin user for permission tests.

    Args:
        db: pytest-django database fixture

    Returns:
        User: Django admin user instance
    """
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
    )


@pytest.fixture
def mock_google_ai_api(monkeypatch):
    """
    Mock Google AI Studio API responses.

    Use this fixture to avoid actual API calls in tests.
    """
    def mock_generate_content(*args, **kwargs):
        return {
            'candidates': [{
                'content': {
                    'parts': [{
                        'text': 'Mocked AI response'
                    }]
                }
            }]
        }

    monkeypatch.setattr(
        'veille_tech.services.google_ai.generate_content',
        mock_generate_content
    )


@pytest.fixture
def mock_firecrawl_api(monkeypatch):
    """
    Mock Firecrawl API responses.

    Use this fixture to avoid actual scraping API calls in tests.
    """
    def mock_scrape(*args, **kwargs):
        return {
            'data': {
                'markdown': '# Mocked Content\n\nTest scraped content',
                'html': '<h1>Mocked Content</h1><p>Test scraped content</p>',
                'metadata': {
                    'title': 'Test Page',
                    'description': 'Test description',
                }
            }
        }

    monkeypatch.setattr(
        'veille_tech.services.firecrawl.scrape',
        mock_scrape
    )


@pytest.fixture
def cleanup_celery_tasks():
    """
    Clean up Celery task registry after tests.

    Prevents task registration conflicts between tests.
    """
    from celery import current_app

    # Store registered tasks
    original_tasks = dict(current_app.tasks)

    yield

    # Restore original task registry
    current_app.tasks = original_tasks
