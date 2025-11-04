"""
Celery tasks for accounts app - async email sending and account operations.
"""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)


@shared_task(
    name='accounts.send_verification_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Retry after 1 minute
)
def send_verification_email(self, user_id, token):
    """
    Send email verification link to user.

    Args:
        user_id (UUID): User ID
        token (UUID): Verification token

    Returns:
        bool: True if email sent successfully, False otherwise

    Raises:
        Exception: If email sending fails after retries
    """
    from .models import CustomUser

    try:
        # Get user
        user = CustomUser.objects.get(id=user_id)

        # Build verification URL
        # In production, this should use the frontend URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{frontend_url}/verify-email?token={token}"

        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': 24,
        }

        # Render email templates
        html_message = render_to_string('accounts/emails/verify_email.html', context)
        plain_message = strip_tags(html_message)

        # Email subject
        subject = _('Verify your email address - Tech Watch Platform')

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Verification email sent to {user.email}")
        return True

    except CustomUser.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False

    except Exception as exc:
        logger.error(f"Failed to send verification email to user {user_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)


@shared_task(
    name='accounts.send_welcome_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_welcome_email(self, user_id):
    """
    Send welcome email after successful email verification.

    Args:
        user_id (UUID): User ID

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    from .models import CustomUser

    try:
        # Get user
        user = CustomUser.objects.get(id=user_id)

        # Email context
        context = {
            'user': user,
            'frontend_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
        }

        # Render email templates
        html_message = render_to_string('accounts/emails/welcome.html', context)
        plain_message = strip_tags(html_message)

        # Email subject
        subject = _('Welcome to Tech Watch Platform!')

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Welcome email sent to {user.email}")
        return True

    except CustomUser.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False

    except Exception as exc:
        logger.error(f"Failed to send welcome email to user {user_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)


@shared_task(
    name='accounts.send_password_reset_email',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def send_password_reset_email(self, user_id, reset_token):
    """
    Send password reset link to user.

    Args:
        user_id (UUID): User ID
        reset_token (str): Password reset token

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    from .models import CustomUser

    try:
        # Get user
        user = CustomUser.objects.get(id=user_id)

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
        html_message = render_to_string('accounts/emails/password_reset.html', context)
        plain_message = strip_tags(html_message)

        # Email subject
        subject = _('Password Reset Request - Tech Watch Platform')

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Password reset email sent to {user.email}")
        return True

    except CustomUser.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return False

    except Exception as exc:
        logger.error(f"Failed to send password reset email to user {user_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)
