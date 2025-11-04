"""
Test data factories for accounts app using factory_boy.

Provides reusable factories for creating test instances of models.
"""

import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'testuser{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = False
    is_email_verified = False

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        """Set password after creation."""
        if not create:
            return
        password = extracted or 'TestPassword123!'
        obj.set_password(password)
        obj.save()


class ActiveUserFactory(UserFactory):
    """Factory for creating active, verified users."""

    is_active = True
    is_email_verified = True
