# User Story: View My Subscriptions

**Story ID:** US-6
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 3 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** user
**I want to** view list of all subjects I'm subscribed to
**So that** I can manage my monitoring topics and make informed decisions about adding/removing subscriptions

## Description

This user story implements the user subscriptions list endpoint that displays all subjects a user has subscribed to. Users can access a paginated, chronologically sorted list of their subscriptions with full subject details. This endpoint is essential for subscription management, allowing users to review their monitored topics, unsubscribe from subjects, and understand their personalization profile.

The endpoint is authenticated (requires JWT) and only returns the current user's subscriptions, providing a personalized view of their monitoring portfolio.

## Acceptance Criteria

### Functional Criteria
- [ ] Endpoint `/api/users/me/subscriptions/` returns user's subscriptions
- [ ] Each subscription includes: subject details (name, description), subscription date
- [ ] Results sorted by subscription date (newest first)
- [ ] Response includes pagination (20 per page)
- [ ] Empty list returned for users with no subscriptions
- [ ] Requires authentication (JWT token)
- [ ] Returns only current user's subscriptions (no access to other users)
- [ ] Response includes unsubscribe action link/button

### Technical Criteria
- [ ] Code follows Django REST Framework conventions
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering authorization and pagination
- [ ] Database query optimized using prefetch_related
- [ ] Documentation includes API specifications

### UI/UX Criteria
- [ ] Subscriptions displayed in clear list format
- [ ] Subject details (name, description) clearly visible
- [ ] Subscription date visible for transparency
- [ ] "Unsubscribe" button easily accessible
- [ ] Responsive design on mobile/tablet/desktop
- [ ] Empty state message when no subscriptions exist

### Performance Criteria
- [ ] Response time < 200ms (P95) for 20 subscriptions
- [ ] Database query uses prefetch_related to minimize queries
- [ ] Pagination prevents loading excessive data

### Security Criteria
- [ ] Authentication required (JWT token validation)
- [ ] User can only view own subscriptions (no cross-user access)
- [ ] Authorization verified at query level

## Technical Details

### Components Affected
**Backend:**
- Subscription serializers (nested subject details)
- User subscription viewsets
- Query optimization with prefetch_related

**Frontend:**
- My Subscriptions page component
- Subscription list component
- Pagination controls
- Unsubscribe button integration

**Database:**
- Subscriptions table (read optimization)
- Subjects table (joined for details)

### API Changes

**New Endpoint:**
- `GET /api/users/me/subscriptions/`
  - **Authentication:** JWT token required
  - **Query Parameters:**
    - `page` (optional, integer, default=1)
    - `page_size` (optional, integer, default=20, max=50)
    - `ordering` (optional, choices=[-subscription_date, subject_name])
  - **Response (200 OK):**
    ```json
    {
      "count": 5,
      "next": "http://api.example.com/api/users/me/subscriptions/?page=2",
      "previous": null,
      "results": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440050",
          "subject": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Kubernetes",
            "description": "Container orchestration and cloud infrastructure",
            "status": "active"
          },
          "subscription_date": "2025-10-28T10:30:00Z",
          "unsubscribe_url": "/api/subscriptions/550e8400-e29b-41d4-a716-446655440050/"
        },
        {
          "id": "550e8400-e29b-41d4-a716-446655440051",
          "subject": {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "name": "AI and Machine Learning",
            "description": "Latest developments in artificial intelligence",
            "status": "active"
          },
          "subscription_date": "2025-10-27T14:15:00Z",
          "unsubscribe_url": "/api/subscriptions/550e8400-e29b-41d4-a716-446655440051/"
        }
      ]
    }
    ```
  - **Error Response (401 - Unauthorized):**
    ```json
    {
      "error": "authentication_required",
      "message": "Authentication credentials were not provided"
    }
    ```
  - **Error Response (400 - Invalid Pagination):**
    ```json
    {
      "error": "invalid_pagination",
      "message": "page_size must be <= 50"
    }
    ```

### Database Changes
**No new tables or fields required** - uses existing Subscription and Subject models

**Query Optimization:**
- Indexes ensure optimal performance:
  - Index on subscriptions(user_id): `CREATE INDEX idx_subscription_user ON subscriptions(user_id);`
  - Index on subscriptions(subscription_date): `CREATE INDEX idx_subscription_date ON subscriptions(subscription_date DESC);`
- Query pattern:
  ```python
  Subscription.objects
    .filter(user=request.user)
    .prefetch_related('subject')
    .order_by('-subscription_date')
  ```

### External Integrations
- None for this user story

## Implementation Notes

### Suggested Approach
1. Create SubscriptionListSerializer with nested SubjectSerializer
2. Create SubscriptionViewSet with custom list() action
3. Override get_queryset() to filter by current user
4. Apply prefetch_related('subject') for query optimization
5. Configure DRF pagination (20 per page, max 50)
6. Implement ordering by subscription_date (descending)
7. Add TestCase for authorization verification
8. Document API endpoint

### Technical Considerations
- **Authentication:** Verify JWT token and extract user from request
- **Filtering:** Use `.filter(user=self.request.user)` at database level
- **Optimization:** prefetch_related('subject') reduces queries to 2 (1 for subscriptions, 1 for subjects)
- **Pagination:** Default 20 per page, max 50 per page
- **Sorting:** Default by subscription_date descending (newest first)
- **Nested Serializer:** Include full subject details to avoid additional requests
- **Links:** Include unsubscribe URL/link in response for frontend

### Known Challenges
- N+1 query problem if prefetch_related not used
- Pagination consistency if subscriptions created during pagination
- Handling very large subscription lists (100+)
- Caching invalidation when subscriptions change

## Dependencies

### Depends On
- US-3: Subscribe to Subject (users must have subscriptions)
- Bloc 1: Authentication (user authentication required)
- Infrastructure: PostgreSQL database with indexes

### Blocks
- Frontend: My Subscriptions page display
- Bloc 4: Report Consultation (may filter by subscriptions)

## Test Scenarios

### Happy Path
1. Authenticated user navigates to "My Subscriptions" page
2. API endpoint `/api/users/me/subscriptions/` is called
3. System queries database for user's subscriptions
4. Results filtered by current user_id
5. Results sorted by subscription_date (descending)
6. System returns paginated list (20 per page)
7. Response includes pagination info
8. User sees list of subscribed subjects
9. Each subscription shows subject name, description, subscription date
10. "Unsubscribe" button available for each subscription

### Alternative Paths
1. **Second Page of Subscriptions:**
   - User has 25 subscriptions (exceeds 20 per page)
   - User clicks "Next" or requests `?page=2`
   - API returns next 5 subscriptions
   - Pagination shows "Page 2 of 2"

2. **Custom Page Size:**
   - User requests `/api/users/me/subscriptions/?page_size=50`
   - System returns 50 subscriptions per page (max allowed)

3. **No Subscriptions:**
   - New user with no subscriptions
   - API returns empty results: `{"count": 0, "results": []}`
   - Frontend displays: "You haven't subscribed to any topics yet"

### Error Scenarios
1. **Invalid JWT Token:**
   - Token expired or malformed
   - System returns 401 Unauthorized
   - Frontend redirects to login page

2. **Invalid Page Number:**
   - User requests `/api/users/me/subscriptions/?page=999`
   - System returns empty results or last page

3. **Excessive Page Size:**
   - User requests `/api/users/me/subscriptions/?page_size=1000`
   - System returns error: "page_size must be <= 50"

4. **Database Error:**
   - PostgreSQL connection fails
   - System returns 503 Service Unavailable

### Edge Cases
1. **Subscription Added During Pagination:**
   - User on page 1 of 10 pages
   - During pagination, new subscription added
   - Pagination offset may shift (acceptable behavior)

2. **Subject Archived After Subscription:**
   - User subscribed to active subject
   - Admin archives subject
   - Archived subject still appears in user's subscriptions (data integrity)
   - Subject status shows "archived" in response

3. **Subscription Deleted Concurrently:**
   - User viewing page 1 of 3 pages
   - Subscription deleted during pagination
   - Subsequent pages may have fewer results than expected

4. **Very Large Subscription List:**
   - Power user with 200+ subscriptions
   - Pagination works correctly (10 pages)
   - Response time remains < 200ms (due to prefetch_related)

## UI/UX Specifications

### My Subscriptions Page Layout
1. Header displays "My Subscriptions"
2. Subscription count displayed (e.g., "5 subscriptions")
3. List of subscriptions with:
   - Subject name (bold)
   - Subject description
   - Subscription date (relative: "Subscribed 2 days ago")
   - "Unsubscribe" button (right-aligned)
4. Pagination at bottom:
   - Previous/Next buttons
   - Page indicators
   - "Results per page" dropdown (20, 50)
5. Empty state if no subscriptions:
   - Icon or illustration
   - Message: "You haven't subscribed to any topics yet"
   - "Browse Subjects" link

### Responsive Design
- Mobile: Single column, full-width subscription cards, button below description
- Tablet: Same as mobile, or two columns if space permits
- Desktop: Single column with button on right

## Security Considerations

- **Authentication:** Requires valid JWT token in Authorization header
- **Authorization:** Query filtered by current user at database level
- **User Isolation:** User can only view own subscriptions (403 implied by filtering)
- **Data Validation:** Pagination parameters validated and bounded

## Performance Requirements

- **Response Time:** < 200ms (P95) for typical user with 20 subscriptions
- **Database Query Time:** < 100ms with prefetch_related optimization
- **JSON Serialization:** < 50ms
- **Throughput:** Support 100+ concurrent requests
- **Caching:** Optional 1-minute TTL for personal data

## Accessibility Requirements

- [ ] Keyboard navigation support (Tab through subscriptions and buttons)
- [ ] Screen reader compatibility (ARIA labels, semantic HTML)
- [ ] Subscription items have proper link semantics
- [ ] Unsubscribe buttons keyboard accessible (Enter to activate)
- [ ] Focus indicators visible on all interactive elements
- [ ] Color contrast meets WCAG standards
- [ ] Pagination controls keyboard navigable

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - User filtering (own subscriptions only)
  - Pagination behavior
  - Sorting by subscription_date
  - Empty list handling
  - Authorization checks
- [ ] Integration tests written
  - Complete subscription list retrieval
  - Multi-user isolation verification
  - Pagination across multiple pages
- [ ] Manual testing completed
  - Test endpoint with various page sizes
  - Test pagination with large subscription lists
  - Verify own subscriptions returned (not others)
  - Test with invalid JWT token
  - Test performance with 100+ subscriptions
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation (OpenAPI/Swagger)
  - Database index documentation
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<200ms P95)
- [ ] Load testing completed
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should subscription list include subscriber count or popularity metrics?
- [ ] Should users be able to reorder subscriptions (favorites)?
- [ ] Should unread reports be highlighted in subscription list?
- [ ] Should subscription list be cacheable (HTTP cache)?

### Assumptions
- Users authenticate via JWT tokens
- Subscriptions sorted by newest first (reverse chronological)
- Archived subjects can remain in user's subscriptions
- Pagination default is 20 items per page
- User can see all their subscriptions regardless of subject status

### Out of Scope
- Subscription notes or tags
- Subscription priority/weight
- Subscription statistics (# of reports received)
- Bulk unsubscribe operations
- Subscription ordering/favorites

## Related User Stories

- **US-2:** View Active Subject Catalog (users discover and subscribe)
- **US-3:** Subscribe to Subject (creates items in this list)
- **US-4:** Unsubscribe from Subject (removes items from this list)
- **Bloc 4:** Report Consultation (displays reports for subscribed subjects)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
