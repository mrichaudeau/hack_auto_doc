# User Story: Celery Worker Service for AI Pipeline

**Story ID:** US-6
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** Celery workers running to execute AI pipeline tasks
**So that** I can test Langgraph agents and async processing locally

## Description

This User Story establishes the Celery worker service that executes asynchronous tasks for the AI-powered Technology Watch Platform. The worker is responsible for running Langgraph-based AI agents that collect, analyze, and synthesize technology content in the background, without blocking API requests.

The worker service shares the same codebase as the Django backend but runs a different entry point (`celery worker` instead of `runserver`). This architecture enables background processing of computationally expensive operations like web scraping via Firecrawl, LLM-based content analysis, and vector embedding generation.

The worker must connect to Redis as the message broker, consume tasks from registered queues, and execute them with appropriate retry logic and error handling. Auto-reload support ensures developers can test task changes without manual container restarts.

Success means developers can enqueue tasks from the backend API, see them executed by workers in real-time, and debug task execution with clear logs.

## Acceptance Criteria

### Functional Criteria
- [ ] Celery worker container shares backend codebase (same Dockerfile)
- [ ] Worker connects to Redis broker successfully at `redis://redis:6379/0`
- [ ] Worker processes tasks from all registered queues
- [ ] Worker logs show task execution details (start, success, failure)
- [ ] Worker auto-reloads on code changes (watchdog enabled)
- [ ] Worker has access to LLM API keys from environment variables
- [ ] Worker can access Firecrawl API for web scraping
- [ ] Failed tasks retry according to configured policy (3 attempts with exponential backoff)

### Technical Criteria
- [ ] Worker service defined in docker-compose.yml
- [ ] Inherits from backend service (same Docker image)
- [ ] Command: `celery -A veille_tech worker --loglevel=info --watchdog`
- [ ] Environment variables for API keys: `GOOGLE_AI_API_KEY`, `FIRECRAWL_API_KEY`
- [ ] Concurrency: 4 worker processes for local development
- [ ] Task queue configuration supports multiple queues (default, high_priority)
- [ ] Worker logs accessible via `docker-compose logs worker`
- [ ] Worker container restarts automatically on failure

### UI/UX Criteria (if applicable)
- Not applicable for background worker service

### Performance Criteria
- [ ] Worker starts and connects to Redis within 10 seconds
- [ ] Task execution begins within 1 second of enqueueing
- [ ] Worker processes up to 4 tasks concurrently
- [ ] Task retry delay follows exponential backoff (1s, 10s, 60s)

## Technical Details

### Components Affected
- `docker-compose.yml` (worker service definition)
- `backend/Dockerfile` (shared with backend service)
- `backend/veille_tech/celery.py` (Celery app configuration)
- `backend/veille_tech/tasks.py` (task definitions)
- `.env.backend` (API keys for worker)

### API Changes
- None (worker consumes tasks, does not expose API)

### Database Changes
- None (worker uses Django ORM to access database)

### External Integrations
- Redis broker for task queues
- Google AI API (Gemini models) for LLM operations
- Firecrawl API for web scraping
- PostgreSQL for task result storage (optional)

## Implementation Notes

### Suggested Approach

1. **Define worker service in docker-compose.yml:**
   - Inherit from backend service (same image)
   - Override command: `poetry run celery -A veille_tech worker --loglevel=info --watchdog`
   - Mount same source code volume as backend for auto-reload
   - Set environment variables from `.env.backend`
   - Depend on redis and backend services

2. **Configure Celery app:**
   - Create `backend/veille_tech/celery.py` with Celery app initialization
   - Configure broker URL: `redis://redis:6379/0`
   - Configure result backend: PostgreSQL or Redis
   - Enable task result storage for debugging
   - Set task retry policy: max_retries=3, default_retry_delay=10s

3. **Enable auto-reload:**
   - Use `--watchdog` flag to enable file watching
   - Worker restarts automatically when Python files change
   - Note: May have performance implications in production

4. **Configure concurrency:**
   - Default: 4 worker processes (prefork pool)
   - Configurable via environment variable: `CELERY_WORKER_CONCURRENCY=4`
   - Consider using gevent or eventlet for I/O-bound tasks

### Technical Considerations

**Performance:**
- Concurrency of 4 sufficient for local development workload
- I/O-bound tasks (API calls) benefit from gevent/eventlet pool
- CPU-bound tasks (data processing) benefit from prefork pool
- Auto-reload adds overhead but critical for development experience

**Security:**
- API keys loaded from environment variables, never hardcoded
- Worker has same database access as backend (Django ORM permissions)
- Task execution isolated from API requests (no shared state)

**Scalability:**
- Docker Compose allows horizontal scaling: `docker-compose up --scale worker=3`
- Multiple workers share Redis broker and task queues
- Task deduplication handled by Langgraph or custom logic

**Backward Compatibility:**
- Celery 5+ compatible with Redis and PostgreSQL result backends
- Worker version must match backend version (same codebase)

### Known Challenges

**Challenge:** Auto-reload may cause in-flight tasks to fail
**Solution:** Configure graceful shutdown with `CELERY_TASK_SOFT_TIME_LIMIT`; accept task failures during reload in development

**Challenge:** LLM API calls may exceed task timeout
**Solution:** Configure appropriate `task_time_limit` (e.g., 300s for AI pipeline tasks)

**Challenge:** Watchdog may not detect changes on Windows Docker Desktop
**Solution:** Use WSL2 backend; alternative is manual worker restart

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-2: Database Service with Vector Support (worker needs database access)
- US-3: Redis Broker and Cache Service (worker requires Redis broker)
- US-4: Django Backend API Service (worker shares codebase)

### Blocks
- Feature user stories that implement AI pipeline tasks (Bloc 3)

## Test Scenarios

### Happy Path
1. Developer runs `docker-compose up -d worker`
2. Worker container starts and connects to Redis broker
3. Worker logs show: "celery@worker ready" and "Connected to redis://redis:6379/0"
4. Developer enqueues test task from Django shell:
   ```python
   from veille_tech.tasks import test_task
   result = test_task.delay("Hello")
   ```
5. Worker logs show task execution: "Task test_task[task-id] received"
6. Task completes successfully
7. Worker logs show: "Task test_task[task-id] succeeded in 0.1s"

### Alternative Paths
1. Developer edits task definition in `backend/veille_tech/tasks.py`
2. Worker logs show: "Reloading worker..."
3. Worker restarts automatically
4. Developer enqueues task again
5. Updated task logic executes

### Error Scenarios
1. **Redis broker unavailable:** Redis service not running
   - Expected: Worker fails to start and retries connection
   - Logs show: "Error connecting to Redis"
   - Worker waits for Redis to become available (depends_on)

2. **Task raises exception:** Task code has unhandled error
   - Expected: Worker catches exception and retries task
   - After 3 retries, task marked as failed
   - Error trace logged for debugging

3. **API key missing:** `GOOGLE_AI_API_KEY` not set
   - Expected: Task fails with clear error message
   - Logs show: "Missing required environment variable"
   - Developer adds key to `.env.backend` and restarts worker

4. **Task timeout:** Task execution exceeds time limit
   - Expected: Worker terminates task and logs timeout error
   - Task marked as failed and may retry depending on configuration

### Edge Cases
1. **Concurrent task execution:** Multiple tasks enqueued simultaneously
   - Expected: Worker processes up to 4 tasks concurrently
   - Additional tasks queued until worker capacity available

2. **Long-running task during shutdown:** Developer stops worker while task running
   - Expected: Worker waits for task to complete (graceful shutdown)
   - If task exceeds soft limit, worker force-terminates

## UI/UX Specifications

Not applicable for background worker service.

## Security Considerations

- API keys for Google AI and Firecrawl loaded from environment variables
- Worker has same database permissions as backend (Django ORM)
- Task inputs should be validated before enqueueing (backend responsibility)
- Worker logs may contain sensitive data—avoid logging API keys or user data
- Production workers should run with minimal privileges

## Performance Requirements

- **Startup Time:** Worker connected to broker within 10 seconds (P95)
- **Task Execution Latency:** Task begins execution within 1 second of enqueueing
- **Concurrency:** Process up to 4 tasks simultaneously
- **Retry Delay:** Exponential backoff (1s, 10s, 60s)
- **Memory Usage:** < 500MB per worker process

## Accessibility Requirements

Not applicable for background worker service.

## Definition of Done

- [ ] Worker service defined in docker-compose.yml with all required configuration
- [ ] Worker inherits from backend service (same Docker image)
- [ ] Celery app configured in `backend/veille_tech/celery.py`
- [ ] Sample task created for testing task execution
- [ ] Worker connects to Redis broker successfully
- [ ] Worker processes tasks from queue
- [ ] Auto-reload (watchdog) enabled and working
- [ ] API keys accessible from environment variables
- [ ] Task retry policy configured (3 attempts)
- [ ] Worker logs accessible and showing task execution details
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] Worker starts successfully with `docker-compose up worker`
- [ ] Task enqueueing and execution verified
- [ ] All acceptance criteria verified
- [ ] Documentation updated with worker management instructions
- [ ] No critical or high-severity issues

## Tasks

Detailed development tasks will be generated in [tasks.md](./tasks.md) using the `/spec-generate-tasks` command.

### Task Summary
- **Total Tasks:** TBD
- **Completed:** 0
- **In Progress:** 0
- **Blocked:** 0

## Notes

### Questions / Open Items
- [ ] Should we use gevent/eventlet pool for I/O-bound AI tasks?
- [ ] Do we need separate queues for high-priority tasks?
- [ ] Should task results be stored in PostgreSQL or Redis?

### Assumptions
- Single worker instance sufficient for local development
- 4 concurrent processes adequate for development workload
- Auto-reload critical for development productivity despite overhead

### Out of Scope
- Horizontal worker scaling in production
- Advanced Celery features (task prioritization, rate limiting)
- Celery Flower monitoring dashboard (handled in separate story if needed)
- Task result cleanup and expiration policies

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-3: Redis Broker and Cache Service (depends on this)
- US-4: Django Backend API Service (shares codebase)
- US-7: Celery Beat Scheduler Service (enqueues recurring tasks)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
