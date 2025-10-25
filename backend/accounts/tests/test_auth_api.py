# -*- coding: utf-8 -*-
"""
Integration tests for authentication API endpoints.
Tests login, logout, token refresh, and user detail retrieval (TASK-2.16, 2.17)
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from allauth.account.models import EmailAddress
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class LoginAPITests(TestCase):
    """Test cases for the login API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.login_url = reverse('accounts:login')

        # Create active user with verified email
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

    def test_login_with_valid_credentials(self):
        """Test successful login with valid email and password."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'test@example.com',
                'password': 'TestPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
        self.assertEqual(response.data['user']['first_name'], 'Test')
        self.assertEqual(response.data['user']['last_name'], 'User')

    def test_login_with_uppercase_email(self):
        """Test login with uppercase email (should work due to case-insensitive lookup)."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'TEST@EXAMPLE.COM',
                'password': 'TestPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_login_with_invalid_password(self):
        """Test login with incorrect password."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'test@example.com',
                'password': 'WrongPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Error can be in 'detail' or 'non_field_errors'
        self.assertTrue('detail' in response.data or 'non_field_errors' in response.data)

    def test_login_with_nonexistent_email(self):
        """Test login with email that doesn't exist."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'nonexistent@example.com',
                'password': 'TestPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)

    def test_login_with_inactive_account(self):
        """Test login with unverified/inactive account."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='TestPassword123!',
            is_active=False
        )

        response = self.client.post(
            self.login_url,
            {
                'email': 'inactive@example.com',
                'password': 'TestPassword123!'
            },
            format='json'
        )

        # Can be 401 or 403 depending on validation order
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        # Check for verification-related message in any error field
        error_text = str(response.data).lower()
        self.assertIn('verifie', error_text)

    def test_login_with_missing_email(self):
        """Test login without providing email."""
        response = self.client.post(
            self.login_url,
            {
                'password': 'TestPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_login_with_missing_password(self):
        """Test login without providing password."""
        response = self.client.post(
            self.login_url,
            {
                'email': 'test@example.com'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_with_empty_credentials(self):
        """Test login with empty email and password."""
        response = self.client.post(
            self.login_url,
            {
                'email': '',
                'password': ''
            },
            format='json'
        )

        # Can be 400 or 401 depending on validation
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class LogoutAPITests(TestCase):
    """Test cases for the logout API endpoint."""

    def setUp(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.logout_url = reverse('accounts:logout')

        # Create active user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
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

    def test_logout_with_valid_refresh_token(self):
        """Test successful logout with valid refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(
            self.logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_without_refresh_token(self):
        """Test logout without providing refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(
            self.logout_url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh_token', response.data)

    def test_logout_without_authentication(self):
        """Test logout without authentication header."""
        response = self.client.post(
            self.logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_refresh_token(self):
        """Test logout with invalid refresh token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.post(
            self.logout_url,
            {'refresh_token': 'invalid.token.here'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_already_blacklisted_token(self):
        """Test logout with a token that's already been blacklisted."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        # First logout (blacklists the token)
        response1 = self.client.post(
            self.logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )
        self.assertEqual(response1.status_code, status.HTTP_204_NO_CONTENT)

        # Try to logout again with same token
        response2 = self.client.post(
            self.logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class TokenRefreshAPITests(TestCase):
    """Test cases for the token refresh API endpoint."""

    def setUp(self):
        """Set up test client and user with tokens."""
        self.client = APIClient()
        self.refresh_url = reverse('accounts:token_refresh')

        # Create active user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )

        # Generate tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

    def test_refresh_with_valid_token(self):
        """Test token refresh with valid refresh token."""
        response = self.client.post(
            self.refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        # Check if refresh token is rotated (ROTATE_REFRESH_TOKENS=True)
        self.assertIn('refresh', response.data)

    def test_refresh_with_invalid_token(self):
        """Test token refresh with invalid refresh token."""
        response = self.client.post(
            self.refresh_url,
            {'refresh': 'invalid.token.format'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_without_token(self):
        """Test token refresh without providing refresh token."""
        response = self.client.post(
            self.refresh_url,
            {},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh', response.data)

    def test_refresh_with_blacklisted_token(self):
        """Test token refresh with blacklisted token."""
        # Blacklist the token by logging out
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        logout_url = reverse('accounts:logout')
        self.client.post(
            logout_url,
            {'refresh_token': self.refresh_token},
            format='json'
        )

        # Try to refresh with blacklisted token
        response = self.client.post(
            self.refresh_url,
            {'refresh': self.refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REST_FRAMEWORK={
        'DEFAULT_THROTTLE_CLASSES': [],  # Disable throttling for tests
        'DEFAULT_THROTTLE_RATES': {}
    }
)
class UserDetailAPITests(TestCase):
    """Test cases for the user detail API endpoint."""

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

        # Generate access token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_get_user_detail_with_valid_token(self):
        """Test retrieving user details with valid access token."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertIn('id', response.data)
        self.assertIn('auth_provider', response.data)
        self.assertIn('date_joined', response.data)

    def test_get_user_detail_without_authentication(self):
        """Test retrieving user details without authentication."""
        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_detail_with_invalid_token(self):
        """Test retrieving user details with invalid token."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.token.here')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_does_not_expose_password(self):
        """Test that user detail endpoint doesn't expose password."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)

    def test_user_detail_includes_auth_provider(self):
        """Test that user detail includes authentication provider."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['auth_provider'], 'standard')
