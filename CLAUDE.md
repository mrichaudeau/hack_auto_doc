# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-powered Technology Watch Platform** (Plateforme de Veille Technologique IA) designed to automate technology monitoring for professionals. The system uses complex AI agents (Langgraph) to collect, analyze, synthesize, and recommend technology content.

**Current Status**: This repository contains comprehensive project specifications and documentation. No implementation code exists yet - this is a planning/design phase repository.

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

### Planned Technology Stack

**Backend:**
- Python 3.11 with Django/Django REST Framework
- Celery + Celery Beat (async tasks & scheduling)
- Langgraph (AI agent orchestration)
- Redis (broker & cache)
- PostgreSQL 15 with pgvector extension

**Frontend:**
- React SPA (Node 20)

**Infrastructure:**
- Docker Compose for local development
- Firecrawl API for web scraping
- LLM APIs (OpenAI/Claude) for synthesis

## Development Workflow (Planned)

### Local Environment Setup

Based on `docs/setup/00_setup_local_docker.md`:

```bash
# 1. Clone and configure
git clone [URL_DU_REPO]
cd [NOM_DU_REPO]
cp env.backend.example .env.backend
cp env.frontend.example .env.frontend
# Edit .env files with API keys (LLM, Firecrawl)

# 2. Build and start services
docker-compose build
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

**Service URLs:**
- Frontend: http://localhost:3000
- API Backend: http://localhost:8000/api/
- Admin Interface (FinOps): http://localhost:8000/admin/

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

The recommended implementation sequence (from `docs/action_plan/Backlog_Global.md`):

1. **Bloc 1: Authentication** - Foundation for security
2. **Bloc 2: Subscription Management** - Defines user demand
3. **Bloc 3: AI Pipeline (Basic)** - Core value creation
4. **Bloc 4: Report Consultation** - Delivers value to users
5. **Bloc 5: Recommendation Engine** - Requires embeddings from Bloc 3
6. **Bloc 6: FinOps Tracking** - Administrative requirement
7. **Bloc 3: AI Pipeline (Advanced)** - Verification loop & resilience

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

- `docs/00_context_project.md` - Project mission and functional pillars
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

## Important Implementation Notes

### Security Requirements
- Password hashing: Argon2 or PBKDF2
- JWT tokens for API authentication
- All authenticated endpoints require valid JWT
- Admin dashboard (FinOps) restricted to admin role
- Report access enforced by subscription (403 for non-subscribers)

### Performance Targets
- Auth endpoint response: < 300ms (P95)
- Pipeline execution: < 5 minutes per subject
- Recommendation query: < 500ms
- Cost logging overhead: < 50ms

### Distributed System Concerns
- Redis-based distributed locking for subject processing
- Celery retry logic (3 attempts) for API failures
- Async profile updates on subscription changes
- Celery Beat for daily recurring scraping tasks
- Refer to @docs\00_choix_technologique.md when making technological assumption.
- Never use emojy in logs or print, only utf-8 encoded characters