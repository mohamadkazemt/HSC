# Generated by Django 5.1.2 on 2024-11-10 15:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LocationSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(max_length=100)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.location')),
            ],
            options={
                'verbose_name': 'بخش محل',
                'verbose_name_plural': 'بخش های محل ها',
            },
        ),
        migrations.AddField(
            model_name='anomaly',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='anomalies', to='anomalis.locationsection', verbose_name='بخش محل '),
        ),
    ]
