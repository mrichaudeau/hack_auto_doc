# Generated manually to rename is_verified to is_email_verified

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='is_verified',
            new_name='is_email_verified',
        ),
    ]
