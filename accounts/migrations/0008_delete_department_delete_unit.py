# Generated by Django 5.1.2 on 2025-01-04 15:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_part_section_remove_unit_department_and_more'),
        ('permissions', '0003_remove_unitpermission_unit_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Department',
        ),
        migrations.DeleteModel(
            name='Unit',
        ),
    ]