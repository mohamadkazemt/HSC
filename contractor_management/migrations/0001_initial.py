# Generated by Django 5.1.2 on 2024-12-06 13:27

import django.db.models.deletion
import django_jalali.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contractor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=255, verbose_name='نام شرکت/پیمانکار')),
                ('manager_name', models.CharField(max_length=255, verbose_name='نام مدیرعامل')),
                ('activity_field', models.CharField(max_length=255, verbose_name='حوزه فعالیت')),
                ('manager_phone', models.CharField(max_length=15, verbose_name='شماره تماس مدیرعامل')),
                ('liability_insurance', models.BooleanField(default=False, verbose_name='بیمه مسئولیت مدنی')),
                ('liability_insurance_expiry', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ انقضای بیمه مسئولیت مدنی')),
                ('contract_file', models.FileField(blank=True, null=True, upload_to='contracts/', verbose_name='قرارداد پیوست شده')),
                ('fire_insurance', models.BooleanField(default=False, verbose_name='بیمه آتش\u200cسوزی')),
                ('contractor_certificate_expiry', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ انقضای صلاحیت پیمانکاری')),
                ('safety_certificate_expiry', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ انقضای صلاحیت ایمنی')),
                ('hse_plan', models.FileField(blank=True, null=True, upload_to='hse_plans/', verbose_name='طرح ایمنی، بهداشت و محیط زیست')),
                ('social_insurance', models.BooleanField(default=False, verbose_name='بیمه تامین اجتماعی')),
            ],
            options={
                'verbose_name': 'پیمانکار',
                'verbose_name_plural': 'پیمانکاران',
            },
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=255, verbose_name='نام')),
                ('last_name', models.CharField(max_length=255, verbose_name='نام خانوادگی')),
                ('national_id', models.CharField(max_length=10, unique=True, verbose_name='کد ملی')),
                ('birth_date', django_jalali.db.models.jDateField(verbose_name='تاریخ تولد')),
                ('phone_number', models.CharField(max_length=15, verbose_name='شماره تماس')),
                ('education', models.CharField(max_length=255, verbose_name='مدرک تحصیلی')),
                ('position', models.CharField(max_length=255, verbose_name='سمت')),
                ('health_certificate', models.FileField(blank=True, null=True, upload_to='health_certificates/', verbose_name='معاینات سلامت شغلی')),
                ('background_check', models.FileField(blank=True, null=True, upload_to='background_checks/', verbose_name='سو پیشینه و عدم اعتیاد')),
                ('safety_training', models.FileField(blank=True, null=True, upload_to='safety_training/', verbose_name='دوره آموزش ایمنی عمومی')),
                ('other_trainings', models.TextField(blank=True, null=True, verbose_name='سایر آموزش\u200cهای فراگرفته')),
                ('entry_permit_expiration', django_jalali.db.models.jDateField(blank=True, null=True, verbose_name='تاریخ انقضای مجوز ورود')),
                ('contractor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='contractor_management.contractor', verbose_name='پیمانکار')),
            ],
            options={
                'verbose_name': 'کارمند',
                'verbose_name_plural': 'کارمندان',
            },
        ),
        migrations.CreateModel(
            name='Vehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_type', models.CharField(max_length=255, verbose_name='نوع خودرو')),
                ('license_plate', models.CharField(max_length=20, unique=True, verbose_name='شماره پلاک خودرو')),
                ('vehicle_card', models.FileField(blank=True, null=True, upload_to='vehicle_cards/', verbose_name='کارت خودرو')),
                ('insurance_expiry', models.DateField(blank=True, null=True, verbose_name='تاریخ انقضای بیمه\u200cنامه')),
                ('technical_inspection_expiry', models.DateField(blank=True, null=True, verbose_name='تاریخ انقضای معاینه فنی')),
                ('driver_name', models.CharField(max_length=255, verbose_name='نام راننده')),
                ('permit_expiry', models.DateField(blank=True, null=True, verbose_name='تاریخ انقضای آخرین مجوز خودرو')),
                ('contractor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='contractor_management.contractor', verbose_name='پیمانکار')),
            ],
            options={
                'verbose_name': 'خودرو',
                'verbose_name_plural': 'خودروها',
            },
        ),
    ]