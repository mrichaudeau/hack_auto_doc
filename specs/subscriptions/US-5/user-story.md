# User Story: Bootstrap Monitoring Task on New Subscription

**Story ID:** US-5
**Feature:** Subject and Subscription Management
**Status:** Draft
**Priority:** P2
**Effort Estimate:** 8 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 2

## User Story Statement

**As a** system
**I want to** trigger immediate monitoring task when first user subscribes to a subject
**So that** new subscribers receive an initial report quickly without waiting for scheduled cycle

## Description

This user story implements the bootstrap mechanism that ensures users don't have to wait for the regular scheduled monitoring cycle to receive their first report. When a user subscribes to a subject, the system checks if a monitoring task is already scheduled for that subject. If not, it immediately queues an async Celery task to collect and synthesize initial content using the AI Pipeline. Redis distributed locking prevents duplicate bootstrap tasks from running concurrently if multiple users subscribe to the same subject within a short time window.

The bootstrap task follows the same pipeline as scheduled tasks, using the AI agents to collect, filter, synthesize, and index content. Typically, the first report is generated within 5 minutes of subscription.

## Acceptance Criteria

### Functional Criteria
- [ ] On subscription creation, system checks if monitoring task is scheduled for subject
- [ ] If no task exists, Celery job is queued immediately (bootstrap)
- [ ] Redis distributed lock prevents duplicate bootstrap tasks
- [ ] Bootstrap task follows same pipeline as scheduled tasks (Bloc 3)
- [ ] If task is already running, new subscription does not create duplicate
- [ ] Task execution logged with subject_id and trigger reason ("bootstrap")
- [ ] First report typically generated within 5 minutes of subscription
- [ ] Task failure does not prevent subscription creation
- [ ] Retry mechanism implemented for failed bootstrap tasks

### Technical Criteria
- [ ] Code follows Django and Celery conventions
- [ ] Unit tests written (>80% coverage with mocked Celery)
- [ ] Integration tests covering bootstrap triggering
- [ ] Redis distributed locking verified
- [ ] Logging captures all task execution details
- [ ] Documentation includes integration with AI Pipeline

### Operational Criteria
- [ ] Task execution monitored via Celery task events
- [ ] Failed tasks generate alerts for ops team
- [ ] Task queue depth and processing time tracked
- [ ] Bootstrap success rate tracked (target 95%)

### Performance Criteria
- [ ] Bootstrap triggering adds < 50ms to subscription API response
- [ ] Task queued within 100ms of subscription creation
- [ ] No blocking operations in subscription endpoint

### Security Criteria
- [ ] Celery task validates subscription exists and is active
- [ ] Task execution logged with audit trail
- [ ] Web scraping respects robots.txt and rate limits
- [ ] Task cannot be triggered manually by users

## Technical Details

### Components Affected
**Backend:**
- Subscription creation signal/hook
- Celery task definitions
- Redis client for distributed locking
- Task logging and monitoring
- Connection to AI Pipeline (Bloc 3)

**Infrastructure:**
- Celery worker pool
- Redis for locking and broker
- Task queue monitoring

**Database:**
- Subscriptions table (unchanged)
- Audit log for task execution

### Task Definition

**Celery Task:**
- `trigger_subject_monitoring(subject_id, trigger='bootstrap')`
  - **Parameters:**
    - `subject_id` (UUID) - Subject to monitor
    - `trigger` (str) - 'bootstrap' or 'scheduled'
  - **Returns:**
    - `{"status": "started", "subject_id": "...", "task_id": "..."}`
  - **Retry Logic:**
    - Max retries: 3
    - Backoff: exponential (60s, 300s, 900s)
  - **Timeout:** 300 seconds (5 minutes)

**Redis Lock:**
- Lock key: `subject_monitoring_lock:{subject_id}`
- Lock TTL: 360 seconds (6 minutes)
- Acquire timeout: 0 (non-blocking)

### Database Changes
**No new tables required** - uses existing models

**Audit Table (Optional):**
- TaskExecution table:
  - `id` (UUID, primary key)
  - `subject_id` (UUID, FK to subjects)
  - `trigger_type` (CharField, enum=[bootstrap, scheduled])
  - `triggered_by_subscription_id` (UUID, FK to subscriptions, nullable)
  - `task_id` (CharField, Celery task ID)
  - `started_at` (DateTimeField)
  - `completed_at` (DateTimeField, nullable)
  - `status` (CharField, enum=[queued, running, completed, failed])
  - `error_message` (TextField, nullable)

### External Integrations
- Redis: Distributed locking
- Celery: Async task execution
- Bloc 3 (AI Pipeline): Task orchestration and execution

## Implementation Notes

### Suggested Approach
1. Create Celery task `trigger_subject_monitoring` function
2. Implement Redis distributed lock acquisition
3. In subscription create() method, call task.delay() asynchronously
4. Use Django signals (post_save) or explicit call from viewset
5. Implement retry logic with exponential backoff
6. Add comprehensive logging at each stage
7. Monitor task execution and log results
8. Create management command for manual task triggering (ops only)
9. Implement dashboard for task queue monitoring

### Detailed Implementation Steps
1. **Lock Acquisition:**
   ```python
   redis_client = get_redis_connection('default')
   lock_key = f"subject_monitoring_lock:{subject_id}"
   acquired = redis_client.set(lock_key, task_id, nx=True, ex=360)
   if not acquired:
       logger.info(f"Bootstrap task already running for subject {subject_id}")
       return {"status": "deferred", "subject_id": subject_id}
   ```

2. **Task Queuing:**
   ```python
   # In subscription viewset create method
   subscription = Subscription.objects.create(user=user, subject=subject)
   trigger_subject_monitoring.delay(subject_id=subject.id, trigger='bootstrap')
   ```

3. **Task Execution:**
   ```python
   @shared_task(bind=True, max_retries=3, time_limit=300)
   def trigger_subject_monitoring(self, subject_id, trigger='bootstrap'):
       lock_key = f"subject_monitoring_lock:{subject_id}"
       try:
           # Call AI Pipeline orchestrator
           result = call_ai_pipeline(subject_id)
           return result
       except Exception as exc:
           logger.error(f"Bootstrap task failed: {exc}")
           raise self.retry(exc=exc, countdown=60)
       finally:
           redis_client.delete(lock_key)
   ```

### Technical Considerations
- **Distributed Locking:** Redis SET with NX flag ensures only one task runs
- **Lock TTL:** 6-minute TTL prevents deadlock if task crashes
- **Task Idempotency:** Multiple subscriptions to same subject within lock window deduplicated
- **Failure Handling:** Task failure does not rollback subscription (independent operations)
- **Retry Strategy:** Exponential backoff (60s, 300s, 900s) prevents thundering herd
- **Celery Configuration:** Set appropriate worker concurrency and task time limits
- **Monitoring:** Use Celery events API to track task progress

### Known Challenges
- Coordinating with AI Pipeline (Bloc 3) if not yet implemented
- Determining optimal lock TTL (balance between preventing duplicates and deadlock)
- Monitoring task queue depth in production
- Handling Redis connection failures gracefully
- Testing distributed locking with multiple worker processes
- Performance impact of multiple concurrent bootstrap tasks

## Dependencies

### Depends On
- US-3: Subscribe to Subject (trigger mechanism)
- Bloc 1: Authentication (subscription user verification)
- Bloc 3: AI Pipeline (task execution - can be stubbed initially)
- Infrastructure: Redis (distributed locking)
- Infrastructure: Celery + worker processes

### Blocks
- Bloc 4: Report Consultation (reports generated by bootstrap)
- Bloc 5: Recommendation Engine (initial user profiles from bootstrap reports)

## Test Scenarios

### Happy Path
1. User subscribes to subject "Kubernetes" (first subscriber)
2. Subscription created successfully (POST /api/subscriptions/ returns 201)
3. Bootstrap trigger logic executes immediately
4. Redis lock acquired for subject_id
5. Celery task queued: `trigger_subject_monitoring(subject_id, trigger='bootstrap')`
6. Task execution begins within 1 second (depending on worker availability)
7. AI Pipeline executes (collect → relevance → synthesis → verification → indexation)
8. Reports generated and indexed
9. Redis lock released
10. First report appears in user's dashboard within 5 minutes

### Alternative Paths
1. **Second User Subscribes During First Bootstrap:**
   - First user subscribes → lock acquired → bootstrap starts
   - Second user subscribes to same subject within 5 minutes
   - Lock acquisition fails for second bootstrap attempt
   - Second subscription succeeds without duplicate task
   - Bootstrap task continues for both users

2. **Scheduled Task Exists:**
   - Admin has scheduled daily monitoring for subject
   - User subscribes outside scheduled window
   - System detects scheduled task exists
   - Bootstrap may still trigger OR skip (product decision)

### Error Scenarios
1. **Redis Connection Failed:**
   - Redis unavailable when acquiring lock
   - Celery task still queued (may create duplicates)
   - Error logged and alerted to ops
   - Subscription succeeds (non-blocking)

2. **Celery Task Queue Full:**
   - Celery broker queue at capacity
   - Task queuing delayed or failed
   - Subscription succeeds
   - Task may be enqueued when capacity available

3. **AI Pipeline Blocked/Slow:**
   - Firecrawl API unavailable
   - LLM API rate limited
   - Task retries 3 times with exponential backoff
   - User eventually receives report or error notification

4. **Task Timeout:**
   - Task execution exceeds 5-minute limit
   - Celery terminates task
   - Lock released
   - New task not queued (prevent thundering herd)
   - Ops alerted to slow task

5. **Invalid Subject:**
   - Subscription created with invalid subject_id (race condition)
   - Task execution fails (subject not found)
   - Task retries and fails again
   - Logged as failed task

### Edge Cases
1. **Rapid Multiple Subscriptions:**
   - 10 users subscribe to same subject within 1 second
   - First subscription queues bootstrap task
   - Remaining 9 subscriptions skip bootstrap (lock held)
   - Single bootstrap task runs for all 10 users

2. **Subscription Created, Then Deleted:**
   - Bootstrap task queued during subscription
   - User immediately unsubscribes
   - Bootstrap task still executes
   - Reports generated but user not subscribed (no impact)

3. **Subject Deleted During Bootstrap:**
   - Subject exists when subscription created
   - Bootstrap task starts
   - Admin deletes subject
   - Task fails gracefully (subject not found)
   - Subscription cascade-deleted or marked inactive

4. **Worker Crash During Bootstrap:**
   - Bootstrap task begins on worker
   - Worker process crashes
   - Celery supervisor restarts worker
   - Task retried on new worker
   - Lock TTL prevents permanent deadlock

## UI/UX Specifications

### User Experience
1. User clicks "Subscribe" button on subject
2. Frontend shows loading state
3. Subscription API returns 201 Created immediately
4. Frontend updates to "Unsubscribe" button
5. Success toast: "You are now subscribed to [Subject Name]. Your first report will be ready shortly."
6. System generates first report asynchronously
7. Report appears in user's dashboard within 5 minutes
8. Optional: Email notification when first report ready

### Admin Monitoring Dashboard (Ops)
1. View of recent bootstrap tasks with timestamps
2. Task status indicators (queued, running, completed, failed)
3. Average task duration
4. Failure rate and trend
5. Manual trigger button (admin only)

## Security Considerations

- **Task Validation:** Verify subscription_id and subject_id before executing task
- **Access Control:** Bootstrap can only be triggered via subscription (user action), not manually by attackers
- **Resource Limits:** Celery task timeouts prevent runaway tasks
- **Audit Trail:** All bootstrap tasks logged with subscription_id, user_id, timestamp
- **Rate Limiting:** No user-facing rate limit needed (per subscription)
- **Data Isolation:** Tasks only access their assigned subject's data

## Performance Requirements

- **Subscription Response:** < 50ms added by bootstrap trigger
- **Task Queuing:** < 100ms from subscription to task queued
- **Bootstrap Execution:** Target < 5 minutes (typical, may vary)
- **Task Queue Throughput:** Support 1000+ bootstrap tasks per second
- **Lock Acquisition:** < 10ms

## Operational Monitoring

- **Metrics:**
  - Bootstrap task success rate (target 95%)
  - Average task duration
  - Task queue depth
  - Lock contention frequency
  - Retry rate and causes
- **Alerts:**
  - Task failure rate > 10%
  - Task queue depth > 1000
  - Task execution > 10 minutes
  - Redis lock unavailable
- **Dashboards:**
  - Task execution timeline
  - Subject-wise bootstrap rate
  - User-wise report generation time

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage with mocked Celery/Redis)
  - Lock acquisition logic
  - Task queueing
  - Error handling and retries
  - Subject validation
- [ ] Integration tests written
  - Complete bootstrap flow
  - Duplicate task prevention
  - Lock behavior verification
- [ ] Manual testing completed
  - Subscribe to subject and verify task queued
  - Multiple concurrent subscriptions to same subject
  - Redis lock prevents duplicates
  - Task failure and retry behavior
  - Task timeout handling
- [ ] AI Pipeline integration verified
  - Bootstrap calls correct pipeline function
  - Reports generated and visible in dashboard
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - Integration guide for AI Pipeline
  - Operational runbook for task monitoring
  - Celery configuration documented
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Load testing completed
  - 100+ concurrent subscriptions
  - Task queue performance verified
- [ ] Monitoring dashboard deployed
- [ ] Ops team trained on bootstrap task monitoring
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should bootstrap skip if scheduled task already exists?
- [ ] What is target report generation time (SLA)?
- [ ] Should failed bootstrap notify user?
- [ ] Should bootstrap be optional (user preference)?

### Assumptions
- AI Pipeline (Bloc 3) task interface defined and available
- Redis and Celery infrastructure in place
- Celery workers can reach AI Pipeline services
- Task execution typically completes within 5 minutes
- Lock TTL of 6 minutes sufficient to prevent duplicates

### Out of Scope
- Manual bootstrap triggering by users
- Bootstrap scheduling/timing optimization
- Priority queue for bootstrap tasks
- Per-subject bootstrap configuration
- Geographic task routing

## Related User Stories

- **US-3:** Subscribe to Subject (trigger event)
- **US-4:** Unsubscribe from Subject (may have running bootstrap)
- **Bloc 3:** AI Pipeline (task execution engine)
- **Bloc 4:** Report Consultation (reports displayed to user)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO subscriptions.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\subscriptions.md
**GitHub Issue:** [To be created]
