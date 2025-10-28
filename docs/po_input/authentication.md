# User Authentication and Authorization

## Overview / Context

This is the authentication and authorization module (Bloc 1) for the AI-Powered Technology Watch Platform. It serves as the entry point to the application, ensuring that only legitimate users can access their data and that user identity is established uniquely and securely.

**Business Value:**
- Secure access control for all platform features
- Enterprise-ready with SSO integration for corporate users
- Seamless user experience with unified login flow
- Compliance with modern security standards

**Target Users:**
- Individual professionals registering with email/password
- Enterprise users accessing via Microsoft Entra ID (SSO)
- Platform administrators managing user accounts

## Functional Requirements

The authentication system must provide:

### 1. Unified Login Flow
The system offers a single access point with two distinct authentication methods:

1. **Standard Authentication:** Email/Password-based with complete lifecycle:
   - User registration (Sign Up)
   - Email verification flow
   - Secure login
   - Password reset capability

2. **Enterprise Authentication (SSO):** Via "Sign in with Microsoft Entra ID" button:
   - OAuth 2.0 protocol for Single Sign-On
   - Automatic profile creation from enterprise directory
   - Seamless integration with existing corporate credentials

### 2. Identity Unification
Critical capability for users with multiple authentication methods:

- **Account Merging Strategy:** When a user attempts SSO login with an email that already exists as a standard account:
  - System does NOT create a duplicate account
  - Proposes to link and unify both authentication methods
  - Requires security validation (standard password submission)
  - Preserves all subscription history and data under single user ID

### 3. User Profile Management
Dedicated "My Account" page allowing users to:
- View and update basic information (first name, last name, email)
- Change password (for standard authentication users)
- Manage active sessions and logout from all devices

### 4. API Security
All authenticated API endpoints must:
- Issue JWT tokens (Access + Refresh) upon successful login
- Validate JWT tokens on every authenticated request
- Support token refresh mechanism
- Implement secure token revocation on logout

## User Stories

### US-1: Standard User Registration
**As a** new user
**I want to** register with my email and password
**So that** I can create an account and access the platform

**Acceptance Criteria:**
- [ ] Registration form accepts email, password, and password confirmation
- [ ] Email validation ensures valid format (RFC 5322 compliant)
- [ ] Password requirements enforced:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character recommended
- [ ] Password is hashed using Argon2 before storage
- [ ] User account created but marked as inactive until email verification
- [ ] Verification email sent within 30 seconds of registration
- [ ] Duplicate email addresses rejected with clear error message: "An account with this email already exists"
- [ ] Form displays real-time validation feedback for each field
- [ ] Registration endpoint responds within 300ms (P95)

**Priority:** P0

**Technical Notes:**
- Backend: Django with django-allauth
- Use Django's built-in User model or custom User model extending AbstractUser
- Configure Argon2 as PASSWORD_HASHERS in Django settings
- SMTP configuration required for email sending
- Rate limiting: Maximum 5 registration attempts per IP per hour

---

### US-2: Email Verification
**As a** newly registered user
**I want to** verify my email address via a secure link
**So that** I can activate my account and access the platform

**Acceptance Criteria:**
- [ ] Verification email contains unique, time-limited token (24-hour expiry)
- [ ] Clicking verification link activates the account
- [ ] User redirected to login page with success message after verification
- [ ] Expired tokens display clear error: "Verification link has expired. Please request a new one."
- [ ] User can request new verification email (maximum 3 times per day)
- [ ] Verification token is single-use only
- [ ] Already verified accounts cannot be re-verified

**Priority:** P0

**Technical Notes:**
- Use django-allauth email verification flow
- Store verification tokens in database with expiry timestamp
- Implement resend verification endpoint: POST /api/auth/resend-verification/

---

### US-3: Standard User Login
**As a** registered user with verified email
**I want to** log in with my email and password
**So that** I can access my personalized dashboard

**Acceptance Criteria:**
- [ ] Login form accepts email and password
- [ ] Successful login returns JWT access token (15-minute expiry) and refresh token (7-day expiry)
- [ ] Response includes user profile data: id, email, first_name, last_name, is_sso_user
- [ ] User redirected to /dashboard after successful login
- [ ] Invalid credentials return 401 with message: "Invalid email or password"
- [ ] Unverified accounts return 403 with message: "Please verify your email before logging in"
- [ ] Rate limiting: Maximum 5 login attempts per IP per 5 minutes
- [ ] Failed login attempts logged for security monitoring
- [ ] Login endpoint responds within 300ms (P95)

**Priority:** P0

**Technical Notes:**
- Use djangorestframework-simplejwt for token generation
- Configure token expiry in settings: ACCESS_TOKEN_LIFETIME, REFRESH_TOKEN_LIFETIME
- Implement login endpoint: POST /api/auth/login/
- Return tokens in response body (not cookies for SPA architecture)

---

### US-4: JWT Token Refresh
**As a** logged-in user with expired access token
**I want to** automatically refresh my access token using my refresh token
**So that** I can continue using the platform without re-logging in

**Acceptance Criteria:**
- [ ] Refresh endpoint accepts valid refresh token
- [ ] New access token issued with fresh 15-minute expiry
- [ ] Original refresh token remains valid (until its 7-day expiry)
- [ ] Invalid or expired refresh token returns 401 with message: "Refresh token is invalid or expired"
- [ ] Refresh endpoint responds within 100ms (P95)
- [ ] Frontend automatically attempts token refresh on 401 responses

**Priority:** P0

**Technical Notes:**
- Implement refresh endpoint: POST /api/auth/token/refresh/
- Use Simple JWT's TokenRefreshView
- Frontend should store tokens in memory or secure storage (not localStorage for XSS protection)

---

### US-5: Password Reset Request
**As a** user who forgot my password
**I want to** request a password reset via my email
**So that** I can regain access to my account

**Acceptance Criteria:**
- [ ] Password reset form accepts email address
- [ ] System sends reset email if account exists (no user enumeration)
- [ ] Reset email contains secure, time-limited link (60-minute expiry)
- [ ] Reset link includes unique token
- [ ] Success message displayed regardless of email existence: "If an account exists, you will receive a reset email"
- [ ] Rate limiting: Maximum 3 reset requests per email per hour
- [ ] Reset email sent within 60 seconds of request

**Priority:** P1

**Technical Notes:**
- Use django-allauth password reset flow
- Implement endpoint: POST /api/auth/password-reset/
- Store reset tokens with 60-minute expiry
- Email template should be branded and professional

---

### US-6: Password Reset Completion
**As a** user with a valid reset link
**I want to** set a new password
**So that** I can log in with my new credentials

**Acceptance Criteria:**
- [ ] Reset form accepts new password and confirmation
- [ ] Password meets all strength requirements (same as registration)
- [ ] Token validated before allowing password change
- [ ] Expired tokens return clear error: "Reset link has expired. Please request a new one."
- [ ] Reset token is single-use only (invalidated after successful reset)
- [ ] New password hashed with Argon2
- [ ] All existing sessions/tokens invalidated after password change
- [ ] User redirected to login with success message
- [ ] Reset endpoint responds within 300ms (P95)

**Priority:** P1

**Technical Notes:**
- Implement endpoint: POST /api/auth/password-reset/confirm/
- Revoke all JWT refresh tokens on password change
- Log password change event for security audit

---

### US-7: Microsoft Entra ID SSO Login
**As an** enterprise user
**I want to** log in using my Microsoft Entra ID account
**So that** I can use single sign-on without creating a separate password

**Acceptance Criteria:**
- [ ] "Sign in with Microsoft" button displayed prominently on login page
- [ ] Clicking button redirects to Microsoft login page
- [ ] OAuth 2.0 flow handles authentication with Microsoft
- [ ] User profile created from Microsoft claims: email, given_name, family_name, sub (user ID)
- [ ] If email matches existing standard account, trigger account unification flow (see US-9)
- [ ] JWT tokens issued after successful SSO authentication
- [ ] User redirected to /dashboard after successful login
- [ ] Failed SSO authentication displays error: "Microsoft authentication failed. Please try again or contact support."
- [ ] SSO login endpoint responds within 500ms (P95) after Microsoft callback

**Priority:** P1

**Technical Notes:**
- Backend: Use django-azure-auth or similar Microsoft authentication library
- Frontend: Use MSAL-React for Microsoft authentication flow
- Configure Azure AD app registration with redirect URIs
- Map Microsoft claims to User model fields
- Store Microsoft user ID (sub) in user profile for future authentication
- Set is_sso_user flag in user profile

---

### US-8: User Profile Viewing
**As a** logged-in user
**I want to** view my profile information
**So that** I can verify my account details

**Acceptance Criteria:**
- [ ] Profile page displays: email, first name, last name
- [ ] Profile page shows authentication method: "Standard" or "Microsoft Entra ID"
- [ ] Profile page shows account creation date
- [ ] Endpoint requires valid JWT token
- [ ] Unauthorized access returns 401
- [ ] Profile endpoint responds within 100ms (P95)

**Priority:** P1

**Technical Notes:**
- Implement endpoint: GET /api/users/me/
- Return user profile data from authenticated user in JWT token
- Do not expose sensitive data (password hash, internal IDs)

---

### US-9: User Profile Update
**As a** logged-in user
**I want to** update my personal information (first name, last name)
**So that** I can keep my profile current

**Acceptance Criteria:**
- [ ] Update form allows editing: first_name, last_name
- [ ] Email address NOT editable (requires separate email change flow)
- [ ] Validation ensures names are not empty if provided
- [ ] Successful update returns 200 with updated profile data
- [ ] Changes immediately reflected in JWT claims on next token refresh
- [ ] Update endpoint requires valid JWT token
- [ ] Update endpoint responds within 200ms (P95)

**Priority:** P2

**Technical Notes:**
- Implement endpoint: PATCH /api/users/me/
- Validate input data
- Do not allow updating email, password, or is_staff fields via this endpoint

---

### US-10: Password Change (Standard Users)
**As a** standard authentication user
**I want to** change my password from my profile page
**So that** I can maintain account security

**Acceptance Criteria:**
- [ ] Password change form requires: current_password, new_password, new_password_confirm
- [ ] Current password validated before allowing change
- [ ] New password meets all strength requirements
- [ ] Incorrect current password returns 400: "Current password is incorrect"
- [ ] Successful change returns 200: "Password changed successfully"
- [ ] All existing refresh tokens invalidated after password change
- [ ] User remains logged in with current session
- [ ] Change password option hidden for SSO-only users
- [ ] Password change endpoint responds within 300ms (P95)

**Priority:** P2

**Technical Notes:**
- Implement endpoint: POST /api/users/me/change-password/
- Validate current password using check_password()
- Hash new password with Argon2
- Revoke all refresh tokens except current session
- Log password change event

---

### US-11: Account Unification (SSO + Standard)
**As a** user with an existing standard account
**I want to** link my Microsoft Entra ID to my existing account when I attempt SSO login
**So that** I can use both authentication methods without losing my data

**Acceptance Criteria:**
- [ ] When SSO login email matches existing standard account, show unification prompt
- [ ] Prompt explains: "An account with this email already exists. Link your Microsoft account?"
- [ ] User must enter their standard account password to confirm unification
- [ ] Incorrect password rejects unification with error: "Password incorrect. Cannot link accounts."
- [ ] Successful unification:
  - Links Microsoft sub (user ID) to existing account
  - Sets is_sso_user flag to True
  - Preserves all subscription history and data
  - User logged in with JWT tokens
- [ ] No duplicate account created
- [ ] Unification process completes within 500ms after password validation
- [ ] Future logins possible with either standard or SSO method

**Priority:** P2

**Technical Notes:**
- Custom logic in SSO authentication backend
- Store Microsoft user ID in user profile (add microsoft_sub field)
- Implement verification step requiring standard password
- Log account unification event for audit
- Handle edge case: SSO user trying to register with standard method (show link to login)

---

### US-12: Logout from Current Session
**As a** logged-in user
**I want to** log out from my current session
**So that** I can securely end my session on a shared or public device

**Acceptance Criteria:**
- [ ] Logout button available in navigation/profile menu
- [ ] Clicking logout invalidates current refresh token
- [ ] Access token remains valid until expiry (15 minutes max) but frontend discards it
- [ ] User redirected to login page after logout
- [ ] Logout confirmation message displayed: "You have been logged out successfully"
- [ ] Logout endpoint responds within 100ms (P95)

**Priority:** P2

**Technical Notes:**
- Implement endpoint: POST /api/auth/logout/
- Blacklist current refresh token (use Simple JWT token blacklist)
- Frontend clears tokens from memory/storage
- Redirect to /login

---

### US-13: Logout from All Devices
**As a** security-conscious user
**I want to** log out from all my active sessions across all devices
**So that** I can revoke access if I suspect unauthorized use

**Acceptance Criteria:**
- [ ] "Logout from all devices" button in profile security section
- [ ] Confirmation modal: "This will log you out from all devices. Continue?"
- [ ] All refresh tokens for the user invalidated
- [ ] Current session also logged out
- [ ] User redirected to login page
- [ ] Success message: "You have been logged out from all devices"
- [ ] Endpoint responds within 200ms (P95)

**Priority:** P3

**Technical Notes:**
- Implement endpoint: POST /api/users/me/logout-all/
- Revoke all refresh tokens associated with user
- Use Simple JWT token blacklist or custom token revocation logic
- Consider adding "last_token_revoke_at" timestamp to User model for efficient validation

---

## Non-Functional Requirements

### Performance
- **Login endpoint response time:** < 300ms (P95)
- **Token refresh response time:** < 100ms (P95)
- **Profile read endpoint:** < 100ms (P95)
- **SSO authentication flow:** < 500ms (P95) after Microsoft callback
- **System must support:** 1000 concurrent authentication requests

### Security
- **Password hashing:** Argon2 algorithm (OWASP recommended)
- **JWT signing:** HS256 algorithm with secure secret key (min 256 bits)
- **HTTPS required:** All authentication endpoints must use TLS 1.2+
- **Rate limiting:**
  - Login: 5 attempts per IP per 5 minutes
  - Registration: 5 attempts per IP per hour
  - Password reset: 3 requests per email per hour
  - Token refresh: 10 requests per refresh token per minute
- **Token expiry:**
  - Access token: 15 minutes
  - Refresh token: 7 days
  - Email verification token: 24 hours
  - Password reset token: 60 minutes
- **Session security:**
  - No sensitive data in JWT payload
  - Tokens transmitted in Authorization header (not URL parameters)
  - Secure token storage on frontend (in-memory or secure storage)
- **Audit logging:**
  - Log all authentication events (login, logout, password change, account unification)
  - Log failed authentication attempts for security monitoring
  - Include timestamp, user ID, IP address, user agent

### Scalability
- **Stateless authentication:** JWT tokens enable horizontal scaling
- **Redis caching:** Use Redis for token blacklist and rate limiting
- **Session data:** No server-side session storage required (JWT is self-contained)
- **Database connection pooling:** Configure for high concurrency

### Availability
- **Authentication service uptime:** 99.9% (excluding planned maintenance)
- **Email delivery:** 99% success rate for verification/reset emails
- **Graceful degradation:** If email service down, queue emails for retry

### Usability
- **Clear error messages:** User-friendly, actionable feedback
- **No user enumeration:** Don't reveal whether email exists in system
- **Responsive design:** Works on mobile, tablet, desktop
- **Accessibility:** WCAG 2.1 Level AA compliance for all forms
- **Multi-language support:** Ready for internationalization (i18n)

## Technical Constraints

### Technology Stack
- **Backend Framework:** Django 4.2+ with Django REST Framework 3.14+
- **Authentication Libraries:**
  - `django-allauth` 0.54+ for standard authentication
  - `django-azure-auth` or `msal` for Microsoft Entra ID SSO
  - `djangorestframework-simplejwt` 5.2+ for JWT tokens
- **Password Hashing:** Argon2 (via `argon2-cffi`)
- **Python Version:** 3.11+
- **Database:** PostgreSQL 15+ (via Supabase)

### Frontend Stack
- **Framework:** React 18+ (SPA architecture)
- **SSO Integration:** MSAL-React for Microsoft authentication flow
- **HTTP Client:** Axios or Fetch API with automatic token refresh

### Integration Requirements
- **Microsoft Entra ID:** Requires Azure AD tenant and app registration
- **SMTP Server:** Required for sending verification/reset emails
- **Redis:** Required for token blacklist and rate limiting

### Infrastructure
- **Environment Variables Required:**
  - `SECRET_KEY` - Django secret key (min 256 bits)
  - `JWT_SECRET_KEY` - JWT signing key (separate from Django secret)
  - `AZURE_CLIENT_ID` - Microsoft app registration client ID
  - `AZURE_CLIENT_SECRET` - Microsoft app registration secret
  - `AZURE_TENANT_ID` - Microsoft tenant ID
  - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` - Email configuration
  - `REDIS_URL` - Redis connection string
  - `FRONTEND_URL` - For CORS and redirect URLs

### API Design Standards
- **REST principles:** Resources, HTTP methods, status codes
- **JSON format:** All requests/responses in JSON
- **Authentication header:** `Authorization: Bearer <access_token>`
- **Error format:** Consistent error response structure
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

## Dependencies

### Internal Dependencies
None - This is the foundational module (Bloc 1)

### External Dependencies
- **Microsoft Entra ID (Azure AD):** For SSO authentication
- **SMTP Email Service:** For sending verification/reset emails (Gmail SMTP, SendGrid, AWS SES, etc.)
- **Redis Server:** For token blacklist and rate limiting
- **Supabase (PostgreSQL):** For user data storage

### Infrastructure Dependencies
- **TLS/SSL Certificates:** For HTTPS endpoints
- **DNS Configuration:** For production domain
- **Azure AD App Registration:** Must be configured before SSO implementation

### Blockers
None identified - All dependencies are standard and well-documented

## Success Metrics

### Key Performance Indicators (KPIs)
- **Authentication success rate:** > 99% (excluding user errors like wrong password)
- **Average login time:** < 2 seconds (including frontend processing)
- **Email delivery rate:** > 99% for verification/reset emails
- **Token refresh success rate:** > 99.9%
- **Zero security breaches:** No compromised passwords or unauthorized access

### User Adoption Metrics
- **Registration completion rate:** > 80% (registered users who verify email)
- **SSO adoption rate:** > 60% for enterprise users
- **Password reset usage:** Track for UX improvement opportunities
- **Account unification rate:** Track to validate feature usefulness

### Business Impact
- **User onboarding time:** Reduce from manual process to < 5 minutes self-service
- **Support ticket reduction:** < 5% of users require authentication support
- **Enterprise readiness:** SSO capability unlocks enterprise sales opportunities

## Implementation Approach

### Phases

**Phase 1: Standard Authentication (P0) - Week 1-2**
- User registration with email verification (US-1, US-2)
- Standard login with JWT tokens (US-3, US-4)
- Password reset flow (US-5, US-6)
- Basic profile viewing (US-8)

**Phase 2: Enterprise SSO (P1) - Week 3**
- Microsoft Entra ID integration (US-7)
- Account unification logic (US-11)
- Testing with Azure AD test tenant

**Phase 3: Profile Management (P2) - Week 4**
- Profile update functionality (US-9)
- Password change for standard users (US-10)
- Logout features (US-12, US-13)

### Rollout Strategy
- **Development environment:** Full testing with test accounts and Azure AD test tenant
- **Staging environment:** UAT with real users (internal team)
- **Production:** Gradual rollout:
  - Day 1: Internal users only
  - Day 3: Beta users (volunteers)
  - Day 7: All users
- **Feature flag:** SSO feature behind flag for controlled rollout

### Risk Mitigation
- **Risk 1: Microsoft SSO integration complexity**
  - Mitigation: Thorough testing with Azure AD test tenant, comprehensive documentation
  - Contingency: Standard auth works independently, SSO can be added later
- **Risk 2: Email delivery failures**
  - Mitigation: Use reliable SMTP service with retry logic, queue failed emails
  - Contingency: Manual verification by admin if needed
- **Risk 3: Token management complexity**
  - Mitigation: Use well-tested Simple JWT library, comprehensive token refresh testing
  - Contingency: Fallback to session-based auth if JWT issues arise (not recommended)
- **Risk 4: Account unification edge cases**
  - Mitigation: Thorough testing of all unification scenarios, clear user communication
  - Contingency: Support team can manually merge accounts if automated flow fails

## Testing Strategy

### Test Coverage
- **Unit tests:** > 80% coverage for all authentication logic
  - User model and managers
  - Authentication backends
  - Token generation and validation
  - Password hashing and verification
  - Email verification logic
  - Account unification logic
- **Integration tests:**
  - Complete registration flow
  - Login with standard and SSO
  - Token refresh flow
  - Password reset flow
  - Account unification scenarios
  - Profile update operations
- **End-to-end tests:**
  - User registration → verification → login → profile access
  - SSO login → profile access
  - Account unification complete flow
  - Logout and re-login

### User Acceptance Testing
- **UAT Plan:**
  - 10 internal users test standard authentication
  - 5 users test Microsoft SSO with test tenant
  - 3 users test account unification scenario
  - All users test profile management features
- **Test Scenarios:**
  - Happy path: Successful registration, verification, login
  - Error paths: Invalid credentials, expired tokens, duplicate emails
  - Edge cases: Concurrent logins, token refresh during long session, account unification
- **Acceptance Criteria:** All user stories' acceptance criteria verified by PO

## Documentation Requirements

- [x] API documentation (OpenAPI/Swagger spec)
- [x] User guide: How to register and log in
- [x] User guide: How to reset password
- [x] User guide: How to use Microsoft SSO
- [x] Administrator guide: User management
- [x] Developer guide: Authentication architecture
- [x] Developer guide: Adding new authentication providers
- [x] Security documentation: Token management best practices
- [x] Troubleshooting guide: Common authentication issues

## Timeline

- **Start Date:** Week 1 of Sprint 1
- **Target Completion:** End of Week 4 (Sprint 1)
- **Milestones:**
  - Week 1: Standard registration and login complete
  - Week 2: Password reset and basic profile management complete
  - Week 3: Microsoft SSO integration complete
  - Week 4: Account unification and logout features complete, UAT passed

## Stakeholders

- **Product Owner:** [PO Name]
- **Tech Lead:** [Tech Lead Name]
- **Backend Developers:** [Team Members]
- **Frontend Developers:** [Team Members]
- **Security Reviewer:** [Security Team Contact]
- **DevOps:** [DevOps Contact] (for Azure AD configuration)

## Notes

### Security Considerations
- All authentication endpoints must be monitored for suspicious activity
- Implement comprehensive logging for audit trail
- Regular security reviews of authentication code
- Keep authentication libraries up to date with security patches

### Future Enhancements (Out of Scope for MVP)
- Multi-factor authentication (MFA)
- Biometric authentication (fingerprint, Face ID)
- Social login (Google, LinkedIn, GitHub)
- Magic link login (passwordless)
- Account deletion and data export (GDPR compliance)
- Login history and device management

### Open Questions
- [ ] What SMTP service will be used for production emails?
- [ ] What is the Azure AD tenant ID for SSO integration?
- [ ] What should be the branding for email templates?
- [ ] Should we implement remember me functionality?
- [ ] What analytics should be tracked for authentication events?

---

**Document Version:** 1.0
**Last Updated:** 2025-10-28
**Source Documents:**
- docs/01_Authentification_Autorisation.md
- docs/00_choix_technologique.md
- CLAUDE.md
