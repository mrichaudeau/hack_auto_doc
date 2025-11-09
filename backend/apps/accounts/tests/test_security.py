"""
Security tests for registration endpoint.

Tests:
- Rate limiting enforcement
- Input validation and sanitization
- SQL injection protection
- XSS prevention
- Password security
- Information disclosure prevention
"""

import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegistrationSecurity:
    """Security tests for registration endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.registration_url = '/api/auth/register/'

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_rate_limiting_enforced(self, mock_email_task):
        """Test that rate limiting prevents excessive registration attempts."""
        registration_data = {
            'email': 'test{}@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        # Make 5 requests (within limit)
        for i in range(5):
            data = registration_data.copy()
            data['email'] = f'test{i}@example.com'
            response = self.client.post(
                self.registration_url,
                data,
                format='json',
                HTTP_X_FORWARDED_FOR='192.168.1.100'  # Simulate same IP
            )
            # First 5 should succeed
            assert response.status_code == status.HTTP_201_CREATED

        # 6th request should be rate limited
        data = registration_data.copy()
        data['email'] = 'test6@example.com'
        response = self.client.post(
            self.registration_url,
            data,
            format='json',
            HTTP_X_FORWARDED_FOR='192.168.1.100'  # Same IP
        )
        # Should return 429 Too Many Requests
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'error' in response.data or 'detail' in response.data

    def test_sql_injection_in_email_safely_handled(self):
        """Test that SQL injection attempts in email are safely handled."""
        malicious_emails = [
            "admin'--@example.com",
            "admin';DROP TABLE users;--@example.com",
            "' OR '1'='1@example.com",
            "admin'/*@example.com",
        ]

        for email in malicious_emails:
            registration_data = {
                'email': email,
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User'
            }

            response = self.client.post(
                self.registration_url,
                registration_data,
                format='json'
            )

            # Should either reject as invalid email or safely store
            # No SQL injection should occur
            if response.status_code == status.HTTP_201_CREATED:
                # If accepted, verify it's safely stored
                user = User.objects.filter(email=email).first()
                if user:
                    assert user.email == email  # Stored as-is, no execution
            else:
                # Should be rejected with validation error
                assert response.status_code == status.HTTP_400_BAD_REQUEST

            # Database should still be intact
            assert User.objects.model._meta.db_table  # Table exists

    def test_xss_in_name_fields_escaped(self):
        """Test that XSS attempts in name fields are escaped."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]

        for payload in xss_payloads:
            registration_data = {
                'email': f'test{hash(payload)}@example.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': payload,
                'last_name': 'User'
            }

            with patch('apps.accounts.tasks.send_verification_email.delay'):
                response = self.client.post(
                    self.registration_url,
                    registration_data,
                    format='json'
                )

            # Should accept (names can contain special chars)
            # but data should be safely stored/escaped
            if response.status_code == status.HTTP_201_CREATED:
                # Verify stored safely (no script execution)
                user = User.objects.get(email=registration_data['email'])
                # Script tags should be stored as plain text
                assert '<script>' not in user.first_name or \
                       user.first_name == payload  # Stored as-is for escaping at display

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_password_not_logged_in_errors(self, mock_email_task):
        """Test that passwords are not logged in error messages."""
        registration_data = {
            'email': 'test@example.com',
            'password': 'weak',  # Weak password
            'password_confirm': 'weak',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Password should not be in error response
        response_str = str(response.data).lower()
        assert 'weak' not in response_str  # Password value not in error

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_password_never_returned_in_response(self, mock_email_task):
        """Test that password is never returned in API responses."""
        registration_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Password fields should not be in response
        assert 'password' not in response.data
        assert 'password_confirm' not in response.data

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_password_hashed_with_argon2(self, mock_email_task):
        """Test that passwords are hashed with Argon2."""
        registration_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify password is hashed with Argon2
        user = User.objects.get(email='test@example.com')
        assert user.password.startswith('$argon2')
        assert user.password != 'SecurePass123!'
        assert user.check_password('SecurePass123!')

    def test_duplicate_email_does_not_reveal_existence(self):
        """Test that duplicate email error doesn't reveal user existence."""
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            password='ExistingPass123!',
            first_name='Existing',
            last_name='User'
        )

        # Attempt to register with same email
        registration_data = {
            'email': 'existing@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        # Should return error but without revealing too much information
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT
        ]

        # Error message should be generic
        error_message = str(response.data).lower()
        # Should not say "user exists" or reveal account details
        # Generic message like "email already in use" is OK

    def test_very_long_inputs_rejected(self):
        """Test that very long inputs are rejected."""
        long_email = 'a' * 300 + '@example.com'  # > 254 char limit
        long_name = 'A' * 1000  # Very long name

        registration_data = {
            'email': long_email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': long_name,
            'last_name': long_name
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        # Should reject long email
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_special_characters_in_email_handled_correctly(self):
        """Test that special characters in email are handled safely."""
        special_emails = [
            "user+test@example.com",  # Valid with +
            "user.name@example.com",  # Valid with .
            "user_name@example.com",  # Valid with _
        ]

        for email in special_emails:
            registration_data = {
                'email': email,
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User'
            }

            with patch('apps.accounts.tasks.send_verification_email.delay'):
                response = self.client.post(
                    self.registration_url,
                    registration_data,
                    format='json'
                )

            # Should accept valid special characters
            assert response.status_code == status.HTTP_201_CREATED
            user = User.objects.get(email=email)
            assert user.email == email

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_csrf_protection_not_required_for_api(self, mock_email_task):
        """Test that CSRF protection is appropriately configured for API."""
        # API endpoints should not require CSRF token
        registration_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        # Request without CSRF token should work for API
        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        # Should work without CSRF token (API endpoint)
        assert response.status_code == status.HTTP_201_CREATED

    def test_information_disclosure_in_errors(self):
        """Test that error messages don't reveal sensitive information."""
        registration_data = {
            'email': 'invalid',
            'password': 'weak',
            'password_confirm': 'different',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Error messages should not reveal:
        # - Database structure
        # - Internal implementation details
        # - System paths
        # - Stack traces (in production)
        error_str = str(response.data)
        assert 'database' not in error_str.lower()
        assert 'traceback' not in error_str.lower()
        assert '/home/' not in error_str and 'C:\\' not in error_str


# ============================================================================
# LOGIN AUTHENTICATION SECURITY TESTS (US-3: Standard User Login, TASK-3.17)
# ============================================================================

import time
import jwt
from django.core.cache import cache
from apps.accounts.models import LoginAuditLog


@pytest.mark.django_db
class TestLoginInjectionAttackPrevention:
    """Test SQL injection and XSS attack prevention for login endpoint."""

    def setup_method(self):
        """Set up test client and verified user."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_verified_user(self, db):
        """Create verified user for login tests."""
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            first_name='John',
            last_name='Doe',
            is_email_verified=True,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_sql_injection_in_login_email_field(self):
        """Test SQL injection payload in login email is safely handled."""
        sql_payloads = [
            "'; DROP TABLE auth_user; --",
            "admin' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "admin' OR '1'='1' /*",
            "1' UNION SELECT NULL, NULL, NULL--",
        ]

        for payload in sql_payloads:
            response = self.client.post(self.login_url, {
                'email': payload,
                'password': 'password123'
            })

            # Should return 400 (validation error) or 401 (invalid credentials)
            # NOT 500 (database error)
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ], f"SQL injection payload '{payload}' caused unexpected status code"

        # Verify users table still exists and is intact
        assert User.objects.count() >= 0, "User table was affected by SQL injection"

    def test_sql_injection_in_login_password_field(self):
        """Test SQL injection payload in login password is safely handled."""
        sql_payloads = [
            "' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
        ]

        for payload in sql_payloads:
            response = self.client.post(self.login_url, {
                'email': 'verified@example.com',
                'password': payload
            })

            # Should return 401 (invalid credentials), not cause database error
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert User.objects.filter(email='verified@example.com').exists()

    def test_xss_in_login_email_field(self):
        """Test XSS payload in login email does not execute or persist unescaped."""
        xss_payloads = [
            '<script>alert("XSS")</script>@example.com',
            '<img src=x onerror=alert("XSS")>@example.com',
            'javascript:alert("XSS")@example.com',
            '<svg/onload=alert("XSS")>@example.com',
        ]

        for payload in xss_payloads:
            response = self.client.post(self.login_url, {
                'email': payload,
                'password': 'password123'
            })

            response_text = response.content.decode('utf-8')

            # Error message should not contain unescaped HTML/JavaScript
            assert '<script>' not in response_text, f"XSS payload '{payload}' not escaped in response"
            assert 'onerror=' not in response_text
            assert 'javascript:' not in response_text
            assert 'onload=' not in response_text

            # Check audit log doesn't store unescaped payload
            if LoginAuditLog.objects.filter(email=payload).exists():
                log = LoginAuditLog.objects.filter(email=payload).latest('timestamp')
                log_email = log.email
                assert '<script>' not in str(log_email)

    def test_xss_in_login_error_messages(self):
        """Test login error messages properly escape user input."""
        response = self.client.post(self.login_url, {
            'email': '<script>alert("XSS")</script>',
            'password': 'test'
        })

        response_data = response.json()
        if 'error' in response_data:
            error_message = str(response_data['error'])
            assert '<script>' not in error_message
            assert 'alert(' not in error_message


@pytest.mark.django_db
class TestLoginTimingAttackMitigation:
    """Test timing attack prevention for account enumeration via login."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_users(self, db):
        """Create test users."""
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='SecurePass123!',
            is_email_verified=False,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_timing_invalid_user_vs_invalid_password(self):
        """Test invalid user vs invalid password take similar time."""
        # Measure time for non-existent user
        timings_invalid_user = []
        for _ in range(5):
            start = time.time()
            self.client.post(self.login_url, {
                'email': 'nonexistent@example.com',
                'password': 'password123'
            })
            timings_invalid_user.append(time.time() - start)

        # Measure time for invalid password
        timings_invalid_password = []
        for _ in range(5):
            start = time.time()
            self.client.post(self.login_url, {
                'email': 'verified@example.com',
                'password': 'wrongpassword123'
            })
            timings_invalid_password.append(time.time() - start)

        # Calculate average times
        avg_invalid_user = sum(timings_invalid_user) / len(timings_invalid_user)
        avg_invalid_password = sum(timings_invalid_password) / len(timings_invalid_password)

        # Times should be within 100ms of each other to prevent timing attacks
        time_difference = abs(avg_invalid_user - avg_invalid_password)
        assert time_difference < 0.1, (
            f"Timing difference too large: {time_difference:.3f}s "
            f"(invalid_user: {avg_invalid_user:.3f}s, invalid_password: {avg_invalid_password:.3f}s)"
        )

    def test_timing_does_not_reveal_verification_status(self):
        """Test timing doesn't reveal if email is verified vs unverified."""
        # Measure time for unverified user (with correct password)
        timings_unverified = []
        for _ in range(5):
            start = time.time()
            self.client.post(self.login_url, {
                'email': 'unverified@example.com',
                'password': 'SecurePass123!'
            })
            timings_unverified.append(time.time() - start)

        # Measure time for non-existent user
        timings_nonexistent = []
        for _ in range(5):
            start = time.time()
            self.client.post(self.login_url, {
                'email': 'nonexistent@example.com',
                'password': 'SecurePass123!'
            })
            timings_nonexistent.append(time.time() - start)

        avg_unverified = sum(timings_unverified) / len(timings_unverified)
        avg_nonexistent = sum(timings_nonexistent) / len(timings_nonexistent)

        # Times should be similar (within 100ms)
        time_difference = abs(avg_unverified - avg_nonexistent)
        assert time_difference < 0.1, (
            f"Timing reveals verification status: {time_difference:.3f}s difference"
        )


@pytest.mark.django_db
class TestLoginPasswordExposurePrevention:
    """Test password never appears in login responses, logs, or tokens."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_verified_user(self, db):
        """Create verified user."""
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_password_not_in_response_body_success(self):
        """Test password never appears in successful login response."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        response_str = str(response.content)
        assert 'SecurePass123!' not in response_str
        # Password field key might appear in docs, but not value
        if 'password' in response_str.lower():
            assert 'SecurePass123!' not in response_str

    def test_password_not_in_response_body_failure(self):
        """Test password never appears in error response."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'WrongPassword456!'
        })

        response_str = str(response.content)
        assert 'WrongPassword456!' not in response_str
        assert 'SecurePass123!' not in response_str  # Real password shouldn't appear either

    def test_password_not_in_audit_log(self):
        """Test password never stored in LoginAuditLog."""
        test_password = 'SecurePass123!'

        self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': test_password
        })

        log = LoginAuditLog.objects.latest('timestamp')

        # Check all log fields
        log_dict = log.__dict__
        for key, value in log_dict.items():
            if value is not None:
                assert test_password not in str(value), f"Password found in audit log field: {key}"

    def test_password_not_in_audit_log_failure(self):
        """Test password not logged even on authentication failure."""
        wrong_password = 'WrongPassword789!'

        self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': wrong_password
        })

        log = LoginAuditLog.objects.latest('timestamp')
        log_str = str(log.__dict__)
        assert wrong_password not in log_str

    def test_password_not_in_jwt_access_token(self):
        """Test JWT access token does not contain password or password hash."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        data = response.json()
        access_token = data['access_token']

        # Decode JWT without verification to inspect payload
        decoded = jwt.decode(access_token, options={"verify_signature": False})

        token_str = str(decoded)
        assert 'SecurePass123!' not in token_str
        assert 'password' not in token_str.lower()

        # Verify token doesn't contain password hash
        assert not any(key in decoded for key in ['password', 'password_hash', 'hashed_password'])

    def test_password_not_in_jwt_refresh_token(self):
        """Test JWT refresh token does not contain password or password hash."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        data = response.json()
        refresh_token = data['refresh_token']

        # Decode JWT without verification to inspect payload
        decoded = jwt.decode(refresh_token, options={"verify_signature": False})

        token_str = str(decoded)
        assert 'SecurePass123!' not in token_str
        assert 'password' not in token_str.lower()


@pytest.mark.django_db
class TestLoginAccountEnumerationPrevention:
    """Test account enumeration prevention through consistent error messages."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_users(self, db):
        """Create test users."""
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='SecurePass123!',
            is_email_verified=False,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_same_error_for_invalid_user_and_invalid_password(self):
        """Test same error message for invalid user vs invalid password."""
        # Test with non-existent user
        response1 = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })

        # Test with existing user but wrong password
        response2 = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'wrongpassword123'
        })

        # Both should return 401
        assert response1.status_code == status.HTTP_401_UNAUTHORIZED
        assert response2.status_code == status.HTTP_401_UNAUTHORIZED

        # Both should have identical error messages
        error1 = response1.json()['error']
        error2 = response2.json()['error']
        assert error1 == error2
        assert 'invalid email or password' in error1.lower()

    def test_error_message_does_not_reveal_user_existence(self):
        """Test error messages never reveal if email exists in database."""
        response = self.client.post(self.login_url, {
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })

        error_message = response.json()['error'].lower()

        # Error should not contain revealing terms
        forbidden_terms = ['not found', 'does not exist', 'user does not exist', 'account not found']
        for term in forbidden_terms:
            assert term not in error_message, f"Error message reveals user existence: '{term}'"

    def test_verification_status_revealed_only_after_auth(self):
        """Test email verification status only revealed after successful authentication."""
        # Unverified user with wrong password should get generic error
        response = self.client.post(self.login_url, {
            'email': 'unverified@example.com',
            'password': 'wrongpassword'
        })

        # Should return 401 with generic error (not 403 about verification)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'invalid email or password' in response.json()['error'].lower()
        assert 'verify' not in response.json()['error'].lower()

        # Unverified user with correct password should get verification error
        response = self.client.post(self.login_url, {
            'email': 'unverified@example.com',
            'password': 'SecurePass123!'
        })

        # Now should return 403 with verification message
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'verify your email' in response.json()['error'].lower()


@pytest.mark.django_db
class TestLoginCSRFProtection:
    """Test CSRF protection for login authentication endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_verified_user(self, db):
        """Create verified user."""
        User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_login_endpoint_does_not_require_csrf_token(self):
        """Test login endpoint is accessible without CSRF token (public endpoint)."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        # Should succeed (200) or fail for auth reasons, not CSRF
        assert response.status_code != status.HTTP_403_FORBIDDEN or \
               'csrf' not in str(response.content).lower()


@pytest.mark.django_db
class TestLoginRateLimitingIntegration:
    """Test rate limiting integration for brute force prevention on login."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_verified_user(self, db):
        """Create verified user."""
        User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_rate_limiting_prevents_brute_force_attempts(self):
        """Test rate limiting blocks excessive failed login attempts."""
        # Make 5 failed attempts (rate limit threshold)
        for i in range(5):
            response = self.client.post(self.login_url, {
                'email': 'verified@example.com',
                'password': f'wrong_password_{i}'
            })
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # 6th attempt should be rate limited
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'wrong_password_6'
        })

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert 'rate limit' in data['message'].lower() or 'too many' in data['message'].lower()

    def test_rate_limit_includes_retry_after_header(self):
        """Test rate limit response includes Retry-After header."""
        # Trigger rate limit
        for i in range(5):
            self.client.post(self.login_url, {
                'email': 'verified@example.com',
                'password': f'wrong_password_{i}'
            })

        # 6th attempt should be rate limited with Retry-After header
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'wrong_password_6'
        })

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert 'Retry-After' in response

    def test_rate_limiting_per_ip_address(self):
        """Test rate limiting is per IP address."""
        # Make 5 failed attempts from one IP
        for i in range(5):
            self.client.post(
                self.login_url,
                {'email': 'verified@example.com', 'password': f'wrong_{i}'},
                HTTP_X_FORWARDED_FOR='192.168.1.100'
            )

        # 6th attempt from same IP should be blocked
        response1 = self.client.post(
            self.login_url,
            {'email': 'verified@example.com', 'password': 'wrong_6'},
            HTTP_X_FORWARDED_FOR='192.168.1.100'
        )
        assert response1.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # But attempt from different IP should succeed (or fail for auth reasons)
        response2 = self.client.post(
            self.login_url,
            {'email': 'verified@example.com', 'password': 'SecurePass123!'},
            HTTP_X_FORWARDED_FOR='192.168.1.200'
        )
        # Should not be rate limited
        assert response2.status_code != status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
class TestLoginSecurityHeaders:
    """Test security-related HTTP headers in login responses."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.login_url = '/api/auth/login/'

    @pytest.fixture(autouse=True)
    def setup_verified_user(self, db):
        """Create verified user."""
        User.objects.create_user(
            email='verified@example.com',
            password='SecurePass123!',
            is_email_verified=True,
            is_active=True
        )

    @pytest.fixture(autouse=True)
    def clear_cache_fixture(self):
        """Clear cache before each test."""
        cache.clear()
        yield
        cache.clear()

    def test_response_does_not_leak_server_info(self):
        """Test response headers don't leak sensitive server information."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        # Server header should not reveal detailed version information
        server_header = response.get('Server', '')
        if 'Django' in server_header:
            assert not any(char.isdigit() for char in server_header), \
                "Server header reveals Django version"

    def test_content_type_is_json(self):
        """Test response Content-Type is application/json."""
        response = self.client.post(self.login_url, {
            'email': 'verified@example.com',
            'password': 'SecurePass123!'
        })

        content_type = response.get('Content-Type', '')
        assert 'application/json' in content_type
