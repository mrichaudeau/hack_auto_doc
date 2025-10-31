"""
Django application configuration for veille_tech.
"""

from django.apps import AppConfig


class VeilleTechConfig(AppConfig):
    """Configuration for the veille_tech Django application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'veille_tech'
    verbose_name = 'Technology Watch Platform'

    def ready(self):
        """
        Perform initialization when Django starts.

        This includes validating environment configuration to ensure all
        required variables are present and properly formatted.
        """
        # Import here to avoid AppRegistryNotReady exception
        from veille_tech.config_validator import should_validate, validate_environment

        # Only validate for web server and worker processes
        # Skip for management commands that don't need external services
        if should_validate():
            try:
                validate_environment()
            except Exception as e:
                # Print error and re-raise to prevent application startup
                import sys
                print(f"\nFATAL: Configuration validation failed: {e}\n", file=sys.stderr)
                raise
