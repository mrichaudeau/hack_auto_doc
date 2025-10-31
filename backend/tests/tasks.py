from celery import shared_task


@shared_task
def test_task():
    """Sample Celery task for testing."""
    return "Task executed successfully"
