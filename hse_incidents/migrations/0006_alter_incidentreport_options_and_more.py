# Generated by Django 5.1.2 on 2025-01-11 16:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hse_incidents', '0005_remove_incidentreport_incident_location_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='incidentreport',
            options={},
        ),
        migrations.AddField(
            model_name='incidentreport',
            name='is_completed',
            field=models.BooleanField(default=False, verbose_name='تکمیل شده'),
        ),
        migrations.CreateModel(
            name='HseCompletionReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('incident_report_time', models.TimeField(blank=True, null=True, verbose_name='ساعت اعلام حادثه')),
                ('hospital_admission_time', models.TimeField(blank=True, null=True, verbose_name='ساعت پذیرش در بیمارستان')),
                ('patient_condition_on_dispatch', models.TextField(blank=True, null=True, verbose_name='شرح حال حادثه دیده هنگام اعزام')),
                ('direct_causes', models.TextField(blank=True, null=True, verbose_name='علل مستقیم بروز حادثه')),
                ('indirect_causes', models.TextField(blank=True, null=True, verbose_name='علل غیر مستقیم بروز حادثه')),
                ('root_causes', models.TextField(blank=True, null=True, verbose_name='علل ریشه ای بروز حادثه')),
                ('social_security_notification', models.BooleanField(default=False, verbose_name='اعلام به بیمه تامین اجتماعی')),
                ('social_security_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست فایل بیمه تامین اجتماعی')),
                ('insurance_notification', models.BooleanField(default=False, verbose_name='اعلام به شرکت های بیمه ای')),
                ('insurance_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست فایل شرکت های بیمه')),
                ('police_notification', models.BooleanField(default=False, verbose_name='اعلام به نیروی انتظامی')),
                ('police_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست فایل نیروی انتظامی')),
                ('traffic_police_notification', models.BooleanField(default=False, verbose_name='اعلام به راهنمایی و رانندگی')),
                ('traffic_police_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست فایل راهنمایی و رانندگی')),
                ('labor_office_notification', models.BooleanField(default=False, verbose_name='اعلام به اداره کار')),
                ('final_injury_outcome', models.TextField(blank=True, null=True, verbose_name='نتیجه نهایی آسیب های ناشی از حادثه')),
                ('estimated_cost', models.CharField(blank=True, max_length=255, null=True, verbose_name='برآورد هزینه تقریبی')),
                ('lost_workdays', models.PositiveIntegerField(blank=True, null=True, verbose_name='روزهای کاری از دست رفته')),
                ('environmental_damage', models.BooleanField(default=False, verbose_name='آسیب به محیط زیست دارد؟')),
                ('environmental_damage_type', models.CharField(blank=True, max_length=255, null=True, verbose_name='نوع آسیب به محیط زیست')),
                ('environmental_damage_description', models.TextField(blank=True, null=True, verbose_name='شرح مختصر آسیب وارد شده به محیط زیست')),
                ('incident_committee_formed', models.BooleanField(default=False, verbose_name='کمیته حوادث تشکیل گردید؟')),
                ('incident_committee_date', models.DateField(blank=True, null=True, verbose_name='تاریخ برگزاری کمیته حوادث')),
                ('incident_committee_details', models.TextField(blank=True, null=True, verbose_name='شرح مختصر جزئیات کمیته حوادث')),
                ('incident_committee_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست صورتجلسه کمیته حوادث')),
                ('corrective_actions', models.TextField(blank=True, null=True, verbose_name='اقدامات اصلاحی و پیشگیرانه')),
                ('lessons_learned', models.BooleanField(default=False, verbose_name='درس آموزی از حادثه دارد؟')),
                ('lessons_learned_file', models.FileField(blank=True, null=True, upload_to='incident_files/', verbose_name='پیوست درس آموزی حادثه')),
                ('incident_report', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hse_completion', to='hse_incidents.incidentreport', verbose_name='گزارش حادثه')),
            ],
            options={
                'verbose_name': 'گزارش تکمیل حادثه',
                'verbose_name_plural': 'گزارشات تکمیل حوادث',
            },
        ),
    ]