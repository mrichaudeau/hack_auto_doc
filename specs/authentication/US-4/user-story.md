# User Story: JWT Token Refresh

**Story ID:** US-4
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 5 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** logged-in user with expired access token
**I want to** automatically refresh my access token using my refresh token
**So that** I can continue using the platform without re-logging in

## Description

This user story implements the JWT token refresh mechanism that enables users to maintain continuous access to the platform without requiring frequent re-authentication. When an access token expires (15 minutes), users can exchange their refresh token for a new access token without entering credentials again. The original refresh token remains valid until its 7-day expiry. This approach balances security (short-lived access tokens) with user experience (seamless session continuity).

This feature is critical for mobile and long-running sessions where users may be using the platform continuously throughout the day.

## Acceptance Criteria

### Functional Criteria
- [ ] Refresh endpoint accepts valid refresh token
- [ ] New access token issued with fresh 15-minute expiry
- [ ] Original refresh token remains valid (until its 7-day expiry)
- [ ] Invalid or expired refresh token returns 401 with message: "Refresh token is invalid or expired"
- [ ] Refresh endpoint responds within 100ms (P95)
- [ ] Frontend automatically attempts token refresh on 401 responses

### Technical Criteria
- [ ] Simple JWT's TokenRefreshView used as base
- [ ] Token expiry times correctly configured
- [ ] Unit tests written (>80% coverage for token logic)
- [ ] Integration tests covering refresh flow and error scenarios
- [ ] Concurrent refresh requests handled correctly

### UI/UX Criteria (Frontend)
- [ ] Refresh happens transparently to user (no visible action required)
- [ ] If refresh fails, user redirected to login with message
- [ ] No performance degradation during token refresh
- [ ] Session continues seamlessly after refresh

### Performance Criteria
- [ ] Refresh endpoint responds within 100ms (P95)
- [ ] Token generation < 50ms
- [ ] Token validation < 20ms
- [ ] System handles 500+ concurrent refresh requests

### Security Criteria
- [ ] Refresh tokens cannot be used more than once per refresh attempt
- [ ] Expired refresh tokens return 401 (not 403)
- [ ] Rate limiting: 10 refresh attempts per token per minute (prevent abuse)
- [ ] Refresh tokens invalidated on logout

## Technical Details

### Components Affected
**Backend:**
- TokenRefreshView (from Simple JWT)
- Token validation service
- Token blacklist (optional, for logout support)
- Rate limiting middleware

**Frontend:**
- HTTP interceptor for automatic token refresh
- Auth service handling token lifecycle
- Automatic retry logic for 401 responses
- Session/store management

**Database:**
- TokenBlacklist table (if implementing logout-based revocation)
- Redis for rate limiting cache

### API Changes

**New Endpoint:**
- `POST /api/auth/token/refresh/`
  - **Request Body:**
    ```json
    {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access_expires_in": 900
    }
    ```
  - **Error Response (401 Unauthorized):**
    ```json
    {
      "error": "invalid_refresh_token",
      "message": "Refresh token is invalid or expired"
    }
    ```
  - **Error Response (429 Too Many Requests - Rate Limit):**
    ```json
    {
      "error": "rate_limited",
      "message": "Too many token refresh attempts. Please try again later.",
      "retry_after_seconds": 60
    }
    ```

### Database Changes

**New table: TokenBlacklist (optional, if implementing token revocation)**
- `id` (UUID primary key)
- `token` (TextField, the actual refresh token)
- `user_id` (foreign key to User)
- `blacklisted_at` (timestamp)
- `blacklist_reason` (varchar 100, e.g., "logout", "password_change", "all_devices_logout")

**Indexes:**
- Index on `token` (for lookup)
- Index on `user_id` (for user-specific queries)
- Index on `blacklisted_at` (for cleanup)

**Refresh token lifetime configuration:**
- `ACCESS_TOKEN_LIFETIME` = timedelta(minutes=15)
- `REFRESH_TOKEN_LIFETIME` = timedelta(days=7)
- `TOKEN_TYPE_CLAIM` = 'token_type'
- `JTI_CLAIM` = 'jti' (unique token ID)

### External Integrations
- **Simple JWT:** djangorestframework-simplejwt library
- **Redis:** For rate limiting cache

## Implementation Notes

### Suggested Approach
1. Use djangorestframework-simplejwt's built-in TokenRefreshView
   - Minimal customization needed
   - Handles token validation and generation out of box
2. Configure token lifetimes in Django settings:
   - Access token: 15 minutes
   - Refresh token: 7 days
3. Implement frontend interceptor that:
   - Catches 401 Unauthorized responses
   - Extracts refresh token from storage
   - Calls refresh endpoint
   - Retries original request with new access token
   - If refresh fails, redirects to login
4. Add rate limiting to refresh endpoint:
   - Redis-backed counter
   - 10 attempts per unique refresh token per minute
   - Returns 429 if exceeded
5. Optional: Implement token blacklist for logout support
   - Simple JWT provides blacklist backend
   - Checks token against blacklist on validation
   - Enables logout-based revocation

### Technical Considerations
- **Token Format:** JWT with exp claim for automatic expiry validation
- **Token Payload:** Include user_id, email, token_type, jti (unique ID)
- **Refresh Flow:**
  1. Access token expires (frontend receives 401)
  2. Frontend calls refresh endpoint with refresh token
  3. Backend validates refresh token (signature, expiry, blacklist)
  4. Backend issues new access token with current timestamp + 15 minutes
  5. Original refresh token unchanged (still valid)
  6. Frontend retries original request with new access token
- **Rate Limiting:** Per refresh token (not per user) to prevent refresh token hijacking detection bypass
- **Concurrency:** JWT validation is stateless, allowing distributed systems
- **Clock Skew:** Implement ±60 second tolerance for exp validation
- **Token Rotation:** Could implement optional refresh token rotation (issue new refresh on each refresh) for enhanced security

### Known Challenges
- Balancing security with UX (short access token requires frequent refresh)
- Detecting compromised refresh tokens (requires logging and monitoring)
- Frontend token storage security (XSS vulnerability mitigation)
- Distributed system token validation (requires consistent clock or JTI blacklist)

## Dependencies

### Depends On
- **US-3:** Standard User Login (creates tokens to refresh)
- **Library:** djangorestframework-simplejwt (for token generation/validation)
- **Infrastructure:** Redis (for rate limiting, optional)

### Blocks
- **Implicit dependency:** Any protected endpoint requires token refresh capability
- **US-12:** Logout from Current Session (needs token invalidation)

## Test Scenarios

### Happy Path
1. User logs in successfully (US-3)
   - Receives access_token and refresh_token
2. Access token stored in memory
3. Refresh token stored securely
4. User makes API request within 15 minutes
   - Access token still valid
   - Request succeeds (200 response)
5. User continues using platform
6. After 15+ minutes, access token expires
7. User makes another API request
   - Backend returns 401 Unauthorized
8. Frontend HTTP interceptor catches 401
9. Frontend calls refresh endpoint with refresh_token
10. Backend validates refresh_token:
    - Signature is valid
    - Token not expired (still within 7 days)
    - Token not blacklisted
11. Backend issues new access_token with 15-minute expiry
12. Response returns new access token
13. Frontend stores new access token
14. Frontend retries original request with new token
15. Request succeeds (200 response)
16. User continues using platform without interruption

### Alternative Paths
1. **Refresh Before Expiry:**
   - User proactively calls refresh endpoint before access token expires
   - New access token issued
   - Original refresh token remains valid
   - Success (200 response)

2. **Refresh Near Expiry:**
   - Access token has ~30 seconds remaining
   - User makes request
   - Token accepted (still valid)
   - Frontend does not refresh
   - Request succeeds

3. **Multiple Concurrent Requests After Expiry:**
   - Access token expires
   - User makes 3 API requests simultaneously
   - All 3 receive 401 responses
   - All 3 trigger refresh
   - Only first refresh succeeds (within rate limit)
   - Others may be rate limited (429) or also receive new token
   - All retry original request with valid token
   - All succeed

### Error Scenarios
1. **Expired Refresh Token:**
   - User's refresh token expired (>7 days old)
   - Refresh endpoint called
   - Backend validates: token.exp < now()
   - Returns 401 Unauthorized
   - Message: "Refresh token is invalid or expired"
   - Frontend redirects to login page
   - User must re-authenticate

2. **Invalid Refresh Token:**
   - Refresh token malformed or corrupted
   - Backend cannot decode JWT
   - Returns 401 Unauthorized
   - Message: "Refresh token is invalid or expired"
   - Frontend redirects to login

3. **Tampered Refresh Token:**
   - Attacker modifies refresh token
   - JWT signature verification fails
   - Returns 401 Unauthorized
   - Message: "Refresh token is invalid or expired"
   - No security breach logged (expected attack)

4. **Refresh Token Blacklisted:**
   - User logged out (token blacklisted)
   - Refresh endpoint called with blacklisted token
   - Backend checks blacklist table
   - Token found in blacklist
   - Returns 401 Unauthorized
   - Message: "Refresh token is invalid or expired"
   - Frontend redirects to login

5. **Rate Limited:**
   - Refresh token used 11 times within 60 seconds
   - 11th attempt rejected
   - Returns 429 Too Many Requests
   - Message: "Too many token refresh attempts. Please try again later."
   - Header: `Retry-After: 60`
   - Indicates possible compromised token or bug

6. **Access Token Sent Instead of Refresh Token:**
   - Frontend sends access token to refresh endpoint (wrong token type)
   - Backend checks token_type claim
   - Mismatch detected
   - Returns 401 Unauthorized
   - Message: "Refresh token is invalid or expired"

### Edge Cases
1. **Token Refresh at Exact Expiry Moment:**
   - Access token expires at exactly T
   - Request arrives at T+1ms
   - Token considered expired
   - Refresh triggered
   - Success

2. **Token Refresh 1ms Before Expiry:**
   - Access token expires at T
   - Request arrives at T-1ms
   - Token still valid
   - Request succeeds without refresh
   - No refresh triggered

3. **Distributed System Clock Skew:**
   - Server A issues token valid until time X
   - Request routed to Server B (clock is 2 minutes behind)
   - Token appears to have 2 minutes more validity
   - System handles gracefully with ±60 second tolerance
   - Or uses centralized JTI blacklist

4. **Token Refresh Immediately After Login:**
   - User logs in, immediately calls refresh
   - New access token issued
   - Original refresh token still valid
   - Both tokens functional (no issues)

5. **Very Rapid Sequential Refreshes:**
   - Frontend calls refresh 10 times in 100ms
   - Each call succeeds (within rate limit)
   - Each receives valid new access token
   - No degradation

6. **User ID in Token vs Database:**
   - Token contains user_id = 123
   - User account deleted in database
   - Refresh endpoint validates token (only checks signature/expiry)
   - Returns valid new token
   - Subsequent API calls using token receive 404 (user not found)
   - Expected behavior (token is still valid)

## UI/UX Specifications

### Frontend Implementation
The refresh process should be completely transparent to the user. The frontend HTTP client must:

1. **Interceptor Logic:**
   - On any 401 response
   - Extract refresh token from secure storage
   - Call `POST /api/auth/token/refresh/` with refresh token
   - Update access token on success
   - Retry original request

2. **Error Handling:**
   - If refresh succeeds: Retry original request silently
   - If refresh fails (401): Redirect to login page
   - If refresh fails (429): Show message: "Session too busy, please try again in a moment"
   - If refresh fails (other): Show message: "Session expired, please log in again"

3. **User Visibility:**
   - No refresh progress bar or loading indicator (happens in background)
   - No notification to user (unless error occurs)
   - Session continues seamlessly

### Design Assets
- No UI components needed (entirely backend + HTTP interceptor logic)
- Documentation of frontend HTTP interceptor pattern

## Security Considerations

- **Authentication:** Verified via JWT signature
- **Authorization:** Not directly (but enables authorization checks)
- **Data Validation:** JWT structure and claims validation
- **Encryption:** JWT signed with SECRET_KEY (symmetric) or private key (asymmetric)
- **Token Rotation:** Optional - could issue new refresh token on each refresh (enhanced security)
- **Rate Limiting:** 10 refresh attempts per token per minute
- **Audit Logging:** Log suspicious refresh patterns (many failures, rapid refreshes)
- **Refresh Token Storage:**
  - Never store in localStorage (XSS risk)
  - Store in memory or SessionStorage (lost on tab close)
  - Or use httpOnly cookie if supporting traditional auth
- **Token Invalidation:** Refresh tokens invalidated on:
  - Password change (user initiated)
  - Account deletion
  - Admin revocation
  - Logout from all devices

## Performance Requirements

- **Response Time:** < 100ms (P95) for refresh endpoint
- **Token Generation:** < 50ms
- **Token Validation:** < 20ms
- **Rate Limit Check:** < 10ms (Redis lookup)
- **Throughput:** Support 500+ concurrent refresh requests
- **Concurrent Users:** System designed for 1000 concurrent authenticated users

## Accessibility Requirements

- [ ] Refresh happens transparently (no UI interaction required)
- [ ] If error occurs, error message is clear and actionable
- [ ] Redirect to login is accessible (keyboard, screen reader)

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Token validation tests
  - Token generation tests
  - Expiry logic tests
  - Rate limiting tests
  - Invalid token tests
- [ ] Integration tests written
  - Full refresh flow
  - Expired token flow
  - Invalid token flow
  - Rate limiting flow
  - Concurrent refresh tests
- [ ] Manual testing completed
  - Test successful refresh
  - Test expired refresh token
  - Test invalid token
  - Test rate limiting
  - Verify access token expiry
  - Verify refresh token remains valid
- [ ] Frontend HTTP interceptor implemented and tested
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Token lifetime configuration
  - Frontend implementation guide
  - Refresh flow architecture diagram
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<100ms P95)
- [ ] Load test completed (500+ concurrent refreshes)
- [ ] Security review completed
  - Token validation verified
  - Rate limiting verified
  - No token exposure in logs
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should we implement refresh token rotation (issue new refresh on each refresh)? (Enhanced security, added complexity)
- [ ] What should be the refresh token expiry? (Currently 7 days)
- [ ] Should refresh be rate limited? (Currently yes, 10 per minute)
- [ ] Should we log all refresh attempts for anomaly detection? (Recommended)

### Assumptions
- JWT library handles signature validation correctly
- Frontend can securely store refresh tokens in memory
- Redis is available for rate limiting
- Clock skew is within ±60 seconds across servers
- Users have access to stable network (refresh won't fail due to network issues)

### Out of Scope
- Refresh token rotation (issue new refresh on each use)
- Biometric verification for refresh
- Refresh token expiration based on inactivity
- Refresh token geo-blocking or device binding
- Persistent token storage (tokens in cookies with httpOnly + Secure flags)

## Related User Stories

- **US-3:** Standard User Login (creates tokens for refresh)
- **US-4:** JWT Token Refresh (THIS STORY)
- **US-12:** Logout from Current Session (invalidates refresh tokens)
- **US-5:** Password Reset Request (invalidates refresh tokens)
- **US-6:** Password Reset Completion (invalidates refresh tokens)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
