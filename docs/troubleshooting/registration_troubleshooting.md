# Registration Troubleshooting Guide

This guide helps diagnose and resolve common issues with the user registration feature.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Frontend Issues](#frontend-issues)
3. [Backend Issues](#backend-issues)
4. [Database Issues](#database-issues)
5. [Email Issues](#email-issues)
6. [Docker Issues](#docker-issues)
7. [Network Issues](#network-issues)
8. [Common Error Messages](#common-error-messages)

## Quick Diagnostics

### Health Check

Run this command to verify all services are running:

```bash
docker-compose ps
```

**Expected Output:**
```
NAME             STATUS                    PORTS
backend          Up (healthy)              0.0.0.0:8000->8000/tcp
frontend         Up                        0.0.0.0:3000->3000/tcp
db               Up (healthy)              5432/tcp
redis            Up (healthy)              6379/tcp
```

### Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/
- **API Docs:** http://localhost:8000/api/docs/
- **Health Check:** http://localhost:8000/api/health/

### Quick Tests

**1. Backend API Test:**
```bash
curl http://localhost:8000/api/health/
```
Expected: `{"status": "ok"}`

**2. Frontend Test:**
```bash
curl http://localhost:3000
```
Expected: HTML response with "Plateforme de Veille"

**3. Registration Test:**
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123","password_confirm":"TestPassword123","first_name":"Test","last_name":"User"}'
```
Expected: 201 status with user data

## Frontend Issues

### Issue: Registration Page Not Loading

**Symptoms:**
- Blank page at `/register`
- "Cannot GET /register" error
- Page loads but form missing

**Diagnosis:**
```bash
# Check frontend logs
docker-compose logs frontend

# Check for JavaScript errors
# Open browser console (F12)
```

**Solutions:**

**1. Frontend Service Not Running:**
```bash
# Restart frontend
docker-compose restart frontend

# Check status
docker-compose ps frontend
```

**2. Build Errors:**
```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

**3. Node Modules Missing:**
```bash
# Reinstall dependencies
docker-compose exec frontend npm install

# Or rebuild
docker-compose build --no-cache frontend
```

### Issue: Form Validation Not Working

**Symptoms:**
- No error messages shown
- Green/red borders not appearing
- Password strength indicator missing

**Diagnosis:**
```javascript
// Open browser console (F12)
// Check for errors
console.error messages
```

**Solutions:**

**1. JavaScript Errors:**
- Check browser console for syntax errors
- Verify React components imported correctly
- Check for missing dependencies

**2. State Not Updating:**
```bash
# Check React DevTools
# Verify state changes in component
```

**3. CSS Not Applied:**
```bash
# Verify CSS files imported
# Check for build errors
# Clear browser cache (Ctrl+Shift+R)
```

### Issue: API Requests Failing

**Symptoms:**
- "Network Error" in console
- CORS errors
- 404 Not Found errors

**Diagnosis:**
```javascript
// Check browser Network tab (F12)
// Look for failed requests
// Check request/response details
```

**Solutions:**

**1. CORS Errors:**
```bash
# Check backend CORS configuration
docker-compose exec backend grep CORS_ALLOWED_ORIGINS .env.backend

# Should include: http://localhost:3000
```

**Fix CORS:**
```bash
# Edit backend/.env.backend
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**2. Wrong API URL:**
```javascript
// Check frontend/src/services/apiClient.js
const API_BASE_URL = 'http://localhost:8000';
```

**3. Backend Not Running:**
```bash
docker-compose ps backend
docker-compose restart backend
```

## Backend Issues

### Issue: Server Won't Start

**Symptoms:**
- Backend container exits immediately
- "Configuration validation failed" error
- Import errors in logs

**Diagnosis:**
```bash
# Check backend logs
docker-compose logs backend

# Look for error messages
docker-compose logs backend | grep ERROR
```

**Common Causes:**

### 1. Missing Environment Variables

**Error:**
```
ConfigurationError: Environment configuration validation failed
```

**Solution:**
```bash
# Check .env.backend exists
ls -la backend/.env.backend

# Verify required variables
cat backend/.env.backend | grep -E "(SECRET_KEY|DATABASE_URL|REDIS)"

# Copy from example if missing
cp backend/.env.backend.example backend/.env.backend
```

**Required Variables:**
```env
SECRET_KEY=your-secret-key-min-50-chars
DATABASE_URL=postgresql://user:password@db:5432/veille_tech_db
REDIS_HOST=redis
CELERY_BROKER_URL=redis://redis:6379/0
```

### 2. Database Connection Failed

**Error:**
```
django.db.utils.OperationalError: connection to server at "db" failed
```

**Diagnosis:**
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Try connecting to database
docker-compose exec db psql -U veille_tech_user -d veille_tech_db
```

**Solutions:**

**A. Database Not Ready:**
```bash
# Wait for database to be healthy
docker-compose up -d db
sleep 10
docker-compose up -d backend
```

**B. Wrong Database Credentials:**
```bash
# Verify DATABASE_URL in .env.backend
# Format: postgresql://user:password@db:5432/database
# Password must not contain special chars like +, @, :
```

**C. Database Volume Corrupted:**
```bash
# Recreate database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d db
docker-compose exec backend python manage.py migrate
```

### 3. Missing Migrations

**Error:**
```
ValueError: Dependency on app with no migrations: accounts
```

**Solution:**
```bash
# Create migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Restart backend
docker-compose restart backend
```

### 4. Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'django_ratelimit'
```

**Solution:**
```bash
# Rebuild backend image
cd backend
poetry lock
cd ..
docker-compose build backend
docker-compose up -d backend
```

### Issue: Registration Endpoint Returns 500

**Symptoms:**
- API returns HTTP 500 Internal Server Error
- "TypeError" in backend logs
- User not created in database

**Diagnosis:**
```bash
# Check backend error logs
docker-compose logs backend | grep -A 20 "Internal Server Error"

# Check Django debug page (if DEBUG=True)
curl -v http://localhost:8000/api/auth/register/ ...
```

**Common Causes:**

### 1. Custom User Manager Missing

**Error:**
```
TypeError: UserManager.create_user() missing 1 required positional argument: 'username'
```

**Solution:**
Verify `CustomUserManager` is defined and assigned:

```python
# backend/apps/accounts/models.py

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Implementation here
        pass

class CustomUser(AbstractUser):
    objects = CustomUserManager()  # ← Must be present
```

### 2. Celery Not Running

**Error:**
```
kombu.exceptions.OperationalError: [Errno 111] Connection refused
```

**Solution:**
```bash
# Start Celery worker
docker-compose up -d worker

# Check worker logs
docker-compose logs worker
```

### 3. Redis Not Available

**Error:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# Restart Redis
docker-compose restart redis
```

## Database Issues

### Issue: Migrations Fail

**Error:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory
```

**Solution:**
```bash
# Option 1: Reset migrations (development only)
docker-compose exec backend python manage.py migrate --fake accounts zero
docker-compose exec backend python manage.py migrate accounts

# Option 2: Reset database (WARNING: Deletes all data)
docker-compose down -v
docker-compose up -d db
docker-compose exec backend python manage.py migrate
```

### Issue: Database Locked

**Error:**
```
psycopg2.errors.LockNotAvailable: could not obtain lock
```

**Solution:**
```bash
# Check for long-running queries
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Kill blocking queries (if safe)
docker-compose exec db psql -U veille_tech_user -d veille_tech_db -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND pid <> pg_backend_pid();"

# Restart database
docker-compose restart db
```

### Issue: Duplicate Key Error

**Error:**
```
psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint "users_email_key"
```

**This is expected** when registering with an email that already exists.

**To test with fresh email:**
```bash
# Delete test user
docker-compose exec backend python manage.py shell
>>> from apps.accounts.models import CustomUser
>>> CustomUser.objects.filter(email='test@example.com').delete()
```

## Email Issues

### Issue: Verification Email Not Sent

**Symptoms:**
- No email in inbox
- No email in console output (development)
- Celery task fails

**Diagnosis:**
```bash
# Check Celery worker logs
docker-compose logs worker

# Check if task was queued
docker-compose exec redis redis-cli KEYS "celery*"

# Check email backend configuration
docker-compose exec backend grep EMAIL_BACKEND .env.backend
```

**Solutions:**

### 1. Celery Worker Not Running

```bash
# Start worker
docker-compose up -d worker

# Verify worker is consuming tasks
docker-compose logs worker | grep "celery@"
```

### 2. Wrong Email Backend (Development)

**Development should use console backend:**
```bash
# Check .env.backend
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

**To see emails in console:**
```bash
# Watch backend logs
docker-compose logs -f backend

# Register a user
# Email content appears in logs
```

### 3. SMTP Configuration Wrong (Production)

**If using SMTP:**
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Test SMTP:**
```bash
docker-compose exec backend python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

## Docker Issues

### Issue: Containers Won't Start

**Error:**
```
ERROR: Cannot start service backend: driver failed
```

**Solutions:**

### 1. Port Already in Use

```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Kill process or change port
# Edit docker-compose.yml: "8001:8000"
```

### 2. Out of Disk Space

```bash
# Check disk space
df -h

# Clean up Docker
docker system prune -a
docker volume prune
```

### 3. Docker Daemon Not Running

```bash
# Start Docker
# Windows: Start Docker Desktop
# Linux: sudo systemctl start docker
# macOS: open Docker.app
```

### Issue: Changes Not Reflected

**Symptoms:**
- Code changes not visible
- Still seeing old code behavior

**Solutions:**

**1. Rebuild Images:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

**2. Clear Volumes:**
```bash
docker-compose down -v
docker-compose up -d
```

**3. Clear Browser Cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (macOS)
- Clear site data: F12 → Application → Clear storage

### Issue: Permission Denied Errors

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/app/...'
```

**Solution:**
```bash
# Fix file permissions
chmod -R 755 backend/
chmod -R 755 frontend/

# On Linux, may need to chown
sudo chown -R $USER:$USER backend/ frontend/
```

## Network Issues

### Issue: Can't Access Frontend

**URL:** http://localhost:3000

**Error:** "This site can't be reached"

**Solutions:**

**1. Check Service Running:**
```bash
docker-compose ps frontend
```

**2. Check Port Mapping:**
```bash
docker-compose port frontend 3000
# Should output: 0.0.0.0:3000
```

**3. Check Firewall:**
```bash
# Windows: Allow port 3000 in Windows Firewall
# Linux: sudo ufw allow 3000
```

**4. Try Different Browser:**
- Chrome/Firefox may cache connection failures
- Try incognito/private mode

### Issue: API Requests Timeout

**Error:** "Network request failed" or timeout

**Diagnosis:**
```bash
# Test API directly
curl -v http://localhost:8000/api/health/

# Check response time
time curl http://localhost:8000/api/health/
```

**Solutions:**

**1. Backend Overloaded:**
```bash
# Check resource usage
docker stats backend

# Increase backend resources
# Edit docker-compose.yml:
#   deploy:
#     resources:
#       limits:
#         cpus: '1.0'
#         memory: 1G
```

**2. Database Slow:**
```bash
# Check slow queries
docker-compose exec db psql -U veille_tech_user -d veille_tech_db \
  -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

**3. Network Congestion:**
```bash
# Check Docker network
docker network ls
docker network inspect hackathon_base_de_connaissance_app-network
```

## Common Error Messages

### "Email is required"

**Cause:** Email field left empty

**Solution:** Fill in email field before submitting

### "Please enter a valid email address"

**Cause:** Invalid email format

**Solution:** Enter valid email (e.g., user@example.com)

### "Password must be at least 8 characters"

**Cause:** Password too short

**Solution:** Enter password with ≥8 characters

### "Password must contain at least one uppercase letter"

**Cause:** Password missing uppercase letter

**Solution:** Include A-Z character in password

### "Passwords do not match"

**Cause:** Password and confirm password different

**Solution:** Ensure both password fields match exactly

### "An account with this email already exists"

**Cause:** Email already registered

**Solution:**
- Use different email, OR
- Login with existing account, OR
- Reset password if forgotten

### "Too many registration attempts. Please try again later."

**Cause:** Rate limit exceeded (>5 attempts in 1 hour from same IP)

**Solution:**
- Wait 1 hour and try again, OR
- Try from different IP/network, OR
- Clear rate limit (development):
  ```bash
  docker-compose exec redis redis-cli FLUSHDB
  ```

### "Registration failed. Please try again."

**Cause:** Generic server error

**Diagnosis:**
```bash
# Check backend logs for details
docker-compose logs backend | tail -50
```

**Solution:** Contact administrator with error details

## Getting Help

### Log Collection

When reporting issues, collect these logs:

```bash
# Create logs directory
mkdir -p logs

# Collect all logs
docker-compose logs --no-color > logs/all-services.log
docker-compose logs backend --no-color > logs/backend.log
docker-compose logs frontend --no-color > logs/frontend.log
docker-compose logs db --no-color > logs/database.log

# System info
docker-compose version > logs/system-info.txt
docker version >> logs/system-info.txt
docker-compose ps >> logs/system-info.txt
```

### Health Report

Generate health report:

```bash
#!/bin/bash
# save as health-check.sh

echo "=== Service Status ==="
docker-compose ps

echo -e "\n=== Backend Health ==="
curl -s http://localhost:8000/api/health/ | python -m json.tool

echo -e "\n=== Database Connection ==="
docker-compose exec -T db pg_isready

echo -e "\n=== Redis Connection ==="
docker-compose exec -T redis redis-cli ping

echo -e "\n=== Recent Errors ==="
docker-compose logs --tail=50 backend | grep -i error
```

### Support Channels

- **GitHub Issues:** [Project Issues](https://github.com/...)
- **Documentation:** `/docs` directory
- **Security Issues:** security@techwatch.com (private)

### Before Reporting

- [ ] Checked this troubleshooting guide
- [ ] Verified all services running (`docker-compose ps`)
- [ ] Collected relevant logs
- [ ] Tried restarting services
- [ ] Checked for known issues on GitHub
- [ ] Documented steps to reproduce
- [ ] Noted your environment (OS, Docker version)

## Prevention Tips

**Development Best Practices:**

1. **Use version control:**
   ```bash
   git status  # Check for uncommitted changes
   git stash   # Save work in progress
   ```

2. **Keep dependencies updated:**
   ```bash
   cd backend && poetry update
   cd ../frontend && npm update
   ```

3. **Regular cleanup:**
   ```bash
   docker system prune -f
   docker volume prune -f
   ```

4. **Monitor logs:**
   ```bash
   # Watch logs during development
   docker-compose logs -f backend frontend
   ```

5. **Test before committing:**
   ```bash
   # Run tests
   docker-compose exec backend pytest

   # Check code style
   docker-compose exec backend black --check .
   docker-compose exec frontend npm run lint
   ```

## Quick Reference

### Service Control

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend python manage.py shell
```

### Database Management

```bash
# Create migrations
docker-compose exec backend python manage.py makemigrations

# Apply migrations
docker-compose exec backend python manage.py migrate

# Access database shell
docker-compose exec db psql -U veille_tech_user -d veille_tech_db
```

### Cache Management

```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB

# View Redis keys
docker-compose exec redis redis-cli KEYS "*"
```

### Testing

```bash
# Run all tests
docker-compose exec backend pytest

# Run specific test file
docker-compose exec backend pytest apps/accounts/tests/test_integration.py

# Run with coverage
docker-compose exec backend pytest --cov=apps.accounts
```

---

**Last Updated:** 2025-11-04
**Version:** 1.0
**Status:** Production Ready
