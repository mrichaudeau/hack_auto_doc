# User Story: Redis Broker and Cache Service

**Story ID:** US-3
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 1 Story Point
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** Redis configured as both Celery broker and application cache
**So that** I can test async task processing and caching locally

## Description

This User Story establishes Redis as a dual-purpose service providing both message brokering for Celery task queues and application-level caching. Redis is critical for the AI pipeline's asynchronous task processing, enabling background execution of Langgraph agents without blocking API requests.

The Redis service must be integrated into the Docker Compose stack with persistent storage for task queues and cache data. It must be accessible from the backend API (for cache operations), Celery workers (for task consumption), and Celery Beat scheduler (for recurring task dispatch).

By using separate Redis database numbers (0 for broker, 1 for cache), the service maintains logical separation between task queue data and cached application data, preventing conflicts and enabling independent configuration of eviction policies.

Success means Redis is accessible from all backend services, task queues function correctly, cache operations work, and data persists appropriately across restarts.

## Acceptance Criteria

### Functional Criteria
- [ ] Redis latest container runs on port 6379
- [ ] Redis accessible from backend, worker, and scheduler containers via internal network
- [ ] Redis data persists in named Docker volume across container restarts
- [ ] Celery broker URL configured: `redis://redis:6379/0`
- [ ] Cache backend configured: `redis://redis:6379/1`
- [ ] Redis connection validated with health check (PING command)
- [ ] Redis CLI accessible via `docker-compose exec redis redis-cli` for debugging

### Technical Criteria
- [ ] Redis service defined in docker-compose.yml
- [ ] Named volume `redis_data` created for persistence
- [ ] Separate Redis databases: DB 0 (broker), DB 1 (cache)
- [ ] Max memory policy configured: `allkeys-lru` for cache eviction
- [ ] Health check configured using `redis-cli ping`
- [ ] Redis logs accessible via `docker-compose logs redis`
- [ ] Redis container restarts automatically on failure

### UI/UX Criteria (if applicable)
- Not applicable for Redis service

### Performance Criteria
- [ ] Redis starts and becomes healthy within 5 seconds
- [ ] Cache GET operations respond within 5ms
- [ ] Task queue operations (LPUSH/RPOP) respond within 10ms
- [ ] Support at least 100 concurrent connections from backend services

## Technical Details

### Components Affected
- `docker-compose.yml` (redis service definition)
- `backend/settings/base.py` (cache and broker configuration)
- `.env.backend` (Redis connection URLs)
- Named volume: `redis_data`

### API Changes
- None (infrastructure service only)

### Database Changes
- None (Redis is key-value store, not relational database)

### External Integrations
- Redis Docker image from Docker Hub (official `redis:latest`)

## Implementation Notes

### Suggested Approach

1. **Define Redis service in docker-compose.yml:**
   - Use official `redis:latest` image
   - Create named volume for data persistence
   - Configure health check using `redis-cli ping`
   - Set restart policy to `unless-stopped`

2. **Configure Redis databases:**
   - DB 0: Celery broker for task queues
   - DB 1: Application cache for API responses, user sessions, etc.
   - Document this separation in .env.backend.example

3. **Configure eviction policy:**
   - Use `maxmemory-policy allkeys-lru` for cache database
   - Set reasonable maxmemory limit for development (e.g., 256MB)
   - Prevents Redis from consuming excessive memory

4. **Set up connection URLs:**
   - Backend settings: `CELERY_BROKER_URL = redis://redis:6379/0`
   - Backend settings: `CACHES['default']['LOCATION'] = redis://redis:6379/1`
   - Document both URLs in .env.backend.example

### Technical Considerations

**Performance:**
- Redis runs entirely in memory for maximum speed
- Named volume persists data to disk periodically (RDB snapshots)
- LRU eviction ensures cache doesn't exhaust memory

**Security:**
- Redis port 6379 NOT exposed to host network—only accessible internally
- No password authentication required for local development (internal network only)
- Production deployment must use Redis AUTH and TLS

**Scalability:**
- Single Redis instance sufficient for local development
- Configuration allows easy migration to Redis Cluster or Sentinel in production
- Connection pooling in backend prevents connection exhaustion

**Backward Compatibility:**
- Using latest Redis ensures compatibility with Celery 5+
- Redis protocol backward compatible with older clients

### Known Challenges

**Challenge:** Redis persistence may cause delays on shutdown
**Solution:** Use RDB snapshots (not AOF) for development; accept potential data loss on crash

**Challenge:** Memory limits may be hit with large task queues
**Solution:** Configure maxmemory with appropriate eviction policy; monitor Redis memory usage

**Challenge:** Debugging task queue state requires Redis CLI knowledge
**Solution:** Document common Redis CLI commands for viewing queues, keys, and task states

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)

### Blocks
- US-4: Django Backend API Service (requires Redis for caching)
- US-6: Celery Worker Service for AI Pipeline (requires Redis broker)
- US-7: Celery Beat Scheduler Service (requires Redis for schedule storage)

## Test Scenarios

### Happy Path
1. Developer runs `docker-compose up -d redis`
2. Redis container starts successfully
3. Health check passes within 5 seconds (PING returns PONG)
4. Developer connects from backend: `docker-compose exec redis redis-cli`
5. Redis CLI prompt appears
6. Developer runs `PING` command
7. Response: `PONG` confirms Redis is operational
8. Developer runs `INFO` to verify configuration

### Alternative Paths
1. Developer inspects task queues: `docker-compose exec redis redis-cli -n 0 KEYS *`
2. All Celery queue keys displayed (celery, celery.backend, etc.)
3. Developer inspects cache keys: `docker-compose exec redis redis-cli -n 1 KEYS *`
4. Cached data keys displayed separately from task queues

### Error Scenarios
1. **Connection refused:** Backend cannot reach Redis
   - Expected: Backend logs show "Connection refused to redis:6379"
   - Resolution: Verify Redis container is running and on same Docker network

2. **Memory limit exceeded:** Redis maxmemory reached
   - Expected: Redis evicts least recently used keys (LRU policy)
   - Cache misses increase but system remains functional

3. **Volume mount failure:** Docker cannot create volume
   - Expected: Container fails to start with clear error
   - Resolution: Check Docker Desktop storage settings

### Edge Cases
1. **Data persistence:** Developer runs `docker-compose down` then `docker-compose up`
   - Expected: Task queue data may be lost (ephemeral)
   - Cache data rebuilds automatically (acceptable for development)

2. **Concurrent access:** Multiple workers and backend processes connect simultaneously
   - Expected: Redis handles concurrent connections gracefully
   - Connection pooling prevents exhaustion

## UI/UX Specifications

Not applicable for Redis service.

## Security Considerations

- Redis port 6379 NOT exposed to host network—only accessible internally via Docker network
- No authentication required for local development (acceptable risk on isolated network)
- Production deployment MUST enable Redis AUTH and TLS encryption
- .env files document security recommendations for production

## Performance Requirements

- **Startup Time:** Redis healthy within 5 seconds (P95)
- **Cache Operations:** GET/SET operations < 5ms (P99)
- **Task Queue Operations:** LPUSH/RPOP operations < 10ms (P99)
- **Concurrent Connections:** Support minimum 100 connections
- **Memory Usage:** Limit to 256MB for development workload

## Accessibility Requirements

Not applicable for Redis service.

## Definition of Done

- [ ] Redis service defined in docker-compose.yml with all required configuration
- [ ] Named volume `redis_data` created and persisting data
- [ ] Health check configured and passing consistently
- [ ] Redis accessible from backend, worker, and scheduler containers
- [ ] Broker URL (DB 0) documented in .env.backend.example
- [ ] Cache URL (DB 1) documented in .env.backend.example
- [ ] Max memory policy (allkeys-lru) configured
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] Redis starts successfully with `docker-compose up redis`
- [ ] Redis CLI accessible for debugging verified
- [ ] PING health check responds correctly
- [ ] Documentation updated with Redis connection instructions
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
- [ ] Should we configure Redis persistence (RDB vs AOF) for local development?
- [ ] Do we need Redis Sentinel or Cluster configuration for local testing?

### Assumptions
- Single Redis instance sufficient for local development load
- Task queue data loss on crash is acceptable for development
- No authentication required for isolated local environment

### Out of Scope
- Redis Cluster or Sentinel configuration (single instance only)
- Advanced Redis configuration (pub/sub, streams)
- Redis monitoring and metrics (basic logs sufficient)
- Redis backup/restore automation

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-2: Database Service with Vector Support (complementary data store)
- US-4: Django Backend API Service (blocked by this)
- US-6: Celery Worker Service for AI Pipeline (blocked by this)
- US-7: Celery Beat Scheduler Service (blocked by this)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
