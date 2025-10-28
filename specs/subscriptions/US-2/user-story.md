# User Story: View Active Subject Catalog

**Story ID:** US-2
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 3 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** user
**I want to** view the list of active monitoring subjects with their descriptions
**So that** I can discover and choose topics relevant to my professional interests

## Description

This user story implements the subject catalog endpoint that allows end users to discover and browse available monitoring topics. Users access a paginated list of all active subjects, with each subject displaying its name, description, and other relevant metadata. The endpoint excludes archived subjects and returns results sorted alphabetically for consistency. This is the user's entry point to the subscription feature, enabling them to see what monitoring topics are available.

The endpoint is designed for high performance (< 100ms response time) to ensure a smooth user experience when browsing the catalog.

## Acceptance Criteria

### Functional Criteria
- [ ] Endpoint `/api/subjects/` returns list of active subjects only
- [ ] Each subject includes: id, name, description, active status
- [ ] Archived subjects are excluded from results
- [ ] Response is sorted alphabetically by subject name
- [ ] Response time < 100ms (P95)
- [ ] API supports pagination for large catalogs
- [ ] Empty list returned when no active subjects exist
- [ ] Endpoint is publicly accessible (no authentication required for browsing)

### Technical Criteria
- [ ] Code follows Django REST Framework conventions
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering pagination and filtering
- [ ] Database query optimized (single query, no N+1 problems)
- [ ] Documentation includes API specifications

### UI/UX Criteria
- [ ] Results displayed in alphabetical order
- [ ] Pagination controls visible for large lists
- [ ] Subject cards display name, description, and metadata clearly
- [ ] Responsive design on mobile/tablet/desktop

### Performance Criteria
- [ ] Response time < 100ms (P95) for 1000 subjects
- [ ] Database index on status field enables fast filtering
- [ ] Pagination prevents loading excessive data

### Security Criteria
- [ ] No sensitive admin data exposed in response
- [ ] Rate limiting applied to prevent API abuse
- [ ] Input validation on pagination parameters

## Technical Details

### Components Affected
**Backend:**
- Subject serializers (DRF)
- Subject viewsets
- Query optimization

**Frontend:**
- Subject catalog component
- Pagination component
- Subject browser UI

**Database:**
- Subjects table (read only for this endpoint)

### API Changes

**New Endpoint:**
- `GET /api/subjects/`
  - **Query Parameters:**
    - `page` (optional, integer, default=1) - pagination page number
    - `page_size` (optional, integer, default=50, max=100) - results per page
  - **Response (200 OK):**
    ```json
    {
      "count": 42,
      "next": "http://api.example.com/api/subjects/?page=2",
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
  - **Error Response (400):**
    ```json
    {
      "error": "invalid_pagination",
      "message": "page_size must be <= 100"
    }
    ```

### Database Changes
**No new tables or fields required** - uses existing Subject model

**Query Optimization:**
- Index on `status` field: `CREATE INDEX idx_subject_status ON subjects(status);`
- Query: `Subject.objects.filter(status='active').order_by('name').values('id', 'name', 'description', 'status')`

### External Integrations
- None for this user story

## Implementation Notes

### Suggested Approach
1. Create SubjectSerializer (DRF) with required fields
2. Create SubjectViewSet with list() action
3. Override get_queryset() to filter only active subjects
4. Apply sorting by name
5. Configure DRF pagination (PageNumberPagination)
6. Add database index on status field
7. Implement response caching (optional, 5-minute TTL)
8. Write comprehensive tests

### Technical Considerations
- **Pagination:** Use DRF's PageNumberPagination with default 50 items per page
- **Filtering:** Use Django ORM `.filter(status='active')` for database-level filtering
- **Sorting:** Use `.order_by('name')` for alphabetical order
- **Performance:** Single database query should execute in < 50ms
- **Caching:** Consider caching entire response for 5 minutes to reduce database load
- **Rate Limiting:** Apply general API rate limiting to prevent abuse

### Known Challenges
- Caching invalidation when admins modify subject catalog
- Handling very large catalogs (1000+ subjects) with pagination
- Ensuring consistent ordering across paginated results

## Dependencies

### Depends On
- US-1: Admin Subject Catalog Management (subjects must exist first)
- Infrastructure: PostgreSQL database with indexes

### Blocks
- US-3: Subscribe to Subject (users browse catalog before subscribing)
- Frontend: Subject discovery/browsing features

## Test Scenarios

### Happy Path
1. User navigates to subject catalog page
2. API endpoint `/api/subjects/` is called
3. System queries database for active subjects
4. Results sorted alphabetically returned
5. User sees "AI and Machine Learning" at top of list
6. User sees pagination showing "Page 1 of 2"
7. Response time < 100ms

### Alternative Paths
1. User requests second page: `/api/subjects/?page=2`
   - System returns next 50 subjects (or fewer if last page)
2. User specifies custom page size: `/api/subjects/?page_size=25`
   - System returns 25 subjects per page
3. User requests with custom limit: `/api/subjects/?page_size=200`
   - System caps at 100 per page (max allowed)

### Error Scenarios
1. **Invalid Page Number:**
   - User requests `/api/subjects/?page=999`
   - System returns empty results or 404 (depending on implementation)

2. **Invalid Page Size:**
   - User requests `/api/subjects/?page_size=500`
   - System returns error: "page_size must be <= 100"

3. **Non-existent Subjects:**
   - All subjects are archived by admin
   - System returns: `{"count": 0, "results": []}`

4. **Database Unavailable:**
   - PostgreSQL connection fails
   - System returns 503 Service Unavailable

### Edge Cases
1. **Exactly One Subject:** Only single active subject exists
   - System returns list with one item
   - Pagination shows "Page 1 of 1"

2. **Very Long Description:** Subject description is 2000+ characters
   - System returns full description without truncation

3. **Special Characters in Names:** Subject name is "C++ and Rust"
   - System sorts correctly alphabetically
   - Response includes special characters without encoding issues

4. **Concurrent Subject Creation:** Admin creates subject while user browses
   - If caching enabled, new subject appears after cache TTL
   - If no caching, new subject appears immediately

## UI/UX Specifications

### Subject Catalog Display
1. Header displays "Available Monitoring Subjects"
2. Search/filter controls at top (optional for first release)
3. Subject list displays:
   - Subject name (clickable to view details or subscribe)
   - Description (first 150-200 characters)
   - "Subscribe" button
4. Pagination at bottom:
   - Previous/Next buttons
   - Page indicators
   - "Results per page" dropdown (25, 50, 100)
5. Empty state if no subjects:
   - Message: "No monitoring subjects available"

### Responsive Design
- Mobile: Single column, full-width subject cards
- Tablet: Two column layout
- Desktop: Three column layout with sidebar filters (future)

## Security Considerations

- **Authentication:** Endpoint is public (no authentication required)
- **Authorization:** All active subjects visible to all users
- **Data Validation:** Pagination parameters validated and bounded
- **Rate Limiting:** Apply API rate limit (e.g., 60 requests/minute per IP)
- **SQL Injection:** ORM parameterization prevents injection attacks

## Performance Requirements

- **Response Time:** < 100ms (P95) for up to 1000 subjects
- **Database Query Time:** < 50ms
- **JSON Serialization:** < 25ms
- **Throughput:** Support 100+ concurrent requests
- **Caching:** Optional 5-minute TTL for entire response

## Accessibility Requirements

- [ ] Keyboard navigation support (Tab through results)
- [ ] Screen reader compatibility (ARIA labels)
- [ ] Subject names and descriptions have proper semantic HTML
- [ ] Pagination buttons keyboard accessible
- [ ] Focus indicators visible on interactive elements
- [ ] Color contrast meets WCAG standards (4.5:1 for normal text)

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Filtering by status
  - Sorting by name
  - Pagination logic
- [ ] Integration tests written
  - Complete API response test
  - Pagination behavior
  - Performance test (verify <100ms response)
- [ ] Manual testing completed
  - Test endpoint with various page sizes
  - Test pagination with large catalogs
  - Verify archived subjects not returned
  - Test performance with 1000+ subjects
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation (OpenAPI/Swagger)
  - Database index creation documented
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<100ms P95)
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should subjects include subscriber count in this endpoint?
- [ ] Should subjects include web source URLs in list endpoint?
- [ ] Should search functionality be included in first release?
- [ ] What caching strategy is preferred (HTTP, Redis, etc.)?

### Assumptions
- Only active subjects should be returned (archived subjects filtered out)
- Alphabetical sorting improves discoverability
- Pagination required for catalogs larger than 50 subjects
- Public access (no authentication) is acceptable for browsing

### Out of Scope
- Advanced search or full-text search
- Subject categories or tagging
- Subject recommendations based on user profile
- Trending or most-subscribed subjects highlighting

## Related User Stories

- **US-1:** Admin Subject Catalog Management (creates subjects displayed here)
- **US-3:** Subscribe to Subject (users browse catalog before subscribing)
- **US-6:** View My Subscriptions (users manage subscribed subjects)
- **US-7:** Display Subscriber Count (displays popularity)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
