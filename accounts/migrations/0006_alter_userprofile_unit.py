# Generated by Django 5.1.2 on 2024-11-27 18:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_department_position_userprofile_department_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='unit',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.unit', verbose_name='بخش'),
        ),
    ]
