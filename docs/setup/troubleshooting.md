# Troubleshooting Guide

This guide provides solutions to common issues encountered during development and deployment of the AI-powered Technology Watch Platform.

## Table of Contents

- [Database Migrations](#database-migrations)
- [Docker Services](#docker-services)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Database Migrations

This section covers common issues encountered when working with Django migrations and the PostgreSQL database with pgvector extension.

### Issue 1: Database Connection Failed

**Symptom:**
```
django.db.utils.OperationalError: could not connect to server: Connection refused
    Is the server running on host "db" (172.18.0.2) and accepting
    TCP/IP connections on port 5432?
```

**Cause:** Database service is not running, not healthy, or network connectivity issue between backend and database containers.

**Resolution:**
```bash
# 1. Check database service status
docker-compose ps db

# 2. If not running, start the database service
docker-compose up -d db

# 3. Wait for health check to pass (5-10 seconds)
docker-compose logs db | grep "database system is ready"

# Expected output: "database system is ready to accept connections"

# 4. Verify database is healthy
docker-compose ps db
# Status should show "healthy"

# 5. Retry migration command
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Always start the database service first and wait for health check
- Use `depends_on` with `service_healthy` condition in docker-compose.yml
- Check database logs regularly for errors: `docker-compose logs -f db`

---

### Issue 2: pgvector Extension Permission Denied

**Symptom:**
```
django.db.utils.ProgrammingError: permission denied to create extension "vector"
HINT: Must be superuser to create this extension.
```

**Cause:** The database user specified in `.env.backend` does not have SUPERUSER privileges required to create PostgreSQL extensions.

**Resolution:**
```bash
# Option 1: Connect as postgres superuser and grant privileges
docker-compose exec db psql -U postgres -d veille_tech -c "ALTER USER veille_tech_user WITH SUPERUSER;"

# Option 2: Create extension as postgres user, then fake migration
docker-compose exec db psql -U postgres -d veille_tech -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify extension created
docker-compose exec db psql -U postgres -d veille_tech -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"

# Mark migration as applied without running it
docker-compose exec backend python manage.py migrate core 0001_enable_pgvector --fake

# Continue with remaining migrations
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Ensure database user in `.env.backend` has SUPERUSER privileges
- Use the `postgres` superuser for initial setup migrations
- Document required privileges in deployment guides

---

### Issue 3: Migration Conflict Detected

**Symptom:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory:
Migration admin.0001_initial is applied before its dependency core.0001_enable_pgvector on database 'default'.
```

**Cause:** Migrations were applied out of order, or migration history in `django_migrations` table is corrupted.

**Resolution:**
```bash
# Option 1: Fake the dependency migration (if already applied manually)
docker-compose exec backend python manage.py migrate core 0001_enable_pgvector --fake

# Option 2: Reset migration history (DEVELOPMENT ONLY - NO DATA LOSS)
# This only clears the tracking table, not actual schema
docker-compose exec db psql -U postgres -d veille_tech -c "DELETE FROM django_migrations WHERE app='core' AND name='0001_enable_pgvector';"
docker-compose exec backend python manage.py migrate core 0001_enable_pgvector --fake

# Option 3: Fresh database (CAUTION: DESTROYS ALL DATA)
docker-compose down -v
docker-compose up -d db
# Wait for database healthy
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Always check migration dependencies before creating new migrations
- Run `showmigrations` before and after applying migrations
- Test migrations on a fresh database before committing
- Never manually modify the `django_migrations` table in production

---

### Issue 4: Migration Timeout

**Symptom:**
```
django.db.utils.OperationalError: canceling statement due to statement timeout
CONTEXT: SQL statement "CREATE INDEX CONCURRENTLY idx_report_embedding..."
```

**Cause:** Migration contains long-running operations (large data transformation, index creation) that exceed the default statement timeout (typically 30-60 seconds).

**Resolution:**
```bash
# 1. Increase statement timeout temporarily for the database
docker-compose exec db psql -U postgres -d veille_tech -c "ALTER DATABASE veille_tech SET statement_timeout = '600s';"

# 2. Retry the migration
docker-compose exec backend python manage.py migrate

# Expected output: Migration completes successfully

# 3. Reset timeout to default (optional)
docker-compose exec db psql -U postgres -d veille_tech -c "ALTER DATABASE veille_tech RESET statement_timeout;"

# Verify timeout reset
docker-compose exec db psql -U postgres -d veille_tech -c "SHOW statement_timeout;"
```

**Alternative approach for index creation:**
```bash
# If timeout occurs during index creation, create index manually without timeout
docker-compose exec db psql -U postgres -d veille_tech

SET statement_timeout = '0';  -- No timeout
CREATE INDEX CONCURRENTLY idx_report_embedding ON reports USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
\q

# Then fake the migration
docker-compose exec backend python manage.py migrate app_name 000X_migration_name --fake
```

**Prevention:**
- Split large data migrations into smaller batches
- Use `RunPython` with batch processing for data transformations
- Create indexes with `CONCURRENTLY` option to avoid table locks
- Test migrations with production-scale data volumes

---

### Issue 5: pgvector Extension Not Found

**Symptom:**
```
django.db.utils.ProgrammingError: type "vector" does not exist
LINE 1: ...rt_embeddings" ADD COLUMN "embedding" vector(1536) NOT NULL
```

**Cause:** Migration attempted to create a vector column before the pgvector extension was enabled in the database.

**Resolution:**
```bash
# 1. Enable pgvector extension manually
docker-compose exec db psql -U postgres -d veille_tech -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Verify extension is enabled
docker-compose exec db psql -U postgres -d veille_tech -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"

# Expected output:
#  extname | extversion
# ---------+------------
#  vector  | 0.5.1

# 3. Mark the pgvector migration as applied (if migration exists)
docker-compose exec backend python manage.py migrate core 0001_enable_pgvector --fake

# 4. Continue with remaining migrations
docker-compose exec backend python manage.py migrate

# 5. Test vector operations
docker-compose exec db psql -U postgres -d veille_tech -c "SELECT '[1,2,3]'::vector;"
```

**Prevention:**
- Ensure `core.0001_enable_pgvector` migration is listed as a dependency in all migrations that use vector fields
- Always apply migrations in order: `python manage.py migrate`
- Verify pgvector extension before creating models with VectorField
- Add migration dependency in models:
  ```python
  class Migration(migrations.Migration):
      dependencies = [
          ('core', '0001_enable_pgvector'),
          # ... other dependencies
      ]
  ```

---

### Issue 6: Migration History Out of Sync

**Symptom:**
```
django.db.migrations.exceptions.NodeNotFoundError:
Migration core.0002_auto_20250104_1530 dependencies reference nonexistent parent node ('core', '0001_initial')
```

**Cause:** Migration files exist in code but are not recorded in the `django_migrations` table, or vice versa.

**Resolution:**
```bash
# 1. Check what migrations are recorded in database
docker-compose exec db psql -U postgres -d veille_tech -c "SELECT app, name FROM django_migrations WHERE app='core' ORDER BY applied;"

# 2. Check what migration files exist in code
ls backend/apps/core/migrations/

# 3. Identify missing migrations and fake them if already applied
docker-compose exec backend python manage.py showmigrations core

# If migration shows [ ] but schema already exists, fake it:
docker-compose exec backend python manage.py migrate core 0001_initial --fake

# 4. Apply remaining migrations normally
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Always commit migration files with model changes
- Pull latest migrations before creating new ones
- Use version control to track migration history
- Run `makemigrations` and `migrate` together in development

---

### Issue 7: Duplicate Extension Creation

**Symptom:**
```
django.db.utils.ProgrammingError: extension "vector" already exists
```

**Cause:** Attempting to create pgvector extension when it's already enabled.

**Resolution:**
```bash
# This is usually safe to ignore. Verify extension exists:
docker-compose exec db psql -U postgres -d veille_tech -c "SELECT extname FROM pg_extension WHERE extname='vector';"

# If migration fails, fake it since extension already exists
docker-compose exec backend python manage.py migrate core 0001_enable_pgvector --fake

# Continue with other migrations
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Always use `CREATE EXTENSION IF NOT EXISTS` in migration SQL
- Check for extension existence before creating
- The provided migration already uses `IF NOT EXISTS` clause

---

### Issue 8: Cannot Roll Back pgvector Migration

**Symptom:**
```
django.db.utils.ProgrammingError: cannot drop extension vector because other objects depend on it
DETAIL: column embedding in table reports depends on type vector
```

**Cause:** Attempting to drop pgvector extension while tables with vector columns still exist.

**Resolution:**
```bash
# Option 1: Roll back all dependent migrations first
# Check which migrations use vector fields
docker-compose exec backend python manage.py showmigrations

# Roll back each app that uses vector fields
docker-compose exec backend python manage.py migrate reports zero
docker-compose exec backend python manage.py migrate recommendations zero

# Then roll back pgvector extension
docker-compose exec backend python manage.py migrate core zero

# Option 2: Manual cleanup (if migrations fail)
docker-compose exec db psql -U postgres -d veille_tech

# Drop all tables with vector columns
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS recommendations CASCADE;

# Drop extension
DROP EXTENSION IF EXISTS vector CASCADE;

\q

# Reset migration history
docker-compose exec db psql -U postgres -d veille_tech -c "DELETE FROM django_migrations;"

# Reapply all migrations
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Rarely roll back the pgvector migration in production
- If needed, roll back dependent apps first
- Consider forward fixes instead of rollback
- Test rollback procedures in development environment

---

## Platform-Specific Issues

### Windows (Docker Desktop with WSL2)

#### Issue: Slow Migration Performance

**Symptom:** Migrations take 5-10x longer than expected, especially with large data transformations.

**Cause:** File system performance degradation when project files are on Windows filesystem (C:\) instead of WSL2 filesystem.

**Resolution:**
```bash
# 1. Move project to WSL2 filesystem
# Open WSL2 terminal
cd /home/your-username/
git clone [REPO_URL]
cd project

# 2. Run Docker commands from WSL2
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Always work from WSL2 filesystem: `/home/username/`
- Avoid Windows paths: `C:\Users\...` or `/mnt/c/...`
- Use WSL2 terminal for all Docker operations

#### Issue: Line Ending Errors in Shell Scripts

**Symptom:**
```
/bin/bash^M: bad interpreter: No such file or directory
```

**Cause:** Git converted LF to CRLF line endings on Windows.

**Resolution:**
```bash
# Configure Git to use LF line endings
git config --global core.autocrlf input
git config --global core.eol lf

# Re-clone repository or fix files
git rm --cached -r .
git reset --hard
```

---

### macOS (Docker Desktop)

#### Issue: Connection Timeout During Migration

**Symptom:**
```
django.db.utils.OperationalError: could not connect to server: Operation timed out
```

**Cause:** Docker Desktop resource limits (CPU/Memory) too low for database operations.

**Resolution:**
```bash
# 1. Open Docker Desktop settings
# 2. Navigate to Resources
# 3. Increase memory allocation to at least 4GB (recommended: 8GB)
# 4. Increase CPU cores to at least 4
# 5. Click "Apply & Restart"

# 6. Verify resources after restart
docker info | grep -E "CPUs|Total Memory"

# 7. Retry migration
docker-compose up -d
docker-compose exec backend python manage.py migrate
```

**Prevention:**
- Allocate sufficient resources from the start
- Monitor resource usage: `docker stats`
- Close unused containers to free resources

#### Issue: Volume Mounting Errors (M1/M2 Macs)

**Symptom:**
```
Error response from daemon: failed to create shim: OCI runtime create failed
```

**Cause:** ARM architecture incompatibility with some Docker images.

**Resolution:**
```yaml
# Add platform specification in docker-compose.yml
services:
  db:
    platform: linux/amd64
    image: ankane/pgvector:latest
```

**Prevention:**
- Use multi-architecture images when available
- Specify `platform: linux/amd64` for x86-only images
- Test on ARM-compatible alternatives first

---

### Linux (Native Docker)

#### Issue: Permission Errors Accessing Database Files

**Symptom:**
```
initdb: could not access directory "/var/lib/postgresql/data": Permission denied
```

**Cause:** User/group ID mismatch between host and container for mounted volumes.

**Resolution:**
```bash
# Option 1: Use named volumes instead of bind mounts (recommended)
# Already configured in docker-compose.yml with postgres_data volume

# Option 2: Fix permissions for bind mount
sudo chown -R 999:999 ./volumes/postgres_data
# (999 is the postgres user ID in the container)

# Option 3: Run container as current user (not recommended for postgres)
```

**Prevention:**
- Always use named volumes for database data: `postgres_data`
- Avoid bind mounting database directories
- Document UID/GID requirements if bind mounts are necessary

#### Issue: Docker Command Requires Sudo

**Symptom:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Cause:** Current user not in `docker` group.

**Resolution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in for changes to take effect
# Or use: newgrp docker

# Verify access
docker ps
```

**Prevention:**
- Add users to docker group during initial setup
- Document group membership requirement

---

## Additional Resources

- **Migration Workflow Guide:** [00_setup_local_docker.md](./00_setup_local_docker.md#database-migrations)
- **Migration Verification Checklist:** [migration_checklist.md](./migration_checklist.md)
- **Django Migrations Documentation:** https://docs.djangoproject.com/en/5.0/topics/migrations/
- **pgvector Documentation:** https://github.com/pgvector/pgvector
- **Docker Compose Documentation:** https://docs.docker.com/compose/

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check logs:**
   ```bash
   docker-compose logs db
   docker-compose logs backend
   ```

2. **Verify service health:**
   ```bash
   docker-compose ps
   ```

3. **Test database connection:**
   ```bash
   docker-compose exec backend python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Connected')"
   ```

4. **Review migration history:**
   ```bash
   docker-compose exec backend python manage.py showmigrations
   docker-compose exec db psql -U postgres -d veille_tech -c "SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 10;"
   ```

5. **Consult the development team** or open an issue in the project repository with:
   - Complete error message
   - Output of diagnostic commands above
   - Platform and Docker version: `docker --version`
   - Steps to reproduce the issue
