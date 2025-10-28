# User Story: Account Unification (SSO + Standard)

**Story ID:** US-11
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P2
**Effort Estimate:** 8 story points
**Assigned To:** [Developer Name]
**Sprint:** [Sprint Number]

## User Story Statement

**As a** user with an existing standard account
**I want to** link my Microsoft Entra ID to my existing account when I attempt SSO login
**So that** I can use both authentication methods without losing my data

## Description

This user story handles the critical edge case where a user has both a standard (email/password) account and attempts to login via Microsoft Entra ID using the same email address. Rather than creating a duplicate account, the system prompts the user to unify/link their accounts.

The unification process requires the user to provide their standard account password to confirm ownership, then links the Microsoft Entra ID identity to the existing account. All subscription history, preferences, and data are preserved under the single unified account. After successful unification, the user can authenticate using either method (standard password or Microsoft SSO).

This feature is critical for enterprise adoption and ensures seamless user experience when transitioning between authentication methods.

## Acceptance Criteria

### Functional Criteria
- [ ] When SSO login email matches existing standard account, show unification prompt
- [ ] Prompt explains: "An account with this email already exists. Link your Microsoft account?"
- [ ] User must enter their standard account password to confirm unification
- [ ] Incorrect password rejects unification with error: "Password incorrect. Cannot link accounts."
- [ ] Successful unification:
  - Links Microsoft sub (user ID) to existing account
  - Sets is_sso_user flag to True
  - Preserves all subscription history and data
  - User logged in with JWT tokens
  - No duplicate account created
- [ ] Unification process completes within 500ms after password validation
- [ ] Future logins possible with either standard or SSO method
- [ ] Account unification logged for audit trail
- [ ] User sees confirmation: "Account linked successfully. You can now login with Microsoft or your password."

### Technical Criteria
- [ ] Custom logic in SSO authentication backend
- [ ] Microsoft user ID (sub claim) stored in user profile (microsoft_sub field)
- [ ] Verification step requiring standard password before unification
- [ ] Database transaction ensures atomicity
- [ ] Account unification event logged with timestamp, user ID, IP address
- [ ] Unit tests covering all scenarios (match, mismatch, failure cases)
- [ ] Integration tests with mock Microsoft OAuth flow
- [ ] API documentation updated

### UI/UX Criteria (if applicable)
- [ ] Unification prompt displayed immediately after SSO callback with email match
- [ ] Clear explanation of what unification means
- [ ] Password input field with eye toggle for visibility
- [ ] Error messages displayed clearly for incorrect password
- [ ] Success message and redirect to dashboard after unification
- [ ] Accessible form controls and inputs
- [ ] Responsive design on mobile/tablet/desktop

### Performance Criteria
- [ ] Unification process < 500ms after password validation
- [ ] Password verification < 100ms (using check_password)
- [ ] Database transaction commits successfully under load

## Technical Details

### Components Affected
- **Backend:** Django authentication backend, SSO middleware, User model, OAuth flow
- **Frontend:** SSO callback handler, account unification modal/component
- **Database:** User model with new microsoft_sub field
- **External:** Microsoft Entra ID OAuth provider

### API Changes
- **Modified Flow - SSO Callback Handling:**
  - `GET /auth/callback?code=...` (implicit SSO flow)
  - When email exists but microsoft_sub not set:
    - Return unification prompt (no automatic redirect)

- **New Endpoint for Unification:**
  - `POST /api/auth/unify-account/` - Link Microsoft account to existing standard account
    - Request Body:
      ```json
      {
        "password": "CurrentPassword123!",
        "microsoft_code": "oauth_code_from_sso"
      }
      ```
    - Response (200 OK):
      ```json
      {
        "message": "Account linked successfully",
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {
          "id": "uuid",
          "email": "user@example.com",
          "first_name": "John",
          "last_name": "Doe",
          "authentication_method": "Standard + Microsoft Entra ID",
          "is_sso_user": true
        }
      }
      ```
    - Response (400 Bad Request - incorrect password):
      ```json
      {
        "error": "invalid_password",
        "message": "Password incorrect. Cannot link accounts."
      }
      ```
    - Response (400 Bad Request - invalid microsoft code):
      ```json
      {
        "error": "invalid_oauth_code",
        "message": "Microsoft authentication failed. Please try again."
      }
      ```

### Database Changes
- **User Model Migration:**
  ```sql
  ALTER TABLE auth_user ADD COLUMN microsoft_sub VARCHAR(255) UNIQUE NULL;
  ALTER TABLE auth_user ADD COLUMN is_sso_user BOOLEAN DEFAULT FALSE;
  ALTER TABLE auth_user ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
  ALTER TABLE auth_user ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();
  ```
- **Audit Log Table:**
  ```sql
  CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES auth_user(id),
    event_type VARCHAR(50),
    event_details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```

### External Integrations
- **Microsoft Entra ID:** OAuth 2.0 flow, Microsoft Graph API (optional for user details)
- **MSAL (Microsoft Authentication Library):** For token exchange

## Implementation Notes

### Suggested Approach
1. Identify email match during Microsoft SSO callback
2. Check if user.microsoft_sub is already set (if yes, proceed to normal login)
3. If no microsoft_sub but same email exists, show unification prompt
4. Create unification endpoint accepting password + microsoft_code
5. Validate provided password against stored hash
6. Exchange microsoft_code for Microsoft tokens
7. Extract Microsoft sub from token claims
8. Update user record with microsoft_sub and is_sso_user=True
9. Log unification event for audit trail
10. Return JWT tokens and redirect to dashboard
11. Write comprehensive test coverage including edge cases
12. Document full flow in API and developer guides

### Technical Considerations
- **Security:** Never log passwords; validate password before linking
- **Account Takeover:** Ensure strong validation of Microsoft tokens
- **Data Integrity:** Use database transaction for atomicity
- **Concurrency:** Handle race conditions (user clicking SSO twice)
- **Token Management:** Revoke old tokens if user was already logged in
- **Audit Trail:** Log all unification attempts (success and failure) for security
- **Rollback:** Plan for transaction rollback if Microsoft token validation fails

### Known Challenges
- Handling duplicate account requests in race conditions
- Managing OAuth state and code expiration
- Ensuring atomicity of database updates
- Error handling for various Microsoft OAuth failures
- User communication clarity about unification process
- Performance under high concurrent unification requests

## Dependencies

### Depends On
- **US-1:** Standard User Registration (existing standard accounts)
- **US-3:** Standard User Login (password validation mechanism)
- **US-7:** Microsoft Entra ID SSO Login (SSO infrastructure)
- **Infrastructure:** Microsoft Entra ID tenant, OAuth configuration, PostgreSQL

### Blocks
- None directly, but enables complete SSO user journey

## Test Scenarios

### Happy Path
1. User has existing standard account with email user@example.com
2. User clicks "Sign in with Microsoft" button
3. Microsoft login flow completes
4. Microsoft returns email user@example.com
5. Backend detects email match but no microsoft_sub
6. Unification prompt displayed on frontend
7. User enters standard account password
8. Frontend sends POST /api/auth/unify-account/ with password and oauth_code
9. Backend validates password (matches hash)
10. Backend exchanges oauth_code for Microsoft tokens
11. Backend updates user: microsoft_sub=<ms_id>, is_sso_user=True
12. JWT tokens returned and stored
13. User redirected to dashboard
14. Account now accessible via both standard and SSO login

### Alternative Paths
1. SSO-only user attempting to register with standard email
   - Backend detects microsoft_sub already exists
   - Shows link to login instead of registration
   - Directs user to use Microsoft login

2. User clicks SSO, sees unification prompt, but has forgotten standard password
   - User can use password reset flow (US-5/US-6)
   - Then retry account unification

### Error Scenarios
1. User enters incorrect standard password
   - POST /api/auth/unify-account/ returns 400
   - Error message: "Password incorrect. Cannot link accounts."
   - Unification not performed, no account changes

2. Microsoft OAuth code invalid or expired
   - Backend returns 400
   - Error: "Microsoft authentication failed. Please try again."
   - User must restart SSO flow

3. User account already has microsoft_sub set (edge case)
   - SSO proceeds to normal login
   - No unification prompt shown

4. Network failure during unification
   - Database transaction rolls back
   - User receives error
   - Can safely retry after connection restored

5. Concurrent unification attempts (user clicks SSO twice rapidly)
   - First request wins, updates microsoft_sub
   - Second request sees microsoft_sub already set
   - Proceeds to normal SSO login

### Edge Cases
1. User cancels Microsoft SSO flow after email selection
   - No unification attempted
   - User returned to login page

2. Microsoft returns different email than expected
   - Unification prompt not shown
   - Backend logs discrepancy for investigation

3. Account unification takes >500ms (rare)
   - User experiences slight delay but operation completes
   - Success displayed

4. Database contains stale microsoft_sub data
   - Validation logic handles gracefully
   - Prevents authentication issues

## UI/UX Specifications

### User Flow - Account Unification
1. User on login page, clicks "Sign in with Microsoft"
2. Redirected to Microsoft login page
3. User enters Microsoft credentials
4. Microsoft redirects back to app with OAuth code
5. Backend detects email exists as standard account
6. Frontend receives unification prompt with:
   - "An account with this email already exists"
   - "Link your Microsoft account to this existing account?"
   - Password input field (to confirm account ownership)
   - "Cancel" and "Link Account" buttons
7. User enters standard account password
8. User clicks "Link Account" button
9. Backend validates password and Microsoft code
10. Success message: "Account linked successfully. You can now login with Microsoft or your password."
11. User redirected to dashboard
12. User logged in with JWT tokens

### Design Requirements
- Modal or dedicated page for unification prompt
- Clear explanation of what linking means
- Password input with eye toggle for visibility
- Error messages in red with clear action items
- Success message in green
- Keyboard accessible form controls
- Mobile responsive design

## Security Considerations

- **Password Validation:** Always require standard password before linking
- **OAuth Security:** Validate Microsoft OAuth code signature and expiration
- **Account Ownership:** Verify user controls the email being linked
- **Token Security:** Ensure tokens are valid and not modified
- **Audit Logging:** Log all unification attempts (success, failure, IP, timestamp)
- **Rate Limiting:** Limit unification attempts per user/IP
- **HTTPS Required:** All SSO callbacks over HTTPS only
- **CSRF Protection:** Django CSRF middleware active
- **XSS Prevention:** Sanitize all user input

## Performance Requirements

- **Unification Process:** < 500ms end-to-end
- **Password Validation:** < 100ms (bcrypt/Argon2 check)
- **OAuth Code Exchange:** < 200ms (Microsoft API call)
- **Database Write:** < 50ms (atomic transaction)
- **Concurrent Operations:** Support 100+ simultaneous unifications
- **Memory:** Minimal additional memory for unification logic

## Accessibility Requirements

- [ ] Unification prompt accessible without JavaScript
- [ ] Keyboard navigation: Tab through password field and buttons
- [ ] Screen reader compatibility: Explanation announced clearly
- [ ] ARIA labels for password input field
- [ ] Error messages associated with input via aria-describedby
- [ ] Color contrast meets WCAG standards
- [ ] Focus indicators visible on form inputs
- [ ] Form submission works without mouse device

## Definition of Done

- [ ] Code implemented and peer-reviewed
- [ ] Unit tests written (>80% coverage for all scenarios)
- [ ] Integration tests with mock Microsoft OAuth
- [ ] Manual testing with real Microsoft Entra ID tenant
- [ ] Acceptance criteria verified by PO
- [ ] API documentation updated (OpenAPI/Swagger)
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (< 500ms)
- [ ] Security review completed
- [ ] Audit logging verified working
- [ ] No critical or high-severity bugs
- [ ] Error handling tested comprehensively

## Tasks

Detailed development tasks are tracked in [tasks.md](./tasks.md)

### Task Summary
- **Total Tasks:** [Number]
- **Completed:** [Number]
- **In Progress:** [Number]
- **Blocked:** [Number]

## Notes

### Questions / Open Items
- [ ] Should we allow unlinking Microsoft account after unification?
- [ ] Should we implement "Try a different account" option in SSO flow?
- [ ] Should we send email notification when account is unified?
- [ ] What happens if Microsoft email changes after unification?

### Assumptions
- User model includes email field (unique constraint)
- is_sso_user and microsoft_sub fields can be added to User model
- Microsoft Entra ID tenant configured and working
- PostgreSQL with proper transaction support
- MSAL library available for token exchange

### Out of Scope
- Unlinking Microsoft from unified account (future feature)
- Multiple SSO providers (Google, GitHub) in MVP
- Automatic account merge for similar names
- Social account linking beyond Microsoft
- Multi-factor authentication setup during unification

## Related User Stories

- **US-1:** Standard User Registration (creates standard accounts)
- **US-3:** Standard User Login (password authentication)
- **US-5:** Password Reset Request (forgot password for unification)
- **US-6:** Password Reset Completion (reset before unification)
- **US-7:** Microsoft Entra ID SSO Login (triggers unification flow)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial user story generation |

---

**Generated by:** Functional Spec Planner
**Source Document:** docs/po_input/authentication.md
**GitHub Issue:** [Link to GitHub issue]
