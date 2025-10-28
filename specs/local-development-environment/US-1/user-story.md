# User Story: Docker Compose Service Orchestration

**Story ID:** US-1
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 3 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want to** start all required services with a single command
**So that** I can quickly spin up the complete development environment

## Description

This User Story establishes the foundational Docker Compose configuration that orchestrates all 6 microservices required for the AI-powered Technology Watch Platform. The configuration must handle service dependencies, networking, health checks, and lifecycle management to provide a seamless development experience.

The Docker Compose setup serves as the infrastructure backbone for all other User Stories in this feature. It defines the complete service topology including PostgreSQL database with pgvector extension, Redis for message brokering and caching, Django backend API, React frontend SPA, Celery worker for AI pipeline execution, and Celery Beat scheduler for recurring tasks.

Success means a developer can execute `docker-compose up` and have all services running, healthy, and accessible within 60 seconds on modern hardware.

## Acceptance Criteria

### Functional Criteria
- [ ] `docker-compose.yml` defines all 6 services: db, redis, backend, frontend, worker, scheduler
- [ ] `docker-compose build` successfully builds all container images without errors
- [ ] `docker-compose up -d` starts all services in detached mode
- [ ] `docker-compose ps` shows all services as "running" with healthy status
- [ ] `docker-compose down` stops and removes all containers cleanly without data loss
- [ ] Services start in correct dependency order (db/redis initialize before backend/worker)
- [ ] Service logs accessible via `docker-compose logs [service_name]`
- [ ] All services restart automatically on failure (restart policy configured)

### Technical Criteria
- [ ] Docker Compose file version 3.8 or higher
- [ ] Service health checks implemented for db, redis, and backend
- [ ] Named volumes created for postgres_data and redis_data
- [ ] Internal Docker network created for service communication
- [ ] Port mappings configured: db (5432), redis (6379), backend (8000), frontend (3000)
- [ ] Environment variable files referenced correctly (.env.backend, .env.frontend)
- [ ] Dependencies declared using `depends_on` with health check conditions
- [ ] Resource limits defined to prevent runaway containers

### UI/UX Criteria (if applicable)
- Not applicable for infrastructure configuration

### Performance Criteria
- [ ] All services start within 60 seconds on hardware with 8GB RAM, 4 CPU cores
- [ ] Service orchestration uses < 500MB RAM overhead beyond individual service requirements
- [ ] Build time for all images < 10 minutes on first build (subsequent builds use cache)

## Technical Details

### Components Affected
- `docker-compose.yml` (new file, root directory)
- `.dockerignore` (new file, for efficient image builds)
- `backend/Dockerfile` (new file)
- `frontend/Dockerfile` (new file)
- `.env.backend.example` (new file)
- `.env.frontend.example` (new file)
- `.gitignore` (update to exclude .env files)

### API Changes
- None (infrastructure only)

### Database Changes
- None at this stage (schema handled in US-9)

### External Integrations
- Docker Hub for pulling base images (postgres:15, redis:latest, python:3.13-slim, node:20-alpine)

## Implementation Notes

### Suggested Approach

1. **Create docker-compose.yml structure:**
   - Define all 6 services with appropriate base images
   - Configure service dependencies (db/redis before backend/worker)
   - Set up named volumes for data persistence
   - Create internal network for service communication

2. **Configure health checks:**
   - Database: `pg_isready -U postgres`
   - Redis: `redis-cli ping`
   - Backend: HTTP GET to `/api/health/` endpoint

3. **Set up port mappings:**
   - Map ports only for services accessed from host (backend, frontend)
   - Keep db and redis on internal network only (security)

4. **Create Dockerfiles:**
   - Backend: Python 3.13 slim image with Poetry setup
   - Frontend: Node 20 alpine image with npm/vite setup
   - Optimize for layer caching to speed up rebuilds

5. **Configure environment files:**
   - Create .example files with placeholder values
   - Document required vs optional variables
   - Add .env files to .gitignore

### Technical Considerations

**Performance:**
- Use multi-stage builds for smaller final images
- Leverage Docker layer caching by copying dependency files before source code
- Configure restart policies to balance availability vs resource usage

**Security:**
- Do not expose db/redis ports to host network
- Use environment variables for all secrets
- Ensure .env files never committed to Git
- Use least-privilege user in containers (non-root)

**Scalability:**
- Design compose file to support horizontal worker scaling (future: docker-compose scale worker=3)
- Use resource limits to prevent resource exhaustion

**Backward Compatibility:**
- Ensure Docker Compose v2 syntax compatibility
- Test on Windows (Docker Desktop with WSL2), macOS, and Linux

### Known Challenges

**Challenge:** Windows Docker Desktop requires WSL2 backend
**Solution:** Provide detailed WSL2 setup documentation and troubleshooting guide

**Challenge:** Large base images increase build time
**Solution:** Use slim/alpine variants where possible; document expected build times

**Challenge:** M1/M2 Mac compatibility for base images
**Solution:** Use multi-architecture images or specify platform: linux/amd64

## Dependencies

### Depends On
- None (this is the foundational User Story)

### Blocks
- US-2: Database Service with Vector Support
- US-3: Redis Broker and Cache Service
- US-4: Django Backend API Service
- US-5: React Frontend SPA Service
- US-6: Celery Worker Service for AI Pipeline
- US-7: Celery Beat Scheduler Service
- US-8: Environment Configuration Management

## Test Scenarios

### Happy Path
1. Developer clones repository
2. Developer runs `docker-compose build`
3. Build completes successfully for all services
4. Developer runs `docker-compose up -d`
5. All 6 services start and report healthy status
6. Developer runs `docker-compose ps` and sees all services "running"
7. Developer accesses http://localhost:8000 and http://localhost:3000
8. Developer runs `docker-compose down`
9. All services stop cleanly without errors

### Alternative Paths
1. Developer runs `docker-compose up` without `-d` flag
2. Logs stream to console in real-time
3. Developer presses Ctrl+C
4. Services shut down gracefully

### Error Scenarios
1. **Port conflict:** Port 8000 already in use on host
   - Expected: Clear error message indicating port conflict
   - Resolution: Document how to change port mappings

2. **Insufficient memory:** Docker allocated < 4GB RAM
   - Expected: Services fail to start with OOM errors
   - Resolution: Clear error message with minimum requirements

3. **Missing .env files:** .env.backend not created from example
   - Expected: Backend service fails with clear message about missing environment variables
   - Resolution: Documentation emphasizes copying .env.example files

### Edge Cases
1. **Stopping mid-startup:** Developer runs `docker-compose down` while services still starting
   - Expected: Clean shutdown of all services regardless of state

2. **Repeated restarts:** Developer runs `docker-compose restart` multiple times
   - Expected: Services restart cleanly without data corruption

## UI/UX Specifications

Not applicable for infrastructure configuration.

## Security Considerations

- Database and Redis ports (5432, 6379) not exposed to host network—only accessible internally
- All secrets loaded from environment files, never hardcoded
- .env files excluded from Git via .gitignore
- Container users run as non-root where possible (backend, worker)
- Docker images from official, trusted registries only

## Performance Requirements

- **Startup Time:** All services healthy within 60 seconds (P95)
- **Build Time:** Initial build completes within 10 minutes (P95)
- **Memory Overhead:** Docker orchestration uses < 500MB RAM
- **Disk Space:** Total image size < 5GB for all services

## Accessibility Requirements

Not applicable for infrastructure configuration.

## Definition of Done

- [ ] docker-compose.yml file created with all 6 services
- [ ] Dockerfiles created for backend and frontend
- [ ] Health checks configured and passing for db, redis, backend
- [ ] Named volumes configured for data persistence
- [ ] Environment example files created (.env.backend.example, .env.frontend.example)
- [ ] .gitignore updated to exclude .env files
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] All services start successfully with `docker-compose up`
- [ ] All services show "healthy" status in `docker-compose ps`
- [ ] Services shut down cleanly with `docker-compose down`
- [ ] Documentation updated with Docker Compose commands
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
- [ ] Should we use Docker Compose profiles for selective service startup (e.g., frontend-only mode)?
- [ ] Do we need a separate docker-compose.override.yml for developer customizations?

### Assumptions
- Developers have Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux) already installed
- Minimum hardware: 8GB RAM, 4 CPU cores, 10GB free disk space
- Developers have internet access for pulling Docker images

### Out of Scope
- Docker Swarm or Kubernetes orchestration (local development uses Docker Compose only)
- Pre-built images in container registry (developers build locally)
- Multi-environment configuration (staging, production)

## Related User Stories

- US-2: Database Service with Vector Support (blocked by this story)
- US-3: Redis Broker and Cache Service (blocked by this story)
- US-4: Django Backend API Service (blocked by this story)
- US-5: React Frontend SPA Service (blocked by this story)
- US-6: Celery Worker Service for AI Pipeline (blocked by this story)
- US-7: Celery Beat Scheduler Service (blocked by this story)
- US-8: Environment Configuration Management (related)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
