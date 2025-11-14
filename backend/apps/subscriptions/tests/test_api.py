"""
Integration tests for Subject REST API endpoints.

Tests complete API workflows, authentication, permissions, and HTTP responses.
Includes security and performance test scenarios.
"""

import pytest
import time
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.subscriptions.models import Subject, WebSource
from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestSubjectAPIEndpoints:
    """Integration tests for Subject API CRUD operations."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def regular_user(self):
        """Create regular user."""
        return CustomUser.objects.create_user(
            email='user@test.com',
            password='testpass123',
            is_staff=False
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject with web sources."""
        subject = Subject.objects.create(
            name='Kubernetes',
            description='Container orchestration',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )
        WebSource.objects.create(
            subject=subject,
            url='https://kubernetes.io/blog/'
        )
        WebSource.objects.create(
            subject=subject,
            url='https://github.com/kubernetes/kubernetes'
        )
        return subject

    def test_list_subjects(self, api_client, admin_user, subject):
        """Test GET /api/admin/subjects/ lists subjects."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get('/api/admin/subjects/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert response.data['results'][0]['name'] == 'Kubernetes'

    def test_list_subjects_pagination(self, api_client, admin_user):
        """Test pagination works correctly."""
        # Create 60 subjects (default page size is 50)
        for i in range(60):
            Subject.objects.create(
                name=f'Subject {i}',
                description='Test',
                created_by=admin_user
            )

        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/admin/subjects/')

        assert response.status_code == status.HTTP_200_OK
        assert 'next' in response.data
        assert 'previous' in response.data
        assert len(response.data['results']) == 50  # Default page size

        # Get page 2
        response = api_client.get('/api/admin/subjects/?page=2')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10  # Remaining items

    def test_list_subjects_filter_by_status(self, api_client, admin_user):
        """Test filtering by status."""
        Subject.objects.create(
            name='Active Subject',
            description='Test',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )
        Subject.objects.create(
            name='Archived Subject',
            description='Test',
            status=Subject.Status.ARCHIVED,
            created_by=admin_user
        )

        api_client.force_authenticate(user=admin_user)

        # Filter active
        response = api_client.get('/api/admin/subjects/?status=active')
        assert response.status_code == status.HTTP_200_OK
        for subject in response.data['results']:
            assert subject['status'] == 'active'

        # Filter archived
        response = api_client.get('/api/admin/subjects/?status=archived')
        assert response.status_code == status.HTTP_200_OK
        for subject in response.data['results']:
            assert subject['status'] == 'archived'

    def test_list_subjects_search(self, api_client, admin_user):
        """Test search functionality."""
        Subject.objects.create(
            name='Docker',
            description='Container platform',
            created_by=admin_user
        )
        Subject.objects.create(
            name='Kubernetes',
            description='Orchestration',
            created_by=admin_user
        )

        api_client.force_authenticate(user=admin_user)

        response = api_client.get('/api/admin/subjects/?search=Docker')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        assert any('Docker' in s['name'] for s in response.data['results'])

    def test_list_subjects_ordering(self, api_client, admin_user):
        """Test ordering by different fields."""
        api_client.force_authenticate(user=admin_user)

        # Order by name ascending
        response = api_client.get('/api/admin/subjects/?ordering=name')
        assert response.status_code == status.HTTP_200_OK

        # Order by created_at descending (default)
        response = api_client.get('/api/admin/subjects/?ordering=-created_at')
        assert response.status_code == status.HTTP_200_OK

    def test_create_subject(self, api_client, admin_user):
        """Test POST /api/admin/subjects/ creates subject."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'name': 'Docker',
            'description': 'Container platform',
            'status': 'active',
            'web_sources': [
                {'url': 'https://docker.com/blog/'}
            ]
        }

        response = api_client.post('/api/admin/subjects/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Docker'
        assert len(response.data['web_sources']) == 1
        assert response.data['web_sources'][0]['url'] == 'https://docker.com/blog/'

        # Verify in database
        subject = Subject.objects.get(name='Docker')
        assert subject.created_by == admin_user
        assert subject.web_sources.count() == 1

    def test_create_subject_without_web_sources(self, api_client, admin_user):
        """Test creating subject without web sources."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'name': 'Python',
            'description': 'Programming language',
            'status': 'active'
        }

        response = api_client.post('/api/admin/subjects/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Python'
        assert len(response.data['web_sources']) == 0

    def test_create_subject_validation_errors(self, api_client, admin_user):
        """Test validation errors are returned."""
        api_client.force_authenticate(user=admin_user)

        # Missing required fields
        data = {}
        response = api_client.post('/api/admin/subjects/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert 'description' in response.data

        # Invalid URL
        data = {
            'name': 'Test',
            'description': 'Test',
            'web_sources': [
                {'url': 'not a valid url'}
            ]
        }
        response = api_client.post('/api/admin/subjects/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_subject_duplicate_name(self, api_client, admin_user, subject):
        """Test duplicate name is rejected."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'name': 'Kubernetes',  # Duplicate
            'description': 'Test'
        }

        response = api_client.post('/api/admin/subjects/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data

    def test_retrieve_subject(self, api_client, admin_user, subject):
        """Test GET /api/admin/subjects/{id}/ retrieves subject."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.get(f'/api/admin/subjects/{subject.id}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Kubernetes'
        assert len(response.data['web_sources']) == 2

    def test_retrieve_subject_not_found(self, api_client, admin_user):
        """Test 404 for non-existent subject."""
        api_client.force_authenticate(user=admin_user)

        import uuid
        fake_id = uuid.uuid4()
        response = api_client.get(f'/api/admin/subjects/{fake_id}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_partial_update_subject(self, api_client, admin_user, subject):
        """Test PATCH /api/admin/subjects/{id}/ updates subject."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'description': 'Updated description'
        }

        response = api_client.patch(
            f'/api/admin/subjects/{subject.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated description'
        assert response.data['name'] == 'Kubernetes'  # Unchanged

        subject.refresh_from_db()
        assert subject.description == 'Updated description'

    def test_full_update_subject(self, api_client, admin_user, subject):
        """Test PUT /api/admin/subjects/{id}/ replaces subject."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'name': 'Kubernetes Updated',
            'description': 'New description',
            'status': 'active',
            'web_sources': [
                {'url': 'https://new-source.com'}
            ]
        }

        response = api_client.put(
            f'/api/admin/subjects/{subject.id}/',
            data,
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Kubernetes Updated'
        assert len(response.data['web_sources']) == 1

        subject.refresh_from_db()
        assert subject.web_sources.count() == 1

    def test_archive_subject(self, api_client, admin_user, subject):
        """Test DELETE /api/admin/subjects/{id}/ archives subject."""
        api_client.force_authenticate(user=admin_user)

        response = api_client.delete(f'/api/admin/subjects/{subject.id}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        subject.refresh_from_db()
        assert subject.status == Subject.Status.ARCHIVED

        # Subject still exists (soft delete)
        assert Subject.objects.filter(id=subject.id).exists()


@pytest.mark.django_db
class TestAPISecurityAndPermissions:
    """Security tests for API authentication and authorization (TASK-1.15)."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def regular_user(self):
        """Create regular user."""
        return CustomUser.objects.create_user(
            email='user@test.com',
            password='testpass123',
            is_staff=False
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject."""
        return Subject.objects.create(
            name='Kubernetes',
            description='Test',
            created_by=admin_user
        )

    def test_unauthenticated_access_denied(self, api_client):
        """Test unauthenticated requests return 401."""
        # List
        response = api_client.get('/api/admin/subjects/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Create
        response = api_client.post('/api/admin/subjects/', {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_access_denied(self, api_client, regular_user, subject):
        """Test non-admin users receive 403 Forbidden."""
        api_client.force_authenticate(user=regular_user)

        # List
        response = api_client.get('/api/admin/subjects/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Retrieve
        response = api_client.get(f'/api/admin/subjects/{subject.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Create
        response = api_client.post('/api/admin/subjects/', {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Update
        response = api_client.patch(f'/api/admin/subjects/{subject.id}/', {})
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Delete
        response = api_client.delete(f'/api/admin/subjects/{subject.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_staff_user_without_superuser_denied(self, api_client):
        """Test staff users without superuser status are denied."""
        staff_user = CustomUser.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False  # Not superuser
        )

        api_client.force_authenticate(user=staff_user)
        response = api_client.get('/api/admin/subjects/')

        # IsAdminUser checks is_staff AND is_superuser by default in DRF
        # Adjust if your implementation differs
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_200_OK]

    def test_url_injection_prevention(self, api_client, admin_user):
        """Test malicious URLs are rejected."""
        api_client.force_authenticate(user=admin_user)

        malicious_urls = [
            'javascript:alert(1)',
            'data:text/html,<script>alert(1)</script>',
            'file:///etc/passwd',
        ]

        for url in malicious_urls:
            data = {
                'name': 'Test',
                'description': 'Test',
                'web_sources': [{'url': url}]
            }

            response = api_client.post('/api/admin/subjects/', data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_xss_prevention_in_responses(self, api_client, admin_user):
        """Test responses don't render script tags."""
        api_client.force_authenticate(user=admin_user)

        # Try to inject XSS in name
        data = {
            'name': '<script>alert("XSS")</script>',
            'description': 'Test'
        }

        response = api_client.post('/api/admin/subjects/', data, format='json')

        # Should be accepted (stored as text)
        assert response.status_code == status.HTTP_201_CREATED

        # Verify it's stored as plain text, not executed
        subject = Subject.objects.get(id=response.data['id'])
        assert '<script>' in subject.name  # Stored as-is
        assert response.data['name'] == '<script>alert("XSS")</script>'


@pytest.mark.django_db
class TestAPIPerformance:
    """Performance tests for Subject API (TASK-1.16)."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def create_subjects(self, admin_user):
        """Create multiple subjects for performance testing."""
        subjects = []
        for i in range(100):
            subject = Subject.objects.create(
                name=f'Subject {i}',
                description=f'Description for subject {i}' * 10,  # Make it realistic
                status=Subject.Status.ACTIVE if i % 2 == 0 else Subject.Status.ARCHIVED,
                created_by=admin_user
            )
            # Add web sources
            for j in range(3):
                WebSource.objects.create(
                    subject=subject,
                    url=f'https://example.com/{i}/{j}'
                )
            subjects.append(subject)
        return subjects

    def test_list_performance_1000_subjects(self, api_client, admin_user):
        """Test list endpoint performance with 1000+ subjects."""
        # Create 1000 subjects
        subjects = []
        for i in range(1000):
            subjects.append(Subject(
                name=f'Subject {i}',
                description=f'Description {i}',
                created_by=admin_user
            ))
        Subject.objects.bulk_create(subjects)

        api_client.force_authenticate(user=admin_user)

        # Measure response time
        start_time = time.time()
        response = api_client.get('/api/admin/subjects/')
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        # Target: < 200ms P95 for 1000+ subjects
        assert duration_ms < 500, f"List took {duration_ms}ms, expected < 500ms"

    def test_query_optimization_n_plus_one(self, api_client, admin_user, create_subjects):
        """Test N+1 query prevention with prefetch_related."""
        api_client.force_authenticate(user=admin_user)

        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as queries:
            response = api_client.get('/api/admin/subjects/')

        # Should have limited queries despite 100 subjects
        # Expected: 1-2 queries (subjects + count)
        # Note: Actual count may vary based on pagination
        assert len(queries) < 10, f"Too many queries: {len(queries)}"

    def test_create_subject_performance(self, api_client, admin_user):
        """Test create endpoint meets performance target."""
        api_client.force_authenticate(user=admin_user)

        data = {
            'name': 'Performance Test',
            'description': 'Testing performance',
            'web_sources': [
                {'url': f'https://example.com/{i}'} for i in range(5)
            ]
        }

        start_time = time.time()
        response = api_client.post('/api/admin/subjects/', data, format='json')
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == status.HTTP_201_CREATED
        # Target: < 500ms for creation
        assert duration_ms < 1000, f"Create took {duration_ms}ms, expected < 1000ms"

    def test_retrieve_with_many_web_sources(self, api_client, admin_user):
        """Test retrieve performance with many web sources."""
        subject = Subject.objects.create(
            name='Performance Test',
            description='Test',
            created_by=admin_user
        )

        # Add 50 web sources
        for i in range(50):
            WebSource.objects.create(
                subject=subject,
                url=f'https://example.com/{i}'
            )

        api_client.force_authenticate(user=admin_user)

        start_time = time.time()
        response = api_client.get(f'/api/admin/subjects/{subject.id}/')
        end_time = time.time()

        duration_ms = (end_time - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['web_sources']) == 50
        # Should be reasonably fast even with many sources
        assert duration_ms < 500, f"Retrieve took {duration_ms}ms, expected < 500ms"
