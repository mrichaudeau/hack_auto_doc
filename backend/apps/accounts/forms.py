"""
Custom forms for accounts app.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class EmailAdminAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form for Django Admin that uses email instead of username.

    This form overrides the default authentication to use email as the identifier
    instead of username, compatible with our CustomUser model.
    """
    username = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'autofocus': True,
            'placeholder': _('Email address')
        })
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

    def clean(self):
        """
        Override clean to use email instead of username for authentication.
        """
        email = self.cleaned_data.get('username')  # Field is named 'username' but contains email
        password = self.cleaned_data.get('password')

        if email is not None and password:
            # Authenticate using email instead of username
            self.user_cache = authenticate(
                self.request,
                email=email,
                password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
