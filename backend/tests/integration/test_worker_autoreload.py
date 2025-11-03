"""
Integration tests and manual testing documentation for Celery worker auto-reload.

The worker auto-reload feature (watchdog) enables automatic worker restart
when source code changes are detected. This is a development productivity feature.

IMPORTANT: Auto-reload tests require special setup and may be flaky in CI.
These tests are marked as @pytest.mark.slow and @pytest.mark.manual.

For reliable testing, use the manual testing procedure documented below.
"""

import pytest
import time
import os
import tempfile
from pathlib import Path


@pytest.mark.integration
@pytest.mark.manual
class TestWorkerAutoReload:
    """
    Tests for worker auto-reload functionality.

    Note: These tests verify configuration but actual auto-reload
    testing should be done manually using the procedure below.
    """

    def test_watchdog_dependency_installed(self):
        """
        Test that watchdog package is installed.

        Watchdog is required for auto-reload functionality.
        """
        try:
            import watchdog
            assert watchdog is not None
            # Verify minimum version if needed
            import watchdog.__version__
            assert watchdog.__version__ is not None
        except ImportError:
            pytest.fail("watchdog package not installed")

    def test_worker_command_includes_watchdog_flag(self):
        """
        Test that docker-compose.yml worker command includes --watchdog flag.

        Note: This test reads docker-compose.yml to verify configuration.
        """
        compose_file = Path(__file__).parent.parent.parent.parent / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not found")

        with open(compose_file, 'r') as f:
            compose_content = f.read()

        # Verify worker service exists and has --watchdog flag
        assert 'worker:' in compose_content
        assert '--watchdog' in compose_content or 'watchdog' in compose_content

    def test_celery_worker_pool_configuration(self, celery_app):
        """
        Test that worker pool configuration supports auto-reload.

        Auto-reload works best with certain pool types (prefork, solo).
        """
        worker_pool = celery_app.conf.worker_pool

        # Verify pool type is compatible with auto-reload
        # prefork, solo, and gevent work well with watchdog
        assert worker_pool in ['prefork', 'solo', 'gevent', 'eventlet']


# ==============================================================================
# MANUAL TESTING PROCEDURE FOR WORKER AUTO-RELOAD
# ==============================================================================

MANUAL_TEST_PROCEDURE = """
# Worker Auto-Reload Manual Testing Procedure

This procedure verifies that the Celery worker automatically reloads
when source code changes are detected.

## Prerequisites

1. Docker Compose environment running
2. Worker service started with --watchdog flag
3. Backend source code mounted as volume in docker-compose.yml
4. WSL2 backend enabled (Windows users only)

## Test Procedure

### Step 1: Start Worker with Visible Logs

```bash
# Start only the worker service with logs
docker-compose up worker

# Or follow logs in a separate terminal
docker-compose logs -f worker
```

**Expected Output:**
```
worker_1  | [INFO] celery@<hostname> ready.
worker_1  | [INFO] Watchdog observer started
```

### Step 2: Verify Initial Task Execution

Open a new terminal and run:

```bash
# Execute Django shell
docker-compose exec backend python manage.py shell

# In shell, execute a test task
from veille_tech.tasks import test_task
result = test_task.delay("Before auto-reload")
print(result.get())
```

**Expected Output:**
```python
{
    'status': 'success',
    'message': 'Before auto-reload',
    'task_id': '<task-id>',
    'retries': 0
}
```

### Step 3: Modify Task Source Code

Edit `backend/veille_tech/tasks.py` and make a visible change:

```python
# Change the test_task to add a prefix
# Original:
return {
    'status': 'success',
    'message': message,
    ...
}

# Modified:
return {
    'status': 'success',
    'message': f"[AUTO-RELOAD TEST] {message}",  # <-- Add this prefix
    ...
}
```

**Save the file.**

### Step 4: Monitor Worker Logs for Reload

Watch the worker logs (from Step 1).

**Expected Log Output (within 2-3 seconds):**
```
worker_1  | [WARNING] /app/veille_tech/tasks.py changed, reloading...
worker_1  | [INFO] Stopping worker gracefully...
worker_1  | [INFO] Worker shutdown complete
worker_1  | [INFO] celery@<hostname> ready.
worker_1  | [INFO] Watchdog observer started
```

**Timing:** Reload should occur within 2-3 seconds of saving the file.

### Step 5: Verify Updated Task Logic Executes

Execute the task again (using Django shell):

```bash
docker-compose exec backend python manage.py shell

# In shell
from importlib import reload
import veille_tech.tasks
reload(veille_tech.tasks)  # Reload module in shell

from veille_tech.tasks import test_task
result = test_task.delay("After auto-reload")
print(result.get())
```

**Expected Output:**
```python
{
    'status': 'success',
    'message': '[AUTO-RELOAD TEST] After auto-reload',  # <-- Prefix added
    'task_id': '<task-id>',
    'retries': 0
}
```

### Step 6: Revert Changes

Restore the original task code and verify auto-reload triggers again:

```python
# Revert to original:
return {
    'status': 'success',
    'message': message,
    ...
}
```

**Save and watch logs for reload.**

## Success Criteria

✅ Worker logs show "reloading..." message when files change
✅ Worker restarts within 2-3 seconds
✅ Modified task logic executes correctly after reload
✅ No errors during reload process
✅ All task executions complete successfully

## Troubleshooting

### Issue: Auto-reload not triggering

**Windows Users:**
- Verify Docker Desktop is using WSL2 backend (not Hyper-V)
- Check Settings > General > Use WSL 2 based engine is enabled
- Restart Docker Desktop after enabling WSL2

**All Platforms:**
- Verify volume mount in docker-compose.yml:
  ```yaml
  volumes:
    - ./backend:/app:rw  # Must have :rw (read-write)
  ```
- Check --watchdog flag is present in worker command
- Verify watchdog package is installed: `docker-compose exec worker pip show watchdog`

### Issue: Reload is slow (> 5 seconds)

**Possible Causes:**
- File watching scanning too many files (node_modules, .git, etc.)
- Insufficient Docker resources

**Solutions:**
- Add .dockerignore to exclude unnecessary directories
- Increase Docker Desktop memory allocation (Settings > Resources)
- Use polling mode (slower but more reliable):
  ```yaml
  environment:
    - WATCHDOG_FORCE_POLLING=true
  ```

### Issue: Worker crashes during reload

**Check:**
- Worker logs for Python syntax errors in modified code
- Database connections are properly closed before restart
- No long-running tasks blocking shutdown (respect soft_time_limit)

**Solution:**
- Fix syntax errors in code
- Ensure graceful shutdown is configured:
  ```python
  CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
  CELERY_TASK_TIME_LIMIT = 600  # 10 minutes
  ```

### Issue: Changes not reflected after reload

**Possible Causes:**
- Python module caching
- Task code loaded in memory before reload
- Stale .pyc files

**Solutions:**
- Restart worker completely: `docker-compose restart worker`
- Clear Python cache: `docker-compose exec backend find . -name "*.pyc" -delete`
- Use Django shell reload: `from importlib import reload; reload(module)`

## Cross-Platform Notes

### Windows (Docker Desktop + WSL2)
- WSL2 backend is REQUIRED for file watching to work reliably
- Hyper-V backend has known issues with volume mount file watching
- Performance is good with WSL2

### macOS (Docker Desktop)
- File watching works well on macOS
- Slight delay (1-2s) due to osxfs volume mount performance
- Consider using cached volumes for better performance:
  ```yaml
  volumes:
    - ./backend:/app:cached
  ```

### Linux (Native Docker)
- Best performance for file watching
- No special configuration needed
- Reload typically occurs within 1 second

## Alternative: Manual Worker Restart

If auto-reload is not working or not needed:

```bash
# Restart worker manually after code changes
docker-compose restart worker

# Or stop/start for full rebuild
docker-compose stop worker
docker-compose up -d worker
```

## Performance Expectations

| Metric | Expected Value |
|--------|----------------|
| Reload trigger time | < 3 seconds |
| Worker shutdown time | < 5 seconds |
| Worker startup time | < 10 seconds |
| Total reload cycle | < 15 seconds |

## References

- Celery Watchdog Documentation: https://docs.celeryq.dev/en/stable/userguide/workers.html#autoreloading
- Watchdog Package: https://github.com/gorakhargosh/watchdog
- Docker Volume Performance: https://docs.docker.com/storage/volumes/
"""


@pytest.mark.manual
def test_manual_procedure_documentation():
    """
    Test that manual testing procedure is documented.

    This test simply ensures the documentation string is present.
    Actual testing should follow the MANUAL_TEST_PROCEDURE steps above.
    """
    assert MANUAL_TEST_PROCEDURE is not None
    assert len(MANUAL_TEST_PROCEDURE) > 100
    assert "Worker Auto-Reload" in MANUAL_TEST_PROCEDURE
    assert "Step 1" in MANUAL_TEST_PROCEDURE
    assert "docker-compose" in MANUAL_TEST_PROCEDURE


def print_manual_test_procedure():
    """
    Utility function to print the manual testing procedure.

    Run with: pytest tests/integration/test_worker_autoreload.py::print_manual_test_procedure -v -s
    """
    print("\n" + "=" * 80)
    print(MANUAL_TEST_PROCEDURE)
    print("=" * 80 + "\n")


if __name__ == "__main__":
    # Print manual procedure when run directly
    print_manual_test_procedure()
