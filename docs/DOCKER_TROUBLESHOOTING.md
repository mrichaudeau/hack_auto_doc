# Docker Environment Troubleshooting Guide

This guide provides solutions to common issues encountered when setting up and running the Docker-based development environment.

## Common Issues

### Services Won't Start
**Symptom:** `docker compose up` fails or services exit immediately

**Solutions:**
1. Check logs: `docker compose logs`
2. Verify .env files exist: `ls .env.backend .env.frontend`
3. Validate configuration: `docker compose config`

### Port Already in Use
**Symptom:** "Bind for 0.0.0.0:8000 failed"

**Solutions:**
Windows: `netstat -ano | findstr :8000`
macOS/Linux: `lsof -i :8000`

Then kill the process or change ports in docker-compose.yml

### Hot Reload Not Working
**Solutions:**
1. Set `CHOKIDAR_USEPOLLING=true` for frontend
2. Verify volumes are mounted: `docker compose config | grep volumes`
3. Restart service: `docker compose restart frontend`

### Database Connection Errors
**Solutions:**
1. Wait for database startup (30-60s)
2. Check credentials: `docker compose exec backend env | grep DATABASE_URL`
3. Verify health: `docker compose exec db pg_isready -U postgres`

### Permission Denied Errors
**Solutions:**
Linux: `sudo chown -R $USER:$USER .`
Windows: Store project in WSL2 file system, not /mnt/c/

See DOCKER_SETUP.md for detailed troubleshooting steps.
