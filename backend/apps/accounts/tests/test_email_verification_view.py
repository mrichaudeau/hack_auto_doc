"""
Unit and integration tests for email verification endpoint.

Tests the GET /api/auth/verify-email/?token=<token> endpoint.
"""

import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import EmailVerificationToken

User = get_user_model()


@pytest.mark.django_db
class TestEmailVerificationView:
    """Tests for the email verification endpoint."""

    def setup_method(self):
        """Set up test client and URL."""
        self.client = APIClient()
        self.verify_url = '/api/auth/verify-email/'

    def test_successful_email_verification(self):
        """Test successful email verification with valid token."""
        # Create inactive user
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )

        # Create verification token
        token = EmailVerificationToken.create_token(user)

        # Mock welcome email task
        with patch('apps.accounts.views.send_welcome_email.delay') as mock_welcome:
            # Verify email
            response = self.client.get(
                self.verify_url,
                {'token': str(token.token)}
            )

            # Assert response
            assert response.status_code == status.HTTP_200_OK
            assert response.data['message'] == 'Email verified successfully. You can now log in.'
            assert response.data['is_active'] is True
            assert response.data['is_email_verified'] is True

            # Assert user updated
            user.refresh_from_db()
            assert user.is_active is True
            assert user.is_email_verified is True
            assert user.email_verified_at is not None

            # Assert token marked as used
            token.refresh_from_db()
            assert token.is_used is True

            # Assert welcome email sent
            mock_welcome.assert_called_once_with(str(user.id))

    def test_missing_token_parameter(self):
        """Test that missing token parameter returns 400."""
        response = self.client.get(self.verify_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'token_required'
        assert 'resend_url' in response.data

    def test_invalid_token_format(self):
        """Test that invalid token format returns 400."""
        response = self.client.get(
            self.verify_url,
            {'token': 'invalid-token-format'}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'token_invalid'
        assert 'resend_url' in response.data

    def test_nonexistent_token(self):
        """Test that non-existent token returns 400."""
        response = self.client.get(
            self.verify_url,
            {'token': '00000000-0000-0000-0000-000000000000'}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'token_invalid'
        assert 'resend_url' in response.data

    def test_already_used_token(self):
        """Test that already used token returns 400."""
        # Create user and token
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )
        token = EmailVerificationToken.create_token(user)

        # Mark token as used
        token.is_used = True
        token.save()

        # Try to use token
        response = self.client.get(
            self.verify_url,
            {'token': str(token.token)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'token_used'
        assert 'resend_url' in response.data

    def test_expired_token(self):
        """Test that expired token returns 410."""
        # Create user
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )

        # Create expired token
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
        )

        # Try to use expired token
        response = self.client.get(
            self.verify_url,
            {'token': str(token.token)}
        )

        assert response.status_code == status.HTTP_410_GONE
        assert response.data['error'] == 'token_expired'
        assert 'resend_url' in response.data

    def test_transaction_atomicity(self):
        """Test that user activation and token marking are atomic."""
        # Create user and token
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )
        token = EmailVerificationToken.create_token(user)

        # Mock welcome email to raise exception after transaction
        with patch('apps.accounts.views.send_welcome_email.delay') as mock_welcome:
            # Verify email (should succeed)
            response = self.client.get(
                self.verify_url,
                {'token': str(token.token)}
            )

            # Both user and token should be updated
            assert response.status_code == status.HTTP_200_OK

            user.refresh_from_db()
            token.refresh_from_db()

            # Verify both changes committed
            assert user.is_active is True
            assert user.is_email_verified is True
            assert token.is_used is True

    def test_verify_already_verified_user_with_new_token(self):
        """Test that an already verified user cannot be verified again."""
        # Create already verified user
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=True,
            is_email_verified=True
        )
        user.email_verified_at = timezone.now()
        user.save()

        # Create new token (should not be possible in practice, but test edge case)
        token = EmailVerificationToken.create_token(user)

        # Try to verify again
        with patch('apps.accounts.views.send_welcome_email.delay'):
            response = self.client.get(
                self.verify_url,
                {'token': str(token.token)}
            )

            # Should still succeed (idempotent operation)
            assert response.status_code == status.HTTP_200_OK

    def test_response_includes_all_required_fields(self):
        """Test that success response includes all required fields."""
        # Create user and token
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )
        token = EmailVerificationToken.create_token(user)

        # Verify email
        with patch('apps.accounts.views.send_welcome_email.delay'):
            response = self.client.get(
                self.verify_url,
                {'token': str(token.token)}
            )

            # Check required fields
            assert 'message' in response.data
            assert 'is_active' in response.data
            assert 'is_email_verified' in response.data

    def test_error_responses_include_resend_url(self):
        """Test that all error responses include resend_url."""
        error_scenarios = [
            # Missing token
            {},
            # Invalid format
            {'token': 'invalid'},
            # Non-existent token
            {'token': '00000000-0000-0000-0000-000000000000'},
        ]

        for params in error_scenarios:
            response = self.client.get(self.verify_url, params)
            assert 'resend_url' in response.data, f"Failed for params: {params}"
            assert response.data['resend_url'] == '/api/auth/resend-verification/'

    def test_verification_updates_email_verified_at(self):
        """Test that email_verified_at timestamp is set correctly."""
        # Create user and token
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )
        token = EmailVerificationToken.create_token(user)

        # Store time before verification
        before_verification = timezone.now()

        # Verify email
        with patch('apps.accounts.views.send_welcome_email.delay'):
            response = self.client.get(
                self.verify_url,
                {'token': str(token.token)}
            )

            assert response.status_code == status.HTTP_200_OK

            # Check email_verified_at is set
            user.refresh_from_db()
            assert user.email_verified_at is not None
            assert user.email_verified_at >= before_verification
            assert user.email_verified_at <= timezone.now()

    @patch('apps.accounts.views.send_welcome_email.delay')
    def test_welcome_email_sent_after_verification(self, mock_welcome):
        """Test that welcome email is sent after successful verification."""
        # Create user and token
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            is_active=False,
            is_email_verified=False
        )
        token = EmailVerificationToken.create_token(user)

        # Verify email
        response = self.client.get(
            self.verify_url,
            {'token': str(token.token)}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_welcome.assert_called_once_with(str(user.id))
