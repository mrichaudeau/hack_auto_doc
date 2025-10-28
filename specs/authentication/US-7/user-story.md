# User Story: Microsoft Entra ID SSO Login

**Story ID:** US-7
**Feature:** Authentication & Authorization
**Status:** Draft
**Priority:** P1
**Effort Estimate:** 10 Story Points
**Assigned To:** [Developer Name]
**Sprint:** Sprint 2

## User Story Statement

**As an** enterprise user
**I want to** log in using my Microsoft Entra ID account
**So that** I can use single sign-on without creating a separate password

## Description

This user story implements Single Sign-On (SSO) integration with Microsoft Entra ID (formerly Azure AD), enabling enterprise users to authenticate using their organizational credentials. The OAuth 2.0 flow redirects users to Microsoft's login page, where they authenticate with their corporate credentials. Upon successful authentication, the system receives user profile claims (email, given_name, family_name, sub/user ID) and either creates a new user account or logs in an existing user. If the email matches an existing standard account (from US-1), the system triggers account unification (US-11) flow. JWT tokens are issued, and users are redirected to the dashboard.

This feature is critical for enterprise adoption and provides a seamless, secure authentication experience for organizational users.

## Acceptance Criteria

### Functional Criteria
- [ ] "Sign in with Microsoft" button displayed prominently on login page
- [ ] Clicking button redirects to Microsoft login page
- [ ] OAuth 2.0 flow handles authentication with Microsoft
- [ ] User profile created from Microsoft claims: email, given_name, family_name, sub (user ID)
- [ ] If email matches existing standard account, trigger account unification flow (see US-11)
- [ ] JWT tokens issued after successful SSO authentication
- [ ] User redirected to /dashboard after successful login
- [ ] Failed SSO authentication displays error: "Microsoft authentication failed. Please try again or contact support."
- [ ] SSO login endpoint responds within 500ms (P95) after Microsoft callback

### Technical Criteria
- [ ] Backend: Use django-azure-auth or similar Microsoft authentication library
- [ ] Frontend: Use MSAL-React for Microsoft authentication flow
- [ ] Configure Azure AD app registration with redirect URIs
- [ ] Map Microsoft claims to User model fields
- [ ] Store Microsoft user ID (sub) in user profile for future authentication
- [ ] Set is_sso_user flag in user profile
- [ ] Unit tests written (>80% coverage for SSO logic)
- [ ] Integration tests covering SSO flow and error scenarios

### UI/UX Criteria
- [ ] "Sign in with Microsoft" button is accessible and visible
- [ ] Button includes Microsoft branding (standard Microsoft logo)
- [ ] Login flow is seamless with minimal redirects
- [ ] Error messages are clear and actionable
- [ ] Account unification prompt (if applicable) is clear
- [ ] Accessibility standards met (WCAG 2.1 Level AA)

### Performance Criteria
- [ ] SSO callback endpoint responds within 500ms (P95)
- [ ] User account creation/lookup < 100ms
- [ ] JWT token generation < 50ms
- [ ] Total flow (redirect to dashboard) < 5 seconds

### Security Criteria
- [ ] OAuth 2.0 state parameter prevents CSRF attacks
- [ ] Redirect URIs validated against whitelist
- [ ] Microsoft user ID (sub) stored securely
- [ ] SSO flow uses HTTPS only
- [ ] No sensitive data logged
- [ ] Rate limiting on callback endpoint

## Technical Details

### Components Affected
**Backend:**
- OAuth 2.0 callback view
- SSO user authentication backend
- User model (microsoft_sub field)
- Account unification logic (part of US-11)
- JWT token generation
- MSAL configuration

**Frontend:**
- Login page with "Sign in with Microsoft" button
- MSAL-React integration
- Account unification prompt component (if needed)
- Session management after SSO

**Database:**
- User model modifications (microsoft_sub, is_sso_user fields)
- SSO audit logging table

### API Changes

**New Endpoint (Backend):**
- `GET /api/auth/microsoft/callback/`
  - **Query Parameters:**
    - `code` - Authorization code from Microsoft
    - `state` - CSRF protection state parameter
    - `session_state` - Microsoft session state
  - **Response (302 Redirect) - Success:**
    - Redirects to `/dashboard` with tokens in session/header
    - Or returns tokens in response body for frontend to store
  - **Response (302 Redirect) - Unification Required:**
    - Redirects to `/auth/unify-account?email=...` (US-11 flow)
  - **Response (400 Bad Request) - Invalid State:**
    ```json
    {
      "error": "csrf_validation_failed",
      "message": "Invalid authentication request. Please try again."
    }
    ```
  - **Response (500 Internal Server Error) - Microsoft Error:**
    ```json
    {
      "error": "microsoft_auth_failed",
      "message": "Microsoft authentication failed. Please try again or contact support."
    }
    ```

**Frontend Integration Points:**
- Login button component calls MSAL: `useMsal()` hook
- Initiates login flow: `instance.loginPopup()` or `instance.loginRedirect()`
- Handles token acquisition on redirect
- Stores tokens in secure location

### Database Changes

**Modified table: User**
- `microsoft_sub` (varchar 255, nullable, unique)
  - Stores Microsoft's unique user identifier
  - Allows future SSO login identification
- `is_sso_user` (boolean, default False)
  - Flags account as SSO-capable
  - Affects password change availability (hidden for SSO-only users)
- `sso_provider` (varchar 50, nullable, e.g., "microsoft")
  - For future support of multiple SSO providers

**New table: SSOAuditLog**
- `id` (UUID primary key)
- `user_id` (foreign key to User, nullable for pre-user events)
- `provider` (varchar 50, e.g., "microsoft")
- `provider_user_id` (varchar 255, e.g., Microsoft sub)
- `email` (varchar 255)
- `action` (varchar 100, e.g., "login_success", "new_account_created", "account_unified")
- `details` (JSON, for additional context)
- `ip_address` (inet/varchar 45)
- `user_agent` (text)
- `created_at` (timestamp)

**Indexes:**
- Index on `microsoft_sub` (for SSO lookup)
- Index on SSOAuditLog `(user_id, created_at)`
- Index on SSOAuditLog `(provider, provider_user_id)`

### External Integrations
- **Microsoft Entra ID:** Azure AD tenant with registered app
- **MSAL-React:** Frontend SDK for Microsoft authentication
- **django-azure-auth or msal:** Backend library for token exchange
- **Azure App Registration:** Client ID, Client Secret, Redirect URI

## Implementation Notes

### Suggested Approach
1. **Backend Implementation:**
   - Create OAuth 2.0 callback view:
     - Extract authorization code from request
     - Validate state parameter (CSRF protection)
     - Exchange code for access token via Microsoft Graph
     - Retrieve user claims from Microsoft Graph (email, given_name, family_name, sub)
     - Check if email exists in system:
       - **New user:** Create account with microsoft_sub, is_sso_user=True, is_active=True
       - **Existing standard user:** Redirect to unification flow (US-11)
       - **Existing SSO user with same email:** Normal login
     - Generate JWT tokens (access + refresh)
     - Return tokens and redirect to dashboard
   - Implement SSO authentication backend extending Django's ModelBackend
   - Use microsoft_sub for user lookup instead of email
   - Log all SSO events for audit trail

2. **Frontend Implementation:**
   - Install MSAL-React: `npm install @azure/msal-react @azure/msal-browser`
   - Configure MSAL with Azure AD credentials
   - Add "Sign in with Microsoft" button on login page
   - Implement login flow:
     - User clicks button
     - MSAL redirects to Microsoft
     - User authenticates with corporate credentials
     - Microsoft redirects back to app
     - Frontend receives tokens from redirect
     - Frontend stores tokens securely
     - Redirect to dashboard or unification flow

3. **Configuration:**
   - Azure AD app registration setup:
     - Create or use existing app registration
     - Set redirect URI: `https://app.example.com/auth/callback`
     - Generate client secret
     - Configure API permissions (User.Read, etc.)
   - Django settings:
     - `AZURE_CLIENT_ID` - From app registration
     - `AZURE_CLIENT_SECRET` - From app registration
     - `AZURE_TENANT_ID` - From Azure AD tenant
     - `SOCIAL_AUTH_AZURE_AD_OAUTH2_KEY` - Client ID
     - `SOCIAL_AUTH_AZURE_AD_OAUTH2_SECRET` - Client secret

### Technical Considerations
- **OAuth 2.0 State Parameter:** Unique per request, prevents CSRF attacks
- **Scope:** Typically "openid profile email"
- **Token Validation:** Verify Microsoft's signature using public keys from Microsoft Graph
- **User Creation:** Auto-create account from first SSO login (no explicit registration)
- **Email Normalization:** Convert to lowercase for comparison
- **Account Unification:** If email exists as standard account, require password confirmation (US-11)
- **Session Expiry:** No specific timeout (managed by JWT tokens)
- **Clock Skew:** Handle time differences between servers and Microsoft Graph
- **Error Handling:** Redirect to login page on failure (not error page with details)
- **Existing SSO Account:** If microsoft_sub already exists, use normal login flow

### Known Challenges
- Azure AD tenant setup and app registration complexity
- MSAL-React integration with backend token management
- Account unification flow complexity (requiring user confirmation)
- Testing SSO in dev environment (requires real Azure AD or mock)
- Multiple SSO providers (future extensibility)
- Handling corporate proxy/firewall issues

## Dependencies

### Depends On
- **Infrastructure:** Microsoft Entra ID (Azure AD) tenant
- **Infrastructure:** Azure AD app registration configured
- **Library:** MSAL-React (frontend)
- **Library:** django-azure-auth or msal (backend)
- **US-11:** Account Unification (for handling email conflicts)

### Blocks
- Enterprise customer adoption
- Feature flag for controlled rollout

## Test Scenarios

### Happy Path - New User
1. User navigates to login page
2. Sees "Sign in with Microsoft" button
3. Clicks button
4. MSAL redirects to Microsoft login page
5. User enters corporate credentials (email@company.com)
6. Microsoft authenticates user
7. Microsoft redirects back to app with authorization code
8. Backend callback endpoint:
   - Validates state parameter (CSRF check)
   - Exchanges code for access token
   - Retrieves user claims:
     - email: user@company.com
     - given_name: John
     - family_name: Doe
     - sub: microsoft-user-id-12345
   - Checks if email exists: NO
   - Creates new User account:
     - email: user@company.com
     - first_name: John
     - last_name: Doe
     - microsoft_sub: microsoft-user-id-12345
     - is_sso_user: True
     - is_active: True
     - is_email_verified: True (SSO emails are verified)
   - Generates JWT tokens
9. Logs SSO event: user_id=new_user_id, action="new_account_created"
10. Redirects to /dashboard
11. Frontend receives tokens
12. Frontend stores tokens
13. Dashboard loads with user's data
14. Success!

### Happy Path - Existing SSO User
1. Existing user with microsoft_sub already set
2. Clicks "Sign in with Microsoft"
3. Authenticates with Microsoft
4. Backend finds user by microsoft_sub
5. Generates JWT tokens
6. Logs SSO event: action="login_success"
7. Redirects to /dashboard
8. User continues

### Alternative Path - Account Unification Required
1. User previously registered with standard auth (US-1)
   - Email: user@company.com
   - Password: [hashed]
   - is_sso_user: False
   - microsoft_sub: NULL
2. User clicks "Sign in with Microsoft"
3. Authenticates with Microsoft
4. Backend receives claims:
   - email: user@company.com (MATCHES existing account)
   - sub: microsoft-id-67890
5. Backend detects conflict:
   - Email exists
   - But microsoft_sub is different (no existing microsoft_sub)
   - User is not yet unified
6. Redirects to unification flow (US-11)
   - Shows prompt: "An account with this email already exists. Link your Microsoft account?"
   - User must enter standard account password to confirm ownership
   - If password correct: Accounts unified (microsoft_sub linked, is_sso_user=True)
   - JWT tokens issued
   - Logs: action="account_unified"

### Error Scenarios
1. **State Parameter Mismatch (CSRF Attack):**
   - Attacker tries to hijack login flow
   - State parameter doesn't match stored session value
   - Backend rejects request
   - Returns 400 Bad Request
   - Message: "Invalid authentication request. Please try again."

2. **Microsoft Authentication Failed:**
   - User cancels Microsoft login
   - Network error occurs
   - Microsoft returns error
   - Backend handles gracefully
   - Redirects to login page with error
   - Message: "Microsoft authentication failed. Please try again or contact support."

3. **Invalid Authorization Code:**
   - Authorization code expired (>10 minutes)
   - Authorization code already used
   - Code doesn't match client ID
   - Backend cannot exchange for token
   - Returns 500 error
   - Message: "Microsoft authentication failed. Please try again or contact support."

4. **Network Error:**
   - Backend cannot reach Microsoft Graph API
   - Network timeout
   - Returns 500 error
   - User sees: "Microsoft authentication failed. Please try again."

5. **Email Claim Missing:**
   - Microsoft returns claims without email
   - Backend cannot create user (email required)
   - Returns 500 error
   - Logs error for debugging

6. **Multiple Accounts with Same Email (shouldn't happen but edge case):**
   - System detects multiple User records with same email
   - Backend fails gracefully
   - Returns error
   - Requires admin intervention to resolve

### Edge Cases
1. **First Name or Last Name Missing:**
   - Microsoft claims don't include given_name or family_name
   - Backend creates user with empty strings or defaults
   - Should handle gracefully (names not required)

2. **Concurrent SSO Login Attempts:**
   - User initiates SSO login twice
   - Both reach callback endpoint simultaneously
   - Database transaction ensures user created once
   - Both requests succeed (or one fails appropriately)

3. **SSO User Tries Standard Login:**
   - User has SSO account (microsoft_sub set)
   - User tries to log in with standard email/password
   - Standard auth backend finds user
   - User provides password
   - If user also has standard password: Login succeeds (both methods work)
   - If user has no standard password: Login fails (expected)
   - Or: Could show message suggesting SSO login instead

4. **User Logs Out, Then SSO Again:**
   - User logs out (tokens revoked/cleared)
   - User clicks "Sign in with Microsoft" again
   - Microsoft may show cached login (no re-auth needed)
   - User quickly re-authenticated
   - New tokens issued
   - Success (expected behavior)

5. **Email Changed in Microsoft:**
   - User's email is user@company.com in Microsoft
   - User logs in via SSO (microsoft_sub linked to that email)
   - Admin changes email in Microsoft to newuser@company.com
   - User clicks "Sign in with Microsoft" again
   - Microsoft returns new email in claims
   - Backend finds user by microsoft_sub (not email)
   - Logs in successfully with unchanged User record
   - **Issue:** Email in database doesn't match Microsoft
   - **Mitigation:** Periodic sync or verification on each login

6. **Microsoft Entra ID Custom Claims:**
   - Organization has custom claims in Azure AD
   - Claims not in standard profile
   - Backend ignores non-standard claims
   - Uses only: email, given_name, family_name, sub
   - Should work correctly

## UI/UX Specifications

### Login Page Design
The login page should display both authentication methods:

**Section 1: Standard Authentication**
- Email input
- Password input
- "Log In" button
- Links: "Forgot Password?" | "Sign Up"

**Section 2: SSO Authentication**
- Divider: "Or"
- "Sign in with Microsoft" button
  - Uses official Microsoft branding
  - Button color: Azure blue (#0078D4)
  - Button includes Microsoft logo
  - Text: "Sign in with Microsoft Entra ID" or "Sign in with Microsoft"
  - Accessible, keyboard-navigable

### Authentication Flow Visualization
1. User clicks "Sign in with Microsoft"
2. Browser redirects to Microsoft login
3. Loading indicator shown (redirect in progress)
4. (Microsoft login page - external UI)
5. After authentication:
   - New account: Redirect to dashboard
   - Existing standard account: Redirect to unification prompt
   - Existing SSO account: Redirect to dashboard

### Account Unification Prompt (if applicable)
- Heading: "Link Your Microsoft Account"
- Message: "An account with this email already exists. To link your Microsoft account, please enter your password."
- Password input field
- Buttons: "Link Account" | "Cancel"
- On success: "Account linked! You can now use either sign-in method."
- On failure: "Password incorrect. Please try again."

### Design Assets
- Link to login page design: [login-page-with-sso]
- Link to Microsoft button design: [microsoft-sso-button]
- Link to unification prompt design: [account-unification-prompt]

## Security Considerations

- **Authentication:** OAuth 2.0 protocol with authorization code flow
- **Authorization:** User verified by Microsoft Entra ID
- **CSRF Protection:** State parameter prevents cross-site request forgery
- **Data Validation:**
  - State parameter validation
  - Authorization code validation
  - Redirect URI validation against whitelist
- **Encryption:** All communication via HTTPS/TLS
- **Sensitive Data:**
  - Client Secret stored in environment variable (not code)
  - Access tokens not logged
  - Microsoft user ID (sub) stored securely
- **Audit Logging:**
  - All SSO login attempts logged
  - New account creation logged
  - Account unification logged
  - Failed attempts logged
  - Include timestamp, IP address, user agent
- **Rate Limiting:**
  - Callback endpoint rate limited (prevent replay attacks)
  - Per IP: 10 attempts per minute
- **Token Storage:**
  - Frontend stores tokens securely (not localStorage)
  - Backend issues tokens via secure channel

## Performance Requirements

- **SSO Callback Response Time:** < 500ms (P95)
- **User Lookup/Creation:** < 100ms
- **Token Generation:** < 50ms
- **Microsoft Graph API Call:** Depends on Microsoft (typically 200-500ms)
- **Total Flow (button click to dashboard):** < 5 seconds
- **Throughput:** Support 50+ concurrent SSO logins
- **Concurrent Users:** System designed for 1000 concurrent

## Accessibility Requirements

- [ ] "Sign in with Microsoft" button keyboard accessible
- [ ] Button has clear focus indicator
- [ ] Button has descriptive ARIA label
- [ ] Logo image has alt text
- [ ] Error messages announced to screen readers
- [ ] Unification prompt accessible (if shown)
- [ ] Color contrast meets WCAG standards
- [ ] Works on all devices and screen sizes

## Definition of Done

- [ ] Azure AD app registration created/configured
- [ ] Redirect URI configured in Azure AD
- [ ] Backend OAuth 2.0 callback view implemented
- [ ] SSO authentication backend implemented
- [ ] Frontend MSAL-React integration completed
- [ ] "Sign in with Microsoft" button added to login page
- [ ] Account unification logic implemented (links to US-11)
- [ ] Unit tests written (>80% coverage)
  - OAuth state parameter validation
  - User creation from Microsoft claims
  - Email conflict detection
  - Token generation
  - Error handling
- [ ] Integration tests written
  - Full SSO login flow (new user)
  - Full SSO login flow (existing SSO user)
  - Email conflict detected (unification flow)
  - State parameter CSRF protection
  - Authorization code exchange
- [ ] Manual testing completed
  - Test new user SSO login
  - Test existing user SSO login
  - Test email conflict (with unification)
  - Verify user created with correct fields
  - Verify microsoft_sub stored correctly
  - Verify JWT tokens issued
  - Verify redirect to dashboard
  - Test error scenarios
- [ ] Testing with real Azure AD tenant (or mock)
- [ ] Frontend MSAL-React testing
- [ ] Acceptance criteria verified by PO
- [ ] Documentation updated
  - API endpoint documentation
  - Azure AD setup guide
  - MSAL-React integration guide
  - Account unification flow documentation
  - Troubleshooting guide
- [ ] Code merged to main branch
- [ ] Deployed to staging environment
- [ ] Performance benchmarks met (<500ms P95)
- [ ] Security audit completed
  - State parameter validation verified
  - Redirect URI whitelist verified
  - Client Secret securely stored
  - HTTPS enforced
  - No sensitive data in logs
- [ ] Feature flag created for controlled rollout
- [ ] No critical or high-severity bugs

## Notes

### Questions / Open Items
- [ ] What Azure AD tenant will be used for production? (Required for setup)
- [ ] Should we support guest accounts in Azure AD? (Out of scope for MVP)
- [ ] Should email be editable after SSO login? (Currently not, linked to microsoft_sub)
- [ ] Should we sync email changes from Microsoft? (Future enhancement)
- [ ] Should we support multiple SSO providers (Google, GitHub)? (Out of scope for MVP)

### Assumptions
- Azure AD tenant is available and app registration configured
- Microsoft Graph API is accessible
- Network connectivity to Microsoft services available
- Enterprise users have valid Microsoft Entra ID accounts
- Email is unique identifier (no duplicate emails across standard and SSO)

### Out of Scope
- Multi-factor authentication for SSO (handled by Microsoft)
- Device compliance checks
- Conditional access policies
- Custom claims beyond standard profile
- Other SSO providers (Google, GitHub, SAML)
- Guest account support
- Email sync with Microsoft

## Related User Stories

- **US-1:** Standard User Registration (alternative auth method)
- **US-3:** Standard User Login (alternative auth method)
- **US-7:** Microsoft Entra ID SSO Login (THIS STORY)
- **US-11:** Account Unification (triggered if email matches existing standard account)
- **US-8:** User Profile Viewing (user data from Microsoft or standard auth)

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-28 | Claude Code | Initial version extracted from PO authentication.md |

---

**Generated by:** Functional Spec Planner
**Source Document:** C:\Users\mrichaudeau_silamir\BU_IA\hackathon_base_de_connaissance\docs\po_input\authentication.md
**GitHub Issue:** [To be created]
