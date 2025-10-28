# User Story: React Frontend SPA Service

**Story ID:** US-5
**Feature:** Local Development Environment
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 2 Story Points
**Assigned To:** TBD
**Sprint:** TBD

## User Story Statement

**As a** developer
**I want** the React frontend running with hot module replacement
**So that** I can see UI changes instantly without manual refresh

## Description

This User Story establishes the React single-page application (SPA) frontend service that provides the user interface for the AI-powered Technology Watch Platform. The frontend communicates with the Django backend API to display technology reports, manage subscriptions, and provide authentication flows.

The service must support Hot Module Replacement (HMR), a critical developer experience feature that updates the browser instantly when code changes are detected—without requiring a full page refresh or losing application state. This dramatically improves frontend development productivity.

The frontend must be configured to proxy API requests to the backend service, enabling seamless communication between the SPA and API during local development. This setup mirrors production architecture where the frontend and backend are deployed separately.

Success means developers can edit React components, see changes reflected instantly in the browser, and test full user workflows with backend integration.

## Acceptance Criteria

### Functional Criteria
- [ ] React development server runs on port 3000
- [ ] Application accessible at `http://localhost:3000`
- [ ] Code changes trigger instant hot module replacement (no full page reload)
- [ ] API proxy configured to forward requests to backend at `http://backend:8000`
- [ ] Environment variables loaded from `.env.frontend`
- [ ] Node modules installed automatically on container start
- [ ] Build errors displayed in browser overlay with clear error messages
- [ ] Source maps enabled for debugging in browser DevTools

### Technical Criteria
- [ ] Frontend service defined in docker-compose.yml
- [ ] Base image: `node:20-alpine`
- [ ] Vite or Create React App configured for development server
- [ ] Source code mounted as volume for HMR
- [ ] API proxy configured: `/api` → `http://backend:8000/api`
- [ ] Environment variable: `VITE_API_URL=http://localhost:8000` or `REACT_APP_API_URL=http://localhost:8000`
- [ ] Package manager: npm or yarn with lockfile committed
- [ ] Development server command: `npm run dev` or `npm start`

### UI/UX Criteria (if applicable)
- Browser overlay displays build errors and warnings clearly
- Console logs show HMR status (connected, updating)
- No CORS errors when making API requests to backend

### Performance Criteria
- [ ] Frontend starts and becomes accessible within 15 seconds
- [ ] HMR updates reflect in browser within 1 second of code change
- [ ] Initial page load time < 2 seconds in development mode
- [ ] API proxy adds < 50ms latency to backend requests

## Technical Details

### Components Affected
- `docker-compose.yml` (frontend service definition)
- `frontend/Dockerfile` (new file)
- `frontend/package.json` (dependencies and scripts)
- `frontend/vite.config.js` or `frontend/craco.config.js` (dev server configuration)
- `.env.frontend` (environment configuration)

### API Changes
- None (frontend consumes existing backend API)

### Database Changes
- None

### External Integrations
- Backend API at `http://backend:8000/api/`
- Potentially: Microsoft Azure AD for SSO (MSAL library)

## Implementation Notes

### Suggested Approach

1. **Create frontend Dockerfile:**
   - Base: `node:20-alpine`
   - Set working directory to `/app`
   - Copy `package.json` and `package-lock.json`
   - Install dependencies with `npm install`
   - Expose port 3000
   - Command: `npm run dev` (Vite) or `npm start` (CRA)

2. **Configure docker-compose frontend service:**
   - Build from `./frontend/Dockerfile`
   - Mount source code: `./frontend:/app` for HMR
   - Mount `node_modules` as named volume (performance optimization)
   - Set environment variables from `.env.frontend`
   - Depend on backend service for API availability
   - Port mapping: `3000:3000`

3. **Configure API proxy:**
   - **Vite:** Configure `server.proxy` in `vite.config.js`:
     ```js
     server: {
       proxy: {
         '/api': {
           target: 'http://backend:8000',
           changeOrigin: true
         }
       }
     }
     ```
   - **Create React App:** Configure proxy in `package.json` or use `http-proxy-middleware`

4. **Set up environment variables:**
   - Create `.env.frontend.example` with:
     - `VITE_API_URL=http://localhost:8000` (Vite)
     - `REACT_APP_API_URL=http://localhost:8000` (CRA)
   - Document that developers must copy to `.env.frontend`

### Technical Considerations

**Performance:**
- Named volume for `node_modules` prevents performance issues on Windows Docker Desktop
- Vite typically faster than CRA for HMR and build times
- Source maps enabled for easier debugging but may slow initial load

**Security:**
- API proxy handles CORS automatically during development
- Environment variables for API URLs allow easy switching between environments
- No sensitive data in frontend (API keys remain on backend)

**Scalability:**
- Single frontend dev server sufficient for local development
- Production build handled separately (not in local dev environment scope)

**Backward Compatibility:**
- Node 20 LTS ensures long-term support and stability
- React 18+ required for latest features (Concurrent Mode, Suspense)

### Known Challenges

**Challenge:** `node_modules` volume mount performance on Windows
**Solution:** Use named volume for `node_modules` separate from source code volume

**Challenge:** HMR WebSocket connection may fail through Docker networking
**Solution:** Configure HMR to use polling or adjust WebSocket URL in Vite/CRA config

**Challenge:** Large number of files may slow file watching on macOS
**Solution:** Increase file watcher limits or use polling mode for dev server

## Dependencies

### Depends On
- US-1: Docker Compose Service Orchestration (must be completed first)
- US-4: Django Backend API Service (frontend calls backend API)

### Blocks
- None (frontend is consumer of backend services)

## Test Scenarios

### Happy Path
1. Developer runs `docker-compose up -d frontend`
2. Frontend container starts and installs dependencies
3. Development server starts on port 3000
4. Developer opens `http://localhost:3000`
5. React application loads and displays initial page
6. Developer edits `frontend/src/App.jsx`
7. Within 1 second, browser updates to reflect changes (no full reload)
8. Browser console shows "HMR connected" or similar message

### Alternative Paths
1. Developer opens browser DevTools Network tab
2. Makes API request to backend via frontend UI
3. Network tab shows request to `/api/health/` proxied to backend
4. Response received successfully without CORS errors

### Error Scenarios
1. **Syntax error in React component:** Developer introduces JSX syntax error
   - Expected: Browser shows error overlay with file path and line number
   - Console shows detailed error trace
   - After fix, HMR updates automatically

2. **Backend not running:** Frontend starts but backend down
   - Expected: Frontend loads successfully
   - API requests fail with network error
   - Clear error message displayed to developer in UI

3. **Port conflict:** Another service on port 3000
   - Expected: Docker reports port binding error
   - Resolution: Stop conflicting service or change port mapping

4. **Node modules installation failure:** Package resolution conflict
   - Expected: Container fails to start with npm error
   - Logs show clear error about conflicting dependencies

### Edge Cases
1. **API proxy timeout:** Backend responds slowly (> 30s)
   - Expected: Frontend shows loading indicator
   - Eventually times out with clear error message

2. **Large file change:** Developer modifies many files simultaneously
   - Expected: HMR processes all changes and updates browser
   - May take slightly longer but completes successfully

## UI/UX Specifications

### Browser Error Overlay
- Full-screen overlay with error details on build failures
- Clear file path and line number
- Stack trace for runtime errors

### HMR Status Indicators
- Console logs confirm HMR connection status
- Visual feedback (optional) when updates applied

### Design Assets
- To be provided by design team in future user stories
- Initial setup uses default React styling

## Security Considerations

- API requests proxied through development server to avoid CORS issues
- No API keys or secrets stored in frontend code
- Environment variables for configuration only (URLs, feature flags)
- Production build must not include development-only code or source maps

## Performance Requirements

- **Startup Time:** Frontend accessible within 15 seconds (P95)
- **HMR Update Time:** Code changes reflected within 1 second (P95)
- **Initial Page Load:** < 2 seconds in development mode
- **API Proxy Latency:** < 50ms overhead for proxied requests
- **Memory Usage:** Frontend dev server uses < 500MB RAM

## Accessibility Requirements

- React components follow semantic HTML structure
- ARIA labels added in feature-specific user stories
- Keyboard navigation support in all interactive elements
- Color contrast meets WCAG 2.1 Level AA standards (enforced in linting)

## Definition of Done

- [ ] Frontend service defined in docker-compose.yml with all required configuration
- [ ] Frontend Dockerfile created and building successfully
- [ ] Node dependencies installed and locked (package-lock.json committed)
- [ ] Development server configured and running
- [ ] HMR working for React component changes
- [ ] API proxy configured and routing requests to backend
- [ ] Source maps enabled for debugging
- [ ] Environment variables documented in .env.frontend.example
- [ ] Build errors display in browser overlay
- [ ] Code reviewed by tech lead
- [ ] Tested on Windows (Docker Desktop), macOS, and Linux
- [ ] Frontend accessible at http://localhost:3000
- [ ] API calls to backend working without CORS errors
- [ ] All acceptance criteria verified
- [ ] Documentation updated with frontend access instructions
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
- [ ] Vite or Create React App for development server?
- [ ] TypeScript or JavaScript for initial setup?
- [ ] Should we configure ESLint and Prettier at this stage?

### Assumptions
- Vite chosen for faster development experience (vs Create React App)
- JavaScript initially (TypeScript optional enhancement)
- Standard React 18+ patterns (hooks, functional components)

### Out of Scope
- Production build configuration (Dockerfile.prod)
- Static hosting setup (Nginx, CDN)
- Advanced bundling optimizations (code splitting, lazy loading)
- E2E testing setup (Cypress, Playwright)

## Related User Stories

- US-1: Docker Compose Service Orchestration (depends on this)
- US-4: Django Backend API Service (frontend calls API)
- US-8: Environment Configuration Management (related)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-01-27 | Functional Spec Planner | Initial version generated from PO input |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/00_local_development_environment.md
**GitHub Issue:** TBD
