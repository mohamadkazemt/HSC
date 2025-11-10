from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fire_extinguisher_management', '0002_migrate_notifications'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Notification',
        ),
    ]
