"""
Utility functions for the accounts app.

This module provides helper functions for user account management,
including secure token generation for email verification and password resets.
"""

import secrets


def generate_verification_token():
    """
    Generate a cryptographically random, URL-safe verification token.

    This function uses Python's secrets module to generate a secure random
    token suitable for email verification, password resets, and other
    security-sensitive operations.

    Security Properties:
        - Uses secrets.token_urlsafe() which provides cryptographically strong
          random number generation from the operating system's secure random
          number generator (e.g., /dev/urandom on Unix, CryptGenRandom on Windows)
        - Generates 32 bytes (256 bits) of entropy
        - Encoded using base64url encoding (RFC 4648)
        - Results in a 43-character string (32 bytes * 4/3 ≈ 43 chars after base64)
        - URL-safe: contains only [A-Za-z0-9_-] characters, no special encoding needed
        - Collision probability: 2^-256 (practically impossible)

    Returns:
        str: A 43-character URL-safe random token string

    Example:
        >>> token = generate_verification_token()
        >>> len(token)
        43
        >>> import re
        >>> bool(re.match(r'^[A-Za-z0-9_-]+$', token))
        True

    Note:
        The token should be stored securely (e.g., hashed) in the database
        if it will be used for authentication purposes. For single-use tokens
        like email verification, storing the raw token with an expiration
        time is acceptable.
    """
    return secrets.token_urlsafe(32)
