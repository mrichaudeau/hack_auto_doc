# US-0: Setup Local Docker Development Environment

**Priority**: P0 (Foundational)
**Bloc**: Infrastructure (Setup)
**Status**: En cours (1/15 tasks complétées)

## Vue d'ensemble

### Contexte

Mettre en place l'environnement de développement local complet basé sur Docker pour permettre à tous les développeurs de travailler efficacement. L'environnement doit inclure 6 services orchestrés (PostgreSQL avec pgvector, Redis, Backend Django, Frontend React, Worker Celery, Scheduler Celery Beat).

**Business value**: Sans cet environnement, aucun développement ne peut commencer. C'est la fondation technique du projet.

### Approche de décomposition

**Total: 15 tâches** réparties en 3 catégories:

- **Infrastructure (10 tâches)**: Configuration Docker, services, networking
- **Configuration (3 tâches)**: Variables d'environnement, scripts d'init
- **Documentation (2 tâches)**: Guides et troubleshooting

**Dépendances**: Aucune - c'est le point de départ du projet

---

## Liste des tâches

| ID | Titre | Type | Spécialité | Effort | Dépendances | Status |
|----|-------|------|------------|--------|-------------|--------|
| TASK-0.1 | Créer le fichier docker-compose.yml | Infrastructure | Config | 4h | None | ⬜ |
| TASK-0.2 | Créer le Dockerfile pour le backend Django | Infrastructure | Config | 3h | TASK-0.1 | ⬜ |
| TASK-0.3 | Configurer le service PostgreSQL avec pgvector | Infrastructure | Database | 3h | TASK-0.1 | ⬜ |
| TASK-0.4 | Configurer le service Redis | Infrastructure | Config | 2h | TASK-0.1 | ⬜ |
| TASK-0.5 | Créer le Dockerfile pour le frontend React | Infrastructure | Config | 3h | TASK-0.1 | ⬜ |
| TASK-0.6 | Configurer le service Celery worker | Infrastructure | Config | 3h | TASK-0.2 | ⬜ |
| TASK-0.7 | Configurer le service Celery Beat scheduler | Infrastructure | Config | 2h | TASK-0.6 | ⬜ |
| TASK-0.8 | Créer les fichiers de configuration réseau Docker | Infrastructure | Config | 2h | TASK-0.1 | ⬜ |
| TASK-0.9 | Créer les volumes Docker pour la persistance | Infrastructure | Config | 2h | TASK-0.1 | ⬜ |
| TASK-0.10 | Créer le script d'initialisation de la base de données | Infrastructure | Database | 3h | TASK-0.3 | ⬜ |
| TASK-0.11 | Créer les templates de fichiers d'environnement | Configuration | Config | 3h | TASK-0.2 | ⬜ |
| TASK-0.12 | Créer le script de démarrage rapide (quick-start.sh) | Configuration | Config | 2h | TASK-0.11 | ⬜ |
| TASK-0.13 | Créer le fichier .dockerignore | Configuration | Config | 1h | None | ⬜ |
| TASK-0.14 | Créer le guide de troubleshooting Docker | Documentation | Documentation | 3h | TASK-0.12 | ⬜ |
| TASK-0.15 | Tester l'environnement complet de bout en bout | Documentation | Config | 4h | TASK-0.14 | ✅ |

---

## Détails des tâches

### ⚙️ Infrastructure

#### TASK-0.1: Créer le fichier docker-compose.yml

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 4 heures

##### Description

Créer le fichier `docker-compose.yml` principal qui orchestre les 6 services de l'environnement de développement. Le fichier doit définir tous les services, leurs dépendances, les réseaux, et les volumes nécessaires.

##### Fichiers impactés

- `docker-compose.yml` (nouveau)

##### Critères d'acceptation

- [ ] Le fichier docker-compose.yml définit 6 services: db, redis, backend, frontend, worker, scheduler
- [ ] Les dépendances entre services sont correctement définies (depends_on)
- [ ] Les ports sont mappés correctement (5432, 6379, 8000, 3000)
- [ ] Les variables d'environnement sont référencées via env_file
- [ ] Les healthchecks sont configurés pour db et redis
- [ ] Le fichier suit les meilleures pratiques Docker Compose v3.8+

**Dépendances**: None
**Effort estimé**: 4 heures

##### Notes d'implémentation

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: supabase/postgres:15.1.0.147
    container_name: veille_db
    environment:
      POSTGRES_DB: veille_db
      POSTGRES_USER: veille_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U veille_user -d veille_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:latest
    container_name: veille_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: veille_backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file:
      - .env.backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: veille_frontend
    command: npm run dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    env_file:
      - .env.frontend
    depends_on:
      - backend

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: veille_worker
    command: celery -A config worker -l INFO
    volumes:
      - ./backend:/app
    env_file:
      - .env.backend
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: veille_scheduler
    command: celery -A config beat -l INFO
    volumes:
      - ./backend:/app
    env_file:
      - .env.backend
    depends_on:
      - redis

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: veille_network
```

---

#### TASK-0.2: Créer le Dockerfile pour le backend Django

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Créer un Dockerfile optimisé pour l'application Django backend utilisant Poetry pour la gestion des dépendances. Le Dockerfile doit installer Python 3.11, Poetry, toutes les dépendances (Django, DRF, Celery, Langgraph, etc.), et configurer l'application pour le développement.

##### Fichiers impactés

- `backend/Dockerfile` (nouveau)
- `backend/pyproject.toml` (nouveau)
- `backend/poetry.lock` (généré par Poetry)

##### Critères d'acceptation

- [ ] Image basée sur python:3.11-slim
- [ ] Poetry installé et configuré
- [ ] Installation des dépendances système nécessaires (postgresql-client, etc.)
- [ ] Installation de toutes les dépendances Python via Poetry
- [ ] WORKDIR configuré à /app
- [ ] User non-root créé pour la sécurité
- [ ] Le build est optimisé avec mise en cache des layers

**Dépendances**: TASK-0.1
**Effort estimé**: 3 heures

##### Notes d'implémentation

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Copy poetry files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create virtual env (we're in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY . .

# Install the project itself
RUN poetry install --no-interaction --no-ansi

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

```toml
# backend/pyproject.toml
[tool.poetry]
name = "veille-backend"
version = "0.1.0"
description = "AI-powered Technology Watch Platform - Backend"
authors = ["Your Team <team@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
Django = "^4.2.7"
djangorestframework = "^3.14.0"
djangorestframework-simplejwt = "^5.3.0"
django-allauth = "^0.57.0"
django-cors-headers = "^4.3.1"
psycopg2-binary = "^2.9.9"
pgvector = "^0.2.4"
celery = "^5.3.4"
redis = "^5.0.1"
langgraph = "^0.0.26"
langchain = "^0.1.0"
langchain-openai = "^0.0.2"
python-dotenv = "^1.0.0"
gunicorn = "^21.2.0"
django-celery-beat = "^2.5.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-django = "^4.7.0"
black = "^23.11.0"
flake8 = "^6.1.0"
mypy = "^1.7.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

---

#### TASK-0.3: Configurer le service PostgreSQL avec pgvector

**Type**: Infrastructure - Database
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Configurer le service PostgreSQL 15 dans Docker Compose en utilisant l'image Supabase qui inclut pgvector et de nombreuses extensions. Créer un script d'initialisation pour vérifier l'installation et configurer la base de données.

##### Fichiers impactés

- `docker-compose.yml` (modification - section db)
- `scripts/init-db.sh` (nouveau)

##### Critères d'acceptation

- [ ] L'image Supabase PostgreSQL 15.1.0.147 est utilisée
- [ ] L'extension pgvector est activée automatiquement
- [ ] La base de données est créée avec le bon encoding (UTF8)
- [ ] Un user/password sont configurés via variables d'environnement
- [ ] Le script d'init vérifie que pgvector est bien activé
- [ ] Les données sont persistées dans un volume Docker

**Dépendances**: TASK-0.1
**Effort estimé**: 3 heures

##### Notes d'implémentation

```bash
#!/bin/bash
# scripts/init-db.sh

set -e

echo "Initializing Supabase PostgreSQL database..."

# Wait for PostgreSQL to be ready
until pg_isready -U veille_user -d veille_db; do
  echo "Waiting for database to be ready..."
  sleep 2
done

# Connect and enable extensions (pgvector already included in Supabase image)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable pgvector extension (should already be available)
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Verify extension is installed
    SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;
EOSQL

echo "Database initialized successfully with pgvector"
```

**Note importante**: L'image Supabase PostgreSQL inclut déjà pgvector et de nombreuses extensions utiles. Utiliser l'image `supabase/postgres:15.1.0.147` qui contient PostgreSQL 15 avec pgvector préinstallé.

**Modification du docker-compose.yml**:
```yaml
db:
  image: supabase/postgres:15.1.0.147  # Image Supabase avec pgvector préinstallé
  # ... rest of config
```

---

#### TASK-0.4: Configurer le service Redis

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 2 heures

##### Description

Configurer Redis comme broker de messages pour Celery et cache distribué. Le service doit être persistent et optimisé pour le développement local.

##### Fichiers impactés

- `docker-compose.yml` (modification - section redis)
- `redis/redis.conf` (nouveau - optionnel)

##### Critères d'acceptation

- [ ] Redis latest est utilisé
- [ ] Le port 6379 est exposé
- [ ] Les données sont persistées dans un volume
- [ ] Le healthcheck est configuré
- [ ] Redis accepte les connexions depuis les autres services Docker
- [ ] La configuration est optimisée pour le développement

**Dépendances**: TASK-0.1
**Effort estimé**: 2 heures

##### Notes d'implémentation

La configuration de base dans docker-compose.yml est suffisante pour le développement. Pour une configuration avancée:

```conf
# redis/redis.conf (optionnel)
# Enable persistence
appendonly yes
appendfilename "appendonly.aof"

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Disable protected mode for Docker network
protected-mode no
```

Si un fichier de config custom est utilisé:
```yaml
redis:
  image: redis:latest
  command: redis-server /usr/local/etc/redis/redis.conf
  volumes:
    - redis_data:/data
    - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
```

---

#### TASK-0.5: Créer le Dockerfile pour le frontend React

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Créer un Dockerfile pour l'application React frontend. Le Dockerfile doit utiliser Node 20, installer les dépendances, et configurer le serveur de développement avec hot reload.

##### Fichiers impactés

- `frontend/Dockerfile` (nouveau)
- `frontend/package.json` (nouveau - structure de base)

##### Critères d'acceptation

- [ ] Image basée sur node:20-alpine
- [ ] Les dépendances npm sont installées
- [ ] Le hot reload fonctionne avec volumes montés
- [ ] Le port 3000 est exposé
- [ ] node_modules est dans un volume anonyme (performance)
- [ ] User non-root pour la sécurité

**Dépendances**: TASK-0.1
**Effort estimé**: 3 heures

##### Notes d'implémentation

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev"]
```

```json
// frontend/package.json (structure minimale)
{
  "name": "veille-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

**Important**: Dans docker-compose.yml, utiliser un volume anonyme pour node_modules:
```yaml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules  # Volume anonyme pour performance
```

---

#### TASK-0.6: Configurer le service Celery worker

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Configurer le service Celery worker qui exécutera les tâches asynchrones (scraping, pipeline IA). Le worker doit utiliser la même image que le backend Django et se connecter à Redis.

##### Fichiers impactés

- `docker-compose.yml` (modification - section worker)
- `backend/config/celery.py` (nouveau)

##### Critères d'acceptation

- [ ] Le worker utilise la même image Docker que le backend
- [ ] La commande Celery est correctement configurée
- [ ] Le worker se connecte à Redis comme broker
- [ ] Les logs sont visibles avec docker-compose logs
- [ ] Le worker démarre après que db et redis soient healthy
- [ ] Les variables d'environnement sont partagées avec le backend

**Dépendances**: TASK-0.2
**Effort estimé**: 3 heures

##### Notes d'implémentation

```python
# backend/config/celery.py
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('veille')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

```python
# backend/config/__init__.py
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**Configuration dans docker-compose.yml**:
```yaml
worker:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: veille_worker
  command: celery -A config worker -l INFO --concurrency=2
  volumes:
    - ./backend:/app
  env_file:
    - .env.backend
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  restart: unless-stopped
```

---

#### TASK-0.7: Configurer le service Celery Beat scheduler

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 2 heures

##### Description

Configurer Celery Beat pour planifier les tâches récurrentes (scraping quotidien, nettoyage de cache, etc.). Le scheduler doit utiliser Redis comme backend de persistance.

##### Fichiers impactés

- `docker-compose.yml` (modification - section scheduler)
- `backend/config/celery.py` (modification)

##### Critères d'acceptation

- [ ] Celery Beat est configuré et démarre correctement
- [ ] Le scheduler utilise Redis comme backend
- [ ] Un exemple de tâche périodique est défini
- [ ] Le scheduler ne crée qu'une seule instance (pas de duplication)
- [ ] Les logs montrent les tâches planifiées
- [ ] Le scheduler redémarre automatiquement en cas d'erreur

**Dépendances**: TASK-0.6
**Effort estimé**: 2 heures

##### Notes d'implémentation

```python
# backend/config/celery.py (ajout)
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Example: Clean up expired data daily at 2 AM
    'cleanup-expired-data': {
        'task': 'accounts.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=2, minute=0),
    },
    # Example: Daily scraping at 6 AM
    'daily-scraping': {
        'task': 'pipeline.tasks.run_daily_scraping',
        'schedule': crontab(hour=6, minute=0),
    },
}

# Use Redis as result backend
app.conf.result_backend = 'redis://redis:6379/0'
```

**Configuration dans docker-compose.yml**:
```yaml
scheduler:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: veille_scheduler
  command: celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
  volumes:
    - ./backend:/app
  env_file:
    - .env.backend
  depends_on:
    - redis
    - backend
  restart: unless-stopped
```

**Note**: Pour utiliser `DatabaseScheduler`, ajouter `django-celery-beat` à requirements.txt

---

#### TASK-0.8: Créer les fichiers de configuration réseau Docker

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 2 heures

##### Description

Configurer le réseau Docker pour permettre la communication entre tous les services. Utiliser un réseau bridge personnalisé pour améliorer la sécurité et les performances.

##### Fichiers impactés

- `docker-compose.yml` (modification - section networks)

##### Critères d'acceptation

- [ ] Un réseau custom est créé (veille_network)
- [ ] Tous les services sont connectés au réseau
- [ ] Les services peuvent se référencer par leur nom (DNS interne)
- [ ] Le réseau est de type bridge
- [ ] La configuration réseau est documentée
- [ ] Les ports exposés sur l'hôte sont minimaux

**Dépendances**: TASK-0.1
**Effort estimé**: 2 heures

##### Notes d'implémentation

```yaml
# docker-compose.yml (section networks)
networks:
  veille_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16

services:
  db:
    networks:
      - veille_network
  redis:
    networks:
      - veille_network
  backend:
    networks:
      - veille_network
  # ... autres services
```

**DNS interne**: Les services peuvent se référencer par leur nom:
- Backend → Redis: `redis://redis:6379`
- Backend → DB: `postgresql://veille_user:pass@db:5432/veille_db`

---

#### TASK-0.9: Créer les volumes Docker pour la persistance

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 2 heures

##### Description

Configurer les volumes Docker pour persister les données importantes (base de données, Redis, fichiers uploadés). Les volumes doivent être nommés et facilement identifiables.

##### Fichiers impactés

- `docker-compose.yml` (modification - section volumes)

##### Critères d'acceptation

- [ ] Volume pour PostgreSQL data (postgres_data)
- [ ] Volume pour Redis data (redis_data)
- [ ] Volume pour les media files Django (media_files)
- [ ] Les volumes sont nommés et préfixés
- [ ] Les volumes survivent à docker-compose down
- [ ] Un script de backup est fourni

**Dépendances**: TASK-0.1
**Effort estimé**: 2 heures

##### Notes d'implémentation

```yaml
# docker-compose.yml (section volumes)
volumes:
  postgres_data:
    name: veille_postgres_data
  redis_data:
    name: veille_redis_data
  media_files:
    name: veille_media_files

services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    volumes:
      - redis_data:/data
  backend:
    volumes:
      - ./backend:/app
      - media_files:/app/media
```

**Script de backup**:
```bash
#!/bin/bash
# scripts/backup-volumes.sh

BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR

echo "Backing up PostgreSQL..."
docker-compose exec -T db pg_dump -U veille_user veille_db > "$BACKUP_DIR/db_backup_$(date +%Y%m%d).sql"

echo "Backing up volumes..."
docker run --rm -v veille_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_$(date +%Y%m%d).tar.gz /data

echo "Backup completed!"
```

---

#### TASK-0.10: Créer le script d'initialisation de la base de données

**Type**: Infrastructure - Database
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Créer un script bash qui initialise complètement la base de données: installation de pgvector, création des extensions nécessaires, et vérification de la configuration.

##### Fichiers impactés

- `scripts/init-db.sh` (modification/complétion)
- `scripts/check-db.sh` (nouveau)

##### Critères d'acceptation

- [ ] Le script installe pgvector automatiquement
- [ ] Le script crée les extensions nécessaires (uuid-ossp, etc.)
- [ ] Le script vérifie que tout est correctement installé
- [ ] Le script est idempotent (peut être réexécuté sans erreur)
- [ ] Les erreurs sont loguées clairement
- [ ] Un script de vérification post-installation est fourni

**Dépendances**: TASK-0.3
**Effort estimé**: 3 heures

##### Notes d'implémentation

```bash
#!/bin/bash
# scripts/init-db.sh

set -e

echo "=== Database Initialization Script ==="

# Wait for PostgreSQL to be ready
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "PostgreSQL is ready!"

# Create extensions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Enable pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Enable UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Verify extensions
    SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');

    -- Grant permissions
    GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;

    -- Create schema if needed
    CREATE SCHEMA IF NOT EXISTS public;
    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;
EOSQL

echo "Extensions installed successfully"

# Run verification
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Test vector operations
    SELECT vector_dims('[1,2,3]'::vector);

    -- Show database encoding
    SHOW SERVER_ENCODING;

    -- Show installed extensions
    \dx
EOSQL

echo "=== Initialization Complete ==="
```

```bash
#!/bin/bash
# scripts/check-db.sh

echo "Checking database configuration..."

docker-compose exec db psql -U veille_user -d veille_db -c "\dx" | grep -E "(vector|uuid-ossp)"

if [ $? -eq 0 ]; then
    echo "Database is correctly configured!"
else
    echo "Error: Extensions not found"
    exit 1
fi
```

---

### 🔧 Configuration

#### TASK-0.11: Créer les templates de fichiers d'environnement

**Type**: Configuration - Config
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Créer les fichiers templates d'environnement (.env.example) pour le backend et le frontend avec toutes les variables nécessaires documentées. Les développeurs copieront ces templates et ajouteront leurs propres valeurs.

##### Fichiers impactés

- `env.backend.example` (nouveau)
- `env.frontend.example` (nouveau)
- `.env.example` (nouveau - variables globales)

##### Critères d'acceptation

- [ ] env.backend.example contient toutes les variables Django/Celery
- [ ] env.frontend.example contient les variables React
- [ ] Chaque variable est documentée avec un commentaire
- [ ] Les valeurs sensibles ont des placeholders clairs
- [ ] Un .gitignore exclut les vrais fichiers .env
- [ ] Les URLs de services Docker sont pré-remplies

**Dépendances**: TASK-0.2
**Effort estimé**: 3 heures

##### Notes d'implémentation

```bash
# env.backend.example

# Django Configuration
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=veille_db
DB_USER=veille_user
DB_PASSWORD=change-this-password
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
FIRECRAWL_API_KEY=fc-your-firecrawl-key-here

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Email Configuration (optional for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password

# Logging
LOG_LEVEL=INFO
```

```bash
# env.frontend.example

# API Configuration
VITE_API_URL=http://localhost:8000/api
VITE_API_TIMEOUT=30000

# Environment
VITE_ENV=development

# Feature Flags
VITE_ENABLE_MOCK_DATA=false
VITE_ENABLE_DEBUG=true

# Authentication
VITE_AUTH_TOKEN_KEY=veille_auth_token
```

```gitignore
# .gitignore (ajout)
.env
.env.backend
.env.frontend
.env.local
*.env
!*.env.example
```

---

#### TASK-0.12: Créer le script de démarrage rapide (quick-start.sh)

**Type**: Configuration - Config
**Priority**: P0
**Estimated Effort**: 2 heures

##### Description

Créer un script bash interactif qui automatise le processus de configuration initiale: copie des fichiers .env, vérification des prérequis, build, démarrage, et initialisation de la base de données.

##### Fichiers impactés

- `quick-start.sh` (nouveau)
- `scripts/init-project.sh` (nouveau)

##### Critères d'acceptation

- [ ] Le script vérifie que Docker et Docker Compose sont installés
- [ ] Le script copie les fichiers .env.example si nécessaire
- [ ] Le script demande confirmation avant chaque étape
- [ ] Le script lance docker-compose build et up
- [ ] Le script exécute les migrations Django
- [ ] Le script affiche les URLs d'accès à la fin

**Dépendances**: TASK-0.11
**Effort estimé**: 2 heures

##### Notes d'implémentation

```bash
#!/bin/bash
# quick-start.sh

set -e

echo "=================================="
echo "Plateforme de Veille Technologique"
echo "Quick Start Script"
echo "=================================="

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

echo "Prerequisites OK"

# Copy environment files if they don't exist
echo ""
echo "Setting up environment files..."

if [ ! -f .env.backend ]; then
    echo "Creating .env.backend from template..."
    cp env.backend.example .env.backend
    echo "Please edit .env.backend and add your API keys"
    read -p "Press Enter when ready to continue..."
fi

if [ ! -f .env.frontend ]; then
    echo "Creating .env.frontend from template..."
    cp env.frontend.example .env.frontend
fi

# Build images
echo ""
echo "Building Docker images..."
docker-compose build

# Start services
echo ""
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Run migrations
echo ""
echo "Running database migrations..."
docker-compose exec -T backend python manage.py migrate

# Create superuser (optional)
echo ""
read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Display access URLs
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Access URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000/api/"
echo "  Admin:     http://localhost:8000/admin/"
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart:       docker-compose restart"
echo ""
```

---

#### TASK-0.13: Créer le fichier .dockerignore

**Type**: Configuration - Config
**Priority**: P0
**Estimated Effort**: 1 heure

##### Description

Créer les fichiers .dockerignore pour optimiser les builds Docker en excluant les fichiers inutiles (node_modules, __pycache__, .git, etc.).

##### Fichiers impactés

- `backend/.dockerignore` (nouveau)
- `frontend/.dockerignore` (nouveau)

##### Critères d'acceptation

- [ ] Fichiers de cache Python exclus (__pycache__, *.pyc)
- [ ] node_modules exclu pour le frontend
- [ ] Fichiers .env exclus
- [ ] Répertoire .git exclu
- [ ] Fichiers de tests exclus
- [ ] Le build est significativement plus rapide

**Dépendances**: None
**Effort estimé**: 1 heure

##### Notes d'implémentation

```
# backend/.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.git
.gitignore
.env
.env.*
!.env.example
*.log
*.sqlite3
db.sqlite3
.pytest_cache
.coverage
htmlcov
.mypy_cache
.vscode
.idea
*.md
!README.md
media/
staticfiles/
```

```
# frontend/.dockerignore
node_modules
npm-debug.log
.git
.gitignore
.env
.env.*
!.env.example
dist
build
.vscode
.idea
*.md
!README.md
.cache
coverage
.nyc_output
```

---

### 📚 Documentation

#### TASK-0.14: Créer le guide de troubleshooting Docker

**Type**: Documentation - Documentation
**Priority**: P0
**Estimated Effort**: 3 heures

##### Description

Créer un guide complet de troubleshooting pour résoudre les problèmes courants rencontrés lors du setup Docker (problèmes de ports, permissions, volumes, networking, etc.).

##### Fichiers impactés

- `docs/setup/TROUBLESHOOTING.md` (nouveau)

##### Critères d'acceptation

- [ ] Guide couvre les 10 problèmes les plus courants
- [ ] Chaque problème a une section diagnostique et solution
- [ ] Des commandes de débogage sont fournies
- [ ] Le guide inclut des liens vers la documentation Docker
- [ ] Le guide est en français
- [ ] Un index des problèmes est présent

**Dépendances**: TASK-0.12
**Effort estimé**: 3 heures

##### Notes d'implémentation

```markdown
# Guide de Troubleshooting Docker

## Problèmes Courants

### 1. Port Already in Use

**Symptôme**: Erreur "port is already allocated" lors du démarrage

**Diagnostic**:
```bash
# Vérifier quel processus utilise le port
lsof -i :8000  # ou :3000, :5432, etc.
```

**Solution**:
- Arrêter le processus conflictuel
- Ou modifier le port dans docker-compose.yml

### 2. Database Connection Failed

**Symptôme**: Backend ne peut pas se connecter à PostgreSQL

**Diagnostic**:
```bash
# Vérifier que le service db est healthy
docker-compose ps
docker-compose logs db
```

**Solution**:
- Attendre que le healthcheck passe
- Vérifier les credentials dans .env.backend
- Vérifier que le service backend a `depends_on` configuré

### 3. pgvector Extension Missing

**Symptôme**: Erreur "extension vector does not exist"

**Diagnostic**:
```bash
# Vérifier les extensions installées
docker-compose exec db psql -U veille_user -d veille_db -c "\dx"
```

**Solution**:
- Vérifier que l'image pgvector/pgvector est utilisée
- Réexécuter le script d'init: `docker-compose restart db`

### 4. Volume Permission Issues

**Symptôme**: Erreurs de permission lors de l'écriture de fichiers

**Solution**:
```bash
# Corriger les permissions
sudo chown -R $USER:$USER ./backend ./frontend
```

### 5. Celery Worker Not Processing Tasks

**Symptôme**: Les tâches restent en pending

**Diagnostic**:
```bash
# Vérifier les logs du worker
docker-compose logs -f worker
```

**Solution**:
- Vérifier que Redis est accessible
- Vérifier la configuration CELERY_BROKER_URL
- Redémarrer le worker: `docker-compose restart worker`

### 6. Hot Reload Not Working

**Symptôme**: Les changements de code ne sont pas détectés

**Solution Frontend**:
- Vérifier que les volumes sont correctement montés
- Utiliser un volume anonyme pour node_modules

**Solution Backend**:
- S'assurer que DEBUG=True dans .env.backend
- Vérifier les volumes dans docker-compose.yml

### 7. Build Cache Issues

**Symptôme**: Modifications non prises en compte après rebuild

**Solution**:
```bash
# Rebuild complet sans cache
docker-compose build --no-cache
docker-compose up -d
```

### 8. Network Communication Issues

**Symptôme**: Services ne peuvent pas communiquer entre eux

**Diagnostic**:
```bash
# Tester la connectivité
docker-compose exec backend ping redis
docker-compose exec backend ping db
```

**Solution**:
- Vérifier que tous les services sont sur le même réseau
- Utiliser les noms de services comme hostnames

### 9. Disk Space Issues

**Symptôme**: Build échoue avec "no space left on device"

**Solution**:
```bash
# Nettoyer les ressources Docker
docker system prune -a --volumes
```

### 10. Container Keeps Restarting

**Symptôme**: Un service redémarre en boucle

**Diagnostic**:
```bash
# Voir les logs détaillés
docker-compose logs --tail=100 [service_name]
```

**Solution**:
- Vérifier la commande de démarrage
- Vérifier les dépendances (depends_on)
- Vérifier les healthchecks

## Commandes Utiles

```bash
# Voir l'état de tous les services
docker-compose ps

# Redémarrer un service spécifique
docker-compose restart backend

# Voir les logs en temps réel
docker-compose logs -f

# Accéder au shell d'un conteneur
docker-compose exec backend bash

# Recréer tous les conteneurs
docker-compose up -d --force-recreate

# Tout supprimer et recommencer
docker-compose down -v
docker-compose up -d
```
```

---

#### TASK-0.15: Tester l'environnement complet de bout en bout

**Type**: Documentation - Config
**Priority**: P0
**Estimated Effort**: 4 heures

##### Description

Effectuer un test end-to-end complet de l'environnement Docker: démarrage des services, vérification des connexions, test des APIs, vérification de Celery, et documentation des résultats.

##### Fichiers impactés

- `scripts/test-environment.sh` (nouveau)
- `docs/setup/SETUP_VERIFICATION.md` (nouveau)

##### Critères d'acceptation

- [x] Script de test automatique créé (Tests via Playwright et curl)
- [x] Tous les services démarrent sans erreur
- [x] Les healthchecks passent pour db et redis
- [x] Le backend répond sur /api/
- [x] Le frontend est accessible sur :3000
- [x] Celery worker et beat sont fonctionnels
- [x] Un rapport de test est généré (Documented in PR #146 and Issue #144)

**Dépendances**: TASK-0.14
**Effort estimé**: 4 heures

##### Notes d'implémentation

```bash
#!/bin/bash
# scripts/test-environment.sh

set -e

echo "==================================="
echo "Environment Testing Script"
echo "==================================="

FAILED=0

# Test 1: Check Docker services
echo ""
echo "[1/7] Checking Docker services..."
if docker-compose ps | grep -q "Up"; then
    echo "Services are running"
else
    echo "ERROR: Services are not running"
    FAILED=$((FAILED + 1))
fi

# Test 2: Check database connection
echo ""
echo "[2/7] Testing database connection..."
if docker-compose exec -T db pg_isready -U veille_user -d veille_db > /dev/null 2>&1; then
    echo "Database is accessible"
else
    echo "ERROR: Cannot connect to database"
    FAILED=$((FAILED + 1))
fi

# Test 3: Check pgvector extension
echo ""
echo "[3/7] Checking pgvector extension..."
if docker-compose exec -T db psql -U veille_user -d veille_db -c "SELECT extname FROM pg_extension WHERE extname='vector'" | grep -q "vector"; then
    echo "pgvector is installed"
else
    echo "ERROR: pgvector is not installed"
    FAILED=$((FAILED + 1))
fi

# Test 4: Check Redis connection
echo ""
echo "[4/7] Testing Redis connection..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "Redis is responsive"
else
    echo "ERROR: Redis is not responding"
    FAILED=$((FAILED + 1))
fi

# Test 5: Check backend API
echo ""
echo "[5/7] Testing backend API..."
if curl -f http://localhost:8000/api/ > /dev/null 2>&1; then
    echo "Backend API is accessible"
else
    echo "WARNING: Backend API not responding (may need migrations)"
fi

# Test 6: Check frontend
echo ""
echo "[6/7] Testing frontend..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend is accessible"
else
    echo "WARNING: Frontend not responding"
fi

# Test 7: Check Celery worker
echo ""
echo "[7/7] Testing Celery worker..."
if docker-compose logs worker | grep -q "celery@"; then
    echo "Celery worker is running"
else
    echo "ERROR: Celery worker not detected"
    FAILED=$((FAILED + 1))
fi

# Summary
echo ""
echo "==================================="
if [ $FAILED -eq 0 ]; then
    echo "ALL TESTS PASSED!"
    echo "Environment is ready for development"
else
    echo "TESTS FAILED: $FAILED issue(s) detected"
    echo "Please check the logs above"
    exit 1
fi
echo "==================================="
```

```markdown
# Setup Verification Checklist

## Prérequis
- [ ] Docker installé (version 20+)
- [ ] Docker Compose installé (version 2+)
- [ ] Git installé

## Étapes de vérification

### 1. Services Docker
```bash
docker-compose ps
```
Tous les services doivent être "Up" et "healthy"

### 2. Base de données
```bash
docker-compose exec db psql -U veille_user -d veille_db -c "\dx"
```
Extensions attendues: vector, uuid-ossp

### 3. Backend API
Accéder à http://localhost:8000/api/
→ Doit retourner une réponse JSON

### 4. Frontend
Accéder à http://localhost:3000
→ Doit afficher l'interface React

### 5. Celery Worker
```bash
docker-compose logs worker
```
→ Doit afficher "celery@[hostname] ready"

### 6. Celery Beat
```bash
docker-compose logs scheduler
```
→ Doit afficher "beat: Starting..."

## Tests Fonctionnels

### Test 1: Création d'un superuser
```bash
docker-compose exec backend python manage.py createsuperuser
```

### Test 2: Accès à l'admin
http://localhost:8000/admin/
→ Login avec le superuser créé

### Test 3: Hot Reload Backend
1. Modifier un fichier Python dans backend/
2. Observer les logs: `docker-compose logs -f backend`
3. Le serveur doit redémarrer automatiquement

### Test 4: Hot Reload Frontend
1. Modifier un fichier React dans frontend/
2. Le navigateur doit se rafraîchir automatiquement

## Troubleshooting

Si un test échoue, consulter `docs/setup/TROUBLESHOOTING.md`
```

##### ✅ Status de complétion

**Date de complétion**: 2025-10-26
**PR**: #146
**Issue**: #144

**Tests effectués**:
- ✅ Tous les 6 services Docker fonctionnels (db, redis, backend, frontend, worker, scheduler)
- ✅ PostgreSQL avec pgvector extension validé
- ✅ Redis accessible et fonctionnel
- ✅ Backend API testée (endpoints d'authentification: register, login, verify-email)
- ✅ Frontend accessible sur http://localhost:3000
- ✅ Celery worker et scheduler opérationnels
- ✅ Tests effectués via Playwright, curl, et vérification des logs Docker

**Problèmes résolus durant les tests**:
1. Configuration Redis incompatible (CLIENT_CLASS) dans `backend/config/settings.py` - Corrigé
2. Port frontend mismatch (Vite 5173 vs Docker 3000) dans `frontend/Dockerfile` - Corrigé

**Documentation générée**:
- Rapport de test complet dans PR #146
- Commentaire détaillé sur Issue #144

---

## Graphe de dépendances

### Séquence d'implémentation recommandée

**Phase 1: Base Infrastructure (Jour 1)**
```
TASK-0.1 (docker-compose.yml) [4h]
    ↓
TASK-0.2 (Backend Dockerfile) [3h]
TASK-0.3 (PostgreSQL + pgvector) [3h]
TASK-0.4 (Redis) [2h]
TASK-0.5 (Frontend Dockerfile) [3h]
```

**Phase 2: Services Celery (Jour 2)**
```
TASK-0.6 (Celery worker) [3h]
    ↓
TASK-0.7 (Celery Beat) [2h]
```

**Phase 3: Configuration (Jour 2)**
```
TASK-0.8 (Networking) [2h]
TASK-0.9 (Volumes) [2h]
TASK-0.10 (DB init script) [3h]
TASK-0.11 (Environment templates) [3h]
    ↓
TASK-0.12 (Quick start script) [2h]
TASK-0.13 (.dockerignore) [1h]
```

**Phase 4: Documentation et Tests (Jour 3)**
```
TASK-0.14 (Troubleshooting guide) [3h]
    ↓
TASK-0.15 (End-to-end testing) [4h]
```

### Opportunités de parallélisation

- **Dockerfiles (0.2, 0.5)** peuvent être créés en parallèle
- **Services (0.3, 0.4)** peuvent être configurés en parallèle
- **Configuration (0.8, 0.9, 0.13)** peuvent être créés en parallèle
- **Documentation (0.14, 0.15)** peut commencer dès que la config est stable

---

## Estimation globale

### Par type de tâche

| Type | Nombre de tâches | Effort total |
|------|------------------|--------------|
| Infrastructure | 10 | 27h (3.4 jours) |
| Configuration | 3 | 6h (0.75 jour) |
| Documentation | 2 | 7h (0.9 jour) |
| **TOTAL** | **15** | **40h (5 jours)** |

### Par développeur

- **1 développeur DevOps**: 5 jours (séquentiel)
- **2 développeurs** (1 DevOps + 1 Doc): 3 jours (parallèle)

### Hypothèses

- Développeur familier avec Docker et Docker Compose
- Docker Desktop déjà installé
- Accès aux images Docker (pas de restrictions réseau)
- Pas de problèmes de compatibilité OS

---

## Notes d'implémentation

### Stack technique

**Infrastructure**:
- Docker Engine 20.10+
- Docker Compose 2.0+
- PostgreSQL 15 avec pgvector
- Redis 7.0+
- Python 3.11
- Node 20

**Services**:
- Django 4.2 + DRF
- React 18 + Vite
- Celery 5.3
- Celery Beat

### Patterns et conventions

**Naming Convention**:
- Services: lowercase, descriptif (db, redis, backend, frontend, worker, scheduler)
- Volumes: prefixé avec le nom du projet (veille_postgres_data)
- Networks: suffixé avec _network

**File Structure**:
```
project/
├── docker-compose.yml
├── .env.backend
├── .env.frontend
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── ...
└── scripts/
    ├── init-db.sh
    ├── quick-start.sh
    └── test-environment.sh
```

---

## Risques et points d'attention

### Risques identifiés

1. **Compatibilité pgvector**
   - **Impact**: Élevé - Sans pgvector, le système de recommandation ne fonctionne pas
   - **Mitigation**: Utiliser l'image officielle pgvector/pgvector:pg15

2. **Performance en développement**
   - **Impact**: Moyen - Hot reload peut être lent sur Windows/Mac
   - **Mitigation**: Utiliser des volumes anonymes pour node_modules, optimiser .dockerignore

3. **Gestion des secrets**
   - **Impact**: Élevé - Risque de commit de secrets
   - **Mitigation**: .gitignore strict, documentation claire, utiliser .env.example

4. **Espace disque**
   - **Impact**: Moyen - Les images et volumes peuvent consommer beaucoup d'espace
   - **Mitigation**: Nettoyer régulièrement avec `docker system prune`

### Points critiques

**Sécurité**:
- Ne jamais commit les fichiers .env
- Changer tous les passwords par défaut
- Utiliser des users non-root dans les conteneurs
- Limiter les ports exposés

**Performance**:
- Utiliser des volumes nommés pour PostgreSQL et Redis
- Ne pas monter node_modules via volume sur Windows/Mac
- Configurer les healthchecks pour éviter les requêtes avant que les services soient prêts

**Compatibilité**:
- Tester sur Windows, Mac, et Linux
- Documenter les différences de comportement (notamment permissions)
- Fournir des scripts compatibles multi-plateformes

---

## Checklist de mise en production

Avant de considérer cette User Story comme terminée:

- [ ] Tous les services démarrent sans erreur
- [ ] Les healthchecks passent
- [ ] pgvector est installé et fonctionnel
- [ ] Celery worker et beat fonctionnent
- [ ] Le hot reload fonctionne (backend et frontend)
- [ ] Le script quick-start.sh fonctionne de bout en bout
- [ ] La documentation est complète
- [ ] Le troubleshooting guide couvre les problèmes courants
- [ ] Les tests d'environnement passent (test-environment.sh)
- [ ] Au moins 2 développeurs ont testé le setup sur leur machine

---

**Prochaines étapes**:
Une fois l'environnement Docker opérationnel, l'équipe peut commencer l'implémentation des User Stories fonctionnelles en commençant par le Bloc 1 (Authentication).
