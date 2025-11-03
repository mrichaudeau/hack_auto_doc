# Frontend Development Guide

## Overview

The Technology Watch Platform frontend is a React single-page application (SPA) built with Vite. This guide covers the complete development workflow, from setup to deployment.

### Technology Stack

**Core Framework:**
- **React 18+**: Component-based UI library
- **Vite 5+**: Lightning-fast development server with HMR

**Development Tools:**
- **Node.js 20**: JavaScript runtime (Alpine Linux)
- **npm**: Package manager
- **Docker**: Containerized development environment

**Key Features:**
- ⚡ **Hot Module Replacement (HMR)**: Instant updates without losing state
- 🔌 **API Proxy**: Seamless backend integration without CORS
- 🗺️ **Source Maps**: Full debugging support
- 🎯 **Path Aliases**: Import from `@/components/...`

---

## Quick Start

### Prerequisites

- Docker Desktop 4.25+ or Docker Engine 24.0+
- Git
- Text editor (VS Code recommended)

### Initial Setup

1. **Clone repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Configure environment**:
   ```bash
   cp .env.frontend.example .env.frontend
   # Edit .env.frontend if needed (usually defaults are fine)
   ```

3. **Start services**:
   ```bash
   docker-compose up -d frontend backend
   ```

4. **Verify frontend is running**:
   - Open browser: http://localhost:3000
   - You should see the React welcome page

5. **Verify API proxy**:
   - Open browser console (F12)
   - Execute: `fetch('/api/').then(r => r.json()).then(console.log)`
   - You should see backend API response (no CORS errors)

---

## Development Workflow

### Starting Development

```bash
# Start only frontend (assumes backend is already running)
docker-compose up frontend

# Or start both frontend and backend
docker-compose up frontend backend

# Start in detached mode (background)
docker-compose up -d frontend backend
```

**Frontend will be available at:** http://localhost:3000

### Editing Code

1. **Open project** in your code editor

2. **Edit React components** in `frontend/src/`:
   ```
   frontend/src/
   ├── App.jsx          # Main application component
   ├── main.jsx         # Application entry point
   ├── config.js        # Environment configuration
   ├── components/      # Reusable components
   ├── pages/           # Page components
   ├── hooks/           # Custom React hooks
   └── utils/           # Utility functions
   ```

3. **Save file** - changes appear **instantly** in browser (HMR)

4. **No manual refresh needed** - React preserves component state

### Hot Module Replacement (HMR)

**What is HMR?**
HMR updates changed modules in the browser without a full page reload, preserving application state.

**How it works:**
1. You edit a `.jsx` or `.css` file
2. Vite detects the change
3. Only the changed module is replaced
4. Browser updates **immediately** (< 100ms)
5. Application state is preserved

**Example:**
```jsx
// Edit App.jsx
function App() {
  const [count, setCount] = useState(0);

  return (
    <div>
      <h1>Count: {count}</h1>  {/* Change this text */}
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

When you save, the heading text updates instantly, but `count` state remains unchanged!

### Making API Calls

The Vite proxy automatically forwards `/api/*` requests to the Django backend.

**Fetch API:**
```javascript
// GET request
fetch('/api/subjects/')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err));

// POST request
fetch('/api/subjects/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ name: 'AI Technology' }),
})
  .then(res => res.json())
  .then(data => console.log('Created:', data));
```

**Using environment variables:**
```javascript
// frontend/src/config.js
export const API_URL = import.meta.env.VITE_API_URL || '/api';

// In your component
import { API_URL } from '@/config';

fetch(`${API_URL}/subjects/`)
  .then(res => res.json())
  .then(data => console.log(data));
```

**No CORS issues!** The proxy handles cross-origin requests automatically.

### Viewing Logs

```bash
# Follow frontend logs in real-time
docker-compose logs -f frontend

# View last 50 lines
docker-compose logs --tail=50 frontend

# View logs with timestamps
docker-compose logs -f -t frontend
```

**What to look for:**
- `[vite] server started at http://localhost:3000` - Server ready
- `[vite] hot updated: /src/App.jsx` - HMR triggered
- `Proxying: GET /api/subjects` - API proxy working

### Stopping Services

```bash
# Stop frontend (keeps container)
docker-compose stop frontend

# Stop and remove frontend container
docker-compose down frontend

# Stop all services
docker-compose down
```

---

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # React entry point (renders App)
│   ├── config.js            # Environment configuration
│   ├── App.css              # App-specific styles
│   ├── index.css            # Global styles
│   │
│   ├── components/          # Reusable UI components
│   │   ├── Header.jsx
│   │   ├── Footer.jsx
│   │   └── Button.jsx
│   │
│   ├── pages/               # Page-level components
│   │   ├── HomePage.jsx
│   │   ├── DashboardPage.jsx
│   │   └── LoginPage.jsx
│   │
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.js
│   │   └── useApi.js
│   │
│   ├── utils/               # Utility functions
│   │   ├── api.js           # API client
│   │   └── formatters.js    # Data formatting
│   │
│   └── assets/              # Static assets
│       ├── images/
│       └── icons/
│
├── public/                  # Public static files (copied to dist/)
│   └── favicon.ico
│
├── tests/                   # Integration tests
│   ├── test_startup.sh
│   ├── test_hmr.sh
│   └── test_api_proxy.sh
│
├── Dockerfile               # Container image definition
├── vite.config.js           # Vite configuration (HMR, proxy, build)
├── package.json             # npm dependencies and scripts
├── index.html               # HTML entry point (loads main.jsx)
├── .dockerignore            # Files to exclude from Docker build
└── .gitignore               # Files to exclude from Git
```

---

## Configuration

### Environment Variables

Create `.env.frontend` from `.env.frontend.example`:

```bash
# Vite server configuration
VITE_API_URL=/api
VITE_APP_NAME=Technology Watch Platform
VITE_APP_VERSION=1.0.0

# Feature flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEBUG=true
```

**Usage in code:**
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
const appName = import.meta.env.VITE_APP_NAME;
```

**Important:** Only variables prefixed with `VITE_` are exposed to the frontend!

### Vite Configuration

The `vite.config.js` file controls:
- **HMR settings**: WebSocket configuration
- **API proxy**: Forwarding `/api/*` to backend
- **Source maps**: Debugging support
- **Path aliases**: Import shortcuts (`@/components/...`)

**Key sections:**
```javascript
// HMR configuration
server: {
  host: '0.0.0.0',     // Allow external access
  port: 3000,
  hmr: {
    protocol: 'ws',
    host: 'localhost',
    port: 3000,
  },
}

// API proxy
proxy: {
  '/api': {
    target: 'http://backend:8000',
    changeOrigin: true,
  },
}

// Path aliases
resolve: {
  alias: {
    '@': '/src',  // import Button from '@/components/Button'
  },
}
```

---

## Common Commands

### npm Scripts

```bash
# Run development server (inside container)
docker-compose exec frontend npm run dev

# Build for production
docker-compose exec frontend npm run build

# Preview production build
docker-compose exec frontend npm run preview

# Install new package
docker-compose exec frontend npm install <package-name>

# Remove package
docker-compose exec frontend npm uninstall <package-name>
```

### Container Management

```bash
# Rebuild container after package.json changes
docker-compose build frontend

# Restart container
docker-compose restart frontend

# Access container shell
docker-compose exec frontend sh

# View container resource usage
docker stats $(docker-compose ps -q frontend)
```

### Testing

```bash
# Run all integration tests
cd frontend/tests
./test_startup.sh && ./test_hmr.sh && ./test_api_proxy.sh

# Run individual tests
./frontend/tests/test_startup.sh    # Service startup
./frontend/tests/test_hmr.sh        # Hot module replacement
./frontend/tests/test_api_proxy.sh  # API proxy
```

---

## Best Practices

### Component Organization

**Use functional components with hooks:**
```javascript
import { useState, useEffect } from 'react';

function MyComponent({ title }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch('/api/data')
      .then(res => res.json())
      .then(setData);
  }, []);

  return <div>{/* component JSX */}</div>;
}
```

**Avoid class components** (use hooks instead).

### File Naming

- **Components**: PascalCase (e.g., `Header.jsx`, `LoginForm.jsx`)
- **Utilities**: camelCase (e.g., `formatDate.js`, `apiClient.js`)
- **Styles**: Same name as component (e.g., `Header.css`)

### Import Organization

```javascript
// 1. External libraries
import React, { useState } from 'react';
import axios from 'axios';

// 2. Internal components
import Header from '@/components/Header';
import Button from '@/components/Button';

// 3. Utilities and hooks
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/formatters';

// 4. Styles
import './MyComponent.css';
```

### State Management

**For simple state:** Use `useState`
```javascript
const [count, setCount] = useState(0);
```

**For complex state:** Use `useReducer`
```javascript
const [state, dispatch] = useReducer(reducer, initialState);
```

**For global state:** Context API or state management library (Redux, Zustand)

### Error Handling

```javascript
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Fetch failed:', error);
    // Show user-friendly error message
  }
}
```

---

## Troubleshooting

See [Frontend Troubleshooting Guide](./frontend_troubleshooting.md) for detailed solutions.

### Quick Fixes

**Issue:** Frontend not starting
```bash
# Check logs
docker-compose logs frontend

# Rebuild container
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

**Issue:** HMR not working
```bash
# Enable polling mode (add to docker-compose.yml frontend service)
environment:
  - CHOKIDAR_USEPOLLING=true

# Restart frontend
docker-compose restart frontend
```

**Issue:** API calls failing with CORS
```bash
# Verify proxy configuration
docker-compose exec frontend cat vite.config.js | grep -A 5 proxy

# Check backend is reachable
docker-compose exec frontend ping backend
```

---

## Additional Resources

**Official Documentation:**
- React: https://react.dev/
- Vite: https://vitejs.dev/
- Node.js: https://nodejs.org/

**Related Documentation:**
- [Frontend Troubleshooting Guide](./frontend_troubleshooting.md)
- [Backend API Documentation](./backend_api.md)
- [Docker Compose Setup](./00_setup_local_docker.md)

**Project Documentation:**
- User Story: `specs/local-development-environment/US-5/user-story.md`
- Task Breakdown: `specs/local-development-environment/US-5/tasks.md`
- Tests: `frontend/tests/README.md`

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
