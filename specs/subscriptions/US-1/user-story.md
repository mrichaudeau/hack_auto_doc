# User Story: Admin Subject Catalog Management

**Story ID:** US-1
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 5 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As an** administrator
**I want to** create, modify, and archive monitoring subjects including their web sources
**So that** I can maintain a curated catalog of technology topics for users to monitor

## Description

This user story implements subject catalog management for administrators of the AI-powered Technology Watch Platform. Administrators have exclusive control over the creation, modification, and archival of monitoring subjects (e.g., "Blockchain", "Data Security"). Each subject includes essential metadata: name, short description, status (active/archived), and web source URLs for content scraping. Only subjects with "Active" status are visible and selectable by end users, allowing administrators to control which topics are available for subscription.

This capability is foundational to the platform's personalization model, as end users can only subscribe to subjects that administrators have created and activated.

## Acceptance Criteria

### Functional Criteria
- [ ] Admin can create new subject with name, description, and web source URLs
- [ ] Admin can modify existing subject details
- [ ] Admin can archive subjects (status change to "archived")
- [ ] Active subjects appear in API and user interface
- [ ] Archived subjects are hidden from end users
- [ ] Subject creation validates URL format for web sources
- [ ] System logs all catalog changes for audit trail
- [ ] Each subject can have multiple web source URLs for scraping

### Technical Criteria
- [ ] Code follows Django conventions and style guidelines
- [ ] Unit tests written (>80% coverage for validation logic)
- [ ] Integration tests covering subject management workflow
- [ ] Documentation updated with admin procedures

### UI/UX Criteria
- [ ] Django Admin interface is intuitive and user-friendly
- [ ] Subject list displays name, description, status, and subscriber count
- [ ] Inline editing supported for descriptions
- [ ] Web source URLs displayed with validation status
- [ ] Ability to bulk archive/reactivate subjects

### Performance Criteria
- [ ] Subject creation completes within 500ms
- [ ] Subject list loads within 200ms for 1000+ subjects
- [ ] Subject modification updates reflected immediately

### Security Criteria
- [ ] Only admin users can access subject management
- [ ] Admin actions logged with timestamp and user ID
- [ ] URL validation prevents malicious input
- [ ] Subject changes do not expose archived subjects to users

## Technical Details

### Components Affected
**Backend:**
- Subject model (Django ORM)
- Subject serializers (DRF)
- Admin views/viewsets
- URL validation validators

**Frontend:**
- Admin interface (Django Admin)

**Database:**
- Subjects table (new)

### API Changes

**New Model Fields:**
- Subject model:
  - `id` (UUID primary key)
  - `name` (CharField, max_length=200, unique)
  - `description` (TextField)
  - `status` (CharField, choices=[active, archived], default='active')
  - `created_at` (DateTimeField)
  - `updated_at` (DateTimeField)
  - `created_by` (ForeignKey to User)

- WebSource model:
  - `id` (UUID primary key)
  - `subject` (ForeignKey to Subject, cascade delete)
  - `url` (URLField)
  - `created_at` (DateTimeField)

**Django Admin Endpoints:**
- `/admin/subscriptions/subject/` - List and manage subjects
- Subject inline editing form with web sources

**API Endpoints (for frontend display):**
- `GET /api/admin/subjects/` - List all subjects (including archived)
  - Returns: id, name, description, status, created_at, updated_at, subscriber_count
- `POST /api/admin/subjects/` - Create new subject
- `PATCH /api/admin/subjects/{id}/` - Modify subject
- `DELETE /api/admin/subjects/{id}/` - Archive subject

### Database Changes
**New tables:**
- Subjects table:
  - `id` (UUID, primary key)
  - `name` (VARCHAR(200), unique, indexed)
  - `description` (TEXT)
  - `status` (VARCHAR(20), enum, indexed)
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)
  - `created_by_id` (INTEGER, FK to auth_user)

- WebSources table:
  - `id` (UUID, primary key)
  - `subject_id` (UUID, FK to subjects, ON DELETE CASCADE)
  - `url` (VARCHAR(2048))
  - `created_at` (TIMESTAMP)

### External Integrations
- None for this user story

## Implementation Notes

### Suggested Approach
1. Create Subject and WebSource Django models
2. Implement Subject admin class with inline WebSource editing
3. Add URL validation to WebSource model
4. Create Django admin customization:
   - Custom admin list display
   - Filters for status
   - Sorting by name and subscriber count
5. Implement audit logging (django-simple-history)
6. Create API endpoints for frontend display
7. Add comprehensive error handling

### Technical Considerations
- **URL Validation:** Use Django's URLValidator to ensure web sources are valid
- **Cascade Delete:** WebSources should cascade delete with Subject
- **Audit Trail:** Use django-simple-history for tracking changes
- **Indexing:** Add database index on status field for query performance
- **Uniqueness:** Subject names should be unique to avoid duplicates
- **Bulk Operations:** Support bulk archive/activate operations for efficiency

### Known Challenges
- URL validation may be too strict for dynamic/JavaScript-heavy URLs
- Determining appropriate timeout for URL validation checks
- Handling very long URLs (some may exceed 2000 characters)
- Managing web sources that may become invalid over time

## Dependencies

### Depends On
- Infrastructure: PostgreSQL database
- Framework: Django Admin setup
- Technology: django-simple-history for audit trail

### Blocks
- US-2: View Active Subject Catalog (requires subjects to exist)
- US-3: Subscribe to Subject (requires subjects to exist)
- US-6: View My Subscriptions (depends on subjects)
- US-7: Display Subscriber Count (depends on subject data)

## Test Scenarios

### Happy Path
1. Admin navigates to Django Admin
2. Clicks "Subjects" in the admin interface
3. Clicks "Add Subject"
4. Enters subject name: "Kubernetes"
5. Enters description: "Container orchestration and cloud infrastructure"
6. Adds three web sources:
   - https://kubernetes.io/blog/
   - https://www.kubernetesnetwork.io/
   - https://github.com/kubernetes/kubernetes/releases
7. Sets status to "Active"
8. Clicks "Save"
9. Subject appears in subject list
10. Subject is visible in user API endpoints
11. Admin can modify description
12. Changes are logged in history

### Alternative Paths
1. Admin archives subject by changing status to "archived"
   - Subject disappears from user-facing API
   - Existing subscriptions remain but display no content
2. Admin bulk archives multiple subjects by selecting and using admin action
3. Admin reactivates archived subject by changing status to "active"

### Error Scenarios
1. **Invalid URL:**
   - Admin enters malformed URL (e.g., "not a url")
   - System returns validation error: "Enter a valid URL"
   - Form rejects submission

2. **Duplicate Subject Name:**
   - Admin creates subject "AI"
   - Admin tries to create another subject named "AI"
   - System returns error: "Subject with this name already exists"

3. **Missing Required Fields:**
   - Admin attempts to save subject without name or description
   - System returns error highlighting required fields

4. **Empty Web Sources:**
   - Subject can be created without web sources (optional)
   - System allows creation and allows addition later

### Edge Cases
1. **Very Long Description:** Admin enters 5000+ character description
   - System accepts and stores without truncation

2. **Special Characters in Name:** Admin creates subject "C++"
   - System accepts special characters in subject names

3. **Same URL Multiple Times:** Admin adds identical URL twice for same subject
   - System allows (for potential redundancy) or prevents via unique constraint

4. **Concurrent Modifications:** Two admins modify same subject simultaneously
   - Last write wins (standard Django behavior)
   - Updated_at timestamp reflects latest change

## UI/UX Specifications

### Admin Interface Layout
1. Subject list view displays:
   - Subject name (clickable for edit)
   - Description (preview, first 100 characters)
   - Status badge (green for Active, gray for Archived)
   - Subscriber count
   - Created date
   - Edit/Delete actions
2. Add/Edit Subject form includes:
   - Name field (text input)
   - Description field (textarea)
   - Status dropdown (Active/Archived)
   - WebSources inline table (add rows dynamically)
   - Save/Cancel buttons
3. List filters on left sidebar:
   - Filter by Status (Active, Archived)
   - Filter by Created Date

### Design Assets
- Use Django Admin default styling
- Inline editing for WebSources
- "Add Another WebSource" link under sources list

## Security Considerations

- **Authentication:** Admin users only (checked by Django @admin_required)
- **Authorization:** Access restricted to staff/admin group
- **Data Validation:** URL validation to prevent injection attacks
- **Audit Logging:** All subject changes logged with admin user ID
- **Immutability:** Consider read-only audit history of changes

## Performance Requirements

- **Response Time:** Subject creation/modification < 500ms
- **List Loading:** Subject admin list < 200ms for 1000 subjects
- **Indexing:** Database index on status field for fast filtering

## Accessibility Requirements

- [ ] Keyboard navigation support for all admin forms
- [ ] Form labels properly associated with inputs
- [ ] Error messages announced to screen readers
- [ ] Status badges include text labels (not color-only)
- [ ] WebSource table has proper headers

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Subject model validation
  - WebSource URL validation
  - Status filtering logic
  - Admin permission checks
- [ ] Integration tests written
  - Complete subject creation workflow
  - Subject modification and archival
  - Admin access control verification
- [ ] Manual testing completed
  - Test subject creation with multiple URLs
  - Test subject archival
  - Verify archived subjects hidden from users
  - Test admin permission enforcement
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - Admin user guide for subject management
  - Database schema documentation
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should web sources be sortable within a subject (priority order)?
- [ ] Should there be a maximum number of web sources per subject?
- [ ] Should subject names be searchable from user API?
- [ ] Should there be subject categories/tags for better organization?

### Assumptions
- Admins have access to Django Admin interface
- URL validation should be strict (RFC 3986 compliant)
- Archived subjects should remain in database for historical tracking
- Subject names are case-insensitive for uniqueness checks

### Out of Scope
- Integration with external subject catalogs
- Subject versioning or rollback capabilities
- Multi-language support for subject names/descriptions
- Subject deprecation workflow

## Related User Stories

- **US-2:** View Active Subject Catalog (displays created subjects)
- **US-3:** Subscribe to Subject (users subscribe to managed subjects)
- **US-6:** View My Subscriptions (displays subscribed subjects)
- **US-7:** Display Subscriber Count (shows subject popularity)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
