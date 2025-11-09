"""
Security logging utilities for authentication events (US-3: Standard User Login).

This module provides centralized logging functionality for all login attempts,
capturing forensic data needed for security incident investigation and pattern detection.

Features:
- Extracts client IP address (handles X-Forwarded-For for proxy/load balancer scenarios)
- Captures user agent strings for device/browser identification
- Creates LoginAuditLog entries with all relevant metadata
- Timezone-aware timestamps
- Graceful handling of missing/malformed headers
- Never logs passwords or sensitive credentials (PII protection)

Security Considerations:
- IP addresses are logged for rate limiting and forensic analysis
- User agents help detect suspicious patterns (automated bots, unusual clients)
- All timestamps are timezone-aware (UTC)
- LoginAuditLog entries are immutable (no updates allowed)
- Logs contain NO passwords or password hashes

Usage:
    from accounts.logging import log_login_attempt

    # In authentication backend
    log_login_attempt(
        user=user,
        email='user@example.com',
        success=True,
        failure_reason=None,
        request=request
    )
"""

import logging
from typing import Optional
from django.http import HttpRequest
from django.contrib.auth import get_user_model

from .models import LoginAuditLog

User = get_user_model()

logger = logging.getLogger('accounts.security')


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address from HTTP request.

    Handles requests behind proxies/load balancers by checking X-Forwarded-For
    header first, then falling back to REMOTE_ADDR.

    Args:
        request: HttpRequest object

    Returns:
        str: Client IP address (IPv4 or IPv6)

    Example:
        >>> get_client_ip(request)
        '192.168.1.100'
        >>> # Behind proxy
        >>> request.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 10.0.0.1'
        >>> get_client_ip(request)
        '203.0.113.1'  # First IP is the real client

    Security Notes:
        - X-Forwarded-For can contain multiple IPs (client, proxy1, proxy2, ...)
        - We take the FIRST IP as the original client IP
        - In production, validate that X-Forwarded-For is set by trusted proxies only
        - Malicious clients can spoof X-Forwarded-For if not behind trusted proxy
    """
    if request is None:
        return '0.0.0.0'

    # Check X-Forwarded-For header (for requests behind proxy/load balancer)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For format: "client, proxy1, proxy2"
        # Take the first IP (client IP)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Direct connection (no proxy)
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

    return ip


def get_user_agent(request: HttpRequest) -> str:
    """
    Extract user agent string from HTTP request.

    User agent identifies the client software (browser, mobile app, bot, etc.)
    and is useful for detecting suspicious patterns like automated attacks.

    Args:
        request: HttpRequest object

    Returns:
        str: User agent string or 'Unknown' if not present

    Example:
        >>> get_user_agent(request)
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...'

    Security Notes:
        - User agents can be spoofed by attackers
        - Use as supplementary forensic data, not primary security mechanism
        - Helps identify legitimate vs automated attack patterns
    """
    if request is None:
        return 'Unknown'

    return request.META.get('HTTP_USER_AGENT', 'Unknown')


def log_login_attempt(
    user: Optional[User],
    email: str,
    success: bool,
    failure_reason: Optional[str],
    request: HttpRequest
) -> LoginAuditLog:
    """
    Log login attempt to LoginAuditLog for security auditing.

    Creates an immutable audit log entry with all relevant metadata for
    forensic analysis and security monitoring. This function should be
    called for EVERY login attempt (success or failure).

    Args:
        user: CustomUser instance (None for non-existent users)
        email: Email address used in login attempt
        success: True if authentication successful, False otherwise
        failure_reason: String reason for failure (or None for success)
            Valid reasons: 'invalid_credentials', 'email_not_verified',
            'rate_limited', 'account_disabled'
        request: HttpRequest object (for IP address and user agent)

    Returns:
        LoginAuditLog: Created audit log entry

    Side Effects:
        - Creates database record in LoginAuditLog table
        - Logs security event to accounts.security logger

    Example:
        >>> # Successful login
        >>> log_login_attempt(
        ...     user=user,
        ...     email='user@example.com',
        ...     success=True,
        ...     failure_reason=None,
        ...     request=request
        ... )

        >>> # Failed login - wrong password
        >>> log_login_attempt(
        ...     user=user,
        ...     email='user@example.com',
        ...     success=False,
        ...     failure_reason='invalid_credentials',
        ...     request=request
        ... )

        >>> # Failed login - user not found
        >>> log_login_attempt(
        ...     user=None,
        ...     email='nonexistent@example.com',
        ...     success=False,
        ...     failure_reason='invalid_credentials',
        ...     request=request
        ... )

    Security Notes:
        - NEVER log passwords or password hashes
        - Log generic 'invalid_credentials' for both wrong password and non-existent user
        - IP addresses and user agents are logged for forensic purposes
        - All timestamps are timezone-aware (UTC)
        - Audit logs are immutable (no updates allowed)
    """
    # Extract request metadata
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # Create audit log entry
    audit_log = LoginAuditLog.objects.create(
        user=user,
        email=email,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason
    )

    # Log to security logger
    if success:
        logger.info(
            f"Login successful: email={email}, "
            f"user_id={user.id if user else None}, "
            f"ip={ip_address[:8]}{'...' if len(ip_address) > 8 else ''}"
        )
    else:
        logger.warning(
            f"Login failed: email={email}, "
            f"reason={failure_reason}, "
            f"ip={ip_address[:8]}{'...' if len(ip_address) > 8 else ''}"
        )

    return audit_log


def log_rate_limit_exceeded(
    email: str,
    ip_address: str,
    user_agent: str,
    request: HttpRequest
) -> LoginAuditLog:
    """
    Log rate limit exceeded event for login attempts.

    Special case of log_login_attempt for rate limiting scenarios.
    Called when IP address exceeds the maximum number of login attempts
    within the rate limit window.

    Args:
        email: Email address used in login attempt
        ip_address: IP address that exceeded rate limit
        user_agent: User agent string
        request: HttpRequest object

    Returns:
        LoginAuditLog: Created audit log entry

    Example:
        >>> log_rate_limit_exceeded(
        ...     email='user@example.com',
        ...     ip_address='192.168.1.100',
        ...     user_agent='Mozilla/5.0...',
        ...     request=request
        ... )

    Security Notes:
        - Rate limited attempts should be monitored for distributed attacks
        - Multiple IPs attempting same account indicates credential stuffing
        - Single IP attempting many accounts indicates account enumeration
    """
    # Try to find user (for audit purposes)
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        user = None

    return log_login_attempt(
        user=user,
        email=email,
        success=False,
        failure_reason='rate_limited',
        request=request
    )
