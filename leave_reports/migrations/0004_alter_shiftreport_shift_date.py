# Generated by Django 5.1.2 on 2024-12-06 12:46

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_reports', '0003_shiftreport_crate_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftreport',
            name='shift_date',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
