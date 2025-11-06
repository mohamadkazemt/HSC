# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fire_reports', '0006_delete_vehiclestatusreport'),
        ('BaseInfo', '0013_emergencyvehicle_has_brake_and_more'),
        ('contractor_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VehicleChecklist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_source', models.CharField(choices=[('company', 'خودروی شرکت'), ('contractor', 'خودروی پیمانکار')], max_length=20, verbose_name='منبع خودرو')),
                ('horn_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت بوق و چراغ گردان')),
                ('horn_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت بوق و چراغ گردان')),
                ('hose_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت شیلنگ‌ها و اتصالات')),
                ('hose_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت شیلنگ‌ها و اتصالات')),
                ('monitor_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت مانیتور')),
                ('monitor_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت مانیتور')),
                ('extinguisher_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت خاموش‌کننده‌های دستی')),
                ('extinguisher_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت خاموش‌کننده‌های دستی')),
                ('equipment_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت تجهیزات آتش‌نشانی')),
                ('equipment_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت تجهیزات آتش‌نشانی')),
                ('foam_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت پودر و فوم خودرو')),
                ('foam_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت پودر و فوم خودرو')),
                ('water_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت آب')),
                ('water_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت آب')),
                ('tire_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت لاستیک‌ها')),
                ('tire_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت لاستیک‌ها')),
                ('brake_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت سیستم ترمز خودرو')),
                ('brake_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت سیستم ترمز خودرو')),
                ('lighting_status', models.CharField(choices=[('suitable', 'مناسب'), ('unsuitable', 'نامناسب')], max_length=10, verbose_name='وضعیت سیستم روشنایی')),
                ('lighting_description', models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت سیستم روشنایی')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت')),
                ('company_vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.emergencyvehicle', verbose_name='خودروی امدادی شرکت')),
                ('contractor_vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contractor_management.vehicle', verbose_name='خودروی پیمانکار')),
                ('fire_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vehicle_checklists', to='fire_reports.firereport', verbose_name='گزارش آتش‌نشانی')),
            ],
            options={
                'verbose_name': 'چک‌لیست خودرو',
                'verbose_name_plural': 'چک‌لیست‌های خودرو',
                'ordering': ['-created_at'],
            },
        ),
    ]

