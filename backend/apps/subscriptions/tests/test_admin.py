"""
Integration tests for Subject Django Admin interface.

Tests admin functionality, inline editing, bulk actions, and permissions.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from apps.subscriptions.models import Subject, WebSource
from apps.subscriptions.admin import SubjectAdmin, WebSourceAdmin
from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestSubjectAdmin:
    """Integration tests for SubjectAdmin."""

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
    def admin_site(self):
        """Create admin site."""
        return AdminSite()

    @pytest.fixture
    def subject_admin(self, admin_site):
        """Create SubjectAdmin instance."""
        return SubjectAdmin(Subject, admin_site)

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
        return subject

    @pytest.fixture
    def request_factory(self):
        """Create request factory."""
        return RequestFactory()

    def test_admin_list_display(self, subject_admin, subject):
        """Test admin list view displays correct fields."""
        list_display = subject_admin.list_display

        assert 'name' in list_display
        assert 'description_preview' in list_display
        assert 'status_badge' in list_display
        assert 'subscriber_count_display' in list_display
        assert 'created_at' in list_display
        assert 'created_by' in list_display

    def test_admin_description_preview(self, subject_admin, subject):
        """Test description_preview truncates long descriptions."""
        subject.description = 'A' * 200
        subject.save()

        preview = subject_admin.description_preview(subject)
        assert len(preview) <= 103  # 100 chars + '...'
        assert preview.endswith('...')

    def test_admin_description_preview_short(self, subject_admin, subject):
        """Test description_preview doesn't truncate short descriptions."""
        subject.description = 'Short description'
        subject.save()

        preview = subject_admin.description_preview(subject)
        assert preview == 'Short description'
        assert not preview.endswith('...')

    def test_admin_status_badge_active(self, subject_admin, subject):
        """Test status_badge for active status."""
        subject.status = Subject.Status.ACTIVE
        badge = subject_admin.status_badge(subject)

        assert '#28a745' in badge  # Green color
        assert 'Active' in badge

    def test_admin_status_badge_archived(self, subject_admin, subject):
        """Test status_badge for archived status."""
        subject.status = Subject.Status.ARCHIVED
        badge = subject_admin.status_badge(subject)

        assert '#6c757d' in badge  # Gray color
        assert 'Archived' in badge

    def test_admin_subscriber_count_display(self, subject_admin, subject):
        """Test subscriber_count_display shows annotation."""
        subject._subscriber_count = 0
        count = subject_admin.subscriber_count_display(subject)

        assert count == 0

    def test_admin_queryset_optimization(self, subject_admin, admin_user, request_factory):
        """Test get_queryset optimizes with annotations and select_related."""
        request = request_factory.get('/admin/subscriptions/subject/')
        request.user = admin_user

        qs = subject_admin.get_queryset(request)

        # Check annotation exists (even if value is 0)
        first = qs.first()
        if first:
            assert hasattr(first, '_subscriber_count')

    def test_admin_save_model_sets_created_by(self, subject_admin, admin_user, request_factory):
        """Test save_model sets created_by on new objects."""
        request = request_factory.post('/admin/subscriptions/subject/add/')
        request.user = admin_user

        # Mock messages framework
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        subject = Subject(
            name='New Subject',
            description='Test'
        )

        # Save via admin (new object, change=False)
        subject_admin.save_model(request, subject, None, change=False)

        assert subject.created_by == admin_user

    def test_admin_save_model_preserves_created_by_on_update(self, subject_admin, admin_user, request_factory, subject):
        """Test save_model doesn't change created_by on updates."""
        original_creator = subject.created_by

        # Create different admin user
        other_admin = CustomUser.objects.create_user(
            email='other@test.com',
            password='testpass123',
            is_staff=True
        )

        request = request_factory.post(f'/admin/subscriptions/subject/{subject.id}/change/')
        request.user = other_admin

        # Mock messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # Update via admin (change=True)
        subject.description = 'Updated'
        subject_admin.save_model(request, subject, None, change=True)

        # created_by should remain unchanged
        assert subject.created_by == original_creator

    def test_admin_archive_subjects_action(self, subject_admin, admin_user, request_factory):
        """Test bulk archive action."""
        # Create multiple subjects
        subjects = []
        for i in range(3):
            s = Subject.objects.create(
                name=f'Subject {i}',
                description='Test',
                status=Subject.Status.ACTIVE,
                created_by=admin_user
            )
            subjects.append(s)

        request = request_factory.post('/admin/subscriptions/subject/')
        request.user = admin_user

        # Mock messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        queryset = Subject.objects.filter(id__in=[s.id for s in subjects])
        subject_admin.archive_subjects(request, queryset)

        # All subjects should be archived
        for subject in subjects:
            subject.refresh_from_db()
            assert subject.status == Subject.Status.ARCHIVED

    def test_admin_reactivate_subjects_action(self, subject_admin, admin_user, request_factory):
        """Test bulk reactivate action."""
        # Create archived subjects
        subjects = []
        for i in range(3):
            s = Subject.objects.create(
                name=f'Subject {i}',
                description='Test',
                status=Subject.Status.ARCHIVED,
                created_by=admin_user
            )
            subjects.append(s)

        request = request_factory.post('/admin/subscriptions/subject/')
        request.user = admin_user

        # Mock messages
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        queryset = Subject.objects.filter(id__in=[s.id for s in subjects])
        subject_admin.reactivate_subjects(request, queryset)

        # All subjects should be active
        for subject in subjects:
            subject.refresh_from_db()
            assert subject.status == Subject.Status.ACTIVE

    def test_admin_inline_web_sources(self, subject_admin):
        """Test WebSourceInline is configured."""
        inlines = subject_admin.inlines

        assert len(inlines) == 1
        assert inlines[0].model == WebSource

    def test_admin_list_filters(self, subject_admin):
        """Test list filters are configured."""
        list_filter = subject_admin.list_filter

        assert 'status' in list_filter
        assert 'created_at' in list_filter

    def test_admin_search_fields(self, subject_admin):
        """Test search fields are configured."""
        search_fields = subject_admin.search_fields

        assert 'name' in search_fields
        assert 'description' in search_fields

    def test_admin_readonly_fields(self, subject_admin):
        """Test readonly fields are configured."""
        readonly_fields = subject_admin.readonly_fields

        assert 'created_at' in readonly_fields
        assert 'updated_at' in readonly_fields


@pytest.mark.django_db
class TestWebSourceAdmin:
    """Integration tests for WebSourceAdmin."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user."""
        return CustomUser.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            is_staff=True
        )

    @pytest.fixture
    def admin_site(self):
        """Create admin site."""
        return AdminSite()

    @pytest.fixture
    def web_source_admin(self, admin_site):
        """Create WebSourceAdmin instance."""
        return WebSourceAdmin(WebSource, admin_site)

    @pytest.fixture
    def subject(self, admin_user):
        """Create subject."""
        return Subject.objects.create(
            name='Kubernetes',
            description='Test',
            created_by=admin_user
        )

    @pytest.fixture
    def web_source(self, subject):
        """Create web source."""
        return WebSource.objects.create(
            subject=subject,
            url='https://kubernetes.io/blog/'
        )

    def test_web_source_admin_list_display(self, web_source_admin):
        """Test WebSourceAdmin list display."""
        list_display = web_source_admin.list_display

        assert 'url' in list_display
        assert 'subject' in list_display
        assert 'created_at' in list_display

    def test_web_source_admin_queryset_optimization(self, web_source_admin, admin_user, web_source):
        """Test get_queryset uses select_related for subject."""
        from django.test import RequestFactory

        request = RequestFactory().get('/admin/subscriptions/websource/')
        request.user = admin_user

        qs = web_source_admin.get_queryset(request)

        # Query should be optimized
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as queries:
            list(qs)  # Execute query
            for ws in qs:
                _ = ws.subject.name  # Access related subject

        # Should not cause additional queries due to select_related
        assert len(queries) <= 2  # 1 for web_sources + select_related


@pytest.mark.django_db
class TestAdminPermissions:
    """Test admin interface access permissions."""

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
    def staff_user(self):
        """Create staff user (not superuser)."""
        return CustomUser.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            is_staff=True,
            is_superuser=False
        )

    @pytest.fixture
    def regular_user(self):
        """Create regular user."""
        return CustomUser.objects.create_user(
            email='user@test.com',
            password='testpass123',
            is_staff=False
        )

    def test_admin_access_superuser(self, admin_user, client):
        """Test superuser can access admin interface."""
        client.force_login(admin_user)
        response = client.get('/admin/subscriptions/subject/')

        assert response.status_code == 200

    def test_admin_access_staff_with_permissions(self, staff_user, client):
        """Test staff user with permissions can access admin."""
        # Grant change permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth.models import Permission

        content_type = ContentType.objects.get_for_model(Subject)
        permission = Permission.objects.get(
            codename='change_subject',
            content_type=content_type,
        )
        staff_user.user_permissions.add(permission)

        client.force_login(staff_user)
        response = client.get('/admin/subscriptions/subject/')

        assert response.status_code == 200

    def test_admin_access_regular_user_denied(self, regular_user, client):
        """Test regular user cannot access admin interface."""
        client.force_login(regular_user)
        response = client.get('/admin/subscriptions/subject/')

        # Should redirect to login
        assert response.status_code == 302
