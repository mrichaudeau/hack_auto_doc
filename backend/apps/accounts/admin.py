"""
Django admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, EmailVerificationToken, LoginAuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin interface for CustomUser model.
    """
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Verification'), {'fields': ('is_email_verified', 'email_verified_at')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_active'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'email_verified_at')


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailVerificationToken model.
    """
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('token', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        """Disable manual token creation through admin."""
        return False


@admin.register(LoginAuditLog)
class LoginAuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for LoginAuditLog model.

    Provides read-only access to login audit logs for security monitoring.
    """
    list_display = ('email', 'success', 'ip_address', 'failure_reason', 'timestamp')
    list_filter = ('success', 'failure_reason', 'timestamp')
    search_fields = ('email', 'ip_address', 'user__email')
    readonly_fields = ('user', 'email', 'ip_address', 'user_agent', 'success', 'failure_reason', 'timestamp')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        """Disable manual creation of audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs for compliance."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make all fields read-only."""
        return False
