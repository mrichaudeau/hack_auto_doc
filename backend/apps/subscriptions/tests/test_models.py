"""
Unit tests for Subject and WebSource models.

Tests model validation, constraints, relationships, and business logic.
Coverage target: >80% for model code.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from apps.subscriptions.models import Subject, WebSource
from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestSubjectModel:
    """Unit tests for Subject model."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for testing."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )

    @pytest.fixture
    def subject(self, admin_user):
        """Create sample subject for testing."""
        return Subject.objects.create(
            name='Kubernetes',
            description='Container orchestration platform',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

    def test_subject_creation(self, admin_user):
        """Test basic subject creation."""
        subject = Subject.objects.create(
            name='Docker',
            description='Container platform',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )

        assert subject.id is not None
        assert subject.name == 'Docker'
        assert subject.description == 'Container platform'
        assert subject.status == Subject.Status.ACTIVE
        assert subject.created_by == admin_user
        assert subject.created_at is not None
        assert subject.updated_at is not None

    def test_subject_default_status(self, admin_user):
        """Test subject defaults to ACTIVE status."""
        subject = Subject.objects.create(
            name='Python',
            description='Programming language',
            created_by=admin_user
        )

        assert subject.status == Subject.Status.ACTIVE

    def test_subject_str_representation(self, subject):
        """Test __str__ method returns name."""
        assert str(subject) == 'Kubernetes'

    def test_subject_name_uniqueness(self, admin_user, subject):
        """Test subject name must be unique."""
        with pytest.raises(IntegrityError):
            Subject.objects.create(
                name='Kubernetes',  # Duplicate name
                description='Different description',
                created_by=admin_user
            )

    def test_subject_name_max_length(self, admin_user):
        """Test subject name has 200 character limit."""
        long_name = 'A' * 201

        with pytest.raises(ValidationError):
            subject = Subject(
                name=long_name,
                description='Test',
                created_by=admin_user
            )
            subject.full_clean()

    def test_subject_status_choices(self, admin_user):
        """Test subject status accepts only valid choices."""
        # Valid statuses should work
        active_subject = Subject.objects.create(
            name='Active Subject',
            description='Test',
            status=Subject.Status.ACTIVE,
            created_by=admin_user
        )
        assert active_subject.status == Subject.Status.ACTIVE

        archived_subject = Subject.objects.create(
            name='Archived Subject',
            description='Test',
            status=Subject.Status.ARCHIVED,
            created_by=admin_user
        )
        assert archived_subject.status == Subject.Status.ARCHIVED

    def test_subject_archival(self, subject):
        """Test archiving a subject."""
        subject.status = Subject.Status.ARCHIVED
        subject.save()

        subject.refresh_from_db()
        assert subject.status == Subject.Status.ARCHIVED

    def test_subject_created_by_null_on_user_delete(self, admin_user):
        """Test created_by is set to NULL when user is deleted."""
        subject = Subject.objects.create(
            name='Test Subject',
            description='Test',
            created_by=admin_user
        )

        admin_user.delete()
        subject.refresh_from_db()

        assert subject.created_by is None

    def test_subject_ordering(self, admin_user):
        """Test subjects are ordered by created_at descending."""
        subject1 = Subject.objects.create(
            name='First',
            description='Test',
            created_by=admin_user
        )
        subject2 = Subject.objects.create(
            name='Second',
            description='Test',
            created_by=admin_user
        )

        subjects = list(Subject.objects.all())
        assert subjects[0] == subject2  # Most recent first
        assert subjects[1] == subject1

    def test_subject_history_tracking(self, subject):
        """Test django-simple-history creates historical records."""
        # Check history exists
        assert subject.history.count() == 1

        # Update subject
        subject.description = 'Updated description'
        subject.save()

        # Check history increased
        assert subject.history.count() == 2

        # Verify historical data
        latest_history = subject.history.first()
        assert latest_history.description == 'Updated description'


@pytest.mark.django_db
class TestWebSourceModel:
    """Unit tests for WebSource model."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for testing."""
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

    @pytest.fixture
    def web_source(self, subject):
        """Create web source for testing."""
        return WebSource.objects.create(
            subject=subject,
            url='https://kubernetes.io/blog/'
        )

    def test_web_source_creation(self, subject):
        """Test basic web source creation."""
        ws = WebSource.objects.create(
            subject=subject,
            url='https://example.com/feed'
        )

        assert ws.id is not None
        assert ws.subject == subject
        assert ws.url == 'https://example.com/feed'
        assert ws.created_at is not None

    def test_web_source_str_representation(self, web_source):
        """Test __str__ method returns URL."""
        assert str(web_source) == 'https://kubernetes.io/blog/'

    def test_web_source_subject_relationship(self, subject, web_source):
        """Test web source foreign key to subject."""
        assert web_source.subject == subject
        assert subject.web_sources.count() == 1
        assert subject.web_sources.first() == web_source

    def test_web_source_cascade_delete(self, subject):
        """Test web sources are deleted when subject is deleted."""
        ws1 = WebSource.objects.create(
            subject=subject,
            url='https://example.com/1'
        )
        ws2 = WebSource.objects.create(
            subject=subject,
            url='https://example.com/2'
        )

        assert WebSource.objects.count() == 2

        subject.delete()

        # Web sources should be cascade deleted
        assert WebSource.objects.count() == 0

    def test_web_source_url_validation(self, subject):
        """Test URL field validates RFC 3986 compliance."""
        # Valid URLs should work
        valid_urls = [
            'https://example.com',
            'http://example.com/path',
            'https://example.com:8080/path?query=value',
            'https://sub.example.com/path#fragment',
        ]

        for url in valid_urls:
            ws = WebSource(subject=subject, url=url)
            ws.full_clean()  # Should not raise

    def test_web_source_invalid_url(self, subject):
        """Test invalid URLs are rejected."""
        invalid_urls = [
            'not a url',
            'javascript:alert(1)',
            '',  # Empty string
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                ws = WebSource(subject=subject, url=url)
                ws.full_clean()

    def test_web_source_url_max_length(self, subject):
        """Test URL field accepts up to 2048 characters."""
        # 2048 characters should work
        long_url = 'https://example.com/' + 'a' * 2020
        ws = WebSource(subject=subject, url=long_url)
        ws.full_clean()  # Should not raise

    def test_web_source_ordering(self, subject):
        """Test web sources are ordered by created_at ascending."""
        ws1 = WebSource.objects.create(
            subject=subject,
            url='https://example.com/1'
        )
        ws2 = WebSource.objects.create(
            subject=subject,
            url='https://example.com/2'
        )

        sources = list(subject.web_sources.all())
        assert sources[0] == ws1  # Oldest first
        assert sources[1] == ws2

    def test_multiple_web_sources_per_subject(self, subject):
        """Test subject can have multiple web sources."""
        urls = [
            'https://example.com/1',
            'https://example.com/2',
            'https://example.com/3',
        ]

        for url in urls:
            WebSource.objects.create(subject=subject, url=url)

        assert subject.web_sources.count() == 3

    def test_same_url_different_subjects(self, admin_user):
        """Test same URL can be used for different subjects."""
        subject1 = Subject.objects.create(
            name='Subject 1',
            description='Test',
            created_by=admin_user
        )
        subject2 = Subject.objects.create(
            name='Subject 2',
            description='Test',
            created_by=admin_user
        )

        url = 'https://example.com/feed'

        ws1 = WebSource.objects.create(subject=subject1, url=url)
        ws2 = WebSource.objects.create(subject=subject2, url=url)

        assert ws1.url == ws2.url
        assert ws1.subject != ws2.subject


@pytest.mark.django_db
class TestSubjectQueryOptimization:
    """Test query optimization for Subject model."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    def test_web_sources_prefetch(self, admin_user):
        """Test prefetch_related optimization for web_sources."""
        # Create subjects with web sources
        for i in range(3):
            subject = Subject.objects.create(
                name=f'Subject {i}',
                description='Test',
                created_by=admin_user
            )
            for j in range(2):
                WebSource.objects.create(
                    subject=subject,
                    url=f'https://example.com/{i}/{j}'
                )

        # Query with prefetch_related
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as queries:
            subjects = Subject.objects.prefetch_related('web_sources').all()
            for subject in subjects:
                list(subject.web_sources.all())

        # Should be 2 queries: 1 for subjects, 1 for web_sources
        assert len(queries) == 2
