# Docker Environment Troubleshooting Guide

## Overview

This guide provides solutions to common issues encountered when running the Technology Watch Platform in Docker.

**Related Documentation:**
- [Setup Local Docker](./setup/00_setup_local_docker.md)
- [Environment Variables](./ENVIRONMENT_VARIABLES.md)

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Service-Specific Issues](#service-specific-issues)
4. [Database Issues](#database-issues)
5. [Network Issues](#network-issues)
6. [Performance Issues](#performance-issues)
7. [Debug Commands](#debug-commands)

---

## Quick Diagnostics

### Check All Services Status

```bash
docker-compose ps
```

Expected output: All services should show "Up" status.

### Check Service Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
docker-compose logs redis
docker-compose logs worker
docker-compose logs scheduler

# Follow logs in real-time
docker-compose logs -f backend
```

### Check Resource Usage

```bash
docker stats
```

### Verify Network Connectivity

```bash
# Test backend to database
docker-compose exec backend ping -c 3 db

# Test backend to redis
docker-compose exec backend ping -c 3 redis
```

---

## Common Issues

### Issue 1: Services Fail to Start

**Symptoms:**
- `docker-compose up` exits with errors
- Services show "Exit 1" or "Restarting" status

**Solutions:**

1. **Check .env file exists and is configured:**
   ```bash
   ls -la .env
   cat .env
   ```

2. **Rebuild images from scratch:**
   ```bash
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Check for port conflicts:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   netstat -ano | findstr :5432
   netstat -ano | findstr :6379

   # Linux/Mac
   lsof -i :8000
   lsof -i :3000
   lsof -i :5432
   lsof -i :6379
   ```

4. **Verify Docker daemon is running:**
   ```bash
   docker info
   ```

---

### Issue 2: "Cannot Connect to Database"

**Symptoms:**
- Backend logs show: `OperationalError: could not connect to server`
- Backend fails to start

**Solutions:**

1. **Check database service is running:**
   ```bash
   docker-compose ps db
   ```

2. **Check database logs:**
   ```bash
   docker-compose logs db
   ```

3. **Verify database credentials in .env:**
   ```bash
   # Ensure these match in .env
   POSTGRES_DB=techwatch_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   ```

4. **Test database connection:**
   ```bash
   docker-compose exec db psql -U postgres -d techwatch_db -c "SELECT 1;"
   ```

5. **Restart database service:**
   ```bash
   docker-compose restart db
   docker-compose logs -f db
   ```

---

### Issue 3: Frontend Shows "Network Error" or "Cannot Connect to API"

**Symptoms:**
- Frontend loads but API requests fail
- Console shows CORS errors or connection refused

**Solutions:**

1. **Check backend is running:**
   ```bash
   docker-compose ps backend
   curl http://localhost:8000/api/
   ```

2. **Verify environment variables:**
   ```bash
   # In .env
   VITE_API_URL=http://localhost:8000
   FRONTEND_URL=http://localhost:3000
   ```

3. **Check CORS configuration:**
   ```bash
   docker-compose exec backend python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.CORS_ALLOWED_ORIGINS)
   >>> print(settings.FRONTEND_URL)
   ```

4. **Restart both services:**
   ```bash
   docker-compose restart backend frontend
   ```

---

### Issue 4: "Permission Denied" Errors

**Symptoms:**
- Errors about file permissions
- Cannot write to volumes

**Solutions:**

1. **Check volume permissions:**
   ```bash
   docker-compose exec backend ls -la /app
   ```

2. **Fix volume ownership (Linux/Mac):**
   ```bash
   # Stop containers
   docker-compose down

   # Fix ownership
   sudo chown -R $USER:$USER ./backend
   sudo chown -R $USER:$USER ./frontend

   # Restart
   docker-compose up -d
   ```

3. **On Windows with WSL2:**
   - Ensure project is in WSL2 filesystem (not /mnt/c/)
   - Use WSL2 terminal for docker commands

---

### Issue 5: Slow Build Times

**Symptoms:**
- `docker-compose build` takes very long
- Image building seems stuck

**Solutions:**

1. **Enable BuildKit (faster builds):**
   ```bash
   # Add to .env or export
   DOCKER_BUILDKIT=1
   COMPOSE_DOCKER_CLI_BUILD=1

   docker-compose build
   ```

2. **Clean Docker cache:**
   ```bash
   docker builder prune -a
   ```

3. **Use fewer layers in Dockerfile:**
   - Check Dockerfile combines RUN commands

4. **Exclude unnecessary files:**
   - Verify .dockerignore is present
   - Add large directories to .dockerignore

---

## Service-Specific Issues

### Backend Service

**Issue: Migrations Not Running**

```bash
# Check migrations status
docker-compose exec backend python manage.py showmigrations

# Run migrations manually
docker-compose exec backend python manage.py migrate

# If migrations fail, check logs
docker-compose logs backend
```

**Issue: Static Files Not Loading**

```bash
# Collect static files manually
docker-compose exec backend python manage.py collectstatic --noinput

# Check static files directory
docker-compose exec backend ls -la /app/staticfiles
```

**Issue: Celery Worker Not Processing Tasks**

```bash
# Check worker status
docker-compose ps worker

# Check worker logs
docker-compose logs -f worker

# Restart worker
docker-compose restart worker

# Test Celery connection
docker-compose exec backend python manage.py shell
>>> from celery import current_app
>>> current_app.control.inspect().active()
```

---

### Frontend Service

**Issue: "ENOENT: no such file or directory"**

```bash
# Rebuild node_modules
docker-compose exec frontend npm ci

# Or rebuild container
docker-compose up -d --build frontend
```

**Issue: Hot Reload Not Working**

Solution: Check that volumes are mounted correctly in docker-compose.yml:

```yaml
frontend:
  volumes:
    - ./frontend:/app
    - /app/node_modules  # Important: excludes node_modules from bind mount
```

**Issue: Vite Build Fails**

```bash
# Check for syntax errors
docker-compose exec frontend npm run build

# Clear Vite cache
docker-compose exec frontend rm -rf node_modules/.vite
docker-compose restart frontend
```

---

### Database Service

**Issue: pgvector Extension Not Installed**

```bash
# Check if extension exists
docker-compose exec db psql -U postgres -d techwatch_db -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Install manually if missing
docker-compose exec db psql -U postgres -d techwatch_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify installation
docker-compose exec db psql -U postgres -d techwatch_db -c "\dx"
```

**Issue: Database Container Crashes**

```bash
# Check logs for errors
docker-compose logs db

# Remove and recreate volume (WARNING: destroys data!)
docker-compose down -v
docker-compose up -d db

# Restore from backup if available
```

---

### Redis Service

**Issue: Redis Connection Refused**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# Check Redis logs
docker-compose logs redis
```

**Issue: Redis Out of Memory**

```bash
# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Clear all data (if safe to do so)
docker-compose exec redis redis-cli FLUSHALL
```

---

## Network Issues

### Issue: Services Cannot Communicate

**Symptoms:**
- Backend cannot reach database
- Worker cannot reach Redis

**Solutions:**

1. **Verify all services on same network:**
   ```bash
   docker network ls
   docker network inspect techwatch_network
   ```

2. **Check service discovery:**
   ```bash
   # From backend, ping other services
   docker-compose exec backend ping -c 3 db
   docker-compose exec backend ping -c 3 redis
   ```

3. **Restart network:**
   ```bash
   docker-compose down
   docker network prune
   docker-compose up -d
   ```

---

### Issue: Cannot Access Services from Host

**Symptoms:**
- `http://localhost:8000` not accessible
- Port forwarding not working

**Solutions:**

1. **Verify ports are exposed:**
   ```bash
   docker-compose ps
   # Check PORTS column
   ```

2. **Check firewall settings:**
   - Windows: Allow Docker in Windows Firewall
   - Linux: Check iptables rules

3. **Use 0.0.0.0 instead of localhost in service binding:**
   ```yaml
   backend:
     command: python manage.py runserver 0.0.0.0:8000
   ```

---

## Performance Issues

### Issue: High CPU Usage

**Diagnosis:**
```bash
docker stats
```

**Solutions:**

1. **Limit container resources in docker-compose.yml:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

2. **Check for infinite loops in code**

3. **Disable debug mode:**
   ```bash
   # In .env
   DJANGO_DEBUG=False
   ```

---

### Issue: High Memory Usage

**Solutions:**

1. **Check which service is consuming memory:**
   ```bash
   docker stats --no-stream
   ```

2. **Increase Docker Desktop memory allocation:**
   - Docker Desktop → Settings → Resources → Memory

3. **Add memory limits to services:**
   ```yaml
   services:
     backend:
       mem_limit: 512m
   ```

---

## Debug Commands

### Access Service Shell

```bash
# Backend (Python/Django)
docker-compose exec backend python manage.py shell

# Backend (Bash)
docker-compose exec backend bash

# Frontend (Node)
docker-compose exec frontend npm run dev

# Frontend (Bash)
docker-compose exec frontend sh

# Database (PostgreSQL)
docker-compose exec db psql -U postgres -d techwatch_db

# Redis
docker-compose exec redis redis-cli
```

---

### Inspect Service Configuration

```bash
# View service environment variables
docker-compose exec backend env

# View service processes
docker-compose exec backend ps aux

# View service file system
docker-compose exec backend ls -la /app
```

---

### Check Service Health

```bash
# Backend health
curl http://localhost:8000/api/health/

# Database health
docker-compose exec db pg_isready -U postgres

# Redis health
docker-compose exec redis redis-cli ping
```

---

### Reset Everything (Nuclear Option)

**WARNING: This destroys all data!**

```bash
# Stop all containers
docker-compose down

# Remove all volumes (data will be lost!)
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Prune everything
docker system prune -a --volumes

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

---

## Getting More Help

### Check Service Logs in Detail

```bash
# Last 100 lines
docker-compose logs --tail=100 backend

# Logs since specific time
docker-compose logs --since 2025-01-01T00:00:00 backend

# Save logs to file
docker-compose logs backend > backend-logs.txt
```

---

### Useful Docker Commands

```bash
# List all containers (including stopped)
docker ps -a

# Remove specific container
docker rm <container_id>

# Remove all stopped containers
docker container prune

# List all volumes
docker volume ls

# Remove specific volume
docker volume rm <volume_name>

# List all networks
docker network ls

# Inspect container details
docker inspect <container_id>
```

---

## Known Issues & Workarounds

### Issue: Windows Line Endings in Shell Scripts

**Symptom:** Scripts fail with `/bin/bash^M: bad interpreter`

**Solution:**
```bash
# Convert line endings
dos2unix scripts/*.sh

# Or with Git
git config --global core.autocrlf input
```

---

### Issue: Docker Desktop Not Starting on Windows

**Solutions:**
1. Enable virtualization in BIOS
2. Enable Hyper-V in Windows Features
3. Enable WSL2
4. Restart Docker Desktop

---

### Issue: Port Already in Use

**Solution:**
```bash
# Find process using port (Windows)
netstat -ano | findstr :8000

# Kill process
taskkill /PID <process_id> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"
```

---

## Performance Tuning

### Optimize Build Performance

```yaml
# In docker-compose.yml
version: '3.8'
services:
  backend:
    build:
      context: ./backend
      cache_from:
        - backend:latest
```

### Optimize Volume Performance (Windows/Mac)

```yaml
# Use cached or delegated for better performance
volumes:
  - ./backend:/app:cached
  - ./frontend:/app:delegated
```

---

## Support Resources

- **Project Documentation**: `docs/`
- **Docker Documentation**: https://docs.docker.com/
- **Django Documentation**: https://docs.djangoproject.com/
- **React/Vite Documentation**: https://vitejs.dev/

---

**Documentation Version**: 1.0
**Last Updated**: 2025-01-25
**Related**: US-0 (Local Docker Setup)
