"""
Rate limiting utilities for accounts app.

This module provides Redis-backed rate limiting functionality to prevent
abuse of sensitive endpoints like resend verification email.

Security considerations:
- Email addresses are hashed (SHA-256) before using as Redis keys for privacy
- Uses atomic Redis operations for counter incrementation
- Graceful degradation if Redis is unavailable (fail open with logging)
- TTL ensures automatic cleanup of rate limit counters
"""

import hashlib
import logging
from typing import Tuple, Optional

from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

# Rate limiting configuration
RESEND_VERIFICATION_MAX_ATTEMPTS = 3
RESEND_VERIFICATION_WINDOW_SECONDS = 24 * 60 * 60  # 24 hours


def _hash_email(email: str) -> str:
    """
    Hash email address for use in Redis keys.

    Args:
        email: Email address to hash

    Returns:
        str: SHA-256 hash of email (lowercase, hex encoded)

    Example:
        >>> _hash_email('user@example.com')
        'b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514'
    """
    # Normalize email to lowercase before hashing
    email_normalized = email.lower().strip()
    # SHA-256 hash for privacy (one-way function)
    return hashlib.sha256(email_normalized.encode('utf-8')).hexdigest()


def _get_rate_limit_key(email: str) -> str:
    """
    Generate Redis key for rate limiting counter.

    Args:
        email: Email address to generate key for

    Returns:
        str: Redis key for rate limiting counter

    Example:
        >>> _get_rate_limit_key('user@example.com')
        'resend_verification:b4c9a289323b21a01c3e940f150eb9b8c542587f1abfd8f0e1cc1ffc5e475514'
    """
    email_hash = _hash_email(email)
    return f'resend_verification:{email_hash}'


def check_resend_rate_limit(email: str) -> Tuple[bool, Optional[int]]:
    """
    Check if email address has exceeded rate limit for resend verification.

    Args:
        email: Email address to check

    Returns:
        Tuple[bool, Optional[int]]:
            - bool: True if rate limit exceeded, False otherwise
            - int: Seconds until rate limit resets (None if not exceeded)

    Raises:
        None: Exceptions are caught and logged, returns False (fail open)

    Example:
        >>> check_resend_rate_limit('user@example.com')
        (False, None)  # Not exceeded, can proceed
        >>> check_resend_rate_limit('spammer@example.com')
        (True, 43200)  # Exceeded, retry after 12 hours
    """
    try:
        key = _get_rate_limit_key(email)
        current_count = cache.get(key, 0)

        # Check if limit exceeded
        if current_count >= RESEND_VERIFICATION_MAX_ATTEMPTS:
            # Get TTL (time until key expires)
            ttl = cache.ttl(key)
            if ttl is None or ttl < 0:
                # Key expired or doesn't exist, reset
                cache.delete(key)
                return False, None

            logger.warning(
                f"Rate limit exceeded for resend verification. "
                f"Email hash: {_hash_email(email)[:16]}..., "
                f"attempts: {current_count}/{RESEND_VERIFICATION_MAX_ATTEMPTS}, "
                f"retry after: {ttl}s"
            )
            return True, ttl

        return False, None

    except Exception as e:
        # Fail open: Allow request if Redis is unavailable
        logger.error(
            f"Rate limiting check failed for resend verification: {e}. "
            f"Failing open (allowing request).",
            exc_info=True
        )
        return False, None


def increment_resend_counter(email: str) -> int:
    """
    Increment resend verification counter for email address.

    Args:
        email: Email address to increment counter for

    Returns:
        int: New counter value after increment

    Raises:
        None: Exceptions are caught and logged, returns 1 (fail open)

    Side Effects:
        - Creates Redis key with TTL if doesn't exist
        - Increments counter atomically
        - Sets 24-hour expiration on first increment

    Example:
        >>> increment_resend_counter('user@example.com')
        1  # First attempt
        >>> increment_resend_counter('user@example.com')
        2  # Second attempt
    """
    try:
        key = _get_rate_limit_key(email)

        # Use add() to atomically initialize counter if doesn't exist
        # Returns True if key didn't exist, False if it did
        if cache.add(key, 1, timeout=RESEND_VERIFICATION_WINDOW_SECONDS):
            logger.info(
                f"Rate limit counter initialized for resend verification. "
                f"Email hash: {_hash_email(email)[:16]}..."
            )
            return 1

        # Key exists, increment atomically
        try:
            new_count = cache.incr(key)
            logger.info(
                f"Rate limit counter incremented for resend verification. "
                f"Email hash: {_hash_email(email)[:16]}..., "
                f"attempts: {new_count}/{RESEND_VERIFICATION_MAX_ATTEMPTS}"
            )
            return new_count
        except ValueError:
            # Key doesn't exist (rare race condition), initialize
            cache.set(key, 1, timeout=RESEND_VERIFICATION_WINDOW_SECONDS)
            return 1

    except Exception as e:
        # Fail open: Return 1 if Redis is unavailable
        logger.error(
            f"Rate limiting increment failed for resend verification: {e}. "
            f"Failing open (returning 1).",
            exc_info=True
        )
        return 1


def get_remaining_resends(email: str) -> int:
    """
    Get number of remaining resend attempts for email address.

    Args:
        email: Email address to check

    Returns:
        int: Number of remaining attempts (0 if limit exceeded)

    Raises:
        None: Exceptions are caught and logged, returns max attempts (fail open)

    Example:
        >>> get_remaining_resends('user@example.com')
        3  # No attempts yet
        >>> increment_resend_counter('user@example.com')
        1
        >>> get_remaining_resends('user@example.com')
        2  # One attempt used, 2 remaining
    """
    try:
        key = _get_rate_limit_key(email)
        current_count = cache.get(key, 0)
        remaining = max(0, RESEND_VERIFICATION_MAX_ATTEMPTS - current_count)

        logger.debug(
            f"Remaining resend attempts checked. "
            f"Email hash: {_hash_email(email)[:16]}..., "
            f"remaining: {remaining}/{RESEND_VERIFICATION_MAX_ATTEMPTS}"
        )

        return remaining

    except Exception as e:
        # Fail open: Return max attempts if Redis is unavailable
        logger.error(
            f"Rate limiting remaining check failed for resend verification: {e}. "
            f"Failing open (returning max attempts).",
            exc_info=True
        )
        return RESEND_VERIFICATION_MAX_ATTEMPTS


def get_rate_limit_ttl(email: str) -> Optional[int]:
    """
    Get time-to-live (seconds) for rate limit counter.

    Args:
        email: Email address to check

    Returns:
        Optional[int]: Seconds until rate limit resets (None if no limit active)

    Raises:
        None: Exceptions are caught and logged, returns None (fail open)

    Example:
        >>> increment_resend_counter('user@example.com')
        1
        >>> get_rate_limit_ttl('user@example.com')
        86399  # ~24 hours remaining
    """
    try:
        key = _get_rate_limit_key(email)
        ttl = cache.ttl(key)

        if ttl is None or ttl < 0:
            return None

        return ttl

    except Exception as e:
        # Fail open: Return None if Redis is unavailable
        logger.error(
            f"Rate limiting TTL check failed for resend verification: {e}. "
            f"Failing open (returning None).",
            exc_info=True
        )
        return None


def reset_rate_limit(email: str) -> bool:
    """
    Reset rate limit counter for email address.

    This is primarily used for testing and administrative purposes.

    Args:
        email: Email address to reset counter for

    Returns:
        bool: True if reset successful, False otherwise

    Raises:
        None: Exceptions are caught and logged

    Example:
        >>> reset_rate_limit('user@example.com')
        True
    """
    try:
        key = _get_rate_limit_key(email)
        cache.delete(key)

        logger.info(
            f"Rate limit counter reset for resend verification. "
            f"Email hash: {_hash_email(email)[:16]}..."
        )
        return True

    except Exception as e:
        logger.error(
            f"Rate limiting reset failed for resend verification: {e}.",
            exc_info=True
        )
        return False


# Login rate limiting configuration (US-3: Standard User Login)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 5 * 60  # 5 minutes


def _hash_ip(ip_address: str) -> str:
    """
    Hash IP address for use in Redis keys.

    Args:
        ip_address: IP address to hash

    Returns:
        str: SHA-256 hash of IP address (hex encoded)

    Example:
        >>> _hash_ip('192.168.1.100')
        '8d93c3c66f85d3b5c4f2e1a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7'
    """
    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()


def _get_login_rate_limit_key(ip_address: str) -> str:
    """
    Generate Redis key for login rate limiting counter.

    Args:
        ip_address: IP address to generate key for

    Returns:
        str: Redis key for login rate limiting counter

    Example:
        >>> _get_login_rate_limit_key('192.168.1.100')
        'login_attempts:8d93c3c66f85d3b5c4f2e1a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7'
    """
    ip_hash = _hash_ip(ip_address)
    return f'login_attempts:{ip_hash}'


def check_login_rate_limit(ip_address: str) -> Tuple[bool, Optional[int]]:
    """
    Check if IP address has exceeded rate limit for login attempts.

    This function implements IP-based rate limiting to prevent brute force attacks
    on the login endpoint. It uses Redis to track failed login attempts per IP.

    Args:
        ip_address: IP address to check

    Returns:
        Tuple[bool, Optional[int]]:
            - bool: True if rate limit exceeded, False otherwise
            - int: Seconds until rate limit resets (None if not exceeded)

    Raises:
        None: Exceptions are caught and logged, returns False (fail open)

    Example:
        >>> check_login_rate_limit('192.168.1.100')
        (False, None)  # Not exceeded, can proceed
        >>> check_login_rate_limit('10.0.0.5')
        (True, 180)  # Exceeded, retry after 3 minutes

    Security Notes:
        - Rate limiting is per IP, not per email (prevents user enumeration)
        - Gracefully degrades if Redis is unavailable (fail open)
        - IP addresses are hashed before storing in Redis for privacy
    """
    try:
        key = _get_login_rate_limit_key(ip_address)
        current_count = cache.get(key, 0)

        # Check if limit exceeded
        if current_count >= LOGIN_MAX_ATTEMPTS:
            # Get TTL (time until key expires)
            ttl = cache.ttl(key)
            if ttl is None or ttl < 0:
                # Key expired or doesn't exist, reset
                cache.delete(key)
                return False, None

            logger.warning(
                f"Login rate limit exceeded. "
                f"IP hash: {_hash_ip(ip_address)[:16]}..., "
                f"attempts: {current_count}/{LOGIN_MAX_ATTEMPTS}, "
                f"retry after: {ttl}s"
            )
            return True, ttl

        return False, None

    except Exception as e:
        # Fail open: Allow request if Redis is unavailable
        logger.error(
            f"Login rate limiting check failed: {e}. "
            f"Failing open (allowing request).",
            exc_info=True
        )
        return False, None


def increment_login_counter(ip_address: str) -> int:
    """
    Increment login attempt counter for IP address.

    This function should be called after every failed login attempt.
    Successful logins should NOT increment this counter.

    Args:
        ip_address: IP address to increment counter for

    Returns:
        int: New counter value after increment

    Raises:
        None: Exceptions are caught and logged, returns 1 (fail open)

    Side Effects:
        - Creates Redis key with TTL if doesn't exist
        - Increments counter atomically
        - Sets 5-minute expiration on first increment

    Example:
        >>> increment_login_counter('192.168.1.100')
        1  # First failed attempt
        >>> increment_login_counter('192.168.1.100')
        2  # Second failed attempt

    Security Notes:
        - Only increment on FAILED login attempts
        - Counter resets automatically after 5 minutes of no activity
        - Uses atomic Redis operations to prevent race conditions
    """
    try:
        key = _get_login_rate_limit_key(ip_address)

        # Use add() to atomically initialize counter if doesn't exist
        # Returns True if key didn't exist, False if it did
        if cache.add(key, 1, timeout=LOGIN_WINDOW_SECONDS):
            logger.info(
                f"Login rate limit counter initialized. "
                f"IP hash: {_hash_ip(ip_address)[:16]}..."
            )
            return 1

        # Key exists, increment atomically
        try:
            new_count = cache.incr(key)
            logger.info(
                f"Login rate limit counter incremented. "
                f"IP hash: {_hash_ip(ip_address)[:16]}..., "
                f"attempts: {new_count}/{LOGIN_MAX_ATTEMPTS}"
            )
            return new_count
        except ValueError:
            # Key doesn't exist (rare race condition), initialize
            cache.set(key, 1, timeout=LOGIN_WINDOW_SECONDS)
            return 1

    except Exception as e:
        # Fail open: Return 1 if Redis is unavailable
        logger.error(
            f"Login rate limiting increment failed: {e}. "
            f"Failing open (returning 1).",
            exc_info=True
        )
        return 1


def reset_login_rate_limit(ip_address: str) -> bool:
    """
    Reset login rate limit counter for IP address.

    This is primarily used for:
    - Testing purposes
    - Administrative actions (unblock legitimate users)
    - Successful login (optional - counter expires naturally)

    Args:
        ip_address: IP address to reset counter for

    Returns:
        bool: True if reset successful, False otherwise

    Raises:
        None: Exceptions are caught and logged

    Example:
        >>> reset_login_rate_limit('192.168.1.100')
        True

    Note:
        Resetting on successful login is optional. The counter will
        naturally expire after 5 minutes, so explicit reset is not
        required for normal operation.
    """
    try:
        key = _get_login_rate_limit_key(ip_address)
        cache.delete(key)

        logger.info(
            f"Login rate limit counter reset. "
            f"IP hash: {_hash_ip(ip_address)[:16]}..."
        )
        return True

    except Exception as e:
        logger.error(
            f"Login rate limiting reset failed: {e}.",
            exc_info=True
        )
        return False


def get_remaining_login_attempts(ip_address: str) -> int:
    """
    Get number of remaining login attempts for IP address.

    Args:
        ip_address: IP address to check

    Returns:
        int: Number of remaining attempts (0 if limit exceeded)

    Raises:
        None: Exceptions are caught and logged, returns max attempts (fail open)

    Example:
        >>> get_remaining_login_attempts('192.168.1.100')
        5  # No failed attempts yet
        >>> increment_login_counter('192.168.1.100')
        1
        >>> get_remaining_login_attempts('192.168.1.100')
        4  # One failed attempt, 4 remaining

    Use Case:
        Can be used in response headers or error messages to inform
        users how many attempts remain (optional security consideration).
    """
    try:
        key = _get_login_rate_limit_key(ip_address)
        current_count = cache.get(key, 0)
        remaining = max(0, LOGIN_MAX_ATTEMPTS - current_count)

        logger.debug(
            f"Remaining login attempts checked. "
            f"IP hash: {_hash_ip(ip_address)[:16]}..., "
            f"remaining: {remaining}/{LOGIN_MAX_ATTEMPTS}"
        )

        return remaining

    except Exception as e:
        # Fail open: Return max attempts if Redis is unavailable
        logger.error(
            f"Login rate limiting remaining check failed: {e}. "
            f"Failing open (returning max attempts).",
            exc_info=True
        )
        return LOGIN_MAX_ATTEMPTS


def rate_limit(limit: int, window: int):
    """
    Decorator for rate limiting Django REST Framework views.

    Args:
        limit: Maximum number of attempts allowed
        window: Time window in seconds

    Returns:
        Decorated function with rate limiting applied

    Example:
        @rate_limit(limit=5, window=300)
        def post(self, request):
            # View logic here
            pass
    """
    from functools import wraps
    from rest_framework.response import Response
    from rest_framework import status

    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Get IP address from request
            ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip_address:
                ip_address = ip_address.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR', '')

            # Check rate limit
            is_limited, retry_after = check_login_rate_limit(ip_address)

            if is_limited:
                return Response({
                    'error': 'Too many login attempts. Please try again later.',
                    'retry_after': retry_after
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Call the original function
            return func(self, request, *args, **kwargs)

        return wrapper
    return decorator
