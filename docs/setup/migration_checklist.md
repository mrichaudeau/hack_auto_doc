# Migration Verification Checklist

Use this checklist after applying migrations to verify everything is working correctly. This verification process should take less than 2 minutes to complete.

## Quick Reference

Run through all checks in order. If any check fails, see the [Troubleshooting Guide](./troubleshooting.md#database-migrations) for resolution steps.

---

## Pre-Flight Checks

Before verifying migrations, ensure all required services are running and healthy.

- [ ] **Database service running**
  ```bash
  docker-compose ps db
  # Status should show "Up (healthy)"
  ```

- [ ] **Backend service running**
  ```bash
  docker-compose ps backend
  # Status should show "Up (healthy)"
  ```

- [ ] **Database accepts connections**
  ```bash
  docker-compose exec db pg_isready -U postgres
  # Should output: postgres:5432 - accepting connections
  ```

---

## Migration Verification

Verify that all migrations have been applied successfully and the database schema is correct.

- [ ] **All migrations applied**
  ```bash
  docker-compose exec backend python manage.py showmigrations
  # All items should show [X], no [ ] pending migrations
  ```
  **Expected output format:**
  ```
  admin
   [X] 0001_initial
   [X] 0002_logentry_remove_auto_add
   [X] 0003_logentry_add_action_flag_choices
  auth
   [X] 0001_initial
   ...
  core
   [X] 0001_enable_pgvector
  sessions
   [X] 0001_initial
  ```

- [ ] **pgvector extension enabled**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "SELECT extname, extversion FROM pg_extension WHERE extname='vector';"
  # Should return: vector | 0.5.1 (or later version)
  ```

- [ ] **Migration history recorded**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "SELECT COUNT(*) FROM django_migrations;"
  # Should return count > 0 (typically 15+ after initial setup)
  ```

- [ ] **Core app migration applied**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "SELECT app, name FROM django_migrations WHERE app='core';"
  # Should return: core | 0001_enable_pgvector
  ```

---

## Functional Tests

Test database connectivity and vector operations to ensure everything is functioning correctly.

- [ ] **Database connection works**
  ```bash
  docker-compose exec backend python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('Connected')"
  # Should print: Connected
  ```

- [ ] **Vector type available**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "SELECT '[1,2,3]'::vector;"
  # Should return vector representation: [1,2,3]
  ```

- [ ] **Vector operations work**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "SELECT '[1,0,0]'::vector <=> '[0,1,0]'::vector AS cosine_distance;"
  # Should return a numeric distance value (e.g., 1.414213...)
  ```

- [ ] **Django can query database**
  ```bash
  docker-compose exec backend python manage.py shell -c "from django.contrib.auth.models import User; print(f'User count: {User.objects.count()}')"
  # Should print: User count: 0 (or higher if users created)
  ```

---

## Optional Verification Commands

These additional checks are useful for debugging but not required for standard verification.

- [ ] **Check migration plan**
  ```bash
  docker-compose exec backend python manage.py showmigrations --plan
  # Shows migration order and dependencies
  ```

- [ ] **Verify database name and user**
  ```bash
  docker-compose exec db psql -U postgres -c "\l veille_tech"
  # Should show database exists with correct owner
  ```

- [ ] **List all extensions**
  ```bash
  docker-compose exec db psql -U postgres -d veille_tech -c "\dx"
  # Should show vector extension among others (plpgsql, etc.)
  ```

---

## Troubleshooting

If any check fails, refer to the appropriate troubleshooting section:

### Quick Fixes

**Service not running:**
```bash
# Start all services
docker-compose up -d

# Or start specific service
docker-compose up -d db
docker-compose up -d backend
```

**Pending migrations:**
```bash
# Apply all pending migrations
docker-compose exec backend python manage.py migrate
```

**Database connection refused:**
```bash
# Wait for database to be healthy (may take 5-10 seconds)
docker-compose ps db

# Check database logs
docker-compose logs db
```

### Detailed Troubleshooting

For more complex issues, see:
- [Migration Troubleshooting Guide](./troubleshooting.md#database-migrations) - Common migration errors and solutions
- [Database Setup Guide](./00_setup_local_docker.md#database-migrations) - Complete migration workflow documentation

---

## Checklist Summary

| Category | Checks | Expected Time |
|----------|--------|---------------|
| Pre-Flight | 3 checks | ~15 seconds |
| Migration Verification | 4 checks | ~30 seconds |
| Functional Tests | 4 checks | ~45 seconds |
| **Total** | **11 checks** | **~90 seconds** |

**Success Criteria:** All required checks (not optional) show green/passing status.

---

## Next Steps

After successful verification:

1. **Create superuser** (if not already created):
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

2. **Access admin interface**: http://localhost:8000/admin/

3. **Continue with setup**: Return to [Local Setup Guide](./00_setup_local_docker.md) for next steps

---

## Notes

- This checklist assumes default configuration from `.env.backend.example`
- If using custom database names or users, adjust commands accordingly
- The pgvector version may vary (0.5.1, 0.6.0, etc.) - any version is acceptable
- All commands should complete within 2-3 seconds; timeouts indicate service issues
