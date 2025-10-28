# US-1: Standard User Registration

**Priority**: P0 (Critical)
**Feature**: Authentication & Authorization
**Status**: To Do
**Story Points**: 8

## Overview

This User Story implements the standard user registration flow for the AI-powered Technology Watch Platform. New users can create an account using their email address and a secure password. The system validates all inputs, enforces strong password requirements, hashes passwords securely using Argon2, and sends a verification email to confirm the user's identity.

### Context

User registration is the entry point for individual professionals to access the platform. This feature establishes user identity and creates the foundation for all authenticated operations. The account remains inactive until email verification is completed (US-2), ensuring that users have access to a valid email address.

### Decomposition Approach

This User Story has been decomposed into **19 granular tasks** across four categories:

- **Backend**: 9 tasks covering database models, API endpoints, security, email service, and configuration
- **Frontend**: 5 tasks for registration form, validation, and user experience
- **Testing**: 3 tasks for unit, integration, and security testing
- **Infrastructure**: 2 tasks for SMTP configuration and API documentation

The tasks follow Django + DRF best practices with React frontend, Argon2 password hashing, Celery async email processing, and comprehensive testing.

---

## Task Summary

| ID | Title | Type | Specialty | Effort | Dependencies | Status |
|----|-------|------|-----------|--------|--------------|--------|
| TASK-1.1 | Create CustomUser model with email as username | Backend | Database | 3h | None | ⬜ |
| TASK-1.2 | Configure django-allauth for email-based auth | Backend | Config | 2h | TASK-1.1 | ⬜ |
| TASK-1.3 | Setup Argon2 password hashing | Backend | Security | 2h | TASK-1.1 | ⬜ |
| TASK-1.4 | Implement password validation rules | Backend | Security | 3h | TASK-1.3 | ⬜ |
| TASK-1.5 | Create user registration serializer | Backend | API | 4h | TASK-1.1, TASK-1.4 | ⬜ |
| TASK-1.6 | Implement registration API endpoint | Backend | API | 4h | TASK-1.5 | ⬜ |
| TASK-1.7 | Setup Celery for async email sending | Backend | Config | 3h | None | ⬜ |
| TASK-1.8 | Implement verification email service | Backend | Email | 4h | TASK-1.7 | ⬜ |
| TASK-1.9 | Configure rate limiting for registration | Backend | Security | 3h | TASK-1.6 | ⬜ |
| TASK-1.10 | Create registration form component | Frontend | Component | 5h | TASK-1.6 | ⬜ |
| TASK-1.11 | Implement password strength indicator | Frontend | Component | 3h | None | ⬜ |
| TASK-1.12 | Create registration page with form | Frontend | Page | 4h | TASK-1.10, TASK-1.11 | ⬜ |
| TASK-1.13 | Create API service for registration | Frontend | API | 3h | TASK-1.6 | ⬜ |
| TASK-1.14 | Implement success/error messaging | Frontend | Component | 2h | TASK-1.13 | ⬜ |
| TASK-1.15 | Write unit tests for registration logic | Testing | Unit | 4h | TASK-1.5, TASK-1.6 | ⬜ |
| TASK-1.16 | Write integration tests for registration | Testing | Integration | 5h | TASK-1.6, TASK-1.8 | ⬜ |
| TASK-1.17 | Write security tests (rate limit, validation) | Testing | Security | 4h | TASK-1.9 | ⬜ |
| TASK-1.18 | Configure SMTP settings for email | Infrastructure | Config | 2h | None | ⬜ |
| TASK-1.19 | Create API documentation for endpoint | Infrastructure | Documentation | 3h | TASK-1.6 | ⬜ |

**Total Tasks**: 19
**Total Effort**: 61 hours (approximately 8 days for 1 developer)

---

## Task Details

### 🔧 Backend Tasks

#### TASK-1.1: Create CustomUser model with email as username

**Type**: Backend - Database
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Create a custom Django User model that extends `AbstractBaseUser` and `PermissionsMixin`, using email as the primary authentication identifier instead of username. The model must include fields for email (unique), first_name, last_name, is_active (default False), is_email_verified (default False), and timestamp fields. This is the foundation for all user-related operations in the system.

##### Files Impacted

- `backend/apps/authentication/models.py` (new)
- `backend/apps/authentication/managers.py` (new)
- `backend/apps/authentication/migrations/0001_initial.py` (new)
- `backend/config/settings.py` (modified - AUTH_USER_MODEL)

##### Acceptance Criteria

- [ ] CustomUser model created extending AbstractBaseUser and PermissionsMixin
- [ ] Email field set as USERNAME_FIELD (unique, required)
- [ ] Fields include: email, first_name, last_name, is_active, is_email_verified, created_at, updated_at
- [ ] Custom UserManager created with create_user and create_superuser methods
- [ ] AUTH_USER_MODEL configured in settings.py
- [ ] Initial migration generated and applied
- [ ] Database table created with proper constraints (unique email, indexes)

##### Dependencies

None (foundation task)

##### Implementation Notes

- Use `AbstractBaseUser` for full control over authentication
- Set `USERNAME_FIELD = 'email'`
- Set `REQUIRED_FIELDS = ['first_name', 'last_name']`
- Create custom manager with `create_user()` that normalizes email
- Use `EmailField` with `unique=True` and `db_index=True`
- Default `is_active=False` to require email verification
- Add `__str__` method returning email

---

#### TASK-1.2: Configure django-allauth for email-based authentication

**Type**: Backend - Config
**Priority**: P0
**Estimated Effort**: 2 hours

##### Description

Install and configure django-allauth to handle email-based authentication flows. This includes configuring allauth settings for email verification, disabling username-based authentication, and setting up email as the primary login method. The configuration establishes the foundation for the registration and verification workflow.

##### Files Impacted

- `backend/requirements.txt` (modified - add django-allauth)
- `backend/config/settings.py` (modified - allauth configuration)
- `backend/config/urls.py` (modified - include allauth URLs)

##### Acceptance Criteria

- [ ] django-allauth installed (version 0.54+)
- [ ] INSTALLED_APPS includes: allauth, allauth.account, allauth.socialaccount
- [ ] AUTHENTICATION_BACKENDS configured with allauth.account.auth_backends.AuthenticationBackend
- [ ] ACCOUNT_AUTHENTICATION_METHOD set to 'email'
- [ ] ACCOUNT_EMAIL_REQUIRED set to True
- [ ] ACCOUNT_USERNAME_REQUIRED set to False
- [ ] ACCOUNT_EMAIL_VERIFICATION set to 'mandatory'
- [ ] Allauth URLs included in project urlconf

##### Dependencies

- TASK-1.1 (CustomUser model must exist)

##### Implementation Notes

- Add to INSTALLED_APPS after django.contrib.auth
- Configure ACCOUNT_USER_MODEL_USERNAME_FIELD = None
- Set ACCOUNT_UNIQUE_EMAIL = True
- Configure ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1 (24 hours)
- Include allauth.urls with path('api/auth/', include('allauth.urls'))

---

#### TASK-1.3: Setup Argon2 password hashing

**Type**: Backend - Security
**Priority**: P0
**Estimated Effort**: 2 hours

##### Description

Configure Django to use Argon2 password hashing algorithm (OWASP recommended) for all password storage. Install the argon2-cffi library and configure Django's PASSWORD_HASHERS setting to prioritize Argon2PasswordHasher. This ensures all new user passwords are hashed with the most secure algorithm available.

##### Files Impacted

- `backend/requirements.txt` (modified - add argon2-cffi)
- `backend/config/settings.py` (modified - PASSWORD_HASHERS)

##### Acceptance Criteria

- [ ] argon2-cffi library installed (version 21.0+)
- [ ] PASSWORD_HASHERS configured with Argon2PasswordHasher as first choice
- [ ] Fallback hashers included for password migration (PBKDF2PasswordHasher)
- [ ] Test user creation verifies password is hashed with argon2
- [ ] Password verification works correctly with argon2 hashes
- [ ] Documentation added explaining hashing configuration

##### Dependencies

- TASK-1.1 (CustomUser model must exist)

##### Implementation Notes

- Add 'argon2-cffi>=21.0' to requirements.txt
- Configure PASSWORD_HASHERS in settings.py:
  ```python
  PASSWORD_HASHERS = [
      'django.contrib.auth.hashers.Argon2PasswordHasher',
      'django.contrib.auth.hashers.PBKDF2PasswordHasher',
  ]
  ```
- Test with `make_password()` and `check_password()` functions
- Argon2 hashes start with '$argon2' prefix

---

#### TASK-1.4: Implement password validation rules

**Type**: Backend - Security
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Create a custom password validator that enforces strong password requirements: minimum 8 characters, at least one uppercase letter, one lowercase letter, one number, and recommends special characters. Integrate with Django's password validation system and provide clear, actionable error messages for users. The validator should work with both the registration API and django-allauth.

##### Files Impacted

- `backend/apps/authentication/validators.py` (new)
- `backend/config/settings.py` (modified - AUTH_PASSWORD_VALIDATORS)
- `backend/apps/authentication/tests/test_validators.py` (new)

##### Acceptance Criteria

- [ ] Custom validator class created (StrongPasswordValidator)
- [ ] Validates minimum 8 characters
- [ ] Validates at least one uppercase letter (A-Z)
- [ ] Validates at least one lowercase letter (a-z)
- [ ] Validates at least one digit (0-9)
- [ ] Recommends but does not require special characters
- [ ] Provides clear error messages for each failed criterion
- [ ] Integrated into AUTH_PASSWORD_VALIDATORS in settings
- [ ] Unit tests written covering all validation scenarios

##### Dependencies

- TASK-1.3 (password hashing must be configured)

##### Implementation Notes

- Implement `validate(password, user=None)` method
- Raise `ValidationError` with descriptive messages
- Use regex patterns for character type validation
- Return list of failed requirements in error message
- Add to AUTH_PASSWORD_VALIDATORS list in settings.py
- Test with passwords: 'weak', 'NoNumber', 'SecurePass123!', etc.

---

#### TASK-1.5: Create user registration serializer with validation

**Type**: Backend - API
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Implement a Django REST Framework serializer for user registration that validates email format (RFC 5322), enforces password requirements, confirms password match, and handles duplicate email detection. The serializer should provide detailed field-level validation errors and integrate with the CustomUser model and password validators.

##### Files Impacted

- `backend/apps/authentication/serializers.py` (new)
- `backend/apps/authentication/tests/test_serializers.py` (new)

##### Acceptance Criteria

- [ ] UserRegistrationSerializer created inheriting serializers.ModelSerializer
- [ ] Fields: email, password, password_confirm, first_name, last_name
- [ ] Email validation ensures valid format (RFC 5322 compliant)
- [ ] Password validation uses StrongPasswordValidator
- [ ] password_confirm field validates match with password
- [ ] Duplicate email returns clear error: "An account with this email already exists"
- [ ] validate() method ensures password == password_confirm
- [ ] create() method creates user with is_active=False, is_email_verified=False
- [ ] Password is hashed using Argon2 (via set_password())
- [ ] Unit tests cover valid/invalid email, password mismatch, duplicate email, weak password

##### Dependencies

- TASK-1.1 (CustomUser model)
- TASK-1.4 (password validators)

##### Implementation Notes

- Use `write_only=True` for password fields
- Override `validate()` for password confirmation check
- Override `create()` to call `user.set_password()`
- Use `validators.EmailValidator()` for email validation
- Return serialized user data without password in response
- Test with valid data: {'email': 'test@example.com', 'password': 'SecurePass123!', 'password_confirm': 'SecurePass123!'}

---

#### TASK-1.6: Implement registration API endpoint

**Type**: Backend - API
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Create a DRF APIView or ViewSet that handles POST requests to `/api/auth/register/` for user registration. The endpoint should validate input using UserRegistrationSerializer, create the user account, trigger the verification email asynchronously, and return appropriate HTTP status codes (201 for success, 400/409 for errors). Implement comprehensive error handling for all failure scenarios.

##### Files Impacted

- `backend/apps/authentication/views.py` (new)
- `backend/apps/authentication/urls.py` (new)
- `backend/config/urls.py` (modified - include authentication URLs)
- `backend/apps/authentication/tests/test_views.py` (new)

##### Acceptance Criteria

- [ ] RegistrationView created (APIView or CreateAPIView)
- [ ] Endpoint: POST /api/auth/register/
- [ ] Accepts JSON: {email, password, password_confirm, first_name, last_name}
- [ ] Returns 201 Created on success with user data and message
- [ ] Returns 400 Bad Request for validation errors
- [ ] Returns 409 Conflict for duplicate email
- [ ] Triggers send_verification_email task asynchronously (Celery)
- [ ] Response includes: user id, email, first_name, last_name, is_active (false)
- [ ] Response message: "Registration successful. Please check your email to verify your account."
- [ ] Endpoint responds within 300ms (P95) - verified by load testing

##### Dependencies

- TASK-1.5 (UserRegistrationSerializer)

##### Implementation Notes

- Use `rest_framework.views.APIView` or `generics.CreateAPIView`
- Set `permission_classes = [AllowAny]`
- Use `serializer.save()` to create user
- Call `send_verification_email.delay(user.id)` after user creation
- Return `Response(data, status=status.HTTP_201_CREATED)`
- Handle exceptions: ValidationError (400), IntegrityError (409)
- Include URL pattern in authentication/urls.py
- Add logging for registration attempts

---

#### TASK-1.7: Setup Celery for async email sending

**Type**: Backend - Config
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Install and configure Celery with Redis as the message broker for asynchronous task processing. This enables non-blocking email sending during user registration, ensuring the registration API responds quickly without waiting for SMTP operations. Configure Celery workers, result backend, and basic task routing.

##### Files Impacted

- `backend/requirements.txt` (modified - add celery, redis)
- `backend/config/celery.py` (new)
- `backend/config/__init__.py` (modified - import celery app)
- `backend/config/settings.py` (modified - Celery configuration)
- `docker-compose.yml` (modified - add worker service)

##### Acceptance Criteria

- [ ] Celery installed (version 5.2+)
- [ ] Redis installed as Python client (redis>=4.5)
- [ ] Celery app configured in config/celery.py
- [ ] CELERY_BROKER_URL configured (Redis connection string)
- [ ] CELERY_RESULT_BACKEND configured (Redis)
- [ ] Celery autodiscover_tasks configured for app modules
- [ ] Celery worker service added to docker-compose.yml
- [ ] Worker starts successfully and connects to Redis
- [ ] Test task can be executed and completed

##### Dependencies

None (infrastructure task)

##### Implementation Notes

- Add to requirements.txt: celery[redis]>=5.2, redis>=4.5
- Create config/celery.py with app = Celery('backend')
- Configure broker: CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
- Set CELERY_RESULT_BACKEND = CELERY_BROKER_URL
- Add to config/__init__.py: `from .celery import app as celery_app`
- Docker Compose worker command: celery -A config worker -l info
- Test with simple task: `@shared_task def add(x, y): return x + y`

---

#### TASK-1.8: Implement verification email service

**Type**: Backend - Email
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Create a Celery task that generates email verification tokens using django-allauth's email confirmation system and sends verification emails via SMTP. The task should create an email message with a verification link containing a time-limited token (24-hour expiry), format the email with HTML and plain text versions, and handle email sending failures with retry logic.

##### Files Impacted

- `backend/apps/authentication/tasks.py` (new)
- `backend/apps/authentication/templates/email/verification_email.html` (new)
- `backend/apps/authentication/templates/email/verification_email.txt` (new)
- `backend/apps/authentication/tests/test_tasks.py` (new)

##### Acceptance Criteria

- [ ] send_verification_email Celery task created with @shared_task decorator
- [ ] Task accepts user_id parameter
- [ ] Generates email confirmation token using allauth (EmailAddress.objects.add_email)
- [ ] Creates verification URL: {FRONTEND_URL}/verify-email?token={token}
- [ ] Email template includes: user name, verification link, expiry time (24 hours)
- [ ] Both HTML and plain text email versions created
- [ ] Email sent via Django's send_mail() function
- [ ] Retry logic configured (3 attempts, exponential backoff)
- [ ] Email sent within 30 seconds of registration
- [ ] Task logs success/failure for monitoring

##### Dependencies

- TASK-1.7 (Celery must be configured)

##### Implementation Notes

- Use `@shared_task(bind=True, max_retries=3)`
- Get user: `User.objects.get(id=user_id)`
- Use allauth: `EmailConfirmation.create(email_address)`
- Generate URL with token: confirmation.key
- Use `render_to_string()` for email templates
- Configure retry: `self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))`
- Subject: "Verify your email address - Technology Watch Platform"

---

#### TASK-1.9: Configure rate limiting for registration endpoint

**Type**: Backend - Security
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Implement rate limiting on the registration endpoint to prevent abuse and brute force attacks. Configure django-ratelimit to restrict registration attempts to 5 per IP address per hour. Rate limit data should be stored in Redis for distributed rate limiting across multiple backend instances. Return clear 429 Too Many Requests responses when limit is exceeded.

##### Files Impacted

- `backend/requirements.txt` (modified - add django-ratelimit)
- `backend/apps/authentication/views.py` (modified - add rate limit decorator)
- `backend/config/settings.py` (modified - rate limit configuration)
- `backend/apps/authentication/tests/test_rate_limiting.py` (new)

##### Acceptance Criteria

- [ ] django-ratelimit installed (version 4.0+)
- [ ] RATELIMIT_USE_CACHE = 'default' configured (Redis cache)
- [ ] @ratelimit decorator applied to RegistrationView: rate='5/h', key='ip'
- [ ] 6th registration attempt within 1 hour returns 429 status
- [ ] Error message: "Too many registration attempts. Please try again later."
- [ ] Rate limit counter resets after 1 hour
- [ ] Rate limit data stored in Redis
- [ ] Rate limit works across multiple backend instances
- [ ] Unit tests verify rate limiting behavior

##### Dependencies

- TASK-1.6 (registration endpoint must exist)

##### Implementation Notes

- Add to requirements.txt: django-ratelimit>=4.0
- Configure Redis cache in settings.py as 'default'
- Decorate view method: `@ratelimit(key='ip', rate='5/h', method='POST')`
- Check `getattr(request, 'limited', False)` in view
- Return Response with 429 status and Retry-After header
- Test with multiple requests from same IP
- Redis key format: 'rl:ip:{ip_address}'

---

### 🎨 Frontend Tasks

#### TASK-1.10: Create registration form component with real-time validation

**Type**: Frontend - Component
**Priority**: P0
**Estimated Effort**: 5 hours

##### Description

Build a React form component for user registration with fields for email, password, password confirmation, first name (optional), and last name (optional). Implement real-time client-side validation that mirrors backend validation rules, providing immediate visual feedback as users type. The component should manage form state, display validation errors, and handle submission with loading states.

##### Files Impacted

- `frontend/src/components/auth/RegistrationForm.jsx` (new)
- `frontend/src/components/auth/RegistrationForm.module.css` (new)
- `frontend/src/hooks/useFormValidation.js` (new)
- `frontend/src/utils/validators.js` (new)

##### Acceptance Criteria

- [ ] RegistrationForm component created with all required fields
- [ ] Real-time email validation (format check)
- [ ] Real-time password validation matching backend rules
- [ ] Password confirmation validation (must match password)
- [ ] Visual feedback for validation state (green check, red X)
- [ ] Form submission triggers API call
- [ ] Loading state displayed during submission
- [ ] Form disabled during submission to prevent double-submit
- [ ] Error messages displayed for field-level and form-level errors
- [ ] Responsive design works on mobile/tablet/desktop

##### Dependencies

- TASK-1.6 (API endpoint must exist for integration)

##### Implementation Notes

- Use controlled components with useState for form fields
- Implement custom useFormValidation hook for reusability
- Validate on blur and on change (debounced for password)
- Use validators.js for validation logic (mirror backend rules)
- Email regex: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
- Password validator checks: length >=8, uppercase, lowercase, digit
- Display validation errors inline below each field
- Use CSS modules for component styling

---

#### TASK-1.11: Implement password strength indicator

**Type**: Frontend - Component
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Create a visual password strength indicator component that provides real-time feedback on password quality as the user types. The indicator should show which password requirements are met (8+ characters, uppercase, lowercase, number, special character) with visual checkmarks or progress indicators. This enhances user experience by guiding users to create strong passwords.

##### Files Impacted

- `frontend/src/components/auth/PasswordStrengthIndicator.jsx` (new)
- `frontend/src/components/auth/PasswordStrengthIndicator.module.css` (new)
- `frontend/src/utils/passwordStrength.js` (new)

##### Acceptance Criteria

- [ ] PasswordStrengthIndicator component created
- [ ] Displays 5 password requirements as checklist
- [ ] ✓ Minimum 8 characters (required)
- [ ] ✓ Contains uppercase letter (required)
- [ ] ✓ Contains lowercase letter (required)
- [ ] ✓ Contains number (required)
- [ ] ○ Contains special character (recommended, not required)
- [ ] Each requirement shows check/X based on password content
- [ ] Color-coded feedback: red (weak), yellow (medium), green (strong)
- [ ] Updates in real-time as user types
- [ ] Accessible to screen readers (ARIA labels)

##### Dependencies

None (standalone UI component)

##### Implementation Notes

- Accept password prop and calculate strength
- Use passwordStrength.js utility to check requirements
- Return object: {hasMinLength, hasUppercase, hasLowercase, hasNumber, hasSpecial}
- Use color variables: --color-weak, --color-medium, --color-strong
- ARIA live region for screen reader updates
- Component can be reused in password change (US-10)

---

#### TASK-1.12: Create registration page with form integration

**Type**: Frontend - Page
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Build the registration page that integrates the RegistrationForm and PasswordStrengthIndicator components. The page should handle form submission, call the registration API service, manage loading and error states, and redirect users to a success page or login page after successful registration. Include links to login page for users who already have accounts.

##### Files Impacted

- `frontend/src/pages/RegisterPage.jsx` (new)
- `frontend/src/pages/RegisterPage.module.css` (new)
- `frontend/src/App.jsx` (modified - add route)

##### Acceptance Criteria

- [ ] RegisterPage component created
- [ ] Integrates RegistrationForm and PasswordStrengthIndicator
- [ ] Calls registrationService.register() on form submit
- [ ] Displays loading spinner during API call
- [ ] On success: Shows success message and redirects to /verify-email page
- [ ] On error: Displays error messages from API response
- [ ] Link to login page: "Already have an account? Sign in"
- [ ] Responsive layout for all screen sizes
- [ ] Accessible (keyboard navigation, screen reader support)
- [ ] Route configured in App.jsx: /register

##### Dependencies

- TASK-1.10 (RegistrationForm component)
- TASK-1.11 (PasswordStrengthIndicator component)

##### Implementation Notes

- Use React Router for navigation
- Handle API errors: 400 (validation), 409 (duplicate email), 429 (rate limit)
- Success message: "Registration successful! Please check your email to verify your account."
- Redirect using navigate('/verify-email') from react-router-dom
- Center form vertically and horizontally
- Add platform branding/logo at top of page

---

#### TASK-1.13: Create API service for registration

**Type**: Frontend - API
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Implement a frontend service module that handles HTTP communication with the registration API endpoint. The service should construct properly formatted requests, handle authentication headers (none required for registration), parse API responses, and transform errors into user-friendly messages. Use Axios or Fetch API with proper error handling and timeout configuration.

##### Files Impacted

- `frontend/src/services/authService.js` (new)
- `frontend/src/utils/apiClient.js` (new)
- `frontend/src/config/api.js` (new)

##### Acceptance Criteria

- [ ] authService.js module created with register() function
- [ ] register() accepts: {email, password, passwordConfirm, firstName, lastName}
- [ ] POST request to /api/auth/register/ with JSON body
- [ ] Content-Type: application/json header set
- [ ] Request timeout configured (10 seconds)
- [ ] Successful response (201) returns user data
- [ ] Error responses (400, 409, 429) parsed and returned with messages
- [ ] Network errors handled gracefully
- [ ] API base URL configurable via environment variable (REACT_APP_API_URL)
- [ ] Service can be mocked for testing

##### Dependencies

- TASK-1.6 (backend API endpoint must exist)

##### Implementation Notes

- Use Axios: `axios.post(${API_BASE_URL}/api/auth/register/, data)`
- Configure apiClient.js with default settings (baseURL, timeout, headers)
- API_BASE_URL from config/api.js: `process.env.REACT_APP_API_URL || 'http://localhost:8000'`
- Transform API errors into {field: message} format
- Handle 429 response with retry-after information
- Export as default: `export default { register }`

---

#### TASK-1.14: Implement success/error messaging component

**Type**: Frontend - Component
**Priority**: P0
**Estimated Effort**: 2 hours

##### Description

Create a reusable alert/message component that displays success, error, warning, and info messages to users. The component should support different message types with appropriate styling, auto-dismiss functionality, and accessibility features. This component will be used throughout the application for user feedback but is critical for the registration flow.

##### Files Impacted

- `frontend/src/components/common/Alert.jsx` (new)
- `frontend/src/components/common/Alert.module.css` (new)

##### Acceptance Criteria

- [ ] Alert component created accepting: type, message, dismissible, duration
- [ ] Supports types: success, error, warning, info
- [ ] Color-coded styling for each type (green, red, yellow, blue)
- [ ] Optional close button when dismissible=true
- [ ] Auto-dismiss after duration milliseconds (if specified)
- [ ] ARIA role="alert" for accessibility
- [ ] Icon displayed for each type (check, X, warning, info)
- [ ] Smooth fade-in/fade-out animation
- [ ] Multiple alerts can be stacked
- [ ] Component is reusable across application

##### Dependencies

- TASK-1.13 (API service for integration)

##### Implementation Notes

- Use CSS modules for scoped styling
- Type prop determines CSS class: alert-success, alert-error, etc.
- Auto-dismiss with useEffect and setTimeout
- Close button calls onDismiss callback
- Icons can be SVG or icon library (react-icons)
- Example usage: `<Alert type="success" message="Registration successful!" />`
- Consider toast notification library (react-toastify) as alternative

---

### ✅ Testing Tasks

#### TASK-1.15: Write unit tests for registration logic

**Type**: Testing - Unit
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Implement comprehensive unit tests for backend registration components including the CustomUser model, UserRegistrationSerializer, password validators, and helper functions. Tests should cover valid inputs, invalid inputs, edge cases, and error conditions. Aim for >80% code coverage on all registration-related modules.

##### Files Impacted

- `backend/apps/authentication/tests/test_models.py` (new)
- `backend/apps/authentication/tests/test_serializers.py` (new)
- `backend/apps/authentication/tests/test_validators.py` (new)
- `backend/pytest.ini` (new/modified)

##### Acceptance Criteria

- [ ] Test suite created using pytest and pytest-django
- [ ] CustomUser model tests: creation, email normalization, password hashing
- [ ] UserRegistrationSerializer tests: valid data, invalid email, password mismatch, weak password, duplicate email
- [ ] Password validator tests: each validation rule tested individually
- [ ] Edge cases tested: empty fields, very long inputs, special characters
- [ ] All tests pass successfully
- [ ] Code coverage >80% for authentication app
- [ ] Tests run in <10 seconds

##### Dependencies

- TASK-1.5 (serializer must be implemented)
- TASK-1.6 (view must be implemented)

##### Implementation Notes

- Use pytest fixtures for test data and database setup
- Create UserFactory using factory_boy for test data generation
- Test valid registration: `test_valid_registration_creates_user()`
- Test invalid email: `test_invalid_email_format_fails()`
- Test password mismatch: `test_password_confirmation_mismatch_fails()`
- Test weak password: `test_weak_password_rejected()`
- Test duplicate email: `test_duplicate_email_rejected()`
- Use pytest markers: `@pytest.mark.django_db`
- Run with: `pytest backend/apps/authentication/tests/`

---

#### TASK-1.16: Write integration tests for registration flow

**Type**: Testing - Integration
**Priority**: P0
**Estimated Effort**: 5 hours

##### Description

Create integration tests that verify the complete registration flow from API request to database persistence to email sending. Tests should use Django's test client or DRF's APIClient to make actual HTTP requests to the registration endpoint, verify database state changes, and confirm that Celery tasks are triggered (using task mocking). Test both successful registration and various error scenarios.

##### Files Impacted

- `backend/apps/authentication/tests/test_integration.py` (new)
- `backend/apps/authentication/tests/factories.py` (new)

##### Acceptance Criteria

- [ ] Integration test suite created using DRF APIClient
- [ ] Test successful registration flow: POST request → user created → email task queued
- [ ] Test duplicate email returns 409 Conflict
- [ ] Test invalid email format returns 400 Bad Request
- [ ] Test password validation errors return 400 with details
- [ ] Test password mismatch returns 400
- [ ] Test user created with is_active=False and is_email_verified=False
- [ ] Test verification email task triggered with correct user_id
- [ ] Test response format matches API specification
- [ ] All integration tests pass

##### Dependencies

- TASK-1.6 (registration endpoint)
- TASK-1.8 (email service)

##### Implementation Notes

- Use APIClient: `client = APIClient()`
- Mock Celery task: `@patch('authentication.tasks.send_verification_email.delay')`
- Test request: `response = client.post('/api/auth/register/', data, format='json')`
- Assert response: `assert response.status_code == 201`
- Verify database: `assert User.objects.filter(email='test@example.com').exists()`
- Verify task called: `mock_task.assert_called_once_with(user.id)`
- Use TransactionTestCase for Celery integration
- Run with: `pytest backend/apps/authentication/tests/test_integration.py`

---

#### TASK-1.17: Write security tests for rate limiting and validation

**Type**: Testing - Security
**Priority**: P0
**Estimated Effort**: 4 hours

##### Description

Implement security-focused tests that verify rate limiting enforcement, input validation, SQL injection protection, XSS prevention, and password security. Tests should attempt to bypass rate limits, inject malicious input, and verify that all security measures are properly enforced. This ensures the registration endpoint is hardened against common attacks.

##### Files Impacted

- `backend/apps/authentication/tests/test_security.py` (new)

##### Acceptance Criteria

- [ ] Rate limiting test: 6th request within 1 hour returns 429
- [ ] SQL injection test: malicious email input safely handled
- [ ] XSS test: script tags in name fields are escaped
- [ ] Password not logged in error messages or logs
- [ ] Password never returned in API responses
- [ ] Password stored as Argon2 hash (starts with $argon2)
- [ ] Duplicate email attempt does not reveal user existence
- [ ] Very long inputs (>500 chars) rejected
- [ ] Special characters in email handled correctly
- [ ] All security tests pass

##### Dependencies

- TASK-1.9 (rate limiting must be configured)

##### Implementation Notes

- Test rate limit: make 6 POST requests with same IP
- Use `X-Forwarded-For` header to simulate IP address
- SQL injection test: email="admin'--@example.com"
- XSS test: first_name="<script>alert('xss')</script>"
- Verify password hash: `assert user.password.startswith('$argon2')`
- Test long email: 500+ character string
- Use pytest parametrize for multiple injection attempts
- Run with: `pytest backend/apps/authentication/tests/test_security.py -v`

---

### ⚙️ Infrastructure Tasks

#### TASK-1.18: Configure SMTP settings for email delivery

**Type**: Infrastructure - Config
**Priority**: P0
**Estimated Effort**: 2 hours

##### Description

Configure Django's email backend to use SMTP for sending verification emails. Set up SMTP server credentials (Gmail SMTP, SendGrid, or AWS SES), configure TLS encryption, and set default sender email address. Create environment variables for sensitive credentials and document the configuration in the setup guide. Test email sending in development and staging environments.

##### Files Impacted

- `backend/config/settings.py` (modified - EMAIL_* settings)
- `backend/.env.example` (modified - add SMTP variables)
- `docs/setup/00_setup_local_docker.md` (modified - SMTP configuration)

##### Acceptance Criteria

- [ ] EMAIL_BACKEND configured for SMTP
- [ ] EMAIL_HOST configured from environment variable
- [ ] EMAIL_PORT configured (587 for TLS)
- [ ] EMAIL_USE_TLS set to True
- [ ] EMAIL_HOST_USER configured from environment variable
- [ ] EMAIL_HOST_PASSWORD configured from environment variable
- [ ] DEFAULT_FROM_EMAIL configured (noreply@platform.com)
- [ ] .env.example includes all SMTP variables with placeholders
- [ ] Test email successfully sent in development environment
- [ ] Documentation updated with SMTP configuration steps

##### Dependencies

None (infrastructure task)

##### Implementation Notes

- Use django.core.mail.backends.smtp.EmailBackend
- Environment variables:
  - SMTP_HOST (e.g., smtp.gmail.com)
  - SMTP_PORT (587)
  - SMTP_USER (email address)
  - SMTP_PASSWORD (app password)
  - SMTP_FROM_EMAIL (noreply@platform.com)
- For development: use Mailtrap or Gmail with app password
- For production: use SendGrid, AWS SES, or Mailgun
- Test with: `python manage.py shell` → `from django.core.mail import send_mail`

---

#### TASK-1.19: Create API documentation for registration endpoint

**Type**: Infrastructure - Documentation
**Priority**: P0
**Estimated Effort**: 3 hours

##### Description

Generate comprehensive API documentation for the registration endpoint using OpenAPI (Swagger) specification. Documentation should include endpoint URL, HTTP method, request schema, response schemas (success and error), example requests/responses, authentication requirements (none), and rate limiting information. Use drf-spectacular or drf-yasg to auto-generate documentation from DRF code with additional manual annotations.

##### Files Impacted

- `backend/requirements.txt` (modified - add drf-spectacular)
- `backend/config/settings.py` (modified - configure spectacular)
- `backend/config/urls.py` (modified - add schema URLs)
- `backend/apps/authentication/views.py` (modified - add API schema decorators)
- `docs/api/authentication.md` (new)

##### Acceptance Criteria

- [ ] drf-spectacular installed and configured
- [ ] OpenAPI schema accessible at /api/schema/
- [ ] Swagger UI accessible at /api/docs/
- [ ] Registration endpoint documented with full details
- [ ] Request schema includes all fields with types and validation rules
- [ ] Success response (201) documented with example
- [ ] Error responses (400, 409, 429) documented with examples
- [ ] Rate limiting noted in documentation (5 requests/hour/IP)
- [ ] Markdown documentation created in docs/api/authentication.md
- [ ] Documentation includes curl examples

##### Dependencies

- TASK-1.6 (registration endpoint must be implemented)

##### Implementation Notes

- Add to requirements.txt: drf-spectacular>=0.26
- Configure in settings.py: REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS']
- Add schema decorators to view:
  ```python
  @extend_schema(
      request=UserRegistrationSerializer,
      responses={201: UserRegistrationSerializer, 400: ErrorSerializer},
      description="Register new user account"
  )
  ```
- Include schema URLs: path('api/schema/', SpectacularAPIView.as_view())
- Include Swagger UI: path('api/docs/', SpectacularSwaggerView.as_view())
- Generate static schema: `python manage.py spectacular --file docs/api/openapi.yaml`

---

## Dependency Graph

### Mermaid Diagram

```mermaid
graph TD
    TASK1.1[1.1: CustomUser Model] --> TASK1.2[1.2: Configure Allauth]
    TASK1.1 --> TASK1.3[1.3: Argon2 Hashing]
    TASK1.3 --> TASK1.4[1.4: Password Validators]
    TASK1.1 --> TASK1.5[1.5: Registration Serializer]
    TASK1.4 --> TASK1.5
    TASK1.5 --> TASK1.6[1.6: Registration Endpoint]
    TASK1.7[1.7: Celery Setup] --> TASK1.8[1.8: Email Service]
    TASK1.6 --> TASK1.9[1.9: Rate Limiting]
    TASK1.6 --> TASK1.10[1.10: Registration Form]
    TASK1.10 --> TASK1.12[1.12: Registration Page]
    TASK1.11[1.11: Password Strength] --> TASK1.12
    TASK1.6 --> TASK1.13[1.13: API Service]
    TASK1.13 --> TASK1.14[1.14: Alert Component]
    TASK1.5 --> TASK1.15[1.15: Unit Tests]
    TASK1.6 --> TASK1.15
    TASK1.6 --> TASK1.16[1.16: Integration Tests]
    TASK1.8 --> TASK1.16
    TASK1.9 --> TASK1.17[1.17: Security Tests]
    TASK1.6 --> TASK1.19[1.19: API Documentation]
```

### Implementation Phases

**Phase 1: Backend Foundation (Days 1-2)**
- TASK-1.1: CustomUser Model → 3h
- TASK-1.2: Configure Allauth → 2h
- TASK-1.3: Argon2 Hashing → 2h
- TASK-1.18: SMTP Configuration → 2h
- TASK-1.7: Celery Setup → 3h

**Phase 2: Backend Core Logic (Days 2-3)**
- TASK-1.4: Password Validators → 3h
- TASK-1.5: Registration Serializer → 4h
- TASK-1.6: Registration Endpoint → 4h
- TASK-1.8: Email Service → 4h
- TASK-1.9: Rate Limiting → 3h

**Phase 3: Frontend Development (Days 3-4)**
- TASK-1.11: Password Strength Indicator → 3h (parallel)
- TASK-1.10: Registration Form → 5h
- TASK-1.13: API Service → 3h
- TASK-1.14: Alert Component → 2h
- TASK-1.12: Registration Page → 4h

**Phase 4: Testing & Documentation (Days 5-6)**
- TASK-1.15: Unit Tests → 4h
- TASK-1.16: Integration Tests → 5h
- TASK-1.17: Security Tests → 4h
- TASK-1.19: API Documentation → 3h

### Parallelization Opportunities

**Backend and Frontend (after TASK-1.6)**:
- Backend: TASK-1.8, TASK-1.9 (email + rate limiting)
- Frontend: TASK-1.10, TASK-1.11, TASK-1.13 (form + password strength + API service)
- Can be done by separate developers simultaneously

**Testing (after core implementation)**:
- TASK-1.15, TASK-1.16, TASK-1.17 can be worked on in parallel
- Different test types by different developers

**Infrastructure (anytime)**:
- TASK-1.18 (SMTP) can be done early or in parallel
- TASK-1.19 (Documentation) can be done after TASK-1.6 completes

---

## Effort Estimation

### By Task Type

| Type | Tasks | Effort | Percentage |
|------|-------|--------|------------|
| Backend | 9 | 28h | 46% |
| Frontend | 5 | 17h | 28% |
| Testing | 3 | 13h | 21% |
| Infrastructure | 2 | 5h | 8% |
| **TOTAL** | **19** | **63h** | **100%** |

### By Developer

**Single Full-Stack Developer**:
- Sequential execution: 63 hours
- 8-hour days: ~8 days
- With overhead and testing: 10 days

**Two Developers (Backend + Frontend)**:
- Backend developer: 28h (backend) + 13h (testing) = 41h = ~5 days
- Frontend developer: 17h (frontend) + 5h (infrastructure) = 22h = ~3 days
- Critical path: Backend → Testing = 5 days
- With coordination and integration: 6 days

**Recommended Approach**:
- Days 1-2: Backend foundation (1 dev)
- Days 3-4: Backend + Frontend in parallel (2 devs)
- Days 5-6: Testing + Documentation (1-2 devs)
- Total: 6 days with 2 developers

---

## Implementation Notes

### Technology Stack

**Backend**:
- Django 4.2+ with Django REST Framework 3.14+
- Python 3.11+
- PostgreSQL 15+ (via Supabase)
- Redis 7+ (Celery broker + rate limiting)
- Celery 5.2+ for async tasks
- django-allauth 0.54+ for auth flows
- argon2-cffi 21.0+ for password hashing
- django-ratelimit 4.0+ for rate limiting

**Frontend**:
- React 18+ with functional components and hooks
- React Router 6+ for navigation
- Axios for HTTP requests
- CSS Modules for styling

**Development Tools**:
- pytest + pytest-django for backend testing
- factory_boy for test data generation
- drf-spectacular for API documentation

### Patterns and Conventions

**Backend**:
- Use class-based views (APIView or generics)
- Serializers for all input/output validation
- Custom managers for model methods
- Shared Celery tasks in tasks.py
- All configuration from environment variables

**Frontend**:
- Functional components with hooks
- Custom hooks for reusable logic (useFormValidation)
- CSS Modules for component styling
- API services in services/ directory
- Environment variables with REACT_APP_ prefix

**Testing**:
- Unit tests for individual functions/components
- Integration tests for API endpoints
- Security tests for vulnerabilities
- >80% code coverage target
- Fast test execution (<10s for unit tests)

### Configuration Requirements

**Environment Variables Required**:
```bash
# Django
SECRET_KEY=<secure-random-key>
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@platform.com

# Frontend
FRONTEND_URL=http://localhost:3000

# JWT (for future US-3)
JWT_SECRET_KEY=<separate-jwt-key>
```

**Docker Compose Services**:
- db (PostgreSQL)
- redis
- backend (Django)
- frontend (React)
- worker (Celery)

---

## Risks and Attention Points

### Identified Risks

**1. Email Delivery Reliability (HIGH IMPACT)**
- **Risk**: SMTP service unavailable or emails not delivered
- **Impact**: Users cannot verify accounts, blocking onboarding
- **Mitigation**:
  - Use reliable SMTP provider (SendGrid, AWS SES)
  - Implement Celery retry logic (3 attempts, exponential backoff)
  - Queue failed emails for manual review
  - Monitor email delivery metrics
- **Contingency**: Manual verification by admin if needed

**2. Rate Limiting Bypass (MEDIUM IMPACT)**
- **Risk**: Attackers bypass IP-based rate limiting using proxies
- **Impact**: System abuse, database load, spam registrations
- **Mitigation**:
  - Store rate limit data in Redis (distributed)
  - Consider additional rate limiting (email-based, CAPTCHA)
  - Monitor for unusual registration patterns
  - Log all registration attempts with IP
- **Contingency**: Temporarily increase rate limits or add CAPTCHA

**3. Performance Under Load (MEDIUM IMPACT)**
- **Risk**: Registration endpoint exceeds 300ms P95 under load
- **Impact**: Poor user experience, failed acceptance criteria
- **Mitigation**:
  - Async email sending (non-blocking)
  - Database query optimization (indexes on email)
  - Redis for fast rate limit lookups
  - Load testing with 100+ concurrent requests
- **Contingency**: Horizontal scaling, caching, CDN

**4. Password Validation Complexity (LOW IMPACT)**
- **Risk**: Password requirements too strict, users frustrated
- **Impact**: High abandonment rate on registration
- **Mitigation**:
  - Balance security vs. usability
  - Real-time feedback with password strength indicator
  - Clear error messages explaining requirements
  - Special characters recommended, not required
- **Contingency**: Adjust validation rules based on user feedback

### Critical Points

**Security**:
- Never log passwords (even hashed) in application logs
- Never return password in API responses (use write_only=True)
- Validate all inputs (email format, password strength, field lengths)
- Test for SQL injection and XSS vulnerabilities
- Rate limit aggressively to prevent brute force

**Performance**:
- Email sending MUST be async (Celery) to meet 300ms target
- Database indexes on email field for fast uniqueness checks
- Redis for fast rate limit lookups
- Connection pooling for database under load

**User Experience**:
- Real-time validation feedback (don't wait for submit)
- Clear, actionable error messages
- Password strength indicator guides users
- Responsive design for mobile users
- Accessibility for screen readers (ARIA labels)

**Testing**:
- Test all error paths, not just happy path
- Security tests for common vulnerabilities
- Load testing to verify performance targets
- Test email sending (use Mailtrap in development)

---

## Verification Checklist

Before marking US-1 as complete, verify:

### Functional Requirements
- [ ] User can register with email and password
- [ ] Email validation enforces valid format
- [ ] Password requirements enforced (8 chars, uppercase, lowercase, number)
- [ ] Passwords hashed with Argon2
- [ ] Duplicate email rejected with clear error message
- [ ] Verification email sent within 30 seconds
- [ ] Account created with is_active=False, is_email_verified=False
- [ ] Real-time validation feedback in UI
- [ ] Registration endpoint responds <300ms (P95)

### Security Requirements
- [ ] Rate limiting: 5 attempts per IP per hour enforced
- [ ] Passwords never logged or exposed
- [ ] Password hashing verified (Argon2)
- [ ] SQL injection tests pass
- [ ] XSS tests pass

### Testing Requirements
- [ ] Unit tests written (>80% coverage)
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Manual testing completed

### Documentation Requirements
- [ ] API documentation complete (OpenAPI/Swagger)
- [ ] Code comments added
- [ ] Setup guide updated (SMTP configuration)
- [ ] README updated if needed

### Performance Requirements
- [ ] Registration endpoint <300ms P95
- [ ] System handles 100+ concurrent registrations
- [ ] Email sending non-blocking

### UI/UX Requirements
- [ ] Responsive on mobile/tablet/desktop
- [ ] Error messages clear and actionable
- [ ] Accessibility standards met (WCAG 2.1 Level AA)
- [ ] Success message displayed after registration

---

## Next Steps After Completion

1. **Code Review**: Submit pull request for peer review
2. **QA Testing**: Deploy to staging for QA verification
3. **Performance Testing**: Load test with 100+ concurrent users
4. **Security Review**: Have security team review implementation
5. **Documentation Review**: Ensure all docs are up to date
6. **Proceed to US-2**: Email Verification (depends on US-1)

---

**Generated**: 2025-10-28
**Version**: 1.0
**Status**: Ready for Implementation
**Estimated Completion**: 6-8 days (1 full-stack developer)
