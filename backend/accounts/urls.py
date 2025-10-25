from django.urls import path, include
from .views import RegisterView, VerifyEmailView, ResendVerificationEmailView

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('auth/register/', RegisterView.as_view(), name='register'),

    # Email Verification
    path('auth/verify-email/<str:key>/', VerifyEmailView.as_view(), name='verify_email'),
    path('auth/resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),

    # Django-allauth URLs (for any remaining allauth functionality)
    path('auth/', include('allauth.urls')),
]
