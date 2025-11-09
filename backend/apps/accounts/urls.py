"""
URL configuration for accounts app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

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

    # US-3: JWT Token Refresh (TASK-3.7)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Additional URLs will be added in subsequent tasks (login, password reset, etc.)
]
