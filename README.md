# AI-Powered Technology Watch Platform

An intelligent platform for automating technology monitoring and generating personalized reports using AI agents (Langgraph) and semantic search.

## Overview

The **Technology Watch Platform** (Plateforme de Veille Technologique IA) helps professionals stay updated with emerging technologies through:

- **AI-powered content collection** using Langgraph agents and Firecrawl web scraping
- **Semantic analysis** with Google Gemini models and vector embeddings
- **Personalized recommendations** using pgvector cosine similarity search
- **Automated report generation** with quality verification loops
- **Cost tracking** for FinOps monitoring via Django Admin

## Architecture

### Technology Stack

**Backend:**
- Python 3.13
- Django 4.2+ / Django REST Framework
- Celery + Celery Beat (async task processing)
- Langgraph (AI agent orchestration)
- Poetry 2.2.1 (dependency management)

**Database & Cache:**
- PostgreSQL 15 with pgvector extension
- Redis 7+ (broker and cache)

**Frontend:**
- Node.js 20
- React 18+ (SPA)
- Vite (dev server with HMR)

**AI/ML Services:**
- Google AI Studio: Gemini 2.5 Flash/Pro, text-embedding-004
- Firecrawl API (web scraping)

**Infrastructure:**
- Docker Engine 24.0+ / Docker Desktop 4.25+
- Docker Compose v2

### Services (Docker Compose)

| Service | Purpose | Port | Image |
|---------|---------|------|-------|
| `db` | PostgreSQL + pgvector | 5432 (internal) | pgvector/pgvector:pg15 |
| `redis` | Celery broker & cache | 6379 | redis:latest |
| `backend` | Django API | 8000 | python:3.13 |
| `frontend` | React SPA | 3000 | node:20 |
| `worker` | Celery worker (AI pipeline) | - | python:3.13 |
| `scheduler` | Celery Beat (recurring tasks) | - | python:3.13 |

## Features

### ✅ User Registration (US-1: Standard User Registration)

Complete user registration system with email-based authentication:

**Frontend:**
- React-based registration form with real-time validation
- Password strength indicator with visual feedback
- Responsive design for all devices
- Accessible UI with ARIA attributes

**Backend:**
- Django REST API with comprehensive validation
- Argon2 password hashing (OWASP recommended)
- Rate limiting (5 registrations/hour/IP)
- Async email verification via Celery
- JWT token-based authentication

**Security:**
- SQL injection prevention
- XSS protection
- CSRF protection
- Input sanitization
- Comprehensive security testing (73 tests, >80% coverage)

**Documentation:**
- [User Workflow Guide](docs/workflows/user_registration_workflow.md)
- [Security Considerations](docs/security/registration_security.md)
- [Testing Guide](docs/testing/registration_testing_guide.md)
- [Registration Troubleshooting](docs/troubleshooting/registration_troubleshooting.md)
- [Authentication Troubleshooting](docs/troubleshooting/authentication.md) ← **NEW**

**Try it:** Navigate to http://localhost:3000/register after starting services

### 🚧 Planned Features

- Email verification (US-2)
- Login/Logout (US-3)
- Password reset (US-4)
- Microsoft Entra ID SSO (US-5)
- AI Content Pipeline (Bloc 3)
- Report Consultation (Bloc 4)
- Recommendation Engine (Bloc 5)
- FinOps Cost Tracking (Bloc 6)

## Quick Start

### Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine + Docker Compose (Linux)
- Git
- 8GB RAM minimum (16GB recommended)
- 10GB disk space

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Configure environment variables:**
   ```bash
   # Copy templates
   cp .env.backend.example .env.backend
   cp .env.frontend.example .env.frontend

   # Generate cryptographically secure secrets (SECRET_KEY, JWT_SECRET_KEY)
   python backend/scripts/generate_secrets.py

   # Or manually generate with openssl
   openssl rand -base64 24  # For POSTGRES_PASSWORD
   openssl rand -base64 48  # For SECRET_KEY (64 chars)
   ```

3. **Configure API keys in `.env.backend`:**
   
   Edit `.env.backend` and set the following required API keys:
   
   ```bash
   # Get from https://makersuite.google.com/app/apikey
   GOOGLE_AI_STUDIO_API_KEY=your-google-ai-studio-api-key
   
   # Get from https://firecrawl.dev/
   FIRECRAWL_API_KEY=your-firecrawl-api-key
   ```
   
   **Important:** Replace ALL placeholder values (`your-*-key-here`) with actual secrets. 
   The application will validate configuration on startup and fail with clear error messages if 
   required variables are missing or invalid.
   
   For complete variable reference, see [Environment Variables Documentation](docs/setup/environment_variables.md).

4. **Build and start services:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

5. **Initialize database:**
   ```bash
   # Run migrations
   docker-compose exec backend python manage.py migrate

   # Create superuser (for admin access)
   docker-compose exec backend python manage.py createsuperuser
   ```

6. **Access the application:**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/

## Database Quick Reference

### Accessing PostgreSQL Shell

```bash
# Interactive psql shell
docker-compose exec db psql -U veille_tech_user -d veille_tech_db

# Run single command
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT version();"
```

### Common Database Operations

#### Verify pgvector Extension

```bash
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

#### Django Migration Commands

```bash
# Apply all pending migrations
docker-compose exec backend python manage.py migrate

# Check migration status (applied vs pending)
docker-compose exec backend python manage.py showmigrations

# Create new migration after model changes
docker-compose exec backend python manage.py makemigrations

# Rollback to specific migration (use with caution)
docker-compose exec backend python manage.py migrate core zero
```

See [Migration Workflow Documentation](docs/setup/00_setup_local_docker.md#database-migrations) for detailed migration procedures.

#### Backup Database

```bash
# SQL format
docker-compose exec db pg_dump -U veille_tech_user veille_tech_db > backup_$(date +%Y%m%d).sql

# Compressed format (faster, smaller)
docker-compose exec db pg_dump -U veille_tech_user -Fc veille_tech_db > backup_$(date +%Y%m%d).dump
```

#### Restore Database

```bash
# From SQL file
cat backup_20251029.sql | docker-compose exec -T db psql -U veille_tech_user -d veille_tech_db

# From compressed dump
docker-compose exec -T db pg_restore -U veille_tech_user -d veille_tech_db < backup_20251029.dump
```

### pgvector Usage Examples

#### Create Table with Vector Column

```sql
CREATE TABLE report_embeddings (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL,
    embedding vector(1536),  -- Dimension for text-embedding-004
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX ON report_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

#### Cosine Similarity Search

```sql
-- Find 10 most similar reports
SELECT report_id, embedding <=> '[query_vector]' AS distance
FROM report_embeddings
ORDER BY embedding <=> '[query_vector]'
LIMIT 10;
```

**Distance operators:**
- `<=>` Cosine distance (1 - cosine similarity)
- `<->` Euclidean distance
- `<#>` Negative dot product

### Database Monitoring

```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity WHERE datname = 'veille_tech_db';

-- Database size
SELECT pg_size_pretty(pg_database_size('veille_tech_db'));

-- Table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Common Commands

### Docker Management

```bash
# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Specific service

# Restart services
docker-compose restart backend
docker-compose restart db

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Rebuild after dependency changes
docker-compose build --no-cache backend
docker-compose up -d --force-recreate backend
```

### Django Commands

```bash
# Django shell
docker-compose exec backend python manage.py shell

# Create app
docker-compose exec backend python manage.py startapp myapp

# Collect static files
docker-compose exec backend python manage.py collectstatic

# Run tests
docker-compose exec backend python manage.py test
docker-compose exec backend pytest
```

### Celery Worker Management

```bash
# Start/stop worker
docker-compose up -d worker
docker-compose stop worker
docker-compose restart worker

# View worker logs
docker-compose logs -f worker

# Check worker health
docker-compose exec backend python manage.py celery_health_check

# Check worker status
docker-compose exec backend poetry run celery -A veille_tech status

# View active tasks
docker-compose exec backend poetry run celery -A veille_tech inspect active

# Enqueue task (from Django shell)
docker-compose exec backend python manage.py shell
>>> from veille_tech.tasks import test_task
>>> result = test_task.delay("Test message")
>>> print(result.id)  # Task ID

# View scheduler logs
docker-compose logs -f scheduler
```

For detailed worker management, troubleshooting, and scaling guides, see [Celery Worker Documentation](docs/setup/celery_worker.md).

### Redis Commands

```bash
# Redis CLI
docker-compose exec redis redis-cli

# Check Redis health
docker-compose exec redis redis-cli ping

# View all keys
docker-compose exec redis redis-cli KEYS '*'

# Flush all data (CAUTION)
docker-compose exec redis redis-cli FLUSHALL
```

## Troubleshooting

### Database Issues

**Connection refused:**
```bash
# Check service status
docker-compose ps db

# View logs
docker-compose logs db

# Restart service
docker-compose restart db
```

**Authentication failed:**
1. Verify credentials in `.env.backend`
2. Ensure `POSTGRES_USER` and `POSTGRES_PASSWORD` match
3. Recreate container: `docker-compose down && docker-compose up db`

**pgvector extension not found:**
```bash
# Check logs for initialization
docker-compose logs db | grep -i vector

# Manually install extension
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Performance Issues

**Slow container startup:**
- Check CPU/memory allocation in Docker Desktop
- Recommended: 4 CPU cores, 8GB RAM minimum
- Verify disk I/O is not saturated

**Slow database queries:**
```sql
-- Check for missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public';

-- Analyze table for statistics
ANALYZE report_embeddings;
```

### Network Issues

**Frontend can't reach backend:**
1. Verify services on same network: `docker-compose ps`
2. Check CORS settings in `.env.backend`: `CORS_ALLOWED_ORIGINS`
3. Verify backend health: `curl http://localhost:8000/api/health/`

## Project Structure

```
.
├── backend/                 # Django application
│   ├── config/             # Django settings
│   ├── apps/               # Django apps (planned)
│   ├── Dockerfile          # Backend container definition
│   ├── pyproject.toml      # Poetry dependencies
│   └── init-db.sql         # PostgreSQL initialization
├── frontend/               # React application
│   ├── src/                # React source code (planned)
│   ├── Dockerfile          # Frontend container definition
│   └── package.json        # npm dependencies
├── docs/                   # Documentation
│   ├── setup/              # Setup guides
│   └── *.md                # Feature specifications (French)
├── specs/                  # Structured specifications (English)
├── docker-compose.yml      # Service orchestration
├── .env.backend.example    # Backend environment template
├── .env.frontend.example   # Frontend environment template
└── README.md               # This file
```

## Development Workflow

### Feature Development

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes to code
3. Test locally with Docker Compose
4. Run tests: `docker-compose exec backend pytest`
5. Create commit: `git commit -m "feat: add my feature"`
6. Push and create pull request

### Running Tests

```bash
# Backend unit tests
docker-compose exec backend pytest

# Backend integration tests
docker-compose exec backend python manage.py test --tag=integration

# Frontend tests
docker-compose exec frontend npm test

# End-to-end tests
docker-compose exec frontend npm run test:e2e
```

### Code Quality

```bash
# Backend linting and formatting
docker-compose exec backend black .
docker-compose exec backend flake8
docker-compose exec backend isort .

# Frontend linting
docker-compose exec frontend npm run lint
docker-compose exec frontend npm run lint:fix
```

## Environment Variables

### Backend (.env.backend)

**Required:**
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - Database credentials
- `GOOGLE_AI_STUDIO_API_KEY` - Google AI Studio API key
- `FIRECRAWL_API_KEY` - Firecrawl web scraping API key
- `SECRET_KEY` - Django secret key (min 50 chars)

**Optional:**
- `AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET`, `AZURE_AD_TENANT_ID` - Microsoft SSO
- `EMAIL_HOST`, `EMAIL_PORT` - Email configuration

### Frontend (.env.frontend)

**Required:**
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

See `.env.backend.example` and `.env.frontend.example` for complete variable lists.

## Documentation

- **Setup Guide:** [docs/setup/00_setup_local_docker.md](docs/setup/00_setup_local_docker.md)
- **Functional Specifications:** `docs/*.md` (French)
- **Structured Specifications:** `specs/` (English)
- **API Documentation:** http://localhost:8000/api/docs/ (when running)

## Contributing

This is an internal project. For contribution guidelines, contact the project maintainer.

## License

Proprietary - Internal use only

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review documentation in `docs/`
3. Check Docker logs: `docker-compose logs [service]`
4. Contact project maintainer

## Project Status

**Current Phase:** Authentication Implementation (Bloc 1)

**Completed:**
- ✅ Docker Compose orchestration (Local Dev Environment)
- ✅ PostgreSQL with pgvector setup
- ✅ **User Registration (US-1)** - 19/19 tasks complete
  - Frontend: React registration form with validation
  - Backend: Django REST API with Argon2 hashing
  - Security: Rate limiting, input validation, comprehensive tests
  - Documentation: Complete workflow, security, testing, and troubleshooting guides

**In Progress:**
- 🔄 Email Verification (US-2) - Planned
- 🔄 Login/Logout (US-3) - Planned
- 🔄 Password Reset (US-4) - Planned

**Planned:**
- Microsoft Entra ID SSO (US-5)
- Subject & Subscription Management (Bloc 2)
- AI Content Pipeline (Bloc 3)
- Report Consultation UI (Bloc 4)
- Recommendation Engine (Bloc 5)
- FinOps Cost Tracking (Bloc 6)

**Statistics:**
- Total Tests: 73 (all passing)
- Test Coverage: >80%
- Backend: 8 core tasks + 6 testing/docs tasks
- Frontend: 5 UI/service tasks
- Security: OWASP Top 10 compliance

See `specs/authentication/US-1/.impl-state.json` for detailed task tracking.
