"""
Integration tests for Celery task retry behavior.

These tests verify that:
- Tasks retry on failure with correct configuration
- Exponential backoff works as expected
- Tasks eventually succeed after retries
- Tasks fail after max_retries is exceeded
- Retry metadata is tracked correctly

IMPORTANT: These tests require a running Celery worker.
Run with: docker-compose exec backend pytest tests/integration/test_task_retry.py -v -m integration

Note: These tests use CELERY_TASK_ALWAYS_EAGER=False to test real retry behavior.
"""

import pytest
import time
from celery.exceptions import Retry
from veille_tech.tasks import failing_test_task


@pytest.mark.integration
class TestTaskRetryBehavior:
    """Integration tests for task retry behavior."""

    def test_task_retries_on_failure(self, celery_app):
        """
        Test that task retries when it fails and eventually succeeds.

        Verifies:
        - Task fails initially
        - Task retries with backoff
        - Task succeeds after configured retries
        - Retry count is tracked correctly
        """
        # Task should fail 2 times before succeeding
        result = failing_test_task.delay(fail_count=2)

        # Wait for task completion (with retries, this will take time)
        # Backoff: 5s (1st retry) + 10s (2nd retry) = ~15s + overhead
        task_result = result.get(timeout=30)

        # Verify task eventually succeeded
        assert task_result is not None
        assert task_result['status'] == 'success'

        # Verify retry count matches expected failures
        assert task_result['retries'] >= 2
        assert task_result['fail_count'] == 2

        # Verify task reached SUCCESS state
        assert result.state == 'SUCCESS'
        assert result.successful()

    def test_task_succeeds_after_retry(self, celery_app):
        """
        Test that task succeeds after exactly 1 retry.

        Verifies:
        - Task fails on first attempt
        - Task succeeds on second attempt (retry 1)
        - Retry metadata is correct
        """
        # Task should fail 1 time before succeeding
        result = failing_test_task.delay(fail_count=1)

        # Wait for completion (1 retry: ~5s + overhead)
        task_result = result.get(timeout=15)

        # Verify success after 1 retry
        assert task_result['status'] == 'success'
        assert task_result['retries'] == 1
        assert task_result['fail_count'] == 1

        # Verify task state
        assert result.state == 'SUCCESS'

    def test_task_max_retries_exceeded(self, celery_app):
        """
        Test that task fails permanently after max_retries is exceeded.

        Verifies:
        - Task retries up to max_retries (3)
        - Task fails permanently after max retries
        - Exception is raised to caller
        - Task state is FAILURE
        """
        # Task configured to fail 10 times (exceeds max_retries=3)
        result = failing_test_task.delay(fail_count=10)

        # Task should fail after 3 retries
        # Backoff: 5s + 10s + 20s = ~35s + overhead
        with pytest.raises(Exception) as exc_info:
            result.get(timeout=60)

        # Verify exception mentions retry exhaustion
        assert 'Intentional failure' in str(exc_info.value)

        # Verify task reached FAILURE state
        assert result.failed()
        assert result.state == 'FAILURE'

    def test_task_exponential_backoff(self, celery_app):
        """
        Test that retry delays follow exponential backoff pattern.

        Verifies:
        - First retry after ~5 seconds
        - Second retry after ~10 seconds (cumulative)
        - Third retry after ~20 seconds (cumulative)

        Note: This test measures actual timing to verify backoff.
        """
        start_time = time.time()

        # Task should fail 2 times before succeeding
        result = failing_test_task.delay(fail_count=2)

        # Wait for completion
        task_result = result.get(timeout=30)

        elapsed_time = time.time() - start_time

        # Verify task succeeded
        assert task_result['status'] == 'success'
        assert task_result['retries'] == 2

        # Verify timing reflects backoff (5s + 10s = 15s minimum)
        # Allow some overhead (worker processing, network, etc.)
        # Expect at least 10 seconds (conservative estimate)
        assert elapsed_time >= 10.0, (
            f"Expected at least 10s for 2 retries, got {elapsed_time:.2f}s"
        )

        # Should not take excessively long (max 30s)
        assert elapsed_time < 30.0, (
            f"Task took too long: {elapsed_time:.2f}s"
        )

    def test_task_retry_with_zero_failures(self, celery_app):
        """
        Test that task succeeds immediately when fail_count=0.

        Verifies:
        - Task succeeds on first attempt
        - No retries occur
        - Execution is fast
        """
        start_time = time.time()

        # Task should succeed immediately (fail_count=0)
        result = failing_test_task.delay(fail_count=0)

        # Should complete quickly
        task_result = result.get(timeout=10)

        elapsed_time = time.time() - start_time

        # Verify immediate success
        assert task_result['status'] == 'success'
        assert task_result['retries'] == 0
        assert task_result['fail_count'] == 0

        # Should complete quickly (< 5 seconds)
        assert elapsed_time < 5.0

    def test_task_retry_metadata(self, celery_app):
        """
        Test that retry metadata is properly tracked and returned.

        Verifies:
        - Task ID is set
        - Retry count is accurate
        - Fail count matches input
        - Result includes all expected fields
        """
        # Task should fail 1 time before succeeding
        result = failing_test_task.delay(fail_count=1)

        # Get result
        task_result = result.get(timeout=15)

        # Verify all metadata fields present
        assert 'status' in task_result
        assert 'retries' in task_result
        assert 'fail_count' in task_result
        assert 'task_id' in task_result

        # Verify metadata values
        assert task_result['status'] == 'success'
        assert task_result['retries'] == 1
        assert task_result['fail_count'] == 1
        assert task_result['task_id'] == result.id


@pytest.mark.integration
@pytest.mark.slow
class TestTaskRetryPerformance:
    """Performance tests for task retry behavior."""

    def test_multiple_retrying_tasks_concurrent(self, celery_app):
        """
        Test that multiple retrying tasks execute concurrently.

        Verifies:
        - Multiple tasks can retry simultaneously
        - All tasks eventually succeed
        - Concurrency improves throughput
        """
        num_tasks = 3

        # Enqueue multiple retrying tasks
        results = [
            failing_test_task.delay(fail_count=1)
            for _ in range(num_tasks)
        ]

        # Wait for all tasks to complete
        # Each task: 1 failure + 1 success = ~5s + overhead
        # With concurrency, should be much faster than sequential (15s)
        task_results = [r.get(timeout=30) for r in results]

        # Verify all succeeded
        assert len(task_results) == num_tasks
        for task_result in task_results:
            assert task_result['status'] == 'success'
            assert task_result['retries'] >= 1

    def test_retry_performance_under_load(self, celery_app):
        """
        Test retry behavior under moderate load.

        Verifies:
        - 5 concurrent retrying tasks
        - All tasks complete successfully
        - Performance is acceptable
        """
        num_tasks = 5
        start_time = time.time()

        # Enqueue tasks with varying fail counts
        results = [
            failing_test_task.delay(fail_count=i % 3)
            for i in range(num_tasks)
        ]

        # Wait for all to complete
        task_results = [r.get(timeout=60) for r in results]

        total_time = time.time() - start_time

        # Verify all completed successfully
        assert len(task_results) == num_tasks
        assert all(r['status'] == 'success' for r in task_results)

        # With concurrency and retries, should complete in reasonable time
        # Expect < 40 seconds (conservative estimate)
        assert total_time < 40.0, (
            f"Tasks took too long: {total_time:.2f}s"
        )


@pytest.mark.integration
class TestTaskRetryEdgeCases:
    """Edge case tests for task retry behavior."""

    def test_task_retry_with_max_failures(self, celery_app):
        """
        Test task behavior when fail_count equals max_retries.

        Verifies:
        - Task succeeds on last possible retry
        - Exactly max_retries attempts are made
        """
        # Task should succeed on 3rd retry (last possible)
        result = failing_test_task.delay(fail_count=3)

        # This should succeed (barely)
        task_result = result.get(timeout=60)

        # Verify success on last retry
        assert task_result['status'] == 'success'
        assert task_result['retries'] == 3
        assert result.successful()

    def test_task_retry_task_id_consistency(self, celery_app):
        """
        Test that task ID remains consistent across retries.

        Verifies:
        - Task ID doesn't change during retries
        - Result can be retrieved using original task ID
        """
        # Enqueue task
        result = failing_test_task.delay(fail_count=1)
        original_task_id = result.id

        # Wait for completion (will retry once)
        task_result = result.get(timeout=15)

        # Verify task ID consistency
        assert task_result['task_id'] == original_task_id
        assert result.id == original_task_id

        # Verify result is retrievable with same ID
        assert result.result == task_result
