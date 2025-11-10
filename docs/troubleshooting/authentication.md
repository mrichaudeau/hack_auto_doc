# Authentication Troubleshooting Guide

> **US-3: Standard User Login - TASK-3.24**
>
> Comprehensive troubleshooting guide for authentication issues including unverified email, rate limiting, invalid credentials, CORS errors, JWT token issues, and infrastructure problems.

## Table of Contents

- [Common Issues Quick Reference](#common-issues-quick-reference)
- [Issue 1: "Please verify your email before logging in" (403)](#issue-1-please-verify-your-email-before-logging-in-403)
- [Issue 2: "Too many login attempts" (429)](#issue-2-too-many-login-attempts-429)
- [Issue 3: "Invalid email or password" (401)](#issue-3-invalid-email-or-password-401)
- [Issue 4: CORS Errors](#issue-4-cors-errors)
- [Issue 5: JWT Token Expired](#issue-5-jwt-token-expired)
- [Issue 6: Redis Connection Failure](#issue-6-redis-connection-failure)
- [Issue 7: Database Connection Issues](#issue-7-database-connection-issues)
- [Issue 8: Missing Environment Variables](#issue-8-missing-environment-variables)
- [FAQ](#faq)
- [Related Documentation](#related-documentation)

---

## Common Issues Quick Reference

| Error Code | Message | Quick Fix |
|------------|---------|-----------|
| 403 | "Please verify your email" | Click verification link or manually verify user |
| 429 | "Too many login attempts" | Wait 5 minutes or clear Redis rate limit |
| 401 | "Invalid email or password" | Check credentials, verify user exists |
| CORS | "No 'Access-Control-Allow-Origin'" | Configure CORS in Django settings |
| 500 | "Server error" | Check backend logs, Redis, and database |

---

## Issue 1: "Please verify your email before logging in" (403)

### Symptoms
- User receives `403 Forbidden` error with message: "Please verify your email before logging in"
- Login form shows error message even with correct credentials
- User can register but cannot login

### Cause
User's `is_email_verified` flag is `False` in the database. Email verification is required before first login (security feature).

### Diagnosis

#### Step 1: Check user verification status
```bash
# Connect to backend container
docker-compose exec backend python manage.py shell

# Check verification status
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='user@example.com')
>>> print(f"Email verified: {user.is_email_verified}")
Email verified: False
>>> print(f"User active: {user.is_active}")
User active: True
```

#### Step 2: Check if verification email was sent
```bash
# Check email backend logs
docker-compose logs backend | grep "Sending verification email"

# Check if verification token exists
>>> from accounts.models import EmailVerificationToken
>>> token = EmailVerificationToken.objects.filter(user=user, is_used=False).first()
>>> if token:
...     print(f"Token: {token.token}")
...     print(f"Expires: {token.expires_at}")
...     print(f"Expired: {token.is_expired()}")
```

### Resolution

#### Option 1: User clicks verification link (Proper Flow)
1. User checks inbox for verification email
2. User clicks verification link
3. User redirected to verification success page
4. User can now login

#### Option 2: Resend verification email
```bash
# Use resend verification endpoint
curl -X POST http://localhost:8000/api/auth/resend-verification/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

#### Option 3: Manually verify (Development/Testing Only)
```bash
docker-compose exec backend python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='user@example.com')
>>> user.is_email_verified = True
>>> user.save()
>>> print("User verified successfully")
```

### Prevention
- Ensure email service (Celery + Redis) is running properly
- Test email delivery in development environment
- Provide clear "Resend Verification Email" button in UI
- Consider adding verification status indicator in admin panel
- Document email verification flow for users

---

## Issue 2: "Too many login attempts" (429)

### Symptoms
- User receives `429 Too Many Requests` error
- Error message: "Too many login attempts. Please try again in X minutes"
- `Retry-After` header present in response
- Subsequent login attempts immediately blocked

### Cause
Rate limiting enforced: **5 failed attempts per IP address per 5 minutes**. This prevents brute force attacks.

### Diagnosis

#### Step 1: Check rate limit counter in Redis
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# Check rate limit counter (replace IP with actual IP)
> GET rate_limit:login:192.168.1.1
"6"  # Number of attempts (over limit of 5)

# Check time until reset
> TTL rate_limit:login:192.168.1.1
287  # Seconds until automatic reset (about 5 minutes)
```

#### Step 2: Check login audit logs
```bash
docker-compose exec backend python manage.py shell

>>> from accounts.models import LoginAuditLog
>>> from datetime.datetime import datetime, timedelta
>>> recent_attempts = LoginAuditLog.objects.filter(
...     ip_address='192.168.1.1',
...     timestamp__gte=datetime.now() - timedelta(minutes=5)
... ).order_by('-timestamp')
>>> for attempt in recent_attempts[:10]:
...     print(f"{attempt.timestamp}: {attempt.email} - {'SUCCESS' if attempt.success else 'FAILED'}")
```

### Resolution

#### Option 1: Wait for automatic reset (Recommended)
- Rate limit automatically resets after 5 minutes
- User sees countdown in error message
- No manual intervention required

#### Option 2: Manually reset rate limit (Testing Only)
```bash
# Clear rate limit for specific IP
docker-compose exec redis redis-cli DEL rate_limit:login:192.168.1.1

# Clear all rate limits (use with caution)
docker-compose exec redis redis-cli FLUSHDB
```

### Prevention
- Educate users about password requirements
- Implement "Forgot Password" flow for users who forgot credentials
- Consider IP whitelisting for trusted office networks
- Monitor rate limit metrics for abuse patterns
- Add CAPTCHA after 3 failed attempts (future enhancement)
- Implement account lockout after repeated violations (future enhancement)

---

## Issue 3: "Invalid email or password" (401)

### Symptoms
- User receives `401 Unauthorized` error
- Error message: "Invalid email or password"
- Same error for non-existent user and wrong password (security feature)
- Login fails even when credentials appear correct

### Cause
- User entered incorrect email or password
- User account doesn't exist
- Password case-sensitivity issue
- Copy-paste added invisible characters

### Diagnosis

#### Step 1: Verify user exists
```bash
docker-compose exec backend python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.filter(email='user@example.com').first()
>>> if user:
...     print(f"User exists: {user.email}")
...     print(f"Active: {user.is_active}")
...     print(f"Verified: {user.is_email_verified}")
... else:
...     print("User does not exist")
```

#### Step 2: Test password verification
```bash
>>> if user:
...     # Test password (replace 'test_password' with actual password)
...     is_valid = user.check_password('test_password')
...     print(f"Password valid: {is_valid}")
```

#### Step 3: Check login audit logs
```bash
>>> from accounts.models import LoginAuditLog
>>> recent_attempts = LoginAuditLog.objects.filter(
...     email__iexact='user@example.com'
... ).order_by('-timestamp')[:5]
>>> for attempt in recent_attempts:
...     print(f"{attempt.timestamp}: {attempt.failure_reason or 'SUCCESS'}")
```

### Resolution

#### Option 1: User resets password (Proper Flow)
```bash
# Use password reset endpoint (future implementation)
curl -X POST http://localhost:8000/api/auth/password-reset/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

#### Option 2: Manually reset password (Testing Only)
```bash
docker-compose exec backend python manage.py shell

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(email='user@example.com')
>>> user.set_password('NewSecurePass123!')
>>> user.save()
>>> print("Password reset successfully")
```

### Prevention
- Implement "Forgot Password" flow
- Show password requirements during registration
- Use password strength indicator
- Trim whitespace from email input
- Provide clear error messages without revealing which field is wrong
- Log failed attempts for security monitoring

---

## Issue 4: CORS Errors

### Symptoms
- Browser console shows CORS error:
  ```
  Access to XMLHttpRequest at 'http://localhost:8000/api/auth/login/' from origin 'http://localhost:3000' has been blocked by CORS policy
  ```
- Network tab shows OPTIONS preflight request fails
- Login request never reaches backend
- Works in Postman but not in browser

### Cause
- CORS (Cross-Origin Resource Sharing) not configured in Django
- Frontend (localhost:3000) trying to access backend (localhost:8000)
- Missing or incorrect CORS headers

### Diagnosis

#### Step 1: Check CORS configuration
```bash
# Check Django settings
docker-compose exec backend grep -r "CORS" config/settings/

# Check installed packages
docker-compose exec backend poetry show | grep cors
```

#### Step 2: Test CORS headers
```bash
# Test OPTIONS preflight request
curl -X OPTIONS http://localhost:8000/api/auth/login/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

### Resolution

#### Step 1: Install django-cors-headers
```bash
cd backend
poetry add django-cors-headers
```

#### Step 2: Configure CORS in Django settings
```python
# backend/config/settings/base.py

INSTALLED_APPS = [
    # ...
    'corsheaders',  # Add this
    # ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add this BEFORE CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    # ...
]

# Development CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Allow credentials (for cookies/auth)
CORS_ALLOW_CREDENTIALS = True

# Allowed headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

#### Step 3: Restart backend
```bash
docker-compose restart backend
```

### Prevention
- Include CORS configuration in initial setup
- Document CORS settings for different environments
- Use environment variables for allowed origins
- Test cross-origin requests during development
- Add CORS to deployment checklist

---

## Issue 5: JWT Token Expired

### Symptoms
- User was logged in, but now gets 401 errors on API calls
- "Token expired" or similar error message
- User must login again even though they were recently active
- Automatic logout after period of inactivity

### Cause
- Access token has expired (typically 15-60 minutes)
- Refresh token has also expired (typically 7-30 days)
- Token refresh failed
- Interceptor not configured to refresh tokens

### Diagnosis

#### Step 1: Check token expiration
```javascript
// In browser console
const token = localStorage.getItem('veille_tech_access_token');
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]));
  const exp = new Date(payload.exp * 1000);
  console.log('Token expires:', exp);
  console.log('Expired:', Date.now() > payload.exp * 1000);
}
```

#### Step 2: Check JWT configuration
```bash
# Check token lifetime settings
docker-compose exec backend python manage.py shell

>>> from django.conf import settings
>>> print(settings.SIMPLE_JWT)
```

### Resolution

#### Option 1: User logs in again (Proper Flow)
- User redirected to /login
- User enters credentials
- New tokens issued

#### Option 2: Use refresh token (Automatic via Interceptor)
```javascript
// Interceptor automatically handles this
// If access token expired but refresh token valid:
// 1. Calls /api/auth/token/refresh/ with refresh token
// 2. Gets new access token
// 3. Updates stored token
// 4. Retries original request
```

#### Option 3: Manually refresh token (Testing)
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token_here>"}'
```

### Prevention
- Implement automatic token refresh (TASK-3.12)
- Use longer refresh token lifetime for better UX
- Clear expired tokens on application start
- Monitor token refresh failures
- Consider "Remember Me" functionality

---

## Issue 6: Redis Connection Failure

### Symptoms
- Login fails with 500 Internal Server Error
- Backend logs show Redis connection errors:
  ```
  redis.exceptions.ConnectionError: Error connecting to Redis
  ```
- Rate limiting not working
- Celery tasks failing

### Cause
- Redis service not running
- Incorrect Redis configuration
- Redis port conflict
- Network connectivity issue

### Diagnosis

#### Step 1: Check Redis service status
```bash
# Check if Redis container is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected output: PONG
```

#### Step 2: Check Redis configuration
```bash
# Check Django Redis settings
docker-compose exec backend python manage.py shell

>>> from django.core.cache import cache
>>> cache.set('test_key', 'test_value', 30)
>>> result = cache.get('test_key')
>>> print(f"Redis working: {result == 'test_value'}")
```

### Resolution

#### Option 1: Start Redis service
```bash
# Start Redis if stopped
docker-compose up -d redis

# Restart all services
docker-compose restart
```

#### Option 2: Fix Redis configuration
```bash
# Check environment variables
cat .env.backend | grep REDIS

# Correct format:
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

#### Option 3: Clear Redis data and restart
```bash
# Clear Redis data
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart backend worker
```

### Prevention
- Include Redis in Docker health checks
- Monitor Redis memory usage
- Set up Redis persistence if needed
- Document Redis configuration
- Test Redis connection during application startup

---

## Issue 7: Database Connection Issues

### Symptoms
- Login fails with 500 Internal Server Error
- Backend logs show database errors:
  ```
  django.db.utils.OperationalError: could not connect to server
  ```
- Cannot create or query users
- Migrations fail

### Cause
- PostgreSQL service not running
- Incorrect database credentials
- Database not initialized (migrations not run)
- Port conflict

### Diagnosis

#### Step 1: Check PostgreSQL service
```bash
# Check if database container is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test database connection
docker-compose exec db psql -U postgres -c "SELECT version();"
```

#### Step 2: Check database configuration
```bash
# Check environment variables
cat .env.backend | grep DB

# Test connection from backend
docker-compose exec backend python manage.py dbshell
```

#### Step 3: Check migrations
```bash
# List migrations
docker-compose exec backend python manage.py showmigrations

# Check if accounts app migrated
docker-compose exec backend python manage.py showmigrations accounts
```

### Resolution

#### Option 1: Start database service
```bash
# Start database if stopped
docker-compose up -d db

# Wait for database to be ready
sleep 5

# Run migrations
docker-compose exec backend python manage.py migrate
```

#### Option 2: Fix database configuration
```bash
# Check .env.backend file
# Correct format:
DB_NAME=veille_tech_db
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432
```

#### Option 3: Reset database (Development Only - DESTRUCTIVE)
```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm hackathon_base_de_connaissance_postgres_data

# Recreate and migrate
docker-compose up -d db
sleep 10
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### Prevention
- Include database in Docker health checks
- Backup database regularly
- Document database setup procedure
- Test database connection during application startup
- Monitor database connections and slow queries

---

## Issue 8: Missing Environment Variables

### Symptoms
- Login fails with unclear error
- Backend logs show warnings about missing settings
- Features not working (email, Redis, etc.)
- Different behavior in different environments

### Cause
- `.env.backend` or `.env.frontend` file missing
- Environment variables not loaded
- Typo in variable names
- Variables not exported in Docker

### Diagnosis

#### Step 1: Check if .env files exist
```bash
# List environment files
ls -la .env*

# Expected files:
# .env.backend
# .env.frontend
```

#### Step 2: Verify variables are loaded
```bash
# Check backend variables
docker-compose exec backend env | sort

# Check specific variables
docker-compose exec backend env | grep -E '(DB_|REDIS_|SECRET_KEY)'
```

#### Step 3: Compare with example files
```bash
# Compare with example
diff .env.backend .env.backend.example
```

### Resolution

#### Option 1: Create from example files
```bash
# Copy example files
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend

# Edit with your values
nano .env.backend
nano .env.frontend
```

#### Option 2: Required environment variables
```bash
# .env.backend minimum required variables
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=veille_tech_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
REDIS_HOST=redis
REDIS_PORT=6379

# .env.frontend minimum required variables
VITE_API_URL=http://localhost:8000
```

#### Option 3: Reload environment
```bash
# Restart services to load new environment
docker-compose down
docker-compose up -d
```

### Prevention
- Include .env.example files in repository
- Document required environment variables
- Add validation for required variables at startup
- Use consistent naming conventions
- Never commit .env files to Git (in .gitignore)

---

## FAQ

### Q: Why am I getting "Invalid email or password" when my credentials are correct?

**A:** Check these common issues:
1. Email not verified (should get 403, not 401)
2. Trailing whitespace in email/password
3. Copy-paste added invisible characters
4. Caps Lock is on (password is case-sensitive)
5. Account disabled (`is_active=False`)

### Q: How do I bypass rate limiting during development?

**A:** Clear Redis rate limit counter:
```bash
docker-compose exec redis redis-cli FLUSHDB
```

**Warning:** This clears ALL Redis data, not just rate limits.

### Q: Can I disable email verification for development?

**A:** Not recommended, but you can manually verify users:
```bash
docker-compose exec backend python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.all().update(is_email_verified=True)
```

### Q: How long are JWT tokens valid?

**A:**
- **Access tokens**: 15-60 minutes (configurable)
- **Refresh tokens**: 7-30 days (configurable)

Check configuration:
```bash
docker-compose exec backend python manage.py shell
>>> from django.conf import settings
>>> print(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
>>> print(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])
```

### Q: What happens if I'm logged in on multiple devices?

**A:** Each device has its own set of tokens. Logout on one device doesn't affect others. To implement global logout, you would need token blacklisting (future enhancement).

### Q: How do I debug authentication issues in production?

**A:**
1. Check application logs
2. Check LoginAuditLog table
3. Verify environment variables
4. Test token refresh endpoint
5. Check CORS configuration
6. Verify SSL/TLS certificates

### Q: Can I customize the rate limit threshold?

**A:** Yes, modify the `@rate_limit` decorator in `backend/accounts/views.py`:
```python
@rate_limit(limit=10, window=600)  # 10 attempts per 10 minutes
def post(self, request):
    # ...
```

---

## Related Documentation

- [Login API Documentation](../api/authentication.md) - API endpoint specifications
- [Token Storage Documentation](../frontend/token-storage.md) - Client-side token management
- [Rate Limiting Documentation](../backend/rate-limiting.md) - Rate limiting implementation
- [JWT Configuration](../backend/jwt-configuration.md) - JWT token settings
- [Email Verification Flow](../workflows/email-verification.md) - Email verification process
- [Docker Setup Guide](../setup/00_setup_local_docker.md) - Local development environment

---

## Support

If you encounter issues not covered in this guide:

1. **Check logs**: `docker-compose logs backend` and `docker-compose logs frontend`
2. **Search LoginAuditLog**: Check for patterns in failed authentication attempts
3. **Test with Postman**: Isolate frontend vs backend issues
4. **Review recent changes**: Check git history for configuration changes
5. **Ask for help**: Provide error messages, logs, and steps to reproduce

---

**Last Updated**: 2025-01-09
**Related User Story**: US-3 (Standard User Login)
**Task**: TASK-3.24 (Create Login Troubleshooting Guide)
