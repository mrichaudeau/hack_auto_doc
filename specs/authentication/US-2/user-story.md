# User Story: Email Verification

**Story ID:** US-2
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P0
**Effort Estimate:** 5 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 1

## User Story Statement

**As a** newly registered user
**I want to** verify my email address via a secure link
**So that** I can activate my account and access the platform

## Description

This user story implements the email verification flow that activates a user's account after registration. Users receive a verification email containing a unique, time-limited token (24-hour expiry). Clicking the verification link confirms the user's email ownership and activates their account, allowing them to log in. Users can request new verification emails if the original expires or if they need to resend it. Verification tokens are single-use and cannot be reused.

This is a critical security feature ensuring that users own the email addresses they register with and preventing account takeovers via incorrect email addresses.

## Acceptance Criteria

### Functional Criteria
- [ ] Verification email contains unique, time-limited token (24-hour expiry)
- [ ] Clicking verification link activates the account
- [ ] User redirected to login page with success message after verification
- [ ] Expired tokens display clear error: "Verification link has expired. Please request a new one."
- [ ] User can request new verification email (maximum 3 times per day)
- [ ] Verification token is single-use only
- [ ] Already verified accounts cannot be re-verified
- [ ] Verification endpoint responds within 200ms (P95)

### Technical Criteria
- [ ] Verification tokens stored with expiry timestamp in database
- [ ] Token uniqueness enforced (cryptographically random)
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests covering verification flow

### UI/UX Criteria
- [ ] Verification success page displays clear message with next steps
- [ ] Verification failure page displays clear error with resend option
- [ ] Email template is professional and branded
- [ ] Responsive design works on all devices
- [ ] Accessibility standards met (WCAG 2.1 Level AA)

### Performance Criteria
- [ ] Verification endpoint responds within 200ms (P95)
- [ ] Email resend endpoint responds within 300ms (P95)
- [ ] Resend rate limiting enforced without performance degradation

## Technical Details

### Components Affected
**Backend:**
- User model (is_active, is_email_verified fields)
- Email verification token model
- Verification views/viewsets
- Email service

**Frontend:**
- Verification link click handler
- Email verification page component
- Resend verification email component

**Database:**
- EmailVerificationToken table
- Users table (modifications for verification status)

### API Changes

**New Endpoints:**

1. **Verify Email Token:**
   - `GET /api/auth/verify-email/`
   - **Query Parameters:** `?token=<verification_token>`
   - **Response (200 OK):**
     ```json
     {
       "message": "Email verified successfully. You can now log in.",
       "is_active": true,
       "is_email_verified": true
     }
     ```
   - **Error Response (400/410):**
     ```json
     {
       "error": "invalid_token",
       "message": "Verification link has expired. Please request a new one.",
       "resend_url": "/verify-email/resend"
     }
     ```

2. **Resend Verification Email:**
   - `POST /api/auth/resend-verification/`
   - **Request Body:**
     ```json
     {
       "email": "user@example.com"
     }
     ```
   - **Response (200 OK):**
     ```json
     {
       "message": "Verification email sent. Please check your email.",
       "next_retry_available_in_seconds": 3600
     }
     ```
   - **Error Response (429):**
     ```json
     {
       "error": "rate_limited",
       "message": "Too many verification email requests. Please try again in 1 hour.",
       "retry_after_seconds": 3600
     }
     ```

### Database Changes

**New table: EmailVerificationToken**
- `id` (UUID primary key)
- `user_id` (foreign key to User)
- `token` (unique, varchar 255, cryptographically random)
- `created_at` (timestamp)
- `expires_at` (timestamp, expires_at = created_at + 24 hours)
- `used_at` (timestamp, nullable, marks when token was used)
- `is_used` (boolean, default False, single-use enforcement)

**Modified table: User**
- `is_email_verified` (boolean, default False)
- `email_verified_at` (timestamp, nullable)

**Indexes:**
- Index on `token` (for lookup)
- Index on `user_id` and `created_at` (for cleanup queries)
- Index on `expires_at` (for cleanup of expired tokens)

### External Integrations
- **Email Service:** SMTP configured for sending verification emails
- **Token Generation:** Cryptographically random token generation

## Implementation Notes

### Suggested Approach
1. Create EmailVerificationToken model with expiry logic
2. Generate cryptographically random tokens (32+ characters)
3. Create verification view that:
   - Accepts token as query parameter
   - Validates token existence and uniqueness
   - Checks expiry timestamp
   - Marks token as used (prevents reuse)
   - Activates user account
   - Returns success/error response
4. Create resend view that:
   - Accepts email address
   - Finds user account
   - Checks resend rate limit (max 3 per day)
   - Generates new token
   - Sends verification email
5. Set up periodic cleanup task (Celery Beat) to delete expired tokens
6. Implement in django-allauth or custom solution

### Technical Considerations
- **Token Generation:** Use secrets.token_urlsafe(32) for cryptographically random tokens
- **Token Storage:** Store in database (not email links themselves) for security
- **Single-Use Enforcement:** Set is_used flag upon verification, check before using
- **Expiry:** Use timestamp comparison (expires_at > now()) instead of age calculation
- **Rate Limiting:** Use Redis-backed counter for resend attempts per email per day
- **Idempotency:** Resend should work even if previous verification failed
- **Cleanup:** Periodic task to delete expired tokens (>30 days old) to prevent table bloat
- **Email Verification Link:** Structure as `/verify-email?token=<token>` (GET for clickability in emails)

### Known Challenges
- Email client rendering: Some clients strip query parameters (use hash routing if needed)
- Token length balancing: Long tokens are secure but create long URLs
- Clock skew: Distributed system clock differences could affect expiry
- Email delivery delays: Users may click link hours after receiving email

## Dependencies

### Depends On
- **US-1:** Standard User Registration (users must be registered first)
- **Infrastructure:** SMTP Server (for email sending)
- **Infrastructure:** Redis (for resend rate limiting)

### Blocks
- **US-3:** Standard User Login (users must verify email before login)
- **US-8:** User Profile Viewing (requires verified account)

## Test Scenarios

### Happy Path
1. User receives verification email after registration (US-1)
2. User clicks verification link in email
3. System retrieves token and validates:
   - Token exists in database
   - Token not yet used (is_used = False)
   - Token not expired (expires_at > now)
   - Token belongs to user email address
4. User account activated (is_active = True, is_email_verified = True)
5. Token marked as used (is_used = True)
6. User redirected to login page
7. Success message: "Email verified successfully. You can now log in."
8. User can now log in with verified account

### Alternative Paths
1. **Resend Verification Email:**
   - User didn't receive first verification email
   - User navigates to "Resend Verification" page
   - Enters email address
   - System finds user account
   - Checks rate limit: user hasn't exceeded 3 resends per day
   - Generates new verification token
   - Sends new verification email
   - Message: "Verification email sent. Please check your email."
   - New token stored, old token not invalidated

2. **Multiple Resend Requests:**
   - Same user submits resend request twice within seconds
   - Only one new token generated per resend (idempotent)
   - Both requests receive "Verification email sent" message

### Error Scenarios
1. **Expired Token:**
   - User receives verification email
   - User waits 25+ hours
   - Clicks verification link
   - System checks: token expires_at < now
   - Returns 410 Gone status
   - Error: "Verification link has expired. Please request a new one."
   - Display link to resend verification page

2. **Invalid Token:**
   - User manually modifies token in URL
   - System cannot find token in database
   - Returns 400 Bad Request
   - Error: "Invalid verification link. Please request a new email."

3. **Already Verified Account:**
   - User has already verified email (is_email_verified = True)
   - User clicks verification link again
   - System detects already verified
   - Returns 400 Bad Request or 200 with info message
   - Message: "Your email is already verified. You can log in now."

4. **Rate Limit Exceeded:**
   - User attempts to resend verification email 4 times in one day
   - 4th attempt rejected with 429 Too Many Requests
   - Error: "Too many verification email requests. Please try again in 1 hour."
   - Include: `Retry-After: 3600` header

5. **User Account Deleted:**
   - User receives verification email
   - User account is deleted by admin
   - User clicks verification link
   - System cannot find user
   - Returns 404 Not Found
   - Error: "Account not found. Please register again."

### Edge Cases
1. **Token Used Twice:**
   - User clicks verification link
   - System marks token as used
   - User clicks same link again
   - System detects is_used = True
   - Returns: "Verification link already used. Please request a new email."

2. **Race Condition:**
   - Two simultaneous requests with same token
   - Database transaction ensures only one succeeds
   - Second request fails gracefully

3. **Verification During Reset:**
   - User registers, receives verification email
   - User requests password reset (before verifying email)
   - User clicks password reset link
   - System should handle: unverified account receiving reset link
   - Allow reset but still require email verification after login

4. **Very Old Token:**
   - Token created >30 days ago
   - Periodic cleanup task deleted from database
   - User clicks verification link
   - System cannot find token
   - Returns: "Verification link is no longer valid. Please register again."

## UI/UX Specifications

### User Flow - Successful Verification
1. User receives email with subject: "Verify your email for [Platform Name]"
2. Email contains:
   - Welcome message
   - Verification button/link: "Verify Email"
   - Link URL: `https://app.example.com/verify-email?token=<token>`
   - Fallback text link for email clients that don't support buttons
   - Expiry notice: "This link expires in 24 hours"
3. User clicks verification link
4. Browser loads verification page (/verify-email?token=...)
5. Page displays: "Verifying your email..."
6. After verification completes (1-2 seconds)
7. Success page displays:
   - Checkmark icon
   - Message: "Your email has been verified!"
   - Message: "You can now log in to your account"
   - Button: "Go to Login" (links to /login)
8. User can now log in

### User Flow - Failed Verification
1. User clicks verification link (expired or invalid)
2. Page displays: "Email verification failed"
3. Error message with reason:
   - "Verification link has expired. Please request a new one."
   - "Verification link is invalid or was already used."
4. Button options:
   - "Request new verification email" (navigates to resend form)
   - "Back to login" (navigates to /login)

### User Flow - Resend Verification
1. User navigates to "Resend Verification Email" page
2. Form displays email field (pre-filled if user is on after registration)
3. User enters email address (if not pre-filled)
4. User clicks "Resend Email" button
5. After submission:
   - Success message: "If an account exists, a verification email has been sent."
   - (Note: Don't reveal whether email exists for security)
6. Countdown timer shown: "You can request a new email in 3600 seconds"
7. User can return to check email

### Design Assets
- Link to email template design: [verification-email-template]
- Link to success page design: [verification-success-page]
- Link to resend form design: [verification-resend-form]

## Security Considerations

- **Authentication:** Not yet required (but can be applied)
- **Authorization:** Resend endpoint is public; verification endpoint can be public or require minimal auth
- **Data Validation:**
  - Token format validation
  - Email format validation (in resend)
  - User existence check
- **Encryption:** Tokens are random strings (not encrypted), transmitted via HTTPS only
- **Audit Logging:**
  - Log all verification attempts (success and failure)
  - Log all resend requests with email and IP
  - Include timestamp and outcome
- **Rate Limiting:**
  - Resend: 3 attempts per email per 24 hours
  - Verification attempts: No limit (only token expiry prevents brute force)
- **No User Enumeration:** When resending, don't reveal whether email exists in system

## Performance Requirements

- **Verification Endpoint Response Time:** < 200ms (P95)
- **Resend Endpoint Response Time:** < 300ms (P95)
- **Email Delivery Time:** Within 30 seconds of resend request (async)
- **Throughput:** Support 100+ concurrent verification requests
- **Concurrent Users:** System designed for 1000 concurrent active users

## Accessibility Requirements

- [ ] Verification link clickable in all email clients
- [ ] Success/error pages keyboard navigable
- [ ] Screen reader friendly error messages
- [ ] ARIA labels on resend form
- [ ] Color contrast meets WCAG standards
- [ ] Focus indicators visible on links and buttons

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Token generation and validation
  - Expiry timestamp logic
  - Single-use enforcement
  - Rate limiting
  - Email sending
- [ ] Integration tests written
  - Full verification flow
  - Resend request flow
  - Edge cases (expired tokens, already verified)
- [ ] Manual testing completed
  - Test verification link click
  - Test expired token
  - Test already verified account
  - Verify rate limiting
  - Test email delivery
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Email template documentation
  - Admin guide for managing verification tokens
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<200ms for verification)
- [ ] Security review completed
  - Token randomness verified
  - Rate limiting verified
  - Email template reviewed for phishing prevention
  - No PII leaked in URLs
- [ ] Periodic cleanup task tested (removes expired tokens)
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] What should be the rate limit for resend? (Currently 3 per 24 hours)
- [ ] Should verification tokens be reusable or single-use? (Currently single-use)
- [ ] What email template branding should be used?
- [ ] Should expired tokens be automatically deleted or retained for audit?

### Assumptions
- Users will click verification link within 24 hours
- Email delivery will be reliable (>99% success rate)
- SMTP service is configured and operational
- Users have access to their email inbox

### Out of Scope
- SMS verification (only email)
- Two-factor authentication (separate feature)
- Email domain verification (whitelist/blacklist)
- Custom verification templates per organization

## Related User Stories

- **US-1:** Standard User Registration (creates unverified account)
- **US-3:** Standard User Login (requires verified account)
- **US-5:** Password Reset Request (may interact with unverified accounts)
- **US-8:** User Profile Viewing (requires verified account)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
