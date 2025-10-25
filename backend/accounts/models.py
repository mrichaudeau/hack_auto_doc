from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where email is the unique identifier
    for authentication instead of usernames.
    """

    class AuthProvider(models.TextChoices):
        STANDARD = 'standard', 'Standard'
        ENTRA_ID = 'entra_id', 'Microsoft Entra ID'
        UNIFIED = 'unified', 'Unified'

    email = models.EmailField(
        'email address',
        unique=True,
        db_index=True,
        help_text='Email address used for authentication (case-insensitive)'
    )
    first_name = models.CharField('first name', max_length=150, blank=True)
    last_name = models.CharField('last name', max_length=150, blank=True)
    auth_provider = models.CharField(
        'authentication provider',
        max_length=20,
        choices=AuthProvider.choices,
        default=AuthProvider.STANDARD,
        help_text='The authentication method used by this user'
    )
    is_active = models.BooleanField(
        'active',
        default=False,
        help_text='Designates whether this user should be treated as active. '
                  'Set to True after email verification for standard accounts.'
    )
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into the admin site.'
    )
    date_joined = models.DateTimeField('date joined', default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        db_table = 'auth_user'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        """
        Return the short name for the user.
        """
        return self.first_name

    def save(self, *args, **kwargs):
        """
        Override save to ensure email is always stored in lowercase.
        """
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
