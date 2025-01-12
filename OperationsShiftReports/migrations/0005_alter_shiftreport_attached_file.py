# Generated by Django 5.1.2 on 2024-10-29 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('OperationsShiftReports', '0004_shiftreport_attached_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftreport',
            name='attached_file',
            field=models.FileField(blank=True, null=True, upload_to='shift_reports/%Y/%m/%d/', verbose_name='فایل ضمیمه'),
        ),
    ]
