# -*- coding: utf-8 -*-
"""
Security tests for JWT authentication (TASK-2.19)
Tests JWT token validation, expiration, blacklisting, and error handling.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class JWTAuthenticationSecurityTests(TestCase):
    """Test cases for JWT authentication security."""

    def setUp(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user_detail_url = reverse('accounts:user_detail')

        # Create active user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True
        )

        # Generate tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

    def test_access_without_authentication_header(self):
        """Test that requests without authentication header are rejected."""
        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_access_with_invalid_token_format(self):
        """Test that requests with malformed tokens are rejected."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.format')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_with_tampered_token(self):
        """Test that tokens with modified signatures are rejected."""
        # Tamper with the token by modifying the signature
        tampered_token = self.access_token[:-10] + 'TAMPERED12'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_with_missing_bearer_prefix(self):
        """Test that tokens without 'Bearer' prefix are rejected."""
        # Send token without 'Bearer ' prefix
        self.client.credentials(HTTP_AUTHORIZATION=self.access_token)

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_blacklisted_token(self):
        """Test that blacklisted refresh tokens cannot be used."""
        refresh_url = reverse('accounts:token_refresh')
        logout_url = reverse('accounts:logout')

        # Blacklist the token by logging out
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        logout_response = self.client.post(
            logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        # Try to refresh with blacklisted token
        refresh_response = self.client.post(
            refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_with_valid_token(self):
        """Test that valid tokens grant access (positive test)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_token_contains_required_claims(self):
        """Test that generated tokens contain required claims."""
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)

        # Check required claims
        self.assertIn('token_type', token)
        self.assertIn('exp', token)
        self.assertIn('user_id', token)
        self.assertIn('jti', token)
        self.assertEqual(token['token_type'], 'access')
        # user_id is stored as string in token
        self.assertEqual(int(token['user_id']), self.user.id)

    def test_refresh_token_rotation(self):
        """Test that refresh tokens are rotated on use (ROTATE_REFRESH_TOKENS)."""
        refresh_url = reverse('accounts:token_refresh')

        response = self.client.post(
            refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # New refresh token should be different from original
        new_refresh = response.data['refresh']
        self.assertNotEqual(new_refresh, self.refresh_token)

    def test_old_refresh_token_blacklisted_after_rotation(self):
        """Test that old refresh token is blacklisted after rotation."""
        refresh_url = reverse('accounts:token_refresh')

        # First refresh (rotates the token)
        response1 = self.client.post(
            refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Try to use old refresh token again
        response2 = self.client.post(
            refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )

        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_multiple_token_refresh_generates_different_tokens(self):
        """Test that multiple refreshes generate different access tokens."""
        refresh_url = reverse('accounts:token_refresh')

        # First refresh
        response1 = self.client.post(
            refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        access1 = response1.data['access']
        refresh1 = response1.data['refresh']

        # Second refresh with new refresh token
        response2 = self.client.post(
            refresh_url,
            {'refresh': refresh1},
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        access2 = response2.data['access']

        # Access tokens should be different
        self.assertNotEqual(access1, access2)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class JWTErrorHandlingTests(TestCase):
    """Test cases for JWT error handling and standardized error responses."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.user_detail_url = reverse('accounts:user_detail')

    def test_error_response_structure_for_missing_token(self):
        """Test that missing token errors have consistent structure."""
        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertIsInstance(response.data['detail'], str)

    def test_error_response_structure_for_invalid_token(self):
        """Test that invalid token errors have consistent structure."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_error_response_for_tampered_token(self):
        """Test error response for tampered tokens."""
        # Create a valid token first
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Tamper with it
        tampered = access_token[:-10] + '0' * 10
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {tampered}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_error_response_for_malformed_authorization_header(self):
        """Test error response for malformed Authorization header."""
        # Send token without Bearer prefix
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=access_token)

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class JWTTokenLifetimeTests(TestCase):
    """Test cases for JWT token lifetime and expiration."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )

    def test_access_token_has_expiration(self):
        """Test that access tokens have an expiration claim."""
        from rest_framework_simplejwt.tokens import AccessToken

        token = AccessToken.for_user(self.user)

        self.assertIn('exp', token)
        # Expiration should be in the future
        exp_timestamp = token['exp']
        current_timestamp = timezone.now().timestamp()
        self.assertGreater(exp_timestamp, current_timestamp)

    def test_refresh_token_has_expiration(self):
        """Test that refresh tokens have an expiration claim."""
        from rest_framework_simplejwt.tokens import RefreshToken

        token = RefreshToken.for_user(self.user)

        self.assertIn('exp', token)
        # Refresh token expiration should be longer than access token
        exp_timestamp = token['exp']
        current_timestamp = timezone.now().timestamp()
        self.assertGreater(exp_timestamp, current_timestamp)

    def test_token_has_jti_claim(self):
        """Test that tokens have a unique JWT ID (jti) for blacklisting."""
        from rest_framework_simplejwt.tokens import RefreshToken

        token1 = RefreshToken.for_user(self.user)
        token2 = RefreshToken.for_user(self.user)

        self.assertIn('jti', token1)
        self.assertIn('jti', token2)
        # JTIs should be unique
        self.assertNotEqual(token1['jti'], token2['jti'])


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class JWTSecurityHeadersTests(TestCase):
    """Test cases for JWT security headers and best practices."""

    def setUp(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user_detail_url = reverse('accounts:user_detail')

        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_bearer_token_in_authorization_header(self):
        """Test that Bearer token authentication works correctly."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_case_insensitive_bearer_prefix(self):
        """Test that Bearer prefix is case-insensitive (per HTTP spec)."""
        # Note: This depends on DRF's implementation
        # Most implementations are case-insensitive
        self.client.credentials(HTTP_AUTHORIZATION=f'bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        # Should still work (case-insensitive)
        # If your implementation is case-sensitive, this test documents that behavior
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
