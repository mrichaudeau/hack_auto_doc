# User Story: Password Reset Completion

**Story ID:** US-6
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 7 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 2

## User Story Statement

**As a** user with a valid reset link
**I want to** set a new password
**So that** I can log in with my new credentials

## Description

This user story implements the password reset completion flow, allowing users to securely change their password using a reset token. Users verify the reset token, enter their new password (meeting strength requirements), confirm the password, and submit. The system validates all inputs, hashes the new password with Argon2, marks the reset token as used (single-use), invalidates all existing refresh tokens (forcing re-authentication on all devices), and logs the password change event. Users are then redirected to login with their new credentials.

This is the second step in the password recovery process, following US-5 (Password Reset Request) where users request the reset.

## Acceptance Criteria

### Functional Criteria
- [ ] Reset form accepts new password and confirmation
- [ ] Password meets all strength requirements (same as registration)
- [ ] Token validated before allowing password change
- [ ] Expired tokens return clear error: "Reset link has expired. Please request a new one."
- [ ] Reset token is single-use only (invalidated after successful reset)
- [ ] New password hashed with Argon2
- [ ] All existing sessions/tokens invalidated after password change
- [ ] User redirected to login with success message
- [ ] Reset endpoint responds within 300ms (P95)

### Technical Criteria
- [ ] Custom endpoint: POST /api/auth/password-reset/confirm/
- [ ] Revoke all JWT refresh tokens on password change
- [ ] Log password change event for security audit
- [ ] Unit tests written (>80% coverage for validation and token logic)
- [ ] Integration tests covering reset completion flow

### UI/UX Criteria
- [ ] Password reset form is responsive
- [ ] Real-time password strength feedback
- [ ] Clear success message after reset
- [ ] Clear error messages for failures
- [ ] Accessibility standards met (WCAG 2.1 Level AA)

### Performance Criteria
- [ ] Reset endpoint responds within 300ms (P95)
- [ ] Password hashing < 100ms (Argon2 tuned parameters)
- [ ] Token refresh revocation < 50ms
- [ ] Concurrent reset operations handled correctly

### Security Criteria
- [ ] Token is single-use (marked as is_used after validation)
- [ ] Expired tokens (>60 minutes) rejected
- [ ] All refresh tokens invalidated (force re-auth everywhere)
- [ ] Password change logged for audit trail
- [ ] No sensitive data in error messages

## Technical Details

### Components Affected
**Backend:**
- Password reset completion view/viewset
- PasswordResetToken model (mark as used)
- Token blacklist service (revoke all refresh tokens)
- Security logging service
- Password validation service

**Frontend:**
- Password reset form component (with token from URL)
- Password strength indicator
- Success/error message display

**Database:**
- PasswordResetToken table (update is_used field)
- TokenBlacklist table (add revoked refresh tokens)
- SecurityAuditLog table (log password change)

### API Changes

**New Endpoint:**
- `POST /api/auth/password-reset/confirm/`
  - **Request Body:**
    ```json
    {
      "token": "eyJhbGc...",
      "new_password": "NewSecurePass123!",
      "new_password_confirm": "NewSecurePass123!"
    }
    ```
  - **Response (200 OK):**
    ```json
    {
      "message": "Password reset successfully. Please log in with your new password.",
      "redirect_url": "/login"
    }
    ```
  - **Error Response (400 Bad Request - Validation):**
    ```json
    {
      "error": "validation_error",
      "message": "Password does not meet strength requirements",
      "details": {
        "new_password": [
          "Must contain at least one uppercase letter",
          "Must contain at least one special character"
        ]
      }
    }
    ```
  - **Error Response (400 Bad Request - Token Invalid):**
    ```json
    {
      "error": "invalid_reset_token",
      "message": "Reset link is invalid or was already used. Please request a new reset email."
    }
    ```
  - **Error Response (410 Gone - Token Expired):**
    ```json
    {
      "error": "expired_reset_token",
      "message": "Reset link has expired. Please request a new one.",
      "reset_url": "/forgot-password"
    }
    ```

### Database Changes

**Modified table: PasswordResetToken**
- `used_at` (timestamp, updated when token is used)
- `is_used` (boolean, set to True after successful password reset)

**New table: SecurityAuditLog**
- `id` (UUID primary key)
- `user_id` (foreign key to User)
- `event_type` (varchar 50, e.g., "password_change", "password_reset", "logout_all")
- `description` (text, e.g., "Password changed via reset link")
- `ip_address` (inet/varchar 45)
- `user_agent` (text)
- `created_at` (timestamp)

**TokenBlacklist updates:**
- When password reset completes, all refresh tokens for user added to blacklist
- Reason: "password_reset"

**Indexes:**
- Index on SecurityAuditLog `(user_id, created_at)`
- Index on TokenBlacklist `(user_id, created_at)`

### External Integrations
- **Password Validation:** Argon2 for hashing
- **Token Revocation:** Redis or database for blacklist

## Implementation Notes

### Suggested Approach
1. Create password reset confirmation view:
   - Extract token from request body
   - Find PasswordResetToken in database
   - Validate: token exists, not used, not expired
   - Find associated User
   - Validate new password strength
   - Validate password confirmation matches
   - Perform password change:
     - Hash password with Argon2
     - Update user.password_hash
     - Mark token as used (is_used=True, used_at=now)
   - Revoke all refresh tokens (add to blacklist)
   - Log event to SecurityAuditLog
   - Return success message
2. Password validation logic:
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character (recommended but not required)
3. Token refresh revocation:
   - Query all TokenBlacklist entries for user (if using explicit blacklist)
   - Or set user.last_password_change timestamp and check in token validation
4. Security logging:
   - Log successful password change
   - Include user_id, ip_address, user_agent
   - Async logging via Celery to prevent blocking

### Technical Considerations
- **Token Validation:** Check in this order:
  1. Token exists in database
  2. is_used is False
  3. expires_at > now()
  4. Belongs to actual user (no orphaned tokens)
- **Password Strength:** Same requirements as registration (US-1)
- **Hash Function:** Use Django's make_password() with Argon2
- **Token Invalidation:** Set is_used=True and used_at=now() immediately after validation
- **Session Invalidation:** Add all user's refresh tokens to blacklist (or use timestamp approach)
- **Audit Trail:** Log password change with timestamp, IP, user agent
- **Response Time:** Should be < 300ms (including Argon2 hashing which takes ~100ms)
- **Idempotency:** If user submits same token twice:
  - First request: Success, token marked as used
  - Second request: Token already used, return error

### Known Challenges
- Argon2 hashing can take 100+ ms (security vs performance tradeoff)
- Revoking all refresh tokens across distributed systems requires centralized blacklist
- Balancing password strength requirements with user experience
- Handling concurrent password reset requests for same user

## Dependencies

### Depends On
- **US-5:** Password Reset Request (creates reset token)
- **US-1:** Standard User Registration (user must exist first)
- **Infrastructure:** Argon2 library (argon2-cffi)
- **Infrastructure:** Redis (for token blacklist, optional)

### Blocks
- **US-3:** Standard User Login (user logs in with new password)

## Test Scenarios

### Happy Path
1. User receives password reset email (US-5)
2. User clicks reset link with token
3. Navigates to password reset page (/reset-password?token=...)
4. Page extracts token from URL
5. Token is validated (exists, not used, not expired)
6. Page displays password reset form with fields:
   - New Password
   - Confirm Password
7. User enters new password meeting all requirements (e.g., "NewSecurePass123!")
8. Real-time feedback shows password strength
9. User confirms password with same value
10. User clicks "Reset Password" button
11. Form submission:
    - Token in request body (extracted from URL)
    - New password and confirmation
12. Backend validates:
    - Token: exists, not used, not expired, belongs to user
    - Password: meets strength requirements
    - Confirmation: matches password
13. Backend performs reset:
    - Hashes password with Argon2
    - Updates user.password
    - Marks token as used (is_used=True, used_at=now)
    - Invalidates all refresh tokens (added to blacklist)
    - Logs event: user_id, event_type=password_reset, ip_address, user_agent
14. Response (200 OK):
    - Message: "Password reset successfully. Please log in with your new password."
    - Redirect URL: "/login"
15. Frontend redirects to login page
16. User sees success message: "Your password has been reset. Please log in with your new password."
17. User logs in with new credentials (US-3)

### Alternative Paths
1. **Password Reset Before Expiry:**
   - User resets password after 30 minutes (before 60-minute expiry)
   - Everything same as happy path
   - Success

2. **Reset Request with Different Device:**
   - User requests password reset on Device A
   - User receives email on Device B
   - User clicks reset link on Device B
   - Completes reset on Device B
   - Token is single-use and valid
   - Success

### Error Scenarios
1. **Expired Reset Token:**
   - User receives reset email
   - Waits 61+ minutes
   - Clicks reset link
   - Backend validates: expires_at < now()
   - Returns 410 Gone
   - Error: "Reset link has expired. Please request a new one."
   - Display: "Request New Reset Email" button (links to US-5)

2. **Already Used Token:**
   - User completes password reset
   - User (or attacker) tries same reset link again
   - Backend validates: is_used = True
   - Returns 400 Bad Request
   - Error: "Reset link is invalid or was already used. Please request a new reset email."

3. **Invalid/Malformed Token:**
   - User modifies token in URL
   - Backend cannot decode token
   - Returns 400 Bad Request
   - Error: "Reset link is invalid or was already used."

4. **Tampered Token:**
   - Attacker modifies reset link
   - Backend queries database: token not found
   - Returns 400 Bad Request
   - Error: "Reset link is invalid or was already used."

5. **Weak Password:**
   - User enters "password" (no uppercase, number, or special char)
   - Frontend validation may catch first
   - Backend validation catches if frontend bypassed
   - Returns 400 Bad Request
   - Error: "Password must contain at least one uppercase letter, one number, and one special character"
   - Form redisplays with error

6. **Password Confirmation Mismatch:**
   - User enters "NewSecurePass123!" and confirms as "NewSecurePass124!"
   - Returns 400 Bad Request
   - Error: "Passwords do not match"

7. **User Account Deleted:**
   - User requests reset for email (account exists)
   - Between reset request and reset completion, account deleted
   - Backend attempts to find user by token
   - User not found
   - Returns 404 Not Found
   - Error: "Account not found. Please register again."

8. **Multiple Reset Requests:**
   - User requests reset multiple times, gets multiple tokens
   - Uses first token to reset password
   - Tries second token
   - Second token is invalid (different token, not yet marked used)
   - Actually, second token is VALID (independent tokens)
   - Second reset succeeds, overwrites password
   - Both resets work independently (no issue)

### Edge Cases
1. **Very Strong Password:**
   - User enters very long password (100+ characters)
   - System accepts (no max length requirement stated)
   - Hashed password stored (always same length after hashing)
   - Success

2. **Special Characters Only:**
   - User enters "!@#$%^&*()" (special chars but no letters/numbers)
   - System validates: missing uppercase, lowercase, number
   - Returns validation error

3. **Unicode Characters:**
   - User enters "NéwPàss123!" (with accented characters)
   - System accepts if database/encoding supports UTF-8
   - Stored and validated correctly

4. **SQL Injection Attempt:**
   - User enters "' OR '1'='1" as password
   - ORM parameterization prevents injection
   - Password stored as literal string (no injection risk)
   - Success (unusual password, but no security risk)

5. **Concurrent Reset Requests:**
   - User somehow submits password reset twice simultaneously
   - Database transaction ensures only one succeeds
   - Other receives duplicate key error (token already marked used)
   - Should be handled gracefully

6. **Reset After Already Logged In:**
   - User is already logged in (has valid session)
   - User requests password reset
   - Token invalidates all refresh tokens
   - User's current session (if JWT-based) remains valid until access token expires
   - Next token refresh fails (refresh token blacklisted)
   - User must re-login (expected behavior)

## UI/UX Specifications

### User Flow
1. User arrives at password reset page (/reset-password?token=...)
2. Page extracts and validates token from URL
   - If invalid/expired: Shows error message and "Request New Reset" button
   - If valid: Shows password reset form
3. Page displays:
   - Heading: "Reset Your Password"
   - Message: "Enter a new password to regain access to your account"
   - New Password field
   - Confirm Password field
   - Password strength indicator (real-time)
   - Requirements checklist showing:
     - ✓/○ Minimum 8 characters
     - ✓/○ Contains uppercase letter
     - ✓/○ Contains lowercase letter
     - ✓/○ Contains number
     - ○/✓ Contains special character (recommended)
   - "Reset Password" button
4. User enters new password
   - Real-time feedback updates requirements checklist
   - Strength meter shows: Weak/Fair/Good/Strong
5. User confirms password
   - Shows match status
6. User clicks "Reset Password"
7. Button shows loading state
8. After 1-2 seconds:
   - **Success:** Success page displays
     - Message: "Password reset successfully!"
     - Message: "You can now log in with your new password"
     - Button: "Go to Login" (links to /login)
   - **Error:** Error message displays on form
     - Message explains error (expired token, validation failure, etc.)
     - Button: "Request New Reset Email" (if error is expired/invalid token)

### Email Verification Form (User's Perspective)
- Heading: "Change Your Password"
- Explanation: "Your password has been reset. You are now logged out from all devices."
- Message: "Please log in again with your new credentials."
- Login button

### Design Assets
- Link to password reset form design: [password-reset-form-component]
- Link to password strength indicator: [password-strength-meter]
- Link to success page design: [password-reset-success-page]

## Security Considerations

- **Authentication:** Not required initially, but password reset validates token ownership
- **Authorization:** Only user who owns the reset token can reset their password
- **Data Validation:**
  - Token format validation (exists in database)
  - Password strength validation
  - Password confirmation matching
- **Encryption:** Passwords hashed with Argon2 (not encrypted)
- **Audit Logging:**
  - Log all password reset attempts (success and failure)
  - Include user_id, IP address, user agent
  - Log token expiry/invalid errors for security monitoring
  - Include timestamp
- **Session Invalidation:**
  - All refresh tokens invalidated immediately
  - Access tokens remain valid until expiry (max 15 minutes)
  - Forces re-authentication everywhere
- **Rate Limiting:** Not explicit (token-based limiting - can only reset once per token)
- **Timing Attacks:** Token validation timing might leak information (minor risk)

## Performance Requirements

- **Response Time:** < 300ms (P95) including Argon2 hashing
- **Password Hashing:** ~100ms (Argon2 tuned parameters)
- **Token Validation:** < 20ms
- **Token Revocation:** < 50ms (blacklist update)
- **Audit Logging:** < 10ms (async)
- **Throughput:** Support 50+ concurrent password resets
- **Concurrent Users:** System designed for 1000 concurrent users

## Accessibility Requirements

- [ ] Keyboard navigation support (Tab through fields)
- [ ] Screen reader compatibility (form labels)
- [ ] ARIA labels on inputs
- [ ] Password strength indicator accessible (aria-live for updates)
- [ ] Color contrast meets WCAG standards
- [ ] Focus indicators visible
- [ ] Error messages associated with fields (aria-describedby)
- [ ] Requirements list read by screen readers

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage)
  - Token validation tests
  - Password strength validation
  - Password confirmation matching
  - Hash verification
  - Token single-use enforcement
  - Refresh token revocation
  - Audit logging
- [ ] Integration tests written
  - Full reset completion flow
  - Expired token flow
  - Invalid token flow
  - Invalid password flow
  - Concurrent reset requests
  - Refresh token revocation verification
- [ ] Manual testing completed
  - Test successful password reset
  - Test expired token
  - Test invalid token
  - Test weak password validation
  - Test password confirmation mismatch
  - Verify password hashed in database
  - Verify refresh tokens revoked
  - Verify audit log entry created
  - Verify re-login required after reset
- [ ] Frontend password strength component tested
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Password requirements documentation
  - Security considerations documented
  - Refresh token revocation explained
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<300ms P95)
- [ ] Security audit completed
  - Password hashing verified (Argon2)
  - Token validation verified
  - Refresh token revocation verified
  - Audit logging verified
  - No sensitive data in errors
- [ ] Load test completed (50+ concurrent resets)
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] Should password reset also require email verification? (Currently no)
- [ ] Should we send confirmation email after successful reset? (Recommended for security)
- [ ] Should we allow resetting same password? (Currently no explicit check)
- [ ] Should reset tokens be usable multiple times (with confirmation)? (Currently single-use only)

### Assumptions
- User has received reset email with valid token
- User's email inbox is secure
- Argon2 library is properly configured
- Database can handle token blacklist operations
- Users will log back in after password reset

### Out of Scope
- SMS-based password reset verification
- Security questions for additional verification
- Biometric verification for password reset
- Password reset confirmation email (separate feature)
- Admin-initiated password resets (separate admin feature)

## Related User Stories

- **US-5:** Password Reset Request (creates reset token)
- **US-6:** Password Reset Completion (THIS STORY)
- **US-3:** Standard User Login (user logs in with new password)
- **US-1:** Standard User Registration (similar password requirements)
- **US-10:** Password Change (different flow, requires current password)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
