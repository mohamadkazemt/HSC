# Generated by Django 5.1.2 on 2024-12-02 17:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('OperationsShiftReports', '0009_alter_loadingoperation_stone_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shiftreport',
            name='shift_leaves',
        ),
        migrations.DeleteModel(
            name='ShiftLeave',
        ),
    ]
