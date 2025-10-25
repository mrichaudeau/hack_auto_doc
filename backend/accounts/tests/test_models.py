# -*- coding: utf-8 -*-
"""
Unit tests for the CustomUser model.
Tests user creation, email uniqueness, password hashing, and default values.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class CustomUserModelTests(TestCase):
    """Test cases for the CustomUser model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

    def test_create_user_with_email(self):
        """Test creating a user with an email is successful."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        self.assertEqual(user.email, self.user_data['email'].lower())
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_active)  # Default for standard accounts
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_normalized_to_lowercase(self):
        """Test that email addresses are converted to lowercase."""
        email_uppercase = 'Test@EXAMPLE.COM'
        user = User.objects.create_user(
            email=email_uppercase,
            password=self.user_data['password']
        )

        self.assertEqual(user.email, email_uppercase.lower())

    def test_email_uniqueness_case_insensitive(self):
        """Test that duplicate emails (different case) are rejected."""
        # Create first user
        User.objects.create_user(
            email='test@example.com',
            password=self.user_data['password']
        )

        # Try to create user with same email (different case)
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email='TEST@EXAMPLE.COM',
                password=self.user_data['password']
            )

    def test_create_user_without_email_raises_error(self):
        """Test that creating a user without an email raises ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email='',
                password=self.user_data['password']
            )

    def test_password_is_hashed(self):
        """Test that password is properly hashed."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        # Password should not be stored in plaintext
        self.assertNotEqual(user.password, self.user_data['password'])
        # But check_password should work
        self.assertTrue(user.check_password(self.user_data['password']))
        # And wrong password should fail
        self.assertFalse(user.check_password('WrongPassword123!'))

    def test_default_auth_provider_is_standard(self):
        """Test that default auth_provider is 'standard'."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        self.assertEqual(user.auth_provider, User.AuthProvider.STANDARD)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!',
            first_name='Admin',
            last_name='User'
        )

        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.email, 'admin@example.com')

    def test_user_string_representation(self):
        """Test the string representation of the user."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        self.assertEqual(str(user), self.user_data['email'].lower())

    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name='John',
            last_name='Doe'
        )

        self.assertEqual(user.get_full_name(), 'John Doe')

    def test_get_full_name_with_empty_fields(self):
        """Test get_full_name with empty first_name or last_name."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name='',
            last_name=''
        )

        self.assertEqual(user.get_full_name(), '')

    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name='John',
            last_name='Doe'
        )

        self.assertEqual(user.get_short_name(), 'John')

    def test_auth_provider_choices(self):
        """Test different auth_provider values."""
        # Standard
        user_standard = User.objects.create_user(
            email='standard@example.com',
            password=self.user_data['password'],
            auth_provider=User.AuthProvider.STANDARD
        )
        self.assertEqual(user_standard.auth_provider, 'standard')

        # Entra ID
        user_entra = User.objects.create_user(
            email='entra@example.com',
            password=self.user_data['password'],
            auth_provider=User.AuthProvider.ENTRA_ID
        )
        self.assertEqual(user_entra.auth_provider, 'entra_id')

        # Unified
        user_unified = User.objects.create_user(
            email='unified@example.com',
            password=self.user_data['password'],
            auth_provider=User.AuthProvider.UNIFIED
        )
        self.assertEqual(user_unified.auth_provider, 'unified')

    def test_is_active_default_false_for_standard_users(self):
        """Test that is_active defaults to False for standard users."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        self.assertFalse(user.is_active)

    def test_user_can_be_activated(self):
        """Test that a user can be activated after creation."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password']
        )

        self.assertFalse(user.is_active)

        user.is_active = True
        user.save()

        # Retrieve from database
        user_from_db = User.objects.get(email=self.user_data['email'].lower())
        self.assertTrue(user_from_db.is_active)
