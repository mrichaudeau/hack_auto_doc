#!/usr/bin/env python
"""
Generate cryptographically secure secrets for Django configuration.

This utility generates random, cryptographically secure secrets suitable for:
- Django SECRET_KEY: Used for cryptographic signing in Django
- JWT_SECRET_KEY: Used for signing JSON Web Tokens

Usage:
    python scripts/generate_secrets.py
    poetry run python scripts/generate_secrets.py

The output format is ready for copying directly to your .env.backend file.
All generated secrets are URL-safe (alphanumeric only) and meet minimum
length requirements (64 characters each).

Security Note:
    Keep these secrets private and never commit them to version control!
    Each environment (dev/staging/prod) should have its own unique secrets.
"""

import secrets
import string


def generate_secret(length=64):
    """
    Generate a cryptographically secure random secret.

    Args:
        length (int): Length of the secret to generate (default: 64 characters)

    Returns:
        str: A random string consisting of letters and digits only (URL-safe)

    Note:
        Uses the secrets module which is designed for generating
        cryptographically strong random numbers suitable for managing
        data such as passwords, account authentication, security tokens,
        and related secrets.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Generated Secrets for Django Configuration")
    print("=" * 70)
    print("\nCopy these values to your .env.backend file:\n")
    print(f"SECRET_KEY={generate_secret(64)}")
    print(f"JWT_SECRET_KEY={generate_secret(64)}")
    print("\n" + "=" * 70)
    print("SECURITY WARNING:")
    print("   - Keep these secrets private and never commit to Git!")
    print("   - Use different secrets for each environment (dev/staging/prod)")
    print("   - Rotate secrets regularly (recommended: every 90 days)")
    print("=" * 70 + "\n")
