# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered Technology Watch Platform** (Plateforme de Veille Technologique IA) designed to automate technology monitoring for professionals. The system uses complex AI agents (Langgraph) to collect, analyze, synthesize, and recommend technology content.

**Current Status**: Transitioning from planning phase to implementation. Infrastructure foundation (Docker environment) is in progress.

## Architecture Overview

The planned system follows a microservices architecture with 6 functional pillars:

### Core Components

1. **Authentication & Authorization** (Bloc 1)
   - Dual authentication: Standard (email/password) + Microsoft Entra ID (SSO)
   - Account unification logic for same-email scenarios
   - JWT-based API security

2. **Subject & Subscription Management** (Bloc 2)
   - Admin-defined monitoring subjects
   - User subscription system that triggers content generation
   - Bootstrap mechanism for immediate report generation on new subscriptions

3. **AI Content Pipeline** (Bloc 3)
   - **Langgraph-based agent orchestration** (stateful graph)
   - **Agent workflow**: Collection → Relevance → Synthesis → Verification → Indexation
   - **Firecrawl** for web scraping (handles JavaScript-heavy sites)
   - Celery workers for async execution
   - Redis distributed locking to prevent concurrent processing of same subject
   - pgvector for semantic embeddings storage

4. **Report Consultation** (Bloc 4)
   - Personalized dashboard showing latest reports for subscribed subjects
   - Full historical access with pagination and filtering
   - Permission-based access control (403 for non-subscribed content)

5. **Recommendation Engine** (Bloc 5)
   - Semantic user profiling based on subscription embeddings
   - pgvector cosine similarity search
   - Suggests new subjects not yet subscribed
   - ANN indexing (HNSW or IVFFlat) for performance

6. **FinOps Cost Tracking** (Bloc 6)
   - Custom Langgraph callback handler capturing LLM token usage
   - Real-time cost calculation (USD) per API call
   - Django Admin dashboard with aggregation and filtering
   - CSV export for budget analysis

## Technology Versions

**Current Stack (from docs/00_choix_technologique.md):**

**Backend:**
- Python: 3.13
- Poetry: 2.2.1
- Django: Latest (via Poetry)
- Django REST Framework: Latest
- Celery + Celery Beat: Latest
- Langgraph: Latest (AI agent orchestration)

**Database & Cache:**
- PostgreSQL: 15 with pgvector extension
- Redis: Latest (7+)

**Frontend:**
- Node.js: 20
- React: Latest (SPA)
- Vite: Latest (dev server with HMR)

**AI/ML Services:**
- Google AI Studio:
  - `gemini-2.5-flash` (workhorse for synthesis/relevance)
  - `gemini-2.5-pro` (verification/quality checking)
  - `text-embedding-004` (embeddings)
- Firecrawl API (web scraping)

**Infrastructure:**
- Docker Engine: 24.0+ / Docker Desktop: 4.25+
- Docker Compose: v2 (file version 3.8)

## Current Implementation State

**Status: Planning Phase → Early Implementation**

### Completed:
- ✅ Functional specifications parsed and structured
- ✅ User Stories generated for: authentication (13), subscriptions (7), local-dev-environment (12)
- ✅ Task breakdown for local-development-environment/US-1 (23 tasks, 52h effort)
- ✅ Generated capability skills: docker-compose-orchestration, dockerfile-development, environment-configuration, service-integration-testing
- ✅ Generated infrastructure-agent for orchestrating Docker tasks
- ✅ Git branch created: feature/US-1-docker-compose-orchestration

### In Progress:
- 🔄 US-1: Docker Compose Service Orchestration (23 tasks pending)
  - Branch: feature/US-1-docker-compose-orchestration
  - See `.impl-state.json` for detailed task status

### Not Started:
- ❌ Authentication implementation (Bloc 1) - 13 User Stories
- ❌ Subscriptions implementation (Bloc 2) - 7 User Stories
- ❌ AI Pipeline implementation (Bloc 3)
- ❌ Reports UI (Bloc 4)
- ❌ Recommendations Engine (Bloc 5)
- ❌ FinOps Tracking (Bloc 6)

## Common Commands

### Specification Management Commands

```bash
# Specification Planning Workflow
/spec-help                                      # Interactive guide
/spec-parse <po-input-file>                     # Convert PO doc to structured specs
/spec-generate-tasks <feature>/<user-story>     # Generate development tasks
/spec-create-issues <feature>/<user-story>      # Create GitHub issues
/spec-full-pipeline <po-input-file>             # Complete workflow

# Implementation Workflow
/impl-init <feature>/<user-story>               # Initialize implementation
/impl-task <task-id>                            # Implement specific task
/impl-us <feature>/<user-story>                 # Implement entire User Story
/impl-status [<feature>/<user-story>]           # Check progress
/impl-resume <feature>/<user-story>             # Resume interrupted work
```

### Docker Commands (Once Implemented)

```bash
# Build and start all services
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Specific service

# Execute commands in containers
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py test
docker-compose exec backend pytest
docker-compose exec backend celery -A config worker -l info

# Frontend commands
docker-compose exec frontend npm test
docker-compose exec frontend npm run build

# Database operations
docker-compose exec db psql -U postgres -d postgres
docker-compose exec redis redis-cli

# Stop and clean up
docker-compose down                 # Stop services
docker-compose down -v              # Stop and remove volumes

# Rebuild after dependency changes
docker-compose build --no-cache backend
docker-compose up -d --force-recreate backend
```

### Testing Commands (Planned)

```bash
# Backend tests
docker-compose exec backend pytest
docker-compose exec backend pytest -v tests/accounts/
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm test
docker-compose exec frontend npm run test:watch
docker-compose exec frontend npm run test:e2e

# Integration tests
docker-compose exec backend python manage.py test --tag=integration

# Code quality
docker-compose exec backend black .
docker-compose exec backend flake8
docker-compose exec frontend npm run lint
```

## Development Workflow

### Local Environment Setup (Planned)

Based on `docs/setup/00_setup_local_docker.md`:

```bash
# 1. Clone and configure
git clone [URL_DU_REPO]
cd [NOM_DU_REPO]
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
# Edit .env files with API keys (LLM, Firecrawl)

# 2. Build and start services
docker-compose build
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# 4. Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

**Service URLs:**
- Frontend: http://localhost:3000
- API Backend: http://localhost:8000/api/
- Admin Interface (FinOps): http://localhost:8000/admin/

**Hardware Requirements:**
- Minimum: 8GB RAM, 4 CPU cores, 10GB disk space
- Recommended: 16GB RAM, 8 CPU cores, 20GB disk space, SSD

### Docker Services

| Service | Purpose | Port |
|---------|---------|------|
| `db` | PostgreSQL 15 + pgvector | 5432 |
| `redis` | Celery broker & cache | 6379 |
| `backend` | Django/DRF API | 8000 |
| `frontend` | React SPA | 3000 |
| `worker` | Celery worker (AI pipeline) | - |
| `scheduler` | Celery Beat (recurring tasks) | - |

## Development Priority Order

The recommended implementation sequence:

1. **Local Development Environment** (In Progress) - Docker infrastructure
2. **Bloc 1: Authentication** - Foundation for security
3. **Bloc 2: Subscription Management** - Defines user demand
4. **Bloc 3: AI Pipeline (Basic)** - Core value creation
5. **Bloc 4: Report Consultation** - Delivers value to users
6. **Bloc 5: Recommendation Engine** - Requires embeddings from Bloc 3
7. **Bloc 6: FinOps Tracking** - Administrative requirement
8. **Bloc 3: AI Pipeline (Advanced)** - Verification loop & resilience

## Generated Agents and Skills

This project uses **role-based agents and capability skills** for implementation tasks. Agents are organized by technical role (Backend, Frontend, Testing, etc.) rather than by User Story, making them highly reusable across all features.

### Active Agents (7 Role-Based Agents)

#### 1. **backend-agent**
- **Purpose**: Django/Python backend development, REST APIs, Celery tasks, database operations, authentication
- **Location**: `.claude/spec-implementer-generated/agents/backend-agent.md`
- **Responsibilities**: Django models/views/serializers, REST API endpoints, Celery configuration, database migrations, Django Admin, security implementation
- **Primary Skills**: backend-django-configuration, celery-worker-configuration, django-migrations-development, database-administration, django-admin-operations, api-development, security-implementation
- **Reusability**: High - works for any backend feature or User Story

#### 2. **frontend-agent**
- **Purpose**: React/Vite frontend development, UI/UX, state management, API integration, frontend infrastructure
- **Location**: `.claude/spec-implementer-generated/agents/frontend-agent.md`
- **Responsibilities**: React components, Vite configuration, state management (Context/Redux), routing, API client, HMR setup, frontend Docker configuration
- **Primary Skills**: frontend-react-vite-development, docker-compose-orchestration, environment-configuration
- **Reusability**: High - works for any frontend feature or User Story

#### 3. **iac-agent** (NEW)
- **Purpose**: Infrastructure as Code (Terraform, CloudFormation), cloud infrastructure provisioning
- **Location**: `.claude/spec-implementer-generated/agents/iac-agent.md`
- **Responsibilities**: Terraform configurations, AWS/Azure/GCP resource provisioning, state management, VPC/RDS/S3 setup
- **Primary Skills**: terraform-configuration, cloudformation-templates
- **Reusability**: High - works for any cloud infrastructure need
- **Note**: This is a NEW capability - project previously had no IaC support

#### 4. **unit-tester-agent**
- **Purpose**: Unit testing with mocks, isolated component testing, test coverage
- **Location**: `.claude/spec-implementer-generated/agents/unit-tester-agent.md`
- **Responsibilities**: pytest unit tests (backend), Vitest/Jest tests (frontend), mocking external dependencies, test fixtures, coverage analysis
- **Primary Skills**: django-testing, frontend-unit-testing
- **Reusability**: High - works for any module or component
- **Boundary**: Unit Tester = isolated tests with mocks, Integration Tester = multi-service tests

#### 5. **integration-tester-agent**
- **Purpose**: End-to-end workflows, multi-service integration testing, Docker Compose testing
- **Location**: `.claude/spec-implementer-generated/agents/integration-tester-agent.md`
- **Responsibilities**: E2E workflow tests, Docker stack testing, API integration tests, database integration tests, Celery task integration tests
- **Primary Skills**: integration-testing, django-testing, service-integration-testing
- **Reusability**: High - works for any workflow or integration scenario
- **Boundary**: Integration Tester = tests with real services (DB, Redis, Docker), Unit Tester = isolated tests

#### 6. **dockerizer-agent**
- **Purpose**: Docker and container orchestration, Dockerfiles, Docker Compose, container infrastructure
- **Location**: `.claude/spec-implementer-generated/agents/dockerizer-agent.md`
- **Responsibilities**: docker-compose.yml configuration, Dockerfile creation/optimization, container networking, volume management, health checks, environment configuration
- **Primary Skills**: docker-compose-orchestration, dockerfile-development, environment-configuration, service-integration-testing
- **Reusability**: High - works for any Docker/container infrastructure need
- **Boundary**: Dockerizer = containers/orchestration, Backend Agent = Django/Celery app config, IAC Agent = cloud infrastructure

#### 7. **documentation-agent**
- **Purpose**: Technical documentation, setup guides, API docs, troubleshooting guides
- **Location**: `.claude/spec-implementer-generated/agents/documentation-agent-new.md`
- **Responsibilities**: Developer documentation, setup guides, API documentation, troubleshooting guides, README updates, CLAUDE.md maintenance
- **Primary Skills**: developer-documentation, environment-configuration
- **Reusability**: High - works for any feature or project area

### Agent Selection Guide

**Use this guide to choose the right agent:**

| Task Type | Agent to Use | Why |
|-----------|-------------|-----|
| Django models/views/APIs | Backend Agent | Backend application logic |
| React components/UI | Frontend Agent | Frontend application logic |
| Terraform/CloudFormation | IAC Agent | Cloud infrastructure provisioning |
| Unit tests (isolated) | Unit Tester Agent | Isolated tests with mocks |
| Integration tests (E2E) | Integration Tester Agent | Multi-service workflows |
| Dockerfiles/docker-compose.yml | Dockerizer Agent | Container infrastructure |
| Documentation/guides | Documentation Agent | Technical writing |

### Active Skills

**Infrastructure & Container Skills:**
- **docker-compose-orchestration**: Multi-service orchestration, networking, health checks
- **dockerfile-development**: Dockerfile creation, multi-stage builds, optimization
- **environment-configuration**: .env files, .dockerignore, .gitignore, config docs
- **service-integration-testing**: Docker stack testing, health check validation

**Backend Skills:**
- **backend-django-configuration**: Django settings, Poetry, cache, Redis integration
- **celery-worker-configuration**: Celery app, broker/result backend, retry policies
- **django-migrations-development**: Django apps, migrations, management commands
- **database-administration**: PostgreSQL, pgvector, privileges, query execution
- **django-admin-operations**: Django Admin setup, superuser creation, ModelAdmin
- **api-development**: REST API endpoints, serializers, authentication
- **security-implementation**: Rate limiting, JWT, password hashing, security logging

**Frontend Skills:**
- **frontend-react-vite-development**: React components, Vite config, HMR, API proxy

**Infrastructure as Code Skills:**
- **terraform-configuration**: Terraform HCL, providers, resources, state management

**Testing Skills:**
- **django-testing**: Django test patterns, pytest-django, fixtures, assertions
- **integration-testing**: E2E workflows, multi-service testing, Docker integration

**Documentation Skills:**
- **developer-documentation**: Setup guides, API docs, troubleshooting guides

## Key Architectural Patterns

### Langgraph Agent Flow

The AI pipeline uses a stateful graph with conditional routing:
- **Collection Agent** scrapes via Firecrawl
- **Relevance Agent** filters for quality/novelty
- **Synthesis Agent** generates structured reports
- **Verification Agent** validates quality (can loop back to Synthesis)
- **Indexation Agent** creates vector embeddings

### Vector Search Strategy

- **Report embeddings**: Stored in pgvector for each generated report
- **User profile vector**: Average of all subscribed subjects' report embeddings
- **Subject representative vector**: Average of all reports for that subject
- **Recommendation**: Cosine similarity search excluding subscribed subjects

### Cost Tracking Integration

- Custom Langgraph callback handler intercepts `on_llm_end` events
- Captures: model name, input tokens, output tokens
- Calculates cost using configured unit rates
- Links to subject for granular analysis

## Documentation Structure

### Original Specifications (French)
- `docs/00_context_project.md` - Project mission and functional pillars
- `docs/00_choix_technologique.md` - Technology stack decisions and rationale
- `docs/01_Authentification_Autorisation.md` - Auth specs (Bloc 1)
- `docs/02_Gestion_Sujets_Abonnements.md` - Subscription specs (Bloc 2)
- `docs/03_Pipeline_Contenu_IA.md` - AI pipeline specs (Bloc 3)
- `docs/04_Consultation_Rapports.md` - Report viewing specs (Bloc 4)
- `docs/05_Moteur_Recommandation.md` - Recommendation specs (Bloc 5)
- `docs/06_Suivi_FinOps.md` - Cost tracking specs (Bloc 6)
- `docs/action_plan/Backlog_Global.md` - Complete user story backlog
- `docs/setup/00_setup_local_docker.md` - Local development setup

Each functional bloc document follows the structure:
1. **Documentation Fonctionnelle** (Product vision)
2. **Exigences** (Functional & non-functional requirements)
3. **Plan d'Action** (User stories with acceptance criteria)

### Structured Specifications (English)

This project uses the **Functional Spec Planner Plugin** to convert PO documentation into structured, implementation-ready specifications. See `README-SPECS.md` for complete workflow documentation.

**Workflow:**
```
PO Input (docs/po_input/*.md)
  ↓ /spec-parse
Feature Spec (specs/<feature>/feature.md)
  + User Stories (specs/<feature>/US-*/user-story.md)
  ↓ /spec-generate-tasks
Development Tasks (specs/<feature>/US-*/tasks.md)
  ↓ /spec-create-issues
GitHub Issues (automated tracking)
  ↓ /impl-init
Implementation State (.impl-state.json)
  ↓ /impl-task or /impl-us
Automated Implementation
```

**Generated Specifications:**
- `specs/local-development-environment/` - 12 User Stories for Docker environment
  - `US-1/tasks.md` - 23 infrastructure tasks (52h effort, 4 phases)
  - `US-2/tasks.md` - Backend Dockerfile and Poetry setup tasks
- `specs/authentication/` - 13 User Stories for authentication/authorization
  - Tasks pending generation
- `specs/subscriptions/` - 7 User Stories for subject/subscription management
  - Tasks pending generation

**Key Files:**
- `.impl-state.json` - Tracks implementation progress, task statuses, generated agents/skills
- `README-SPECS.md` - Complete workflow documentation for spec management

## Important Implementation Notes

### Security Requirements
- Password hashing: Argon2 or PBKDF2
- JWT tokens for API authentication
- All authenticated endpoints require valid JWT
- Admin dashboard (FinOps) restricted to admin role
- Report access enforced by subscription (403 for non-subscribers)
- Never expose database or Redis ports (5432, 6379) in production
- All secrets in .env files, never in code or docker-compose.yml
- Run containers as non-root users (backend: appuser, frontend: node)

### Performance Targets
- Auth endpoint response: < 300ms (P95)
- Pipeline execution: < 5 minutes per subject
- Recommendation query: < 500ms
- Cost logging overhead: < 50ms
- Docker stack startup: < 60 seconds (all services healthy)

### Distributed System Concerns
- Redis-based distributed locking for subject processing
- Celery retry logic (3 attempts) for API failures
- Async profile updates on subscription changes
- Celery Beat for daily recurring scraping tasks

### Development Best Practices
- **Always refer to** `docs/00_choix_technologique.md` when making technological assumptions
- **Never use emojis** in logs or print statements, only UTF-8 encoded characters
- **Always check for skills** to apply first before implementing manually
- **Always check for subagents** to delegate work to specialized agents
- **Always force subagents** to use skills if available and matching tasks
- **Always prefer parallelization** when possible to maximize efficiency
- **Use Docker best practices**: Multi-stage builds, layer caching, .dockerignore, non-root users
- **Hot reloading**: Django runserver for backend, Vite HMR for frontend
- **Health checks**: All services must implement health checks for orchestration

### Docker Development Patterns
- **Named volumes** for data persistence (postgres_data, redis_data)
- **Bind mounts** for source code hot reloading (./backend:/app, ./frontend:/app)
- **Health checks** with service_healthy conditions for startup ordering
- **Resource limits** to prevent runaway containers (6GB total for 8GB system)
- **Restart policy**: unless-stopped (auto-restart on failure)
- **Multi-stage builds** for smaller final images (40-60% reduction)

### Cross-Platform Considerations
- **Windows**: Use Docker Desktop with WSL2 backend (not Hyper-V)
- **macOS M1/M2**: Add `platform: linux/amd64` if ARM-specific issues occur
- **Linux**: Test on Ubuntu and Debian distributions
- **File watching**: Use CHOKIDAR_USEPOLLING=true for Vite on Windows/Mac
- **Vite configuration**: host: '0.0.0.0' for external access from host
