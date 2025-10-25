# Environment Variables Documentation

## Overview

This document details all environment variables required for the Technology Watch Platform, with special focus on authentication-related variables (US-2).

## Backend Environment Variables

### Required Variables

#### Django Core

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `DJANGO_SECRET_KEY` | Secret key for Django security | `your-secret-key-here` | None | Yes |
| `DJANGO_DEBUG` | Enable debug mode | `True` or `False` | `False` | Yes |
| `DJANGO_ALLOWED_HOSTS` | Allowed hosts for Django | `localhost,127.0.0.1` | `localhost` | Yes |

#### Database

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `DATABASE_URL` | PostgreSQL database URL | `postgresql://user:pass@localhost/dbname` | SQLite (dev) | No* |
| `DB_NAME` | Database name | `techwatch_db` | `db.sqlite3` | No* |
| `DB_USER` | Database user | `postgres` | None | No* |
| `DB_PASSWORD` | Database password | `secretpassword` | None | No* |
| `DB_HOST` | Database host | `localhost` | None | No* |
| `DB_PORT` | Database port | `5432` | `5432` | No* |

*Required for production with PostgreSQL

#### Authentication (US-2)

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `JWT_SECRET_KEY` | Secret key for JWT signing | `jwt-secret-key-here` | Uses DJANGO_SECRET_KEY | No |
| `JWT_ACCESS_TOKEN_LIFETIME` | Access token lifetime (minutes) | `15` | `15` | No |
| `JWT_REFRESH_TOKEN_LIFETIME` | Refresh token lifetime (days) | `7` | `7` | No |
| `FRONTEND_URL` | Frontend application URL | `http://localhost:5173` | `http://localhost:5173` | Yes |

#### Email Configuration

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `EMAIL_BACKEND` | Email backend class | `django.core.mail.backends.smtp.EmailBackend` | `console` (dev) | No |
| `EMAIL_HOST` | SMTP server host | `smtp.gmail.com` | `smtp.gmail.com` | No* |
| `EMAIL_PORT` | SMTP server port | `587` | `587` | No* |
| `EMAIL_USE_TLS` | Use TLS for email | `True` | `True` | No* |
| `EMAIL_HOST_USER` | SMTP username | `noreply@techwatch.com` | Empty | No* |
| `EMAIL_HOST_PASSWORD` | SMTP password | `app-specific-password` | Empty | No* |
| `DEFAULT_FROM_EMAIL` | Default sender email | `noreply@techwatch.com` | `noreply@techwatch.com` | No |

*Required for production email sending

#### CORS Configuration

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` | See settings.py | No |
| `CORS_ALLOW_CREDENTIALS` | Allow credentials in CORS | `True` | `True` | No |

---

## Frontend Environment Variables

### Required Variables

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000` | `http://localhost:8000` | Yes |
| `VITE_FRONTEND_URL` | Frontend application URL | `http://localhost:5173` | `http://localhost:5173` | Yes |

### Optional Variables

| Variable | Description | Example | Default | Required |
|----------|-------------|---------|---------|----------|
| `VITE_API_TIMEOUT` | API request timeout (ms) | `30000` | `30000` | No |
| `VITE_ENABLE_ANALYTICS` | Enable analytics | `true` | `false` | No |

---

## Environment Files

### Backend: `.env.backend`

Create this file in the `backend/` directory:

```bash
# Django Core
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Development - SQLite)
# No configuration needed for SQLite

# Database (Production - PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/techwatch_db
# DB_NAME=techwatch_db
# DB_USER=postgres
# DB_PASSWORD=your_db_password
# DB_HOST=localhost
# DB_PORT=5432

# Authentication
FRONTEND_URL=http://localhost:5173

# Email (Development - Console Backend)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Email (Production - SMTP)
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=noreply@techwatch.com
# EMAIL_HOST_PASSWORD=your_app_specific_password
# DEFAULT_FROM_EMAIL=noreply@techwatch.com

# CORS
# CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Frontend: `.env.frontend`

Create this file in the `frontend/` directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_FRONTEND_URL=http://localhost:5173

# Optional
VITE_API_TIMEOUT=30000
VITE_ENABLE_ANALYTICS=false
```

---

## Docker Environment Variables

### Docker Compose: `.env`

For Docker deployments, create this file in the project root:

```bash
# Django
DJANGO_SECRET_KEY=your-docker-secret-key-change-in-production
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database
POSTGRES_DB=techwatch_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password_here
DB_HOST=db
DB_PORT=5432

# Authentication
FRONTEND_URL=http://localhost:3000

# Email (Production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@techwatch.com
EMAIL_HOST_PASSWORD=your_app_specific_password

# Frontend
VITE_API_URL=http://localhost:8000
VITE_FRONTEND_URL=http://localhost:3000
```

---

## Security Best Practices

### 1. Secret Key Generation

Generate secure secret keys using Python:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Or use command line:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Never Commit Secrets

- Add `.env`, `.env.*` to `.gitignore`
- Use separate keys for development and production
- Rotate keys periodically in production

### 3. Environment-Specific Configuration

**Development**:
- `DJANGO_DEBUG=True`
- SQLite database
- Console email backend
- Relaxed CORS

**Production**:
- `DJANGO_DEBUG=False`
- PostgreSQL database
- SMTP email backend
- Strict CORS configuration
- HTTPS enforcement

---

## JWT Configuration Details

### Token Lifetimes

The following JWT token lifetimes are configured by default:

| Token Type | Default Lifetime | Configurable Via | Recommended Range |
|------------|------------------|------------------|-------------------|
| Access Token | 15 minutes | `JWT_ACCESS_TOKEN_LIFETIME` | 5-30 minutes |
| Refresh Token | 7 days | `JWT_REFRESH_TOKEN_LIFETIME` | 1-30 days |

### Security Features

The JWT configuration includes:

- **Token Rotation**: New refresh token issued on each refresh
- **Blacklisting**: Old refresh tokens automatically blacklisted
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Signing Key**: Derived from `DJANGO_SECRET_KEY` or `JWT_SECRET_KEY`

---

## Email Configuration for Different Providers

### Gmail

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_specific_password
```

Note: Use App-Specific Passwords, not your regular Gmail password.

### SendGrid

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
```

### Amazon SES

```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_ses_smtp_username
EMAIL_HOST_PASSWORD=your_ses_smtp_password
```

### Mailgun

```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_mailgun_username
EMAIL_HOST_PASSWORD=your_mailgun_password
```

---

## Rate Limiting Configuration

Rate limiting is configured in Django settings and does not require environment variables. The default configuration is:

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **Authentication endpoints**: 10 requests/minute
- **Authentication burst limit**: 3 requests/minute

To modify these limits, edit `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']` in `backend/config/settings.py`.

---

## Troubleshooting

### Common Issues

1. **"SECRET_KEY not set"**
   - Ensure `DJANGO_SECRET_KEY` is set in `.env.backend`
   - Verify `.env.backend` is in the correct directory

2. **"Email not sending"**
   - Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
   - Verify your email provider allows SMTP access
   - Check firewall/network settings

3. **"CORS errors in frontend"**
   - Ensure `CORS_ALLOWED_ORIGINS` includes your frontend URL
   - Verify `FRONTEND_URL` matches your frontend's actual URL

4. **"JWT token errors"**
   - Ensure frontend and backend URLs are consistent
   - Check that tokens are being stored and sent correctly
   - Verify `JWT_SECRET_KEY` hasn't changed (would invalidate all tokens)

### Verifying Configuration

Check if environment variables are loaded:

```bash
# Backend
cd backend
poetry run python manage.py shell
>>> from django.conf import settings
>>> print(settings.SECRET_KEY)
>>> print(settings.FRONTEND_URL)
```

```bash
# Frontend
cd frontend
npm run dev
# Check browser console for VITE_ variables
```

---

## Production Checklist

Before deploying to production, ensure:

- [ ] `DJANGO_DEBUG=False`
- [ ] Strong, unique `DJANGO_SECRET_KEY` set
- [ ] `DJANGO_ALLOWED_HOSTS` configured with production domain(s)
- [ ] PostgreSQL database configured
- [ ] SMTP email backend configured and tested
- [ ] `FRONTEND_URL` set to production URL
- [ ] HTTPS enabled (not in environment variables, but in deployment config)
- [ ] CORS origins restricted to production domains only
- [ ] All secrets stored securely (e.g., AWS Secrets Manager, Azure Key Vault)
- [ ] Environment variables backed up securely

---

## Related Documentation

- [API Authentication Documentation](./API_AUTHENTICATION.md)
- [Django Settings](../backend/config/settings.py)
- [Setup Local Docker](./setup/00_setup_local_docker.md)

**Documentation Version**: 1.0
**Last Updated**: 2025-01-25
**Related**: US-2 (Standard Account Login), TASK-2.22
