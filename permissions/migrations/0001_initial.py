# Generated by Django 5.1.2 on 2024-12-24 19:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0006_alter_userprofile_unit'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('view_name', models.CharField(max_length=100, verbose_name='نام ویو')),
                ('can_view', models.BooleanField(default=False, verbose_name='مشاهده')),
                ('can_add', models.BooleanField(default=False, verbose_name='افزودن')),
                ('can_edit', models.BooleanField(default=False, verbose_name='ویرایش')),
                ('can_delete', models.BooleanField(default=False, verbose_name='حذف')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.department', verbose_name='بخش')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.position', verbose_name='پست')),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.unit', verbose_name='واحد')),
            ],
        ),
    ]
