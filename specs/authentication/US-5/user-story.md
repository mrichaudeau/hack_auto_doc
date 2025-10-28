# User Story: Password Reset Request

**Story ID:** US-5
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 6 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 2

## User Story Statement

**As a** user who forgot my password
**I want to** request a password reset via my email
**So that** I can regain access to my account

## Description

This user story implements the password reset request flow, allowing users who have forgotten their password to securely recover their account. Users enter their email address, and the system sends a password reset email containing a time-limited link (60-minute expiry) with a unique token. The system uses generic success messages to prevent user enumeration attacks (doesn't reveal whether an email exists in the system). Rate limiting prevents abuse. The reset email is sent within 60 seconds of the request.

This is the first step in the password recovery process, followed by US-6 (Password Reset Completion) where users actually change their password.

## Acceptance Criteria

### Functional Criteria
- [ ] Password reset form accepts email address
- [ ] System sends reset email if account exists (no user enumeration)
- [ ] Reset email contains secure, time-limited link (60-minute expiry)
- [ ] Reset link includes unique token
- [ ] Success message displayed regardless of email existence: "If an account exists, you will receive a reset email"
- [ ] Rate limiting: Maximum 3 reset requests per email per hour
- [ ] Reset email sent within 60 seconds of request
- [ ] Password reset endpoint responds within 300ms (P95)

### Technical Criteria
- [ ] Use django-allauth password reset flow or custom implementation
- [ ] Store reset tokens with 60-minute expiry in database
- [ ] Unit tests written (>80% coverage for token generation and rate limiting)
- [ ] Integration tests covering request flow and error scenarios

### UI/UX Criteria
- [ ] Password reset request form is responsive
- [ ] Success message clear and consistent (regardless of email existence)
- [ ] Option to return to login page or resend request
- [ ] Email template is professional and branded
- [ ] Accessibility standards met (WCAG 2.1 Level AA)

### Performance Criteria
- [ ] Request endpoint responds within 300ms (P95)
- [ ] Email sending (async) completes within 60 seconds
- [ ] Rate limiting check overhead < 10ms

### Security Criteria
- [ ] No user enumeration via response differences
- [ ] Rate limiting enforced: 3 per email per hour
- [ ] Reset tokens are cryptographically random
- [ ] Reset tokens expire after 60 minutes
- [ ] Email template reviewed for phishing prevention

## Technical Details

### Components Affected
**Backend:**
- PasswordResetToken model
- Password reset request view/viewset
- Email service
- Rate limiting service

**Frontend:**
- Password reset request form component
- Success page component

**Database:**
- PasswordResetToken table
- Rate limiting cache (Redis)

### API Changes

**New Endpoint:**
- `POST /api/auth/password-reset/`
  - **Request Body:**
    ```json
    {
      "email": "user@example.com"
    }
    ```
  - **Response (200 OK) - Always for security:**
    ```json
    {
      "message": "If an account exists, you will receive a reset email"
    }
    ```
  - **Response (429 Too Many Requests - Rate Limit):**
    ```json
    {
      "error": "rate_limited",
      "message": "Too many password reset requests. Please try again in 1 hour.",
      "retry_after_seconds": 3600
    }
    ```

### Database Changes

**New table: PasswordResetToken**
- `id` (UUID primary key)
- `user_id` (foreign key to User)
- `token` (unique, varchar 255, cryptographically random)
- `created_at` (timestamp)
- `expires_at` (timestamp, expires_at = created_at + 60 minutes)
- `used_at` (timestamp, nullable, marks when token was used)
- `is_used` (boolean, default False, single-use enforcement)

**Indexes:**
- Index on `token` (for lookup during password reset confirmation)
- Index on `user_id` (for finding active reset requests for user)
- Index on `expires_at` (for cleanup queries)
- Index on `(user_id, created_at)` (for rate limiting)

### External Integrations
- **Email Service:** SMTP configured for sending reset emails
- **Token Generation:** Cryptographically random token generation
- **Redis:** For rate limiting cache

## Implementation Notes

### Suggested Approach
1. Create PasswordResetToken model similar to EmailVerificationToken:
   - Unique cryptographically random token
   - FK to User
   - Expiry timestamp (60 minutes)
   - Single-use enforcement (is_used flag)
2. Create password reset request view:
   - Accepts email in request body
   - Validates email format (not user existence)
   - Checks rate limit (3 per email per hour in Redis)
   - Finds user by email (if exists)
   - Generates new reset token
   - Sends reset email (async via Celery)
   - Returns generic success message
3. Implement rate limiting:
   - Redis counter keyed by email
   - Increment on each request (regardless of success)
   - 1-hour reset window
   - Returns 429 if exceeded
4. Email sending (async):
   - Celery task for async execution
   - Includes reset link with token
   - Professional email template
   - Configurable branding

### Technical Considerations
- **Token Generation:** Use secrets.token_urlsafe(32) for cryptographically random
- **Rate Limiting:** Per-email (not per IP) to prevent legitimate users from being blocked
- **Success Message:** Always return 200 OK with generic message (prevents user enumeration)
- **Email Sending:** Async Celery task to prevent request blocking
- **Resend Logic:** Each request generates new token; old tokens become invalid
- **Idempotency:** Multiple requests within window generate new tokens (not idempotent, but safe)
- **Cleanup:** Periodic task to delete expired tokens (>30 days old)
- **Email Format:** Structure reset link as `/reset-password?token=<token>` (GET for email clickability)

### Known Challenges
- User enumeration via timing attacks (response time differences)
- Email delivery delays (user may click old token before new one received)
- Distinguishing between rate limiting and legitimate requests (human factor)
- Clock synchronization in distributed systems

## Dependencies

### Depends On
- **US-1:** Standard User Registration (users must exist first)
- **Infrastructure:** SMTP Server (for email sending)
- **Infrastructure:** Redis (for rate limiting)

### Blocks
- **US-6:** Password Reset Completion (must request reset first)

## Test Scenarios

### Happy Path
1. User navigates to login page
2. Clicks "Forgot Password?" link
3. Navigated to password reset request page
4. User enters registered email address
5. Clicks "Send Reset Email" button
6. System validates:
   - Email format is valid
   - Not blank
7. System checks rate limit:
   - User hasn't exceeded 3 requests per hour for this email
8. System finds user account by email
9. System generates new PasswordResetToken:
   - Random token generated
   - expires_at = now + 60 minutes
   - is_used = False
   - Stored in database
10. Async Celery task sends email:
    - To: user's email
    - Subject: "Password Reset Request"
    - Body includes reset link: https://app.example.com/reset-password?token=<token>
    - Sent within 60 seconds
11. Endpoint returns 200 OK
    - Message: "If an account exists, you will receive a reset email"
12. Page displays success message
13. User checks email inbox
14. Receives password reset email
15. User clicks reset link (leading to US-6)

### Alternative Paths
1. **Multiple Reset Requests:**
   - User requests reset, doesn't receive email (false negative)
   - User requests reset again within 1 hour
   - Second request is not rate limited (< 3 per hour)
   - New token generated
   - New email sent
   - Only newest token is valid

2. **Reset Request, Then Login:**
   - User requests password reset
   - Later remembers password
   - User logs in normally
   - Previous reset tokens remain valid but unused
   - User can still use reset link if needed

### Error Scenarios
1. **Rate Limit Exceeded:**
   - User requests password reset 4 times in 1 hour for same email
   - 4th request rejected
   - Returns 429 Too Many Requests
   - Message: "Too many password reset requests. Please try again in 1 hour."
   - Header: `Retry-After: 3600`
   - No email sent

2. **Invalid Email Format:**
   - User enters "notanemail"
   - System validates email format
   - Returns 400 Bad Request
   - Message: "Please enter a valid email address"
   - Does NOT reveal whether email exists
   - Does NOT increment rate limit

3. **Non-Existent Email:**
   - User enters valid format but non-existent email
   - System cannot find user
   - Returns 200 OK (same as success for security)
   - Message: "If an account exists, you will receive a reset email"
   - No email sent
   - Does increment rate limit (to prevent enumeration via rapid requests)

4. **Email Sending Failure:**
   - System generates token
   - Celery task fails to send email (SMTP down)
   - Token stored in database
   - Celery retry logic attempts 3 times
   - After 3 failures, logged for admin review
   - User doesn't receive email (sad case, requires support intervention)
   - User can request new reset email (rate limit allows 3 per hour)

5. **Account Deleted:**
   - User requests reset for email that existed
   - Between request and email send, account deleted
   - Celery task attempts to send (may fail or succeed)
   - Even if email sent, user cannot log in (account doesn't exist)
   - Next step (US-6) fails appropriately

### Edge Cases
1. **Uppercase/Lowercase Email:**
   - User registers with "User@Example.com"
   - Requests reset with "user@example.com"
   - System performs case-insensitive lookup
   - Reset works correctly

2. **Email with Whitespace:**
   - User enters " user@example.com " (leading/trailing spaces)
   - System trims whitespace
   - Reset works correctly

3. **Multiple Users (shouldn't exist, but edge case):**
   - (After deduplication logic) only one user per email
   - Reset finds correct user

4. **Rapid Rate Limit Boundary:**
   - 3 requests made, all within 1 hour window
   - 3rd request succeeds (at limit)
   - 4th request rejected (exceeds limit)
   - After 1 hour from first request, new request allowed

5. **Token Generation Collision:**
   - System generates random token
   - Collision with existing token (extremely unlikely)
   - Database constraint prevents duplicate token
   - Retry token generation
   - (Cryptographically random, collision probability ~0)

## UI/UX Specifications

### User Flow
1. User arrives at password reset request page (/forgot-password)
2. Page displays:
   - Heading: "Reset Your Password"
   - Text: "Enter your email address and we'll send you a link to reset your password"
   - Email input field
   - "Send Reset Email" button
   - Link back to login: "Remember your password? Sign In"
3. User enters email address
4. User clicks "Send Reset Email"
5. Button shows loading state
6. After 1-2 seconds:
   - Success page displays
   - Message: "Success! Check your email for reset instructions"
   - Message: "If you don't see an email in a few minutes, check your spam folder"
   - Button: "Back to Sign In"
   - Message: "Didn't receive an email? You can try again in a few minutes"
7. User checks email inbox
8. Receives password reset email with subject: "Password Reset Request - [Platform Name]"
9. Email contains:
   - Reset button/link: "Reset Password"
   - Link URL: `https://app.example.com/reset-password?token=<token>`
   - Message: "This link expires in 60 minutes"
   - Message: "If you didn't request this, ignore the email"
10. User clicks reset link
11. Navigates to password reset confirmation page (US-6)

### Email Template
- Professional branding with logo
- Clear subject line: "Password Reset Request"
- Friendly greeting: "Hi [First Name],"
- Clear call-to-action button
- Expiry notice: "This link expires in 60 minutes"
- Fallback text link for email clients that don't support buttons
- Footer with support contact information
- Unsubscribe option (if mailing list subscriptions exist)

### Design Assets
- Link to password reset request form design: [password-reset-request-form]
- Link to password reset email template: [password-reset-email-template]
- Link to success page design: [password-reset-success-page]

## Security Considerations

- **Authentication:** Not required (public endpoint)
- **Authorization:** Not applicable
- **Data Validation:**
  - Email format validation
  - No validation of password (not yet entered)
- **Encryption:** Tokens are random strings (not encrypted), transmitted via HTTPS
- **Audit Logging:**
  - Log all reset requests with email (hashed) and IP address
  - Log rate limit violations for security monitoring
  - Include timestamp and outcome
- **Rate Limiting:**
  - 3 requests per email per hour (prevents enumeration and abuse)
  - Per-email (not per IP) for better UX
  - Cached in Redis
- **No User Enumeration:**
  - Response always 200 OK with generic message
  - Rate limit increments even for non-existent emails (but not if validation fails)
  - Timing attack possible but mitigated by async email sending
- **Email Template Security:**
  - No sensitive data in email
  - Token in URL (standard practice)
  - Link expires in 60 minutes
  - Includes warning about unsolicited emails

## Performance Requirements

- **Request Endpoint Response Time:** < 300ms (P95)
- **Email Sending (Async):** Completes within 60 seconds
- **Rate Limiting Check:** < 10ms (Redis lookup)
- **Throughput:** Support 100+ concurrent reset requests
- **Concurrent Users:** System designed for 1000 concurrent active users

## Accessibility Requirements

- [ ] Keyboard navigation support (Tab through form)
- [ ] Screen reader compatibility (form labels)
- [ ] ARIA labels on form inputs
- [ ] Color contrast meets WCAG standards
- [ ] Focus indicators visible
- [ ] Error messages associated with form fields
- [ ] Success page accessible

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Token generation tests
  - Email format validation tests
  - Rate limiting logic tests
  - Success message verification
- [ ] Integration tests written
  - Full reset request flow
  - Rate limiting enforcement
  - Email sending verification
  - Non-existent email handling
- [ ] Manual testing completed
  - Test successful reset request
  - Test rate limiting
  - Verify email delivery
  - Test with various email formats
  - Test non-existent email (verify generic response)
- [ ] Email template reviewed for:
  - Professional appearance
  - Phishing prevention
  - Spam filter compatibility
  - Responsive design on mobile
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Email template documentation
  - Rate limiting configuration
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<300ms P95)
- [ ] Security review completed
  - Token randomness verified
  - Rate limiting verified
  - No user enumeration possible
  - Email template reviewed
- [ ] Celery task tested with retry logic
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should rate limit be per-email or per-IP? (Currently per-email)
- [ ] What should be the reset token expiry? (Currently 60 minutes)
- [ ] Should we send reset emails to admin if too many requests? (Potential future feature)
- [ ] Should we implement CAPTCHA for reset requests? (Out of scope, not needed with rate limiting)

### Assumptions
- SMTP service is configured and operational
- Redis is available for rate limiting
- Email delivery is reliable (>99%)
- Users have access to their email inbox
- Users won't lose access to their email account

### Out of Scope
- SMS-based password reset
- Security questions for identity verification
- CAPTCHA for reset requests
- Multi-factor authentication for reset
- Admin manual password reset (separate admin feature)

## Related User Stories

- **US-1:** Standard User Registration (creates account that may need password reset)
- **US-5:** Password Reset Request (THIS STORY)
- **US-6:** Password Reset Completion (next step, uses token from US-5)
- **US-3:** Standard User Login (user returns after resetting password)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
