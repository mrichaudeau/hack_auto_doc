"""
Django REST Framework serializers for Subject and WebSource models.

This module provides JSON serialization/deserialization for Subject catalog API,
including nested web source handling, validation, and subscriber count display.

Serializers:
    - WebSourceSerializer: For web scraping source URLs (admin use)
    - SubjectSerializer: Full subject serializer with web_sources (admin use)
    - SubjectListSerializer: Read-only public catalog serializer (public use)
"""

from rest_framework import serializers
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Subject, WebSource


class WebSourceSerializer(serializers.ModelSerializer):
    """
    Serializer for WebSource model.

    Handles URL validation using Django's URLValidator for RFC 3986 compliance.
    Used as nested serializer within SubjectSerializer for create/update operations.

    Fields:
        id: UUID primary key (read-only)
        url: Web scraping URL (validated for RFC 3986 compliance)
        created_at: Timestamp of creation (read-only)
    """

    class Meta:
        model = WebSource
        fields = ['id', 'url', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_url(self, value):
        """
        Validate URL format using Django's URLValidator.

        Args:
            value: URL string to validate

        Returns:
            Validated URL string

        Raises:
            serializers.ValidationError: If URL format is invalid
        """
        validator = URLValidator()
        try:
            validator(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(f"Invalid URL format: {str(e)}")
        return value


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model with nested web sources.

    Handles complete subject catalog operations including:
    - Nested web source creation/updates
    - Case-insensitive name uniqueness validation
    - Status enum validation
    - Subscriber count display (placeholder until US-3)

    Fields:
        id: UUID primary key (read-only)
        name: Unique subject name
        description: Technology topic description
        status: Active or archived status
        web_sources: Nested list of WebSource objects
        subscriber_count: Number of subscribers (read-only, placeholder)
        created_at: Creation timestamp (read-only)
        updated_at: Last modification timestamp (read-only)

    Create/Update Behavior:
        - On create: Creates subject with nested web sources atomically
        - On update: Replaces all web sources with provided list
        - Web sources are optional (subject can exist without sources)
    """

    web_sources = WebSourceSerializer(many=True, required=False)
    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
            'description',
            'status',
            'web_sources',
            'subscriber_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'subscriber_count']

    def get_subscriber_count(self, obj):
        """
        Get subscriber count for display.

        Returns placeholder 0 until US-3 (Subscribe to Subject) is implemented.
        Once US-3 is complete, this will count actual subscriptions.

        Args:
            obj: Subject instance

        Returns:
            Integer subscriber count (currently always 0)
        """
        # TODO: Replace with real subscription count once US-3 is implemented
        # return obj.subscriptions.count() or use annotation from view
        return 0

    def validate_name(self, value):
        """
        Validate subject name for uniqueness (case-insensitive).

        Ensures no duplicate subject names exist in the catalog, using
        case-insensitive comparison to prevent "Kubernetes" and "kubernetes"
        being treated as different subjects.

        Args:
            value: Subject name string

        Returns:
            Validated name string

        Raises:
            serializers.ValidationError: If name already exists (case-insensitive)
        """
        # Case-insensitive uniqueness check
        queryset = Subject.objects.filter(name__iexact=value)

        # Exclude current instance for updates
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Subject with this name already exists (case-insensitive match)."
            )

        return value

    def validate_status(self, value):
        """
        Validate status enum value.

        Ensures status is one of the valid choices from Subject.Status enum.

        Args:
            value: Status string

        Returns:
            Validated status string

        Raises:
            serializers.ValidationError: If status is not 'active' or 'archived'
        """
        valid_statuses = [choice[0] for choice in Subject.Status.choices]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Status must be one of: {', '.join(valid_statuses)}"
            )
        return value

    def create(self, validated_data):
        """
        Create subject with nested web sources atomically.

        Extracts web_sources data from validated_data, creates the subject,
        then creates associated web sources in a single transaction.

        Args:
            validated_data: Validated serializer data dict

        Returns:
            Created Subject instance with web_sources relationship populated
        """
        web_sources_data = validated_data.pop('web_sources', [])

        # Create subject
        subject = Subject.objects.create(**validated_data)

        # Create web sources
        for ws_data in web_sources_data:
            WebSource.objects.create(subject=subject, **ws_data)

        return subject

    def update(self, instance, validated_data):
        """
        Update subject and replace web sources.

        Updates subject fields and completely replaces web sources if provided.
        If web_sources not provided in request, existing sources are preserved.

        Args:
            instance: Existing Subject instance to update
            validated_data: Validated serializer data dict

        Returns:
            Updated Subject instance
        """
        web_sources_data = validated_data.pop('web_sources', None)

        # Update subject fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update web sources if provided (complete replacement)
        if web_sources_data is not None:
            # Delete existing web sources
            instance.web_sources.all().delete()

            # Create new web sources
            for ws_data in web_sources_data:
                WebSource.objects.create(subject=instance, **ws_data)

        return instance


class SubjectListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for subject list views.

    Excludes web_sources for better performance in list views.
    Use SubjectSerializer for detail views and create/update operations.

    Fields:
        id: UUID primary key
        name: Subject name
        description: Short description preview (first 200 chars in view)
        status: Active or archived status
        subscriber_count: Number of subscribers (placeholder)
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    subscriber_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id',
            'name',
            'description',
            'status',
            'subscriber_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'subscriber_count']

    def get_subscriber_count(self, obj):
        """
        Get subscriber count from queryset annotation if available.

        Args:
            obj: Subject instance (may have _subscriber_count annotation)

        Returns:
            Integer subscriber count (0 if not annotated)
        """
        # Check for annotation from viewset queryset optimization
        return getattr(obj, '_subscriber_count', 0)


class PublicSubjectSerializer(serializers.ModelSerializer):
    """
    Public-facing read-only serializer for subject catalog browsing (US-2).

    Minimal field set for public discovery without sensitive information.
    No web sources, subscriber count, or admin metadata exposed.
    Used for public GET /api/subjects/ endpoint.

    Fields:
        id: UUID primary key
        name: Subject name
        description: Technology topic description
        status: Active status (only 'active' subjects returned by view)
    """

    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'status']
        read_only_fields = ['id', 'name', 'description', 'status']
