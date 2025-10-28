# User Story: Subscribe to Subject

**Story ID:** US-3
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 5 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** user
**I want to** subscribe to a monitoring subject with a single click
**So that** I can start receiving technology watch reports on that topic

## Description

This user story implements the subscription creation mechanism that allows users to subscribe to monitoring subjects. When a user clicks the "Subscribe" button on any active subject, the system creates a subscription relationship between the user and that subject. The subscription is processed immediately with real-time UI feedback. Subscribing to a subject triggers the bootstrap mechanism to generate an initial monitoring report, ensuring users receive content shortly after subscription.

This is a core user engagement feature that directly triggers the AI content pipeline and enables personalized report delivery.

## Acceptance Criteria

### Functional Criteria
- [ ] Endpoint `POST /api/subscriptions/` creates subscription
- [ ] Request requires authentication (JWT token)
- [ ] Request includes subject_id in payload
- [ ] Subject is added to user's subscription list
- [ ] API returns 201 Created with subscription details
- [ ] Cannot subscribe to archived subjects (400 Bad Request)
- [ ] Cannot create duplicate subscription (409 Conflict or idempotent behavior)
- [ ] Frontend updates UI to show "subscribed" state immediately
- [ ] Bootstrap task triggered automatically on successful subscription
- [ ] Subscription includes metadata (subscription_date, subject details)

### Technical Criteria
- [ ] Code follows Django REST Framework conventions
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering subscription creation and validation
- [ ] Django unique_together constraint on (user, subject)
- [ ] Documentation includes API specifications

### UI/UX Criteria
- [ ] Subscribe button changes to "Unsubscribe" after successful subscription
- [ ] Loading state shown during subscription creation
- [ ] Success message displayed: "You are now subscribed to [Subject Name]"
- [ ] Error messages are clear and actionable
- [ ] Subscription state persists after page refresh

### Performance Criteria
- [ ] Subscription endpoint responds within 300ms
- [ ] Bootstrap task queued asynchronously (non-blocking)
- [ ] Duplicate detection is fast (< 100ms query)

### Security Criteria
- [ ] Authentication required (JWT token validation)
- [ ] User can only subscribe/unsubscribe own subscriptions
- [ ] Active user verification
- [ ] Subscription actions logged for audit trail

## Technical Details

### Components Affected
**Backend:**
- Subscription model (Django ORM)
- Subscription serializers (DRF)
- Subscription viewsets
- Bootstrap task triggering logic
- Permission/authentication classes

**Frontend:**
- Subscribe button component
- Subscription state management
- Success/error notification UI

**Database:**
- Subscriptions table (new)

### API Changes

**New Model Fields:**
- Subscription model:
  - `id` (UUID primary key)
  - `user` (ForeignKey to User, cascade delete)
  - `subject` (ForeignKey to Subject, cascade delete)
  - `subscription_date` (DateTimeField, auto_now_add=True)
  - `is_active` (BooleanField, default=True)
  - `created_at` (DateTimeField, auto_now_add=True)
  - `updated_at` (DateTimeField, auto_now=True)
  - Unique constraint: unique_together = ['user', 'subject']

**New Endpoint:**
- `POST /api/subscriptions/`
  - **Authentication:** JWT token required
  - **Request Body:**
    ```json
    {
      "subject_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
  - **Response (201 Created):**
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440099",
      "user_id": "1",
      "subject": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Kubernetes",
        "description": "Container orchestration...",
        "status": "active"
      },
      "subscription_date": "2025-10-28T10:30:00Z",
      "message": "Successfully subscribed to Kubernetes"
    }
    ```
  - **Error Response (400 - Archived Subject):**
    ```json
    {
      "error": "invalid_subject",
      "message": "Cannot subscribe to archived subjects"
    }
    ```
  - **Error Response (409 - Duplicate):**
    ```json
    {
      "error": "duplicate_subscription",
      "message": "You are already subscribed to this subject"
    }
    ```
  - **Error Response (401 - Unauthorized):**
    ```json
    {
      "error": "authentication_required",
      "message": "Authentication credentials were not provided"
    }
    ```
  - **Error Response (404 - Subject Not Found):**
    ```json
    {
      "error": "subject_not_found",
      "message": "Subject with this ID does not exist"
    }
    ```

### Database Changes
**New table:**
- Subscriptions table:
  - `id` (UUID, primary key)
  - `user_id` (INTEGER, FK to auth_user, ON DELETE CASCADE)
  - `subject_id` (UUID, FK to subjects, ON DELETE CASCADE)
  - `subscription_date` (TIMESTAMP)
  - `is_active` (BOOLEAN, default=true)
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)
  - **Unique Constraint:** UNIQUE(user_id, subject_id)
  - **Indexes:**
    - `CREATE INDEX idx_subscription_user ON subscriptions(user_id);`
    - `CREATE INDEX idx_subscription_subject ON subscriptions(subject_id);`
    - `CREATE INDEX idx_subscription_user_subject ON subscriptions(user_id, subject_id);`

### External Integrations
- Redis: Distributed locking for bootstrap task (see US-5)
- Celery: Async bootstrap task queuing

## Implementation Notes

### Suggested Approach
1. Create Subscription Django model with unique_together constraint
2. Create SubscriptionSerializer with validation
3. Create SubscriptionViewSet with create() action
4. Implement authentication check (@permission_classes decorator)
5. Validate subject exists and is active
6. Check for duplicate subscription
7. Create subscription record
8. Queue bootstrap task via Celery (non-blocking)
9. Return 201 with subscription details
10. Implement error handling for all scenarios

### Technical Considerations
- **Unique Constraint:** Use Django unique_together to prevent duplicates
- **Validation:** Check subject status before creating subscription
- **Async Triggering:** Bootstrap task queued immediately after subscription creation
- **Error Handling:** Return appropriate HTTP status codes (400, 409, 404, 401)
- **Transaction Consistency:** Wrap subscription creation in transaction
- **Logging:** Log subscription creation with user_id, subject_id, timestamp
- **Idempotency:** Could implement idempotent behavior (return existing if already subscribed)

### Known Challenges
- Race condition if user subscribes while bootstrap task still running
- Bootstrap task may fail; need retry logic and user notification
- Determining if duplicate subscription should return 409 or idempotent 201
- Handling subject deletion (cascade behavior)

## Dependencies

### Depends On
- US-1: Admin Subject Catalog Management (subjects must exist)
- US-2: View Active Subject Catalog (users discover subjects)
- Bloc 1: Authentication (user authentication required)
- Bloc 3: AI Pipeline (bootstrap task execution - see US-5)
- Infrastructure: Redis, Celery

### Blocks
- US-4: Unsubscribe from Subject (users must be able to unsubscribe)
- US-5: Bootstrap Monitoring Task (triggered by subscription)
- US-6: View My Subscriptions (displays subscribed subjects)
- Bloc 4: Report Consultation (reports generated for subscribed subjects)

## Test Scenarios

### Happy Path
1. Authenticated user navigates to subject catalog
2. User clicks "Subscribe" button on "Kubernetes" subject
3. Loading indicator appears
4. Request sent to `POST /api/subscriptions/` with subject_id
5. Server validates JWT token and extracts user_id
6. Server verifies subject exists and is active
7. Server checks no duplicate subscription exists
8. Server creates subscription record in database
9. Server queues bootstrap Celery task (non-blocking)
10. Server returns 201 with subscription details
11. Frontend receives response and updates button to "Unsubscribe"
12. Frontend displays success message: "You are now subscribed to Kubernetes"
13. Subscription appears in user's "My Subscriptions" list

### Alternative Paths
1. User subscribes to subject when first bootstrap task is still running
   - Server queues second subscription creation
   - Bootstrap task runs once (deduplicated via Redis lock)
2. User attempts to subscribe while subscription is being created
   - Frontend disables button
   - Duplicate POST request handled gracefully

### Error Scenarios
1. **Archived Subject:**
   - User tries to subscribe to archived subject
   - System returns 400 Bad Request
   - Error message: "Cannot subscribe to archived subjects"

2. **Duplicate Subscription:**
   - User already subscribed to subject
   - User clicks Subscribe again
   - System returns 409 Conflict
   - Error message: "You are already subscribed to this subject"

3. **Non-existent Subject:**
   - User manipulates frontend to send invalid subject_id
   - System returns 404 Not Found
   - Error message: "Subject with this ID does not exist"

4. **Unauthorized Access:**
   - User's JWT token is invalid or expired
   - System returns 401 Unauthorized
   - Frontend redirects to login page

5. **Database Error:**
   - Unique constraint violation (race condition)
   - System returns 409 Conflict
   - Error message: "Subscription already exists"

6. **Bootstrap Task Queue Failed:**
   - Celery broker unavailable
   - Subscription created but bootstrap task not queued
   - System returns 201 (subscription created)
   - Background job retries task creation

### Edge Cases
1. **Concurrent Subscriptions:** Two simultaneous subscription requests for same user+subject
   - First succeeds, second gets 409 Conflict
   - Database unique constraint prevents both from succeeding

2. **Subject Deleted After Browse:** User subscribes after admin deleted subject
   - Subscription creation fails with 404
   - Subject removal cascade deletes any subscriptions

3. **Very Rapid Unsubscribe/Resubscribe:** User unsubscribes then immediately resubscribes
   - Second request succeeds
   - Creates new subscription record
   - Previous bootstrap task may still be running (deduplication via Redis lock)

## UI/UX Specifications

### Subject Catalog Item
1. Subject card displays:
   - Subject name and description
   - "Subscribe" button (primary CTA)
2. On hover/focus:
   - Button changes color
   - Cursor indicates clickability
3. After click:
   - Button shows loading spinner
   - Button disabled
   - Cursor indicates loading state

### Success State
1. Button text changes to "Unsubscribe"
2. Button color changes (e.g., from blue to gray)
3. Toast notification appears: "You are now subscribed to [Subject Name]"
4. Toast disappears after 5 seconds
5. If user navigates away, subscription persists on return

### Error State
1. Button returns to "Subscribe" state
2. Error toast appears with message
3. User can retry immediately

## Security Considerations

- **Authentication:** Requires valid JWT token in Authorization header
- **Authorization:** Users can only create subscriptions for themselves
- **User Verification:** Active user account required
- **Rate Limiting:** Apply rate limiting to prevent subscription spam
- **Input Validation:** subject_id must be valid UUID format
- **Audit Logging:** Log all subscription creations with user_id, subject_id, timestamp, IP address

## Performance Requirements

- **Response Time:** < 300ms (P95) for subscription creation
- **Bootstrap Task:** Queued asynchronously (non-blocking, < 50ms)
- **Query Performance:** Duplicate check query < 100ms
- **Throughput:** Support 1000+ concurrent subscriptions per second

## Accessibility Requirements

- [ ] Subscribe button keyboard accessible (Enter to activate)
- [ ] Button focused state visible with clear indicator
- [ ] Loading state announced to screen readers ("Loading...")
- [ ] Success/error messages announce to screen readers
- [ ] Color not sole indicator of state (text label required)

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Subject validation (active/archived)
  - Duplicate subscription detection
  - Error response formatting
  - Bootstrap task triggering (mocked Celery)
- [ ] Integration tests written
  - Complete subscription creation flow
  - Authorization checks
  - Duplicate subscription handling
  - Bootstrap task queuing
- [ ] Manual testing completed
  - Subscribe to subject successfully
  - Attempt duplicate subscription
  - Try subscribing to archived subject
  - Verify bootstrap task queued
  - Test with invalid JWT
  - Test rapid subscribe/unsubscribe
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation (OpenAPI/Swagger)
  - Bootstrap task integration guide
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<300ms P95)
- [ ] Security review completed (authentication, authorization)
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should duplicate subscriptions return 409 or be idempotent (201)?
- [ ] Should bootstrap task failure prevent subscription creation?
- [ ] Should subscription include initial preference/settings?
- [ ] Should there be a subscription limit per user?

### Assumptions
- Users are authenticated via JWT tokens
- Archived subjects should reject subscriptions
- Bootstrap task failure does not rollback subscription
- One subscription per (user, subject) pair
- Subscriptions are soft-deleted or re-created on unsubscribe/resubscribe

### Out of Scope
- User preferences/settings per subscription
- Subscription notification preferences
- Subscription priority or weight
- Bulk subscription operations

## Related User Stories

- **US-1:** Admin Subject Catalog Management (creates subjects)
- **US-2:** View Active Subject Catalog (users discover subjects)
- **US-4:** Unsubscribe from Subject (inverse operation)
- **US-5:** Bootstrap Monitoring Task (triggered by subscription)
- **US-6:** View My Subscriptions (displays user subscriptions)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
