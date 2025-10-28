# User Story: Database Initialization and Migrations

**Story ID:** US-9
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** automated database schema setup on first run
**So that** I can start development without manual SQL commands

## Description

This User Story establishes the automated database initialization and migration system that creates and updates the PostgreSQL schema for the AI-powered Technology Watch Platform. Using Django's migration framework, developers can apply schema changes incrementally without writing SQL manually.

The system must handle the initial database setup (creating all tables, indexes, constraints) as well as ongoing schema evolution as new features are developed. A critical requirement is enabling the pgvector extension, which must be activated before any tables with vector columns are created.

The migration system provides version control for database schema, enabling developers to track changes, roll back if needed, and ensure consistency across development environments. Each migration is recorded in the database, preventing duplicate applications.

Success means developers can run a single command to set up a fresh database or apply pending migrations, with clear error messages if issues occur.

## Acceptance Criteria

### Functional Criteria
- [ ] Django migrations run successfully via documented command
- [ ] pgvector extension enabled in PostgreSQL database
- [ ] All Django model tables created correctly with proper schema
- [ ] Initial data fixtures loaded (if any seed data required)
- [ ] Migration history tracked in `django_migrations` table
- [ ] Command: `docker-compose exec backend python manage.py migrate` applies all migrations
- [ ] Migration failures display clear error messages with resolution guidance
- [ ] Subsequent migrations can be applied incrementally without issues

### Technical Criteria
- [ ] pgvector extension enabled before any vector column migrations
- [ ] Migrations located in `backend/apps/*/migrations/` directories
- [ ] Custom migration to enable pgvector: `CREATE EXTENSION IF NOT EXISTS vector;`
- [ ] Zero-downtime migration strategy for production readiness
- [ ] Migration dependencies properly ordered (avoid circular dependencies)
- [ ] `--check` flag available to verify migrations without applying
- [ ] Rollback capability via `python manage.py migrate <app> <migration_number>`

### UI/UX Criteria (if applicable)
- Not applicable for database migrations

### Performance Criteria
- [ ] Initial migration (all tables) completes within 30 seconds
- [ ] Individual incremental migrations complete within 5 seconds (typical)
- [ ] Large data migrations (if any) provide progress indicators
- [ ] Migration execution does not block other database connections unnecessarily

## Technical Details

### Components Affected
- `backend/apps/*/migrations/` (migration files for each Django app)
- `backend/apps/core/migrations/0001_enable_pgvector.py` (custom migration for pgvector)
- `backend/veille_tech/settings/base.py` (database configuration)
- PostgreSQL database (schema tables, indexes, constraints)
- `docs/setup/00_setup_local_docker.md` (migration instructions)

### API Changes
- None (database schema only)

### Database Changes
- **Core infrastructure tables:**
  - `django_migrations` (migration history)
  - `django_content_type` (Django content types)
  - `auth_user`, `auth_group`, `auth_permission` (Django auth)

- **Application tables:** (created in feature-specific user stories)
  - Users, profiles (Bloc 1: Authentication)
  - Subjects, subscriptions (Bloc 2: Subscriptions)
  - Reports, embeddings (Bloc 3: AI Pipeline)
  - Cost tracking (Bloc 6: FinOps)

- **Extensions:**
  - `vector` (pgvector for embedding storage)

### External Integrations
- PostgreSQL database connection

## Implementation Notes

### Suggested Approach

1. **Create initial Django app structure:**
   - Create core app: `python manage.py startapp core`
   - Register app in `INSTALLED_APPS`

2. **Create custom migration to enable pgvector:**
   - Create empty migration: `python manage.py makemigrations --empty core`
   - Edit migration file:
     ```python
     from django.db import migrations

     class Migration(migrations.Migration):
         dependencies = []

         operations = [
             migrations.RunSQL(
                 sql='CREATE EXTENSION IF NOT EXISTS vector;',
                 reverse_sql='DROP EXTENSION IF EXISTS vector;'
             )
         ]
     ```

3. **Run initial migrations:**
   - Document command: `docker-compose exec backend python manage.py migrate`
   - Applies Django core migrations (auth, contenttypes, sessions)
   - Applies custom pgvector migration
   - Creates all initial tables

4. **Verify migrations applied:**
   - Check migration status: `python manage.py showmigrations`
   - Query database: `SELECT * FROM django_migrations;`
   - Test pgvector: `SELECT vector('[1,2,3]');`

5. **Create management command for one-time setup (optional):**
   - Command: `python manage.py setup_dev_environment`
   - Combines migrate + createsuperuser + load fixtures
   - Simplifies onboarding for new developers

### Technical Considerations

**Performance:**
- Migrations run sequentially (transaction-safe)
- Large data migrations may need batching to avoid long locks
- Consider using `--fake` flag for migrations in production (schema already applied)

**Security:**
- pgvector extension requires database superuser privileges initially
- Production migrations should be reviewed before deployment
- Sensitive data migrations (e.g., password hashing changes) need special handling

**Scalability:**
- Django migrations scale well for schema changes
- Large data migrations may need custom scripts outside migration framework
- Zero-downtime migrations require careful planning (additive changes first)

**Backward Compatibility:**
- Migrations should be reversible where possible (provide reverse_sql)
- Avoid destructive changes without backup strategy
- Test rollback process in development

### Known Challenges

**Challenge:** pgvector extension requires superuser to enable
**Solution:** Use PostgreSQL superuser for initial setup; document privilege requirements

**Challenge:** Migration order dependencies across apps
**Solution:** Explicitly define migration dependencies; test migration order

**Challenge:** Long-running migrations may timeout
**Solution:** Configure appropriate timeout values; split large migrations into smaller steps

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-2: Database Service with Vector Support (database must be running)
- US-4: Django Backend API Service (backend service required to run migrations)

### Blocks
- US-10: Superuser Creation for Admin Access (requires migration to create auth tables)
- Feature user stories that add database tables (Blocs 1-6)

## Test Scenarios

### Happy Path
1. Developer starts fresh environment: `docker-compose up -d`
2. Database service starts successfully
3. Backend service starts successfully
4. Developer runs: `docker-compose exec backend python manage.py migrate`
5. Migration output shows:
   ```
   Operations to perform:
     Apply all migrations: admin, auth, contenttypes, core, sessions
   Running migrations:
     Applying contenttypes.0001_initial... OK
     Applying auth.0001_initial... OK
     Applying core.0001_enable_pgvector... OK
     ...
   ```
6. All migrations applied successfully
7. Developer verifies: `docker-compose exec backend python manage.py showmigrations`
8. All migrations show `[X]` (applied)

### Alternative Paths
1. Developer checks migration status before applying:
   ```bash
   docker-compose exec backend python manage.py showmigrations
   ```
2. Sees list of pending migrations (no `[X]`)
3. Runs migrate command
4. Verifies all migrations now applied

### Error Scenarios
1. **Database not accessible:** PostgreSQL service not running
   - Expected: Migration command fails with connection error
   - Output: "OperationalError: could not connect to server"
   - Resolution: Start database service first

2. **pgvector extension cannot be enabled:** Insufficient privileges
   - Expected: Migration fails with permission error
   - Output: "ERROR: permission denied to create extension"
   - Resolution: Ensure database user has superuser privileges or pre-enable extension

3. **Migration conflict:** Two developers create migrations for same app concurrently
   - Expected: Migration conflict detected
   - Output: "Conflicting migrations detected"
   - Resolution: Merge migrations or regenerate

4. **Failed migration leaves partial state:** Error during migration execution
   - Expected: Transaction rolled back (for DDL operations)
   - Migration marked as not applied
   - Resolution: Fix migration code and re-run

### Edge Cases
1. **Re-running migrations:** Developer runs migrate command multiple times
   - Expected: Django detects already-applied migrations
   - Output: "No migrations to apply"
   - Idempotent operation—safe to re-run

2. **Migrating with existing data:** Developer applies migration that modifies existing table
   - Expected: Migration handles existing data gracefully
   - Use data migrations if transformation needed

## UI/UX Specifications

Not applicable for database migrations.

## Security Considerations

- Database superuser privileges required for enabling extensions
- Production migrations should be reviewed and tested in staging first
- Sensitive data migrations (e.g., encryption) need special handling
- Migration files committed to Git (reviewed in code review)
- No secrets or sensitive data hardcoded in migrations

## Performance Requirements

- **Initial Migration Time:** All migrations complete within 30 seconds (P95)
- **Incremental Migration Time:** Single migration completes within 5 seconds (typical)
- **Database Locking:** Minimize lock time for production migrations
- **Rollback Time:** Rollback migration completes within 10 seconds

## Accessibility Requirements

Not applicable for database migrations.

## Definition of Done

- [ ] pgvector extension enabled via custom migration
- [ ] All Django core migrations applied (auth, contenttypes, sessions)
- [ ] Migration command documented: `docker-compose exec backend python manage.py migrate`
- [ ] Migration history tracked in `django_migrations` table
- [ ] Verification command documented: `python manage.py showmigrations`
- [ ] Error handling provides clear messages for common issues
- [ ] Rollback capability tested and documented
- [ ] Code reviewed by tech lead
- [ ] Tested on fresh database (no existing schema)
- [ ] Tested with existing database (idempotent)
- [ ] All acceptance criteria verified
- [ ] Documentation updated with migration workflow
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
- [ ] Should we create a management command that combines migrate + fixtures + superuser?
- [ ] Do we need a CI/CD check to ensure all migrations are applied before tests?
- [ ] Should we implement squash migrations strategy for older migrations?

### Assumptions
- Database user has sufficient privileges to create extensions
- Developers run migrations locally after pulling new code
- Migration rollback rarely needed in development (forward-only preferred)

### Out of Scope
- Zero-downtime migration strategy for production (handled in deployment planning)
- Advanced migration tools (django-migration-linter, etc.)
- Automatic migration on container startup (requires manual trigger)
- Migration testing framework (manual testing sufficient)

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-2: Database Service with Vector Support (depends on this)
- US-4: Django Backend API Service (depends on this)
- US-10: Superuser Creation for Admin Access (blocked by this)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
