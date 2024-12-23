# Generated by Django 5.1.2 on 2024-11-18 14:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anomalis', '0002_locationsection_anomaly_section'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anomaly',
            name='description',
            field=models.TextField(verbose_name='توضیحات'),
        ),
        migrations.AlterField(
            model_name='anomaly',
            name='hse_type',
            field=models.CharField(choices=[('H', 'Health'), ('S', 'Safety'), ('E', 'Environment')], max_length=1, verbose_name='حوزه HSE'),
        ),
        migrations.AlterField(
            model_name='anomaly',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.location', verbose_name='سایت'),
        ),
        migrations.AlterField(
            model_name='anomaly',
            name='section',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='anomalies', to='anomalis.locationsection', verbose_name='محل شناسایی آنومالی'),
        ),
    ]
