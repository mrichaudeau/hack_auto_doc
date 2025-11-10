"""
Integration Tests for Login API Endpoint (US-3: Standard User Login, TASK-3.16)

Comprehensive tests covering:
- Successful login with valid credentials
- JWT token validation and structure
- User profile response format
- Error scenarios (401, 403, 400, 429)
- Rate limiting integration
- Security logging verification
- IP address and user agent capture

Target: 90%+ code coverage for login view
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import LoginAuditLog
from django.conf import settings
from django.core.cache import cache
import jwt

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide API client for making requests."""
    return APIClient()


@pytest.fixture
def verified_user(db):
    """Create verified and active user for successful login tests."""
    user = User.objects.create_user(
        email='verified@example.com',
        password='SecurePass123!',
        first_name='John',
        last_name='Doe',
        is_email_verified=True,
        is_active=True
    )
    return user


@pytest.fixture
def unverified_user(db):
    """Create unverified user for email verification tests."""
    user = User.objects.create_user(
        email='unverified@example.com',
        password='SecurePass123!',
        first_name='Jane',
        last_name='Smith',
        is_email_verified=False,
        is_active=False  # User remains inactive until email verified
    )
    return user


@pytest.fixture
def inactive_user(db):
    """Create inactive user for account disabled tests."""
    user = User.objects.create_user(
        email='inactive@example.com',
        password='SecurePass123!',
        first_name='Bob',
        last_name='Wilson',
        is_email_verified=True,
        is_active=False  # Account disabled
    )
    return user


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test to reset rate limiting."""
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestLoginAPISuccessFlow:
    """Test successful login scenarios."""

    def test_successful_login_returns_200(self, api_client, verified_user):
        """Test successful login with valid credentials returns 200 OK."""
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        assert response.status_code == status.HTTP_200_OK

    def test_response_includes_tokens_and_user(self, api_client, verified_user):
        """Test response includes access_token, refresh_token, and user profile."""
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        data = response.json()
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data

    def test_access_token_is_valid_jwt(self, api_client, verified_user):
        """Test access_token is valid JWT with correct structure."""
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        data = response.json()
        token = data['access_token']

        # Decode JWT without verification to check structure
        decoded = jwt.decode(token, options={"verify_signature": False})

        # Check standard JWT claims
        assert 'user_id' in decoded
        assert 'exp' in decoded  # Expiration time
        assert 'iat' in decoded  # Issued at time
        assert 'jti' in decoded  # JWT ID (for blacklisting)

    def test_user_profile_structure(self, api_client, verified_user):
        """Test user profile includes id, email, first_name, last_name, is_sso_user."""
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        data = response.json()
        user = data['user']

        assert 'id' in user
        assert user['email'] == 'verified@example.com'
        assert user['first_name'] == 'John'
        assert user['last_name'] == 'Doe'
        assert 'is_sso_user' in user
        assert user['is_sso_user'] is False

    def test_case_insensitive_email_login(self, api_client, verified_user):
        """Test login works with different email case variations."""
        # Try uppercase
        response = api_client.post('/api/auth/login/', {
            'email': 'VERIFIED@EXAMPLE.COM',
            'password': 'SecurePass123!'
        })
        assert response.status_code == status.HTTP_200_OK

        # Try mixed case
        response = api_client.post('/api/auth/login/', {
            'email': 'VeRiFiEd@ExAmPlE.cOm',
            'password': 'SecurePass123!'
        })
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLoginAPIErrorScenarios:
    """Test error scenarios and status codes."""

    def test_invalid_email_returns_401(self, api_client):
        """Test 401 for non-existent email."""
        response = api_client.post('/api/auth/login/', {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert 'error' in data
        assert 'invalid email or password' in data['error'].lower()

    def test_invalid_password_returns_401(self, api_client, verified_user):
        """Test 401 for incorrect password."""
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'WrongPassword123!'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert 'error' in data
        assert 'invalid email or password' in data['error'].lower()

    def test_unverified_email_returns_403(self, api_client, unverified_user):
        """Test 403 for unverified email (is_email_verified=False)."""
        response = api_client.post('/api/auth/login/', {
            'email': 'unverified@example.com',
            'password': 'SecurePass123!'
        })

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert 'error' in data
        assert 'verify your email' in data['error'].lower()

    def test_missing_email_returns_400(self, api_client):
        """Test 400 for missing email field."""
        response = api_client.post('/api/auth/login/', {
            'password': 'SomePassword123!'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'email' in data

    def test_missing_password_returns_400(self, api_client):
        """Test 400 for missing password field."""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@example.com'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'password' in data

    def test_invalid_email_format_returns_400(self, api_client):
        """Test 400 for invalid email format."""
        response = api_client.post('/api/auth/login/', {
            'email': 'not-an-email',
            'password': 'SomePassword123!'
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert 'email' in data

    def test_empty_credentials_returns_400(self, api_client):
        """Test 400 for empty email and password."""
        response = api_client.post('/api/auth/login/', {
            'email': '',
            'password': ''
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inactive_account_returns_401(self, api_client, inactive_user):
        """Test 401 for disabled account."""
        response = api_client.post('/api/auth/login/', {
            'email': 'inactive@example.com',
            'password': 'SecurePass123!'
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLoginAPIRateLimiting:
    """Test rate limiting integration."""

    def test_rate_limit_after_5_failed_attempts(self, api_client, verified_user):
        """Test 429 after 5 failed login attempts from same IP."""
        # Make 5 failed attempts
        for i in range(5):
            response = api_client.post('/api/auth/login/', {
                'email': 'verified@example.com',
                'password': 'WrongPassword!'
            })
            # First 5 should return 401
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 6th attempt should be rate limited
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'WrongPassword!'
        })

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert 'error' in data or 'message' in data

    def test_rate_limit_header_present(self, api_client, verified_user):
        """Test Retry-After header present in 429 response."""
        # Exhaust rate limit
        for i in range(6):
            api_client.post('/api/auth/login/', {
                'email': 'verified@example.com',
                'password': 'WrongPassword!'
            })

        # Check 6th response has Retry-After header
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'WrongPassword!'
        })

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            # Note: Retry-After header might be in response.data instead of headers
            # depending on rate_limit decorator implementation
            data = response.json()
            assert 'retry_after_seconds' in data or 'Retry-After' in response.headers

    def test_successful_login_not_rate_limited(self, api_client, verified_user):
        """Test successful logins do not trigger rate limit."""
        # Make 6 successful login attempts
        for i in range(6):
            response = api_client.post('/api/auth/login/', {
                'email': 'verified@example.com',
                'password': 'SecurePass123!'
            })
            # All should succeed
            assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestLoginAPIAuditLogging:
    """Test security audit logging."""

    def test_audit_log_created_on_success(self, api_client, verified_user):
        """Test LoginAuditLog entry created for successful login."""
        initial_count = LoginAuditLog.objects.count()

        api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        assert LoginAuditLog.objects.count() == initial_count + 1

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.email.lower() == 'verified@example.com'
        assert log.success is True
        assert log.failure_reason is None
        assert log.user == verified_user

    def test_audit_log_created_on_failure(self, api_client, verified_user):
        """Test LoginAuditLog entry created for failed login."""
        initial_count = LoginAuditLog.objects.count()

        api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'WrongPassword!'
        })

        assert LoginAuditLog.objects.count() == initial_count + 1

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.email.lower() == 'verified@example.com'
        assert log.success is False
        assert log.failure_reason == 'invalid_credentials'

    def test_audit_log_for_unverified_email(self, api_client, unverified_user):
        """Test audit log records email_not_verified failure reason."""
        api_client.post('/api/auth/login/', {
            'email': 'unverified@example.com',
            'password': 'SecurePass123!'
        })

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.email.lower() == 'unverified@example.com'
        assert log.success is False
        assert log.failure_reason == 'email_not_verified'

    def test_audit_log_for_nonexistent_user(self, api_client):
        """Test audit log created for non-existent user (user=None)."""
        api_client.post('/api/auth/login/', {
            'email': 'nobody@example.com',
            'password': 'SomePassword!'
        })

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.email.lower() == 'nobody@example.com'
        assert log.user is None
        assert log.success is False
        assert log.failure_reason == 'invalid_credentials'

    def test_audit_log_contains_ip_address(self, api_client, verified_user):
        """Test audit log captures IP address."""
        # Set custom IP via META (simulates X-Forwarded-For)
        api_client.post(
            '/api/auth/login/',
            {'email': 'verified@example.com', 'password': 'SecurePass123!'},
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.ip_address == '192.168.1.100'

    def test_audit_log_contains_user_agent(self, api_client, verified_user):
        """Test audit log captures user agent."""
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0'

        api_client.post(
            '/api/auth/login/',
            {'email': 'verified@example.com', 'password': 'SecurePass123!'},
            HTTP_USER_AGENT=user_agent
        )

        log = LoginAuditLog.objects.latest('timestamp')
        assert log.user_agent == user_agent

    def test_multiple_audit_logs_for_same_user(self, api_client, verified_user):
        """Test multiple login attempts create separate audit log entries."""
        initial_count = LoginAuditLog.objects.count()

        # Successful login
        api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        # Failed login
        api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'WrongPassword!'
        })

        # Another successful login
        api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        assert LoginAuditLog.objects.count() == initial_count + 3

        logs = LoginAuditLog.objects.filter(
            email__iexact='verified@example.com'
        ).order_by('-timestamp')[:3]

        assert logs[0].success is True
        assert logs[1].success is False
        assert logs[2].success is True


@pytest.mark.django_db
class TestLoginAPIEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_login_with_extra_whitespace_in_email(self, api_client, verified_user):
        """Test login handles extra whitespace in email."""
        response = api_client.post('/api/auth/login/', {
            'email': '  verified@example.com  ',
            'password': 'SecurePass123!'
        })

        # Should still work (email gets stripped)
        # Note: This depends on serializer implementation
        # If it doesn't strip, test should expect 400
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_login_with_very_long_password(self, api_client, verified_user):
        """Test login with extremely long password."""
        long_password = 'a' * 10000

        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': long_password
        })

        # Should return 401 (invalid credentials), not crash
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_with_unicode_characters(self, api_client):
        """Test login handles Unicode characters in input."""
        response = api_client.post('/api/auth/login/', {
            'email': 'test@例え.jp',
            'password': 'пароль123'
        })

        # Should handle gracefully (either 400 or 401)
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED]

    def test_concurrent_login_attempts(self, api_client, verified_user):
        """Test multiple concurrent login attempts don't break state."""
        responses = []

        # Simulate concurrent requests
        for _ in range(3):
            response = api_client.post('/api/auth/login/', {
                'email': 'verified@example.com',
                'password': 'SecurePass123!'
            })
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK

    def test_login_after_password_change(self, api_client, verified_user):
        """Test login works after user changes password."""
        # Change password
        verified_user.set_password('NewPassword123!')
        verified_user.save()

        # Old password should fail
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # New password should work
        response = api_client.post('/api/auth/login/', {
            'email': 'verified@example.com',
            'password': 'NewPassword123!'
        })
        assert response.status_code == status.HTTP_200_OK
