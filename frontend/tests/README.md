# Frontend Integration Tests

This directory contains integration tests for the React frontend SPA service.

## Test Scripts

### 1. Service Startup Test (`test_startup.sh`)
**Task:** TASK-5.11

Tests that the frontend service starts correctly and responds to health checks.

**Usage:**
```bash
./frontend/tests/test_startup.sh
```

**What it tests:**
- Frontend container is running
- Service responds to HTTP requests
- Returns HTTP 200 status code
- HTML contains React root element

**Requirements:**
- Docker Compose environment running
- Frontend service started

### 2. Hot Module Replacement Test (`test_hmr.sh`)
**Task:** TASK-5.12

Tests that Vite's HMR (Hot Module Replacement) is working correctly.

**Usage:**
```bash
./frontend/tests/test_hmr.sh
```

**What it tests:**
- Frontend service is running
- Volume mounts are configured correctly
- File watching is enabled
- File changes trigger HMR updates
- Logs show HMR activity

**Requirements:**
- Docker Compose environment running
- Source code mounted as bind volume
- Vite HMR enabled in `vite.config.js`

**Troubleshooting:**
If HMR is not working on Windows/macOS, add to frontend service:
```yaml
environment:
  - CHOKIDAR_USEPOLLING=true
```

### 3. API Proxy Test (`test_api_proxy.sh`)
**Task:** TASK-5.13

Tests that the Vite dev server correctly proxies API requests to the Django backend.

**Usage:**
```bash
./frontend/tests/test_api_proxy.sh
```

**What it tests:**
- Backend service is accessible
- Frontend service is running
- Proxy configuration is present in `vite.config.js`
- API requests are forwarded to backend
- Proxy logs show activity

**Requirements:**
- Docker Compose environment running
- Frontend and backend services started
- Proxy configured for `/api` routes

## Running All Tests

Run all tests in sequence:

```bash
cd frontend/tests
./test_startup.sh && ./test_hmr.sh && ./test_api_proxy.sh
```

Or run individually as needed.

## Test Prerequisites

### Start Required Services

```bash
# Start all services
docker-compose up -d

# Or start specific services
docker-compose up -d backend frontend
```

### Verify Services

```bash
# Check service status
docker-compose ps

# Check frontend logs
docker-compose logs -f frontend

# Check backend logs
docker-compose logs -f backend
```

## Expected Results

All tests should pass with exit code 0:

```
✓ All frontend startup tests passed!
✓ HMR functionality test passed!
✓ API proxy integration test passed!
```

## Common Issues

### Issue: Frontend not starting
**Symptoms:** `test_startup.sh` fails

**Solutions:**
1. Check logs: `docker-compose logs frontend`
2. Verify port 3000 is not in use: `netstat -ano | findstr :3000` (Windows) or `lsof -i :3000` (Mac/Linux)
3. Rebuild container: `docker-compose build frontend`

### Issue: HMR not working
**Symptoms:** File changes not reflected, no HMR messages

**Solutions:**
1. Enable polling (Windows/macOS):
   ```yaml
   environment:
     - CHOKIDAR_USEPOLLING=true
   ```
2. Verify volume mount is bind mount (not named volume for source code)
3. Check `vite.config.js` has `watch` configuration

### Issue: API proxy failing
**Symptoms:** `test_api_proxy.sh` returns HTTP errors

**Solutions:**
1. Verify backend is running: `docker-compose ps backend`
2. Check Docker network: `docker network inspect <network-name>`
3. Test connectivity: `docker-compose exec frontend ping backend`
4. Review proxy config in `vite.config.js`

## Manual Testing

### Manual HMR Test

1. Start services:
   ```bash
   docker-compose up frontend backend
   ```

2. Open browser: http://localhost:3000

3. Open browser console (F12)

4. Edit `frontend/src/App.jsx`:
   ```jsx
   // Add a comment or change text
   <h1>Hello World!</h1>
   ```

5. Save file

6. Watch console for: `[vite] hot updated`

7. Verify changes appear without page refresh

### Manual API Proxy Test

1. Open browser: http://localhost:3000

2. Open browser console (F12)

3. Execute API call:
   ```javascript
   fetch('/api/')
     .then(res => res.json())
     .then(data => console.log('API Response:', data))
     .catch(err => console.error('API Error:', err))
   ```

4. Verify no CORS errors

5. Check network tab shows request to `/api/`

## Test Coverage

| Test | Coverage |
|------|----------|
| **Service Startup** | Container health, HTTP response, React mount point |
| **HMR** | File watching, volume mounts, hot updates |
| **API Proxy** | Backend connectivity, request forwarding, CORS elimination |

## References

- **User Story:** `specs/local-development-environment/US-5/user-story.md`
- **Task Breakdown:** `specs/local-development-environment/US-5/tasks.md`
- **Vite Config:** `frontend/vite.config.js`
- **Docker Compose:** `docker-compose.yml`

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
