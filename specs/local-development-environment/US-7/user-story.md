# User Story: Celery Beat Scheduler Service

**Story ID:** US-7
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** Celery Beat scheduler running for recurring tasks
**So that** I can test daily scraping schedules locally

## Description

This User Story establishes the Celery Beat scheduler service that dispatches recurring tasks on a schedule for the AI-powered Technology Watch Platform. The scheduler is responsible for enqueueing periodic tasks like daily technology content scraping, weekly report aggregation, and periodic cleanup operations.

The scheduler service shares the same codebase as the Django backend but runs the Celery Beat entry point. Unlike the worker service which executes tasks, the scheduler only dispatches tasks to Redis queues according to configured schedules (cron-like expressions or intervals).

The scheduler must persist its schedule state to prevent duplicate task execution across restarts. Using django-celery-beat, schedules are stored in the PostgreSQL database, enabling dynamic schedule management through the Django Admin interface.

Success means developers can configure recurring tasks, see them dispatched at the correct intervals, and modify schedules without restarting containers.

## Acceptance Criteria

### Functional Criteria
- [ ] Celery Beat container shares backend codebase (same Dockerfile)
- [ ] Scheduler connects to Redis broker successfully at `redis://redis:6379/0`
- [ ] Scheduled tasks execute at configured intervals
- [ ] Scheduler logs show task dispatch messages with timestamps
- [ ] Scheduler persists schedule state to database to avoid duplicate dispatches
- [ ] Scheduler can be stopped/started without task loss
- [ ] Default schedule configured for daily scraping at 2 AM local time

### Technical Criteria
- [ ] Scheduler service defined in docker-compose.yml
- [ ] Inherits from backend service (same Docker image)
- [ ] Command: `celery -A veille_tech beat --loglevel=info`
- [ ] django-celery-beat installed for database-backed schedules
- [ ] Schedule stored in database tables (django_celery_beat_*)
- [ ] Scheduler uses database as schedule backend (not in-memory)
- [ ] Scheduler logs accessible via `docker-compose logs scheduler`
- [ ] Scheduler container restarts automatically on failure

### UI/UX Criteria (if applicable)
- Django Admin interface shows scheduled tasks in django-celery-beat admin
- Developers can add/edit/delete schedules via admin interface

### Performance Criteria
- [ ] Scheduler starts and connects to Redis within 10 seconds
- [ ] Task dispatch occurs within 1 second of scheduled time
- [ ] Scheduler handles up to 100 concurrent schedules
- [ ] Database queries for schedule checking complete within 50ms

## Technical Details

### Components Affected
- `docker-compose.yml` (scheduler service definition)
- `backend/Dockerfile` (shared with backend service)
- `backend/veille_tech/celery.py` (Celery Beat configuration)
- `backend/veille_tech/settings/base.py` (django-celery-beat configuration)
- PostgreSQL database (schedule storage tables)

### API Changes
- None (scheduler dispatches tasks, does not expose API)

### Database Changes
- New tables from django-celery-beat:
  - `django_celery_beat_periodictask`
  - `django_celery_beat_intervalschedule`
  - `django_celery_beat_crontabschedule`
  - `django_celery_beat_clockedschedule`
  - `django_celery_beat_solarschedule`

### External Integrations
- Redis broker for task enqueueing
- PostgreSQL for schedule persistence

## Implementation Notes

### Suggested Approach

1. **Install django-celery-beat:**
   - Add to `backend/pyproject.toml` dependencies
   - Run `poetry add django-celery-beat`
   - Add `django_celery_beat` to `INSTALLED_APPS`

2. **Configure Celery Beat to use database scheduler:**
   - In `backend/veille_tech/celery.py`:
     ```python
     app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'
     ```

3. **Define scheduler service in docker-compose.yml:**
   - Inherit from backend service (same image)
   - Override command: `poetry run celery -A veille_tech beat --loglevel=info`
   - Mount same source code volume as backend
   - Set environment variables from `.env.backend`
   - Depend on redis, db, and backend services

4. **Create initial schedule via Django Admin or migration:**
   - Create PeriodicTask for daily scraping
   - CrontabSchedule: `0 2 * * *` (2 AM daily)
   - Task name: `veille_tech.tasks.daily_scraping_task`

5. **Run database migrations:**
   - `python manage.py migrate django_celery_beat`
   - Creates schedule tables in PostgreSQL

### Technical Considerations

**Performance:**
- Database-backed scheduler more reliable than in-memory
- Schedule checking frequency: default 5 seconds (configurable)
- Minimal CPU usage when no tasks scheduled
- Database queries optimized with indexes

**Security:**
- Scheduler has read-only access to Redis (only enqueues tasks)
- Schedule management restricted to Django Admin (admin-only access)
- No sensitive data in schedule configurations

**Scalability:**
- Single scheduler instance sufficient for development and production
- Multiple schedulers not recommended (causes duplicate tasks)
- Distributed locking prevents race conditions if multiple schedulers accidentally run

**Backward Compatibility:**
- django-celery-beat compatible with Celery 5+
- Migration path from Celery's default scheduler (file-based)

### Known Challenges

**Challenge:** Scheduler may dispatch duplicate tasks if restarted at exact schedule time
**Solution:** django-celery-beat tracks last run time in database to prevent duplicates

**Challenge:** Clock drift between scheduler and workers
**Solution:** Use NTP to synchronize container clocks; schedule times in UTC

**Challenge:** Timezone handling for scheduled tasks
**Solution:** Configure Django `USE_TZ=True` and store schedules in UTC; convert to local time for display

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-2: Database Service with Vector Support (scheduler stores schedules in database)
- US-3: Redis Broker and Cache Service (scheduler enqueues tasks to Redis)
- US-4: Django Backend API Service (scheduler shares codebase)
- US-6: Celery Worker Service for AI Pipeline (workers execute scheduled tasks)

### Blocks
- Feature user stories that require recurring tasks (e.g., daily scraping)

## Test Scenarios

### Happy Path
1. Developer runs database migrations: `docker-compose exec backend python manage.py migrate django_celery_beat`
2. Developer runs `docker-compose up -d scheduler`
3. Scheduler container starts and connects to Redis and database
4. Scheduler logs show: "celery beat v5.x.x is starting"
5. Developer creates periodic task via Django Admin:
   - Name: "Test Task"
   - Task: `veille_tech.tasks.test_task`
   - Interval: 1 minute
6. After 1 minute, scheduler logs show: "Scheduler: Sending due task test_task"
7. Worker picks up task and executes it

### Alternative Paths
1. Developer opens Django Admin at `http://localhost:8000/admin/`
2. Navigates to "Periodic Tasks" section (django-celery-beat)
3. Views list of scheduled tasks
4. Edits existing task to change schedule
5. Scheduler picks up change within 5 seconds (next schedule check)

### Error Scenarios
1. **Redis broker unavailable:** Redis service not running
   - Expected: Scheduler fails to start and retries connection
   - Logs show: "Error connecting to Redis"
   - Scheduler waits for Redis to become available

2. **Database unavailable:** PostgreSQL service not running
   - Expected: Scheduler cannot read schedules
   - Logs show: "OperationalError: could not connect to server"
   - Scheduler waits for database to become available

3. **Invalid task name in schedule:** Task does not exist
   - Expected: Scheduler enqueues task, but worker logs error
   - Worker logs: "NotRegistered: 'invalid_task_name'"
   - Developer corrects task name in Django Admin

4. **Duplicate scheduler instances:** Two schedulers running accidentally
   - Expected: django-celery-beat's distributed locking prevents duplicate dispatches
   - Only one scheduler actively dispatches tasks

### Edge Cases
1. **Scheduler restart during scheduled time:** Scheduler stopped at 2:00 AM, scheduled task at 2:00 AM
   - Expected: After restart, scheduler checks last run time and dispatches task if missed
   - No duplicate task dispatched

2. **Clock skew between scheduler and database:** Scheduler time ahead of database time
   - Expected: Scheduler uses database time as source of truth
   - Tasks dispatched according to database time

## UI/UX Specifications

### Django Admin Interface
- Periodic Tasks admin shows list of scheduled tasks
- Fields: Name, Task, Schedule (Interval/Crontab), Enabled, Last Run At
- Inline editing of schedules
- Enable/disable toggle for quick task control

## Security Considerations

- Scheduler only enqueues tasks to Redis (no task execution)
- Schedule management restricted to Django Admin (admin users only)
- Scheduled task names validated against registered Celery tasks
- No arbitrary code execution via schedule definitions
- Audit log of schedule changes (Django Admin history)

## Performance Requirements

- **Startup Time:** Scheduler connected to broker within 10 seconds (P95)
- **Dispatch Latency:** Tasks dispatched within 1 second of scheduled time
- **Schedule Checking Frequency:** Database polled every 5 seconds
- **Database Query Time:** Schedule queries complete within 50ms
- **Maximum Schedules:** Support up to 100 concurrent schedules

## Accessibility Requirements

- Django Admin interface for schedule management follows Django's built-in accessibility standards

## Definition of Done

- [ ] Scheduler service defined in docker-compose.yml with all required configuration
- [ ] Scheduler inherits from backend service (same Docker image)
- [ ] django-celery-beat installed and configured
- [ ] Database migrations applied (django_celery_beat tables created)
- [ ] Celery app configured to use DatabaseScheduler
- [ ] Scheduler connects to Redis and database successfully
- [ ] Sample periodic task created for testing
- [ ] Scheduler dispatches tasks at correct intervals
- [ ] Django Admin interface shows scheduled tasks
- [ ] Schedule state persists across scheduler restarts
- [ ] Scheduler logs accessible and showing dispatch messages
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] Scheduler starts successfully with `docker-compose up scheduler`
- [ ] Task scheduling and dispatch verified
- [ ] All acceptance criteria verified
- [ ] Documentation updated with scheduler management instructions
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
- [ ] Should we create default schedules via data migration or Django Admin?
- [ ] Do we need Celery Flower for monitoring scheduler and worker activity?
- [ ] Should scheduled tasks be configurable via environment variables?

### Assumptions
- Single scheduler instance sufficient for development and production
- django-celery-beat provides reliable schedule persistence
- Database-backed scheduler preferred over file-based for reliability

### Out of Scope
- Multiple scheduler instances with distributed locking
- Advanced scheduling patterns (solar times, custom schedulers)
- Celery Flower monitoring dashboard
- Dynamic schedule creation via API (Admin UI sufficient)

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-2: Database Service with Vector Support (depends on this)
- US-3: Redis Broker and Cache Service (depends on this)
- US-4: Django Backend API Service (shares codebase)
- US-6: Celery Worker Service for AI Pipeline (executes scheduled tasks)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
