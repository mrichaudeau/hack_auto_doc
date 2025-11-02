# Frontend Development Guide

## Quick Start

```bash
# Start frontend service
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend

# Access application
# Frontend: http://localhost:3000
# Backend API (via proxy): http://localhost:3000/api/
```

## Hot Module Replacement (HMR)

Code changes are automatically detected and applied instantly:

1. Edit any file in `frontend/src/`
2. Save the file
3. Browser updates within 1 second (no full reload)
4. Component state preserved across updates

**Example:**
```jsx
// Edit frontend/src/App.jsx
function App() {
  return <h1>My Changes Appear Instantly!</h1>
}
```

## Debugging

### Browser DevTools

1. Open http://localhost:3000
2. Press F12 to open DevTools
3. Go to Sources tab
4. Navigate to webpack:// or vite:// section
5. Find your original .jsx files
6. Set breakpoints in original source code

Source maps are enabled automatically in development.

## API Integration

### Making API Requests

```jsx
import config from './config'

async function fetchData() {
  const response = await fetch(`${config.apiUrl}/health/`)
  const data = await response.json()
  return data
}
```

### API Proxy

All requests to `/api/*` are automatically proxied to backend:

- Frontend: `http://localhost:3000/api/health/`
- Proxied to: `http://backend:8000/api/health/`
- No CORS issues!

## Common Tasks

### Install New Package

```bash
docker-compose exec frontend npm install package-name
```

### Run Build

```bash
docker-compose exec frontend npm run build
```

### View Logs

```bash
docker-compose logs -f frontend
```

### Restart Frontend

```bash
docker-compose restart frontend
```

## Environment Variables

See `.env.frontend.example` for available variables.

Copy and customize:
```bash
cp .env.frontend.example .env.frontend
```

All environment variables must be prefixed with `VITE_` to be accessible in the application.

## npm Commands

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm run preview`: Preview production build

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable React components
│   ├── pages/          # Page components
│   ├── services/       # API client functions
│   ├── config.js       # Centralized configuration
│   ├── App.jsx         # Root component
│   └── main.jsx        # Entry point
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
└── package.json        # Dependencies and scripts
```

## Troubleshooting

See [Frontend Troubleshooting Guide](./frontend_troubleshooting.md) for common issues and solutions.
