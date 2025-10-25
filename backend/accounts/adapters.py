# -*- coding: utf-8 -*-
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for django-allauth to customize email verification URLs.
    Generates frontend URLs instead of backend URLs.
    """

    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Override to return frontend URL for email verification.
        Format: http://localhost:5173/verify-email/<key>
        """
        # Get the confirmation key
        key = emailconfirmation.key

        # Get frontend URL from settings or use default
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        # Return frontend verification URL
        return f"{frontend_url}/verify-email/{key}"
