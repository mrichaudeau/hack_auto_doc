# User Registration Workflow

Complete guide for the user registration process in the Technology Watch Platform.

## Table of Contents

1. [Overview](#overview)
2. [User Journey](#user-journey)
3. [Step-by-Step Process](#step-by-step-process)
4. [Technical Flow](#technical-flow)
5. [Email Verification](#email-verification)
6. [Error Scenarios](#error-scenarios)
7. [User Experience Considerations](#user-experience-considerations)

## Overview

The registration workflow allows new users to create an account on the Technology Watch Platform. The process includes:

- **Client-side validation** for immediate feedback
- **Server-side validation** for security and data integrity
- **Email verification** for account activation
- **Rate limiting** to prevent abuse
- **Secure password storage** using Argon2 hashing

**Registration Status:**
- ✅ Implemented (US-1)
- 🚀 Production-ready
- 📧 Email verification pending (future US)

## User Journey

```
┌─────────────┐
│  Landing    │
│    Page     │──> Click "Get Started"
└─────────────┘
       │
       ▼
┌─────────────┐
│Registration │
│    Form     │──> Fill in details
└─────────────┘
       │
       ▼
┌─────────────┐
│  Validation │
│ & Submit    │──> Real-time validation
└─────────────┘
       │
       ▼
┌─────────────┐
│   Success   │
│   Message   │──> "Check your email"
└─────────────┘
       │
       ▼
┌─────────────┐
│Email Verify │
│    Page     │──> Waiting for verification
└─────────────┘
```

## Step-by-Step Process

### Step 1: Access Registration Page

**User Actions:**
1. Navigate to http://localhost:3000 (or production URL)
2. Click the "Get Started" button on the homepage

**System Response:**
- Redirects to `/register`
- Displays registration form with:
  - Email field (required)
  - Password field (required)
  - Confirm Password field (required)
  - First Name field (optional)
  - Last Name field (optional)

**Visual Design:**
- Purple gradient background
- White card containing form
- Clean, professional interface
- Responsive design for all devices

### Step 2: Fill in Registration Details

**Required Fields:**

1. **Email Address**
   - Format: valid email (RFC 5322)
   - Max length: 254 characters
   - Must be unique (not already registered)
   - Example: `user@example.com`

2. **Password**
   - Minimum 8 characters
   - Must contain at least one uppercase letter (A-Z)
   - Must contain at least one lowercase letter (a-z)
   - Must contain at least one number (0-9)
   - Recommended: Special character (!@#$%^&*...)
   - Example: `TestPassword123`

3. **Confirm Password**
   - Must exactly match the password field
   - Real-time validation on blur

**Optional Fields:**

4. **First Name**
   - Max length: 150 characters
   - Accepts letters, spaces, hyphens, apostrophes
   - Example: `John`

5. **Last Name**
   - Max length: 150 characters
   - Accepts letters, spaces, hyphens, apostrophes
   - Example: `Doe`

### Step 3: Real-Time Validation

**As User Types:**

1. **Email Field:**
   - ✓ Green border when valid email format
   - ✗ Red border with error message when invalid
   - Error: "Please enter a valid email address"

2. **Password Field:**
   - Password strength indicator appears
   - Shows 5 requirements with checkmarks:
     - ✓ At least 8 characters
     - ✓ Contains uppercase letter (A-Z)
     - ✓ Contains lowercase letter (a-z)
     - ✓ Contains number (0-9)
     - ○ Contains special character (Optional)
   - Color-coded strength:
     - 🔴 Weak (0-2 requirements met)
     - 🟡 Medium (3 requirements met)
     - 🟢 Strong (4+ requirements met)

3. **Confirm Password Field:**
   - ✓ Green border when passwords match
   - ✗ Red border when passwords don't match
   - Error: "Passwords do not match"

4. **Name Fields:**
   - ✓ Green border when valid (after first input)
   - ✗ Red border if exceeds 150 characters

### Step 4: Submit Registration

**User Actions:**
1. Click "Create Account" button

**Client-Side Processing:**
1. Validates all fields
2. Disables submit button (prevents double-submit)
3. Shows loading state: "Creating Account..."
4. Sends POST request to `/api/auth/register/`

**Server-Side Processing:**
1. Validates request data
2. Checks rate limit (5 requests/hour/IP)
3. Validates email uniqueness
4. Validates password strength
5. Hashes password with Argon2
6. Creates user account:
   - `is_active`: false (awaiting verification)
   - `is_verified`: false
   - `date_joined`: current timestamp
7. Creates email verification token
8. Queues async email task (Celery)
9. Returns success response

### Step 5: Success Confirmation

**System Response:**
- Success alert appears:
  - Type: Success (green)
  - Message: "Registration successful! Please check your email to verify your account."
  - Auto-dismiss: After 2 seconds
- After 2 seconds:
  - Redirects to `/verify-email`
  - Passes email address in route state

**Verify Email Page:**
- Displays success icon (checkmark)
- Shows message: "We've sent a verification email to [user@example.com]"
- Instructions: "Please check your inbox and click the verification link"
- "Resend Verification Email" button (disabled - future feature)
- "Back to Home" link

### Step 6: Email Verification (Future)

**Current Implementation:**
- Email task is queued but not sent (console backend)
- Token generated and stored in database
- Verification endpoint not yet implemented

**Future Implementation:**
1. User receives email with verification link
2. User clicks link
3. System validates token
4. Account activated:
   - `is_active`: true
   - `is_verified`: true
   - `email_verified_at`: current timestamp
5. Redirect to login page

## Technical Flow

### Frontend Flow

```javascript
// 1. User submits form
handleSubmit(formData) {
  // 2. Validate all fields
  if (!validateForm()) return;

  // 3. Call API
  const result = await authService.register(formData);

  // 4. Handle success
  if (result.success) {
    showSuccessAlert(result.data.message);
    setTimeout(() => {
      navigate('/verify-email', {
        state: { email: formData.email }
      });
    }, 2000);
  }

  // 5. Handle errors
  else {
    showErrorAlert(result.error);
  }
}
```

### Backend Flow

```python
# 1. Receive request
POST /api/auth/register/

# 2. Rate limit check (django-ratelimit)
@ratelimit(key='ip', rate='5/h', method='POST')

# 3. Validate serializer
serializer = UserRegistrationSerializer(data=request.data)
serializer.is_valid(raise_exception=True)

# 4. Create user
user = CustomUser.objects.create_user(
    email=validated_data['email'],
    password=validated_data['password'],
    first_name=validated_data.get('first_name', ''),
    last_name=validated_data.get('last_name', ''),
    is_active=False,  # Requires email verification
    is_verified=False
)

# 5. Create verification token
token = EmailVerificationToken.create_token(user)

# 6. Queue email task (async)
send_verification_email.delay(user.id, str(token.token))

# 7. Return response
return Response({
    'id': user.id,
    'email': user.email,
    'message': 'Registration successful. Please check your email...'
}, status=status.HTTP_201_CREATED)
```

### Database Changes

```sql
-- User record created
INSERT INTO users (
    id, email, password, first_name, last_name,
    is_active, is_verified, date_joined
) VALUES (
    'uuid-here',
    'user@example.com',
    'argon2$argon2id$v=19$m=102400,t=2,p=8$...',
    'John',
    'Doe',
    false,
    false,
    '2025-11-04 22:00:00'
);

-- Verification token created
INSERT INTO email_verification_tokens (
    id, user_id, token, created_at, expires_at, is_used
) VALUES (
    'token-uuid',
    'user-uuid',
    'verification-token-uuid',
    '2025-11-04 22:00:00',
    '2025-11-05 22:00:00',  -- 24 hours later
    false
);
```

## Email Verification

### Verification Email Content

**Subject:** Verify Your Email Address - Tech Watch Platform

**Body:**
```
Hi John,

Thank you for registering with Tech Watch Platform!

Please verify your email address by clicking the link below:

[Verify Email Address]
http://localhost:3000/verify-email/[token]

This link will expire in 24 hours.

If you didn't create this account, you can safely ignore this email.

Best regards,
Tech Watch Platform Team
```

### Verification Process (Future Implementation)

1. **User clicks verification link**
   - Link format: `/verify-email/[token]`
   - Frontend extracts token from URL

2. **Frontend sends verification request**
   ```javascript
   POST /api/auth/verify-email/
   {
     "token": "verification-token-uuid"
   }
   ```

3. **Backend validates token**
   - Checks token exists
   - Checks token not expired (< 24 hours)
   - Checks token not already used
   - Checks associated user exists

4. **Account activated**
   - Sets `is_active = true`
   - Sets `is_verified = true`
   - Sets `email_verified_at = now()`
   - Marks token as used

5. **Success response**
   - Returns success message
   - Frontend redirects to login page

## Error Scenarios

### 1. Invalid Email Format

**User Input:** `test@invalid`

**Response:**
- Status: 400 Bad Request
- Error message: "Please enter a valid email address"
- Field highlighted in red
- Error displayed below field

### 2. Weak Password

**User Input:** `abc123`

**Response:**
- Status: 400 Bad Request
- Error message: "Password must be at least 8 characters"
- Password strength indicator shows unmet requirements
- Field highlighted in red

### 3. Password Mismatch

**User Input:**
- Password: `TestPassword123`
- Confirm: `TestPassword456`

**Response:**
- Client-side validation (before submit)
- Error message: "Passwords do not match"
- Confirm password field highlighted in red

### 4. Duplicate Email

**User Input:** Email already registered

**Response:**
- Status: 409 Conflict
- Error message: "An account with this email already exists."
- Alert displayed at top of form
- Email field highlighted in red
- Link to login page shown

### 5. Rate Limit Exceeded

**Scenario:** 6th registration attempt within 1 hour from same IP

**Response:**
- Status: 429 Too Many Requests
- Error message: "Too many registration attempts. Please try again later."
- Alert displayed at top of form
- Submit button disabled temporarily

### 6. Missing Required Fields

**User Input:** Submit without email or password

**Response:**
- Status: 400 Bad Request
- Multiple error messages:
  - "Email is required"
  - "Password is required"
- All missing fields highlighted in red

### 7. Server Error

**Scenario:** Database connection failure or unexpected error

**Response:**
- Status: 500 Internal Server Error
- Error message: "An unexpected error occurred. Please try again later."
- Error logged on server for investigation
- User-friendly message (no technical details exposed)

## User Experience Considerations

### Progressive Enhancement

1. **Visual Feedback:**
   - Instant field validation on blur
   - Color-coded borders (green/red)
   - Clear error messages
   - Password strength indicator

2. **Loading States:**
   - Submit button shows "Creating Account..." during processing
   - Button disabled to prevent double-submit
   - Spinner or loading indicator

3. **Success Feedback:**
   - Success alert with auto-dismiss
   - Smooth transition to verify email page
   - Clear next steps communicated

### Accessibility

1. **ARIA Attributes:**
   - `aria-required="true"` on required fields
   - `aria-invalid="true"` on fields with errors
   - `aria-describedby` linking to error messages
   - `role="alert"` on error messages

2. **Keyboard Navigation:**
   - Tab order follows logical flow
   - Enter key submits form
   - Escape key dismisses alerts

3. **Screen Reader Support:**
   - Labels properly associated with inputs
   - Error messages announced
   - Success messages announced
   - Password requirements read

### Mobile Optimization

1. **Responsive Design:**
   - Form adapts to screen size
   - Touch-friendly button sizes (min 44x44px)
   - Readable font sizes (min 16px)
   - No horizontal scrolling

2. **Input Types:**
   - `type="email"` triggers email keyboard
   - `type="password"` masks input
   - `autocomplete` attributes for autofill

3. **Performance:**
   - Form validation debounced
   - Minimal bundle size
   - Fast API response times (<300ms)

### Security UX

1. **Password Visibility:**
   - Masked by default
   - Show/hide toggle (future enhancement)
   - Copy-paste allowed (for password managers)

2. **Error Messages:**
   - Informative but not too specific
   - No indication of whether email exists (security)
   - Generic error for server issues

3. **Rate Limiting Feedback:**
   - Clear message when limit reached
   - Indication of when user can retry
   - No specific IP information disclosed

## Next Steps After Registration

1. **Immediate:**
   - User redirected to verify email page
   - Email sent to user's inbox (async)
   - User can close browser (safe to continue later)

2. **Within 24 Hours:**
   - User receives verification email
   - User clicks verification link
   - Account activated
   - User can log in

3. **If Email Not Received:**
   - Check spam folder
   - Verify email address correct
   - Request new verification email (future feature)
   - Contact support if issues persist

## Integration Points

### Email Service

**Current:** Console email backend (development)
**Future:** SMTP service (production)

Configuration in `.env.backend`:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
DEFAULT_FROM_EMAIL=noreply@techwatch.local
```

### Celery Workers

**Purpose:** Async email sending
**Queue:** Celery with Redis broker
**Retry Logic:** 3 attempts with exponential backoff

### Rate Limiting

**Implementation:** django-ratelimit with Redis cache
**Limit:** 5 registrations per hour per IP
**Storage:** Redis (distributed across instances)

## Monitoring and Analytics

### Metrics to Track

1. **Registration Funnel:**
   - Page visits to `/register`
   - Form submissions
   - Successful registrations
   - Email verifications

2. **Error Rates:**
   - Validation errors by field
   - Duplicate email attempts
   - Rate limit hits
   - Server errors

3. **Performance:**
   - API response times
   - Email delivery times
   - Page load times

### Logging

Important events logged:
- User registration attempts (with IP)
- Successful registrations (user ID, email)
- Verification email sent (user ID, timestamp)
- Rate limit violations (IP, timestamp)
- Errors (with stack traces)

**Note:** Passwords are NEVER logged

## Future Enhancements

- [ ] Social authentication (Microsoft Entra ID)
- [ ] Password visibility toggle
- [ ] Resend verification email
- [ ] Email verification page with actual verification
- [ ] Account activation without email (admin override)
- [ ] CAPTCHA for bot prevention
- [ ] Progressive profiling (additional fields after registration)
- [ ] Welcome email after verification
- [ ] Registration analytics dashboard
