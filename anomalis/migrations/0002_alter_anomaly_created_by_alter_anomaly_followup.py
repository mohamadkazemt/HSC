# Generated by Django 5.1.1 on 2024-10-11 19:19

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='anomaly',
            name='created_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_anomalies', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده'),
        ),
        migrations.AlterField(
            model_name='anomaly',
            name='followup',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_anomalies', to=settings.AUTH_USER_MODEL, verbose_name='پیگیری'),
        ),
    ]