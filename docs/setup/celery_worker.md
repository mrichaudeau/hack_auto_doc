# Celery Worker Management Guide

## Overview

This guide provides comprehensive instructions for managing Celery workers in the Technology Watch Platform. Celery workers handle asynchronous task processing for the AI pipeline, including web scraping, content analysis, report synthesis, and vector embedding generation.

**Technologies:**
- Celery 5.4+
- Redis 7+ (message broker)
- Python 3.13
- Django 5.1+
- Docker Compose

**Architecture:**
```
Django API → Task Enqueue → Redis (Broker) → Celery Worker → Task Execution
                                                    ↓
                                            Redis (Results Backend)
```

## Table of Contents

1. [Starting and Stopping Workers](#starting-and-stopping-workers)
2. [Viewing Logs](#viewing-logs)
3. [Enqueueing Tasks](#enqueueing-tasks)
4. [Checking Worker Status](#checking-worker-status)
5. [Scaling Workers](#scaling-workers)
6. [Troubleshooting](#troubleshooting)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)

---

## Starting and Stopping Workers

### Start Worker with Docker Compose

```bash
# Start worker service only
docker-compose up worker

# Start worker in detached mode (background)
docker-compose up -d worker

# Start entire stack (includes worker)
docker-compose up -d
```

### Stop Worker

```bash
# Stop worker gracefully (allows tasks to complete)
docker-compose stop worker

# Stop worker immediately
docker-compose kill worker

# Stop and remove worker container
docker-compose down worker
```

### Restart Worker

```bash
# Restart worker (useful after code changes if watchdog not enabled)
docker-compose restart worker

# Rebuild and restart worker (after dependency changes)
docker-compose up -d --build worker
```

### Manual Worker Start (Development)

For debugging or development without Docker:

```bash
cd backend

# Start worker with default settings
poetry run celery -A veille_tech worker --loglevel=info

# Start worker with auto-reload (watchdog)
poetry run celery -A veille_tech worker --loglevel=info --watchdog

# Start worker with custom concurrency
poetry run celery -A veille_tech worker --loglevel=info --concurrency=8

# Start worker listening to specific queues
poetry run celery -A veille_tech worker --loglevel=info -Q default,high_priority
```

---

## Viewing Logs

### Real-Time Logs

```bash
# Follow worker logs (tail -f style)
docker-compose logs -f worker

# Follow all services including worker
docker-compose logs -f

# View last 100 lines of worker logs
docker-compose logs --tail=100 worker
```

### Log Filtering

```bash
# Search logs for specific task
docker-compose logs worker | grep "test_task"

# Search for errors
docker-compose logs worker | grep "ERROR"

# Search for specific task ID
docker-compose logs worker | grep "task_id=abc123"
```

### Log Output Format

Celery logs include:
- **Timestamp**: When task executed
- **Log Level**: INFO, WARNING, ERROR, DEBUG
- **Task Name**: Fully qualified task name (e.g., veille_tech.tasks.test_task)
- **Task ID**: Unique identifier for task execution
- **Worker Name**: Which worker processed the task
- **Status**: Task received, started, succeeded, failed, retrying

Example log entry:
```
[2025-11-02 14:30:45,123: INFO/MainProcess] Task veille_tech.tasks.test_task[abc-123] received
[2025-11-02 14:30:45,125: INFO/ForkPoolWorker-1] Task veille_tech.tasks.test_task[abc-123] succeeded in 1.23s
```

---

## Enqueueing Tasks

### From Django Shell

```bash
# Enter Django shell
docker-compose exec backend python manage.py shell

# In shell:
from veille_tech.tasks import test_task, health_check_task

# Enqueue task asynchronously (returns immediately)
result = test_task.delay("Hello from shell")
print(f"Task ID: {result.id}")

# Enqueue with custom countdown (delay execution)
result = test_task.apply_async(args=["Delayed task"], countdown=60)  # Execute in 60 seconds

# Enqueue with custom priority
result = test_task.apply_async(args=["High priority"], priority=9)

# Enqueue to specific queue
result = test_task.apply_async(args=["Urgent task"], queue='high_priority')
```

### From Django Views/API

```python
# In your Django view or DRF API endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response
from veille_tech.tasks import test_task

@api_view(['POST'])
def enqueue_task(request):
    message = request.data.get('message', 'Default message')

    # Enqueue task
    result = test_task.delay(message)

    return Response({
        'task_id': result.id,
        'status': 'Task enqueued successfully'
    })
```

### Task Result Retrieval

```python
# In Django shell
from celery.result import AsyncResult

# Get task result by ID
task_id = "abc-123-def-456"
result = AsyncResult(task_id)

# Check task state
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

# Get result (blocks until task completes)
if result.successful():
    print(result.result)  # Task return value
elif result.failed():
    print(result.traceback)  # Error traceback
```

---

## Checking Worker Status

### Health Check Command

```bash
# Run health check (checks app, broker, workers)
docker-compose exec backend python manage.py celery_health_check

# Expected output for healthy worker:
# ============================================================
# Celery Worker Health Check
# ============================================================
#
# [1/3] Checking Celery app initialization...
#   OK Celery app initialized: veille_tech
#
# [2/3] Checking Redis broker connectivity...
#   OK Redis broker reachable: redis://redis:6379/0
#
# [3/3] Checking active workers...
#   OK Found 1 active worker(s):
#     - celery@worker
#       Pool: prefork, Concurrency: 4
#     Active tasks: 0
# ============================================================
# HEALTH CHECK PASSED: All systems operational
```

### Docker Health Status

```bash
# Check worker health status from Docker
docker-compose ps worker

# Expected output (healthy):
# NAME      IMAGE           STATUS
# worker    backend:latest  Up 5 minutes (healthy)
```

### Celery Inspect Commands

```bash
# Inspect active tasks
docker-compose exec backend poetry run celery -A veille_tech inspect active

# Inspect registered tasks
docker-compose exec backend poetry run celery -A veille_tech inspect registered

# Inspect worker stats
docker-compose exec backend poetry run celery -A veille_tech inspect stats

# Inspect scheduled tasks (ETA/countdown)
docker-compose exec backend poetry run celery -A veille_tech inspect scheduled

# Inspect reserved tasks (prefetched but not started)
docker-compose exec backend poetry run celery -A veille_tech inspect reserved
```

### Celery Status Command

```bash
# Show worker status summary
docker-compose exec backend poetry run celery -A veille_tech status

# Expected output:
# celery@worker: OK
#
# 1 node online.
```

### Monitor Task Queue

```bash
# Check queue length using Redis CLI
docker-compose exec redis redis-cli LLEN celery

# Check specific queue
docker-compose exec redis redis-cli LLEN high_priority
```

---

## Scaling Workers

### Horizontal Scaling (Multiple Worker Containers)

Modify `docker-compose.yml`:

```yaml
services:
  # Worker 1 - Default queue
  worker:
    # ... existing configuration ...
    command: poetry run celery -A veille_tech worker --loglevel=info --concurrency=4 -Q default

  # Worker 2 - High priority queue
  worker_high_priority:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: worker_high_priority
    restart: unless-stopped
    env_file:
      - .env.backend
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./backend:/app
    networks:
      - app-network
    depends_on:
      redis:
        condition: service_healthy
    command: poetry run celery -A veille_tech worker --loglevel=info --concurrency=8 -Q high_priority
```

Then start both:
```bash
docker-compose up -d worker worker_high_priority
```

### Vertical Scaling (Concurrency)

#### Option 1: Environment Variable (Recommended)

Update `.env.backend`:
```bash
# Increase from default 4 to 8 workers
CELERY_WORKER_CONCURRENCY=8
```

Restart worker:
```bash
docker-compose restart worker
```

#### Option 2: Docker Compose Override

```bash
# Start worker with custom concurrency
docker-compose run --rm -e CELERY_WORKER_CONCURRENCY=8 worker
```

#### Option 3: Autoscaling

Enable autoscaling in worker command:

```yaml
# In docker-compose.yml
command: poetry run celery -A veille_tech worker --loglevel=info --autoscale=10,2
# Scales between 2 (min) and 10 (max) worker processes based on load
```

### Pool Type Selection

#### Prefork (Default - CPU-bound tasks)
```bash
CELERY_WORKER_POOL=prefork
CELERY_WORKER_CONCURRENCY=4  # 2-4 per CPU core
```

**Use for:** LLM API calls, data processing, computation

#### Gevent (I/O-bound tasks)
```bash
CELERY_WORKER_POOL=gevent
CELERY_WORKER_CONCURRENCY=100  # Much higher concurrency
```

**Use for:** Web scraping, HTTP requests, file I/O

**Requires:** Install gevent dependency
```bash
poetry add gevent
```

#### Eventlet (Alternative I/O-bound)
```bash
CELERY_WORKER_POOL=eventlet
CELERY_WORKER_CONCURRENCY=100
```

**Requires:** Install eventlet dependency
```bash
poetry add eventlet
```

---

## Troubleshooting

### Problem: Worker Not Starting

**Symptoms:**
- Worker container exits immediately
- `docker-compose ps worker` shows "Exit 1"

**Solutions:**

1. **Check logs for errors:**
   ```bash
   docker-compose logs worker
   ```

2. **Verify Redis is running:**
   ```bash
   docker-compose ps redis
   docker-compose exec redis redis-cli ping
   # Expected: PONG
   ```

3. **Verify environment variables:**
   ```bash
   docker-compose exec backend env | grep CELERY
   ```

4. **Test Celery app loads:**
   ```bash
   docker-compose exec backend poetry run python -c "from veille_tech.celery import app; print(app)"
   # Expected: <Celery veille_tech at 0x...>
   ```

### Problem: Tasks Not Executing

**Symptoms:**
- Tasks enqueued but never start
- Worker shows 0 active tasks

**Solutions:**

1. **Check worker is listening to correct queue:**
   ```bash
   docker-compose logs worker | grep "celery@worker ready"
   # Should show queues: [default, high_priority]
   ```

2. **Verify task routing configuration:**
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.CELERY_TASK_ROUTES)
   ```

3. **Check task is registered:**
   ```bash
   docker-compose exec backend poetry run celery -A veille_tech inspect registered
   # Should list: veille_tech.tasks.test_task, etc.
   ```

4. **Verify queue has tasks:**
   ```bash
   docker-compose exec redis redis-cli LLEN celery
   ```

### Problem: Worker Consuming Too Much Memory

**Symptoms:**
- Worker container OOM killed
- `docker stats worker` shows high memory usage

**Solutions:**

1. **Set max tasks per child (restart workers periodically):**
   ```bash
   # In .env.backend
   CELERY_WORKER_MAX_TASKS_PER_CHILD=100
   ```

2. **Reduce concurrency:**
   ```bash
   CELERY_WORKER_CONCURRENCY=2
   ```

3. **Increase Docker memory limit:**
   ```yaml
   # In docker-compose.yml
   worker:
     deploy:
       resources:
         limits:
           memory: 4G  # Increase from 2G
   ```

4. **Use gevent pool for I/O tasks:**
   ```bash
   CELERY_WORKER_POOL=gevent
   ```

### Problem: Tasks Timing Out

**Symptoms:**
- Tasks fail with `SoftTimeLimitExceeded` or `TimeLimitExceeded`

**Solutions:**

1. **Increase time limits:**
   ```python
   # In settings/base.py
   CELERY_TASK_SOFT_TIME_LIMIT = 600  # 10 minutes
   CELERY_TASK_TIME_LIMIT = 1200  # 20 minutes
   ```

2. **Set per-task limits:**
   ```python
   @shared_task(soft_time_limit=600, time_limit=1200)
   def long_running_task():
       pass
   ```

3. **Break task into smaller subtasks:**
   ```python
   from celery import chain

   # Chain tasks sequentially
   workflow = chain(task1.s(), task2.s(), task3.s())
   workflow.apply_async()
   ```

### Problem: Auto-Reload Not Working

**Symptoms:**
- Code changes not reflected without manual restart
- Worker not restarting on file changes

**Solutions:**

1. **Verify watchdog is installed:**
   ```bash
   docker-compose exec backend poetry show watchdog
   ```

2. **Check watchdog flag in command:**
   ```bash
   docker-compose exec worker ps aux | grep celery
   # Should show: --watchdog flag
   ```

3. **Windows/macOS: Use WSL2 backend:**
   - Docker Desktop → Settings → General → Use WSL 2 based engine

4. **Alternative: Manual restart:**
   ```bash
   docker-compose restart worker
   ```

### Problem: Redis Connection Errors

**Symptoms:**
- Worker logs show "Error connecting to redis://redis:6379/0"
- Broker connectivity failed

**Solutions:**

1. **Verify Redis service healthy:**
   ```bash
   docker-compose ps redis
   # Should show: (healthy)
   ```

2. **Test Redis connectivity:**
   ```bash
   docker-compose exec backend ping redis
   docker-compose exec redis redis-cli ping
   ```

3. **Check broker URL configuration:**
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from veille_tech.celery import app
   >>> print(app.conf.broker_url)
   # Expected: redis://redis:6379/0
   ```

4. **Restart Redis and worker:**
   ```bash
   docker-compose restart redis worker
   ```

### Problem: Tasks Stuck in PENDING State

**Symptoms:**
- Task result shows PENDING indefinitely
- Task never executed

**Solutions:**

1. **Verify task was actually sent to broker:**
   ```bash
   docker-compose logs worker | grep "Task.*received"
   ```

2. **Check worker is consuming from correct queue:**
   ```bash
   docker-compose exec backend poetry run celery -A veille_tech inspect active_queues
   ```

3. **Verify result backend connectivity:**
   ```bash
   docker-compose exec backend python manage.py check_redis
   ```

---

## Configuration

### Environment Variables

**Required Variables** (`.env.backend`):

```bash
# Celery Broker Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Worker Configuration
CELERY_WORKER_POOL=prefork           # prefork, gevent, eventlet
CELERY_WORKER_CONCURRENCY=4          # Number of worker processes
CELERY_WORKER_MAX_TASKS_PER_CHILD=100  # Restart worker after N tasks

# API Keys (for AI pipeline tasks)
GOOGLE_AI_API_KEY=your-google-ai-key
FIRECRAWL_API_KEY=your-firecrawl-key
```

### Django Settings

**Key Settings** (`backend/veille_tech/settings/base.py`):

```python
# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')

# Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Timezone
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Retry Policy
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_DEFAULT_RETRY_DELAY = 10
CELERY_TASK_MAX_RETRIES = 3

# Time Limits
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes

# Queue Routing
CELERY_TASK_ROUTES = {
    'veille_tech.tasks.test_task': {'queue': 'default'},
    'veille_tech.tasks.health_check_task': {'queue': 'default'},
    'veille_tech.ai_pipeline.*': {'queue': 'high_priority'},
    'veille_tech.urgent.*': {'queue': 'high_priority'},
}

# Queue Priorities
CELERY_TASK_QUEUE_MAX_PRIORITY = 10
CELERY_TASK_DEFAULT_PRIORITY = 5

# Worker Configuration
CELERY_WORKER_POOL = config('CELERY_WORKER_POOL', default='prefork')
CELERY_WORKER_CONCURRENCY = config('CELERY_WORKER_CONCURRENCY', default=4, cast=int)
CELERY_WORKER_MAX_TASKS_PER_CHILD = config('CELERY_WORKER_MAX_TASKS_PER_CHILD', default=100, cast=int)
CELERY_WORKER_PREFETCH_MULTIPLIER = 4

# Broker Connection
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Result Backend Settings
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
```

---

## Best Practices

### 1. Task Idempotency

Design tasks to be safely retried without side effects:

```python
@shared_task(bind=True, max_retries=3)
def process_report(self, report_id: int):
    """Idempotent task - can be safely retried."""
    try:
        # Check if already processed
        report = Report.objects.get(id=report_id)
        if report.processed:
            return {'status': 'already_processed'}

        # Process report
        result = process_report_logic(report)

        # Mark as processed (atomic operation)
        report.processed = True
        report.save()

        return result
    except Exception as exc:
        raise self.retry(exc=exc)
```

### 2. Graceful Error Handling

```python
@shared_task(bind=True, max_retries=3)
def api_call_task(self, url: str):
    """Task with graceful error handling."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        # Transient error - retry
        raise self.retry(exc=exc, countdown=60)

    except requests.HTTPError as exc:
        if 500 <= exc.response.status_code < 600:
            # Server error - retry
            raise self.retry(exc=exc, countdown=120)
        else:
            # Client error (4xx) - don't retry
            logger.error(f"Client error: {exc}")
            return {'error': str(exc)}
```

### 3. Structured Logging

```python
import logging
logger = logging.getLogger(__name__)

@shared_task(bind=True)
def logged_task(self, data: dict):
    """Task with comprehensive logging."""
    task_id = self.request.id

    logger.info(
        f"Task started [task_id={task_id}] [data={data}]"
    )

    try:
        result = process_data(data)

        logger.info(
            f"Task completed [task_id={task_id}] [result={result}]"
        )
        return result

    except Exception as exc:
        logger.error(
            f"Task failed [task_id={task_id}] [error={str(exc)}]",
            exc_info=True
        )
        raise
```

### 4. Resource Management

```python
@shared_task(bind=True)
def file_processing_task(self, file_path: str):
    """Task with proper resource cleanup."""
    file_handle = None

    try:
        file_handle = open(file_path, 'r')
        data = file_handle.read()
        result = process_file_data(data)
        return result

    finally:
        # Always clean up resources
        if file_handle:
            file_handle.close()
```

### 5. Monitoring and Alerting

```python
from celery.signals import task_failure

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Alert on task failures."""
    logger.error(
        f"Task failed: {sender.name} [task_id={task_id}] [error={exception}]"
    )

    # Send alert (email, Slack, etc.)
    # send_alert(f"Celery task {sender.name} failed: {exception}")
```

### 6. Task Chains and Workflows

```python
from celery import chain, group, chord

# Sequential tasks (chain)
workflow = chain(
    scrape_content.s(url),
    analyze_content.s(),
    generate_report.s()
)
workflow.apply_async()

# Parallel tasks (group)
parallel_tasks = group(
    scrape_content.s(url1),
    scrape_content.s(url2),
    scrape_content.s(url3)
)
parallel_tasks.apply_async()

# Parallel then callback (chord)
workflow = chord(
    group(scrape_content.s(url) for url in urls),
    aggregate_results.s()
)
workflow.apply_async()
```

---

## Testing Worker Auto-Reload

The worker auto-reload feature (watchdog) automatically restarts the worker when source code changes. This is essential for development productivity.

### Manual Testing Procedure

**1. Start worker with visible logs:**
```bash
docker-compose up worker
```

**2. Execute a test task (baseline):**
```bash
docker-compose exec backend python manage.py shell

# In shell:
from veille_tech.tasks import test_task
result = test_task.delay("Before reload")
print(result.get())
# Expected: {'status': 'success', 'message': 'Before reload', ...}
```

**3. Modify task source code:**

Edit `backend/veille_tech/tasks.py` and add a visible change:
```python
# In test_task, change:
return {
    'status': 'success',
    'message': message,  # Original
    ...
}

# To:
return {
    'status': 'success',
    'message': f"[RELOADED] {message}",  # Modified
    ...
}
```

Save the file.

**4. Monitor worker logs for reload:**

Within 2-3 seconds, you should see:
```
worker_1  | [WARNING] /app/veille_tech/tasks.py changed, reloading...
worker_1  | [INFO] Stopping worker gracefully...
worker_1  | [INFO] celery@<hostname> ready.
```

**5. Verify updated task executes:**
```bash
docker-compose exec backend python manage.py shell

# In shell:
from importlib import reload
import veille_tech.tasks
reload(veille_tech.tasks)

from veille_tech.tasks import test_task
result = test_task.delay("After reload")
print(result.get())
# Expected: {'status': 'success', 'message': '[RELOADED] After reload', ...}
```

**6. Revert changes and verify reload triggers again.**

### Success Criteria

✅ Worker logs show "reloading..." within 3 seconds of file change
✅ Worker restarts successfully without errors
✅ Modified task logic executes correctly
✅ No task execution failures during reload

### Platform-Specific Notes

**Windows (Docker Desktop):**
- **REQUIRED:** Enable WSL2 backend (Settings → General → Use WSL 2 based engine)
- Hyper-V backend does NOT support file watching reliably
- Restart Docker Desktop after enabling WSL2

**macOS (Docker Desktop):**
- Works well out of the box
- Slight delay (1-2s) due to osxfs volume performance
- Consider using `:cached` volume mount for better performance

**Linux (Native Docker):**
- Best performance (<1s reload time)
- No special configuration needed

### Troubleshooting Auto-Reload

**Problem: Reload not triggering**

Verify configuration:
```bash
# Check watchdog is installed
docker-compose exec backend poetry show watchdog

# Verify --watchdog flag in worker command
docker-compose config | grep -A 10 "worker:"

# Check volume mount has read-write access
docker-compose config | grep -A 5 "volumes:" | grep backend
# Should show: ./backend:/app:rw
```

**Problem: Slow reload (>5 seconds)**

Solutions:
- Add `.dockerignore` to exclude unnecessary files (node_modules, .git)
- Increase Docker Desktop memory (Settings → Resources → Memory)
- Enable polling mode (slower but more reliable):
  ```yaml
  environment:
    - WATCHDOG_FORCE_POLLING=true
  ```

**Problem: Worker crashes during reload**

Check for:
- Python syntax errors in modified code
- Long-running tasks blocking shutdown (check soft_time_limit)
- Database connection issues

Fix:
```bash
# View full error logs
docker-compose logs worker

# Restart worker completely
docker-compose restart worker
```

For comprehensive testing documentation, see:
```bash
# View full manual testing procedure
cat backend/tests/integration/test_worker_autoreload.py
```

---

## Additional Resources

**Official Documentation:**
- Celery: https://docs.celeryq.dev/en/stable/
- Django-Celery: https://docs.celeryq.dev/en/stable/django/
- Redis: https://redis.io/docs/
- Watchdog: https://github.com/gorakhargosh/watchdog

**Monitoring Tools:**
- Flower (Celery monitoring): https://flower.readthedocs.io/
- Celery Events: https://docs.celeryq.dev/en/stable/userguide/monitoring.html

**Related Documentation:**
- [Redis Setup Guide](./redis_setup.md)
- [Django Settings Configuration](../backend/settings.md)
- [Docker Compose Setup](./00_setup_local_docker.md)
- [Worker Auto-Reload Testing](../backend/tests/integration/test_worker_autoreload.py)

---

**Last Updated:** 2025-11-03
**Version:** 1.1.0
