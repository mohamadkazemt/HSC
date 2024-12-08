# Generated by Django 5.1.2 on 2024-11-29 05:28

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_reports', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftreport',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shiftreport',
            name='work_group',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]