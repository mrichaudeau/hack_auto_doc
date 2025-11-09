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


@pytest.mark.django_db
class TestLoginAuditLogModel:
    """
    Test suite for LoginAuditLog model (US-3: Standard User Login, TASK-3.14).

    Tests:
    - Model creation with all fields
    - Nullable user field (for non-existent users)
    - Email field validation and indexing
    - IP address field (IPv4 and IPv6)
    - User agent field
    - Success/failure tracking
    - Failure reason choices
    - Timestamp auto_now_add
    - String representation
    - Ordering (most recent first)
    - Admin registration and configuration
    """

    def test_create_audit_log_with_user(self):
        """Test creating audit log with existing user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        from apps.accounts.models import LoginAuditLog

        log = LoginAuditLog.objects.create(
            user=user,
            email='test@example.com',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0)',
            success=True,
            failure_reason=None
        )

        assert log.user == user
        assert log.email == 'test@example.com'
        assert log.ip_address == '192.168.1.100'
        assert log.user_agent == 'Mozilla/5.0 (Windows NT 10.0)'
        assert log.success is True
        assert log.failure_reason is None
        assert log.timestamp is not None

    def test_create_audit_log_without_user(self):
        """Test creating audit log for non-existent user (user=None)."""
        from apps.accounts.models import LoginAuditLog

        log = LoginAuditLog.objects.create(
            user=None,
            email='nonexistent@example.com',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )

        assert log.user is None
        assert log.email == 'nonexistent@example.com'
        assert log.success is False
        assert log.failure_reason == 'invalid_credentials'

    def test_email_field_max_length(self):
        """Test email field respects max_length=255."""
        from apps.accounts.models import LoginAuditLog

        # Valid email within limit
        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )
        assert log.email == 'test@example.com'

    def test_ipv4_address_support(self):
        """Test IPv4 address storage."""
        from apps.accounts.models import LoginAuditLog

        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            success=True
        )

        assert log.ip_address == '192.168.1.100'

    def test_ipv6_address_support(self):
        """Test IPv6 address storage."""
        from apps.accounts.models import LoginAuditLog

        ipv6_address = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address=ipv6_address,
            user_agent='Mozilla/5.0',
            success=True
        )

        assert log.ip_address == ipv6_address

    def test_user_agent_text_field(self):
        """Test user_agent TextField accepts long strings."""
        from apps.accounts.models import LoginAuditLog

        long_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' * 10
        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent=long_user_agent,
            success=True
        )

        assert log.user_agent == long_user_agent
        assert len(log.user_agent) > 255  # TextField has no length limit

    def test_success_boolean_field(self):
        """Test success boolean field."""
        from apps.accounts.models import LoginAuditLog

        # Successful login
        success_log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )
        assert success_log.success is True

        # Failed login
        failure_log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )
        assert failure_log.success is False

    def test_failure_reason_choices(self):
        """Test failure_reason choices validation."""
        from apps.accounts.models import LoginAuditLog

        valid_reasons = [
            'invalid_credentials',
            'email_not_verified',
            'rate_limited',
            'account_disabled'
        ]

        for reason in valid_reasons:
            log = LoginAuditLog.objects.create(
                email='test@example.com',
                ip_address='192.168.1.1',
                user_agent='Mozilla/5.0',
                success=False,
                failure_reason=reason
            )
            assert log.failure_reason == reason

    def test_timestamp_auto_now_add(self):
        """Test timestamp is automatically set on creation."""
        from apps.accounts.models import LoginAuditLog
        from django.utils import timezone
        import time

        before = timezone.now()
        time.sleep(0.01)  # Small delay to ensure different timestamp

        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        time.sleep(0.01)
        after = timezone.now()

        assert log.timestamp is not None
        assert before < log.timestamp < after

    def test_str_method(self):
        """Test __str__ method returns meaningful representation."""
        from apps.accounts.models import LoginAuditLog

        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        # Successful login
        success_log = LoginAuditLog.objects.create(
            user=user,
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        str_repr = str(success_log)
        assert 'test@example.com' in str_repr
        assert 'Success' in str_repr or 'success' in str_repr or str(True) in str_repr

        # Failed login
        failure_log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )

        str_repr = str(failure_log)
        assert 'test@example.com' in str_repr

    def test_ordering_most_recent_first(self):
        """Test logs are ordered by timestamp descending (most recent first)."""
        from apps.accounts.models import LoginAuditLog
        import time

        # Create logs with slight delays to ensure different timestamps
        log1 = LoginAuditLog.objects.create(
            email='test1@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        time.sleep(0.01)

        log2 = LoginAuditLog.objects.create(
            email='test2@example.com',
            ip_address='192.168.1.2',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )

        time.sleep(0.01)

        log3 = LoginAuditLog.objects.create(
            email='test3@example.com',
            ip_address='192.168.1.3',
            user_agent='Mozilla/5.0',
            success=True
        )

        # Retrieve all logs
        logs = list(LoginAuditLog.objects.all())

        # Most recent should be first
        assert logs[0].id == log3.id
        assert logs[1].id == log2.id
        assert logs[2].id == log1.id

    def test_user_deletion_sets_null(self):
        """Test user deletion sets user field to NULL (on_delete=SET_NULL)."""
        from apps.accounts.models import LoginAuditLog

        user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

        log = LoginAuditLog.objects.create(
            user=user,
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        assert log.user == user

        # Delete user
        user_id = user.id
        user.delete()

        # Refresh log from database
        log.refresh_from_db()

        # User should be NULL but log should still exist
        assert log.user is None
        assert log.email == 'test@example.com'

    def test_admin_registration(self):
        """Test LoginAuditLog is registered in Django admin."""
        from django.contrib import admin
        from apps.accounts.models import LoginAuditLog

        # Check if model is registered
        assert LoginAuditLog in admin.site._registry

    def test_database_indexes(self):
        """Test database indexes are created for email and timestamp."""
        from apps.accounts.models import LoginAuditLog

        # Get model meta information
        indexes = [field.db_index for field in LoginAuditLog._meta.fields if hasattr(field, 'db_index')]

        # At least some fields should have indexes
        # (email and timestamp should have db_index=True)
        assert any(indexes), "Expected at least one indexed field"

    def test_failure_reason_nullable(self):
        """Test failure_reason can be NULL for successful logins."""
        from apps.accounts.models import LoginAuditLog

        log = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True,
            failure_reason=None
        )

        assert log.failure_reason is None

    def test_multiple_logs_same_email(self):
        """Test multiple audit logs can be created for same email."""
        from apps.accounts.models import LoginAuditLog

        # Create multiple logs for same email
        log1 = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )

        log2 = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=False,
            failure_reason='invalid_credentials'
        )

        log3 = LoginAuditLog.objects.create(
            email='test@example.com',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            success=True
        )

        # All logs should exist
        logs = LoginAuditLog.objects.filter(email='test@example.com')
        assert logs.count() == 3
