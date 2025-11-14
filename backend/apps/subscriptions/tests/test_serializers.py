"""
Unit tests for Subject and WebSource serializers.

Tests serialization, deserialization, validation, and nested relationships.
Coverage target: >80% for serializer code.
"""

import pytest
from rest_framework.exceptions import ValidationError
from apps.subscriptions.models import Subject, WebSource
from apps.subscriptions.serializers import (
    SubjectSerializer,
    SubjectListSerializer,
    WebSourceSerializer,
)
from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestWebSourceSerializer:
    """Unit tests for WebSourceSerializer."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject for testing."""
        return Subject.objects.create(
            name='Kubernetes',
            description='Container orchestration',
            created_by=admin_user
        )

    def test_web_source_serialization(self, subject):
        """Test serializing WebSource instance."""
        ws = WebSource.objects.create(
            subject=subject,
            url='https://kubernetes.io/blog/'
        )

        serializer = WebSourceSerializer(ws)
        data = serializer.data

        assert 'id' in data
        assert data['url'] == 'https://kubernetes.io/blog/'
        assert 'created_at' in data

    def test_web_source_deserialization(self):
        """Test deserializing WebSource data."""
        data = {
            'url': 'https://example.com/feed'
        }

        serializer = WebSourceSerializer(data=data)
        assert serializer.is_valid()

        assert serializer.validated_data['url'] == 'https://example.com/feed'

    def test_web_source_url_validation_valid(self):
        """Test URL validation accepts valid URLs."""
        valid_urls = [
            'https://example.com',
            'http://example.com/path',
            'https://example.com:8080/path?query=value',
        ]

        for url in valid_urls:
            serializer = WebSourceSerializer(data={'url': url})
            assert serializer.is_valid(), f"URL {url} should be valid"

    def test_web_source_url_validation_invalid(self):
        """Test URL validation rejects invalid URLs."""
        invalid_urls = [
            'not a url',
            'javascript:alert(1)',
            '',
        ]

        for url in invalid_urls:
            serializer = WebSourceSerializer(data={'url': url})
            assert not serializer.is_valid(), f"URL {url} should be invalid"

    def test_web_source_read_only_fields(self):
        """Test id and created_at are read-only."""
        serializer = WebSourceSerializer()
        meta = serializer.Meta

        assert 'id' in meta.read_only_fields
        assert 'created_at' in meta.read_only_fields


@pytest.mark.django_db
class TestSubjectSerializer:
    """Unit tests for SubjectSerializer."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject with web sources."""
        subject = Subject.objects.create(
            name='Kubernetes',
            description='Container orchestration platform',
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

    def test_subject_serialization(self, subject):
        """Test serializing Subject instance with nested web sources."""
        serializer = SubjectSerializer(subject)
        data = serializer.data

        assert data['name'] == 'Kubernetes'
        assert data['description'] == 'Container orchestration platform'
        assert data['status'] == 'active'
        assert 'web_sources' in data
        assert len(data['web_sources']) == 2
        assert data['subscriber_count'] == 0
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_subject_deserialization(self):
        """Test deserializing Subject data."""
        data = {
            'name': 'Docker',
            'description': 'Container platform',
            'status': 'active',
            'web_sources': [
                {'url': 'https://docker.com/blog/'}
            ]
        }

        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        validated = serializer.validated_data
        assert validated['name'] == 'Docker'
        assert validated['description'] == 'Container platform'
        assert validated['status'] == 'active'
        assert len(validated['web_sources']) == 1

    def test_subject_create_with_web_sources(self, admin_user):
        """Test creating subject with nested web sources."""
        data = {
            'name': 'Docker',
            'description': 'Container platform',
            'status': 'active',
            'web_sources': [
                {'url': 'https://docker.com/blog/'},
                {'url': 'https://github.com/docker/docker'}
            ]
        }

        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

        subject = serializer.save(created_by=admin_user)

        assert subject.name == 'Docker'
        assert subject.web_sources.count() == 2
        assert subject.created_by == admin_user

    def test_subject_create_without_web_sources(self, admin_user):
        """Test creating subject without web sources is allowed."""
        data = {
            'name': 'Python',
            'description': 'Programming language',
            'status': 'active'
        }

        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid()

        subject = serializer.save(created_by=admin_user)

        assert subject.name == 'Python'
        assert subject.web_sources.count() == 0

    def test_subject_update_with_web_sources(self, subject):
        """Test updating subject replaces web sources."""
        data = {
            'name': 'Kubernetes Updated',
            'description': 'Updated description',
            'web_sources': [
                {'url': 'https://new-source.com'}
            ]
        }

        serializer = SubjectSerializer(subject, data=data, partial=True)
        assert serializer.is_valid()

        updated_subject = serializer.save()

        assert updated_subject.name == 'Kubernetes Updated'
        assert updated_subject.web_sources.count() == 1
        assert updated_subject.web_sources.first().url == 'https://new-source.com'

    def test_subject_update_without_web_sources(self, subject):
        """Test updating subject without web_sources preserves existing."""
        original_count = subject.web_sources.count()

        data = {
            'description': 'Updated description only'
        }

        serializer = SubjectSerializer(subject, data=data, partial=True)
        assert serializer.is_valid()

        updated_subject = serializer.save()

        # Web sources should remain unchanged
        assert updated_subject.web_sources.count() == original_count

    def test_subject_name_uniqueness_validation(self, admin_user, subject):
        """Test name uniqueness validation (case-insensitive)."""
        # Exact duplicate
        data = {
            'name': 'Kubernetes',
            'description': 'Test'
        }

        serializer = SubjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Case-insensitive duplicate
        data = {
            'name': 'kubernetes',  # lowercase
            'description': 'Test'
        }

        serializer = SubjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

    def test_subject_name_uniqueness_update(self, subject):
        """Test name uniqueness doesn't apply to same instance."""
        data = {
            'name': 'Kubernetes',  # Same name, should be valid for update
            'description': 'Updated'
        }

        serializer = SubjectSerializer(subject, data=data, partial=True)
        assert serializer.is_valid()

    def test_subject_status_validation(self):
        """Test status enum validation."""
        # Valid status
        data = {
            'name': 'Test',
            'description': 'Test',
            'status': 'active'
        }
        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid()

        # Invalid status
        data['status'] = 'invalid_status'
        serializer = SubjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'status' in serializer.errors

    def test_subject_subscriber_count_method(self, subject):
        """Test get_subscriber_count returns 0 (placeholder)."""
        serializer = SubjectSerializer(subject)
        assert serializer.data['subscriber_count'] == 0

    def test_subject_read_only_fields(self):
        """Test read-only fields cannot be set."""
        serializer = SubjectSerializer()
        meta = serializer.Meta

        read_only = meta.read_only_fields
        assert 'id' in read_only
        assert 'created_at' in read_only
        assert 'updated_at' in read_only
        assert 'subscriber_count' in read_only


@pytest.mark.django_db
class TestSubjectListSerializer:
    """Unit tests for SubjectListSerializer (lightweight)."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject with web sources."""
        subject = Subject.objects.create(
            name='Kubernetes',
            description='Container orchestration',
            created_by=admin_user
        )
        WebSource.objects.create(
            subject=subject,
            url='https://kubernetes.io/blog/'
        )
        return subject

    def test_subject_list_serialization(self, subject):
        """Test SubjectListSerializer excludes web_sources."""
        serializer = SubjectListSerializer(subject)
        data = serializer.data

        assert data['name'] == 'Kubernetes'
        assert data['description'] == 'Container orchestration'
        assert 'web_sources' not in data  # Should not be included
        assert 'subscriber_count' in data

    def test_subject_list_subscriber_count_annotation(self, subject):
        """Test get_subscriber_count uses annotation if available."""
        # Simulate annotation
        subject._subscriber_count = 5

        serializer = SubjectListSerializer(subject)
        assert serializer.data['subscriber_count'] == 5

    def test_subject_list_subscriber_count_fallback(self, subject):
        """Test get_subscriber_count falls back to 0 without annotation."""
        serializer = SubjectListSerializer(subject)
        assert serializer.data['subscriber_count'] == 0


@pytest.mark.django_db
class TestSerializerValidation:
    """Test edge cases and validation scenarios."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    def test_subject_empty_web_sources_list(self, admin_user):
        """Test empty web_sources list is valid."""
        data = {
            'name': 'Test',
            'description': 'Test',
            'web_sources': []
        }

        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid()

        subject = serializer.save(created_by=admin_user)
        assert subject.web_sources.count() == 0

    def test_subject_missing_required_fields(self):
        """Test validation fails without required fields."""
        data = {}

        serializer = SubjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors
        assert 'description' in serializer.errors

    def test_web_source_invalid_url_in_nested(self):
        """Test invalid URL in nested web_sources is caught."""
        data = {
            'name': 'Test',
            'description': 'Test',
            'web_sources': [
                {'url': 'not a valid url'}
            ]
        }

        serializer = SubjectSerializer(data=data)
        assert not serializer.is_valid()
        assert 'web_sources' in serializer.errors

    def test_subject_very_long_description(self, admin_user):
        """Test very long descriptions are accepted (TextField)."""
        long_description = 'A' * 10000

        data = {
            'name': 'Test',
            'description': long_description,
        }

        serializer = SubjectSerializer(data=data)
        assert serializer.is_valid()

        subject = serializer.save(created_by=admin_user)
        assert len(subject.description) == 10000

    def test_subject_special_characters_in_name(self, admin_user):
        """Test special characters in name are accepted."""
        special_names = [
            'C++',
            'C#',
            'Node.js',
            'ASP.NET Core',
            'Vue.js 3.0'
        ]

        for name in special_names:
            data = {
                'name': name,
                'description': 'Test'
            }

            serializer = SubjectSerializer(data=data)
            assert serializer.is_valid(), f"Name '{name}' should be valid"

            subject = serializer.save(created_by=admin_user)
            assert subject.name == name

            # Clean up for uniqueness constraint
            subject.delete()
