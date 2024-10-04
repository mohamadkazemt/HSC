# Generated by Django 5.1.1 on 2024-10-04 05:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0002_anomaly'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorrectiveAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(max_length=500)),
                ('anomali_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalytype')),
            ],
        ),
    ]
