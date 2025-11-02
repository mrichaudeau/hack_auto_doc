# Frontend Troubleshooting Guide

## HMR Not Working

**Symptoms:** Changes don't appear in browser, full reload required

**Solutions:**

1. **Check volume mounting:**
   ```bash
   docker-compose exec frontend ls -la /app/src
   # Should see your source files
   ```

2. **Enable polling (if native watching fails):**
   ```js
   // frontend/vite.config.js
   server: {
     watch: {
       usePolling: true,
       interval: 1000,
     }
   }
   ```

3. **Check file watching limits (Linux/macOS):**
   ```bash
   # Increase file watch limit
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

4. **Verify WebSocket connection:**
   - Open browser console
   - Should see: "[vite] connected"

## Port 3000 Already in Use

**Symptoms:** Frontend container fails to start

**Solutions:**

```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:3000
kill -9 <PID>
```

Or change port in docker-compose.yml:
```yaml
ports:
  - "3001:3000"  # Use different host port
```

## API Proxy Returns 502

**Symptoms:** API requests fail, 502 Bad Gateway

**Solutions:**

1. **Verify backend is running:**
   ```bash
   docker-compose ps backend
   curl http://localhost:8000/api/health/
   ```

2. **Check proxy configuration in vite.config.js**

3. **Check both services on same network:**
   ```yaml
   # docker-compose.yml
   frontend:
     networks:
       - app-network
   backend:
     networks:
       - app-network
   ```

## Slow HMR Performance

**Symptoms:** HMR takes > 3 seconds

**Solutions:**

1. **Verify named volume for node_modules:**
   ```bash
   docker volume ls | grep frontend_node_modules
   ```

2. **Use WSL2 filesystem on Windows:**
   - Store code in WSL filesystem, not Windows (C:\)

3. **Reduce file watching scope:**
   ```js
   // vite.config.js
   server: {
     watch: {
       ignored: ['**/node_modules/**', '**/dist/**']
     }
   }
   ```

## node_modules Issues

**Symptoms:** Package not found, dependencies outdated

**Solutions:**

```bash
# Rebuild node_modules
docker-compose down frontend
docker volume rm frontend_node_modules
docker-compose up --build frontend
```

## Container Keeps Restarting

**Symptoms:** Frontend container in restart loop

**Solutions:**

1. **Check logs:**
   ```bash
   docker-compose logs frontend
   ```

2. **Common causes:**
   - Missing package.json
   - Invalid Dockerfile
   - Port conflict
   - Missing dependencies

3. **Rebuild from scratch:**
   ```bash
   docker-compose down
   docker-compose build --no-cache frontend
   docker-compose up frontend
   ```

## Platform-Specific Issues

### Windows (Docker Desktop)

- **Use WSL2 backend** (Settings > General > Use WSL 2)
- **Store code in WSL filesystem** for better performance
- **Named volume for node_modules** is critical

### macOS

- **File watching may hit limits** on large projects
- **Use polling** if native watching fails

### Linux

- **File watching limits:** increase inotify watches
- **Permissions:** ensure user has read/write access to mounted volumes

## Getting Help

If issues persist:
1. Check Docker Desktop status
2. Restart Docker Desktop
3. Run: `docker-compose down && docker-compose up --build`
4. Check GitHub Issues
5. Ask in team communication channel
