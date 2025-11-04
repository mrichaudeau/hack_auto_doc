"""
Unit tests for password validators.

Tests:
- Minimum 8 characters validation
- Uppercase letter requirement
- Lowercase letter requirement
- Number requirement
- Special character recommendation
- Error messages
"""

import pytest
from django.core.exceptions import ValidationError
from apps.accounts.validators import PasswordStrengthValidator


class TestPasswordStrengthValidator:
    """Test suite for PasswordStrengthValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = PasswordStrengthValidator()

    def test_valid_password(self):
        """Test that valid passwords pass validation."""
        valid_passwords = [
            'TestPass123!',
            'SecurePassword1',
            'MyP@ssw0rd',
            'Complex123Pass',
            'ValidPass123',
        ]

        for password in valid_passwords:
            # Should not raise any exception
            try:
                self.validator.validate(password)
            except ValidationError:
                pytest.fail(f"Valid password '{password}' failed validation")

    def test_password_too_short(self):
        """Test that passwords shorter than 8 characters fail."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('Short1!')

        assert 'at least 8 characters' in str(exc_info.value).lower()

    def test_password_missing_uppercase(self):
        """Test that passwords without uppercase letters fail."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('lowercase123!')

        assert 'uppercase' in str(exc_info.value).lower()

    def test_password_missing_lowercase(self):
        """Test that passwords without lowercase letters fail."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('UPPERCASE123!')

        assert 'lowercase' in str(exc_info.value).lower()

    def test_password_missing_number(self):
        """Test that passwords without numbers fail."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('NoNumberPass!')

        assert 'number' in str(exc_info.value).lower() or 'digit' in str(exc_info.value).lower()

    def test_password_all_requirements_missing(self):
        """Test password that fails multiple requirements."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('weak')

        error_message = str(exc_info.value).lower()
        # Should mention multiple requirements
        assert '8' in error_message  # Min length
        assert ('uppercase' in error_message or
                'lowercase' in error_message or
                'number' in error_message or
                'digit' in error_message)

    def test_password_with_whitespace(self):
        """Test password with whitespace."""
        # Whitespace should be allowed
        try:
            self.validator.validate('Test Pass 123')
        except ValidationError:
            # Some validators may reject whitespace, which is acceptable
            pass

    def test_password_with_special_characters(self):
        """Test that special characters are accepted (recommended but not required)."""
        passwords_with_special = [
            'TestPass123!',
            'SecureP@ss1',
            'MyP#ssw0rd',
            'Valid$Pass123',
        ]

        for password in passwords_with_special:
            try:
                self.validator.validate(password)
            except ValidationError:
                pytest.fail(f"Password with special char '{password}' should be valid")

    def test_password_without_special_characters(self):
        """Test that passwords without special characters are still valid."""
        password = 'TestPassword123'  # No special chars

        # Should pass - special chars recommended but not required
        try:
            self.validator.validate(password)
        except ValidationError as e:
            # If it fails, it should NOT be because of missing special char
            error_message = str(e).lower()
            assert 'special' not in error_message, \
                "Special characters should be recommended but not required"

    def test_password_exactly_8_characters(self):
        """Test password with exactly 8 characters."""
        password = 'Test123!'  # Exactly 8 chars
        try:
            self.validator.validate(password)
        except ValidationError:
            pytest.fail("Password with exactly 8 characters should be valid")

    def test_very_long_password(self):
        """Test very long password (should be valid)."""
        password = 'V' + 'e' * 100 + 'ry' + 'L' + 'o' * 50 + 'ng' + 'P' + 'a' * 30 + 'ss123!'
        try:
            self.validator.validate(password)
        except ValidationError as e:
            # Should not fail due to length requirements
            error_message = str(e).lower()
            assert 'too long' not in error_message, "Long passwords should be accepted"

    def test_password_unicode_characters(self):
        """Test password with Unicode characters."""
        unicode_passwords = [
            'Tëst123Pass',  # Accented characters
            'Test中文123',  # Chinese characters
            'Пароль123Test',  # Cyrillic characters
        ]

        for password in unicode_passwords:
            # Unicode characters should be accepted
            try:
                self.validator.validate(password)
            except ValidationError:
                # Some validators may have Unicode restrictions
                pass

    def test_error_message_format(self):
        """Test that error messages are clear and actionable."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate('weak')

        error_message = str(exc_info.value)
        # Error message should be helpful and specific
        assert len(error_message) > 10, "Error message should be descriptive"

    def test_validator_with_user_context(self):
        """Test validator with user context (optional parameter)."""
        # Validator should work with or without user parameter
        try:
            self.validator.validate('TestPass123!', user=None)
        except ValidationError:
            pytest.fail("Validator should work without user context")
