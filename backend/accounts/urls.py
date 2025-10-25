from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    VerifyEmailView,
    ResendVerificationEmailView,
    LoginView,
    LogoutView,
    UserDetailView
)

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('auth/register/', RegisterView.as_view(), name='register'),

    # Email Verification
    path('auth/verify-email/<str:key>/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),

    # Authentication
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User Profile
    path('users/me/', UserDetailView.as_view(), name='user_detail'),
]
