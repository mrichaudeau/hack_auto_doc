"""
Custom authentication backends for email-based login (US-3: Standard User Login).

This module implements EmailBackend, which:
- Authenticates users with email instead of username
- Enforces email verification requirement (is_email_verified=True)
- Logs all authentication attempts to LoginAuditLog for security auditing
- Prevents account enumeration by using generic error messages
- Implements constant-time comparison where possible to prevent timing attacks

Security Features:
- Case-insensitive email lookup
- Email verification enforcement
- Comprehensive audit logging
- Generic error messages (prevents user enumeration)
- Timing attack mitigation

Usage:
    Add to settings/base.py:
    AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from typing import Optional

from .logging import log_login_attempt

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users by email instead of username.

    Features:
    - Case-insensitive email lookup
    - Password validation using Django's check_password
    - Email verification enforcement (is_email_verified must be True)
    - Comprehensive audit logging for all attempts (success and failure)
    - Security logging with IP address and user agent
    - Generic error messages to prevent account enumeration

    Security Considerations:
    - Returns None for all failure scenarios (doesn't distinguish between invalid
      email, wrong password, unverified email to prevent user enumeration)
    - Logs all attempts to LoginAuditLog with specific failure reasons
    - Uses constant-time password comparison (via check_password)
    - Captures IP address and user agent for forensic analysis

    Usage:
        # In settings/base.py
        AUTHENTICATION_BACKENDS = ['accounts.backends.EmailBackend']

        # In views
        from django.contrib.auth import authenticate
        user = authenticate(request, email='user@example.com', password='password')
    """

    def authenticate(
        self,
        request,
        email: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> Optional[User]:
        """
        Authenticate user by email and password.

        Args:
            request: HttpRequest object (for IP/user agent logging)
            email: User email address
            password: User password (plain text)
            **kwargs: Additional keyword arguments (ignored)

        Returns:
            User instance if authentication successful, None otherwise

        Side Effects:
            Creates LoginAuditLog entry for every attempt

        Example:
            >>> user = EmailBackend().authenticate(request, email='user@example.com', password='password123')
            >>> if user:
            ...     print(f"Logged in as {user.email}")
        """
        # Validate required parameters
        if email is None or password is None:
            return None

        try:
            # Case-insensitive email lookup
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # User not found - log with generic failure reason to prevent enumeration
            log_login_attempt(
                user=None,
                email=email,
                success=False,
                failure_reason='invalid_credentials',
                request=request
            )
            return None

        # Verify password (uses constant-time comparison internally)
        if not user.check_password(password):
            # Invalid password - log with generic failure reason
            log_login_attempt(
                user=user,
                email=email,
                success=False,
                failure_reason='invalid_credentials',
                request=request
            )
            return None

        # Check email verification status
        if not user.is_email_verified:
            # Email not verified - log with specific reason
            log_login_attempt(
                user=user,
                email=email,
                success=False,
                failure_reason='email_not_verified',
                request=request
            )
            return None

        # Check if account is disabled
        if not user.is_active:
            # Account disabled - log with specific reason
            log_login_attempt(
                user=user,
                email=email,
                success=False,
                failure_reason='account_disabled',
                request=request
            )
            return None

        # Authentication successful - log success
        log_login_attempt(
            user=user,
            email=email,
            success=True,
            failure_reason=None,
            request=request
        )

        return user

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Retrieve user by primary key.

        This method is called by Django authentication framework to retrieve
        the user object from the user_id stored in the session.

        Args:
            user_id: User primary key

        Returns:
            User instance if found, None otherwise

        Example:
            >>> user = EmailBackend().get_user(1)
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
