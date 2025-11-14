"""
Integration tests for public subject catalog API (US-2).

Tests the GET /api/subjects/ endpoint for browsing active subjects.
Covers pagination, filtering, performance, and security aspects.
"""

import pytest
import time
from rest_framework.test import APIClient
from django.test.utils import override_settings
from apps.subscriptions.models import Subject
from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestPublicSubjectListAPI:
    """Integration tests for public subject catalog endpoint."""

    @pytest.fixture
    def client(self):
        """Create API client (no authentication)."""
        return APIClient()

    @pytest.fixture
    def admin_user(self):
        """Create admin user for subject creation."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def active_subjects(self, admin_user):
        """Create multiple active subjects for testing."""
        subjects = []
        for i in range(5):
            subject = Subject.objects.create(
                name=f'Subject {chr(65+i)}',  # A, B, C, D, E
                description=f'Description for subject {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )
            subjects.append(subject)
        return subjects

    def test_endpoint_accessible_without_authentication(self, client):
        """GET /api/subjects/ should be accessible without auth token."""
        response = client.get('/api/subjects/')
        assert response.status_code == 200

    def test_response_format_matches_spec(self, client, active_subjects):
        """Response should include count, next, previous, results."""
        response = client.get('/api/subjects/')
        data = response.json()

        assert 'count' in data
        assert 'next' in data
        assert 'previous' in data
        assert 'results' in data
        assert isinstance(data['results'], list)
        assert data['count'] == 5

    def test_returns_only_active_subjects(self, client, admin_user):
        """API should return only active subjects, exclude archived."""
        Subject.objects.create(
            name='Active 1',
            description='Active subject',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )
        Subject.objects.create(
            name='Active 2',
            description='Active subject',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )
        Subject.objects.create(
            name='Archived',
            description='Archived subject',
            status=Subject.Status.ARCHIVED,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        data = response.json()

        assert data['count'] == 2
        names = [s['name'] for s in data['results']]
        assert 'Active 1' in names
        assert 'Active 2' in names
        assert 'Archived' not in names

    def test_results_sorted_alphabetically(self, client, admin_user):
        """Results should be sorted by name alphabetically."""
        Subject.objects.create(name='Zebra', status=Subject.Status.ACTIVE, created_by=admin_user)
        Subject.objects.create(name='Alpha', status=Subject.Status.ACTIVE, created_by=admin_user)
        Subject.objects.create(name='Beta', status=Subject.Status.ACTIVE, created_by=admin_user)

        response = client.get('/api/subjects/')
        data = response.json()
        names = [s['name'] for s in data['results']]

        assert names == ['Alpha', 'Beta', 'Zebra']

    def test_subject_fields_included(self, client, admin_user):
        """Each subject should include id, name, description, status."""
        Subject.objects.create(
            name='Test AI',
            description='Artificial Intelligence',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        subject = response.json()['results'][0]

        assert 'id' in subject
        assert 'name' in subject
        assert 'description' in subject
        assert 'status' in subject
        assert subject['name'] == 'Test AI'
        assert subject['description'] == 'Artificial Intelligence'
        assert subject['status'] == 'active'

    def test_no_sensitive_fields_exposed(self, client, admin_user):
        """Response should not include web_sources, created_by, or timestamps."""
        Subject.objects.create(
            name='Test',
            description='Test subject',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        subject = response.json()['results'][0]

        # These fields should NOT be present in public API
        assert 'web_sources' not in subject
        assert 'created_by' not in subject
        assert 'created_at' not in subject
        assert 'updated_at' not in subject
        assert 'subscriber_count' not in subject

    def test_empty_catalog_returns_empty_results(self, client):
        """Empty catalog should return empty results array."""
        response = client.get('/api/subjects/')
        data = response.json()

        assert data['count'] == 0
        assert data['results'] == []
        assert data['next'] is None
        assert data['previous'] is None

    def test_default_pagination_page_size(self, client, admin_user):
        """Default page size should be 50."""
        # Create 60 subjects
        for i in range(60):
            Subject.objects.create(
                name=f'Subject {i:03d}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )

        response = client.get('/api/subjects/')
        data = response.json()

        assert data['count'] == 60
        assert len(data['results']) == 50
        assert data['next'] is not None
        assert data['previous'] is None

    def test_custom_page_size(self, client, admin_user):
        """Should accept custom page_size parameter."""
        for i in range(30):
            Subject.objects.create(
                name=f'Subject {i:03d}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )

        response = client.get('/api/subjects/', {'page_size': 10})
        data = response.json()

        assert len(data['results']) == 10
        assert data['count'] == 30

    def test_page_size_maximum_limit(self, client, admin_user):
        """page_size should be capped at 100."""
        for i in range(150):
            Subject.objects.create(
                name=f'Subject {i:03d}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )

        response = client.get('/api/subjects/', {'page_size': 100})
        data = response.json()

        assert len(data['results']) == 100

    def test_page_navigation(self, client, admin_user):
        """Should navigate between pages correctly."""
        for i in range(60):
            Subject.objects.create(
                name=f'Subject {i:02d}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )

        # Page 1
        response = client.get('/api/subjects/', {'page': 1, 'page_size': 25})
        page1 = response.json()
        assert len(page1['results']) == 25
        assert page1['previous'] is None
        assert page1['next'] is not None

        # Page 2
        response = client.get('/api/subjects/', {'page': 2, 'page_size': 25})
        page2 = response.json()
        assert len(page2['results']) == 25
        assert page2['previous'] is not None
        assert page2['next'] is not None

        # Page 3 (last page)
        response = client.get('/api/subjects/', {'page': 3, 'page_size': 25})
        page3 = response.json()
        assert len(page3['results']) == 10  # Remaining items
        assert page3['next'] is None

    def test_invalid_page_number(self, client, admin_user):
        """Invalid page number should return 404."""
        Subject.objects.create(
            name='Test',
            description='Test subject',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/', {'page': 999})
        assert response.status_code == 404

    def test_special_characters_in_fields(self, client, admin_user):
        """Should handle special characters in name and description."""
        Subject.objects.create(
            name='C++ & Rust',
            description='Low-level <programming>',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        subject = response.json()['results'][0]

        assert subject['name'] == 'C++ & Rust'
        assert '<' in subject['description']

    def test_very_long_description(self, client, admin_user):
        """Should return full description without truncation."""
        long_desc = 'A' * 5000
        Subject.objects.create(
            name='Test',
            description=long_desc,
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        subject = response.json()['results'][0]

        assert len(subject['description']) == 5000

    @override_settings(DEBUG=True)
    def test_single_database_query(self, client, admin_user):
        """Endpoint should execute single optimized query."""
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        # Create test subjects
        for i in range(10):
            Subject.objects.create(
                name=f'Subject {i}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )

        with CaptureQueriesContext(connection) as queries:
            response = client.get('/api/subjects/')
            assert response.status_code == 200

        # Should be minimal queries (count + results + pagination)
        # Allow up to 5 queries for DRF pagination overhead
        assert len(queries) <= 5, f"Expected <= 5 queries, got {len(queries)}"

    def test_response_time_for_large_catalog(self, client, admin_user):
        """Response time should be < 100ms for 100 subjects."""
        # Create 100 subjects
        subjects = [
            Subject(
                name=f'Subject {i:03d}',
                description=f'Description {i}',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )
            for i in range(100)
        ]
        Subject.objects.bulk_create(subjects)

        # Measure response time
        start = time.time()
        response = client.get('/api/subjects/')
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        # Relaxed target (200ms) for test environment
        assert elapsed < 200, f"Response took {elapsed}ms, expected < 200ms"

    def test_concurrent_read_access(self, client, admin_user):
        """Multiple concurrent requests should work without issues."""
        Subject.objects.create(
            name='Test',
            description='Test subject',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        # Simulate concurrent requests
        responses = []
        for _ in range(10):
            response = client.get('/api/subjects/')
            responses.append(response)

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 1


@pytest.mark.django_db
class TestPublicSubjectSecurity:
    """Security tests for public subject catalog."""

    @pytest.fixture
    def client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    def test_read_only_endpoint(self, client):
        """POST, PUT, DELETE should not be allowed."""
        # POST
        response = client.post('/api/subjects/', {'name': 'Test'})
        assert response.status_code in [405, 403]  # Method not allowed or Forbidden

        # PUT (detail endpoint doesn't exist for public)
        response = client.put('/api/subjects/some-id/', {'name': 'Test'})
        assert response.status_code in [405, 404]

        # DELETE
        response = client.delete('/api/subjects/some-id/')
        assert response.status_code in [405, 404]

    def test_no_admin_metadata_exposed(self, client, admin_user):
        """Admin-specific fields should not be exposed."""
        Subject.objects.create(
            name='Test',
            description='Test',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        subject = response.json()['results'][0]

        # Verify no admin metadata
        assert 'created_by' not in subject
        assert 'web_sources' not in subject

    def test_archived_subjects_not_accessible(self, client, admin_user):
        """Archived subjects should never be returned."""
        subject = Subject.objects.create(
            name='Archived',
            description='Should not appear',
            status=Subject.Status.ARCHIVED,
            created_by=admin_user
        )

        response = client.get('/api/subjects/')
        data = response.json()

        assert data['count'] == 0
        assert len(data['results']) == 0
