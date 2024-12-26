# Generated by Django 5.1.2 on 2024-12-26 18:22

import django.db.models.deletion
import django_jalali.db.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contractor_management', '0005_alter_vehicle_insurance_expiry_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_datetime', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ و زمان ثبت گزارش')),
                ('status', models.CharField(choices=[('full', 'کارکرد کامل (8 ساعت)'), ('partial', 'کارکرد ناقص'), ('inactive', 'غیر فعال')], default='full', max_length=10, verbose_name='وضعیت کارکرد')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='ساعت شروع کار')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='ساعت پایان کار')),
                ('stop_active', models.BooleanField(default=False, verbose_name='توقف فعال')),
                ('stop_time', models.PositiveIntegerField(blank=True, null=True, verbose_name='مدت زمان توقف (دقیقه)')),
                ('stop_reason', models.TextField(blank=True, null=True, verbose_name='دلیل توقف')),
                ('restart_time', models.TimeField(blank=True, null=True, verbose_name='ساعت شروع کار بعد از توقف')),
                ('inactive_reason', models.TextField(blank=True, null=True, verbose_name='دلیل غیر فعال بودن')),
                ('contractor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contractor_management.contractor', verbose_name='پیمانکار')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='کاربر')),
                ('vehicle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contractor_management.vehicle', verbose_name='خودرو')),
            ],
            options={
                'verbose_name': 'گزارش کارکرد خودرو',
                'verbose_name_plural': 'گزارش کارکرد خودروها',
            },
        ),
    ]
