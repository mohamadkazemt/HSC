from django.db import migrations


def migrate_notifications(apps, schema_editor):
    OldNotification = apps.get_model('fire_extinguisher_management', 'Notification')
    DashboardNotification = apps.get_model('dashboard', 'Notification')

    for old in OldNotification.objects.all():
        notification_type = 'warning'
        message = old.message or ''
        lowered = message.lower()
        if 'منقضی' in message or 'انقضا' in message or 'نیاز به تعمیر' in message:
            notification_type = 'warning'
        elif 'سرویس' in message or 'ثبت شد' in message:
            notification_type = 'info'

        DashboardNotification.objects.create(
            user=old.user,
            title='اعلان کپسول آتش‌نشانی',
            message=message,
            notification_type=notification_type,
            url=old.url or '',
            is_read=old.is_read,
            read_at=old.created_at if old.is_read else None,
            created_at=old.created_at,
        )


def reverse_migration(apps, schema_editor):
    DashboardNotification = apps.get_model('dashboard', 'Notification')
    DashboardNotification.objects.filter(title='اعلان کپسول آتش‌نشانی').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('fire_extinguisher_management', '0001_initial'),
        ('dashboard', '0005_alter_notification_options_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_notifications, reverse_migration),
    ]
