# Product Owner Input Guide

This guide helps Product Owners create effective functional specifications that can be automatically parsed into structured Features and User Stories.

## Overview

The Functional Spec Planner plugin transforms your functional specifications into:
1. **Features** - High-level functional capabilities
2. **User Stories** - Specific user-facing requirements
3. **Tasks** - Granular development work items
4. **GitHub Issues** - Trackable implementation tasks

## Document Structure

Your PO input document should follow this recommended structure:

```markdown
# Feature Name

## Overview / Context
Brief description of the feature and its business value.

## Functional Requirements
Detailed description of what the feature should do.

## User Stories

### US-1: [Short Title]
**As a** [user type]
**I want to** [action/capability]
**So that** [benefit/value]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Priority:** P0 | P1 | P2 | P3

### US-2: [Short Title]
...

## Non-Functional Requirements
Performance, security, scalability requirements.

## Technical Constraints
Technology choices, infrastructure requirements.

## Dependencies
Other features or systems this depends on.
```

## Best Practices

### 1. Clear Feature Boundaries
- One PO document = One Feature
- Keep features focused and cohesive
- Split large features into multiple documents

### 2. Well-Defined User Stories
- Follow the "As a... I want... So that..." format
- Make acceptance criteria specific and testable
- Include priority levels (P0=critical, P1=high, P2=medium, P3=low)

### 3. Testable Acceptance Criteria
Good:
- ✅ "User receives email confirmation within 30 seconds"
- ✅ "System displays error message when password is less than 8 characters"

Bad:
- ❌ "System works well"
- ❌ "User has good experience"

### 4. Appropriate Granularity
- Each User Story should be implementable in 1-2 weeks
- If larger, break into multiple User Stories
- If smaller, combine related functionality

### 5. Clear Dependencies
- Explicitly state dependencies on other features
- Mention required third-party services or APIs
- Note any infrastructure requirements

## Example PO Input

```markdown
# User Authentication

## Overview
Implement dual authentication system supporting both standard email/password login and Microsoft Entra ID SSO for enterprise users.

## Functional Requirements

The authentication system must support:
1. Standard registration with email/password
2. Microsoft Entra ID SSO integration
3. Account unification for users with same email
4. JWT-based API authentication
5. Session management with refresh tokens

## User Stories

### US-1: Standard User Registration
**As a** new user
**I want to** register with email and password
**So that** I can create an account and access the platform

**Acceptance Criteria:**
- [ ] Registration form accepts email, password, and password confirmation
- [ ] Email validation ensures valid format
- [ ] Password must be minimum 8 characters with uppercase, lowercase, and number
- [ ] Password is hashed using Argon2 before storage
- [ ] User receives confirmation email after registration
- [ ] Duplicate email addresses are rejected with clear error message
- [ ] Form displays real-time validation feedback

**Priority:** P0

**Technical Notes:**
- Use Django's built-in User model
- Implement Argon2 password hasher
- Send confirmation emails via SMTP

### US-2: Microsoft Entra ID SSO Login
**As an** enterprise user
**I want to** log in using my Microsoft Entra ID account
**So that** I can use single sign-on without creating a separate password

**Acceptance Criteria:**
- [ ] "Sign in with Microsoft" button displayed on login page
- [ ] OAuth2 flow redirects to Microsoft login
- [ ] User profile created from Microsoft claims (email, name, etc.)
- [ ] If email matches existing account, accounts are unified
- [ ] JWT token issued after successful authentication
- [ ] Failed authentication displays appropriate error message

**Priority:** P1

**Technical Notes:**
- Use Microsoft Authentication Library (MSAL)
- Configure Azure AD app registration
- Map Microsoft claims to user profile fields

### US-3: JWT Token-Based API Authentication
**As a** frontend application
**I want to** authenticate API requests using JWT tokens
**So that** I can securely access backend resources

**Acceptance Criteria:**
- [ ] Access token issued on successful login (15-minute expiry)
- [ ] Refresh token issued with access token (7-day expiry)
- [ ] All protected endpoints require valid access token in Authorization header
- [ ] Invalid/expired tokens return 401 Unauthorized
- [ ] Refresh endpoint issues new access token using valid refresh token
- [ ] Token includes user ID and role claims

**Priority:** P0

**Technical Notes:**
- Use djangorestframework-simplejwt
- Configure token expiry times
- Implement token refresh endpoint

## Non-Functional Requirements

### Security
- Passwords hashed using Argon2 (OWASP recommended)
- JWT tokens signed with HS256 algorithm
- HTTPS required for all authentication endpoints
- Rate limiting on login attempts (max 5 per minute)

### Performance
- Authentication endpoint response time < 300ms (P95)
- Token refresh < 100ms (P95)
- Support 1000 concurrent authentication requests

### Scalability
- Stateless authentication (JWT) for horizontal scaling
- Redis caching for token validation
- Session data stored in Redis, not database

## Technical Constraints

- Backend: Django 4.2+ with Django REST Framework
- Token library: djangorestframework-simplejwt
- Password hashing: Argon2
- SSO: Microsoft Authentication Library (MSAL)
- Cache: Redis 7+

## Dependencies

- Redis server for session and token caching
- SMTP server for email confirmation
- Microsoft Azure AD tenant for SSO
- Environment variables for secrets (JWT secret, Azure credentials)

## Success Metrics

- 95% of users successfully authenticate within 5 seconds
- Zero password breaches due to weak hashing
- SSO adoption rate > 60% for enterprise users
```

## What Happens Next

After you create your PO input document:

1. **Parse the document**:
   ```bash
   /spec-parse docs/po_input/your-feature.md
   ```

2. **Review generated specs**:
   - `./specs/your-feature/feature.md` - Structured Feature spec
   - `./specs/your-feature/US-*/user-story.md` - Individual User Stories

3. **Generate development tasks**:
   ```bash
   /spec-generate-tasks your-feature/US-1
   ```

4. **Review tasks** in `./specs/your-feature/US-1/tasks.md`

5. **Create GitHub issues**:
   ```bash
   /spec-create-issues your-feature/US-1
   ```

## Tips for Product Owners

### Do's ✅
- Write acceptance criteria from user perspective
- Include technical constraints upfront
- Specify non-functional requirements clearly
- Provide context and business rationale
- Use consistent terminology throughout
- Include examples and edge cases

### Don'ts ❌
- Don't specify implementation details (let devs decide)
- Don't mix multiple features in one document
- Don't use vague acceptance criteria
- Don't forget non-functional requirements
- Don't skip dependency documentation

## Questions?

Run `/spec-help` for more information about the workflow and available commands.
