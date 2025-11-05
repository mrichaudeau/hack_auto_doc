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


@shared_task(
    name='accounts.cleanup_expired_verification_tokens',
    bind=True,
    max_retries=3,
    default_retry_delay=60
)
def cleanup_expired_verification_tokens(self, dry_run=False):
    """
    Clean up expired and old used email verification tokens.

    Runs daily to prevent database bloat from expired tokens.
    Deletes tokens that are either:
    - Already used (is_used=True) AND created_at < 7 days ago
    - Expired (expires_at < now)

    Args:
        dry_run (bool): If True, only count tokens without deleting

    Returns:
        dict: Statistics about the cleanup operation with keys:
            - deleted (int): Number of tokens deleted (0 if dry_run)
            - would_delete (int): Number of tokens that would be deleted (only if dry_run)
            - expired_count (int): Number of expired tokens
            - used_count (int): Number of old used tokens
            - dry_run (bool): Whether this was a dry run
            - timestamp (str): ISO timestamp of cleanup (only if not dry_run)
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Q
    from .models import EmailVerificationToken

    logger.info("Starting cleanup of expired verification tokens")

    try:
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        # Find used tokens older than 7 days
        old_used_tokens = EmailVerificationToken.objects.filter(
            is_used=True,
            created_at__lt=seven_days_ago
        )

        # Find expired tokens (any age)
        expired_tokens = EmailVerificationToken.objects.filter(
            expires_at__lt=now
        )

        # Count by type for detailed logging
        expired_count = expired_tokens.filter(is_used=False).count()
        used_count = old_used_tokens.count()

        # Combine queries (OR condition) - union of both sets
        tokens_to_delete = old_used_tokens | expired_tokens

        total_count = tokens_to_delete.count()

        if dry_run:
            logger.info(f"[DRY RUN] Would delete {total_count} verification tokens "
                       f"(expired: {expired_count}, old used: {used_count})")
            return {
                'deleted': 0,
                'would_delete': total_count,
                'expired_count': expired_count,
                'used_count': used_count,
                'dry_run': True
            }

        if total_count > 0:
            # Bulk delete for efficiency
            deleted_count, _ = tokens_to_delete.delete()
            logger.info(
                f"Deleted {deleted_count} verification tokens "
                f"(expired: {expired_count}, old used: {used_count})"
            )
        else:
            deleted_count = 0
            logger.info("No expired or old used verification tokens to delete")

        return {
            'deleted': deleted_count,
            'expired_count': expired_count,
            'used_count': used_count,
            'dry_run': False,
            'timestamp': now.isoformat()
        }

    except Exception as exc:
        logger.error(f"Error during token cleanup: {exc}", exc_info=True)
        # Retry with exponential backoff (60s, 120s, 180s)
        raise self.retry(exc=exc, countdown=60)
