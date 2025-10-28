# Docker Development Environment Setup

This guide provides step-by-step instructions for setting up the AI-powered Technology Watch Platform's local development environment using Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Service Architecture](#service-architecture)
- [Common Commands](#common-commands)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

**Docker Installation:**
- **Windows**: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 4.25+ with WSL2 backend
- **macOS**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) 4.25+
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/) 24+ and [Docker Compose plugin](https://docs.docker.com/compose/install/linux/)

**Minimum Hardware:**
- 8GB RAM (6GB allocated to Docker)
- 4 CPU cores
- 10GB free disk space
- SSD strongly recommended

**Recommended Hardware:**
- 16GB RAM (12GB allocated to Docker)
- 8 CPU cores
- 20GB free disk space
- SSD required

### Verify Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.0.0 or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.20.0 or higher

# Verify Docker is running
docker ps
# Should return empty list (no containers running yet)
```

## Quick Start

For experienced developers, here's the fastest path to a running environment:

```bash
# 1. Clone repository
git clone <repository-url>
cd hackathon_base_de_connaissance

# 2. Configure environment
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
# Edit .env files with your API keys

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec backend python manage.py migrate

# 5. Create superuser
docker compose exec backend python manage.py createsuperuser

# 6. Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/
# Admin: http://localhost:8000/admin/
```

## Detailed Setup

### Step 1: Environment Configuration

#### Backend Configuration (.env.backend)

```bash
# Copy example file
cp .env.backend.example .env.backend

# Edit with your preferred editor
nano .env.backend  # or vim, code, etc.
```

**Required Variables to Update:**

1. **Google AI Studio API Key** (Required for AI features)
   - Get your key from: https://makersuite.google.com/app/apikey
   - Update: `GOOGLE_AI_STUDIO_API_KEY=your-actual-api-key`

2. **Firecrawl API Key** (Required for web scraping)
   - Get your key from: https://firecrawl.dev/
   - Update: `FIRECRAWL_API_KEY=your-actual-api-key`

3. **Django Secret Key** (Recommended to change)
   - Generate secure key:
     ```bash
     python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
     ```
   - Update: `SECRET_KEY=your-generated-secret-key`

4. **JWT Secret Key** (Recommended to change)
   - Generate secure key:
     ```bash
     openssl rand -base64 32
     ```
   - Update: `JWT_SECRET_KEY=your-generated-jwt-secret`

**Optional Variables:**

- **Microsoft Entra ID SSO** (Only if using Azure AD)
  - `AZURE_AD_CLIENT_ID`, `AZURE_AD_CLIENT_SECRET`, `AZURE_AD_TENANT_ID`

- **Email Configuration** (For development, console backend is fine)
  - Already configured for local development

#### Frontend Configuration (.env.frontend)

```bash
# Copy example file
cp .env.frontend.example .env.frontend
```

The default values are correct for local development. No changes needed unless you're running services on non-standard ports.

### Step 2: Build Docker Images

```bash
# Build all service images (first time only)
docker compose build

# This will:
# - Download base images (python:3.13-slim, node:20-alpine, postgres:15, redis:latest)
# - Install backend dependencies via Poetry
# - Install frontend dependencies via npm
# - Create optimized multi-stage images
# Expected time: 5-10 minutes on first build
```

**Build Progress Indicators:**
- `[internal] load metadata`: Downloading base images
- `[builder N/N] RUN poetry install`: Installing Python dependencies
- `[stage-1 N/N] RUN npm ci`: Installing Node dependencies

### Step 3: Start Services

```bash
# Start all services in detached mode (background)
docker compose up -d

# Monitor startup logs
docker compose logs -f

# Wait for all services to be healthy
# Expected time: 30-60 seconds
```

**Startup Order:**
1. PostgreSQL and Redis start first
2. Backend API starts after database is healthy
3. Worker and Scheduler start after backend
4. Frontend starts independently

**Health Check Verification:**
```bash
# Check service status
docker compose ps

# All services should show status "Up" and "healthy" after 60 seconds
# Example output:
# NAME        IMAGE                STATUS              PORTS
# db          postgres:15          Up (healthy)        5432:5432
# redis       redis:latest         Up (healthy)        6379:6379
# backend     ...                  Up (healthy)        8000:8000
# frontend    ...                  Up                  3000:3000
# worker      ...                  Up
# scheduler   ...                  Up
```

### Step 4: Initialize Database

```bash
# Run Django migrations
docker compose exec backend python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, sessions, accounts, ...
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   ...

# Create admin user
docker compose exec backend python manage.py createsuperuser

# Follow prompts:
# Username: admin
# Email: admin@example.com
# Password: (enter secure password)
# Password (again): (confirm password)
```

### Step 5: Verify Installation

```bash
# Test backend API
curl http://localhost:8000/api/health/
# Expected: {"status": "healthy"}

# Test frontend
curl http://localhost:3000
# Expected: HTML response

# Test database connection
docker compose exec backend python manage.py check
# Expected: System check identified no issues (0 silenced).

# Test Redis connection
docker compose exec redis redis-cli ping
# Expected: PONG
```

## Service Architecture

### Services Overview

| Service | Purpose | Port | Technology |
|---------|---------|------|------------|
| **db** | PostgreSQL database with pgvector | 5432 | PostgreSQL 15 |
| **redis** | Message broker & cache | 6379 | Redis 7+ |
| **backend** | Django REST API | 8000 | Python 3.13, Django |
| **frontend** | React SPA | 3000 | Node 20, React, Vite |
| **worker** | Celery worker for AI tasks | - | Celery |
| **scheduler** | Celery Beat for recurring tasks | - | Celery Beat |

### Data Persistence

**Named Volumes:**
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistence files

**Volume Location:**
```bash
# List volumes
docker volume ls | grep hackathon_base_de_connaissance

# Inspect volume location
docker volume inspect hackathon_base_de_connaissance_postgres_data
```

**Backup Strategy:**
```bash
# Backup PostgreSQL data
docker compose exec db pg_dump -U postgres tech_watch_db > backup.sql

# Restore PostgreSQL data
docker compose exec -T db psql -U postgres tech_watch_db < backup.sql
```

## Common Commands

### Service Management

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend

# Stop all services (keeps volumes)
docker compose down

# Stop and remove volumes (data loss!)
docker compose down -v

# Restart specific service
docker compose restart backend

# View service logs
docker compose logs -f backend
docker compose logs -f --tail=100 backend  # Last 100 lines
```

### Build and Update

```bash
# Rebuild images after dependency changes
docker compose build --no-cache backend

# Rebuild and restart
docker compose up -d --build backend

# Pull latest base images
docker compose pull
```

### Executing Commands

```bash
# Django management commands
docker compose exec backend python manage.py <command>

# Examples:
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
docker compose exec backend python manage.py test

# Run tests
docker compose exec backend pytest
docker compose exec backend pytest -v tests/accounts/

# Frontend commands
docker compose exec frontend npm test
docker compose exec frontend npm run lint
docker compose exec frontend npm run build

# Database commands
docker compose exec db psql -U postgres -d tech_watch_db
docker compose exec db pg_dump -U postgres tech_watch_db

# Redis commands
docker compose exec redis redis-cli
docker compose exec redis redis-cli KEYS "*"
```

### Monitoring

```bash
# View resource usage
docker stats

# View service status
docker compose ps

# Follow logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f backend

# Check service health
docker compose ps | grep healthy
```

## Development Workflow

### Hot Reload

**Backend (Django):**
- Source code is mounted as volume: `./backend:/app`
- Django runserver detects changes automatically
- No rebuild needed for code changes

**Frontend (Vite):**
- Source code is mounted as volume: `./frontend:/app`
- Vite HMR (Hot Module Replacement) enabled
- Browser updates automatically on save

### Adding Dependencies

**Backend (Poetry):**
```bash
# Add new dependency
docker compose exec backend poetry add <package-name>

# Add dev dependency
docker compose exec backend poetry add --dev <package-name>

# Update poetry.lock
docker compose exec backend poetry lock

# Rebuild image (after dependency changes)
docker compose build backend
docker compose up -d backend
```

**Frontend (npm):**
```bash
# Add new dependency
docker compose exec frontend npm install <package-name>

# Add dev dependency
docker compose exec frontend npm install --save-dev <package-name>

# Rebuild image (after dependency changes)
docker compose build frontend
docker compose up -d frontend
```

### Database Migrations

```bash
# Create new migration
docker compose exec backend python manage.py makemigrations

# Apply migrations
docker compose exec backend python manage.py migrate

# View migration status
docker compose exec backend python manage.py showmigrations

# Rollback last migration
docker compose exec backend python manage.py migrate <app_name> <previous_migration>
```

### Running Tests

```bash
# Backend tests
docker compose exec backend pytest
docker compose exec backend pytest -v tests/

# Frontend tests
docker compose exec frontend npm test

# Integration tests
docker compose exec backend python manage.py test --tag=integration

# Code coverage
docker compose exec backend pytest --cov=. --cov-report=html
```

## Troubleshooting

See [DOCKER_TROUBLESHOOTING.md](./DOCKER_TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Quick Fixes

**Services won't start:**
```bash
# Check logs
docker compose logs

# Verify .env files exist
ls .env.backend .env.frontend

# Restart services
docker compose down
docker compose up -d
```

**Port conflicts:**
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Stop conflicting service or change port in docker-compose.yml
```

**Database connection errors:**
```bash
# Check database is healthy
docker compose ps db

# Verify database credentials in .env.backend
docker compose exec backend env | grep POSTGRES

# Restart database
docker compose restart db
```

**Hot reload not working:**
```bash
# Verify volumes are mounted
docker compose config | grep volumes

# For Windows/Mac: Check CHOKIDAR_USEPOLLING is set
docker compose exec frontend env | grep CHOKIDAR
```

## Next Steps

1. **Configure AI API Keys**: Add your Google AI Studio and Firecrawl API keys to `.env.backend`
2. **Explore Admin Interface**: Visit http://localhost:8000/admin/ with superuser credentials
3. **Run Tests**: Execute `docker compose exec backend pytest` to verify setup
4. **Read Architecture Docs**: See `docs/` for detailed architecture documentation
5. **Start Development**: Begin implementing features following the project structure

## Support

- **Documentation**: See `docs/` directory for comprehensive guides
- **Issues**: Report problems on GitHub Issues
- **Docker Docs**: https://docs.docker.com/
