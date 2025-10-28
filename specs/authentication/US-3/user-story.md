# User Story: Standard User Login

**Story ID:** US-3
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 8 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** registered user with verified email
**I want to** log in with my email and password
**So that** I can access my personalized dashboard

## Description

This user story implements the standard email/password login flow for users who have already registered and verified their email address. Upon successful authentication, the system issues JWT tokens (access token with 15-minute expiry and refresh token with 7-day expiry) that enable access to protected API endpoints. The login response includes essential user profile data. Failed login attempts are logged for security monitoring, and rate limiting prevents brute-force attacks.

This is the primary entry point for returning users to access the platform's features and their personalized content.

## Acceptance Criteria

### Functional Criteria
- [ ] Login form accepts email and password
- [ ] Successful login returns JWT access token (15-minute expiry) and refresh token (7-day expiry)
- [ ] Response includes user profile data: id, email, first_name, last_name, is_sso_user
- [ ] User redirected to /dashboard after successful login
- [ ] Invalid credentials return 401 with message: "Invalid email or password"
- [ ] Unverified accounts return 403 with message: "Please verify your email before logging in"
- [ ] Rate limiting: Maximum 5 login attempts per IP per 5 minutes
- [ ] Failed login attempts logged for security monitoring
- [ ] Login endpoint responds within 300ms (P95)

### Technical Criteria
- [ ] djangorestframework-simplejwt library used for token generation
- [ ] Token expiry configured: ACCESS_TOKEN_LIFETIME (15 min), REFRESH_TOKEN_LIFETIME (7 days)
- [ ] Unit tests written (>80% coverage for authentication logic)
- [ ] Integration tests covering login flow and error scenarios
- [ ] Security audit log contains all login attempts

### UI/UX Criteria
- [ ] Login form is responsive on mobile/tablet/desktop
- [ ] Clear error messages for different failure scenarios
- [ ] Password field masked (dots/asterisks)
- [ ] Loading state shown during login processing
- [ ] Accessibility standards met (WCAG 2.1 Level AA)

### Performance Criteria
- [ ] Login endpoint responds within 300ms (P95)
- [ ] Response time includes password hashing verification
- [ ] System handles 100+ concurrent login requests
- [ ] Token generation and validation sub-50ms

### Security Criteria
- [ ] Rate limiting: 5 attempts per IP per 5 minutes
- [ ] Password never logged or included in error messages
- [ ] Failed login attempts logged with IP, email (hashed), and timestamp
- [ ] Tokens transmitted in response body (not cookies for SPA)
- [ ] Tokens expire appropriately (no indefinite sessions)

## Technical Details

### Components Affected
**Backend:**
- Custom authentication backend extending Django's ModelBackend
- Login view/viewset
- JWT token generation service
- Rate limiting middleware/decorator
- Security logging service

**Frontend:**
- Login form component
- Session/token management store (Redux, Context, Zustand)
- HTTP interceptor for token injection
- Redirect to dashboard on successful login

**Database:**
- User table (for password validation)
- Audit log table (for security logging)
- Rate limiting cache (Redis)

### API Changes

**New Endpoint:**
- `POST /api/auth/login/`
  - **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePass123!"
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
      "access_token_expires_in": 900,
      "refresh_token_expires_in": 604800,
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "is_sso_user": false
      }
    }
    ```

  - **Error Response (401 Unauthorized):**
    ```json
    {
      "error": "invalid_credentials",
      "message": "Invalid email or password"
    }
    ```

  - **Error Response (403 Forbidden - Unverified Email):**
    ```json
    {
      "error": "email_not_verified",
      "message": "Please verify your email before logging in"
    }
    ```

  - **Error Response (429 Too Many Requests - Rate Limit):**
    ```json
    {
      "error": "rate_limited",
      "message": "Too many login attempts. Please try again in 5 minutes.",
      "retry_after_seconds": 300
    }
    ```

### Database Changes
**Modified table: User**
- Add fields (if not present):
  - `last_login` (timestamp, nullable, for audit trail)
  - `login_attempts` (counter in Redis, not DB)

**New table: LoginAuditLog**
- `id` (UUID primary key)
- `user_id` (foreign key to User, nullable for failed attempts)
- `email` (varchar 255, for tracking attempts before user found)
- `ip_address` (inet/varchar 45, for IPv6)
- `user_agent` (text, for device tracking)
- `success` (boolean)
- `failure_reason` (varchar 100, e.g., "invalid_credentials", "email_not_verified")
- `created_at` (timestamp)

**Indexes:**
- Index on `(ip_address, created_at)` for rate limiting
- Index on `(user_id, created_at)` for user login history
- Index on `(email, created_at)` for failed attempt tracking

### External Integrations
- **Redis:** For rate limiting cache and session management
- **JWT Library:** djangorestframework-simplejwt for token generation

## Implementation Notes

### Suggested Approach
1. Create custom authentication backend extending Django's ModelBackend:
   - Authenticate by email (not username)
   - Verify password using Django's check_password()
   - Check is_email_verified flag
   - Log login attempt (success/failure)
2. Create login view that:
   - Accepts email and password
   - Calls authentication backend
   - Generates JWT tokens on success
   - Returns user profile and tokens
   - Implements rate limiting
3. Integrate with djangorestframework-simplejwt:
   - Configure token lifetime settings
   - Use TokenObtainPairView as base
   - Customize response to include user data
4. Implement rate limiting:
   - Use django-ratelimit or custom Redis-based solution
   - Track per-IP address
   - Count failed attempts only
   - Block after 5 attempts per 5 minutes
5. Set up security logging:
   - Log all authentication attempts
   - Include IP address, user agent, timestamp
   - Async logging to prevent performance impact

### Technical Considerations
- **Password Verification:** Use Django's check_password() which handles Argon2 verification
- **Token Lifetime:**
  - Access token: 15 minutes (short-lived, reduces impact of theft)
  - Refresh token: 7 days (long-lived, allows session continuity)
- **Rate Limiting:**
  - Redis-backed counter increments on each attempt
  - Resets after 5 minutes of no attempts
  - Operates at IP level (not per user) to prevent account enumeration
- **Security Logging:**
  - Log all attempts (success and failure)
  - Async logging via Celery to prevent request blocking
  - Include request context: IP, user agent, timestamp
  - Store hashed email for privacy
- **Error Messaging:**
  - Never distinguish between "email not found" vs "password wrong"
  - Always respond with "Invalid email or password" for both cases
  - Prevents user enumeration attacks
- **Response Security:**
  - Tokens in response body (not cookies, for SPA architecture)
  - Frontend stores tokens in memory (not localStorage for XSS protection)
  - Include token expiry times in response
- **Clock Skew:** Implement clock skew tolerance (±60 seconds) for token validation

### Known Challenges
- Distinguishing between failed attempts and legitimate users with wrong passwords
- Preventing rate limit bypass via IP spoofing or botnets
- Balancing security (short access token) with UX (frequent token refresh)
- Coordinating rate limiting across multiple backend instances (requires Redis)

## Dependencies

### Depends On
- **US-1:** Standard User Registration (users must exist first)
- **US-2:** Email Verification (users must verify email first)
- **Infrastructure:** Redis (for rate limiting and token management)
- **Library:** djangorestframework-simplejwt (for JWT token generation)

### Blocks
- **US-4:** JWT Token Refresh (requires access/refresh tokens)
- **US-8:** User Profile Viewing (requires login)
- **US-12:** Logout from Current Session (requires login session)

## Test Scenarios

### Happy Path
1. User navigates to login page
2. Enters verified email address
3. Enters correct password
4. Clicks "Log In" button
5. System validates:
   - Email format is valid
   - User account exists
   - Email is verified (is_email_verified = True)
   - Password matches hash
   - Not rate limited
6. Authentication successful
7. System generates:
   - JWT access token (15-min expiry)
   - JWT refresh token (7-day expiry)
8. Response includes:
   - Access token
   - Refresh token
   - Token expiry times
   - User data: id, email, first_name, last_name, is_sso_user
9. Frontend stores tokens
10. User redirected to /dashboard
11. Login audit log entry created with success=True

### Alternative Paths
1. **First-Time Login:** User logs in for first time
   - Everything same as happy path
   - last_login field updated
   - Dashboard shows welcome message

2. **Multiple Logins:** User logs in again after previous session
   - Same flow as happy path
   - Last login timestamp updated
   - Previous tokens still valid until expiry (not revoked)

### Error Scenarios
1. **Invalid Email Address:**
   - User enters "notanemail"
   - System validates email format
   - Returns 400 Bad Request
   - Message: "Please enter a valid email address"

2. **Non-Existent Account:**
   - User enters valid email that's not registered
   - System cannot find user
   - Returns 401 Unauthorized
   - Message: "Invalid email or password" (don't reveal email doesn't exist)
   - Audit log: success=False, failure_reason="invalid_credentials"

3. **Wrong Password:**
   - User enters correct email but wrong password
   - password hash verification fails
   - Returns 401 Unauthorized
   - Message: "Invalid email or password"
   - Rate limiting counter increments
   - Audit log: success=False, failure_reason="invalid_credentials"

4. **Email Not Verified:**
   - User registered but didn't verify email (is_email_verified = False)
   - Password correct but account inactive
   - Returns 403 Forbidden
   - Message: "Please verify your email before logging in"
   - Link to resend verification email (US-2)
   - Audit log: success=False, failure_reason="email_not_verified"
   - Does NOT increment rate limit counter

5. **Account Deactivated:**
   - Admin deactivated user account (is_active = False)
   - Password and email correct
   - Returns 403 Forbidden
   - Message: "Your account has been deactivated. Contact support."
   - Audit log: success=False, failure_reason="account_inactive"

6. **Rate Limited - Too Many Attempts:**
   - User attempts login 6 times from same IP within 5 minutes
   - 6th attempt rejected
   - Returns 429 Too Many Requests
   - Message: "Too many login attempts. Please try again in 5 minutes."
   - Header: `Retry-After: 300`
   - Audit log: success=False, failure_reason="rate_limited"

### Edge Cases
1. **Concurrent Login Attempts:**
   - User submits login form twice rapidly
   - Only one successful authentication
   - Both requests may receive tokens (within rate limit)
   - No race condition issues

2. **Case-Insensitive Email:**
   - User registers with "User@Example.com"
   - Later logs in with "user@example.com"
   - System performs case-insensitive email lookup
   - Login succeeds

3. **Extra Whitespace in Email:**
   - User enters " user@example.com " (with spaces)
   - System trims whitespace before lookup
   - Login succeeds

4. **Rapid Rate Limit Test:**
   - User hits rate limit
   - Waits exactly 5 minutes
   - Next attempt should succeed (counter reset)
   - System correctly interprets timeout

5. **Token Claims:**
   - Decode JWT token
   - Verify claims include: user_id, email, exp (expiry)
   - No sensitive data exposed (no password, no is_staff)

6. **Distributed Environment:**
   - Multiple backend instances
   - Rate limiting via Redis (shared state)
   - All instances respect same rate limit
   - No request goes to one instance to bypass limit on another

## UI/UX Specifications

### User Flow
1. User navigates to login page (/login)
2. Page displays login form with fields:
   - Email address (text input)
   - Password (password input with mask)
   - "Remember me" checkbox (optional)
3. User enters email address
   - No real-time validation (prevents user enumeration)
4. User enters password
   - Password field shows dots/asterisks (masked)
5. User clicks "Log In" button
6. Button shows loading state (spinner/disabled)
7. After 1-2 seconds (typical response time):
   - **Success:** Redirect to dashboard
   - **Error:** Error message displayed above form
     - Example: "Invalid email or password"
     - Example: "Please verify your email before logging in"
     - Example: "Too many login attempts. Please try again later."
8. User sees "Forgot Password?" link for password reset flow
9. User sees "Sign Up" link for new account registration

### Error Message Handling
- Generic error for invalid credentials (prevents enumeration)
- Specific error for unverified email with link to resend verification
- Specific rate limit error with retry time countdown
- All errors displayed prominently with action items

### Design Assets
- Link to login form design: [login-form-component]
- Link to error message design: [error-message-component]
- Link to loading state design: [button-loading-state]

## Security Considerations

- **Authentication:** Email/password verification via Argon2 hash
- **Authorization:** Post-login, JWT tokens control access to protected endpoints
- **Data Validation:**
  - Email format validation (RFC 5322)
  - Password accepted as plain text (hashed server-side)
  - Input sanitization prevents injection attacks
- **Encryption:** Passwords hashed with Argon2 (not encrypted)
- **Audit Logging:**
  - All login attempts logged (success and failure)
  - Include IP address, user agent, email (or hashed)
  - Timestamp and outcome recorded
  - No passwords logged
- **Rate Limiting:**
  - 5 attempts per IP per 5 minutes (after which 429 returned)
  - Counter per IP address (not per user, to prevent enumeration)
  - Redis-backed for distributed systems
- **Token Security:**
  - Access tokens short-lived (15 minutes)
  - Refresh tokens long-lived (7 days)
  - Tokens never stored in cookies (prevents CSRF)
  - Frontend stores in memory only (prevents XSS via localStorage)

## Performance Requirements

- **Response Time:** < 300ms (P95) including password hashing
- **Throughput:** Support 100+ concurrent login requests
- **Concurrent Users:** System designed for 1000 concurrent authenticated users
- **Latency:** Token generation and validation < 50ms
- **Rate Limiting Check:** < 10ms (Redis lookup)

## Accessibility Requirements

- [ ] Keyboard navigation support (Tab through form fields)
- [ ] Screen reader compatibility (form labels announced)
- [ ] ARIA labels on form inputs (aria-label or associated labels)
- [ ] Color contrast meets WCAG standards (4.5:1)
- [ ] Focus indicators visible on form fields
- [ ] Password field properly marked as password type
- [ ] Error messages associated with form fields (aria-describedby)
- [ ] Form submission accessible via Enter key or button click

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Authentication backend tests
  - Password verification tests
  - Token generation tests
  - Rate limiting logic tests
  - Email verification check tests
- [ ] Integration tests written
  - Full login flow (successful)
  - Invalid credentials flow
  - Unverified email flow
  - Rate limiting flow
- [ ] Manual testing completed
  - Test successful login
  - Test wrong password
  - Test non-existent email
  - Test unverified email
  - Verify rate limiting
  - Test with different email cases (uppercase, spaces)
- [ ] Security audit completed
  - Verify password hashing (never plaintext)
  - Verify tokens in response (not cookies)
  - Verify rate limiting enforced
  - Verify audit log captures attempts
  - Verify no user enumeration
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Token lifecycle documentation
  - Rate limiting configuration
  - Security considerations documented
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<300ms P95)
- [ ] Load test completed (100+ concurrent requests)
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should "Remember Me" functionality be implemented? (Currently not planned)
- [ ] What should be the password reset flow for lost passwords? (US-5 covers this)
- [ ] Should login tracking be exposed to users (e.g., "last login from X IP")? (Future feature)
- [ ] Should we implement device fingerprinting for fraud detection? (Out of scope)

### Assumptions
- Email is the unique user identifier
- Passwords are hashed with Argon2
- JWT tokens are used for API authentication
- Rate limiting operates at IP level (not user level)
- Frontend will handle token storage and refresh
- SMTP/verification is working (dependency on US-2)

### Out of Scope
- Biometric authentication (fingerprint, Face ID)
- Multi-factor authentication (MFA)
- Social login (Google, GitHub)
- Login with link (passwordless authentication)
- Device trust/remember this device
- Login history exposed to users

## Related User Stories

- **US-1:** Standard User Registration (creates account for login)
- **US-2:** Email Verification (required before login)
- **US-3:** Standard User Login (THIS STORY)
- **US-4:** JWT Token Refresh (uses tokens from login)
- **US-5:** Password Reset Request (for forgotten passwords)
- **US-8:** User Profile Viewing (requires login)
- **US-12:** Logout from Current Session (ends login session)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
