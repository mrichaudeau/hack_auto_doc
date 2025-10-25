# -*- coding: utf-8 -*-
"""
Integration tests for authentication API endpoints.
Tests registration, email verification, and resend verification flows.
"""
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from allauth.account.models import EmailAddress, EmailConfirmation

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationAPITests(TestCase):
    """Test cases for the registration API endpoint."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.register_url = reverse('accounts:register')
        self.valid_payload = {
            'email': 'newuser@example.com',
            'password': 'SecureP@ssw0rd123!',
            'password_confirm': 'SecureP@ssw0rd123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

    def test_register_user_success(self):
        """Test successful user registration."""
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], self.valid_payload['email'].lower())

        # Verify user was created
        user = User.objects.get(email=self.valid_payload['email'].lower())
        self.assertEqual(user.first_name, self.valid_payload['first_name'])
        self.assertEqual(user.last_name, self.valid_payload['last_name'])
        self.assertFalse(user.is_active)  # Should be inactive until verified

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.valid_payload['email'].lower(), mail.outbox[0].to)

    def test_register_user_with_existing_email(self):
        """Test registration with an email that already exists."""
        # Create existing user
        User.objects.create_user(
            email=self.valid_payload['email'],
            password='ExistingPassword123!'
        )

        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_with_existing_email_different_case(self):
        """Test registration with existing email (different case)."""
        # Create existing user
        User.objects.create_user(
            email='newuser@example.com',
            password='ExistingPassword123!'
        )

        # Try to register with uppercase email
        payload = self.valid_payload.copy()
        payload['email'] = 'NEWUSER@EXAMPLE.COM'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_with_weak_password(self):
        """Test registration with a weak password."""
        payload = self.valid_payload.copy()
        payload['password'] = 'weak'
        payload['password_confirm'] = 'weak'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_register_user_with_mismatched_passwords(self):
        """Test registration with non-matching passwords."""
        payload = self.valid_payload.copy()
        payload['password_confirm'] = 'DifferentPassword123!'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Error is on password_confirm field
        self.assertIn('password_confirm', response.data)

    def test_register_user_with_invalid_email(self):
        """Test registration with an invalid email format."""
        payload = self.valid_payload.copy()
        payload['email'] = 'invalid-email'

        response = self.client.post(self.register_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_user_with_missing_fields(self):
        """Test registration with missing required fields."""
        # Missing email
        payload = self.valid_payload.copy()
        del payload['email']
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing password
        payload = self.valid_payload.copy()
        del payload['password']
        response = self.client.post(self.register_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_creates_email_address_object(self):
        """Test that registration creates an EmailAddress object."""
        response = self.client.post(self.register_url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email=self.valid_payload['email'].lower())
        email_address = EmailAddress.objects.get(user=user)

        self.assertFalse(email_address.verified)
        self.assertTrue(email_address.primary)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationAPITests(TestCase):
    """Test cases for the email verification API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        self.email_address = EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=False
        )

    def test_verify_email_with_valid_key(self):
        """Test email verification with a valid key."""
        # Send confirmation email to get a valid key
        confirmation = EmailConfirmation.create(self.email_address)
        confirmation.sent = timezone.now()  # Set sent timestamp to avoid None + timedelta error
        confirmation.save()
        key = confirmation.key

        verify_url = reverse('accounts:verify_email', kwargs={'key': key})
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertTrue(response.data.get('verified'))

        # Verify user is now active
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Verify email is marked as verified
        self.email_address.refresh_from_db()
        self.assertTrue(self.email_address.verified)

    def test_verify_email_with_invalid_key(self):
        """Test email verification with an invalid key."""
        verify_url = reverse('accounts:verify_email', kwargs={'key': 'invalid-key'})
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_verify_email_already_verified(self):
        """Test verifying an email that's already verified."""
        # Mark email as verified first
        self.email_address.verified = True
        self.email_address.save()
        self.user.is_active = True
        self.user.save()

        # Create new confirmation for the already-verified email
        confirmation = EmailConfirmation.create(self.email_address)
        confirmation.sent = timezone.now()  # Set sent timestamp
        confirmation.save()
        key = confirmation.key

        verify_url = reverse('accounts:verify_email', kwargs={'key': key})
        response = self.client.get(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_verify_email_post_method(self):
        """Test email verification using POST method."""
        # Create confirmation
        confirmation = EmailConfirmation.create(self.email_address)
        confirmation.sent = timezone.now()  # Set sent timestamp
        confirmation.save()
        key = confirmation.key

        verify_url = reverse('accounts:verify_email', kwargs={'key': key})
        response = self.client.post(verify_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('verified'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ResendVerificationEmailAPITests(TestCase):
    """Test cases for the resend verification email API endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.resend_url = reverse('accounts:resend_verification')
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=False
        )
        self.email_address = EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=False
        )

    def test_resend_verification_email_success(self):
        """Test resending verification email successfully."""
        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_resend_verification_email_already_verified(self):
        """Test resending verification email for already verified account."""
        self.email_address.verified = True
        self.email_address.save()
        self.user.is_active = True
        self.user.save()

        response = self.client.post(self.resend_url, {'email': self.user.email}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_resend_verification_email_nonexistent_user(self):
        """Test resending verification email for non-existent user."""
        response = self.client.post(self.resend_url, {'email': 'nonexistent@example.com'}, format='json')

        # Should return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_email_missing_email(self):
        """Test resending verification email without providing email."""
        response = self.client.post(self.resend_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_resend_verification_email_case_insensitive(self):
        """Test resending verification email with different email case."""
        response = self.client.post(self.resend_url, {'email': 'TEST@EXAMPLE.COM'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
