"""
Celery tasks for Technology Watch Platform.

This module contains task definitions for asynchronous processing,
including test tasks and future AI pipeline tasks.
"""

import logging
import time
from typing import Dict, Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name='veille_tech.tasks.test_task'
)
def test_task(self, message: str) -> Dict[str, Any]:
    """
    Sample task for testing Celery worker execution.

    This task demonstrates proper task structure with:
    - Logging for observability
    - Error handling with retry logic
    - Exponential backoff on failure
    - Structured return values

    Args:
        self: Task instance (provided by bind=True)
        message: Test message to process

    Returns:
        dict: Task execution result with:
            - status: 'success' or 'failed'
            - message: The processed message
            - task_id: Unique task identifier
            - retries: Number of retry attempts

    Raises:
        Exception: Re-raised after max retries exhausted
    """
    task_id = self.request.id
    retry_count = self.request.retries

    try:
        logger.info(
            f"Executing test_task [task_id={task_id}] "
            f"[retry={retry_count}] [message={message}]"
        )

        # Simulate work
        time.sleep(1)

        # Log success
        logger.info(f"test_task completed successfully [task_id={task_id}]")

        return {
            'status': 'success',
            'message': message,
            'task_id': task_id,
            'retries': retry_count
        }

    except Exception as exc:
        logger.error(
            f"test_task failed [task_id={task_id}] "
            f"[retry={retry_count}] [error={str(exc)}]"
        )

        # Retry with exponential backoff: 10s, 20s, 40s, 80s...
        # countdown = base_delay * (2 ** retry_count)
        countdown = 10 * (2 ** retry_count)

        # Re-raise exception to trigger retry
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name='veille_tech.tasks.health_check_task'
)
def health_check_task(self) -> Dict[str, Any]:
    """
    Health check task for monitoring worker availability.

    This task can be called periodically to verify that:
    - Workers are running and accepting tasks
    - Task routing is functioning
    - Basic task execution works

    Returns:
        dict: Health check result with:
            - status: 'healthy'
            - timestamp: UTC timestamp of execution
            - worker: Worker hostname
    """
    from datetime import datetime

    worker = self.request.hostname

    logger.info(f"Health check executed [worker={worker}]")

    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'worker': worker
    }
