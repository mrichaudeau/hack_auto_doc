"""
URL configuration for accounts app.
"""

from django.urls import path
from .views import UserRegistrationView

app_name = 'accounts'

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    # Additional URLs will be added in subsequent tasks
]
