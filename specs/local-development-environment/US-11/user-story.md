# User Story: Service Health Monitoring and Logs

**Story ID:** US-11
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** visibility into service health and logs
**So that** I can quickly diagnose issues during development

## Description

This User Story establishes comprehensive health monitoring and logging infrastructure that enables developers to quickly identify and debug issues in the local development environment. With 6 services running concurrently (database, Redis, backend, frontend, worker, scheduler), developers need clear visibility into which services are healthy and access to detailed logs when troubleshooting.

Health checks provide automated validation that services are not just running, but actually functional—for example, a database container may be running but unable to accept connections. Docker Compose health checks enable dependency orchestration, ensuring dependent services wait for upstream services to become healthy before starting.

Centralized logging through Docker Compose provides a unified interface to view logs from all services, with the ability to filter by service, follow logs in real-time, and search for specific error messages. Structured logging with timestamps and severity levels enables efficient debugging.

Success means developers can instantly determine if all services are healthy, access logs for any service with a single command, and quickly identify the root cause of issues.

## Acceptance Criteria

### Functional Criteria
- [ ] `docker-compose ps` shows status of all services (up/down/healthy)
- [ ] Each service has health check configured where applicable (db, redis, backend)
- [ ] `docker-compose logs [service]` displays service-specific logs
- [ ] `docker-compose logs -f` follows logs in real-time across all services
- [ ] Error logs clearly indicate source service and timestamp
- [ ] Startup logs confirm successful initialization of each service
- [ ] Request/response logs available for backend API debugging
- [ ] Log format includes timestamps and severity levels (INFO, WARNING, ERROR)

### Technical Criteria
- [ ] Health checks configured in docker-compose.yml:
  - Database: `pg_isready -U postgres`
  - Redis: `redis-cli ping`
  - Backend: HTTP GET to `/api/health/` returns 200
- [ ] Health check parameters: interval, timeout, retries, start_period
- [ ] Log drivers configured: default JSON file driver
- [ ] Log rotation configured to prevent disk fill
- [ ] Structured logging format (JSON) for easier parsing (optional)
- [ ] Service dependencies use `depends_on` with health check conditions

### UI/UX Criteria (if applicable)
- Terminal output clearly shows service status with color coding
- Log output formatted for readability (timestamps, service names)

### Performance Criteria
- [ ] Health checks complete within 5 seconds per service
- [ ] Log retrieval command responds within 1 second
- [ ] Real-time log following has < 1 second latency
- [ ] Log files limited to 10MB per service (rotation enabled)

## Technical Details

### Components Affected
- `docker-compose.yml` (health check configuration)
- `backend/veille_tech/urls.py` (health check endpoint)
- `backend/veille_tech/views.py` (health check view)
- Docker log configuration (log driver, rotation)
- `docs/setup/00_setup_local_docker.md` (logging commands)

### API Changes
- New endpoint: `GET /api/health/` returns `{"status": "healthy", "services": {...}}`
- Optional: Detailed health check with database and Redis connectivity validation

### Database Changes
- None

### External Integrations
- None (Docker logging infrastructure only)

## Implementation Notes

### Suggested Approach

1. **Configure health checks in docker-compose.yml:**

   **Database service:**
   ```yaml
   db:
     healthcheck:
       test: ["CMD-SHELL", "pg_isready -U postgres"]
       interval: 10s
       timeout: 5s
       retries: 5
       start_period: 10s
   ```

   **Redis service:**
   ```yaml
   redis:
     healthcheck:
       test: ["CMD", "redis-cli", "ping"]
       interval: 10s
       timeout: 3s
       retries: 5
       start_period: 5s
   ```

   **Backend service:**
   ```yaml
   backend:
     healthcheck:
       test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
       interval: 30s
       timeout: 10s
       retries: 3
       start_period: 40s
   ```

2. **Implement backend health check endpoint:**
   ```python
   # backend/veille_tech/views.py
   from django.http import JsonResponse
   from django.db import connection
   from django.core.cache import cache

   def health_check(request):
       status = {"status": "healthy", "services": {}}

       # Check database
       try:
           connection.ensure_connection()
           status["services"]["database"] = "healthy"
       except Exception as e:
           status["services"]["database"] = f"unhealthy: {str(e)}"
           status["status"] = "unhealthy"

       # Check Redis
       try:
           cache.set("health_check", "ok", 1)
           status["services"]["redis"] = "healthy"
       except Exception as e:
           status["services"]["redis"] = f"unhealthy: {str(e)}"
           status["status"] = "unhealthy"

       return JsonResponse(status)
   ```

3. **Configure service dependencies with health checks:**
   ```yaml
   backend:
     depends_on:
       db:
         condition: service_healthy
       redis:
         condition: service_healthy
   ```

4. **Configure logging:**
   - Default JSON file log driver (no changes needed)
   - Optional: Add log rotation limits:
     ```yaml
     logging:
       driver: "json-file"
       options:
         max-size: "10m"
         max-file: "3"
     ```

5. **Document logging commands:**
   - View all logs: `docker-compose logs`
   - View specific service: `docker-compose logs backend`
   - Follow logs: `docker-compose logs -f`
   - Filter by time: `docker-compose logs --since 10m`
   - Tail last N lines: `docker-compose logs --tail=100`

### Technical Considerations

**Performance:**
- Health checks run on configured intervals (balance frequency vs overhead)
- Start period allows slow-starting services to initialize before health checks fail
- Log file rotation prevents disk space exhaustion

**Security:**
- Health check endpoint should not expose sensitive information
- Consider authentication for production health endpoints
- Logs may contain sensitive data—configure accordingly

**Scalability:**
- Health checks scale well with multiple service instances
- Centralized logging becomes challenging at scale (consider log aggregation like ELK)

**Backward Compatibility:**
- Docker Compose v2 health check syntax
- Health check conditions require Docker Compose 1.27+

### Known Challenges

**Challenge:** Health checks may report false negatives during heavy load
**Solution:** Configure appropriate timeouts and retries; use start_period for slow initialization

**Challenge:** Logs fill disk space over time
**Solution:** Configure log rotation with max-size and max-file limits

**Challenge:** Debugging intermittent health check failures
**Solution:** Increase health check logging verbosity; check network connectivity between containers

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-2: Database Service with Vector Support (database health check)
- US-3: Redis Broker and Cache Service (Redis health check)
- US-4: Django Backend API Service (backend health check endpoint)

### Blocks
- None (health monitoring is supplementary infrastructure)

## Test Scenarios

### Happy Path
1. Developer runs `docker-compose up -d`
2. All services start successfully
3. Developer runs `docker-compose ps`
4. Output shows all services "healthy":
   ```
   NAME       SERVICE    STATUS         HEALTH
   db         db         Up 1 minute    healthy
   redis      redis      Up 1 minute    healthy
   backend    backend    Up 1 minute    healthy
   frontend   frontend   Up 1 minute
   worker     worker     Up 1 minute
   scheduler  scheduler  Up 1 minute
   ```
5. Developer runs `docker-compose logs backend`
6. Backend logs display with timestamps and request logs
7. Developer runs `docker-compose logs -f`
8. Logs from all services stream in real-time

### Alternative Paths
1. Developer filters logs by time:
   ```bash
   docker-compose logs --since 10m backend
   ```
2. Only logs from last 10 minutes displayed

3. Developer searches logs for errors:
   ```bash
   docker-compose logs backend | grep ERROR
   ```
4. Only ERROR-level logs displayed

### Error Scenarios
1. **Database unhealthy:** PostgreSQL not accepting connections
   - Expected: `docker-compose ps` shows db as "unhealthy"
   - Backend service does not start (waits for db health)
   - Logs show health check failures

2. **Backend health check failing:** /api/health/ returns 500
   - Expected: `docker-compose ps` shows backend as "unhealthy"
   - Health check logs show HTTP error details
   - Developer inspects backend logs to identify root cause

3. **Service crash:** Backend container exits unexpectedly
   - Expected: `docker-compose ps` shows backend as "Exit 1"
   - Developer runs `docker-compose logs backend` to view error traces
   - Container restarts automatically (restart policy)

4. **Log disk space exhaustion:** Logs fill available disk
   - Expected: Log rotation prevents full disk
   - Oldest logs deleted automatically when limits reached

### Edge Cases
1. **Health check during initialization:** Service not ready yet
   - Expected: Health check uses start_period to delay initial checks
   - Service not marked unhealthy during startup grace period

2. **Viewing logs from stopped container:** Service stopped but logs retained
   - Expected: `docker-compose logs [service]` still shows historical logs
   - Logs persist until container removed with `docker-compose down -v`

## UI/UX Specifications

### Terminal Output
- `docker-compose ps` uses color coding for status (green=healthy, red=unhealthy)
- Log output prefixed with service name: `[backend] | 2025-01-27 10:30:00 | INFO | ...`
- Timestamps in ISO 8601 format for easy parsing

## Security Considerations

- Health check endpoint should not expose sensitive system information
- Logs may contain sensitive data (API keys, user data)—avoid logging secrets
- Production health endpoints should require authentication
- Log access restricted to authorized developers

## Performance Requirements

- **Health Check Execution Time:** < 5 seconds per service (P95)
- **Log Retrieval Time:** < 1 second to display recent logs
- **Real-time Log Latency:** < 1 second for log streaming
- **Log File Size:** Limited to 10MB per service with rotation
- **Health Check Frequency:** Every 10-30 seconds (configurable)

## Accessibility Requirements

Not applicable for logging infrastructure.

## Definition of Done

- [ ] Health checks configured for db, redis, and backend services
- [ ] Health check parameters optimized (interval, timeout, retries)
- [ ] Backend health check endpoint implemented and tested
- [ ] Service dependencies configured with health check conditions
- [ ] Log rotation configured to prevent disk fill
- [ ] Logging commands documented with examples
- [ ] Code reviewed by tech lead
- [ ] Tested: All services show "healthy" status after startup
- [ ] Tested: Logs accessible for all services
- [ ] Tested: Real-time log following works correctly
- [ ] All acceptance criteria verified
- [ ] Documentation updated with health monitoring workflow
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
- [ ] Should we implement a centralized health check endpoint that aggregates all services?
- [ ] Do we need structured JSON logging for easier parsing and analysis?
- [ ] Should we integrate with a log aggregation tool (ELK, Grafana Loki)?

### Assumptions
- Docker Compose's built-in logging sufficient for local development
- Health checks using command-line tools (pg_isready, redis-cli, curl)
- Developers comfortable using terminal commands for log access

### Out of Scope
- Centralized log aggregation (ELK, Splunk, Datadog)
- Advanced monitoring (Prometheus, Grafana)
- Application Performance Monitoring (APM) tools
- Distributed tracing (OpenTelemetry, Jaeger)

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-2: Database Service with Vector Support (depends on this)
- US-3: Redis Broker and Cache Service (depends on this)
- US-4: Django Backend API Service (depends on this)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
