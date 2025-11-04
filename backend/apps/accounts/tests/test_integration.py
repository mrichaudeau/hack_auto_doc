"""
Integration tests for registration flow.

Tests the complete registration flow from API request to database
persistence to email sending.

Tests:
- Successful registration flow
- Duplicate email handling
- Email task triggering
- Response format validation
- Database state changes
"""

import pytest
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.accounts.models import EmailVerificationToken

User = get_user_model()


@pytest.mark.django_db
class TestRegistrationIntegration:
    """Integration tests for complete registration flow."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()
        self.registration_url = '/api/auth/register/'

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_successful_registration_flow(self, mock_email_task):
        """Test complete successful registration flow."""
        registration_data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        # Verify HTTP response
        assert response.status_code == status.HTTP_201_CREATED
        assert 'email' in response.data
        assert response.data['email'] == 'newuser@example.com'
        assert 'message' in response.data
        assert 'verify' in response.data['message'].lower()

        # Verify user created in database
        assert User.objects.filter(email='newuser@example.com').exists()
        user = User.objects.get(email='newuser@example.com')
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.is_active is False
        assert user.is_email_verified is False
        assert user.check_password('SecurePass123!')

        # Verify verification token created
        assert EmailVerificationToken.objects.filter(user=user).exists()

        # Verify email task was triggered
        mock_email_task.assert_called_once()
        call_args = mock_email_task.call_args[0]
        assert str(user.id) == call_args[0]

    def test_duplicate_email_returns_conflict(self):
        """Test that duplicate email returns 409 Conflict."""
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

        # Should return 400 (validation error) or 409 (conflict)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT
        ]
        assert 'email' in response.data

    def test_invalid_email_returns_bad_request(self):
        """Test that invalid email format returns 400."""
        registration_data = {
            'email': 'invalid-email',
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

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data

    def test_password_mismatch_returns_bad_request(self):
        """Test that password mismatch returns 400."""
        registration_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = self.client.post(
            self.registration_url,
            registration_data,
            format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert ('password' in response.data or
                'password_confirm' in response.data or
                'non_field_errors' in response.data)

    def test_weak_password_returns_bad_request(self):
        """Test that weak password returns 400 with validation errors."""
        registration_data = {
            'email': 'test@example.com',
            'password': 'weak',
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
        assert 'password' in response.data

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_response_format_matches_specification(self, mock_email_task):
        """Test that response format matches API specification."""
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

        # Verify response contains required fields
        assert 'email' in response.data
        assert 'first_name' in response.data
        assert 'last_name' in response.data
        assert 'message' in response.data

        # Verify password NOT in response
        assert 'password' not in response.data
        assert 'password_confirm' not in response.data

        # Verify user is inactive
        user = User.objects.get(email='test@example.com')
        assert user.is_active is False

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_multiple_registrations_independent(self, mock_email_task):
        """Test that multiple registrations are independent."""
        users_data = [
            {
                'email': f'user{i}@example.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': f'User{i}',
                'last_name': 'Test'
            }
            for i in range(3)
        ]

        for user_data in users_data:
            response = self.client.post(
                self.registration_url,
                user_data,
                format='json'
            )
            assert response.status_code == status.HTTP_201_CREATED

        # Verify all users created
        assert User.objects.count() == 3
        for i in range(3):
            assert User.objects.filter(email=f'user{i}@example.com').exists()

    def test_missing_required_fields_returns_bad_request(self):
        """Test that missing required fields returns 400."""
        # Missing email
        response = self.client.post(
            self.registration_url,
            {
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
            },
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Missing password
        response = self.client.post(
            self.registration_url,
            {
                'email': 'test@example.com',
                'password_confirm': 'SecurePass123!',
            },
            format='json'
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('apps.accounts.tasks.send_verification_email.delay')
    def test_email_case_insensitive(self, mock_email_task):
        """Test that email addresses are case-insensitive."""
        # Register with lowercase
        response1 = self.client.post(
            self.registration_url,
            {
                'email': 'test@example.com',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!',
                'first_name': 'Test',
                'last_name': 'User'
            },
            format='json'
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Try to register with uppercase (should fail)
        response2 = self.client.post(
            self.registration_url,
            {
                'email': 'TEST@EXAMPLE.COM',
                'password': 'NewPass123!',
                'password_confirm': 'NewPass123!',
                'first_name': 'Another',
                'last_name': 'User'
            },
            format='json'
        )
        assert response2.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_409_CONFLICT
        ]

        # Verify only one user created
        assert User.objects.count() == 1
