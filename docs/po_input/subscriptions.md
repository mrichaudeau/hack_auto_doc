# Subject and Subscription Management

## Overview / Context

This feature is the core personalization component of the technology watch platform. It manages the catalog of monitoring subjects available to users and handles the subscription relationships between subjects and users. Subscription management is the **primary trigger** for content generation by the AI Pipeline.

**Target Users:**
- End users (technology professionals) who subscribe to subjects
- Administrators who manage the subject catalog

**Strategic Importance:**
- Enables personalized content delivery based on user interests
- Drives AI pipeline execution and resource allocation
- Foundation for recommendation engine functionality

## Functional Requirements

### Subject Catalog Management

**Administrative Control:**
- Only administrators can create, modify, or archive monitoring subjects (e.g., "Blockchain", "Data Security")
- Each subject includes: name, short description, status (active/archived), and web sources (URLs) for scraping
- Only subjects with "Active" status are visible and selectable by end users

### User Subscription Management

**Simple Interaction:**
- Users manage subscriptions via "My Account" page or dedicated panel
- Subscribe/unsubscribe actions require single click (toggle mechanism)
- Clear visibility of currently subscribed subjects

**Pipeline Triggering:**
- **On Subscribe:** System immediately checks if monitoring task exists for the subject. If not, triggers async task to collect and generate first report (bootstrap mechanism)
- **On Unsubscribe:** Does not stop monitoring cycle if at least one subscriber remains

### Dashboard Integration

- User dashboard displays reports only for subscribed subjects
- Filtering available by monitoring subject
- Direct link to report consultation (Bloc 4)

## User Stories

### US-1: Admin Subject Catalog Management
**As an** administrator
**I want to** create, modify, and archive monitoring subjects including their web sources
**So that** I can maintain a curated catalog of technology topics for users to monitor

**Acceptance Criteria:**
- [ ] Admin can create new subject with name, description, and web source URLs
- [ ] Admin can modify existing subject details
- [ ] Admin can archive subjects (status change to "archived")
- [ ] Active subjects appear in API and user interface
- [ ] Archived subjects are hidden from end users
- [ ] Subject creation validates URL format for web sources
- [ ] System logs all catalog changes for audit trail

**Priority:** P1

**Technical Notes:**
- Implement in Django Admin interface for rapid development
- Use Django REST Framework for API endpoints
- Validate URL format using URLField validators

---

### US-2: View Active Subject Catalog
**As a** user
**I want to** view the list of active monitoring subjects with their descriptions
**So that** I can discover and choose topics relevant to my professional interests

**Acceptance Criteria:**
- [ ] Endpoint `/api/subjects/` returns list of active subjects only
- [ ] Each subject includes: id, name, description, active status
- [ ] Archived subjects are excluded from results
- [ ] Response is sorted alphabetically by subject name
- [ ] Response time < 100ms (P95)
- [ ] API supports pagination for large catalogs

**Priority:** P1

**Technical Notes:**
- Use Django ORM filtering on status field
- Implement DRF pagination (50 subjects per page)
- Add database index on status field for performance

---

### US-3: Subscribe to Subject
**As a** user
**I want to** subscribe to a monitoring subject with a single click
**So that** I can start receiving technology watch reports on that topic

**Acceptance Criteria:**
- [ ] Endpoint `POST /api/subscriptions/` creates subscription
- [ ] Request requires authentication (JWT token)
- [ ] Request includes subject_id in payload
- [ ] Subject is added to user's subscription list
- [ ] API returns 201 Created with subscription details
- [ ] Cannot subscribe to archived subjects (400 Bad Request)
- [ ] Cannot create duplicate subscription (409 Conflict or idempotent behavior)
- [ ] Frontend updates UI to show "subscribed" state immediately

**Priority:** P1

**Technical Notes:**
- Use Django unique_together constraint on (user, subject)
- Signal/webhook triggers bootstrap task (see US-5)

---

### US-4: Unsubscribe from Subject
**As a** user
**I want to** unsubscribe from a monitoring subject
**So that** I stop receiving reports on topics no longer relevant to me

**Acceptance Criteria:**
- [ ] Endpoint `DELETE /api/subscriptions/<id>/` removes subscription
- [ ] Request requires authentication (JWT token)
- [ ] Subject is removed from user's subscription list
- [ ] API returns 204 No Content on success
- [ ] Unsubscribing does not affect monitoring if other users remain subscribed
- [ ] Cannot unsubscribe from non-existent subscription (404 Not Found)
- [ ] Frontend updates UI to show "unsubscribed" state immediately

**Priority:** P2

**Technical Notes:**
- Soft delete is NOT required - hard delete is acceptable
- No impact on existing reports or historical data

---

### US-5: Bootstrap Monitoring Task on New Subscription
**As a** system
**I want to** trigger immediate monitoring task when first user subscribes to a subject
**So that** new subscribers receive an initial report quickly without waiting for scheduled cycle

**Acceptance Criteria:**
- [ ] On subscription creation, system checks if monitoring task is scheduled for subject
- [ ] If no task exists, Celery job is queued immediately (bootstrap)
- [ ] Redis distributed lock prevents duplicate bootstrap tasks
- [ ] Bootstrap task follows same pipeline as scheduled tasks (Bloc 3)
- [ ] If task is already running, new subscription does not create duplicate
- [ ] Task execution logged with subject_id and trigger reason ("bootstrap")
- [ ] First report typically generated within 5 minutes of subscription

**Priority:** P2

**Technical Notes:**
- Use Redis cache.lock() with subject_id as key
- Celery task: `trigger_subject_monitoring(subject_id, trigger='bootstrap')`
- Link to AI Pipeline (Bloc 3) task orchestration

---

### US-6: View My Subscriptions
**As a** user
**I want to** view list of all subjects I'm subscribed to
**So that** I can manage my monitoring topics and make informed decisions about adding/removing subscriptions

**Acceptance Criteria:**
- [ ] Endpoint `/api/users/me/subscriptions/` returns user's subscriptions
- [ ] Each subscription includes: subject details (name, description), subscription date
- [ ] Results sorted by subscription date (newest first)
- [ ] Response includes pagination (20 per page)
- [ ] Empty list returned for users with no subscriptions
- [ ] Requires authentication (JWT token)

**Priority:** P1

**Technical Notes:**
- Use Django prefetch_related to optimize query
- Return embedded subject details to avoid additional requests

---

### US-7: Display Subscriber Count (Admin View)
**As an** administrator
**I want to** see subscriber count for each subject
**So that** I can evaluate community interest and make informed catalog management decisions

**Acceptance Criteria:**
- [ ] Admin interface displays subscriber count next to each subject
- [ ] Count aggregated in real-time from subscription records
- [ ] Sorting available by subscriber count (high to low)
- [ ] Count includes only active subscriptions
- [ ] Zero shown for subjects with no subscribers

**Priority:** P3

**Technical Notes:**
- Use Django annotate() with Count() aggregation
- Cache counts for 5 minutes to reduce database load
- Display in Django Admin list view

## Non-Functional Requirements

### Performance
- **RNF-PERF-002:** Subject catalog listing endpoint must respond in < 100ms (P95)
- Response time critical for user browsing experience
- Database query optimization required (indexing on status field)

### Availability
- **RNF-DISPO-001:** Subscription management system must maintain 99.9% uptime
- Critical path for user engagement and content triggering
- Requires robust error handling and monitoring

### Operational
- **RNF-OPE-002:** All subscription actions (subscribe/unsubscribe) must be logged
- Logging facilitates audit trail and user support
- Logs should include: timestamp, user_id, subject_id, action type

## Technical Constraints

### Technology Stack
- **Backend Framework:** Django 3.2+ with Django REST Framework
- **Database:** PostgreSQL 15 with django-simple-history for audit trail
- **Task Queue:** Celery with Redis broker
- **Authentication:** JWT tokens (django-rest-framework-simplejwt)

### Integration Requirements
- **Internal Dependencies:**
  - Authentication system (Bloc 1) for user identification
  - AI Pipeline (Bloc 3) for bootstrap task triggering
  - Report Consultation (Bloc 4) for dashboard filtering
- **External Dependencies:**
  - Redis for distributed locking and Celery broker
  - PostgreSQL for relational data storage

### Infrastructure
- Docker Compose for local development
- Redis service must be available before subscription operations
- Database migrations required for Subject and Subscription models

## Dependencies

### Internal Dependencies
- **Bloc 1 (Authentication):** Must be implemented first to provide user authentication
- **Bloc 3 (AI Pipeline):** Required for bootstrap task execution (can be stubbed initially)
- **Bloc 4 (Report Consultation):** Depends on subscription data for filtering

### External Dependencies
- **Redis:** Required for distributed locking and Celery task queue
- **PostgreSQL:** Database for storing subjects and subscriptions

### Blockers
- Cannot implement bootstrap mechanism (US-5) until AI Pipeline (Bloc 3) foundation is available
- Admin interface requires Django Admin setup and admin user creation

## Success Metrics

### Key Performance Indicators (KPIs)
- **Subscription Rate:** Target 70% of registered users subscribe to at least one subject within first week
- **Average Subscriptions per User:** Target 3-5 subjects per active user
- **Bootstrap Success Rate:** 95% of bootstrap tasks complete successfully within 5 minutes

### User Adoption Metrics
- Track daily active subscribers vs. total registered users
- Monitor subscription churn rate (unsubscribe actions per week)
- Measure time from registration to first subscription

### Technical Performance
- Subject catalog API response time (P50, P95, P99)
- Subscription API response time (P50, P95, P99)
- Bootstrap task queue depth and processing time

## Testing Strategy

### Test Coverage
- **Unit Tests:**
  - Subject model validation (active/archived status)
  - Subscription model unique constraint
  - API serializer validation
  - Bootstrap trigger logic

- **Integration Tests:**
  - Complete subscription flow (create → verify in database → check API response)
  - Unsubscribe flow with authorization checks
  - Admin subject management workflow
  - Bootstrap task queuing (mock Celery)

- **End-to-End Tests:**
  - User browses catalog → subscribes → receives first report
  - Admin creates subject → appears in user catalog → user subscribes
  - User unsubscribes → subject removed from dashboard

### User Acceptance Testing
- Admin tests subject creation, modification, and archiving in Django Admin
- End users test subscription flow in frontend application
- Verify bootstrap task execution by monitoring Celery logs

## Implementation Phases

### Phase 1: Foundation (Sprint 1)
- Subject and Subscription Django models
- Django Admin interface for subject management
- Basic API endpoints (list subjects, create/delete subscription)

### Phase 2: Core Features (Sprint 2)
- Bootstrap task triggering mechanism
- Redis distributed locking
- My subscriptions endpoint
- Logging and audit trail

### Phase 3: Polish (Sprint 3)
- Admin subscriber count display
- Performance optimization (caching, indexing)
- Comprehensive test coverage

## Rollout Strategy

- Deploy behind feature flag initially
- Enable for internal testing users first
- Monitor bootstrap task execution and performance
- Gradual rollout to all users

## Documentation Requirements
- [ ] API documentation (OpenAPI/Swagger) for all endpoints
- [ ] Admin user guide for subject catalog management
- [ ] Developer guide for bootstrap task integration with AI Pipeline

## Timeline
- **Phase 1:** 1 week (Foundation)
- **Phase 2:** 1 week (Core Features)
- **Phase 3:** 3 days (Polish)
- **Total:** ~2.5 weeks

## Stakeholders
- **Product Owner:** Defines subject categories and catalog strategy
- **Tech Lead:** Reviews architecture and integration patterns
- **Backend Team:** Implements API and task triggering logic
- **Frontend Team:** Builds subscription UI components
- **DevOps:** Configures Redis and Celery infrastructure
