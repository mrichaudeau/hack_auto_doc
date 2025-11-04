from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Core infrastructure app configuration.

    This app houses infrastructure-level migrations and configurations
    that don't belong to specific feature apps, such as:
    - Database extension enablement (pgvector)
    - Cross-cutting concerns
    - Infrastructure-level models and utilities
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core Infrastructure'
