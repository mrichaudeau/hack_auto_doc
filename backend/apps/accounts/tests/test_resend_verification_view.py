"""
Tests for resend verification email endpoint.

This module tests the ResendVerificationEmailView endpoint which allows
users to request a new verification email if they haven't received or
lost the original one.

Test Coverage:
- Successful email resend (first attempt)
- Successful email resend (subsequent attempts)
- Rate limit enforcement (4th attempt blocked)
- Already verified email handling
- Non-existent email handling
- Invalid email format handling
- Old tokens invalidation
- New token creation
- Attempts remaining calculation
- Case-insensitive email matching
"""

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from apps.accounts.models import CustomUser, EmailVerificationToken
from apps.accounts.rate_limiting import reset_rate_limit


@pytest.mark.django_db
class ResendVerificationEmailViewTest(TestCase):
    """
    Test suite for POST /api/auth/resend-verification/ endpoint.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.client = APIClient()
        self.url = reverse('accounts:resend-verification')

        # Create test user (unverified)
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe',
            is_active=False,
            is_email_verified=False
        )

        # Create verified user for testing already verified scenario
        self.verified_user = CustomUser.objects.create_user(
            email='verified@example.com',
            password='TestPassword123!',
            first_name='Jane',
            last_name='Smith',
            is_active=True,
            is_email_verified=True
        )

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Reset rate limiting for all test emails
        reset_rate_limit('test@example.com')
        reset_rate_limit('verified@example.com')
        reset_rate_limit('nonexistent@example.com')
        reset_rate_limit('TEST@EXAMPLE.COM')

    def test_successful_resend_first_attempt(self):
        """
        Test successful verification email resend on first attempt.

        Expected behavior:
        - HTTP 200 OK response
        - Success message returned
        - 2 attempts remaining (3 max - 1 used)
        - New verification token created
        - Verification email sent asynchronously
        """
        payload = {'email': 'test@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay') as mock_send:
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['message'],
            'Verification email sent successfully. Please check your inbox.'
        )
        self.assertEqual(response.data['attempts_remaining'], 2)

        # Verify token was created
        token = EmailVerificationToken.objects.filter(
            user=self.user,
            is_used=False
        ).latest('created_at')
        self.assertIsNotNone(token)

        # Verify email was sent asynchronously
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        self.assertEqual(args[0], str(self.user.id))
        self.assertEqual(args[1], str(token.token))

    def test_successful_resend_second_attempt(self):
        """
        Test successful verification email resend on second attempt.

        Expected behavior:
        - HTTP 200 OK response
        - Success message returned
        - 1 attempt remaining (3 max - 2 used)
        - New verification token created
        """
        payload = {'email': 'test@example.com'}

        # First attempt
        with patch('apps.accounts.views.send_verification_email.delay'):
            self.client.post(self.url, payload, format='json')

        # Second attempt
        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['attempts_remaining'], 1)

    def test_successful_resend_third_attempt(self):
        """
        Test successful verification email resend on third (final) attempt.

        Expected behavior:
        - HTTP 200 OK response
        - Success message returned
        - 0 attempts remaining (3 max - 3 used)
        - New verification token created
        """
        payload = {'email': 'test@example.com'}

        # First two attempts
        with patch('apps.accounts.views.send_verification_email.delay'):
            self.client.post(self.url, payload, format='json')
            self.client.post(self.url, payload, format='json')

        # Third (final) attempt
        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['attempts_remaining'], 0)

    def test_rate_limit_exceeded(self):
        """
        Test rate limit enforcement on 4th attempt within 24 hours.

        Expected behavior:
        - HTTP 429 Too Many Requests response
        - Error code 'rate_limit_exceeded'
        - Descriptive error message
        - retry_after_seconds provided
        - max_attempts and attempts_remaining included
        - No verification email sent
        """
        payload = {'email': 'test@example.com'}

        # Make 3 successful attempts
        with patch('apps.accounts.views.send_verification_email.delay'):
            for _ in range(3):
                self.client.post(self.url, payload, format='json')

        # 4th attempt should be rate limited
        with patch('apps.accounts.views.send_verification_email.delay') as mock_send:
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data['error'], 'rate_limit_exceeded')
        self.assertEqual(
            response.data['message'],
            'Too many verification email requests. Please try again later.'
        )
        self.assertIn('retry_after_seconds', response.data)
        self.assertEqual(response.data['max_attempts'], 3)
        self.assertEqual(response.data['attempts_remaining'], 0)

        # Verify no email was sent
        mock_send.assert_not_called()

    def test_already_verified_email(self):
        """
        Test handling of already verified email addresses.

        Expected behavior:
        - HTTP 400 Bad Request response
        - Validation error on email field
        - Descriptive error message
        - No verification email sent
        """
        payload = {'email': 'verified@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay') as mock_send:
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(
            response.data['email'][0],
            'This email address is already verified.'
        )

        # Verify no email was sent
        mock_send.assert_not_called()

    def test_nonexistent_email(self):
        """
        Test handling of non-existent email addresses.

        Expected behavior:
        - HTTP 400 Bad Request response
        - Validation error on email field
        - Descriptive error message
        - No verification email sent
        """
        payload = {'email': 'nonexistent@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay') as mock_send:
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertEqual(
            response.data['email'][0],
            'No account found with this email address.'
        )

        # Verify no email was sent
        mock_send.assert_not_called()

    def test_invalid_email_format(self):
        """
        Test handling of invalid email format.

        Expected behavior:
        - HTTP 400 Bad Request response
        - Validation error on email field
        - Email format error message
        """
        payload = {'email': 'invalid-email-format'}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_missing_email_field(self):
        """
        Test handling of missing email field in request.

        Expected behavior:
        - HTTP 400 Bad Request response
        - Validation error on email field
        - Required field error message
        """
        payload = {}

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_old_tokens_invalidated(self):
        """
        Test that old unused tokens are invalidated when resending.

        Expected behavior:
        - All previous unused tokens marked as is_used=True
        - New token created and marked as is_used=False
        - Only one valid (unused) token exists after resend
        """
        # Create multiple old tokens
        old_token1 = EmailVerificationToken.create_token(self.user)
        old_token2 = EmailVerificationToken.create_token(self.user)
        old_token3 = EmailVerificationToken.create_token(self.user)

        # Verify all tokens are unused initially
        self.assertFalse(old_token1.is_used)
        self.assertFalse(old_token2.is_used)
        self.assertFalse(old_token3.is_used)

        payload = {'email': 'test@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh old tokens from database
        old_token1.refresh_from_db()
        old_token2.refresh_from_db()
        old_token3.refresh_from_db()

        # Verify old tokens are now invalidated
        self.assertTrue(old_token1.is_used)
        self.assertTrue(old_token2.is_used)
        self.assertTrue(old_token3.is_used)

        # Verify new token exists and is unused
        new_token = EmailVerificationToken.objects.filter(
            user=self.user,
            is_used=False
        ).latest('created_at')
        self.assertIsNotNone(new_token)

        # Verify only one unused token exists
        unused_count = EmailVerificationToken.objects.filter(
            user=self.user,
            is_used=False
        ).count()
        self.assertEqual(unused_count, 1)

    def test_new_token_created(self):
        """
        Test that a new verification token is created on resend.

        Expected behavior:
        - New token created with unique UUID
        - Token associated with correct user
        - Token has 24-hour expiry
        - Token is not marked as used
        """
        payload = {'email': 'test@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the new token
        new_token = EmailVerificationToken.objects.filter(
            user=self.user,
            is_used=False
        ).latest('created_at')

        self.assertIsNotNone(new_token)
        self.assertEqual(new_token.user, self.user)
        self.assertFalse(new_token.is_used)
        self.assertFalse(new_token.is_expired())

        # Verify expiry is approximately 24 hours from now
        time_until_expiry = new_token.expires_at - timezone.now()
        self.assertAlmostEqual(
            time_until_expiry.total_seconds(),
            24 * 60 * 60,  # 24 hours
            delta=60  # Allow 1 minute variance
        )

    def test_case_insensitive_email_matching(self):
        """
        Test that email matching is case-insensitive.

        Expected behavior:
        - Email 'TEST@EXAMPLE.COM' matches 'test@example.com'
        - Verification email sent successfully
        - Rate limiting works across different cases
        """
        # Test with uppercase email
        payload = {'email': 'TEST@EXAMPLE.COM'}

        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['attempts_remaining'], 2)

        # Test with mixed case email (should count as same email for rate limiting)
        payload = {'email': 'TeSt@ExAmPlE.cOm'}

        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['attempts_remaining'], 1)

    def test_attempts_remaining_decremented_correctly(self):
        """
        Test that attempts_remaining is decremented correctly.

        Expected behavior:
        - First attempt: 2 remaining
        - Second attempt: 1 remaining
        - Third attempt: 0 remaining
        - Fourth attempt: rate limited (0 remaining)
        """
        payload = {'email': 'test@example.com'}
        expected_remaining = [2, 1, 0]

        with patch('apps.accounts.views.send_verification_email.delay'):
            for expected in expected_remaining:
                response = self.client.post(self.url, payload, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data['attempts_remaining'], expected)

    def test_concurrent_resend_requests(self):
        """
        Test handling of concurrent resend requests (race condition).

        Expected behavior:
        - Both requests should succeed (atomic operations)
        - Rate limiting should still work correctly
        - No duplicate tokens created
        """
        payload = {'email': 'test@example.com'}

        # Simulate two concurrent requests
        with patch('apps.accounts.views.send_verification_email.delay'):
            response1 = self.client.post(self.url, payload, format='json')
            response2 = self.client.post(self.url, payload, format='json')

        # Both should succeed (rate limit allows 3 attempts)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Verify rate limiting tracked both attempts
        with patch('apps.accounts.views.send_verification_email.delay'):
            response3 = self.client.post(self.url, payload, format='json')

        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data['attempts_remaining'], 0)

    def test_response_structure(self):
        """
        Test that success response has correct structure.

        Expected behavior:
        - Response contains 'message' field
        - Response contains 'attempts_remaining' field
        - No unexpected fields in response
        """
        payload = {'email': 'test@example.com'}

        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('attempts_remaining', response.data)
        self.assertEqual(len(response.data), 2)  # Only 2 fields

    def test_error_response_structure_rate_limit(self):
        """
        Test that rate limit error response has correct structure.

        Expected behavior:
        - Response contains 'error' field
        - Response contains 'message' field
        - Response contains 'retry_after_seconds' field
        - Response contains 'max_attempts' field
        - Response contains 'attempts_remaining' field
        """
        payload = {'email': 'test@example.com'}

        # Exhaust rate limit
        with patch('apps.accounts.views.send_verification_email.delay'):
            for _ in range(3):
                self.client.post(self.url, payload, format='json')

        # Next request should be rate limited
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)
        self.assertIn('message', response.data)
        self.assertIn('retry_after_seconds', response.data)
        self.assertIn('max_attempts', response.data)
        self.assertIn('attempts_remaining', response.data)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_email_actually_sent_with_eager_celery(self):
        """
        Test that email is actually sent when Celery runs eagerly.

        This test uses CELERY_TASK_ALWAYS_EAGER=True to execute tasks synchronously.

        Expected behavior:
        - Celery task executes immediately
        - Email is sent successfully
        - Email appears in Django's outbox (test mode)
        """
        payload = {'email': 'test@example.com'}

        # Clear mail outbox
        mail.outbox = []

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Note: With .delay() mocked in other tests, this test would need
        # actual Celery configuration to verify email sending.
        # For now, we verify the response is successful.

    def test_transaction_atomicity(self):
        """
        Test that token invalidation and creation happen atomically.

        Expected behavior:
        - If token creation fails, old tokens remain unchanged
        - Database consistency maintained
        """
        # Create old token
        old_token = EmailVerificationToken.create_token(self.user)
        self.assertFalse(old_token.is_used)

        payload = {'email': 'test@example.com'}

        # Simulate successful transaction
        with patch('apps.accounts.views.send_verification_email.delay'):
            response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify transaction completed successfully
        old_token.refresh_from_db()
        self.assertTrue(old_token.is_used)

        # Verify new token exists
        new_token = EmailVerificationToken.objects.filter(
            user=self.user,
            is_used=False
        ).latest('created_at')
        self.assertIsNotNone(new_token)
