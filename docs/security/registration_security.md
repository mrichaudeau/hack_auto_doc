# Registration Security Considerations

Comprehensive security documentation for the user registration feature.

## Table of Contents

1. [Security Overview](#security-overview)
2. [OWASP Top 10 Protection](#owasp-top-10-protection)
3. [Password Security](#password-security)
4. [Input Validation](#input-validation)
5. [Rate Limiting](#rate-limiting)
6. [Data Protection](#data-protection)
7. [API Security](#api-security)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Testing](#security-testing)
10. [Incident Response](#incident-response)

## Security Overview

The registration system implements multiple layers of security to protect user data and prevent common attacks.

### Security Principles

1. **Defense in Depth:** Multiple security layers
2. **Least Privilege:** Minimal permissions by default
3. **Secure by Default:** Safe configuration out of the box
4. **Fail Securely:** Errors don't expose sensitive information
5. **Zero Trust:** Validate all inputs, never trust user data

### Threat Model

**Assets to Protect:**
- User credentials (emails, passwords)
- User personal information (names)
- System availability
- Database integrity

**Potential Threats:**
- Brute force attacks
- SQL injection
- XSS attacks
- CSRF attacks
- Rate limiting bypass
- Password cracking
- Information disclosure
- Account enumeration

### Security Status

✅ **Implemented:**
- Password hashing (Argon2)
- Input validation (client & server)
- Rate limiting (IP-based)
- SQL injection prevention (ORM)
- XSS prevention (Django templates)
- CSRF protection (Django)
- Secure password requirements

🚧 **Future Enhancements:**
- CAPTCHA for bot prevention
- Email verification enforcement
- Account lockout after failed attempts
- Two-factor authentication
- Security headers (CSP, HSTS)

## OWASP Top 10 Protection

### A01:2021 - Broken Access Control

**Risk:** Unauthorized access to user accounts

**Mitigation:**
1. **Email verification required** before account activation
   - `is_active=false` until email verified
   - Prevents access to authenticated endpoints

2. **JWT authentication** for API access
   - Short-lived access tokens (60 minutes)
   - Refresh tokens (7 days)
   - Tokens must be included in Authorization header

3. **No user enumeration**
   - Same error message for duplicate email and other errors
   - No indication if email already exists during registration

### A02:2021 - Cryptographic Failures

**Risk:** Sensitive data exposure

**Mitigation:**
1. **Argon2 password hashing**
   ```python
   PASSWORD_HASHERS = [
       'django.contrib.auth.hashers.Argon2PasswordHasher',
   ]
   ```
   - Memory-hard algorithm (resistant to GPU attacks)
   - Salt automatically generated per password
   - Configurable work factors

2. **No plaintext password storage**
   - Passwords hashed immediately on creation
   - Never logged or displayed
   - Not included in API responses

3. **Secure token generation**
   - UUID4 for verification tokens
   - Cryptographically secure random
   - 24-hour expiration

### A03:2021 - Injection

**Risk:** SQL injection, command injection

**Mitigation:**
1. **Django ORM** for database queries
   - Parameterized queries by default
   - Automatic escaping
   - No raw SQL in registration flow

2. **Input validation** before database operations
   - Email format validation
   - Length limits enforced
   - Special characters handled safely

3. **Test coverage** for injection attempts
   ```python
   # Test case: SQL injection in email
   email = "test@example.com' OR '1'='1"
   # Expected: 400 error, not SQL error
   ```

### A04:2021 - Insecure Design

**Risk:** Flawed security architecture

**Mitigation:**
1. **Secure by default configuration**
   - `is_active=false` for new users
   - Email verification required
   - Strong password policy enforced

2. **Rate limiting** built into design
   - IP-based limiting (5 requests/hour)
   - Distributed cache (Redis)
   - Cannot be bypassed by client

3. **Async email processing**
   - Non-blocking Celery tasks
   - Retry logic for failures
   - No email in synchronous path

### A05:2021 - Security Misconfiguration

**Risk:** Insecure default settings

**Mitigation:**
1. **Environment-based configuration**
   - Secrets in `.env.backend` (never committed)
   - Different settings for dev/prod
   - Debug mode off in production

2. **Secure Django settings**
   ```python
   DEBUG = False  # Production
   ALLOWED_HOSTS = ['techwatch.com']
   CORS_ALLOWED_ORIGINS = ['https://techwatch.com']
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

3. **Validation on startup**
   - Config validator checks critical settings
   - Application fails fast if misconfigured
   - Clear error messages for missing config

### A06:2021 - Vulnerable and Outdated Components

**Risk:** Security vulnerabilities in dependencies

**Mitigation:**
1. **Dependency management with Poetry**
   ```bash
   poetry update  # Regular updates
   poetry show --outdated  # Check for updates
   ```

2. **Current versions** (as of implementation)
   - Django: 5.2.7
   - djangorestframework: 3.16.1
   - django-ratelimit: 4.1.0
   - argon2-cffi: 23.1.0

3. **Security advisories** monitoring
   - GitHub Dependabot alerts enabled
   - Regular security patch updates
   - CVE monitoring for Python packages

### A07:2021 - Identification and Authentication Failures

**Risk:** Weak authentication implementation

**Mitigation:**
1. **Strong password policy**
   - Minimum 8 characters
   - Must contain uppercase, lowercase, number
   - Recommended: special characters
   - Enforced client and server-side

2. **No default credentials**
   - Superuser must be created manually
   - Strong password required for admin accounts

3. **Account lockout** (future)
   - After X failed login attempts
   - Temporary lockout period
   - Admin notification

### A08:2021 - Software and Data Integrity Failures

**Risk:** Unauthorized code/data modification

**Mitigation:**
1. **Input validation** at all layers
   - Client-side: Immediate feedback
   - Server-side: Security enforcement
   - Database: Constraints and indexes

2. **Atomic transactions**
   ```python
   from django.db import transaction

   @transaction.atomic
   def create_user_with_token(validated_data):
       user = User.objects.create(...)
       token = EmailVerificationToken.create_token(user)
       return user, token
   ```

3. **Data integrity checks**
   - Email uniqueness constraint
   - Token uniqueness constraint
   - Foreign key constraints

### A09:2021 - Security Logging and Monitoring Failures

**Risk:** Undetected security incidents

**Mitigation:**
1. **Comprehensive logging**
   ```python
   import logging
   logger = logging.getLogger(__name__)

   # Log registration attempts
   logger.info(f"Registration attempt from IP: {ip}")

   # Log successful registrations
   logger.info(f"User registered: {user.email}")

   # Log rate limit violations
   logger.warning(f"Rate limit exceeded: {ip}")
   ```

2. **No sensitive data in logs**
   - Passwords never logged
   - Tokens not logged (only user ID)
   - Email partially masked in production logs

3. **Monitoring endpoints**
   - Health check: `/api/health/`
   - Metrics: Rate limit hits, error rates
   - Alerts: Unusual registration patterns

### A10:2021 - Server-Side Request Forgery (SSRF)

**Risk:** Unauthorized requests from server

**Mitigation:**
1. **No user-controlled URLs** in registration flow
2. **Email validation** prevents URL injection
3. **Future considerations** for profile pictures:
   - Whitelist allowed domains
   - Validate file types
   - Scan for malware

## Password Security

### Password Hashing

**Algorithm:** Argon2id (OWASP recommended)

**Configuration:**
```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',  # Fallback
]
```

**Argon2 Parameters:**
- Memory cost: 102,400 KB (100 MB)
- Time cost: 2 iterations
- Parallelism: 8 threads
- Salt: 16 bytes (auto-generated)

**Hash Example:**
```
argon2$argon2id$v=19$m=102400,t=2,p=8$c2FsdGhlcmU$hash_output
```

### Password Requirements

**Enforced Rules:**
1. Minimum 8 characters
2. At least one uppercase letter (A-Z)
3. At least one lowercase letter (a-z)
4. At least one number (0-9)
5. Recommended: Special character (!@#$%^&*...)

**Validation Implementation:**
```python
# Server-side
class PasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Minimum 8 characters required")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Uppercase letter required")
        # ... additional checks
```

**Password Strength Estimation:**
- Entropy calculation based on character sets
- Visual feedback (weak/medium/strong)
- Real-time updates as user types

### Password Storage Best Practices

**✅ DO:**
- Hash passwords with Argon2
- Use unique salt per password
- Store only hashed passwords
- Update hash on password change
- Use slow hashing algorithm

**❌ DON'T:**
- Store plaintext passwords
- Log passwords (even hashed)
- Display passwords in UI
- Send passwords via email
- Reuse salts

### Password Reset Security (Future)

**Secure Reset Flow:**
1. User requests reset (email only, no hints)
2. Token sent to email (single-use, time-limited)
3. Token validated server-side
4. New password set (re-hashed)
5. Invalidate all existing sessions
6. Notify user of password change

## Input Validation

### Validation Layers

**1. Client-Side Validation:**
- Purpose: User experience
- Implementation: React validators
- Security: Not trusted, can be bypassed

**2. Server-Side Validation:**
- Purpose: Security enforcement
- Implementation: Django serializers
- Security: Always enforced, never skipped

**3. Database Validation:**
- Purpose: Data integrity
- Implementation: Model constraints
- Security: Last line of defense

### Email Validation

**Format Validation:**
```python
# Regex pattern (simplified RFC 5322)
r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

# Django EmailValidator
from django.core.validators import EmailValidator
validator = EmailValidator(message="Invalid email format")
```

**Additional Checks:**
- Length limit: 254 characters
- Domain has valid TLD
- No special characters in local part (configurable)

**Normalized Form:**
- Lowercase domain: `User@EXAMPLE.com` → `User@example.com`
- Trim whitespace
- Reject if empty

### Password Validation

**Server-Side Checks:**
```python
def validate_password(password):
    validators = [
        MinimumLengthValidator(min_length=8),
        UppercaseValidator(),
        LowercaseValidator(),
        NumberValidator(),
    ]
    for validator in validators:
        validator.validate(password)
```

**Special Cases Handled:**
- Unicode characters allowed
- Whitespace allowed (but not recommended)
- Very long passwords (max 128 characters)

### Name Validation

**Allowed Characters:**
- Letters (a-z, A-Z)
- Spaces
- Hyphens (-)
- Apostrophes (')
- Accented characters (é, ñ, ü)

**Length Limits:**
- Minimum: 0 characters (optional field)
- Maximum: 150 characters

**Sanitization:**
- Trim leading/trailing whitespace
- Normalize multiple spaces to single space
- HTML escape for display (XSS prevention)

### Input Sanitization

**HTML Escaping:**
```python
from django.utils.html import escape
safe_name = escape(user_input)
```

**SQL Injection Prevention:**
```python
# ✅ Good: ORM with parameters
User.objects.filter(email=user_email)

# ❌ Bad: Raw SQL with string concatenation
cursor.execute(f"SELECT * FROM users WHERE email='{user_email}'")
```

**Command Injection Prevention:**
- No shell commands with user input
- Subprocess calls avoided
- If necessary: Use `shlex.quote()` for escaping

## Rate Limiting

### Implementation

**Library:** `django-ratelimit`

**Configuration:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/h', method='POST', block=False)
class UserRegistrationView(generics.CreateAPIView):
    ...
```

**Parameters:**
- **key:** `ip` (rate limit per IP address)
- **rate:** `5/h` (5 requests per hour)
- **method:** `POST` (only limit POST requests)
- **block:** `False` (return 429, don't block request)

### Rate Limit Storage

**Backend:** Redis cache

**Configuration:**
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

**Advantages:**
- Distributed: Works across multiple backend instances
- Fast: In-memory storage
- Atomic: Thread-safe operations
- Persistent: Survives backend restarts

### Rate Limit Response

**HTTP Status:** 429 Too Many Requests

**Response Body:**
```json
{
  "error": "Too many registration attempts. Please try again later."
}
```

**Headers:**
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699200000
Retry-After: 3600
```

### Bypass Prevention

**IP Spoofing Protection:**
- Use `X-Forwarded-For` header carefully
- Validate against trusted proxies only
- Consider using REMOTE_ADDR as fallback

**VPN/Proxy Consideration:**
- Rate limit may affect legitimate users behind NAT
- Consider adjusting limits for production
- Monitor false positives

### Rate Limit Tuning

**Current Limits:**
- Registration: 5 per hour per IP

**Recommended Adjustments:**
- Development: Disable or increase (10/hour)
- Staging: Same as production
- Production: Consider decreasing (3/hour)

**Monitoring:**
- Track rate limit hits
- Analyze patterns (bots vs. users)
- Adjust based on abuse attempts

## Data Protection

### Data Minimization

**Collected Data:**
- Email (required, for authentication)
- Password (required, never stored in plaintext)
- First Name (optional, for personalization)
- Last Name (optional, for personalization)

**Not Collected:**
- Phone number
- Address
- Date of birth
- Payment information (not at registration)

### Data Encryption

**In Transit:**
- HTTPS enforced (TLS 1.2+)
- HSTS header in production
- No mixed content

**At Rest:**
- Database encryption (PostgreSQL)
- Passwords hashed (Argon2)
- Tokens encrypted (UUID4)

**Configuration (Production):**
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### Data Retention

**User Data:**
- Retained while account active
- Deleted on account deletion request
- Anonymized for analytics

**Verification Tokens:**
- Expired tokens deleted after 30 days
- Used tokens deleted immediately after verification

**Logs:**
- Registration logs: 90 days
- Error logs: 1 year
- Audit logs: 7 years (compliance)

### GDPR Compliance

**User Rights:**
1. **Right to Access:** API endpoint for user data export
2. **Right to Erasure:** Account deletion with data purge
3. **Right to Rectification:** Profile update endpoints
4. **Right to Data Portability:** JSON export format

**Implementation:**
```python
# DELETE /api/account/
def delete_account(request):
    user = request.user
    user.delete()  # Cascade deletes all related data
    return Response(status=204)
```

## API Security

### Authentication

**Method:** JWT (JSON Web Tokens)

**Implementation:**
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}
```

**Token Lifetime:**
- Access token: 60 minutes
- Refresh token: 7 days

### CORS Configuration

**Allowed Origins:**
```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Development
    'https://techwatch.com',  # Production
]
```

**Allowed Methods:**
```python
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS',
]
```

### CSRF Protection

**Protection Enabled:**
```python
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',
]
```

**API Exemption:**
- Registration endpoint exempt (public)
- JWT authentication used instead
- CSRF token required for cookie-based auth

### Content Security Policy (Future)

**Recommended Headers:**
```python
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]  # Minimize inline
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
CSP_IMG_SRC = ["'self'", "data:", "https:"]
CSP_CONNECT_SRC = ["'self'", "https://api.techwatch.com"]
```

## Monitoring and Logging

### Security Events to Log

**1. Authentication Events:**
- Registration attempts (IP, timestamp)
- Successful registrations (user ID, email)
- Email verification attempts
- Failed login attempts (future)

**2. Security Violations:**
- Rate limit exceeded (IP, count)
- Invalid input detected (type, value)
- Potential injection attempts
- Suspicious patterns

**3. System Events:**
- Configuration changes
- Database migrations
- Service restarts
- Error rates

### Log Format

**Structured Logging (JSON):**
```json
{
  "timestamp": "2025-11-04T22:00:00Z",
  "level": "INFO",
  "event": "user_registered",
  "user_id": "uuid",
  "email": "u***@example.com",
  "ip": "203.0.113.1",
  "user_agent": "Mozilla/5.0..."
}
```

**Benefits:**
- Parseable by log aggregators
- Searchable and filterable
- Standardized format

### Log Security

**✅ DO:**
- Log security events
- Include context (IP, timestamp)
- Mask sensitive data
- Use appropriate log levels
- Rotate logs regularly

**❌ DON'T:**
- Log passwords (even hashed)
- Log full tokens
- Log credit card numbers
- Log personal identifiable information
- Log in production debug mode

### Monitoring Alerts

**Critical Alerts:**
- Sudden spike in registrations (>50/minute)
- Rate limit violations (>100/hour)
- Repeated failed validations
- Database connection errors

**Warning Alerts:**
- Elevated error rate (>1%)
- Slow response times (>1s)
- High memory usage (>80%)
- Disk space low (<10%)

## Security Testing

### Testing Strategy

**1. Unit Tests:** Component-level security
**2. Integration Tests:** End-to-end flows
**3. Security Tests:** Specific attack scenarios
**4. Penetration Tests:** Manual testing
**5. Code Review:** Peer review for security

### Automated Security Tests

**15 Security Test Cases:**

1. Rate limiting enforcement
2. SQL injection prevention
3. XSS prevention
4. Password hashing verification
5. Password not in logs
6. Password not in responses
7. Duplicate email handling
8. Very long input rejection
9. Special characters handling
10. CSRF token validation
11. Information disclosure prevention
12. Token expiration
13. Token reuse prevention
14. Input sanitization
15. Error message safety

**Run Tests:**
```bash
pytest apps/accounts/tests/test_security.py -v
```

### Manual Security Testing

**Checklist:**
- [ ] Try SQL injection payloads
- [ ] Test XSS vectors
- [ ] Verify rate limiting
- [ ] Check password hashing
- [ ] Test error messages
- [ ] Verify HTTPS enforcement
- [ ] Check CORS configuration
- [ ] Test authentication bypass
- [ ] Verify authorization checks
- [ ] Test session handling

## Incident Response

### Security Incident Types

**1. Data Breach:**
- Unauthorized access to user data
- Database compromise
- Credentials leaked

**2. Service Abuse:**
- Automated registration attacks
- Rate limiting bypass
- Resource exhaustion

**3. Vulnerability Discovery:**
- Security researcher report
- Internal audit finding
- Automated scan detection

### Response Plan

**1. Detection:**
- Monitor logs for suspicious activity
- Alert on security events
- User reports

**2. Containment:**
- Isolate affected systems
- Block malicious IPs
- Revoke compromised tokens

**3. Investigation:**
- Analyze logs
- Identify scope
- Determine root cause

**4. Remediation:**
- Apply security patches
- Update configurations
- Deploy fixes

**5. Recovery:**
- Restore normal operations
- Verify system integrity
- Monitor for recurrence

**6. Lessons Learned:**
- Document incident
- Update procedures
- Improve detection

### Contact Information

**Security Team:**
- Email: security@techwatch.com
- PGP Key: [Link to public key]
- Response Time: 24 hours

**Responsible Disclosure:**
- Report vulnerabilities privately
- Allow 90 days for fix
- Coordinate public disclosure

## Security Checklist

### Pre-Deployment

- [ ] All tests passing (including security tests)
- [ ] Dependencies up to date
- [ ] Secrets in environment variables
- [ ] Debug mode disabled
- [ ] HTTPS enforced
- [ ] Rate limiting configured
- [ ] Logging enabled
- [ ] Monitoring alerts set up
- [ ] Backup strategy in place
- [ ] Incident response plan documented

### Post-Deployment

- [ ] Monitor error rates
- [ ] Review security logs
- [ ] Check rate limit effectiveness
- [ ] Verify email delivery
- [ ] Test from external network
- [ ] Run security scan
- [ ] Update documentation
- [ ] Train support team

### Regular Maintenance

**Monthly:**
- [ ] Review security logs
- [ ] Update dependencies
- [ ] Run security tests
- [ ] Check for CVEs

**Quarterly:**
- [ ] Security audit
- [ ] Penetration testing
- [ ] Update threat model
- [ ] Review access controls

**Annually:**
- [ ] External security assessment
- [ ] Compliance review
- [ ] Update security policies
- [ ] Team security training

## References

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Django Security Documentation](https://docs.djangoproject.com/en/5.0/topics/security/)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
