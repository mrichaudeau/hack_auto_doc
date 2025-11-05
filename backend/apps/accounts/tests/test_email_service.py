"""
Tests for email service integration (TASK-2.6).

This module tests the email sending functionality including:
- Verification email sending
- Welcome email sending
- Password reset email sending
- Email template rendering
- Async email sending via Celery
- Error handling
"""

from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core import mail
from django.conf import settings

from apps.accounts.models import CustomUser, EmailVerificationToken
from apps.accounts.email import (
    send_verification_email,
    send_welcome_email,
    send_password_reset_email,
    send_email_with_template
)


class EmailServiceTestCase(TestCase):
    """
    Test case for email service functionality.

    Tests the email sending functions in apps.accounts.email module,
    including verification emails, welcome emails, and password reset emails.
    """

    def setUp(self):
        """Set up test data."""
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.token = EmailVerificationToken.create_token(self.user)

    def tearDown(self):
        """Clean up test data."""
        # Clear mailbox after each test
        mail.outbox = []

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_verification_email_sync(self):
        """Test sending verification email synchronously."""
        # Send email synchronously (async_send=False)
        success = send_verification_email(self.user, self.token, async_send=False)

        # Verify email was sent
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Verify your email address - Tech Watch Platform')
        self.assertEqual(email.to, [self.user.email])
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)

        # Verify verification URL is in email body
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={self.token.token}"
        self.assertIn(verification_url, email.body)

        # Verify HTML alternative exists
        self.assertEqual(len(email.alternatives), 1)
        html_content, content_type = email.alternatives[0]
        self.assertEqual(content_type, 'text/html')
        self.assertIn(verification_url, html_content)

        # Verify expiry notice
        self.assertIn('24 hours', email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('apps.accounts.email.send_verification_email_task')
    def test_send_verification_email_async(self, mock_celery_task):
        """Test sending verification email asynchronously via Celery."""
        # Send email asynchronously (async_send=True)
        success = send_verification_email(self.user, self.token, async_send=True)

        # Verify Celery task was called
        self.assertTrue(success)
        mock_celery_task.delay.assert_called_once_with(str(self.user.id), str(self.token.token))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_verification_email_html_template(self):
        """Test verification email HTML template rendering."""
        # Send email
        send_verification_email(self.user, self.token, async_send=False)
        email = mail.outbox[0]

        # Get HTML content
        html_content, content_type = email.alternatives[0]

        # Verify HTML elements
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('Tech Watch Platform', html_content)
        self.assertIn(self.user.first_name, html_content)
        self.assertIn('Verify Email Address', html_content)

        # Verify responsive design elements
        self.assertIn('max-width: 600px', html_content)  # Mobile-friendly
        self.assertIn('class="button"', html_content)  # CTA button

        # Verify alternative text link
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={self.token.token}"
        self.assertIn(verification_url, html_content)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_welcome_email_sync(self):
        """Test sending welcome email synchronously."""
        # Send welcome email
        success = send_welcome_email(self.user, async_send=False)

        # Verify email was sent
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Welcome to Tech Watch Platform!')
        self.assertEqual(email.to, [self.user.email])
        self.assertIn(self.user.first_name, email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('apps.accounts.email.send_welcome_email_task')
    def test_send_welcome_email_async(self, mock_celery_task):
        """Test sending welcome email asynchronously via Celery."""
        # Send email asynchronously
        success = send_welcome_email(self.user, async_send=True)

        # Verify Celery task was called
        self.assertTrue(success)
        mock_celery_task.delay.assert_called_once_with(str(self.user.id))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_password_reset_email_sync(self):
        """Test sending password reset email synchronously."""
        reset_token = 'test-reset-token-abc123'

        # Send password reset email
        success = send_password_reset_email(self.user, reset_token, async_send=False)

        # Verify email was sent
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        # Verify email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Password Reset Request - Tech Watch Platform')
        self.assertEqual(email.to, [self.user.email])

        # Verify reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        self.assertIn(reset_url, email.body)

        # Verify expiry notice (1 hour for password reset)
        self.assertIn('1 hour', email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    @patch('apps.accounts.email.send_password_reset_email_task')
    def test_send_password_reset_email_async(self, mock_celery_task):
        """Test sending password reset email asynchronously via Celery."""
        reset_token = 'test-reset-token-abc123'

        # Send email asynchronously
        success = send_password_reset_email(self.user, reset_token, async_send=True)

        # Verify Celery task was called
        self.assertTrue(success)
        mock_celery_task.delay.assert_called_once_with(str(self.user.id), reset_token)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_email_with_template(self):
        """Test generic email sending with custom template."""
        # Send generic email
        context = {
            'user': self.user,
            'message': 'This is a test message'
        }
        success = send_email_with_template(
            subject='Test Email',
            template_name='accounts/emails/verify_email.html',
            context=context,
            recipient_list=[self.user.email],
            async_send=False
        )

        # Verify email was sent
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)

        # Verify email
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Test Email')
        self.assertEqual(email.to, [self.user.email])

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_failure_handling(self):
        """Test graceful error handling when email sending fails."""
        # Mock send method to raise exception
        with patch('django.core.mail.EmailMultiAlternatives.send', side_effect=Exception('SMTP error')):
            success = send_verification_email(self.user, self.token, async_send=False)

            # Verify function returns False on failure
            self.assertFalse(success)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        FRONTEND_URL='https://app.techwatch.com'
    )
    def test_frontend_url_configuration(self):
        """Test that FRONTEND_URL setting is properly used in emails."""
        # Send email
        send_verification_email(self.user, self.token, async_send=False)
        email = mail.outbox[0]

        # Verify production URL is used
        self.assertIn('https://app.techwatch.com', email.body)
        self.assertNotIn('http://localhost:3000', email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_plain_text_fallback(self):
        """Test that plain text version is generated from HTML."""
        # Send email
        send_verification_email(self.user, self.token, async_send=False)
        email = mail.outbox[0]

        # Verify plain text body exists
        self.assertIsNotNone(email.body)
        self.assertGreater(len(email.body), 0)

        # Verify plain text doesn't contain HTML tags
        self.assertNotIn('<html>', email.body)
        self.assertNotIn('<div>', email.body)
        self.assertNotIn('<p>', email.body)

        # Verify plain text contains key information
        self.assertIn(self.user.first_name, email.body)
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={self.token.token}"
        self.assertIn(verification_url, email.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_from_address(self):
        """Test that emails use correct FROM address."""
        # Send email
        send_verification_email(self.user, self.token, async_send=False)
        email = mail.outbox[0]

        # Verify FROM address
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_multiple_emails_sent_sequentially(self):
        """Test sending multiple emails in sequence."""
        # Create additional users
        user2 = CustomUser.objects.create_user(
            email='user2@example.com',
            first_name='User',
            last_name='Two',
            password='testpass123'
        )
        token2 = EmailVerificationToken.create_token(user2)

        # Send multiple emails
        send_verification_email(self.user, self.token, async_send=False)
        send_verification_email(user2, token2, async_send=False)

        # Verify both emails were sent
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertEqual(mail.outbox[1].to, [user2.email])


class EmailConfigurationTestCase(TestCase):
    """Test case for email configuration in Django settings."""

    def test_email_backend_configured(self):
        """Test that EMAIL_BACKEND is configured."""
        self.assertIsNotNone(settings.EMAIL_BACKEND)
        # In tests, should use locmem or console backend
        self.assertIn('Backend', settings.EMAIL_BACKEND)

    def test_default_from_email_configured(self):
        """Test that DEFAULT_FROM_EMAIL is configured."""
        self.assertIsNotNone(settings.DEFAULT_FROM_EMAIL)
        self.assertIn('@', settings.DEFAULT_FROM_EMAIL)

    def test_frontend_url_configured(self):
        """Test that FRONTEND_URL is configured."""
        self.assertIsNotNone(settings.FRONTEND_URL)
        self.assertTrue(settings.FRONTEND_URL.startswith('http'))

    def test_email_host_configured(self):
        """Test that EMAIL_HOST is configured."""
        self.assertIsNotNone(settings.EMAIL_HOST)

    def test_email_port_configured(self):
        """Test that EMAIL_PORT is configured."""
        self.assertIsNotNone(settings.EMAIL_PORT)
        self.assertIsInstance(settings.EMAIL_PORT, int)
