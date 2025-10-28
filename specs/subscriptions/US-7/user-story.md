# User Story: Display Subscriber Count (Admin View)

**Story ID:** US-7
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P3
**Effort Estimate:** 2 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 3

## User Story Statement

**As an** administrator
**I want to** see subscriber count for each subject
**So that** I can evaluate community interest and make informed catalog management decisions

## Description

This user story implements the subscriber count display feature for administrators in the Django Admin interface. Administrators can view the number of active users subscribed to each subject, helping them understand community engagement and popularity of monitoring topics. The display includes real-time aggregation from subscription records with optional caching to reduce database load. Administrators can also sort subjects by subscriber count to identify trending topics and make data-driven decisions about catalog management, promotion, and deprecation.

This feature provides critical business intelligence for platform growth and content strategy decisions.

## Acceptance Criteria

### Functional Criteria
- [ ] Admin interface displays subscriber count next to each subject
- [ ] Count aggregated in real-time from subscription records
- [ ] Sorting available by subscriber count (high to low)
- [ ] Count includes only active subscriptions
- [ ] Zero shown for subjects with no subscribers
- [ ] Subscriber count updated when subscriptions created/deleted
- [ ] Count hidden from regular users (admin only)
- [ ] Subject list can be filtered by subscriber count ranges (optional)

### Technical Criteria
- [ ] Code follows Django conventions
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering aggregation and sorting
- [ ] Database query optimized with Count() aggregation
- [ ] Documentation includes implementation details

### Admin Interface Criteria
- [ ] Column added to subject list view displaying count
- [ ] Column is sortable (click to sort by count)
- [ ] Count updates when admin adds/removes subscriptions
- [ ] Layout remains readable and professional
- [ ] Mobile-responsive admin interface

### Performance Criteria
- [ ] Subject list loads within 200ms with 1000 subjects
- [ ] Count aggregation query completes within 100ms
- [ ] Caching reduces database queries (5-minute TTL)
- [ ] No N+1 query problems

### Security Criteria
- [ ] Only admin users can view subscriber counts
- [ ] Subscriber count does not expose individual user identities
- [ ] Admin permission checks enforced

## Technical Details

### Components Affected
**Backend:**
- Subject admin class (list_display, list_filter, ordering)
- Subject serializers for API (optional)
- Query optimization with Count()

**Database:**
- Subscriptions table (unchanged)
- Subjects table (no schema changes)

### Implementation Details

**Django Admin Customization:**
- Subject admin list_display includes subscriber_count annotation
- Custom property or method for aggregation
- Admin sorting by count
- Optional filter by count range

**Aggregation Query:**
```python
from django.db.models import Count, Q

# In SubjectAdmin or custom manager
subjects_with_counts = Subject.objects.annotate(
    subscriber_count=Count('subscription', filter=Q(subscription__is_active=True))
).order_by('-subscriber_count')
```

**Django Admin Customization Code:**
```python
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'status', 'subscriber_count']
    list_filter = ['status', 'created_at']
    ordering = ['-subscriber_count']
    search_fields = ['name', 'description']

    def subscriber_count(self, obj):
        return obj.subscription_set.filter(is_active=True).count()
    subscriber_count.short_description = 'Subscribers'
    subscriber_count.admin_order_field = 'subscriber_count_annotation'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            subscriber_count_annotation=Count('subscription', filter=Q(subscription__is_active=True))
        )
        return queryset
```

### Database Changes
**No new tables or fields required** - uses existing models

**Query Optimization:**
- Index on subscriptions(is_active) for faster filtering: `CREATE INDEX idx_subscription_active ON subscriptions(is_active);`
- Composite index helpful: `CREATE INDEX idx_subscription_user_active ON subscriptions(subject_id, is_active);`

**Caching (Optional):**
- Cache key: `subject_subscriber_counts`
- TTL: 300 seconds (5 minutes)
- Invalidated on subscription create/delete

### API Changes (Optional)
**Extended Subject List for Admin API:**
- `GET /api/admin/subjects/` (admin only)
  - Includes `subscriber_count` field in response
  - Response:
    ```json
    {
      "results": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "name": "Kubernetes",
          "description": "Container orchestration...",
          "status": "active",
          "subscriber_count": 42
        },
        {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "name": "Blockchain",
          "description": "Blockchain technology...",
          "status": "active",
          "subscriber_count": 28
        }
      ]
    }
    ```

## Implementation Notes

### Suggested Approach
1. Override SubjectAdmin.get_queryset() to add Count() annotation
2. Add subscriber_count to list_display
3. Set admin_order_field for sorting functionality
4. Create method to format count display
5. Test aggregation with multiple subscriptions
6. Implement optional caching for performance
7. Document for admin users

### Technical Considerations
- **Aggregation:** Use Django's Count() with filter parameter to exclude inactive subscriptions
- **Admin Ordering:** Set admin_order_field to enable sorting from admin interface
- **Performance:** Aggregation at database level is efficient
- **Caching:** Optional for larger installations (1000+ subscriptions)
- **Queryset Optimization:** Must be applied in get_queryset() for admin list view
- **Sorting:** "Subscribers" column becomes sortable in admin list

### Alternative Implementations
1. **Custom Manager:**
   ```python
   class SubjectManager(models.Manager):
       def with_subscriber_counts(self):
           return self.annotate(
               subscriber_count=Count('subscription', filter=Q(subscription__is_active=True))
           )
   ```

2. **Property Method (Less Efficient):**
   ```python
   class Subject(models.Model):
       @property
       def subscriber_count(self):
           return self.subscription_set.filter(is_active=True).count()
   ```
   - Note: Not efficient for list displays (N+1 problem)

3. **Cache-Based Approach:**
   ```python
   def get_subscriber_count(subject_id):
       cache_key = f"subject_subscribers:{subject_id}"
       count = cache.get(cache_key)
       if count is None:
           count = Subscription.objects.filter(
               subject_id=subject_id,
               is_active=True
           ).count()
           cache.set(cache_key, count, 300)
       return count
   ```

### Known Challenges
- Determining optimal cache TTL (balance between freshness and performance)
- Handling cache invalidation when subscriptions change
- Performance with very large subscription tables (millions of records)
- Caching strategy across multiple admin users

## Dependencies

### Depends On
- US-1: Admin Subject Catalog Management (subjects must exist)
- US-3: Subscribe to Subject (subscriptions must exist)
- Infrastructure: PostgreSQL database

### Blocks
- None (independent feature for admin insights)

## Test Scenarios

### Happy Path
1. Admin navigates to Django Admin
2. Clicks "Subjects" in admin interface
3. Subject list displays with "Subscribers" column
4. Each subject shows subscriber count (e.g., "Kubernetes: 42 subscribers")
5. Admin clicks "Subscribers" column header
6. List re-sorts by subscriber count (descending)
7. Most subscribed subject appears at top
8. Zero subscribers shown as "0"

### Alternative Paths
1. **Filter by Status:**
   - Admin filters to show only "Active" subjects
   - Subscriber counts accurately reflect filtered view

2. **Search Within Results:**
   - Admin searches for subject "Kubernetes"
   - Subscriber count displayed for matching subject

3. **Bulk Actions with Counts:**
   - Admin selects multiple subjects
   - Subscriber counts visible before bulk action
   - Helps inform decisions about archival

### Error Scenarios
1. **No Subscriptions:**
   - Subject with zero subscribers displays "0"
   - No error message required

2. **Unsubscribe During Display:**
   - Admin viewing list while user unsubscribes
   - Count updates on next page refresh
   - No real-time updates (page refresh needed)

3. **Cache Staleness:**
   - Subscription created
   - Cache not yet invalidated
   - Count appears outdated
   - Resolved after cache TTL expires

### Edge Cases
1. **Very High Subscriber Count:**
   - Subject with 1000000+ subscribers
   - Number displays correctly without truncation

2. **Rapid Subscribe/Unsubscribe:**
   - User subscribes and unsubscribes rapidly
   - Count fluctuates
   - Settles to correct value after activity stops

3. **Concurrent Admin and User Activity:**
   - Admin viewing list while subscriptions added/removed
   - Count snapshot represents moment of query
   - Next refresh shows current state

4. **Soft-Deleted Subscriptions:**
   - If soft delete implemented, query must filter for is_active=True
   - Hard-deleted subscriptions automatically excluded

## UI/UX Specifications

### Admin Subject List Display
1. Column headers (left to right):
   - [Checkbox] Name | Status | Subscribers | Created | Actions
2. Subscriber column displays:
   - Number (right-aligned)
   - Icon showing trend (optional)
   - Green color for high count (optional)
3. Column is clickable/sortable
   - Click to sort ascending/descending
   - Visual indicator showing sort direction

### Admin List View
- Subject list table with new "Subscribers" column
- Column width appropriate for numbers
- Number right-aligned for readability
- Consistent with other Django Admin columns

### Sorting Behavior
- Default sort: Status, then Subscribers (descending)
- Click "Subscribers" header to toggle sort
- Visual indicator (arrow up/down) shows sort direction

## Security Considerations

- **Access Control:** Admin users only (Django admin permission)
- **Data Exposure:** Subscriber count is aggregate (no individual user data exposed)
- **Audit Trail:** Not required (read-only display)
- **Information Security:** Count is non-sensitive aggregate statistic

## Performance Requirements

- **List Display:** Subject list loads < 200ms with 1000 subjects
- **Query Time:** Count aggregation < 100ms
- **Caching:** Optional 5-minute TTL reduces database load
- **Sorting:** Sorting by count completes < 300ms

## Operational Monitoring

- **Metrics:**
  - Most subscribed subjects
  - Subject popularity trends
  - Subscriber churn per subject
- **Insights:**
  - Identify trending topics
  - Detect dead/unpopular subjects
  - Inform content strategy

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Count aggregation logic
  - Filtering active subscriptions
  - Sorting by count
- [ ] Integration tests written
  - Subject list display with counts
  - Sorting functionality
  - Cache invalidation (if caching implemented)
- [ ] Manual testing completed
  - View subject list in admin
  - Verify counts accurate
  - Test sorting by subscriber count
  - Subscribe/unsubscribe and verify count updates
  - Test with archived subjects
  - Verify non-admin users cannot see counts
- [ ] Performance testing completed
  - List loads < 200ms with 1000 subjects
  - Sorting completes < 300ms
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - Django Admin customization documented
  - Performance considerations documented
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should subscriber counts be visible in public API?
- [ ] Should trending subjects be highlighted or featured?
- [ ] Should there be alerts for sudden subscriber changes?
- [ ] Should subscriber count include soft-deleted subscriptions?

### Assumptions
- Only active (is_active=True) subscriptions counted
- Admin interface is primary display location
- Count updates on page refresh (not real-time)
- Caching is optional optimization (not required for MVP)
- Sorting by count uses database query (not post-fetch)

### Out of Scope
- Real-time subscriber count updates
- Trending indicators or badges
- Per-subject subscriber analytics dashboard
- Email alerts for milestone subscriber counts
- Historical subscriber count tracking

## Related User Stories

- **US-1:** Admin Subject Catalog Management (subject management context)
- **US-3:** Subscribe to Subject (creates subscribers)
- **US-4:** Unsubscribe from Subject (updates counts)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
