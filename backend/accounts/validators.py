"""
Custom password validators for enhanced security.
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    """
    Validates that a password meets complexity requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        """
        Validate the password against complexity requirements.

        Args:
            password: The password to validate
            user: The user object (optional, for context)

        Raises:
            ValidationError: If password doesn't meet requirements
        """
        errors = []

        # Check minimum length
        if len(password) < self.min_length:
            errors.append(
                _(f"Le mot de passe doit contenir au moins {self.min_length} caractères.")
            )

        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins une lettre majuscule.")
            )

        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append(
                _("Le mot de passe doit contenir au moins une lettre minuscule.")
            )

        # Check for at least one digit
        if not re.search(r'\d', password):
            errors.append(
                _("Le mot de passe doit contenir au moins un chiffre.")
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        """
        Return a help text describing the password requirements.
        """
        return _(
            f"Votre mot de passe doit contenir au moins {self.min_length} caractères, "
            "dont au moins une lettre majuscule, une lettre minuscule et un chiffre."
        )
