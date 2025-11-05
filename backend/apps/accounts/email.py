"""
Email service utilities for the accounts app.

This module provides high-level email sending functions that integrate with
Django's email backend and Celery for asynchronous email delivery.

All email sending is done asynchronously via Celery tasks to avoid blocking
HTTP requests and provide automatic retry logic for transient failures.
"""

import logging
from typing import Optional
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import CustomUser, EmailVerificationToken

logger = logging.getLogger(__name__)


def send_verification_email(user: CustomUser, token: EmailVerificationToken, async_send: bool = True) -> bool:
    """
    Send email verification link to user.

    This function creates and sends an email with a verification link that allows
    users to verify their email address. The email includes both HTML and plain text
    versions for maximum compatibility.

    Email Features:
        - Responsive HTML design (mobile-friendly)
        - Clear call-to-action button
        - Alternative text link for clients that don't support buttons
        - Professional branding (Tech Watch Platform)
        - Expiry warning (24 hours)
        - Plain text fallback for email clients without HTML support

    Args:
        user (CustomUser): The user to send the verification email to
        token (EmailVerificationToken): The verification token to include in the email
        async_send (bool): If True, send via Celery task (default). If False, send synchronously.

    Returns:
        bool: True if email was successfully queued/sent, False if there was an error

    Example:
        >>> from apps.accounts.models import CustomUser, EmailVerificationToken
        >>> user = CustomUser.objects.get(email='user@example.com')
        >>> token = EmailVerificationToken.create_token(user)
        >>> success = send_verification_email(user, token)
        >>> if success:
        ...     print("Verification email sent successfully")

    Note:
        - This function uses async Celery task by default for better performance
        - Set async_send=False for synchronous sending (useful for testing)
        - The verification URL format is: {FRONTEND_URL}/verify-email?token={token}
        - Email delivery failures are automatically retried (3 attempts with exponential backoff)
    """
    try:
        # Build verification URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={token.token}"

        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': 24,
        }

        # Render email templates
        html_content = render_to_string('accounts/emails/verify_email.html', context)
        text_content = strip_tags(html_content)

        # Email subject
        subject = 'Verify your email address - Tech Watch Platform'

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")

        if async_send:
            # Send asynchronously via Celery task
            from .tasks import send_verification_email as send_verification_email_task
            send_verification_email_task.delay(str(user.id), str(token.token))
            logger.info(f"Verification email queued for {user.email}")
        else:
            # Send synchronously (for testing or when Celery is not available)
            email.send(fail_silently=False)
            logger.info(f"Verification email sent to {user.email}")

        return True

    except Exception as exc:
        logger.error(f"Failed to send verification email to {user.email}: {str(exc)}", exc_info=True)
        return False


def send_welcome_email(user: CustomUser, async_send: bool = True) -> bool:
    """
    Send welcome email after successful email verification.

    This function sends a welcome email to users after they have successfully
    verified their email address. The email welcomes them to the platform and
    provides next steps.

    Args:
        user (CustomUser): The user to send the welcome email to
        async_send (bool): If True, send via Celery task (default). If False, send synchronously.

    Returns:
        bool: True if email was successfully queued/sent, False if there was an error

    Example:
        >>> from apps.accounts.models import CustomUser
        >>> user = CustomUser.objects.get(email='user@example.com')
        >>> success = send_welcome_email(user)
        >>> if success:
        ...     print("Welcome email sent successfully")
    """
    try:
        # Email context
        context = {
            'user': user,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
        }

        # Render email templates
        html_content = render_to_string('accounts/emails/welcome.html', context)
        text_content = strip_tags(html_content)

        # Email subject
        subject = 'Welcome to Tech Watch Platform!'

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")

        if async_send:
            # Send asynchronously via Celery task
            from .tasks import send_welcome_email as send_welcome_email_task
            send_welcome_email_task.delay(str(user.id))
            logger.info(f"Welcome email queued for {user.email}")
        else:
            # Send synchronously (for testing or when Celery is not available)
            email.send(fail_silently=False)
            logger.info(f"Welcome email sent to {user.email}")

        return True

    except Exception as exc:
        logger.error(f"Failed to send welcome email to {user.email}: {str(exc)}", exc_info=True)
        return False


def send_password_reset_email(user: CustomUser, reset_token: str, async_send: bool = True) -> bool:
    """
    Send password reset link to user.

    This function sends an email with a password reset link that allows users
    to reset their password. The email includes both HTML and plain text versions.

    Args:
        user (CustomUser): The user to send the password reset email to
        reset_token (str): The password reset token to include in the email
        async_send (bool): If True, send via Celery task (default). If False, send synchronously.

    Returns:
        bool: True if email was successfully queued/sent, False if there was an error

    Example:
        >>> from apps.accounts.models import CustomUser
        >>> from apps.accounts.utils import generate_verification_token
        >>> user = CustomUser.objects.get(email='user@example.com')
        >>> reset_token = generate_verification_token()
        >>> success = send_password_reset_email(user, reset_token)
        >>> if success:
        ...     print("Password reset email sent successfully")

    Note:
        - Password reset tokens expire in 1 hour
        - The reset URL format is: {FRONTEND_URL}/reset-password?token={reset_token}
    """
    try:
        # Build reset URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        # Email context
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 1,  # Password reset tokens expire in 1 hour
        }

        # Render email templates
        html_content = render_to_string('accounts/emails/password_reset.html', context)
        text_content = strip_tags(html_content)

        # Email subject
        subject = 'Password Reset Request - Tech Watch Platform'

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")

        if async_send:
            # Send asynchronously via Celery task
            from .tasks import send_password_reset_email as send_password_reset_email_task
            send_password_reset_email_task.delay(str(user.id), reset_token)
            logger.info(f"Password reset email queued for {user.email}")
        else:
            # Send synchronously (for testing or when Celery is not available)
            email.send(fail_silently=False)
            logger.info(f"Password reset email sent to {user.email}")

        return True

    except Exception as exc:
        logger.error(f"Failed to send password reset email to {user.email}: {str(exc)}", exc_info=True)
        return False


def send_email_with_template(
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: list,
    async_send: bool = True
) -> bool:
    """
    Generic function to send emails using Django templates.

    This is a utility function that can be used to send any email with
    HTML and plain text versions. It's useful for custom email types
    not covered by the specific functions above.

    Args:
        subject (str): Email subject line
        template_name (str): Template path relative to templates directory (without .html extension)
        context (dict): Context variables to pass to the template
        recipient_list (list): List of recipient email addresses
        async_send (bool): If True, send asynchronously (not implemented for generic emails)

    Returns:
        bool: True if email was successfully sent, False if there was an error

    Example:
        >>> success = send_email_with_template(
        ...     subject='Test Email',
        ...     template_name='accounts/emails/test_email.html',
        ...     context={'user': user},
        ...     recipient_list=['user@example.com']
        ... )

    Note:
        - This function does not use Celery for async sending (async_send parameter is ignored)
        - For production use cases, consider creating dedicated Celery tasks
    """
    try:
        # Render email templates
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
        )
        email.attach_alternative(html_content, "text/html")

        # Send synchronously (async not implemented for generic function)
        email.send(fail_silently=False)
        logger.info(f"Email sent to {', '.join(recipient_list)}")

        return True

    except Exception as exc:
        logger.error(f"Failed to send email: {str(exc)}", exc_info=True)
        return False
