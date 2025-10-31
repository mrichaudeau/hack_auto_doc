"""
Environment configuration validator for Django application.

This module validates required environment variables at startup to prevent
runtime failures due to missing or invalid configuration.
"""

import os
import re
import sys
from typing import List, Tuple
from urllib.parse import urlparse


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class EnvironmentValidator:
    """Validates environment configuration at application startup."""

    # Required environment variables that must not be empty or placeholder values
    REQUIRED_VARS = [
        'GOOGLE_AI_STUDIO_API_KEY',
        'FIRECRAWL_API_KEY',
    ]

    # Required variables that have acceptable defaults but should be checked
    IMPORTANT_VARS = [
        'SECRET_KEY',
        'JWT_SECRET_KEY',
    ]

    # Placeholder patterns that indicate configuration was not completed
    PLACEHOLDER_PATTERNS = [
        r'your-.*-key-here',
        r'your-.*-api-key',
        r'change-in-production',
        r'your_.*_here',
        r'placeholder',
    ]

    # URL format validation patterns
    URL_PATTERNS = {
        'DATABASE_URL': r'^postgresql://[\w\-]+:[\w\-]+@[\w\-\.]+:\d+/[\w\-]+$',
        'REDIS_CACHE_URL': r'^redis://[\w\-\.]+:\d+/\d+$',
        'CELERY_BROKER_URL': r'^redis://[\w\-\.]+:\d+/\d+$',
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Validate all environment configuration.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        self._validate_required_variables()
        self._validate_important_variables()
        self._validate_url_formats()
        self._validate_api_keys()

        return len(self.errors) == 0

    def _validate_required_variables(self):
        """Check that all required variables are present and not empty."""
        for var in self.REQUIRED_VARS:
            value = os.environ.get(var, '').strip()

            if not value:
                self.errors.append(
                    f"Missing required environment variable: {var}\n"
                    f"  Please set this variable in .env.backend file.\n"
                    f"  See docs/setup/environment_variables.md for details."
                )
            elif self._is_placeholder(value):
                self.errors.append(
                    f"Environment variable {var} contains placeholder value: {value}\n"
                    f"  Please replace with actual API key from provider.\n"
                    f"  See docs/setup/environment_variables.md for links to obtain keys."
                )

    def _validate_important_variables(self):
        """Check important variables and warn about insecure values."""
        for var in self.IMPORTANT_VARS:
            value = os.environ.get(var, '').strip()

            if not value:
                self.warnings.append(
                    f"Important variable {var} is not set.\n"
                    f"  Using default value, but this is not recommended for production."
                )
            elif len(value) < 50:
                self.warnings.append(
                    f"Variable {var} is too short (min 50 characters recommended).\n"
                    f"  Generate secure secret with: python backend/scripts/generate_secrets.py"
                )
            elif self._is_placeholder(value):
                self.errors.append(
                    f"Variable {var} contains placeholder value: {value}\n"
                    f"  Generate secure secret with: python backend/scripts/generate_secrets.py"
                )

    def _validate_url_formats(self):
        """Validate URL format for database and cache connection strings."""
        for var, pattern in self.URL_PATTERNS.items():
            value = os.environ.get(var, '').strip()

            if value and not re.match(pattern, value):
                self.errors.append(
                    f"Invalid format for {var}: {value}\n"
                    f"  Expected format: {self._get_url_format_example(var)}\n"
                    f"  See docs/setup/environment_variables.md for examples."
                )

    def _validate_api_keys(self):
        """Validate API key formats for known providers."""
        # Google AI Studio keys start with 'AIzaSy'
        google_key = os.environ.get('GOOGLE_AI_STUDIO_API_KEY', '').strip()
        if google_key and not google_key.startswith('AIzaSy'):
            self.warnings.append(
                f"GOOGLE_AI_STUDIO_API_KEY does not match expected format.\n"
                f"  Google AI Studio keys typically start with 'AIzaSy'.\n"
                f"  If you're sure this is correct, you can ignore this warning.\n"
                f"  Get valid key from: https://makersuite.google.com/app/apikey"
            )

        # Firecrawl keys start with 'fc-'
        firecrawl_key = os.environ.get('FIRECRAWL_API_KEY', '').strip()
        if firecrawl_key and not firecrawl_key.startswith('fc-'):
            self.warnings.append(
                f"FIRECRAWL_API_KEY does not match expected format.\n"
                f"  Firecrawl keys typically start with 'fc-'.\n"
                f"  If you're sure this is correct, you can ignore this warning.\n"
                f"  Get valid key from: https://firecrawl.dev/"
            )

    def _is_placeholder(self, value: str) -> bool:
        """Check if value matches placeholder patterns."""
        value_lower = value.lower()
        return any(re.search(pattern, value_lower) for pattern in self.PLACEHOLDER_PATTERNS)

    def _get_url_format_example(self, var: str) -> str:
        """Get example URL format for variable."""
        examples = {
            'DATABASE_URL': 'postgresql://username:password@host:5432/database',
            'REDIS_CACHE_URL': 'redis://host:6379/1',
            'CELERY_BROKER_URL': 'redis://host:6379/0',
        }
        return examples.get(var, 'See documentation')

    def print_report(self):
        """Print validation report to stderr."""
        if self.errors or self.warnings:
            print("\n" + "="*70, file=sys.stderr)
            print("ENVIRONMENT CONFIGURATION VALIDATION REPORT", file=sys.stderr)
            print("="*70, file=sys.stderr)

        if self.errors:
            print("\nERRORS (must be fixed):", file=sys.stderr)
            for i, error in enumerate(self.errors, 1):
                print(f"\n{i}. {error}", file=sys.stderr)

        if self.warnings:
            print("\nWARNINGS (should be addressed):", file=sys.stderr)
            for i, warning in enumerate(self.warnings, 1):
                print(f"\n{i}. {warning}", file=sys.stderr)

        if self.errors or self.warnings:
            print("\n" + "="*70, file=sys.stderr)
            print("For detailed configuration reference, see:", file=sys.stderr)
            print("  docs/setup/environment_variables.md", file=sys.stderr)
            print("="*70 + "\n", file=sys.stderr)


def validate_environment() -> bool:
    """
    Validate environment configuration and print report.

    Returns:
        bool: True if validation passes, False if there are errors.

    Raises:
        ConfigurationError: If validation fails and application should not start.
    """
    validator = EnvironmentValidator()
    is_valid = validator.validate()

    # Always print report if there are errors or warnings
    if validator.errors or validator.warnings:
        validator.print_report()

    if not is_valid:
        raise ConfigurationError(
            "Environment configuration validation failed. "
            "Please fix the errors above before starting the application."
        )

    return True


# Skip validation for certain management commands
SKIP_VALIDATION_COMMANDS = [
    'makemigrations',
    'migrate',
    'shell',
    'shell_plus',
    'dbshell',
    'createsuperuser',
    'collectstatic',
    'check',
    'help',
    'showmigrations',
    'sqlmigrate',
]


def should_validate() -> bool:
    """
    Determine if configuration validation should run.

    Skips validation for management commands that don't need external services.
    """
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command in SKIP_VALIDATION_COMMANDS:
            return False
    return True
