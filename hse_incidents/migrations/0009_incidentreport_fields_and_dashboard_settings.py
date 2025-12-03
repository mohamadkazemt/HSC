# Generated manually
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('hse_incidents', '0008_incidentreport_related_risk'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # افزودن فیلدهای جدید به IncidentReport
        migrations.AddField(
            model_name='incidentreport',
            name='is_severe_production_stoppage',
            field=models.BooleanField(default=False, verbose_name='حادثه شدید منجر به توقف تولید'),
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='تاریخ ثبت'),
            preserve_default=False,
        ),
        # ایجاد مدل IncidentDashboardSettings
        migrations.CreateModel(
            name='IncidentDashboardSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('days_without_incident_start_date', models.DateField(blank=True, null=True, verbose_name='تاریخ شروع شمارش روزهای بدون حادثه (آخرین حادثه شدید منجر به توقف تولید)')),
                ('average_man_hours_per_day', models.IntegerField(default=2000, verbose_name='میانگین ساعت-کار روزانه (برای محاسبه شاخص\u200cهای FR, SR, FSI)')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ آخرین بروزرسانی')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_incident_settings', to='accounts.userprofile', verbose_name='بروزرسانی شده توسط')),
            ],
            options={
                'verbose_name': 'تنظیمات داشبورد حوادث',
                'verbose_name_plural': 'تنظیمات داشبورد حوادث',
            },
        ),
    ]

