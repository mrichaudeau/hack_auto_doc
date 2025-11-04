"""
Custom password validators for the authentication system.

Implements password validation rules as specified in US-1:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (recommended)
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class MinimumLengthValidator:
    """
    Validate that the password is at least 8 characters long.
    """
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters."
            % {'min_length': self.min_length}
        )


class UppercaseValidator:
    """
    Validate that the password contains at least one uppercase letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter (A-Z)."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Your password must contain at least one uppercase letter (A-Z).")


class LowercaseValidator:
    """
    Validate that the password contains at least one lowercase letter.
    """
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter (a-z)."),
                code='password_no_lower',
            )

    def get_help_text(self):
        return _("Your password must contain at least one lowercase letter (a-z).")


class NumberValidator:
    """
    Validate that the password contains at least one numeric digit.
    """
    def validate(self, password, user=None):
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one number (0-9)."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Your password must contain at least one number (0-9).")


class SpecialCharacterValidator:
    """
    Validate that the password contains at least one special character.

    Special characters: !@#$%^&*()_+-=[]{}|;:,.<>?
    """
    def __init__(self, special_chars=r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]'):
        self.special_chars = special_chars

    def validate(self, password, user=None):
        if not re.search(self.special_chars, password):
            raise ValidationError(
                _("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Your password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?).")


class PasswordStrengthValidator:
    """
    Comprehensive password strength validator that combines all rules.

    This validator ensures passwords meet the following requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character (recommended)
    """
    def validate(self, password, user=None):
        errors = []

        # Minimum length check
        if len(password) < 8:
            errors.append(_("Password must be at least 8 characters long."))

        # Uppercase check
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))

        # Lowercase check
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))

        # Number check
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one number."))

        # Special character check (recommended, not enforced)
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            # This is a warning, not an error - special chars are recommended but not required
            pass

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, including "
            "at least one uppercase letter, one lowercase letter, and one number. "
            "Special characters are recommended for added security."
        )


def validate_password_strength(password):
    """
    Convenience function to validate password strength.

    Args:
        password (str): The password to validate

    Raises:
        ValidationError: If the password doesn't meet requirements

    Returns:
        dict: Password strength analysis with score and feedback
    """
    validator = PasswordStrengthValidator()
    validator.validate(password)

    # Calculate strength score (0-100)
    score = 0

    # Length scoring (max 40 points)
    if len(password) >= 8:
        score += 20
    if len(password) >= 12:
        score += 10
    if len(password) >= 16:
        score += 10

    # Character variety scoring (max 60 points)
    if re.search(r'[A-Z]', password):
        score += 15  # Uppercase
    if re.search(r'[a-z]', password):
        score += 15  # Lowercase
    if re.search(r'\d', password):
        score += 15  # Numbers
    if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        score += 15  # Special chars

    # Determine strength label
    if score >= 80:
        strength = 'strong'
    elif score >= 60:
        strength = 'medium'
    else:
        strength = 'weak'

    return {
        'score': score,
        'strength': strength,
        'feedback': {
            'length': len(password),
            'has_uppercase': bool(re.search(r'[A-Z]', password)),
            'has_lowercase': bool(re.search(r'[a-z]', password)),
            'has_numbers': bool(re.search(r'\d', password)),
            'has_special': bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password)),
        }
    }
