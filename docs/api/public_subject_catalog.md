# Public Subject Catalog API (US-2)

**Version:** 1.0
**Last Updated:** 2025-01-14
**Endpoint:** `GET /api/subjects/`

## Overview

Public endpoint for browsing active technology monitoring subjects. No authentication required. Enables users to discover available topics before subscribing.

## Endpoint Details

### GET /api/subjects/

Returns paginated list of active subjects sorted alphabetically by name.

**URL:** `http://localhost:8000/api/subjects/`

**Method:** GET

**Authentication:** None required (public endpoint)

**Permissions:** AllowAny

## Query Parameters

| Parameter | Type | Required | Default | Max | Description |
|-----------|------|----------|---------|-----|-------------|
| `page` | integer | No | 1 | - | Page number for pagination |
| `page_size` | integer | No | 50 | 100 | Number of items per page |

## Response Format

### Success Response (200 OK)

```json
{
  "count": 42,
  "next": "http://localhost:8000/api/subjects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "AI and Machine Learning",
      "description": "Latest developments in artificial intelligence and machine learning frameworks",
      "status": "active"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Blockchain",
      "description": "Blockchain technology, cryptocurrency, and distributed ledgers",
      "status": "active"
    }
  ]
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `count` | integer | Total number of active subjects |
| `next` | string\|null | URL for next page (null if last page) |
| `previous` | string\|null | URL for previous page (null if first page) |
| `results` | array | Array of subject objects |

#### Subject Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Unique identifier for the subject |
| `name` | string | Subject name (e.g., "Kubernetes") |
| `description` | string | Detailed description of the technology topic |
| `status` | string | Subject status (always "active" in results) |

### Error Responses

#### 404 Not Found (Invalid Page)

```json
{
  "detail": "Invalid page."
}
```

**Cause:** Requested page number exceeds available pages

## Example Requests

### Bash/cURL

```bash
# Get first page (default)
curl http://localhost:8000/api/subjects/

# Get second page
curl http://localhost:8000/api/subjects/?page=2

# Custom page size (25 items)
curl http://localhost:8000/api/subjects/?page_size=25

# Maximum page size (100 items)
curl http://localhost:8000/api/subjects/?page_size=100
```

### JavaScript/Fetch

```javascript
// Fetch first page
fetch('http://localhost:8000/api/subjects/')
  .then(response => response.json())
  .then(data => {
    console.log(`Total subjects: ${data.count}`);
    console.log('Subjects:', data.results);
  });

// Fetch with pagination
async function fetchSubjects(page = 1, pageSize = 50) {
  const url = `http://localhost:8000/api/subjects/?page=${page}&page_size=${pageSize}`;
  const response = await fetch(url);
  return await response.json();
}

// Usage
const data = await fetchSubjects(2, 25);
```

### Python/Requests

```python
import requests

# Get first page
response = requests.get('http://localhost:8000/api/subjects/')
data = response.json()
print(f"Total subjects: {data['count']}")
print(f"Subjects on this page: {len(data['results'])}")

# Iterate through all pages
def fetch_all_subjects():
    subjects = []
    url = 'http://localhost:8000/api/subjects/'

    while url:
        response = requests.get(url)
        data = response.json()
        subjects.extend(data['results'])
        url = data['next']  # Next page URL or None

    return subjects

all_subjects = fetch_all_subjects()
print(f"Total subjects fetched: {len(all_subjects)}")
```

## Behavior

### Filtering
- **Active subjects only**: Only subjects with status='active' are returned
- **Archived subjects excluded**: Archived subjects are never visible via this endpoint

### Sorting
- Results are sorted **alphabetically by name** (A-Z)
- Sorting is case-sensitive at database level

### Pagination
- Default page size: 50 items
- Maximum page size: 100 items
- Invalid page numbers return 404
- Empty catalog returns empty results array with count=0

### Performance
- **Response time**: < 100ms (P95) for catalogs up to 1000 subjects
- **Query optimization**: Single database query with indexed status field
- **Concurrency**: Supports 100+ concurrent requests

## Security

### Public Access
- No authentication required
- Accessible to all users (authenticated or anonymous)
- Read-only endpoint (POST/PUT/DELETE not allowed)

### Data Exposure
**Exposed fields:**
- id, name, description, status (public information)

**NOT exposed:**
- web_sources (admin-only metadata)
- created_by, created_at, updated_at (admin-only timestamps)
- subscriber_count (future feature, US-3)

### Rate Limiting
- Not currently enforced for public browsing
- Future: May add rate limiting (e.g., 60 requests/minute per IP)

## Testing

```bash
# Run public API tests
cd backend && docker compose exec backend pytest apps/subscriptions/tests/test_public_api.py -v

# Expected: 20 tests passing
# Test coverage: Integration, security, performance, pagination
```

## OpenAPI/Swagger Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## Related Endpoints

- **Admin Subject Management**: `GET /api/admin/subjects/` (requires admin authentication)
- **Future**: `POST /api/subscriptions/` (US-3 - Subscribe to Subject)

## Notes

### Performance Optimization
- Status field indexed for fast filtering
- `.only()` used to fetch minimal fields
- Query execution time: < 50ms for 1000+ subjects

### Data Consistency
- Subjects are returned from primary database
- No caching currently implemented
- Changes by admins are immediately visible

### Future Enhancements (Out of Scope for US-2)
- Full-text search on name/description
- Category/tag filtering
- Trending/popular subjects
- Subject recommendations based on user profile
- Response caching with cache invalidation

## Troubleshooting

### Issue: Empty results despite subjects existing
**Cause:** All subjects are archived
**Solution:** Admin must activate subjects via `/api/admin/subjects/`

### Issue: Page not found (404)
**Cause:** Invalid page number
**Solution:** Check total pages: `Math.ceil(count / page_size)`

### Issue: Slow response time
**Cause:** Database not optimized
**Solution:** Verify status field index exists:
```sql
\d+ subscriptions_subject  -- Check for idx_subject_status
```

## Support

For issues or questions:
- Check test suite: `apps/subscriptions/tests/test_public_api.py`
- Review admin guide: `docs/admin/subject_management_guide.md`
- See implementation: `backend/apps/subscriptions/views.py` (PublicSubjectViewSet)

---

**Implementation:** US-2 - View Active Subject Catalog
**Related User Stories:** US-1 (Admin Management), US-3 (Subscribe to Subject)
