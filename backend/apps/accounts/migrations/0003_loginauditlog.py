# Generated manually for US-3: Standard User Login
# Task: TASK-3.1 - Create LoginAuditLog Model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_rename_is_verified_to_is_email_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginAuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(db_index=True, help_text='Email address used in login attempt', max_length=255, verbose_name='email address')),
                ('ip_address', models.GenericIPAddressField(help_text='IP address of the client (supports IPv4 and IPv6)', verbose_name='IP address')),
                ('user_agent', models.TextField(help_text='Browser/client user agent string', verbose_name='user agent')),
                ('success', models.BooleanField(db_index=True, default=False, help_text='Whether the login attempt was successful', verbose_name='success')),
                ('failure_reason', models.CharField(blank=True, choices=[('invalid_credentials', 'Invalid email or password'), ('email_not_verified', 'Email not verified'), ('rate_limited', 'Rate limit exceeded'), ('account_disabled', 'Account disabled')], help_text='Reason for failed login attempt', max_length=100, null=True, verbose_name='failure reason')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When the login attempt occurred', verbose_name='timestamp')),
                ('user', models.ForeignKey(blank=True, help_text='User attempting to login (null if user not found)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='login_attempts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'login audit log',
                'verbose_name_plural': 'login audit logs',
                'db_table': 'login_audit_log',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='loginauditlog',
            index=models.Index(fields=['email', 'timestamp'], name='idx_audit_email_time'),
        ),
        migrations.AddIndex(
            model_name='loginauditlog',
            index=models.Index(fields=['ip_address', 'timestamp'], name='idx_audit_ip_time'),
        ),
        migrations.AddIndex(
            model_name='loginauditlog',
            index=models.Index(fields=['user', 'timestamp'], name='idx_audit_user_time'),
        ),
        migrations.AddIndex(
            model_name='loginauditlog',
            index=models.Index(fields=['success'], name='idx_audit_success'),
        ),
    ]
