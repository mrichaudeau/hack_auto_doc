# Report Consultation and History

## Overview / Context

This feature provides the primary user interface for consuming technology watch intelligence. It delivers a personalized dashboard and comprehensive historical access to AI-generated reports. This is where users realize the value of the platform by accessing curated technology insights.

**Target Users:**
- End users (technology professionals) consuming generated reports
- Administrators monitoring content delivery and usage

**Strategic Importance:**
- Primary value delivery mechanism to end users
- User engagement and retention driver
- Demonstrates ROI of technology watch automation

## Functional Requirements

### Personalized Dashboard

The dashboard (`/dashboard`) is the rapid-access point for users.

**Default Filtering:**
- Displays only **most recent reports** linked to subjects the user is **subscribed to** (integration with Bloc 2)
- Unsubscribed subjects' reports are never visible

**Display Format:**
- Reports presented as cards for quick scanning
- Each card shows: title, key points (AI-synthesized summary), publication date, associated monitoring subject
- Clean, scannable visual layout

**Pagination:**
- Flow paginated for optimal performance
- Load new reports as user scrolls (infinite scroll) or via pagination buttons
- Default page size: 20 reports

### Detailed Report View

Each report card links to detailed view (`/reports/<id>`).

**Enriched Format:**
- Complete report content rendered from Markdown to HTML
- Professional typography and spacing

**Traceable Sources:**
- Link to original web source (collected by Firecrawl) prominently displayed
- Enables user verification and deeper exploration

### History and Traceability Management

Traceability is essential for technology watch.

**Implicit Historization:**
- All generated reports stored permanently
- `django-simple-history` used for version tracking (foundation for future manual edits)
- No report deletion by default

**Detailed History View:**
- User can select a monitoring subject and view all reports generated for that subject
- Sorted by date (newest to oldest)
- Paginated for performance (20 reports per page)

## User Stories

### US-1: Detailed Report View with Markdown Rendering
**As a** user
**I want to** click on a report title to access detailed view showing complete content and original sources
**So that** I can read the full technology intelligence and verify information against original sources

**Acceptance Criteria:**
- [ ] Endpoint `/api/reports/<id>/` returns complete report details
- [ ] Frontend route `/reports/<id>` displays detailed view
- [ ] Markdown content correctly rendered to HTML
- [ ] HTML rendering follows clean design system with proper typography
- [ ] Original web source URL displayed as clickable link
- [ ] Source link opens in new tab
- [ ] Report metadata displayed: subject name, publication date, author (system)
- [ ] 404 error if report ID does not exist
- [ ] 403 Forbidden if user not subscribed to report's subject (security check)

**Priority:** P1

**Technical Notes:**
- Use markdown-it or similar library for Markdown → HTML rendering
- Sanitize HTML output to prevent XSS
- Implement permission check in API view

---

### US-2: Paginated Dashboard for Subscribed Subjects
**As a** user
**I want to** see paginated list of latest reports on dashboard for my subscribed subjects
**So that** I can quickly scan new technology insights relevant to my interests

**Acceptance Criteria:**
- [ ] Endpoint `/api/dashboard/` returns reports for user's subscribed subjects only
- [ ] Reports sorted by publication date (newest first)
- [ ] Pagination: 20 reports per page
- [ ] Each report includes: id, title, key_points (summary), subject_name, published_at
- [ ] Cursor-based or offset pagination implemented
- [ ] Empty state message if user has no subscriptions
- [ ] Response time < 500ms (P95)
- [ ] Frontend displays reports as cards with smooth loading

**Priority:** P1

**Technical Notes:**
- Use Django ORM filtering: `Report.objects.filter(subject__in=user.subscriptions.all())`
- DRF pagination: CursorPagination for performance
- Prefetch related subjects to avoid N+1 queries

---

### US-3: Filter Dashboard by Specific Subject
**As a** user
**I want to** filter dashboard to show reports from only one monitoring subject
**So that** I can focus on a specific technology topic of current interest

**Acceptance Criteria:**
- [ ] Dashboard API accepts query parameter `?subject_id=<id>`
- [ ] When filtered, only reports from specified subject displayed
- [ ] Subject filter validates user is subscribed to subject (403 if not)
- [ ] Filter persists across pagination
- [ ] Clear filter option returns to all subscribed subjects
- [ ] Subject filter dropdown populated with user's subscribed subjects
- [ ] Filter state reflected in URL for bookmarking

**Priority:** P2

**Technical Notes:**
- Use DRF FilterBackend or manual query parameter handling
- Frontend: URL state management with query parameters
- Validate subject_id belongs to user's subscriptions

---

### US-4: Historical Report Listing for Subject
**As a** user
**I want to** access page showing all historical reports for a specific monitoring subject
**So that** I can review past technology insights and track topic evolution over time

**Acceptance Criteria:**
- [ ] Endpoint `/api/subjects/<id>/reports/` returns all reports for subject
- [ ] Reports sorted by publication date (newest to oldest)
- [ ] Paginated: 20 reports per page
- [ ] Requires user subscription to subject (403 if not subscribed)
- [ ] Includes all report metadata: title, summary, publication date
- [ ] Frontend route `/subjects/<id>/history` displays historical view
- [ ] Date range filter optional (future enhancement placeholder)
- [ ] Total count of reports displayed

**Priority:** P2

**Technical Notes:**
- Simple ORM query: `Report.objects.filter(subject_id=subject_id).order_by('-published_at')`
- Check user subscription in API permission class
- Consider caching total count for large datasets

---

### US-5: 403 Error on Unauthorized Report Access
**As a** system
**I want to** return 403 Forbidden when user attempts to access report for non-subscribed subject
**So that** content access is properly restricted and business model is enforced

**Acceptance Criteria:**
- [ ] Report detail API checks if user subscribed to report's subject
- [ ] If not subscribed, API returns 403 Forbidden with error message
- [ ] Error message: "You must be subscribed to this subject to view reports"
- [ ] Security check occurs at API level (not just frontend)
- [ ] Admin users can access all reports regardless of subscription
- [ ] Test coverage includes unauthorized access attempts
- [ ] Frontend displays friendly error message with subscribe button

**Priority:** P3

**Technical Notes:**
- Custom DRF permission class: `IsSubscribedToSubject`
- Check: `request.user.subscriptions.filter(subject=report.subject).exists()`
- Admin bypass: `or request.user.is_staff`

---

### US-6: Fast Dashboard Loading Performance
**As a** user
**I want to** dashboard initial page to load quickly
**So that** I have smooth user experience and can access information without frustration

**Acceptance Criteria:**
- [ ] Dashboard API response time < 500ms at P95
- [ ] Database query optimization: use select_related and prefetch_related
- [ ] Database indexes on: report.published_at, report.subject_id
- [ ] Frontend implements loading skeleton for perceived performance
- [ ] Images lazy-loaded if report cards include thumbnails
- [ ] API response gzipped for faster transfer
- [ ] Performance monitoring tracks P50, P95, P99 metrics
- [ ] Alert if P95 exceeds 500ms threshold

**Priority:** P3

**Technical Notes:**
- Use Django Debug Toolbar to identify slow queries
- Database indexes: `db_index=True` on foreign keys and ordering fields
- Consider Redis caching for frequent queries (cache dashboard per user for 1 minute)
- Frontend: React.lazy() or Vue's async components

## Non-Functional Requirements

### Performance
- **RNF-PERF-003:** Dashboard initial load (first page) must not exceed **500ms**
- Critical for user engagement and retention
- Optimization focus: database queries, network latency, rendering

### Security
- **RNF-SEC-003:** User must never access (even via API) reports from non-subscribed subjects
- Authorization check required on all report endpoints
- Implements subscription-based content access control
- Prevents data leakage and enforces business model

### User Experience
- **RNF-UI-001:** Report content rendering must use Markdown/HTML with clean, readable design
- Professional typography (font hierarchy, line spacing, margins)
- Responsive design for desktop and mobile
- Accessible design (WCAG 2.1 AA compliance)

## Technical Constraints

### Technology Stack
- **Backend Framework:** Django 3.2+ with Django REST Framework
- **Frontend Framework:** React SPA (Node 20)
- **Database:** PostgreSQL 15 with django-simple-history
- **Markdown Processing:** Python-markdown or markdown-it (JavaScript)
- **Authentication:** JWT tokens for API authorization

### Integration Requirements
- **Internal Dependencies:**
  - Authentication (Bloc 1) for user identification
  - Subscription Management (Bloc 2) for permission checks
  - AI Pipeline (Bloc 3) as source of report data
- **External Dependencies:**
  - PostgreSQL for report storage
  - Redis for optional caching

### Infrastructure
- Docker Compose for local development
- Database migrations for Report model with history tracking
- CDN for static assets (future consideration)

## Dependencies

### Internal Dependencies
- **Bloc 1 (Authentication):** Provides JWT authentication for API access
- **Bloc 2 (Subscription Management):** Defines which subjects user can access reports for
- **Bloc 3 (AI Pipeline):** Generates reports that this feature displays

### External Dependencies
- **PostgreSQL:** Database storage for reports
- **Redis (optional):** Caching layer for dashboard queries

### Blockers
- Cannot display reports until AI Pipeline (Bloc 3) is generating them
- Subscription check requires Subscription Management (Bloc 2) to be functional
- Authentication (Bloc 1) must be complete for secure API access

## Success Metrics

### Key Performance Indicators (KPIs)
- **Daily Active Readers:** Target 70% of subscribed users view dashboard daily
- **Average Reports Read per User:** Target 5 reports per session
- **Source Link Click-through Rate:** Target 20% of report views result in source click

### User Engagement Metrics
- Time spent on detailed report view (target: 2+ minutes)
- Scroll depth on dashboard (target: 80% of users scroll past first page)
- Return visitor rate (target: 60% return within 24 hours)

### Technical Performance
- Dashboard load time P95 < 500ms (monitored continuously)
- API error rate < 1%
- 403 authorization errors properly logged (not counted as application errors)

## Testing Strategy

### Test Coverage
- **Unit Tests:**
  - Report model and history tracking
  - API serializers with permission checks
  - Markdown rendering with XSS prevention
  - Pagination logic

- **Integration Tests:**
  - Dashboard API returns only subscribed reports
  - Report detail API enforces subscription check (403 for non-subscribed)
  - Historical report listing with pagination
  - Filter functionality

- **End-to-End Tests:**
  - User logs in → views dashboard → clicks report → reads content → clicks source
  - User attempts to access non-subscribed report → receives 403 error
  - Admin accesses all reports regardless of subscription
  - Filter dashboard by subject → see filtered results

### Performance Testing
- Load test dashboard API with 100 concurrent users
- Measure query performance with 10,000+ reports in database
- Profile Markdown rendering performance
- Test pagination at large offsets

### User Acceptance Testing
- End users test dashboard browsing and report reading
- Verify Markdown rendering quality across report types
- Test mobile responsive design
- Verify source links navigate correctly

## Implementation Phases

### Phase 1: Foundation (Week 1)
- Report model with django-simple-history
- Report detail API and view
- Basic Markdown rendering
- Permission checks

### Phase 2: Dashboard (Week 1)
- Dashboard API with subscription filtering
- Pagination implementation
- Subject filter functionality
- Frontend dashboard components

### Phase 3: Polish (3 days)
- Historical report listing
- Performance optimization (indexing, caching)
- 403 error handling and user messaging
- Comprehensive test coverage

## Rollout Strategy

- Deploy behind feature flag for beta testing
- Enable for small user group to test performance
- Monitor dashboard load times and API response times
- Gradual rollout to all users based on performance metrics

## Risk Mitigation

- **Performance Degradation:** Implement caching and database indexing proactively
- **High Database Load:** Use read replicas for dashboard queries if needed
- **Markdown Security:** Use trusted library with XSS protection built-in
- **User Confusion:** Provide clear empty states and onboarding flow

## Documentation Requirements
- [ ] API documentation (OpenAPI/Swagger) for all report endpoints
- [ ] User guide for navigating dashboard and reading reports
- [ ] Developer guide for Markdown rendering customization

## Timeline
- **Phase 1:** 1 week (Foundation)
- **Phase 2:** 1 week (Dashboard)
- **Phase 3:** 3 days (Polish)
- **Total:** ~2.5 weeks

## Stakeholders
- **Product Owner:** Defines dashboard UX and report presentation format
- **Tech Lead:** Reviews architecture and performance optimization
- **Backend Team:** Implements API and permission logic
- **Frontend Team:** Builds dashboard and report UI components
- **UX Designer:** Creates dashboard and report view designs
