# Generated by Django 5.1.1 on 2024-10-03 17:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Anomaly',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('anomalytype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalytype')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_anomalies', to=settings.AUTH_USER_MODEL)),
                ('followup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_anomalies', to=settings.AUTH_USER_MODEL)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.location')),
            ],
        ),
    ]
