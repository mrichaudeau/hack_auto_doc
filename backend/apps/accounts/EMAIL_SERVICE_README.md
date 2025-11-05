# Email Service Integration (TASK-2.6)

## Overview

The email service integration provides robust, asynchronous email sending capabilities for user account operations. All emails are sent via Celery tasks to prevent blocking HTTP requests and provide automatic retry logic for transient failures.

## Features

- **Asynchronous Email Sending**: All emails sent via Celery tasks by default
- **Automatic Retries**: 3 retry attempts with exponential backoff (1 minute delay)
- **HTML + Plain Text**: All emails include both HTML and plain text versions
- **Responsive Design**: HTML emails are mobile-friendly (max-width: 600px)
- **Professional Branding**: Tech Watch Platform branding in all emails
- **Secure Links**: Verification and password reset links with expiry times
- **Error Handling**: Graceful failure handling with detailed logging

## Email Types

### 1. Verification Email

Sent when a new user registers to verify their email address.

**Features:**
- Clear call-to-action button
- Alternative text link for clients that don't support buttons
- 24-hour expiry warning
- Professional branding

**Usage:**
```python
from apps.accounts.models import CustomUser, EmailVerificationToken
from apps.accounts.email import send_verification_email

user = CustomUser.objects.get(email='user@example.com')
token = EmailVerificationToken.create_token(user)
success = send_verification_email(user, token)
```

**Template:** `backend/apps/accounts/templates/accounts/emails/verify_email.html`

**Link Format:** `{FRONTEND_URL}/verify-email?token={token}`

### 2. Welcome Email

Sent after successful email verification to welcome users to the platform.

**Usage:**
```python
from apps.accounts.models import CustomUser
from apps.accounts.email import send_welcome_email

user = CustomUser.objects.get(email='user@example.com')
success = send_welcome_email(user)
```

**Template:** `backend/apps/accounts/templates/accounts/emails/welcome.html`

### 3. Password Reset Email

Sent when a user requests a password reset.

**Features:**
- 1-hour expiry warning
- Clear instructions for password reset

**Usage:**
```python
from apps.accounts.models import CustomUser
from apps.accounts.email import send_password_reset_email

user = CustomUser.objects.get(email='user@example.com')
reset_token = 'generated-reset-token'
success = send_password_reset_email(user, reset_token)
```

**Template:** `backend/apps/accounts/templates/accounts/emails/password_reset.html`

**Link Format:** `{FRONTEND_URL}/reset-password?token={reset_token}`

## Configuration

### Django Settings

All email configuration is centralized in `backend/veille_tech/settings/base.py`:

```python
# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=1025, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@techwatch.local')

# Frontend URL for email links
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')
```

### Environment Variables

Configure email settings in `.env.backend`:

```bash
# Development (console backend - prints to console)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=False
DEFAULT_FROM_EMAIL=noreply@techwatch.local
FRONTEND_URL=http://localhost:3000

# Production (SMTP backend - actual email sending)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@yourcompany.com
FRONTEND_URL=https://app.yourcompany.com
```

### Email Backend Options

1. **Console Backend** (Development)
   - Prints emails to console
   - No SMTP server required
   - Perfect for local development

   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   ```

2. **SMTP Backend** (Production)
   - Sends real emails via SMTP
   - Requires SMTP server credentials
   - Use with EMAIL_USE_TLS=True for security

   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   ```

3. **File Backend** (Testing)
   - Saves emails to files
   - Useful for testing without SMTP

   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
   EMAIL_FILE_PATH = '/tmp/app-emails'
   ```

4. **In-Memory Backend** (Unit Tests)
   - Stores emails in memory (mail.outbox)
   - Perfect for unit tests

   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
   ```

## Celery Integration

All email sending is done asynchronously via Celery tasks for better performance and reliability.

### Celery Tasks

Located in `backend/apps/accounts/tasks.py`:

- `send_verification_email(user_id, token)` - Send verification email
- `send_welcome_email(user_id)` - Send welcome email
- `send_password_reset_email(user_id, reset_token)` - Send password reset email

### Task Configuration

- **Max Retries**: 3 attempts
- **Retry Delay**: 60 seconds (exponential backoff)
- **Retry Strategy**: Automatic retry on transient failures
- **Queue**: Default queue (priority 5)

### Monitoring Celery Tasks

```bash
# View Celery worker logs
docker-compose logs -f worker

# Check task status
docker-compose exec backend python manage.py shell
>>> from celery.result import AsyncResult
>>> result = AsyncResult('task-id')
>>> result.status
'SUCCESS'
```

## Email Templates

### Template Structure

All email templates are located in `backend/apps/accounts/templates/accounts/emails/`:

- `verify_email.html` - Email verification template
- `welcome.html` - Welcome email template
- `password_reset.html` - Password reset template
- `verification_email.txt` - Plain text fallback (optional)

### Template Variables

**Verification Email:**
- `user` - CustomUser object (user.first_name, user.email)
- `verification_url` - Full URL with token
- `expiry_hours` - Token expiry time (24 hours)

**Welcome Email:**
- `user` - CustomUser object
- `frontend_url` - Frontend application URL

**Password Reset Email:**
- `user` - CustomUser object
- `reset_url` - Full URL with reset token
- `expiry_hours` - Token expiry time (1 hour)

### Customizing Templates

To customize email templates:

1. Edit the HTML file in `backend/apps/accounts/templates/accounts/emails/`
2. Keep responsive design (max-width: 600px)
3. Include plain text alternative link
4. Test on multiple email clients (Gmail, Outlook, etc.)

### Template Best Practices

- Use inline CSS (external stylesheets often blocked)
- Keep HTML simple (avoid complex layouts)
- Include plain text alternative
- Test on mobile devices
- Use web-safe fonts (Arial, sans-serif)
- Avoid JavaScript (not supported in email clients)

## Testing

### Unit Tests

Located in `backend/apps/accounts/tests/test_email_service.py`:

```bash
# Run all email service tests
docker-compose exec backend python manage.py test apps.accounts.tests.test_email_service

# Run specific test
docker-compose exec backend python manage.py test apps.accounts.tests.test_email_service.EmailServiceTestCase.test_send_verification_email_sync
```

### Manual Testing

**With Console Backend:**
```bash
# Start backend
docker-compose up -d backend worker

# Register a new user via API
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'

# Check console output for email
docker-compose logs worker
```

**With SMTP Backend (Mailhog):**
```bash
# Add Mailhog to docker-compose.yml
mailhog:
  image: mailhog/mailhog
  ports:
    - "1025:1025"  # SMTP
    - "8025:8025"  # Web UI

# Update .env.backend
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mailhog
EMAIL_PORT=1025
EMAIL_USE_TLS=False

# View emails at http://localhost:8025
```

## Troubleshooting

### Common Issues

**1. Emails not sending**

Check Celery worker is running:
```bash
docker-compose ps worker
docker-compose logs worker
```

**2. SMTP Connection Errors**

- Verify EMAIL_HOST and EMAIL_PORT are correct
- Check EMAIL_USE_TLS setting matches SMTP server
- Verify credentials (EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
- Check firewall/network allows SMTP connections

**3. Template Rendering Errors**

- Verify template path is correct
- Check template variables are provided
- Look for syntax errors in templates
- Check logs: `docker-compose logs backend`

**4. Wrong Links in Emails**

- Verify FRONTEND_URL setting in .env.backend
- Check frontend application is running on that URL
- Ensure URL includes protocol (http:// or https://)

**5. Emails Marked as Spam**

For production:
- Configure SPF records for your domain
- Set up DKIM signing
- Use DMARC policy
- Use authenticated SMTP server
- Avoid spam trigger words in subject/body

## Security Considerations

### Email Security

1. **SMTP Authentication**
   - Always use authenticated SMTP in production
   - Use app-specific passwords (not account password)
   - Store credentials in environment variables, not code

2. **TLS/SSL Encryption**
   - Enable EMAIL_USE_TLS=True for production
   - Use port 587 (STARTTLS) or 465 (SSL/TLS)
   - Never send credentials over unencrypted connections

3. **Token Security**
   - Verification tokens expire after 24 hours
   - Password reset tokens expire after 1 hour
   - Tokens are cryptographically random (UUID4)
   - Tokens are single-use (marked as used after verification)

4. **Rate Limiting**
   - Registration endpoint: 5 requests/hour per IP
   - Resend verification: 3 requests/hour per IP
   - Prevents email bombing attacks

5. **Email Validation**
   - Email format validated on registration
   - Domain verification (optional, via DNS lookup)
   - Disposable email detection (optional)

### Production Checklist

- [ ] Configure SMTP backend with TLS
- [ ] Use authenticated SMTP server
- [ ] Set proper DEFAULT_FROM_EMAIL domain
- [ ] Configure SPF/DKIM/DMARC records
- [ ] Enable rate limiting on email endpoints
- [ ] Monitor email delivery failures
- [ ] Set up email bounce handling
- [ ] Configure FRONTEND_URL to production domain
- [ ] Test email deliverability (Gmail, Outlook, etc.)
- [ ] Set up email delivery monitoring/alerts

## API Integration

### Registration Flow

```python
# 1. User registers (views.py)
@method_decorator(ratelimit(key='ip', rate='5/h', method='POST'), name='dispatch')
class UserRegistrationView(generics.CreateAPIView):
    def perform_create(self, serializer):
        user = serializer.save()
        token = EmailVerificationToken.create_token(user)

        # Send verification email asynchronously
        send_verification_email.delay(str(user.id), str(token.token))
```

### Resend Verification Flow

```python
# 2. Resend verification email
class ResendVerificationEmailView(generics.GenericAPIView):
    def post(self, request):
        user = CustomUser.objects.get(email=request.data['email'])
        token = EmailVerificationToken.create_token(user)

        # Send verification email asynchronously
        send_verification_email.delay(str(user.id), str(token.token))
```

## Maintenance

### Monitoring

Monitor email delivery in production:

```bash
# Check Celery worker health
docker-compose exec backend celery -A veille_tech inspect active

# Check failed tasks
docker-compose exec backend celery -A veille_tech inspect scheduled

# View task results
docker-compose exec redis redis-cli
> SELECT 0
> KEYS *
```

### Cleanup Tasks

Periodically clean up expired tokens:

```python
# Celery Beat task (scheduled daily)
@shared_task
def cleanup_expired_tokens():
    """Delete expired email verification tokens."""
    from django.utils import timezone
    from apps.accounts.models import EmailVerificationToken

    expired = EmailVerificationToken.objects.filter(expires_at__lt=timezone.now())
    count = expired.count()
    expired.delete()

    return f"Deleted {count} expired tokens"
```

## Future Improvements

Potential enhancements for the email service:

1. **Email Templates**
   - Add more email types (account deletion, password change, etc.)
   - Support multiple languages (i18n)
   - Add email preferences (HTML vs plain text)

2. **Delivery Tracking**
   - Track email open rates
   - Track link clicks
   - Monitor bounce rates

3. **Advanced Features**
   - Email queue prioritization
   - Batch email sending
   - Email scheduling (send later)
   - A/B testing for email content

4. **Monitoring**
   - Grafana dashboard for email metrics
   - Alerts for delivery failures
   - SLA monitoring (delivery time)

5. **Security**
   - Email encryption (S/MIME, PGP)
   - Advanced spam filtering
   - Phishing protection

## References

- [Django Email Documentation](https://docs.djangoproject.com/en/stable/topics/email/)
- [Celery Task Documentation](https://docs.celeryproject.org/en/stable/userguide/tasks.html)
- [Email Template Best Practices](https://www.campaignmonitor.com/resources/guides/email-coding/)
- [SMTP Configuration Guide](https://docs.djangoproject.com/en/stable/topics/email/#smtp-backend)

## Support

For issues or questions:
- Check logs: `docker-compose logs backend worker`
- Review error messages in Celery worker output
- Verify configuration in .env.backend
- Test with console backend first
- Check email template rendering
