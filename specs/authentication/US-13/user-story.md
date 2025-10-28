# User Story: Logout from All Devices

**Story ID:** US-13
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P3
**Effort Estimate:** 6 story points
**Assigned To:** [Developer Name]
**Sprint:** [Sprint Number]

## User Story Statement

**As a** security-conscious user
**I want to** log out from all my active sessions across all devices
**So that** I can revoke access if I suspect unauthorized use

## Description

This user story provides security-conscious users with the ability to invalidate all their active sessions across all devices simultaneously. Unlike regular logout (US-12) which only ends the current session, this feature revokes ALL refresh tokens associated with the user account.

This is critical for security scenarios where users suspect account compromise or want to ensure no unauthorized access from other devices/browsers. The feature includes a confirmation modal to prevent accidental activation and provides clear feedback about the security implications.

After logout from all devices, the user remains logged out on the current device but can immediately re-login with credentials or SSO, at which point all other devices' sessions are also terminated.

## Acceptance Criteria

### Functional Criteria
- [ ] "Logout from all devices" button in profile security section
- [ ] Confirmation modal displays: "This will log you out from all devices. Continue?"
- [ ] All refresh tokens for the user invalidated
- [ ] Current session also logged out
- [ ] User redirected to login page
- [ ] Success message: "You have been logged out from all devices"
- [ ] Endpoint responds within 200ms (P95)
- [ ] All subsequent API requests fail with 401 (no valid tokens)

### Technical Criteria
- [ ] Endpoint implemented at POST /api/users/me/logout-all/
- [ ] Revoke all refresh tokens (blacklist or new issuance)
- [ ] Use Simple JWT token blacklist or custom token revocation logic
- [ ] Consider adding "last_token_revoke_at" timestamp to User model for efficient validation
- [ ] All tokens invalidated in single atomic operation
- [ ] Logout event logged with timestamp, user ID, IP address
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering success and edge cases
- [ ] API documentation updated

### UI/UX Criteria (if applicable)
- [ ] "Logout from all devices" button clearly visible in Security section
- [ ] Confirmation modal with clear warning message
- [ ] "Yes, logout from all devices" and "Cancel" buttons
- [ ] Success message displayed prominently
- [ ] Fast redirect to login page
- [ ] Accessible form controls and buttons
- [ ] Mobile responsive design

### Performance Criteria
- [ ] Response time < 200ms (P95)
- [ ] Token revocation operation < 100ms
- [ ] Handles large number of tokens efficiently
- [ ] No database locking or significant resource consumption

## Technical Details

### Components Affected
- **Backend:** Django User model, JWT token management, token revocation logic
- **Frontend:** Profile security component, confirmation modal
- **Database:** User model (add last_token_revoke_at field), token blacklist table
- **External:** None

### API Changes
- **New Endpoints:**
  - `POST /api/users/me/logout-all/` - Logout from all devices
    - Request Header: `Authorization: Bearer <access_token>`
    - Request Body: `{}` (empty, or optional confirmation flag)
    - Response (200 OK):
      ```json
      {
        "message": "You have been logged out from all devices",
        "detail": "All your active sessions have been terminated. Please log in again."
      }
      ```
    - Response (401 Unauthorized):
      ```json
      {
        "error": "unauthorized",
        "message": "Invalid or missing authentication token"
      }
      ```

### Database Changes
- **User Model Migration:**
  ```sql
  ALTER TABLE auth_user ADD COLUMN last_token_revoke_at TIMESTAMP NULL DEFAULT NULL;
  ```
  - This timestamp enables efficient token validation:
    - On token validation, check: token.issued_at > user.last_token_revoke_at
    - If false, token is invalid (issued before revocation)
    - Avoids blacklist lookup for revoked tokens

- **Alternative: Token Blacklist Table (if using database-backed blacklist):**
  ```sql
  CREATE TABLE IF NOT EXISTS token_blacklist (
    id UUID PRIMARY KEY,
    token TEXT NOT NULL,
    user_id UUID REFERENCES auth_user(id),
    blacklist_type VARCHAR(50), -- 'refresh_only' or 'all'
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
  );
  CREATE INDEX idx_token_blacklist_user_id ON token_blacklist(user_id);
  CREATE INDEX idx_token_blacklist_expires_at ON token_blacklist(expires_at);
  ```

- **Audit Log Entry:**
  ```sql
  INSERT INTO audit_log (user_id, event_type, event_details, ip_address, user_agent, created_at)
  VALUES (user_id, 'logout_all_devices', '{"session_count": 5}', ip_address, user_agent, NOW());
  ```

### External Integrations
- None

## Implementation Notes

### Suggested Approach

**Option 1: Using last_token_revoke_at Timestamp (Recommended)**
1. When user calls logout-all endpoint:
   - Set user.last_token_revoke_at = now()
   - Save user record
   - Return success response
2. On token validation (every API request):
   - Extract token.issued_at from JWT payload
   - Compare with user.last_token_revoke_at
   - If token.issued_at < user.last_token_revoke_at, reject token (401)
3. Benefits:
   - No need to store list of revoked tokens
   - Scales efficiently (O(1) token validation)
   - Redis not required for token blacklist
   - Clean, stateless approach

**Option 2: Using Token Blacklist (Alternative)**
1. When user calls logout-all endpoint:
   - Query all user's refresh tokens from database
   - Add all tokens to blacklist with expiry time
   - Return success response
2. On token validation:
   - Check if token exists in blacklist
   - If exists and not expired, reject (401)
3. Benefits:
   - Standard Simple JWT approach
   - Works with database or Redis blacklist
4. Drawbacks:
   - Must store all tokens in blacklist
   - Scales poorly with many tokens

**Recommended: Implement Option 1 with fallback to Option 2**

1. Create logout-all endpoint in user viewset
2. Add last_token_revoke_at field to User model
3. Implement custom token authentication backend:
   ```python
   def validate_token(token):
       payload = jwt.decode(token)
       user = User.objects.get(id=payload['user_id'])
       if user.last_token_revoke_at and payload['iat'] < user.last_token_revoke_at.timestamp():
           return None  # Token revoked
       return user
   ```
4. Update logout-all endpoint:
   ```python
   def logout_all(request):
       user = request.user
       user.last_token_revoke_at = now()
       user.save()
       # Optionally blacklist current token too
       blacklist_token(request.auth)
       log_event(user, 'logout_all_devices')
       return Response({'message': 'logged out from all devices'})
   ```
5. Implement comprehensive tests
6. Document in API specification

### Technical Considerations
- **Security:** Ensure all tokens truly invalidated; no lingering sessions
- **Performance:** Token validation must be fast (< 1ms per request)
- **Scalability:** No need for central token list
- **Consistency:** All devices receive 401 on next API request
- **Audit Trail:** Log logout-all events for security investigation
- **Recovery:** User can immediately login again if needed

### Known Challenges
- Efficient token revocation at scale
- Synchronizing token invalidation across distributed systems
- User experience: Clear communication about session termination
- Edge case: Logout-all during active requests on other devices
- Performance: Token validation on every API request must be fast

## Dependencies

### Depends On
- **US-3:** Standard User Login (JWT token system)
- **US-7:** Microsoft Entra ID SSO Login (SSO users can logout-all too)
- **US-8:** User Profile Viewing (security section context)
- **Infrastructure:** PostgreSQL with user table, token management system

### Blocks
- None directly

## Test Scenarios

### Happy Path
1. User logged in on multiple devices (browser, mobile, tablet)
2. User navigates to Profile → Security
3. User clicks "Logout from all devices" button
4. Confirmation modal appears with warning
5. User clicks "Yes, logout from all devices"
6. POST /api/users/me/logout-all/ called
7. Backend updates user.last_token_revoke_at = now()
8. Backend returns 200 success
9. Frontend clears tokens and redirects to /login
10. Success message displayed: "You have been logged out from all devices"
11. On other devices:
    - User makes API request with old tokens
    - Backend validates token: issued_at < last_token_revoke_at
    - Request fails with 401 Unauthorized
    - Frontend on other devices redirects to login
12. User can login again with fresh tokens

### Alternative Paths
1. User clicks logout-all, but cancels confirmation modal
   - Modal closes
   - No logout occurs
   - User remains logged in on all devices

2. User has only one active session
   - Same flow as above
   - Logout-all behaves like regular logout
   - User still protected if account compromised

### Error Scenarios
1. User not authenticated (missing JWT token)
   - POST returns 401 Unauthorized
   - User redirected to login

2. Database failure during revocation
   - Operation rolled back
   - User receives error message
   - User can retry logout-all

3. Network error during logout-all
   - Request fails, tokens not revoked
   - User can retry operation
   - Other devices continue working

### Edge Cases
1. User calls logout-all while other request in flight
   - Both complete successfully
   - Other request's token may still be valid briefly
   - Eventually all tokens invalid

2. Very long session history (user has 100+ devices)
   - Token revocation still O(1)
   - No performance impact
   - All devices logout successfully

3. User calls logout-all, then immediately logs in
   - New tokens generated with new issued_at timestamp
   - New issued_at > last_token_revoke_at
   - New tokens valid, old tokens still invalid

4. Clock skew between servers
   - Timestamp-based validation more resilient than token list
   - No synchronization needed across instances

5. Multiple concurrent logout-all requests
   - First request sets last_token_revoke_at
   - Subsequent requests succeed (idempotent)
   - Only one timestamp recorded

## UI/UX Specifications

### User Flow
1. User clicks "Profile" or navigates to Account Settings
2. User clicks "Security" or "Sessions" tab
3. User sees "Active Sessions" section showing:
   - Current session (browser, device, location)
   - Other active sessions (if any)
4. User sees "Logout from all devices" button in red/warning color
5. User clicks button
6. Confirmation modal appears:
   - Header: "Logout from all devices?"
   - Body: "This will log you out from all devices. Continue?"
   - Buttons: "Yes, logout from all devices" (red) and "Cancel" (gray)
7. User clicks "Yes, logout from all devices"
8. Modal closes
9. Loading state shows during logout operation
10. Success message appears: "You have been logged out from all devices"
11. Auto-redirect to /login after 2 seconds
12. All other devices also receive 401 errors on next API request

### Design Requirements
- "Logout from all devices" button in Security section
- Warning color (red or orange) to indicate security implication
- Confirmation modal with clear warning text
- Explicit confirmation buttons: "Yes, logout from all devices" and "Cancel"
- Success notification with reassuring message
- Fast redirect to login
- Accessible form controls and buttons
- Mobile responsive (modal adapts to screen size)

## Security Considerations

- **Authorization:** Only user can logout their own sessions
- **Token Revocation:** All tokens invalidated simultaneously
- **Audit Logging:** Log logout-all with user ID, IP, timestamp
- **XSS Prevention:** Modal cannot be bypassed via script
- **CSRF Protection:** Django CSRF middleware active
- **Rate Limiting:** Limit logout-all attempts (e.g., 3 per hour per user)
- **Security Implications:** Clearly communicate what happens
- **Account Recovery:** User can login again immediately

## Performance Requirements

- **Response Time:** < 200ms (P95)
- **Revocation Operation:** < 100ms (database write or timestamp update)
- **Token Validation:** < 1ms per API request (timestamp comparison)
- **Concurrent Operations:** Support 100+ simultaneous logout-all requests
- **Database:** No blocking queries, efficient write operations

## Accessibility Requirements

- [ ] "Logout from all devices" button keyboard accessible
- [ ] Confirmation modal accessible without mouse
- [ ] Screen reader announces modal dialog clearly
- [ ] ARIA labels on buttons and warning text
- [ ] Keyboard navigation within modal (Tab, Enter, Escape)
- [ ] Focus management: Focus moves to modal, then back to page after close
- [ ] Color not only indicator of severity (icon, text also used)
- [ ] Success message announced by screen reader

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] User model migration applied (add last_token_revoke_at field)
- [ ] Token validation logic updated
- [ ] Unit tests written (>80% coverage for all scenarios)
- [ ] Integration tests written and passing
- [ ] Manual testing across multiple devices
- [ ] Acceptance criteria verified by PO
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] Code merged to main branch
- [ ] Database migrations executed in staging
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (< 200ms response, < 1ms token validation)
- [ ] Security review completed
- [ ] Audit logging verified working
- [ ] No critical or high-severity bugs

## Tasks

Detailed development tasks are tracked in [tasks.md](./tasks.md)

### Task Summary
- **Total Tasks:** [Number]
- **Completed:** [Number]
- **In Progress:** [Number]
- **Blocked:** [Number]

## Notes

### Questions / Open Items
- [ ] Should we show list of active sessions before logout-all?
- [ ] Should we allow selective logout (logout from specific devices)?
- [ ] Should we send email notification when logout-all occurs?
- [ ] Should we implement IP-based session tracking?
- [ ] Should we add device/browser identification to sessions?

### Assumptions
- User model can have last_token_revoke_at field
- Token payload includes issued_at (iat) claim
- All servers synchronized to approximately same time (NTP)
- No requirement to show active session list (just logout-all button)
- Simple JWT or similar JWT library in use

### Out of Scope
- Active session management/list display
- Selective logout from specific devices
- Session activity tracking/history
- Device fingerprinting
- Geo-location based session tracking
- Forced re-authentication for sensitive operations

## Related User Stories

- **US-3:** Standard User Login (generates initial tokens)
- **US-7:** Microsoft Entra ID SSO Login (SSO users logout-all)
- **US-8:** User Profile Viewing (security section context)
- **US-12:** Logout from Current Session (simpler single-device logout)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial user story generation |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/authentication.md
**GitHub Issue:** [Link to GitHub issue]
