"""
Django Admin configuration for Subject and WebSource management.

This module provides comprehensive admin interface for technology monitoring
subject catalog management, including inline web source editing, bulk operations,
and subscriber count display.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from simple_history.admin import SimpleHistoryAdmin
from .models import Subject, WebSource


class WebSourceInline(admin.TabularInline):
    """
    Inline admin for managing web sources within Subject admin.

    Allows administrators to add, edit, and delete web scraping URLs
    directly from the Subject edit page without navigating away.
    """
    model = WebSource
    extra = 1
    fields = ('url',)
    verbose_name = "Web Source"
    verbose_name_plural = "Web Sources"


@admin.register(Subject)
class SubjectAdmin(SimpleHistoryAdmin):
    """
    Django Admin configuration for Subject model.

    Features:
    - List display with name, description preview, status badge, subscriber count
    - Filtering by status and creation date
    - Search by name and description
    - Inline web source editing
    - Bulk archive/reactivate operations
    - History tracking via django-simple-history
    - Subscriber count annotation (placeholder until US-3)

    Performance optimizations:
    - select_related for created_by FK
    - Annotated subscriber_count for efficient display
    """

    list_display = (
        'name',
        'description_preview',
        'status_badge',
        'subscriber_count_display',
        'created_at',
        'created_by',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'
    inlines = [WebSourceInline]
    actions = ['archive_subjects', 'reactivate_subjects']
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Subject Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related and subscriber count annotation.

        Annotates queryset with subscriber count for efficient display.
        TODO: Replace Count('id') * 0 with Count('subscriptions') once US-3 is implemented.
        """
        qs = super().get_queryset(request)
        # Placeholder annotation: returns 0 until US-3 (Subscribe to Subject) is implemented
        # Once US-3 is complete, replace with: qs.annotate(_subscriber_count=Count('subscriptions'))
        qs = qs.annotate(_subscriber_count=Count('id') * 0)
        qs = qs.select_related('created_by')
        return qs

    def description_preview(self, obj):
        """
        Display truncated description (100 characters max) in list view.

        Args:
            obj: Subject instance

        Returns:
            Truncated description string with ellipsis if longer than 100 chars
        """
        if len(obj.description) > 100:
            return obj.description[:100] + '...'
        return obj.description

    description_preview.short_description = 'Description'

    def status_badge(self, obj):
        """
        Display color-coded status badge for visual identification.

        Args:
            obj: Subject instance

        Returns:
            HTML-formatted status badge (green for active, gray for archived)
        """
        color = '#28a745' if obj.status == Subject.Status.ACTIVE else '#6c757d'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Status'

    def subscriber_count_display(self, obj):
        """
        Display subscriber count from annotated queryset.

        Args:
            obj: Subject instance with _subscriber_count annotation

        Returns:
            Integer subscriber count (0 until US-3 implemented)
        """
        return getattr(obj, '_subscriber_count', 0)

    subscriber_count_display.short_description = 'Subscribers'
    subscriber_count_display.admin_order_field = '_subscriber_count'

    def archive_subjects(self, request, queryset):
        """
        Bulk action to archive selected subjects.

        Sets status to ARCHIVED for all selected subjects, hiding them
        from user-facing API endpoints while preserving data for audit trail.

        Args:
            request: HttpRequest object
            queryset: QuerySet of selected Subject instances
        """
        updated = queryset.update(status=Subject.Status.ARCHIVED)
        self.message_user(
            request,
            f'{updated} subject(s) archived successfully.',
            level='success'
        )

    archive_subjects.short_description = 'Archive selected subjects'

    def reactivate_subjects(self, request, queryset):
        """
        Bulk action to reactivate archived subjects.

        Sets status to ACTIVE for all selected subjects, making them
        visible again in user-facing API endpoints.

        Args:
            request: HttpRequest object
            queryset: QuerySet of selected Subject instances
        """
        updated = queryset.update(status=Subject.Status.ACTIVE)
        self.message_user(
            request,
            f'{updated} subject(s) reactivated successfully.',
            level='success'
        )

    reactivate_subjects.short_description = 'Reactivate selected subjects'

    def save_model(self, request, obj, form, change):
        """
        Override save to auto-populate created_by with current admin user.

        Args:
            request: HttpRequest object
            obj: Subject instance being saved
            form: ModelForm instance
            change: Boolean indicating if this is an update (True) or create (False)
        """
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WebSource)
class WebSourceAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for WebSource model.

    Provides standalone admin interface for web sources in case
    administrators need to manage them independently of subjects.
    Most web source management is done via SubjectAdmin inline.
    """

    list_display = ('url', 'subject', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('url', 'subject__name')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        """Optimize queryset with select_related for subject FK."""
        qs = super().get_queryset(request)
        return qs.select_related('subject')
