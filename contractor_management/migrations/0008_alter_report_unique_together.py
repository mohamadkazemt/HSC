# Generated by Django 5.1.2 on 2024-12-28 16:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contractor_management', '0007_report_group_report_shift'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='report',
            unique_together={('vehicle', 'report_datetime', 'shift')},
        ),
    ]
