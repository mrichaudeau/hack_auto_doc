"""
Django app configuration for accounts app.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Configuration for the accounts application.

    This app handles user authentication, registration, and authorization.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    verbose_name = 'User Accounts & Authentication'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        This is called when Django starts up.
        """
        # Import signals when ready (if we add any later)
        # import apps.accounts.signals
        pass
