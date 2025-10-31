# Backend API Documentation

## Base URL

**Development**: `http://localhost:8000/api/`

## Authentication

Authentication endpoints will be implemented in future user stories (Bloc 1: Authentication & Authorization).

## Available Endpoints

### Health Check

Check the health status of the backend service and its dependencies.

**Endpoint**: `GET /api/health/`

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "database": "ok",
  "redis": "ok"
}
```

**Status Codes**:
- `200 OK`: All services are healthy
- `503 Service Unavailable`: One or more dependencies are unavailable

**Example**:
```bash
curl http://localhost:8000/api/health/
```

### API Root

Access the Django REST Framework browsable API.

**Endpoint**: `GET /api/`

**Authentication**: Required (not yet implemented)

**Response**: HTML page with available API endpoints

**Example**:
```bash
curl http://localhost:8000/api/
```

### Admin Interface

Access the Django Admin interface for administrative tasks.

**URL**: `http://localhost:8000/admin/`

**Credentials** (development only):
- Username: `admin`
- Password: `admin`

**Features**:
- User and group management
- Session management
- Content type management
- Future: FinOps cost tracking, user management, etc.

## Error Handling

All API errors return JSON with the following format:

```json
{
  "error": "Error type",
  "detail": "Detailed error description",
  "status_code": 400
}
```

Common error status codes:
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service dependencies unavailable

## CORS

The API accepts cross-origin requests from:
- `http://localhost:3000` (frontend development server)

CORS headers included:
- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Access-Control-Allow-Credentials`

## Rate Limiting

Rate limiting is not yet implemented but will be added in future versions.

## Pagination

Pagination will follow Django REST Framework conventions:
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/resource/?page=2",
  "previous": null,
  "results": [...]
}
```

## Versioning

API versioning will be implemented in future releases using URL path versioning:
- `/api/v1/...`
- `/api/v2/...`

## Future Endpoints

The following endpoints will be implemented in upcoming user stories:

**Authentication** (Bloc 1):
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/refresh/` - Refresh JWT token
- `POST /api/auth/azure/` - Azure AD SSO

**Subscriptions** (Bloc 2):
- `GET /api/subjects/` - List available monitoring subjects
- `POST /api/subscriptions/` - Subscribe to a subject
- `DELETE /api/subscriptions/{id}/` - Unsubscribe from a subject
- `GET /api/subscriptions/` - List user subscriptions

**Reports** (Bloc 4):
- `GET /api/reports/` - List user's reports
- `GET /api/reports/{id}/` - Get report details
- `GET /api/reports/{id}/content/` - Get report content

**Recommendations** (Bloc 5):
- `GET /api/recommendations/` - Get personalized subject recommendations

**FinOps** (Bloc 6):
- `GET /api/costs/` - Get cost tracking data (admin only)
- `GET /api/costs/export/` - Export cost data to CSV (admin only)

## Development Notes

### Running Migrations

```bash
docker-compose exec backend python manage.py migrate
```

### Creating a Superuser

```bash
docker-compose exec backend python manage.py createsuperuser
```

### Django Shell

```bash
docker-compose exec backend python manage.py shell
```

### Checking Configuration

```bash
docker-compose exec backend python manage.py check
```

## Support

For issues or questions:
- Check logs: `docker-compose logs backend`
- Django Admin: http://localhost:8000/admin/
- Health Check: http://localhost:8000/api/health/
