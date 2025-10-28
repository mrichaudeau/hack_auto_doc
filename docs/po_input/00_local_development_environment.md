# Local Development Environment

## Overview / Context

The Local Development Environment provides a complete, Docker-based development stack that enables developers to run the entire AI-powered Technology Watch Platform locally. This foundational infrastructure is critical for development, testing, and debugging before deployment to production environments.

The environment orchestrates 6 containerized services (database, cache, API backend, frontend SPA, async workers, and task scheduler) using Docker Compose, ensuring consistency across developer machines and eliminating "works on my machine" issues.

**Business Value:**
- Reduces onboarding time for new developers (from days to hours)
- Ensures development environment parity with production
- Enables isolated testing of complex AI pipelines
- Supports rapid iteration and debugging

## Functional Requirements

The local development environment must provide:

1. **Complete Service Orchestration**: All 6 microservices (database, Redis, backend API, frontend, Celery worker, Celery Beat scheduler) running in isolated Docker containers
2. **One-Command Setup**: Simple `docker-compose up` command to start the entire stack
3. **Persistent Data**: Database and Redis data persisted across container restarts
4. **Hot Reloading**: Live code reloading for both backend (Django) and frontend (React) during development
5. **Service Health Checks**: Automatic validation that all services are running and accessible
6. **Environment Configuration**: Secure management of API keys, secrets, and configuration via environment files
7. **Database Initialization**: Automated schema migrations and pgvector extension setup
8. **Admin Access**: Pre-configured superuser creation for Django Admin and FinOps dashboard

## User Stories

### US-1: Docker Compose Service Orchestration
**As a** developer
**I want to** start all required services with a single command
**So that** I can quickly spin up the complete development environment

**Acceptance Criteria:**
- [ ] `docker-compose.yml` defines all 6 services: db, redis, backend, frontend, worker, scheduler
- [ ] `docker-compose build` successfully builds all container images
- [ ] `docker-compose up -d` starts all services in detached mode
- [ ] `docker-compose ps` shows all services as "running" (healthy status)
- [ ] `docker-compose down` stops and removes all containers cleanly
- [ ] Services start in correct dependency order (db/redis before backend/worker)
- [ ] Service logs accessible via `docker-compose logs [service_name]`
- [ ] All services restart automatically on failure

**Priority:** P0

**Technical Notes:**
- PostgreSQL 15 with pgvector extension for database
- Redis latest for message broker and cache
- Python 3.13 base image for backend/worker/scheduler
- Node 20 base image for frontend
- Use Docker health checks for service readiness

### US-2: Database Service with Vector Support
**As a** developer
**I want** a PostgreSQL database with pgvector extension pre-configured
**So that** I can develop and test semantic search features locally

**Acceptance Criteria:**
- [ ] PostgreSQL 15 container runs on port 5432
- [ ] pgvector extension is enabled automatically
- [ ] Database credentials configured via environment variables
- [ ] Database data persists in named Docker volume
- [ ] Database accessible from backend, worker, and scheduler containers
- [ ] Database connection pool configured for concurrent access
- [ ] Health check validates database connectivity

**Priority:** P0

**Technical Notes:**
- Use Supabase PostgreSQL image or official postgres:15 with pgvector
- Named volume: `postgres_data`
- Default database name: `veille_tech_db`
- Connection string format: `postgresql://user:password@db:5432/veille_tech_db`

### US-3: Redis Broker and Cache Service
**As a** developer
**I want** Redis configured as both Celery broker and application cache
**So that** I can test async task processing and caching locally

**Acceptance Criteria:**
- [ ] Redis latest container runs on port 6379
- [ ] Redis accessible from backend, worker, and scheduler containers
- [ ] Redis data persists in named Docker volume
- [ ] Celery broker URL configured: `redis://redis:6379/0`
- [ ] Cache backend configured: `redis://redis:6379/1`
- [ ] Redis connection validated with health check
- [ ] Redis CLI accessible via `docker-compose exec redis redis-cli`

**Priority:** P0

**Technical Notes:**
- Use official `redis:latest` image
- Named volume: `redis_data`
- Separate Redis databases for broker (0) and cache (1)
- Max memory policy: `allkeys-lru`

### US-4: Django Backend API Service
**As a** developer
**I want** the Django/DRF backend API running with hot reload
**So that** I can develop and test API endpoints without rebuilding containers

**Acceptance Criteria:**
- [ ] Django development server runs on port 8000
- [ ] API accessible at `http://localhost:8000/api/`
- [ ] Django Admin accessible at `http://localhost:8000/admin/`
- [ ] Code changes trigger automatic reload (no container restart needed)
- [ ] Backend connects successfully to PostgreSQL and Redis
- [ ] Static files served correctly for admin interface
- [ ] Environment variables loaded from `.env.backend`
- [ ] Python dependencies installed via Poetry
- [ ] Container logs show startup messages and request logs

**Priority:** P0

**Technical Notes:**
- Base image: `python:3.13-slim`
- Use Poetry 2.2.1 for dependency management
- Mount source code as volume for hot reload
- Django settings: `DEBUG=True`, `ALLOWED_HOSTS=*`
- Command: `python manage.py runserver 0.0.0.0:8000`

### US-5: React Frontend SPA Service
**As a** developer
**I want** the React frontend running with hot module replacement
**So that** I can see UI changes instantly without manual refresh

**Acceptance Criteria:**
- [ ] React development server runs on port 3000
- [ ] Application accessible at `http://localhost:3000`
- [ ] Code changes trigger instant hot module replacement
- [ ] API proxy configured to forward requests to backend:8000
- [ ] Environment variables loaded from `.env.frontend`
- [ ] Node modules installed automatically on container start
- [ ] Build errors displayed in browser overlay
- [ ] Source maps enabled for debugging

**Priority:** P0

**Technical Notes:**
- Base image: `node:20-alpine`
- Use Vite or Create React App for dev server
- Mount source code as volume for HMR
- Proxy API requests to `http://backend:8000`
- Environment variable: `REACT_APP_API_URL=http://localhost:8000`

### US-6: Celery Worker Service for AI Pipeline
**As a** developer
**I want** Celery workers running to execute AI pipeline tasks
**So that** I can test Langgraph agents and async processing locally

**Acceptance Criteria:**
- [ ] Celery worker container shares backend codebase
- [ ] Worker connects to Redis broker successfully
- [ ] Worker processes tasks from all registered queues
- [ ] Worker logs show task execution details
- [ ] Worker auto-reloads on code changes (watchdog enabled)
- [ ] Worker has access to LLM API keys from environment
- [ ] Worker can access Firecrawl API for scraping
- [ ] Failed tasks retry according to configured policy

**Priority:** P0

**Technical Notes:**
- Inherits from backend service (same Dockerfile)
- Command: `celery -A veille_tech worker --loglevel=info --watchdog`
- Environment variables for API keys: `GOOGLE_AI_API_KEY`, `FIRECRAWL_API_KEY`
- Concurrency: 4 worker processes for local development

### US-7: Celery Beat Scheduler Service
**As a** developer
**I want** Celery Beat scheduler running for recurring tasks
**So that** I can test daily scraping schedules locally

**Acceptance Criteria:**
- [ ] Celery Beat container shares backend codebase
- [ ] Scheduler connects to Redis broker successfully
- [ ] Scheduled tasks execute at configured intervals
- [ ] Scheduler logs show task dispatch messages
- [ ] Scheduler persists schedule state to avoid duplicates
- [ ] Scheduler can be stopped/started without task loss
- [ ] Default schedule configured for daily scraping at 2 AM

**Priority:** P1

**Technical Notes:**
- Inherits from backend service (same Dockerfile)
- Command: `celery -A veille_tech beat --loglevel=info`
- Use Redis as Celery Beat scheduler backend (django-celery-beat)
- Schedule stored in database for persistence

### US-8: Environment Configuration Management
**As a** developer
**I want** secure management of API keys and configuration
**So that** I can run the application without exposing secrets in code

**Acceptance Criteria:**
- [ ] Example files provided: `env.backend.example`, `env.frontend.example`
- [ ] Setup instructions guide copying examples to `.env.backend`, `.env.frontend`
- [ ] Backend `.env` includes: database URL, Redis URL, JWT secret, LLM API keys
- [ ] Frontend `.env` includes: API URL, environment mode
- [ ] Actual `.env` files excluded from version control (.gitignore)
- [ ] Services load environment variables correctly
- [ ] Missing required variables cause clear error messages
- [ ] Documentation lists all required and optional variables

**Priority:** P0

**Technical Notes:**
- Use `python-decouple` or `django-environ` for backend
- Use `.env` files with `dotenv` for frontend
- Required backend vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GOOGLE_AI_API_KEY`, `FIRECRAWL_API_KEY`
- Required frontend vars: `VITE_API_URL` or `REACT_APP_API_URL`

### US-9: Database Initialization and Migrations
**As a** developer
**I want** automated database schema setup on first run
**So that** I can start development without manual SQL commands

**Acceptance Criteria:**
- [ ] Django migrations run automatically via documented command
- [ ] pgvector extension enabled in PostgreSQL
- [ ] All model tables created correctly
- [ ] Initial data fixtures loaded (if any)
- [ ] Migration history tracked in database
- [ ] Command: `docker-compose exec backend python manage.py migrate`
- [ ] Migration failures display clear error messages
- [ ] Subsequent migrations can be applied incrementally

**Priority:** P0

**Technical Notes:**
- Migrations located in `backend/apps/*/migrations/`
- Enable pgvector: `CREATE EXTENSION IF NOT EXISTS vector;`
- Consider Django management command for one-time setup
- Use `--check` flag to verify migrations without applying

### US-10: Superuser Creation for Admin Access
**As a** developer
**I want** to create an admin account for Django Admin
**So that** I can access the FinOps dashboard and manage data

**Acceptance Criteria:**
- [ ] Command provided: `docker-compose exec backend python manage.py createsuperuser`
- [ ] Interactive prompt for username, email, password
- [ ] Password validation enforces security rules (min 8 chars, complexity)
- [ ] Superuser can log in to `http://localhost:8000/admin/`
- [ ] Superuser has access to all Django Admin features
- [ ] Superuser can view FinOps cost tracking dashboard
- [ ] Non-interactive creation supported for CI/CD (optional)

**Priority:** P1

**Technical Notes:**
- Use Django's built-in `createsuperuser` command
- Admin accessible via `django.contrib.admin`
- For automated setup, use `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` env vars

### US-11: Service Health Monitoring and Logs
**As a** developer
**I want** visibility into service health and logs
**So that** I can quickly diagnose issues during development

**Acceptance Criteria:**
- [ ] `docker-compose ps` shows status of all services
- [ ] Each service has health check configured (where applicable)
- [ ] `docker-compose logs [service]` displays service-specific logs
- [ ] `docker-compose logs -f` follows logs in real-time
- [ ] Error logs clearly indicate source service
- [ ] Startup logs confirm successful initialization
- [ ] Request/response logs available for debugging
- [ ] Log format includes timestamps and severity levels

**Priority:** P1

**Technical Notes:**
- Health checks: HTTP endpoint for backend, Redis PING, PostgreSQL `pg_isready`
- Log drivers: default JSON file driver
- Consider structured logging (JSON) for easier parsing
- Log rotation configured to prevent disk fill

### US-12: Development Workflow Documentation
**As a** new developer
**I want** clear setup instructions and common commands
**So that** I can onboard and start contributing quickly

**Acceptance Criteria:**
- [ ] README or setup guide includes all prerequisites (Git, Docker Desktop)
- [ ] Step-by-step instructions for first-time setup
- [ ] Common commands documented: build, up, down, logs, exec
- [ ] Troubleshooting section for known issues
- [ ] Architecture diagram showing service relationships
- [ ] Port mapping table (service -> localhost port)
- [ ] Instructions for accessing each service (URLs)
- [ ] Commands for running tests, linting, migrations

**Priority:** P1

**Technical Notes:**
- Documentation located at `docs/setup/00_setup_local_docker.md`
- Include examples of common development tasks
- Provide tips for Docker Desktop memory/CPU allocation
- Link to external resources for Docker Compose basics

## Non-Functional Requirements

### Performance
- All services start within 60 seconds on modern hardware (8GB RAM, 4 CPU cores)
- Database queries respond within 100ms for common operations
- Hot reload triggers within 2 seconds of code changes
- API endpoint response time < 500ms in development mode

### Reliability
- Services automatically restart on crash (Docker restart policy: `unless-stopped`)
- Data persists across container restarts (volumes for db and redis)
- No data loss on clean shutdown (`docker-compose down`)
- Health checks detect and report unhealthy services

### Scalability
- Configuration supports horizontal scaling (multiple worker instances)
- Resource limits defined to prevent single service hogging resources
- Worker concurrency configurable via environment variables

### Security
- Secrets managed via environment files, never committed to Git
- Default credentials documented but changeable
- Database and Redis not exposed to host network (only internal Docker network)
- JWT secrets randomized per developer environment

### Developer Experience
- One-command setup for new developers
- Clear error messages for common configuration issues
- Consistent behavior across Windows, Mac, Linux
- Minimal resource usage when idle (< 2GB RAM)

## Technical Constraints

**Backend:**
- Django 4.2+ with Django REST Framework
- Python 3.13 (official base image)
- Poetry 2.2.1 for dependency management
- Celery 5+ for async tasks
- PostgreSQL 15 with pgvector extension

**Frontend:**
- React 18+ (SPA architecture)
- Node 20 LTS
- Vite or Create React App for development server
- TypeScript recommended but optional

**Infrastructure:**
- Docker Engine 24+ or Docker Desktop 4.25+
- Docker Compose v2 (integrated with Docker CLI)
- Minimum 8GB RAM, 4 CPU cores recommended
- 10GB free disk space for images and volumes

**AI/ML Stack:**
- Langgraph for agent orchestration
- Google AI Studio (Gemini 2.5 Flash/Pro models)
- Firecrawl API for web scraping
- text-embedding-004 for vector embeddings

**Authentication:**
- django-allauth for standard auth
- django-azure-auth / MSAL-React for Microsoft SSO
- djangorestframework-simplejwt for JWT tokens
- Argon2 for password hashing

## Dependencies

**External Services:**
- Google AI Studio API (Gemini models) - requires API key
- Firecrawl API - requires API key
- Microsoft Azure AD tenant (for SSO, optional in local dev)
- SMTP server (for email, can be mocked locally)

**Infrastructure:**
- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git for version control
- Code editor with Docker extension (VSCode recommended)

**Network Requirements:**
- Internet access for pulling Docker images
- Access to Docker Hub, PyPI, NPM registries
- Access to AI API endpoints (Google, Firecrawl)

## Success Metrics

- New developer can start environment within 30 minutes (including Docker installation)
- Zero "works on my machine" issues in team standup meetings
- 95% of API endpoints testable locally without external dependencies
- Hot reload reduces development feedback loop to < 5 seconds
- All integration tests pass in local environment before CI/CD

## Known Limitations

- AI API calls require internet and valid API keys (cannot be fully mocked)
- Firecrawl scraping limited to API quotas (may need mock responses for heavy testing)
- Microsoft SSO requires Azure AD configuration (can be skipped for local auth testing)
- pgvector performance differs from production (smaller dataset, no indexing optimizations)
- Celery Beat scheduler may drift slightly in development mode

## Future Enhancements (Out of Scope)

- Docker Compose profiles for selective service startup (e.g., frontend-only mode)
- Integration with VSCode Dev Containers for consistent IDE setup
- Pre-built Docker images in registry to skip local builds
- Mock services for AI APIs to enable offline development
- Automated backup/restore scripts for local database
