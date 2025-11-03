# Frontend Troubleshooting Guide

This guide covers common issues encountered when developing with the React frontend and their solutions.

---

## Table of Contents

1. [Service Startup Issues](#service-startup-issues)
2. [Hot Module Replacement (HMR) Issues](#hot-module-replacement-hmr-issues)
3. [API Proxy Issues](#api-proxy-issues)
4. [Build and Dependency Issues](#build-and-dependency-issues)
5. [Performance Issues](#performance-issues)
6. [Docker and Container Issues](#docker-and-container-issues)
7. [Cross-Platform Issues](#cross-platform-issues)

---

## Service Startup Issues

### Issue: Frontend container not starting

**Symptoms:**
- `docker-compose up frontend` fails
- Container exits immediately
- Error: "Container exited with code 1"

**Diagnostic:**
```bash
# Check container logs
docker-compose logs frontend

# Check container status
docker-compose ps frontend
```

**Solutions:**

**1. Port 3000 already in use:**
```bash
# Windows
netstat -ano | findstr :3000

# Mac/Linux
lsof -i :3000

# Kill process using port
kill <PID>

# Or change port in docker-compose.yml
ports:
  - "3001:3000"  # Map to different external port
```

**2. Dependency installation failed:**
```bash
# Rebuild with no cache
docker-compose build --no-cache frontend

# Check package.json is valid
docker-compose exec frontend cat package.json | python -m json.tool

# If npm install fails, try clearing cache
docker-compose exec frontend npm cache clean --force
docker-compose restart frontend
```

**3. Dockerfile syntax error:**
```bash
# Validate Dockerfile
docker build -t test-frontend ./frontend

# Check for typos or missing files
cat frontend/Dockerfile
```

---

### Issue: Frontend responds with 404

**Symptoms:**
- Container is running
- http://localhost:3000 returns 404 Not Found
- Browser shows "Cannot GET /"

**Diagnostic:**
```bash
# Check if Vite server is running
docker-compose logs frontend | grep "server started"

# Check if index.html exists
docker-compose exec frontend ls -la /app/index.html
```

**Solutions:**

**1. index.html missing:**
```bash
# Verify file exists in source
ls frontend/index.html

# Rebuild container
docker-compose build frontend
docker-compose up -d frontend
```

**2. Vite not serving correctly:**
```bash
# Check vite.config.js is valid
docker-compose exec frontend cat vite.config.js

# Restart with explicit host
docker-compose exec frontend npm run dev -- --host 0.0.0.0 --port 3000
```

---

## Hot Module Replacement (HMR) Issues

### Issue: Changes not reflected in browser

**Symptoms:**
- Edit `.jsx` or `.css` files
- Browser doesn't update
- Manual refresh shows changes

**Diagnostic:**
```bash
# Check if file watching is working
docker-compose logs frontend | grep -i "hot\|hmr\|update"

# Verify volume mount
docker inspect $(docker-compose ps -q frontend) --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{end}}'
```

**Solutions:**

**1. Enable polling mode (Windows/macOS):**

Edit `docker-compose.yml`:
```yaml
frontend:
  environment:
    - CHOKIDAR_USEPOLLING=true
```

Restart:
```bash
docker-compose restart frontend
```

**2. Verify volume mount is correct:**

Check `docker-compose.yml`:
```yaml
volumes:
  - ./frontend:/app              # ✓ Correct (bind mount)
  - frontend_code:/app            # ✗ Wrong (named volume)
```

**3. Increase polling interval (if slow):**

Edit `vite.config.js`:
```javascript
server: {
  watch: {
    usePolling: true,
    interval: 1000,  // Check every 1 second
  },
}
```

**4. Clear browser cache:**
```
Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

---

### Issue: HMR WebSocket connection failed

**Symptoms:**
- Console error: "WebSocket connection to 'ws://localhost:3000' failed"
- Changes require manual refresh
- Warning: "HMR disconnected"

**Diagnostic:**
```bash
# Check HMR configuration
docker-compose exec frontend cat vite.config.js | grep -A 10 hmr
```

**Solutions:**

**1. Update HMR client configuration:**

Edit `vite.config.js`:
```javascript
server: {
  hmr: {
    protocol: 'ws',           // or 'wss' for HTTPS
    host: 'localhost',        // Change to your hostname if needed
    port: 3000,
    clientPort: 3000,         // Must match external port
  },
}
```

**2. If using Docker Desktop on Windows:**
```javascript
server: {
  hmr: {
    host: 'host.docker.internal',  // Special Docker hostname
  },
}
```

**3. Check firewall settings:**
```bash
# Allow port 3000 through firewall
# Windows: Windows Defender Firewall -> Allow an app
# Mac: System Preferences -> Security & Privacy -> Firewall
```

---

## API Proxy Issues

### Issue: API calls return 404 or 500

**Symptoms:**
- `fetch('/api/subjects/')` returns 404
- Console error: "Failed to fetch"
- Proxy not forwarding to backend

**Diagnostic:**
```bash
# Check proxy configuration
docker-compose exec frontend cat vite.config.js | grep -A 10 proxy

# Test backend directly
curl http://localhost:8000/api/

# Test from within frontend container
docker-compose exec frontend wget -O- http://backend:8000/api/
```

**Solutions:**

**1. Verify backend is running:**
```bash
docker-compose ps backend
docker-compose logs backend | tail -20
```

**2. Check proxy target in vite.config.js:**
```javascript
proxy: {
  '/api': {
    target: 'http://backend:8000',  // Must match backend service name
    changeOrigin: true,
    secure: false,
  },
}
```

**3. Test Docker network connectivity:**
```bash
# Check containers are in same network
docker network inspect $(docker network ls -q -f name=app-network)

# Ping backend from frontend
docker-compose exec frontend ping -c 3 backend
```

**4. Check backend CORS settings** (if making direct requests):
```python
# backend/veille_tech/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

---

### Issue: API proxy returns CORS errors

**Symptoms:**
- Console error: "Access to fetch at 'http://backend:8000/api/' from origin 'http://localhost:3000' has been blocked by CORS policy"
- API calls fail with CORS error

**Solution:**

**This should NEVER happen with the proxy!** The proxy eliminates CORS issues.

If you're seeing CORS errors:
1. You're making direct requests to `http://localhost:8000` instead of `/api`
2. Proxy is not configured correctly

**Fix:**
```javascript
// ✗ Wrong - direct backend request (causes CORS)
fetch('http://localhost:8000/api/subjects/')

// ✓ Correct - goes through proxy (no CORS)
fetch('/api/subjects/')
```

---

## Build and Dependency Issues

### Issue: npm install fails

**Symptoms:**
- Container build fails with "npm ERR!"
- Dependency resolution errors
- Network timeouts

**Solutions:**

**1. Clear npm cache:**
```bash
docker-compose exec frontend npm cache clean --force

# Or rebuild with --no-cache
docker-compose build --no-cache frontend
```

**2. Use npm ci instead of npm install:**

Edit `Dockerfile`:
```dockerfile
# Faster and more reliable than npm install
RUN npm ci
```

**3. Increase npm timeout:**
```bash
docker-compose exec frontend npm config set fetch-timeout 60000
docker-compose exec frontend npm install
```

**4. Check npm registry:**
```bash
# Test npm registry connectivity
docker-compose exec frontend npm ping

# Use different registry if needed
docker-compose exec frontend npm config set registry https://registry.npmjs.org/
```

---

### Issue: Module not found errors

**Symptoms:**
- Error: "Cannot find module '@/components/Button'"
- Import statements failing
- Relative imports work but aliases don't

**Solutions:**

**1. Verify path alias in vite.config.js:**
```javascript
resolve: {
  alias: {
    '@': '/src',  // Maps '@' to '/src' directory
  },
}
```

**2. Restart Vite server:**
```bash
docker-compose restart frontend
```

**3. Check file actually exists:**
```bash
docker-compose exec frontend ls -la /app/src/components/Button.jsx
```

**4. Use correct import syntax:**
```javascript
// ✓ Correct
import Button from '@/components/Button';

// ✗ Wrong - missing file extension in some configs
import Button from '@/components/Button.jsx';
```

---

## Performance Issues

### Issue: Slow HMR updates (> 5 seconds)

**Symptoms:**
- File changes take long time to reflect
- Console shows delays between save and update

**Solutions:**

**1. Disable polling if on Linux:**
```yaml
# docker-compose.yml
frontend:
  environment:
    # Remove this on Linux for better performance
    # - CHOKIDAR_USEPOLLING=true
```

**2. Exclude node_modules from watching:**
```javascript
// vite.config.js
server: {
  watch: {
    ignored: ['**/node_modules/**', '**/dist/**'],
  },
}
```

**3. Increase Docker resources:**
- Docker Desktop → Settings → Resources
- Increase Memory to 4GB+
- Increase CPUs to 4+

**4. Use named volume for node_modules:**
```yaml
volumes:
  - ./frontend:/app
  - frontend_node_modules:/app/node_modules  # Faster on Windows/Mac
```

---

### Issue: High CPU usage

**Symptoms:**
- Docker Desktop using 80%+ CPU
- Fan running constantly
- System slow

**Solutions:**

**1. Check if file watching is too aggressive:**
```yaml
# Add to docker-compose.yml
frontend:
  environment:
    - CHOKIDAR_INTERVAL=1000  # Check every 1s instead of default
```

**2. Reduce Docker resource limits:**
```yaml
frontend:
  deploy:
    resources:
      limits:
        cpus: '0.5'      # Limit to 50% of 1 CPU
        memory: 512M
```

**3. Stop unused containers:**
```bash
docker-compose stop scheduler worker  # If not needed for frontend work
```

---

## Docker and Container Issues

### Issue: Container runs out of memory

**Symptoms:**
- Container crashes randomly
- Error: "JavaScript heap out of memory"
- npm install fails

**Solutions:**

**1. Increase Node.js memory limit:**
```dockerfile
# Dockerfile
ENV NODE_OPTIONS="--max-old-space-size=4096"
```

**2. Increase Docker memory limit:**
```yaml
# docker-compose.yml
frontend:
  deploy:
    resources:
      limits:
        memory: 1G    # Increase from 512M
```

**3. Use production build for testing:**
```bash
# Production build uses less memory
docker-compose exec frontend npm run build
docker-compose exec frontend npm run preview
```

---

### Issue: Cannot access frontend from host

**Symptoms:**
- Frontend works inside container
- Cannot access from browser at localhost:3000
- Connection refused

**Solutions:**

**1. Verify host is 0.0.0.0:**
```javascript
// vite.config.js
server: {
  host: '0.0.0.0',  // Listen on all interfaces
  port: 3000,
}
```

**2. Check port mapping:**
```yaml
# docker-compose.yml
ports:
  - "3000:3000"  # external:internal
```

**3. Test from container:**
```bash
# This should work inside container
docker-compose exec frontend wget -O- http://localhost:3000

# This should work from host
curl http://localhost:3000
```

---

## Cross-Platform Issues

### Windows-Specific Issues

**Issue: File watching not working**
- **Solution:** Enable polling (`CHOKIDAR_USEPOLLING=true`)
- **Solution:** Use WSL2 backend (Docker Desktop → Settings → Use WSL 2)

**Issue: Slow performance**
- **Solution:** Use named volume for node_modules
- **Solution:** Move project to WSL2 filesystem (`\\wsl$\Ubuntu\home\...`)

**Issue: Line ending issues (CRLF vs LF)**
```bash
# Configure git to use LF
git config --global core.autocrlf input

# Convert existing files
dos2unix frontend/**/*.js frontend/**/*.jsx
```

### macOS-Specific Issues

**Issue: File watching not reliable**
- **Solution:** Increase file watch limit:
  ```bash
  # Add to ~/.zshrc or ~/.bash_profile
  echo kern.maxfiles=65536 | sudo tee -a /etc/sysctl.conf
  echo kern.maxfilesperproc=65536 | sudo tee -a /etc/sysctl.conf
  sudo sysctl -w kern.maxfiles=65536
  sudo sysctl -w kern.maxfilesperproc=65536
  ```

**Issue: Slow Docker performance**
- **Solution:** Use `:cached` volume mount:
  ```yaml
  volumes:
    - ./frontend:/app:cached
  ```

### Linux-Specific Issues

**Issue: Permission denied**
```bash
# Fix ownership
sudo chown -R $USER:$USER frontend/

# Or run container as current user
docker-compose run --user $(id -u):$(id -g) frontend npm install
```

---

## Getting Help

### Diagnostic Commands

Run these commands to gather information:

```bash
# System info
docker --version
docker-compose --version
node --version  # Inside container: docker-compose exec frontend node --version

# Service status
docker-compose ps
docker-compose logs frontend --tail=50

# Container inspection
docker inspect $(docker-compose ps -q frontend)

# Network connectivity
docker-compose exec frontend ping backend
docker-compose exec frontend wget -O- http://localhost:3000

# File permissions
docker-compose exec frontend ls -la /app

# Environment variables
docker-compose exec frontend env | grep VITE
```

### Log Files to Check

1. **Frontend logs:** `docker-compose logs frontend`
2. **Build logs:** `docker-compose build frontend` output
3. **Browser console:** F12 → Console tab
4. **Network tab:** F12 → Network tab (for API calls)

### Reporting Issues

When reporting issues, include:

1. **Environment:**
   - OS (Windows/macOS/Linux)
   - Docker version
   - Docker Compose version

2. **Symptoms:**
   - What you expected to happen
   - What actually happened
   - Error messages (full text)

3. **Reproduction steps:**
   - Commands run
   - Files modified
   - Configuration used

4. **Diagnostic output:**
   - Container logs
   - docker-compose ps output
   - Browser console errors

---

## Additional Resources

- [Frontend Development Guide](./frontend_development.md)
- [Backend API Documentation](./backend_api.md)
- [Docker Compose Setup](./00_setup_local_docker.md)
- [Integration Tests](../../frontend/tests/README.md)

**Official Documentation:**
- Vite Troubleshooting: https://vitejs.dev/guide/troubleshooting.html
- Docker Docs: https://docs.docker.com/
- React Docs: https://react.dev/

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
