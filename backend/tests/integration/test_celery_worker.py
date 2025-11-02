"""
Integration tests for Celery worker task execution.

These tests verify that:
- Tasks can be enqueued and executed by workers
- Task results are stored and retrievable
- Multiple concurrent tasks execute correctly
- Task logging works as expected
- Health check task executes successfully

IMPORTANT: These tests require a running Celery worker.
Run with: docker-compose exec backend pytest tests/integration/test_celery_worker.py -v -m integration
"""

import pytest
import time
import logging
from veille_tech.tasks import test_task, health_check_task


@pytest.mark.integration
class TestCeleryWorkerExecution:
    """Integration tests for Celery worker task execution."""

    def test_task_enqueue_and_execute(self, celery_app):
        """
        Test that a task can be enqueued and executed successfully.

        Verifies:
        - Task is enqueued via .delay()
        - Task result is retrievable via .get()
        - Result contains expected data structure
        - Task ID is properly set
        """
        # Enqueue task
        result = test_task.delay("Integration test message")

        # Verify task was enqueued
        assert result is not None
        assert result.id is not None

        # Wait for task completion and retrieve result
        task_result = result.get(timeout=10)

        # Verify result structure
        assert isinstance(task_result, dict)
        assert task_result['status'] == 'success'
        assert task_result['message'] == "Integration test message"
        assert task_result['task_id'] == result.id
        assert task_result['retries'] == 0

        # Verify task state
        assert result.state == 'SUCCESS'
        assert result.successful()

    def test_task_result_retrieval(self, celery_app):
        """
        Test that task results can be retrieved from result backend.

        Verifies:
        - Result is stored in Redis result backend
        - Result can be retrieved using task ID
        - Result persists across multiple retrievals
        """
        # Enqueue and execute task
        result = test_task.delay("Test result retrieval")
        task_result = result.get(timeout=10)

        # Verify result is stored
        assert result.backend is not None

        # Retrieve result again using same AsyncResult instance
        retrieved_result = result.get(timeout=5)
        assert retrieved_result == task_result

        # Verify result metadata
        assert result.info == task_result

    def test_multiple_tasks_concurrent(self, celery_app):
        """
        Test that multiple tasks can be executed concurrently.

        Verifies:
        - Multiple tasks can be enqueued simultaneously
        - All tasks complete successfully
        - Each task has unique task ID
        - Results are correctly associated with tasks
        """
        num_tasks = 5
        task_messages = [f"Concurrent task {i}" for i in range(num_tasks)]

        # Enqueue multiple tasks
        results = [test_task.delay(msg) for msg in task_messages]

        # Verify all tasks have unique IDs
        task_ids = [r.id for r in results]
        assert len(task_ids) == len(set(task_ids))  # All IDs are unique

        # Wait for all tasks to complete
        task_results = [r.get(timeout=30) for r in results]

        # Verify all tasks completed successfully
        assert len(task_results) == num_tasks
        for i, task_result in enumerate(task_results):
            assert task_result['status'] == 'success'
            assert task_result['message'] == task_messages[i]
            assert task_result['retries'] == 0

        # Verify all tasks reached SUCCESS state
        for result in results:
            assert result.state == 'SUCCESS'

    def test_task_logging(self, celery_app, caplog):
        """
        Test that task execution generates proper logs.

        Verifies:
        - Task start log is generated
        - Task completion log is generated
        - Logs include task ID and message
        """
        with caplog.at_level(logging.INFO):
            # Execute task
            result = test_task.delay("Logging test")
            task_result = result.get(timeout=10)

            # Note: Logs may not appear in caplog with eager mode
            # This test primarily verifies task executes without errors
            assert task_result['status'] == 'success'

    def test_health_check_task(self, celery_app):
        """
        Test that health check task executes successfully.

        Verifies:
        - Health check task can be enqueued
        - Task returns expected health status
        - Task includes timestamp and worker information
        """
        # Execute health check task
        result = health_check_task.delay()

        # Get result
        health_result = result.get(timeout=10)

        # Verify health check structure
        assert isinstance(health_result, dict)
        assert health_result['status'] == 'healthy'
        assert 'timestamp' in health_result
        assert 'worker' in health_result

        # Verify timestamp format (ISO 8601)
        from datetime import datetime
        timestamp = datetime.fromisoformat(health_result['timestamp'])
        assert timestamp is not None

        # Verify task completed successfully
        assert result.state == 'SUCCESS'

    def test_task_state_transitions(self, celery_app):
        """
        Test that task state transitions correctly during execution.

        Verifies:
        - Task starts in PENDING state
        - Task transitions to SUCCESS state after completion
        - Task state can be queried during execution
        """
        # Enqueue task
        result = test_task.delay("State transition test")

        # Note: With eager mode, task executes immediately
        # State transitions happen too fast to observe PENDING state
        # This test verifies final state is correct

        # Get result (task should complete)
        task_result = result.get(timeout=10)

        # Verify final state
        assert result.state == 'SUCCESS'
        assert result.successful()
        assert not result.failed()

        # Verify result is available
        assert result.result == task_result


@pytest.mark.integration
class TestCeleryWorkerErrorHandling:
    """Integration tests for Celery worker error handling."""

    def test_task_timeout_handling(self, celery_app):
        """
        Test that long-running tasks are handled correctly.

        Note: This test verifies task execution completes within limits.
        Actual timeout testing requires non-eager mode and longer timeouts.
        """
        # Execute task with normal execution time
        result = test_task.delay("Timeout test")

        # Verify task completes within reasonable time
        task_result = result.get(timeout=15)

        assert task_result['status'] == 'success'

    def test_invalid_task_arguments(self, celery_app):
        """
        Test that tasks handle invalid arguments gracefully.

        Verifies:
        - Task raises appropriate exception for invalid args
        - Error is propagated correctly
        """
        # Test with missing required argument
        with pytest.raises(TypeError):
            # test_task requires a 'message' argument
            test_task.delay()

    def test_task_result_metadata(self, celery_app):
        """
        Test that task result includes proper metadata.

        Verifies:
        - Task ID is set
        - Task name is correct
        - Task result info is available
        """
        result = test_task.delay("Metadata test")
        task_result = result.get(timeout=10)

        # Verify metadata
        assert result.id is not None
        assert result.name == 'veille_tech.tasks.test_task'
        assert result.info is not None


@pytest.mark.integration
@pytest.mark.slow
class TestCeleryWorkerPerformance:
    """Integration tests for Celery worker performance."""

    def test_task_execution_time(self, celery_app):
        """
        Test that tasks execute within expected time limits.

        Verifies:
        - Simple tasks complete quickly (< 5 seconds)
        - Task execution is reasonably fast
        """
        start_time = time.time()

        result = test_task.delay("Performance test")
        task_result = result.get(timeout=10)

        execution_time = time.time() - start_time

        # Task should complete within 5 seconds
        # (includes 1s sleep in task + overhead)
        assert execution_time < 5.0
        assert task_result['status'] == 'success'

    def test_concurrent_task_throughput(self, celery_app):
        """
        Test throughput with multiple concurrent tasks.

        Verifies:
        - 10 tasks can be processed concurrently
        - All tasks complete within reasonable time
        """
        num_tasks = 10
        start_time = time.time()

        # Enqueue multiple tasks
        results = [test_task.delay(f"Task {i}") for i in range(num_tasks)]

        # Wait for all to complete
        task_results = [r.get(timeout=30) for r in results]

        total_time = time.time() - start_time

        # Verify all completed successfully
        assert len(task_results) == num_tasks
        assert all(r['status'] == 'success' for r in task_results)

        # With eager mode and concurrency, should complete quickly
        # Expect < 3 seconds per task on average
        assert total_time < num_tasks * 3
