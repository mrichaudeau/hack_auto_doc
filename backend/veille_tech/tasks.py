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


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name='veille_tech.tasks.failing_test_task'
)
def failing_test_task(self, fail_count: int = 2) -> Dict[str, Any]:
    """
    Test task that fails N times before succeeding (for retry testing).

    This task is designed for testing retry behavior:
    - Fails on first N attempts
    - Succeeds after fail_count retries
    - Uses exponential backoff
    - Logs all retry attempts

    Args:
        self: Task instance (provided by bind=True)
        fail_count: Number of times to fail before succeeding (default: 2)

    Returns:
        dict: Task execution result with:
            - status: 'success' (only after retries)
            - retries: Number of retry attempts made
            - fail_count: Configured failure threshold

    Raises:
        Exception: Intentional failure to trigger retry (before reaching fail_count)
    """
    task_id = self.request.id
    retry_count = self.request.retries

    logger.info(
        f"Executing failing_test_task [task_id={task_id}] "
        f"[retry={retry_count}/{self.max_retries}] "
        f"[fail_count={fail_count}]"
    )

    # Fail if we haven't reached the fail_count threshold yet
    if retry_count < fail_count:
        error_msg = f"Intentional failure (retry {retry_count}/{fail_count})"
        logger.warning(
            f"failing_test_task intentionally failing "
            f"[task_id={task_id}] [retry={retry_count}] [reason={error_msg}]"
        )

        # Retry with exponential backoff
        countdown = 5 * (2 ** retry_count)  # 5s, 10s, 20s, 40s...

        raise self.retry(
            exc=Exception(error_msg),
            countdown=countdown
        )

    # Success after enough retries
    logger.info(
        f"failing_test_task succeeded after {retry_count} retries "
        f"[task_id={task_id}]"
    )

    return {
        'status': 'success',
        'retries': retry_count,
        'fail_count': fail_count,
        'task_id': task_id
    }
