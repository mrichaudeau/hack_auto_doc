# User Stories: Subscriptions Feature

**Feature:** Subject and Subscription Management
**Feature ID:** subscriptions
**Last Updated:** 2025-10-28

## Overview

This document provides an overview of all User Stories for the Subscriptions feature. The subscriptions system manages the catalog of technology monitoring subjects available to users and handles the subscription relationships between subjects and users. Subscription management is the **primary trigger** for content generation by the AI Pipeline.

**Total User Stories:** 7
**Estimated Total Effort:** 29 days
**Implementation Phases:** 3

## User Stories by Priority

### P1 - High (4 stories, 16 days)
Core personalization and discovery functionality required for platform operation.

| ID | Title | Effort | Status | Phase |
|----|-------|--------|--------|-------|
| [US-1](./US-1/user-story.md) | Admin Subject Catalog Management | 5 days | Draft | 1 |
| [US-2](./US-2/user-story.md) | View Active Subject Catalog | 3 days | Draft | 1 |
| [US-3](./US-3/user-story.md) | Subscribe to Subject | 5 days | Draft | 2 |
| [US-6](./US-6/user-story.md) | View My Subscriptions | 3 days | Draft | 3 |

### P2 - Medium (2 stories, 11 days)
Content triggering and subscription management features.

| ID | Title | Effort | Status | Phase |
|----|-------|--------|--------|-------|
| [US-4](./US-4/user-story.md) | Unsubscribe from Subject | 3 days | Draft | 2 |
| [US-5](./US-5/user-story.md) | Bootstrap Monitoring Task on New Subscription | 8 days | Draft | 2 |

### P3 - Low (1 story, 2 days)
Admin analytics and insights.

| ID | Title | Effort | Status | Phase |
|----|-------|--------|--------|-------|
| [US-7](./US-7/user-story.md) | Display Subscriber Count (Admin View) | 2 days | Draft | 3 |

## User Stories by Phase

### Phase 1: Subject Catalog Foundation (Days 1-8)
**Goal:** Establish subject management and user discovery capabilities
**Stories:** US-1, US-2
**Effort:** 8 days
**Status:** Draft

**Description:**
Admin subject catalog management and user discovery of available monitoring subjects. This phase establishes the foundation for personalization.

**Key Deliverables:**
- Subject model with validation and audit trail
- Django Admin interface for subject management
- REST API for subject discovery
- Database indexes for performance
- Pagination and filtering support
- API documentation

**Success Criteria:**
- Admins can create, modify, and archive subjects
- Users can view and discover active subjects
- Subject catalog API responds in < 100ms (P95)
- All acceptance criteria met for US-1 and US-2
- No N+1 query problems
- Pagination working smoothly

**Dependencies:**
- Bloc 1 (Authentication) - for admin role verification

### Phase 2: User Subscription & Content Triggering (Days 9-21)
**Goal:** Enable user personalization and content generation triggering
**Stories:** US-3, US-4, US-5
**Effort:** 16 days
**Status:** Draft

**Description:**
User subscription management with automatic triggering of content generation pipeline. This phase enables the core value proposition of personalized monitoring.

**Key Deliverables:**
- Subscription model with unique constraint
- REST APIs for subscribe/unsubscribe
- Celery integration for bootstrap task
- Redis distributed locking
- Audit logging and trail
- Error handling and retry logic
- Integration with Bloc 3 (AI Pipeline)

**Success Criteria:**
- Users can subscribe to subjects
- Bootstrap task triggered on new subscription
- Bootstrap tasks complete within 5 minutes (P95)
- Distributed locking prevents duplicates
- Users can unsubscribe from subjects
- All subscription actions audited
- All acceptance criteria met for US-3, US-4, US-5

**Dependencies:**
- Bloc 1 (Authentication)
- Bloc 3 (AI Pipeline) - for bootstrap task orchestration
- Redis for distributed locking
- Celery for async task execution

### Phase 3: Subscription Management & Analytics (Days 22-29)
**Goal:** User experience and admin insights
**Stories:** US-6, US-7
**Effort:** 7 days
**Status:** Draft

**Description:**
User subscription management views and admin analytics. This phase completes user experience and provides insights for catalog management.

**Key Deliverables:**
- My subscriptions endpoint with pagination
- Admin subscriber count display
- Caching for subscriber counts
- Performance optimization
- Complete test coverage
- UAT preparation

**Success Criteria:**
- Users can view their subscriptions
- Subscription list sorted by date
- Pagination working smoothly
- Admin can see subscriber counts
- Counts updated in real-time
- Performance: subscriber count display < 500ms
- All acceptance criteria met for US-6, US-7
- UAT passed

**Dependencies:**
- Phase 2 (subscriptions must exist)

## User Story Details

### US-1: Admin Subject Catalog Management (P1)

**As an** administrator
**I want to** create, modify, and archive monitoring subjects including their web sources
**So that** I can maintain a curated catalog of technology topics for users to monitor

**Key Features:**
- Subject creation with name, description, and web source URLs
- Subject modification capability
- Subject archiving (status change to "archived")
- Unique subject name constraint
- URL format validation for web sources
- Audit trail of all catalog changes
- Django Admin interface
- Batch operations support

**API Endpoints:**
- GET /api/admin/subjects/
- POST /api/admin/subjects/
- PATCH /api/admin/subjects/{id}/
- DELETE /api/admin/subjects/{id}/

**Depends On:** None
**Blocks:** US-2, US-7
**Related:** Authentication (admin role required)

**Technical Requirements:**
- Django Admin interface with custom ModelAdmin
- URL validation using URLField validators
- Audit logging with django-simple-history
- Database indexes on name field

---

### US-2: View Active Subject Catalog (P1)

**As a** user
**I want to** view the list of active monitoring subjects with their descriptions
**So that** I can discover and choose topics relevant to my professional interests

**Key Features:**
- Endpoint returns list of active subjects only
- Subject details: id, name, description, status
- Archived subjects excluded from results
- Results sorted alphabetically by name
- Pagination support (50 subjects per page)
- Performance: < 100ms response time (P95)
- Optional filtering by search term
- Subject count aggregation
- Subscriber count display (if US-7 complete)

**API Endpoints:**
- GET /api/subjects/ (authenticated)
- Query params: page, page_size, search, ordering

**Response Format:**
```json
{
  "count": 145,
  "next": "http://api.example.com/subjects/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Artificial Intelligence",
      "description": "AI and machine learning advancements",
      "subscriber_count": 234,
      "status": "active"
    }
  ]
}
```

**Depends On:** US-1
**Blocks:** US-3
**Related:** None

**Technical Requirements:**
- DRF pagination with page size 50
- Database index on status field
- Optimized queries (select_related/prefetch_related)
- Sorting by name and subscriber_count

---

### US-3: Subscribe to Subject (P1)

**As a** user
**I want to** subscribe to a monitoring subject with a single click
**So that** I can start receiving technology watch reports on that topic

**Key Features:**
- Endpoint creates subscription for authenticated user
- Request includes subject_id
- Subject added to user's subscription list
- API returns 201 Created with subscription details
- Cannot subscribe to archived subjects (400 error)
- Cannot create duplicate subscription (409 or idempotent)
- Frontend UI updates immediately
- Subscription timestamp recorded
- Triggers bootstrap monitoring task (US-5)

**API Endpoints:**
- POST /api/subscriptions/ (authenticated)
- DELETE /api/subscriptions/{id}/ (unsubscribe)

**Request Format:**
```json
{
  "subject_id": 1
}
```

**Response Format (201 Created):**
```json
{
  "id": 42,
  "subject_id": 1,
  "subject": {
    "id": 1,
    "name": "Artificial Intelligence",
    "description": "AI and machine learning advancements"
  },
  "created_at": "2025-10-28T10:30:00Z"
}
```

**Error Response (409 Conflict):**
```json
{
  "error": "duplicate_subscription",
  "message": "Already subscribed to this subject"
}
```

**Depends On:** US-1, US-2
**Blocks:** US-4, US-5, US-6
**Related:** Authentication (user auth required)

**Technical Requirements:**
- Django unique_together constraint on (user, subject)
- Signal triggers bootstrap task
- Subscription model tracks created_at timestamp
- Permission validation (authenticated users only)

---

### US-4: Unsubscribe from Subject (P2)

**As a** user
**I want to** unsubscribe from a monitoring subject
**So that** I stop receiving reports on topics no longer relevant to me

**Key Features:**
- Endpoint removes subscription for authenticated user
- API returns 204 No Content on success
- Subject removed from user's subscription list
- Unsubscribe does not affect monitoring if other subscribers remain
- Cannot unsubscribe from non-existent subscription (404 error)
- Frontend UI updates immediately
- Unsubscribe action audited

**API Endpoints:**
- DELETE /api/subscriptions/{id}/ (authenticated)

**Response:**
- 204 No Content (success)
- 404 Not Found (subscription doesn't exist or not user's)

**Error Response (404 Not Found):**
```json
{
  "error": "not_found",
  "message": "Subscription not found"
}
```

**Depends On:** US-3
**Blocks:** None
**Related:** None

**Technical Requirements:**
- Permission validation (user can only delete own subscriptions)
- Soft delete NOT required - hard delete acceptable
- No impact on subject monitoring for other subscribers
- Audit logging of unsubscribe action

---

### US-5: Bootstrap Monitoring Task on New Subscription (P2)

**As a** system
**I want to** trigger immediate monitoring task when first user subscribes to a subject
**So that** new subscribers receive an initial report quickly without waiting for scheduled cycle

**Key Features:**
- On subscription creation, system checks if monitoring task exists for subject
- If no task exists, Celery job queued immediately (bootstrap)
- Redis distributed lock prevents duplicate bootstrap tasks
- Bootstrap follows same pipeline as scheduled tasks (Bloc 3)
- If task already running, new subscription does not create duplicate
- Task execution logged with subject_id and trigger reason ("bootstrap")
- First report typically generated within 5 minutes of subscription
- Bootstrap task failure does not fail subscription
- Retry logic for failed bootstrap tasks (3 attempts)
- Timeout handling for stuck tasks

**Celery Task:**
- Function: `trigger_subject_monitoring(subject_id, trigger='bootstrap')`
- Queue: high_priority
- Retry: 3 attempts with exponential backoff
- Timeout: 5 minutes
- Lock timeout: 5 minutes

**Redis Lock:**
- Key format: `subject_monitoring_lock:{subject_id}`
- TTL: 5 minutes
- Prevents concurrent execution

**Logging:**
```
Task triggered: subject_id=1, trigger=bootstrap, timestamp=2025-10-28T10:30:00Z
Task result: status=completed, duration=180s
```

**Depends On:** US-3
**Blocks:** None
**Related:** Bloc 3 (AI Pipeline), Redis, Celery

**Technical Requirements:**
- Celery task definition with retry logic
- Redis lock implementation using SETEX
- Integration with Bloc 3 task orchestration
- Comprehensive logging
- Error handling and recovery
- Monitoring/alerting for queue depth and latency

---

### US-6: View My Subscriptions (P1)

**As a** user
**I want to** view list of all subjects I'm subscribed to
**So that** I can manage my monitoring topics and make informed decisions about adding/removing subscriptions

**Key Features:**
- Endpoint returns authenticated user's subscriptions
- Each subscription includes subject details (name, description) and subscription date
- Results sorted by subscription date (newest first)
- Response includes pagination (20 per page)
- Empty list returned for users with no subscriptions
- Requires authentication (JWT token)
- Performance: < 200ms response time (P95)
- Unsubscribe link/button available for each subscription

**API Endpoints:**
- GET /api/users/me/subscriptions/ (authenticated)
- Query params: page, page_size, ordering

**Response Format:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "subject": {
        "id": 1,
        "name": "Artificial Intelligence",
        "description": "AI and machine learning advancements",
        "status": "active"
      },
      "created_at": "2025-10-28T10:30:00Z"
    },
    {
      "id": 41,
      "subject": {
        "id": 2,
        "name": "Blockchain",
        "description": "Blockchain and distributed ledger technology",
        "status": "active"
      },
      "created_at": "2025-10-27T14:20:00Z"
    }
  ]
}
```

**Empty Response:**
```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

**Depends On:** US-3, US-4
**Blocks:** None
**Related:** None

**Technical Requirements:**
- DRF pagination with page size 20
- Optimized queries (select_related for subject)
- Sorting by created_at (DESC)
- Permission validation (users only see own subscriptions)

---

### US-7: Display Subscriber Count (Admin View) (P3)

**As an** administrator
**I want to** see subscriber count for each subject
**So that** I can evaluate community interest and make informed catalog management decisions

**Key Features:**
- Admin interface displays subscriber count next to each subject
- Count aggregated in real-time from subscription records
- Sorting available by subscriber count (high to low)
- Count includes only active subscriptions
- Zero shown for subjects with no subscribers
- Counts cached for 5 minutes to reduce database load
- Trend analysis (new subscriptions this week/month)
- Top subjects ranking
- Subscriber count in admin list view
- Subscriber count in admin detail view

**Admin Features:**
- Subject list with inline subscriber count
- Sort by subscriber_count
- Filter by count range (< 10, 10-50, 50+)
- Chart showing subscription trends
- Export subscriber data as CSV

**API Endpoint (Optional):**
- GET /api/admin/subjects/statistics/ (admin only)

**Response Format:**
```json
{
  "results": [
    {
      "id": 1,
      "name": "Artificial Intelligence",
      "subscriber_count": 234,
      "new_this_week": 12,
      "new_this_month": 45,
      "trend": "up"
    }
  ]
}
```

**Depends On:** US-1, US-3
**Blocks:** None
**Related:** None

**Technical Requirements:**
- Django annotate() with Count() aggregation
- Cache with 5-minute TTL
- Background task to refresh cache periodically
- Admin custom display filter
- Optional admin report dashboard

---

## Dependencies Graph

### Critical Path (Sequential)
```
US-1 -> US-2 -> US-3 -> US-5
```

### Subject Catalog Flow
```
US-1 (Create subjects)
  |
  v
US-2 (View subjects)
  |
  v
US-3 (Subscribe to subjects)
  |
  v
US-5 (Bootstrap content generation)
```

### Subscription Management Flow
```
US-3 (Subscribe)
  |
  +---> US-4 (Unsubscribe)
  |
  +---> US-5 (Bootstrap)
  |
  +---> US-6 (View my subscriptions)
```

### Admin Analytics Flow
```
US-1 (Create subjects) + US-3 (Users subscribe)
  |
  v
US-7 (View subscriber counts)
```

## Parallel Development Opportunities

### After Phase 1 (Catalog Complete)
These stories can be developed in parallel:
- **US-3, US-4** (Subscribe/Unsubscribe) - Main development team
- **US-5** (Bootstrap) - Can start once Bloc 3 provides integration interface

### After Phase 2 (Subscriptions Complete)
These stories can be developed in parallel:
- **US-6** (View My Subscriptions)
- **US-7** (Subscriber Count Display)

## External Dependencies

### Bloc 1 (Authentication)
**Affected Stories:** All (US-1 through US-7)
**Type:** Feature
**Required:** Yes
**Notes:** All user operations require authentication. Admin operations require admin role. Must be implemented first or in parallel.

### Bloc 3 (AI Pipeline)
**Affected Stories:** US-5
**Type:** Feature
**Required:** No (for MVP)
**Notes:** Required for bootstrap task execution. Can stub with logging initially. Core integration:
- Celery task: `trigger_subject_monitoring(subject_id, trigger='bootstrap')`
- Async execution via message broker
- Returns task_id for tracking

### Redis Server
**Affected Stories:** US-3, US-4, US-5
**Type:** Infrastructure
**Required:** Yes
**Notes:** Required for:
- Distributed locking (prevent duplicate bootstrap tasks)
- Celery broker
- Optional caching for subscriber counts

### PostgreSQL Database
**Affected Stories:** All
**Type:** Database
**Required:** Yes
**Notes:** Required for Subject and Subscription data persistence. Version 15+. Indexes needed on: status, user_id, subject_id.

### Celery Task Queue
**Affected Stories:** US-5
**Type:** Infrastructure
**Required:** Yes (for bootstrap)
**Notes:** Required for async bootstrap task execution. Integrated with Redis broker.

## Acceptance Criteria Summary

**Total Acceptance Criteria:** ~50 across all 7 stories

**By Category:**
- Functional criteria: ~25
- Technical criteria: ~12
- Security criteria: ~8
- Performance criteria: ~5

**Critical Success Factors:**
- Subject creation requires admin role
- Subscriptions tied to authenticated users
- No duplicate subscriptions allowed
- Bootstrap tasks complete within 5 minutes
- Distributed locking prevents concurrent processing
- All operations audited
- Performance targets met (< 100ms for catalog, < 200ms for subscriptions)
- Graceful error handling

## Testing Requirements

### Unit Tests
- > 80% code coverage for all subscription logic
- Subject model with validation
- Subscription model with unique constraint
- Bootstrap trigger logic
- Permission checks
- Audit logging

### Integration Tests
- Complete subject creation workflow
- Subject API listing with pagination
- User subscription creation and deletion
- Bootstrap task queuing with Celery
- Audit logging verification
- My subscriptions endpoint with authorization
- Duplicate subscription prevention

### End-to-End Tests
- Admin creates subject -> appears in catalog -> user discovers -> subscribes -> bootstrap triggered
- User browses subjects -> filters/sorts -> subscribes
- User views my subscriptions
- User unsubscribes -> subject removed from list
- Multiple users subscribe -> bootstrap only triggers once

### Performance Tests
- Load testing: 1000+ concurrent subscriptions
- Subject listing with 1000+ subjects
- Bootstrap task queue processing
- Database query optimization

### Security Tests
- SQL injection and XSS protection
- CSRF protection
- Authorization: admins only for subject management
- Authorization: users only manage own subscriptions
- Token validation

## Documentation

Each User Story includes comprehensive documentation:
- API specifications with request/response examples
- Database schema changes
- Security considerations
- Performance requirements
- Test scenarios
- Implementation guidance

For detailed information on each story, click the links in the tables above to view the full user-story.md files.

## Progress Tracking

**Overall Status:** Draft

**Phase 1 (Subject Catalog):** Not Started
**Phase 2 (Subscriptions & Bootstrap):** Not Started
**Phase 3 (Management & Analytics):** Not Started

**Next Steps:**
1. Review and approve all User Stories
2. Generate development tasks for US-1 (first story)
3. Set up development environment
4. Begin Phase 1 implementation

---

**Generated by:** Functional Spec Planner Plugin
**Source Document:** docs/po_input/subscriptions.md
**Last Updated:** 2025-10-28
