"""
URL configuration for public subscriptions API endpoints (US-2).

Provides public browsing access to active subject catalog for discovery
before subscription. No authentication required.

Endpoints:
- GET /api/subjects/ - List active subjects (paginated, alphabetical)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PublicSubjectViewSet

# Create router and register public viewsets
router = DefaultRouter()
router.register(r'subjects', PublicSubjectViewSet, basename='public-subject')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
