# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used in the Technology Watch Platform.

## Table of Contents

- [Backend Environment Variables (.env.backend)](#backend-environment-variables-envbackend)
  - [Database Configuration](#database-configuration)
  - [Redis Configuration](#redis-configuration)
  - [Django Settings](#django-settings)
  - [JWT Configuration](#jwt-configuration)
  - [AI/ML API Keys](#aiml-api-keys)
  - [Email Configuration](#email-configuration)
  - [Microsoft Entra ID / Azure AD SSO](#microsoft-entra-id--azure-ad-sso)
  - [Celery Configuration](#celery-configuration)
  - [Logging](#logging)
  - [Security Settings](#security-settings)
- [Frontend Environment Variables (.env.frontend)](#frontend-environment-variables-envfrontend)
  - [API Configuration](#api-configuration)
  - [Feature Flags](#feature-flags)
  - [Development Settings](#development-settings)
- [Security Best Practices](#security-best-practices)

---

## Backend Environment Variables (.env.backend)

### Database Configuration

PostgreSQL database connection settings using pgvector extension for vector embeddings.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `POSTGRES_USER` | Yes | String | `veille_tech_user` | PostgreSQL username | `veille_tech_user` |
| `POSTGRES_PASSWORD` | Yes | String | - | PostgreSQL password (min 16 chars) | `K7mP9nQr...` |
| `POSTGRES_DB` | Yes | String | `veille_tech_db` | Database name | `veille_tech_db` |
| `POSTGRES_HOST` | No | String | `db` | Database host (Docker service name) | `db` or `localhost` |
| `POSTGRES_PORT` | No | Integer | `5432` | PostgreSQL port | `5432` |
| `DB_CONN_MAX_AGE` | No | Integer | `600` | Connection pool max age (seconds) | `600` |
| `DATABASE_URL` | No | String | (constructed) | Full database connection string | `postgresql://user:pass@db:5432/dbname` |

**Notes:**
- Generate secure password with: `openssl rand -base64 24`
- `DATABASE_URL` is typically auto-constructed from individual variables
- Connection pooling improves performance for high-concurrency scenarios
- Port 5432 is NOT exposed to host for security (internal Docker network only)

### Redis Configuration

Redis configuration for Celery broker (DB 0) and application cache (DB 1).

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `REDIS_HOST` | No | String | `redis` | Redis host (Docker service name) | `redis` or `localhost` |
| `REDIS_PORT` | No | Integer | `6379` | Redis port | `6379` |
| `CELERY_BROKER_URL` | No | String | `redis://redis:6379/0` | Celery broker connection string (DB 0) | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | No | String | `redis://redis:6379/0` | Celery result backend connection string | `redis://redis:6379/0` |
| `REDIS_CACHE_URL` | No | String | `redis://redis:6379/1` | Django cache connection string (DB 1) | `redis://redis:6379/1` |

**Notes:**
- DB 0 is reserved for Celery task queuing
- DB 1 is reserved for Django caching (sessions, API responses)
- Memory limit: 256MB with LRU eviction policy
- Port 6379 is NOT exposed to host for security
- **Production**: Enable Redis AUTH and TLS encryption

### Django Settings

Core Django framework configuration.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `SECRET_KEY` | Yes | String | - | Django secret key (min 50 chars, alphanumeric) | `XyZ123abc...` (64 chars) |
| `DEBUG` | No | Boolean | `False` | Enable Django debug mode | `True` or `False` |
| `ALLOWED_HOSTS` | No | CSV | `localhost,127.0.0.1` | Allowed host headers for requests | `localhost,127.0.0.1,backend` |
| `CORS_ALLOWED_ORIGINS` | No | CSV | `http://localhost:3000` | CORS allowed origins | `http://localhost:3000,http://localhost:8080` |

**Notes:**
- Generate `SECRET_KEY` with: `python backend/scripts/generate_secrets.py`
- Never use `DEBUG=True` in production
- `ALLOWED_HOSTS` must include all domains serving the application
- CORS origins must include frontend URL for API access

### JWT Configuration

JSON Web Token authentication settings for API security.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `JWT_SECRET_KEY` | Yes | String | Falls back to `SECRET_KEY` | JWT signing secret (min 50 chars) | `AbC456xyz...` (64 chars) |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | No | Integer | `60` | Access token expiration (minutes) | `60` (1 hour) |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | No | Integer | `7` | Refresh token expiration (days) | `7` (1 week) |
| `JWT_ALGORITHM` | No | String | `HS256` | JWT signing algorithm | `HS256` |

**Notes:**
- Generate `JWT_SECRET_KEY` with: `python backend/scripts/generate_secrets.py`
- Use different secret than `SECRET_KEY` for defense in depth
- Access token lifetime should be short (15-60 minutes)
- Refresh token lifetime should be longer but still reasonable (7-30 days)
- Supported algorithms: HS256, HS384, HS512 (symmetric), RS256, RS384, RS512 (asymmetric)

### AI/ML API Keys

External API keys for AI services (Google Gemini, Firecrawl).

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `GOOGLE_AI_STUDIO_API_KEY` | Yes | String | - | Google AI Studio API key for Gemini models | `AIzaSy...` |
| `FIRECRAWL_API_KEY` | Yes | String | - | Firecrawl API key for web scraping | `fc-...` |

**Notes:**
- **Google AI Studio:** Get API key from [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
  - Used for: Gemini 2.5 Flash/Pro (synthesis, relevance), text-embedding-004 (embeddings)
  - Free tier: 60 requests/minute
  - Monitor usage in Google AI Studio console
- **Firecrawl:** Get API key from [https://firecrawl.dev/](https://firecrawl.dev/)
  - Used for: JavaScript-heavy web scraping, content extraction
  - Handles dynamic content rendering better than traditional scrapers
  - Monitor usage in Firecrawl dashboard
- Both services are REQUIRED for AI pipeline functionality

### Email Configuration

SMTP email configuration for notifications and user communications.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `EMAIL_BACKEND` | No | String | `django.core.mail.backends.console.EmailBackend` | Django email backend class | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | No | String | `localhost` | SMTP server hostname | `smtp.gmail.com` |
| `EMAIL_PORT` | No | Integer | `1025` | SMTP server port | `587` (TLS) or `465` (SSL) |
| `EMAIL_HOST_USER` | No | String | `` | SMTP authentication username | `noreply@example.com` |
| `EMAIL_HOST_PASSWORD` | No | String | `` | SMTP authentication password | `app-specific-password` |
| `EMAIL_USE_TLS` | No | Boolean | `False` | Use TLS encryption | `True` |
| `DEFAULT_FROM_EMAIL` | No | String | `noreply@techwatch.local` | Default sender email address | `noreply@example.com` |

**Notes:**
- Console backend (default) prints emails to console for local development
- For production, use SMTP backend with proper credentials
- Gmail requires "App Passwords" if 2FA is enabled
- Always use TLS (`EMAIL_USE_TLS=True`) for production
- Test email configuration with: `docker-compose exec backend python manage.py sendtestemail user@example.com`

### Microsoft Entra ID / Azure AD SSO

Optional Microsoft Entra ID (Azure AD) Single Sign-On integration.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `AZURE_AD_CLIENT_ID` | No | String | `` | Azure AD application (client) ID | `12345678-abcd-...` |
| `AZURE_AD_CLIENT_SECRET` | No | String | `` | Azure AD client secret | `AbC~123...` |
| `AZURE_AD_TENANT_ID` | No | String | `` | Azure AD tenant ID | `87654321-dcba-...` |
| `AZURE_AD_REDIRECT_URI` | No | String | `http://localhost:8000/accounts/azure/callback` | OAuth2 redirect URI | `http://localhost:8000/accounts/azure/callback` |

**Notes:**
- Leave all empty to disable SSO (only standard email/password authentication)
- Requires Azure AD app registration with "Web" platform
- Redirect URI must be registered in Azure AD app configuration
- Tenant ID can be found in Azure Portal > Azure Active Directory > Overview
- For multi-tenant apps, use `common` or `organizations` instead of tenant ID

### Celery Configuration

Celery worker and scheduler configuration for async task processing.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `CELERY_WORKER_CONCURRENCY` | No | Integer | `2` | Number of worker threads | `4` |
| `CELERY_TASK_TIME_LIMIT` | No | Integer | `3600` | Max task execution time (seconds) | `3600` (1 hour) |
| `CELERY_BEAT_SCHEDULE_ENABLED` | No | Boolean | `True` | Enable periodic task scheduling | `True` or `False` |

**Notes:**
- Concurrency should match CPU cores (typically 2-4 for local dev)
- Time limit prevents runaway tasks from blocking workers
- Beat scheduler runs recurring tasks (daily scraping, cleanup jobs)
- Monitor Celery with: `docker-compose logs -f worker` and `docker-compose logs -f scheduler`

### Logging

Application logging configuration.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `LOG_LEVEL` | No | String | `INFO` | Logging level | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

**Notes:**
- `DEBUG`: Verbose logging for development (not recommended for production)
- `INFO`: Standard informational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `CRITICAL`: Critical system failures
- Logs are output to console and captured by Docker

### Security Settings

Additional security configuration for production deployments.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `PASSWORD_HASHERS` | No | String | `django.contrib.auth.hashers.Argon2PasswordHasher` | Password hashing algorithm | `django.contrib.auth.hashers.Argon2PasswordHasher` |
| `CSRF_TRUSTED_ORIGINS` | No | CSV | `http://localhost:3000` | Trusted origins for CSRF protection | `http://localhost:3000,https://app.example.com` |
| `SESSION_COOKIE_SECURE` | No | Boolean | `False` | Send session cookies over HTTPS only | `True` (production) |
| `CSRF_COOKIE_SECURE` | No | Boolean | `False` | Send CSRF cookies over HTTPS only | `True` (production) |

**Notes:**
- Argon2 is recommended for production (more secure than PBKDF2)
- Set `*_SECURE=True` in production with HTTPS
- CSRF trusted origins must match frontend domain

---

## Frontend Environment Variables (.env.frontend)

### API Configuration

Backend API connection settings.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `VITE_API_URL` | Yes | String | `http://localhost:8000/api` | Backend API base URL (no trailing slash) | `http://localhost:8000/api` |

**Notes:**
- For Docker: use service name `backend` (e.g., `http://backend:8000/api`)
- For host development: use `localhost` (e.g., `http://localhost:8000/api`)
- Must NOT include trailing slash
- Must be prefixed with `VITE_` to be accessible in React code
- Access in code via: `import.meta.env.VITE_API_URL`

### Feature Flags

Optional feature toggles for conditional functionality.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `VITE_ENABLE_SSO` | No | Boolean | `false` | Enable Microsoft Entra ID SSO login button | `true` or `false` |
| `VITE_ENABLE_ANALYTICS` | No | Boolean | `false` | Enable analytics tracking | `true` or `false` |
| `VITE_DEBUG_MODE` | No | Boolean | `false` | Enable additional console logging | `true` or `false` |

**Notes:**
- Boolean values must be lowercase strings (`true`/`false`)
- Feature flags allow A/B testing and gradual rollouts
- Debug mode should be disabled in production

### Development Settings

Environment indicator for conditional behavior.

| Variable | Required | Type | Default | Description | Example |
|----------|----------|------|---------|-------------|---------|
| `VITE_ENV` | No | String | `development` | Environment name | `development`, `staging`, `production` |

**Notes:**
- Used to conditionally enable development tools
- Can be used to configure different API endpoints per environment

---

## Security Best Practices

### General Guidelines

1. **Never commit `.env` files to Git**
   - Use `.env.*.example` files as templates
   - Add `.env.*` to `.gitignore` (already configured)
   - Verify with: `git check-ignore .env.backend`

2. **Generate cryptographically secure secrets**
   ```bash
   # Django SECRET_KEY and JWT_SECRET_KEY
   python backend/scripts/generate_secrets.py

   # Database password
   openssl rand -base64 24
   ```

3. **Use different secrets for each environment**
   - Development secrets != Staging secrets != Production secrets
   - Prevents secret leakage across environments

4. **Rotate secrets regularly**
   - Recommended: Every 90 days for production
   - After any suspected compromise
   - When team members leave the organization

5. **Validate API keys are not placeholders**
   - Django startup validation checks for `your-*-key-here` patterns
   - Application will fail to start with invalid/missing keys

### Production-Specific Recommendations

1. **Use environment variable management services**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Kubernetes Secrets

2. **Enable HTTPS and secure cookies**
   ```bash
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

3. **Restrict CORS origins**
   ```bash
   CORS_ALLOWED_ORIGINS=https://app.example.com
   ```

4. **Enable Redis authentication**
   ```bash
   REDIS_URL=redis://:password@redis:6379/0
   ```

5. **Use strong password policies**
   ```bash
   PASSWORD_HASHERS=django.contrib.auth.hashers.Argon2PasswordHasher
   ```

### Troubleshooting

**Environment variables not loading:**
- Verify file name is exactly `.env.backend` or `.env.frontend`
- Check file is in project root directory
- Restart Docker containers after changes: `docker-compose restart backend`
- Verify no typos in variable names (case-sensitive)

**"Missing environment variable" errors:**
- Check startup logs: `docker-compose logs backend`
- Verify required variables are set in `.env.backend`
- Ensure no placeholder values (`your-api-key-here`)
- Compare against `.env.backend.example` for missing variables

**API keys not working:**
- Verify API keys are active and not expired
- Check usage limits in provider dashboards
- Ensure no extra whitespace in API key values
- Test API keys with provider's test endpoints

---

For setup instructions, see:
- [Local Docker Setup Guide](./00_setup_local_docker.md)
- [Backend .env.backend.example](../../.env.backend.example)
- [Frontend .env.frontend.example](../../.env.frontend.example)

For additional help, contact the project maintainer.
