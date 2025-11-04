"""
URL configuration for accounts app.
"""

from django.urls import path
from .views import (
    UserRegistrationView,
    EmailVerificationView,
    ResendVerificationEmailView
)

app_name = 'accounts'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    # Additional URLs will be added in subsequent tasks (login, password reset, etc.)
]
