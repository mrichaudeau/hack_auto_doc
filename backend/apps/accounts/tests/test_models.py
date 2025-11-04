"""
Unit tests for CustomUser model.

Tests:
- User creation with email as username
- Email normalization
- Password hashing (Argon2)
- User manager methods
- Model validation
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestCustomUserModel:
    """Test suite for CustomUser model."""

    def test_create_user_with_email(self):
        """Test creating a user with email as username."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.is_active is False  # Inactive until email verified
        assert user.is_email_verified is False
        assert user.check_password('TestPassword123!')
        assert str(user) == 'test@example.com'

    def test_email_normalization(self):
        """Test that email addresses are normalized (lowercase domain)."""
        user = User.objects.create_user(
            email='test@EXAMPLE.COM',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        # Django's normalize_email lowercases the domain part
        assert user.email == 'test@example.com'

    def test_password_hashed_with_argon2(self):
        """Test that passwords are hashed using Argon2."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        # Argon2 hashes start with $argon2
        assert user.password.startswith('$argon2')
        assert user.password != 'TestPassword123!'
        assert user.check_password('TestPassword123!')

    def test_create_superuser(self):
        """Test creating a superuser."""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!',
            first_name='Admin',
            last_name='User'
        )

        assert superuser.is_superuser is True
        assert superuser.is_staff is True
        assert superuser.is_active is True  # Superuser is active by default

    def test_email_required(self):
        """Test that email is required."""
        with pytest.raises(TypeError):
            User.objects.create_user(
                email=None,
                password='TestPassword123!'
            )

    def test_duplicate_email_rejected(self):
        """Test that duplicate emails are rejected."""
        User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        # Attempt to create another user with the same email
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='test@example.com',
                password='DifferentPassword123!',
                first_name='Another',
                last_name='User'
            )

    def test_verify_email_method(self):
        """Test verify_email method activates user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        assert user.is_active is False
        assert user.is_email_verified is False

        user.verify_email()

        assert user.is_active is True
        assert user.is_email_verified is True

    def test_user_without_password(self):
        """Test that users can be created without a password (for social auth)."""
        user = User.objects.create_user(
            email='test@example.com',
            password=None,
            first_name='Test',
            last_name='User'
        )

        assert user.email == 'test@example.com'
        assert not user.has_usable_password()

    def test_username_field_is_email(self):
        """Test that USERNAME_FIELD is set to email."""
        assert User.USERNAME_FIELD == 'email'
        assert User.REQUIRED_FIELDS == ['first_name', 'last_name']

    def test_user_str_representation(self):
        """Test string representation of user."""
        user = User(email='test@example.com')
        assert str(user) == 'test@example.com'

    def test_empty_email_rejected(self):
        """Test that empty email is rejected."""
        with pytest.raises((ValueError, ValidationError, TypeError)):
            User.objects.create_user(
                email='',
                password='TestPassword123!',
                first_name='Test',
                last_name='User'
            )
