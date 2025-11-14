"""
Subject and WebSource models for technology monitoring catalog.

This module defines the core data models for the subject catalog:
- Subject: Technology topics that users can subscribe to (e.g., "Kubernetes", "AI Ethics")
- WebSource: URLs associated with subjects for content scraping via Firecrawl
"""

import uuid
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords


class Subject(models.Model):
    """
    Technology monitoring subject model.

    Represents a technology topic that users can subscribe to for automated monitoring.
    Only active subjects are visible to end users. Admins have exclusive control over
    subject creation, modification, and archival.

    Fields:
        id: UUID primary key for distributed systems compatibility
        name: Unique subject name (e.g., "Kubernetes")
        description: Detailed description of the technology topic
        status: Active or archived status (only active subjects visible to users)
        created_at: Timestamp of subject creation
        updated_at: Timestamp of last modification
        created_by: Admin user who created the subject

    Constraints:
        - Name must be unique (case-sensitive at DB level)
        - Status indexed for efficient filtering
        - Name indexed for fast uniqueness checks and sorting

    Related Models:
        - WebSource: One-to-many relationship (subject.web_sources)
        - Future: Subscription (one-to-many, to be implemented in US-3)
    """

    class Status(models.TextChoices):
        """Subject status enum for catalog visibility control."""
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the subject"
    )
    name = models.CharField(
        max_length=200,
        unique=True,
        db_index=True,
        help_text="Unique name of the technology subject"
    )
    description = models.TextField(
        help_text="Detailed description of the technology topic"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Subject visibility status (active subjects are visible to users)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when subject was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when subject was last modified"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_subjects',
        help_text="Admin user who created this subject"
    )

    # Audit trail - tracks all changes to subject with user and timestamp
    # Creates HistoricalSubject table automatically via migration
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        """String representation of the subject (returns name)."""
        return self.name


class WebSource(models.Model):
    """
    Web scraping source URL model.

    Represents a URL associated with a subject for automated content scraping via Firecrawl.
    Each subject can have multiple web sources. Web sources are automatically deleted when
    their parent subject is deleted (CASCADE behavior).

    Fields:
        id: UUID primary key
        subject: Foreign key to parent Subject
        url: Web scraping URL (validated for RFC 3986 compliance)
        created_at: Timestamp of web source addition

    Constraints:
        - URL max length: 2048 characters (RFC 3986 recommendation)
        - Cascade delete with subject (deleting subject removes all web sources)

    Validation:
        - Django's URLField automatically validates RFC 3986 compliance
        - Accepts http:// and https:// protocols only
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the web source"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='web_sources',
        help_text="Parent subject for this web source"
    )
    url = models.URLField(
        max_length=2048,
        help_text="URL for content scraping (RFC 3986 compliant)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when web source was added"
    )

    class Meta:
        verbose_name = "Web Source"
        verbose_name_plural = "Web Sources"
        ordering = ['created_at']

    def __str__(self):
        """String representation of the web source (returns URL)."""
        return self.url
