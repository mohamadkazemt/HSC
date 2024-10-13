# Generated by Django 5.1.1 on 2024-10-13 15:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0005_comments'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comments',
            name='anomaly',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='anomalis.anomaly', verbose_name='آنومالی'),
        ),
    ]
