from django.urls import path, include
from .views import RegisterView

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('auth/register/', RegisterView.as_view(), name='register'),

    # Django-allauth URLs (includes email verification endpoints)
    path('auth/', include('allauth.urls')),
]
