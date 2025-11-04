"""
User models for authentication system.

This module defines the custom User model that extends Django's AbstractUser
to use email as the primary identifier instead of username.
"""

import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Custom User model that uses email as the username field.

    This model extends Django's AbstractUser to implement email-based
    authentication. The email field is unique and required, while the
    username field is disabled.

    Attributes:
        id (UUID): Primary key, automatically generated UUID
        email (str): User's email address, used for authentication (unique)
        first_name (str): User's first name
        last_name (str): User's last name
        is_active (bool): Whether the account is active (email verified)
        is_verified (bool): Whether the email has been verified
        date_joined (datetime): When the account was created
        last_login (datetime): Last login timestamp
    """

    # Override id to use UUID
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the user")
    )

    # Override email to make it required and unique
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("An account with this email already exists."),
        },
        help_text=_("User's email address, used for authentication")
    )

    # Disable username field (we use email instead)
    username = None

    # Email verification status
    is_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_("Designates whether this user's email has been verified.")
    )

    # Email verification timestamp
    email_verified_at = models.DateTimeField(
        _('email verified at'),
        null=True,
        blank=True,
        help_text=_("When the email was verified")
    )

    # Set email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Required for createsuperuser

    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email'], name='idx_user_email'),
            models.Index(fields=['is_active'], name='idx_user_active'),
            models.Index(fields=['is_verified'], name='idx_user_verified'),
        ]

    def __str__(self):
        """String representation of the user."""
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.email.split('@')[0]

    @property
    def is_email_verified(self):
        """Check if email has been verified."""
        return self.is_verified

    def verify_email(self):
        """
        Mark the user's email as verified and activate the account.
        """
        from django.utils import timezone
        self.is_verified = True
        self.is_active = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'is_active', 'email_verified_at'])


class EmailVerificationToken(models.Model):
    """
    Model to store email verification tokens.

    Tokens are single-use and expire after 24 hours.

    Attributes:
        user (CustomUser): The user this token belongs to
        token (str): The verification token (UUID)
        created_at (datetime): When the token was created
        expires_at (datetime): When the token expires
        is_used (bool): Whether the token has been used
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=_("Verification token")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the token was created")
    )

    expires_at = models.DateTimeField(
        help_text=_("When the token expires")
    )

    is_used = models.BooleanField(
        default=False,
        help_text=_("Whether the token has been used")
    )

    class Meta:
        db_table = 'email_verification_tokens'
        verbose_name = _('email verification token')
        verbose_name_plural = _('email verification tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token'], name='idx_token'),
            models.Index(fields=['user', 'is_used'], name='idx_user_token'),
        ]

    def __str__(self):
        """String representation of the token."""
        return f"Token for {self.user.email} ({self.token})"

    def is_expired(self):
        """Check if the token has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired()

    @classmethod
    def create_token(cls, user):
        """
        Create a new verification token for a user.

        Args:
            user (CustomUser): The user to create a token for

        Returns:
            EmailVerificationToken: The created token
        """
        from datetime import timedelta
        from django.utils import timezone

        # Token expires in 24 hours
        expires_at = timezone.now() + timedelta(hours=24)

        token = cls.objects.create(
            user=user,
            expires_at=expires_at
        )

        return token
