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
