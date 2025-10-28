# User Story: Django Backend API Service

**Story ID:** US-4
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 3 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** the Django/DRF backend API running with hot reload
**So that** I can develop and test API endpoints without rebuilding containers

## Description

This User Story establishes the Django REST Framework backend API service as the core application server for the Technology Watch Platform. The backend exposes RESTful API endpoints for authentication, subscription management, report consultation, and FinOps tracking, while also serving the Django Admin interface for administrative tasks.

The service must support hot reloading, meaning code changes are automatically detected and the server restarts without requiring manual container rebuilds. This dramatically improves developer productivity during active development sessions.

The backend connects to both PostgreSQL (for persistent data) and Redis (for caching and Celery broker), serving as the central orchestrator for all application logic. It must be accessible from both the frontend (for API calls) and developers' browsers (for Django Admin access).

Success means developers can edit Python code, see changes reflected immediately, and test API endpoints and admin features without container restarts.

## Acceptance Criteria

### Functional Criteria
- [ ] Django development server runs on port 8000
- [ ] API accessible at `http://localhost:8000/api/`
- [ ] Django Admin accessible at `http://localhost:8000/admin/`
- [ ] Code changes trigger automatic reload without container restart
- [ ] Backend connects successfully to PostgreSQL database
- [ ] Backend connects successfully to Redis for caching and Celery broker
- [ ] Static files served correctly for Django Admin interface
- [ ] Environment variables loaded from `.env.backend`
- [ ] Python dependencies installed via Poetry
- [ ] Container logs show startup messages, request logs, and error traces

### Technical Criteria
- [ ] Backend service defined in docker-compose.yml
- [ ] Base image: `python:3.13-slim`
- [ ] Poetry 2.2.1 installed for dependency management
- [ ] Source code mounted as volume for hot reload
- [ ] Django settings: `DEBUG=True`, `ALLOWED_HOSTS=*` for local development
- [ ] Command: `python manage.py runserver 0.0.0.0:8000`
- [ ] Health check endpoint: `/api/health/` returns 200 OK
- [ ] CORS headers configured to allow frontend origin (localhost:3000)

### UI/UX Criteria (if applicable)
- Django Admin interface loads correctly with all registered models
- Static files (CSS, JS) for admin interface served without 404 errors

### Performance Criteria
- [ ] Backend starts and becomes healthy within 20 seconds
- [ ] API endpoint response time < 500ms in development mode (P95)
- [ ] Hot reload triggers within 2 seconds of code change
- [ ] Static file serving does not cause significant latency

## Technical Details

### Components Affected
- `docker-compose.yml` (backend service definition)
- `backend/Dockerfile` (new file)
- `backend/pyproject.toml` (Poetry dependencies)
- `backend/manage.py` (Django management script)
- `backend/veille_tech/settings/` (Django settings modules)
- `.env.backend` (environment configuration)

### API Changes
- New health check endpoint: `GET /api/health/` returns `{"status": "healthy"}`
- API root endpoint: `GET /api/` returns API documentation or available endpoints

### Database Changes
- None at this stage (models handled in feature-specific user stories)

### External Integrations
- PostgreSQL database connection
- Redis connection for cache and Celery broker
- Google AI API (API key loaded from environment)
- Firecrawl API (API key loaded from environment)

## Implementation Notes

### Suggested Approach

1. **Create backend Dockerfile:**
   - Base: `python:3.13-slim`
   - Install Poetry 2.2.1
   - Copy `pyproject.toml` and `poetry.lock`
   - Install dependencies with `poetry install`
   - Set working directory to `/app`
   - Expose port 8000

2. **Configure docker-compose backend service:**
   - Build from `./backend/Dockerfile`
   - Mount source code: `./backend:/app` for hot reload
   - Set environment variables from `.env.backend`
   - Depend on db and redis services
   - Command: `poetry run python manage.py runserver 0.0.0.0:8000`
   - Health check: `curl http://localhost:8000/api/health/`

3. **Set up Django settings:**
   - Use django-environ or python-decouple for environment variables
   - Database: PostgreSQL connection from `DATABASE_URL`
   - Cache: Redis connection from `REDIS_URL`
   - Celery broker: `CELERY_BROKER_URL`
   - Static files: Configure `STATIC_ROOT` and `STATIC_URL`
   - CORS: Allow localhost:3000 for frontend requests

4. **Create health check endpoint:**
   - Simple view returning JSON with status
   - Optionally check database and Redis connectivity
   - Register endpoint in `urls.py`

### Technical Considerations

**Performance:**
- Hot reload uses Django's auto-reload mechanism (watches .py files)
- Volume mounts may have performance implications on Windows (WSL2 mitigates this)
- Use Poetry's `--no-dev` flag in production builds (not local development)

**Security:**
- `DEBUG=True` acceptable for local development only
- `ALLOWED_HOSTS=*` acceptable for local development only
- API keys loaded from environment, never committed to Git
- CORS configured to allow frontend origin only

**Scalability:**
- Single backend instance sufficient for local development
- Gunicorn or uWSGI not needed (Django dev server adequate)
- Database connection pooling configured for concurrent requests

**Backward Compatibility:**
- Python 3.13 ensures latest language features and performance improvements
- Django 4.2+ LTS ensures long-term support and stability

### Known Challenges

**Challenge:** Poetry dependency resolution may be slow on first install
**Solution:** Use Poetry's dependency lock file for consistent, fast installs; consider caching Poetry cache directory

**Challenge:** Volume mount performance on Windows Docker Desktop
**Solution:** Use WSL2 backend; store code in WSL filesystem for native performance

**Challenge:** Hot reload may not detect changes in non-.py files (templates, static files)
**Solution:** Document that frontend assets handled by frontend service; backend only reloads Python code

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-2: Database Service with Vector Support (backend requires database connection)
- US-3: Redis Broker and Cache Service (backend requires Redis connection)

### Blocks
- US-6: Celery Worker Service for AI Pipeline (shares backend codebase)
- US-7: Celery Beat Scheduler Service (shares backend codebase)
- US-9: Database Initialization and Migrations (requires backend service)
- US-10: Superuser Creation for Admin Access (requires backend service)

## Test Scenarios

### Happy Path
1. Developer runs `docker-compose up -d backend`
2. Backend container starts and connects to db and redis
3. Health check passes within 20 seconds
4. Developer opens `http://localhost:8000/api/health/`
5. Response: `{"status": "healthy"}`
6. Developer opens `http://localhost:8000/admin/`
7. Django Admin login page displays correctly with CSS styling
8. Developer edits `backend/veille_tech/views.py`
9. Backend logs show "Watching for file changes with StatReloader"
10. Within 2 seconds, logs show "Performing system checks... OK"
11. Developer refreshes browser, changes are reflected

### Alternative Paths
1. Developer runs `docker-compose exec backend python manage.py shell`
2. Interactive Django shell opens
3. Developer can execute Python code and ORM queries for debugging

### Error Scenarios
1. **Database connection failure:** PostgreSQL not running
   - Expected: Backend fails health check
   - Logs show "OperationalError: could not connect to server"
   - Backend waits for database to become available (depends_on with health check)

2. **Redis connection failure:** Redis not running
   - Expected: Backend starts but cache operations fail
   - Logs show "ConnectionError: Error connecting to Redis"
   - Resolution: Ensure Redis service starts before backend

3. **Missing environment variables:** `.env.backend` not configured
   - Expected: Backend fails to start
   - Logs show clear error about missing required variables
   - Resolution: Copy `.env.backend.example` to `.env.backend`

4. **Port conflict:** Another service on port 8000
   - Expected: Docker reports port binding error
   - Resolution: Stop conflicting service or change port mapping

### Edge Cases
1. **Syntax error in Python code:** Developer introduces syntax error
   - Expected: Hot reload detects error and displays traceback in logs
   - Server stops serving requests until error fixed
   - After fix, server resumes automatically

2. **Long-running database migration:** Migration takes > 30 seconds
   - Expected: Health check may timeout during migration
   - Docker restarts backend container after health check failures
   - Resolution: Increase health check timeout for migrations

## UI/UX Specifications

### Django Admin Interface
- Standard Django Admin theme with all registered models
- Login page accessible at `/admin/`
- Static files (CSS, JS) loaded correctly from CDN or local static directory

### API Documentation (Optional)
- Consider DRF browsable API at `/api/`
- Swagger/OpenAPI docs at `/api/docs/` (if implemented)

## Security Considerations

- `DEBUG=True` only for local development—must be `False` in production
- `ALLOWED_HOSTS=*` only for local development—must be restricted in production
- API keys for Google AI and Firecrawl loaded from environment variables
- Database credentials loaded from environment variables
- JWT secret key generated and stored in `.env.backend`
- CORS restricted to frontend origin (localhost:3000)
- Django Admin accessible only after authentication

## Performance Requirements

- **Startup Time:** Backend healthy within 20 seconds (P95)
- **API Response Time:** < 500ms for simple GET requests (P95)
- **Hot Reload Time:** Code changes detected and reloaded within 2 seconds
- **Static File Serving:** < 100ms for admin CSS/JS files
- **Database Query Time:** < 100ms for typical ORM queries

## Accessibility Requirements

- Django Admin interface follows Django's built-in accessibility standards
- API endpoints return proper HTTP status codes for error handling
- Error messages are clear and actionable

## Definition of Done

- [ ] Backend service defined in docker-compose.yml with all required configuration
- [ ] Backend Dockerfile created and building successfully
- [ ] Poetry dependencies installed and locked (poetry.lock committed)
- [ ] Django settings configured for local development
- [ ] Health check endpoint implemented and responding
- [ ] Backend connects to PostgreSQL and Redis successfully
- [ ] Django Admin interface accessible and styled correctly
- [ ] Hot reload working for Python code changes
- [ ] CORS configured to allow frontend requests
- [ ] Environment variables documented in .env.backend.example
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] Backend starts successfully with `docker-compose up backend`
- [ ] All acceptance criteria verified
- [ ] Documentation updated with API access instructions
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
- [ ] Should we use Gunicorn for local development instead of Django dev server?
- [ ] Should we implement API documentation (Swagger/OpenAPI) at this stage?
- [ ] Do we need to configure Django Debug Toolbar for local development?

### Assumptions
- Django development server adequate for local development (no Gunicorn needed)
- Single backend instance sufficient for local development load
- Hot reload is critical for developer productivity

### Out of Scope
- Production WSGI server configuration (Gunicorn, uWSGI)
- Advanced Django middleware (throttling, monitoring)
- API versioning strategy (handled in feature user stories)
- Background task execution (handled by Celery worker service)

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-2: Database Service with Vector Support (depends on this)
- US-3: Redis Broker and Cache Service (depends on this)
- US-5: React Frontend SPA Service (calls backend API)
- US-6: Celery Worker Service for AI Pipeline (shares codebase)
- US-9: Database Initialization and Migrations (uses backend service)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
