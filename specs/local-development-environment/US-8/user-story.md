# User Story: Environment Configuration Management

**Story ID:** US-8
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 1 Story Point
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** secure management of API keys and configuration
**So that** I can run the application without exposing secrets in code

## Description

This User Story establishes a secure and developer-friendly system for managing environment-specific configuration, API keys, and secrets. The platform requires multiple external API keys (Google AI, Firecrawl), database credentials, JWT secrets, and service URLs that must be configured without committing sensitive data to version control.

The solution uses environment files (.env) that are loaded by backend and frontend services at runtime. Example template files (.env.example) are committed to the repository, providing developers with a clear reference for required configuration without exposing actual secrets.

This approach follows the Twelve-Factor App methodology for configuration management, ensuring that the same codebase can run in different environments (local, staging, production) with only configuration changes.

Success means developers can configure their local environment by copying example files and filling in their API keys, with clear error messages if required variables are missing.

## Acceptance Criteria

### Functional Criteria
- [ ] Example files provided: `env.backend.example`, `env.frontend.example`
- [ ] Setup instructions guide copying examples to `.env.backend`, `.env.frontend`
- [ ] Backend `.env` includes: database URL, Redis URL, JWT secret, LLM API keys, Firecrawl API key
- [ ] Frontend `.env` includes: API URL, environment mode
- [ ] Actual `.env` files excluded from version control (in .gitignore)
- [ ] Services load environment variables correctly on startup
- [ ] Missing required variables cause clear error messages on service startup
- [ ] Documentation lists all required and optional variables with descriptions

### Technical Criteria
- [ ] Backend uses `python-decouple` or `django-environ` for environment loading
- [ ] Frontend uses `.env` files with `dotenv` (Vite) or built-in support (CRA)
- [ ] Required backend vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GOOGLE_AI_API_KEY`, `FIRECRAWL_API_KEY`
- [ ] Required frontend vars: `VITE_API_URL` or `REACT_APP_API_URL`
- [ ] .gitignore includes: `.env`, `.env.backend`, `.env.frontend`, `.env.local`
- [ ] docker-compose.yml references `.env.backend` and `.env.frontend` via `env_file` directive
- [ ] Example files include comments explaining each variable

### UI/UX Criteria (if applicable)
- Not applicable for configuration management

### Performance Criteria
- [ ] Environment variable loading adds < 100ms to service startup time
- [ ] No performance impact during runtime (variables loaded once at startup)

## Technical Details

### Components Affected
- `.env.backend` (new file, ignored by Git)
- `.env.frontend` (new file, ignored by Git)
- `env.backend.example` (new file, committed to Git)
- `env.frontend.example` (new file, committed to Git)
- `.gitignore` (updated to exclude .env files)
- `backend/veille_tech/settings/base.py` (environment loading logic)
- `frontend/vite.config.js` or `frontend/.env` (frontend environment loading)
- `docker-compose.yml` (env_file references)
- `docs/setup/00_setup_local_docker.md` (setup instructions)

### API Changes
- None (configuration infrastructure only)

### Database Changes
- None (database credentials configured via environment)

### External Integrations
- Google AI API (API key required)
- Firecrawl API (API key required)

## Implementation Notes

### Suggested Approach

1. **Create backend example file (env.backend.example):**
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://postgres:postgres@db:5432/veille_tech_db

   # Redis Configuration
   REDIS_URL=redis://redis:6379/1
   CELERY_BROKER_URL=redis://redis:6379/0

   # Django Configuration
   SECRET_KEY=your-secret-key-here-change-in-production
   DEBUG=True
   ALLOWED_HOSTS=*

   # JWT Configuration
   JWT_SECRET=your-jwt-secret-here-change-in-production

   # AI API Keys
   GOOGLE_AI_API_KEY=your-google-ai-api-key-here

   # Firecrawl API Key
   FIRECRAWL_API_KEY=your-firecrawl-api-key-here

   # Optional: Email Configuration (for development)
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   ```

2. **Create frontend example file (env.frontend.example):**
   ```bash
   # API Configuration (Vite)
   VITE_API_URL=http://localhost:8000

   # Or for Create React App:
   # REACT_APP_API_URL=http://localhost:8000

   # Environment Mode
   NODE_ENV=development
   ```

3. **Configure backend to load environment variables:**
   - Install `python-decouple` or `django-environ`
   - In `settings/base.py`:
     ```python
     from decouple import config

     DATABASE_URL = config('DATABASE_URL')
     REDIS_URL = config('REDIS_URL')
     GOOGLE_AI_API_KEY = config('GOOGLE_AI_API_KEY')
     ```
   - Raise clear errors if required variables missing

4. **Configure frontend to load environment variables:**
   - Vite automatically loads `.env` files
   - Access via `import.meta.env.VITE_API_URL`
   - CRA automatically loads `.env` files
   - Access via `process.env.REACT_APP_API_URL`

5. **Update .gitignore:**
   ```
   # Environment files
   .env
   .env.backend
   .env.frontend
   .env.local
   .env.*.local
   ```

6. **Update docker-compose.yml:**
   ```yaml
   backend:
     env_file:
       - .env.backend

   frontend:
     env_file:
       - .env.frontend
   ```

7. **Document setup process:**
   - Add step to setup guide: "Copy example files and fill in API keys"
   - Include instructions for obtaining API keys (links to Google AI, Firecrawl)

### Technical Considerations

**Performance:**
- Environment variables loaded once at startup (no runtime overhead)
- Large number of variables does not impact performance significantly

**Security:**
- .env files never committed to Git (verified in CI/CD)
- Example files contain placeholder values, not real secrets
- Production environments use secure secret management (AWS Secrets Manager, Azure Key Vault)
- JWT secrets should be randomly generated (provide generation script)

**Scalability:**
- Same configuration pattern scales to production deployments
- Configuration-as-code enables infrastructure-as-code practices
- Easy to add new variables as features expand

**Backward Compatibility:**
- python-decouple and django-environ support default values for optional variables
- Frontend environment variables follow standard Vite/CRA conventions

### Known Challenges

**Challenge:** Developers forget to copy .env.example files
**Solution:** Provide clear setup instructions; consider startup script that checks for .env files

**Challenge:** API keys may be invalid or expired
**Solution:** Implement health checks that validate API connectivity; provide clear error messages

**Challenge:** Different developers have different API quotas/keys
**Solution:** Document that API keys are developer-specific; provide instructions for obtaining keys

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (services must load environment variables)

### Blocks
- US-2: Database Service with Vector Support (requires database credentials)
- US-3: Redis Broker and Cache Service (requires Redis URL)
- US-4: Django Backend API Service (requires backend environment)
- US-5: React Frontend SPA Service (requires frontend environment)
- US-6: Celery Worker Service for AI Pipeline (requires API keys)

## Test Scenarios

### Happy Path
1. Developer clones repository
2. Developer runs `cp env.backend.example .env.backend`
3. Developer runs `cp env.frontend.example .env.frontend`
4. Developer edits `.env.backend` and adds Google AI API key
5. Developer edits `.env.backend` and adds Firecrawl API key
6. Developer runs `docker-compose up`
7. Backend service starts successfully and loads all environment variables
8. Frontend service starts successfully and loads API URL
9. No error messages about missing configuration

### Alternative Paths
1. Developer uses provided script to generate JWT secret
2. Script outputs random secure secret
3. Developer copies secret to `.env.backend`
4. Backend starts with secure JWT configuration

### Error Scenarios
1. **Missing .env.backend file:** File not copied from example
   - Expected: Backend service fails to start
   - Logs show: "Error: .env.backend file not found"
   - Documentation provides resolution steps

2. **Missing required variable:** GOOGLE_AI_API_KEY not set
   - Expected: Backend starts but tasks fail when calling AI API
   - Logs show: "Error: GOOGLE_AI_API_KEY environment variable not set"
   - Clear error message with instructions to set variable

3. **Invalid database URL format:** Typo in DATABASE_URL
   - Expected: Backend fails database connection with clear error
   - Logs show: "OperationalError: could not parse DATABASE_URL"
   - Documentation provides correct format examples

4. **API key invalid:** GOOGLE_AI_API_KEY is incorrect
   - Expected: AI tasks fail with authentication error
   - Logs show: "API Error 401: Invalid API key"
   - Documentation provides link to obtain API key

### Edge Cases
1. **Environment variable with special characters:** Value contains quotes or spaces
   - Expected: Value correctly parsed by decouple/dotenv libraries
   - Proper escaping documented in example files

2. **Override with OS environment variables:** Developer sets env var in shell
   - Expected: Shell variable takes precedence over .env file
   - Documented behavior in setup guide

## UI/UX Specifications

Not applicable for configuration management.

## Security Considerations

- .env files excluded from version control (enforced via .gitignore)
- Example files never contain real secrets (placeholders only)
- API keys loaded from environment, never hardcoded in source
- JWT secrets randomly generated (provide generation utility)
- Database credentials configurable per environment
- Production deployments must use secure secret management systems
- Audit logs for configuration changes (if admin UI for config added later)

## Performance Requirements

- **Variable Loading Time:** < 100ms to load all environment variables at startup
- **Runtime Performance:** No impact (variables loaded once at startup)

## Accessibility Requirements

Not applicable for configuration management.

## Definition of Done

- [ ] env.backend.example created with all required variables documented
- [ ] env.frontend.example created with all required variables documented
- [ ] .gitignore updated to exclude .env files
- [ ] Backend configured to load environment variables with python-decouple or django-environ
- [ ] Frontend configured to load environment variables (Vite or CRA)
- [ ] docker-compose.yml references .env files via env_file directive
- [ ] Clear error messages implemented for missing required variables
- [ ] Documentation updated with setup instructions and variable descriptions
- [ ] JWT secret generation utility provided (optional)
- [ ] Code reviewed by tech lead
- [ ] Tested: Services start successfully with correct .env files
- [ ] Tested: Services fail gracefully with clear errors when .env missing
- [ ] All acceptance criteria verified
- [ ] No secrets committed to Git (verified)
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
- [ ] Should we provide a setup script that automatically copies .env.example files?
- [ ] Should we implement environment variable validation at startup?
- [ ] Do we need a centralized configuration file for shared values?

### Assumptions
- Developers have access to Google AI and Firecrawl API keys
- .env file pattern is familiar to developers (widely used standard)
- Different developers will use different API keys (not shared)

### Out of Scope
- Centralized secret management (AWS Secrets Manager, HashiCorp Vault)
- Dynamic configuration reloading (requires service restart)
- Configuration UI in Django Admin
- Encrypted environment files

## Related User Stories

- US-1: Docker Compose Service Orchestration (loads environment variables)
- US-2: Database Service with Vector Support (uses database credentials)
- US-4: Django Backend API Service (requires backend configuration)
- US-5: React Frontend SPA Service (requires frontend configuration)
- US-6: Celery Worker Service for AI Pipeline (requires API keys)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
