"""
URL configuration for subscriptions API endpoints.

Registers SubjectViewSet with Django REST Framework router for automatic
URL pattern generation:
- GET /api/admin/subjects/ - List subjects
- POST /api/admin/subjects/ - Create subject
- GET /api/admin/subjects/{id}/ - Retrieve subject
- PATCH /api/admin/subjects/{id}/ - Partial update subject
- PUT /api/admin/subjects/{id}/ - Full update subject
- DELETE /api/admin/subjects/{id}/ - Archive subject
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubjectViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'subjects', SubjectViewSet, basename='subject')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
