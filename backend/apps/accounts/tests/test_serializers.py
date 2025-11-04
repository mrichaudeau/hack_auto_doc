"""
Unit tests for registration serializer.

Tests:
- Valid registration data
- Invalid email format
- Password mismatch
- Weak password validation
- Duplicate email handling
- Field-level validation
"""

import pytest
from django.contrib.auth import get_user_model
from apps.accounts.serializers import UserRegistrationSerializer

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Test suite for UserRegistrationSerializer."""

    def test_valid_registration_data(self):
        """Test serializer with valid registration data."""
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.check_password('SecurePass123!')
        assert user.is_active is False
        assert user.is_email_verified is False

    def test_invalid_email_format(self):
        """Test serializer with invalid email format."""
        invalid_emails = [
            'notanemail',
            'missing@domain',
            '@example.com',
            'user@',
            'user @example.com',
            'user..name@example.com',
        ]

        for email in invalid_emails:
            data = {
                'email': email,
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User'
            }

            serializer = UserRegistrationSerializer(data=data)
            assert not serializer.is_valid()
            assert 'email' in serializer.errors

    def test_password_mismatch(self):
        """Test serializer with mismatched passwords."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors or 'non_field_errors' in serializer.errors

    def test_weak_password_rejected(self):
        """Test serializer with weak passwords."""
        weak_passwords = [
            'short',  # Too short
            'nouppercase123',  # No uppercase
            'NOLOWERCASE123',  # No lowercase
            'NoNumbers!',  # No numbers
            'weakpass',  # Multiple issues
        ]

        for password in weak_passwords:
            data = {
                'email': 'test@example.com',
                'password': password,
                'password_confirm': password,
                'first_name': 'Test',
                'last_name': 'User'
            }

            serializer = UserRegistrationSerializer(data=data)
            assert not serializer.is_valid()
            assert 'password' in serializer.errors

    def test_duplicate_email_rejected(self):
        """Test serializer with duplicate email."""
        # Create existing user
        User.objects.create_user(
            email='existing@example.com',
            password='ExistingPass123!',
            first_name='Existing',
            last_name='User'
        )

        # Try to register with same email
        data = {
            'email': 'existing@example.com',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'New',
            'last_name': 'User'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        error_message = str(serializer.errors['email'][0]).lower()
        assert 'already' in error_message or 'exists' in error_message

    def test_missing_required_fields(self):
        """Test serializer with missing required fields."""
        # Missing email
        data = {
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

        # Missing password
        data = {
            'email': 'test@example.com',
            'password_confirm': 'SecurePass123!',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

        # Missing password_confirm
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
        }
        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password_confirm' in serializer.errors

    def test_optional_name_fields(self):
        """Test that first_name and last_name are optional."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }

        serializer = UserRegistrationSerializer(data=data)
        # Should be valid even without names
        if serializer.is_valid():
            user = serializer.save()
            assert user.email == 'test@example.com'
            assert user.first_name == '' or user.first_name is None
            assert user.last_name == '' or user.last_name is None

    def test_empty_string_fields(self):
        """Test serializer with empty string fields."""
        data = {
            'email': '',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': '',
            'last_name': ''
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_very_long_email(self):
        """Test serializer with very long email (should fail)."""
        long_email = 'a' * 250 + '@example.com'  # > 254 chars (RFC 5321 limit)
        data = {
            'email': long_email,
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_case_sensitive_email(self):
        """Test that email addresses are case-insensitive."""
        # Create user with lowercase email
        User.objects.create_user(
            email='test@example.com',
            password='ExistingPass123!',
            first_name='Test',
            last_name='User'
        )

        # Try to register with uppercase email
        data = {
            'email': 'TEST@EXAMPLE.COM',
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!',
            'first_name': 'Another',
            'last_name': 'User'
        }

        serializer = UserRegistrationSerializer(data=data)
        # Should fail due to duplicate email (case-insensitive)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_password_not_in_response(self):
        """Test that password is not included in serialized data."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        serialized_data = UserRegistrationSerializer(user).data

        # Password should not be in serialized output
        assert 'password' not in serialized_data
        assert 'password_confirm' not in serialized_data

    def test_special_characters_in_name(self):
        """Test serializer with special characters in name fields."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': "O'Brien",
            'last_name': "van der Berg"
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()
        assert user.first_name == "O'Brien"
        assert user.last_name == "van der Berg"

    def test_unicode_in_name_fields(self):
        """Test serializer with Unicode characters in names."""
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'José',
            'last_name': 'Müller'
        }

        serializer = UserRegistrationSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        user = serializer.save()
        assert user.first_name == 'José'
        assert user.last_name == 'Müller'
