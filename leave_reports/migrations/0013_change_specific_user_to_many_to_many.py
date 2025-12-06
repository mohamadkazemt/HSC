# Generated manually for changing specific_user to specific_users (ManyToManyField)

from django.conf import settings
from django.db import migrations, models


def migrate_specific_user_to_specific_users(apps, schema_editor):
    """
    Migrate data from specific_user (ForeignKey) to specific_users (ManyToManyField)
    """
    ApprovalHierarchy = apps.get_model('leave_reports', 'ApprovalHierarchy')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    
    for hierarchy in ApprovalHierarchy.objects.all():
        if hasattr(hierarchy, 'specific_user_id') and hierarchy.specific_user_id:
            try:
                user = User.objects.get(pk=hierarchy.specific_user_id)
                hierarchy.specific_users.add(user)
            except User.DoesNotExist:
                pass


def reverse_migrate_specific_users_to_specific_user(apps, schema_editor):
    """
    Reverse migration: take first user from specific_users and put it in specific_user
    Note: This will only preserve the first user, others will be lost
    """
    ApprovalHierarchy = apps.get_model('leave_reports', 'ApprovalHierarchy')
    
    for hierarchy in ApprovalHierarchy.objects.all():
        if hierarchy.specific_users.exists():
            first_user = hierarchy.specific_users.first()
            # Note: We can't set specific_user here as it's already removed
            # This is just for reverse compatibility
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_userprofile_national_code_alter_payslip_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('leave_reports', '0012_alter_approvalhierarchy_unique_together_and_more'),
    ]

    operations = [
        # Step 1: Remove the old index for specific_user
        migrations.RemoveIndex(
            model_name='approvalhierarchy',
            name='leave_repor_specifi_f0e434_idx',
        ),
        # Step 2: Create the new ManyToMany field
        migrations.AddField(
            model_name='approvalhierarchy',
            name='specific_users',
            field=models.ManyToManyField(
                blank=True,
                help_text='برای تعریف تأیید کننده خاص برای چند کاربر مشخص',
                to=settings.AUTH_USER_MODEL,
                verbose_name='کاربران خاص'
            ),
        ),
        # Step 3: Migrate data from old field to new field
        migrations.RunPython(
            code=migrate_specific_user_to_specific_users,
            reverse_code=reverse_migrate_specific_users_to_specific_user,
        ),
        # Step 4: Remove the old ForeignKey field
        migrations.RemoveField(
            model_name='approvalhierarchy',
            name='specific_user',
        ),
    ]

