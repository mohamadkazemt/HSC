# Generated by Django 5.1.2 on 2024-12-16 17:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('BaseInfo', '0011_miningmachine_contractor_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('shift', models.CharField(choices=[('morning', 'صبح'), ('evening', 'عصر'), ('night', 'شب')], max_length=10, verbose_name='شیفت کاری')),
                ('supervisor_comments', models.TextField(blank=True, verbose_name='توضیحات سرشیفت')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='افسر ایمنی')),
            ],
        ),
        migrations.CreateModel(
            name='BlastingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('explosion_occurred', models.BooleanField(default=False, verbose_name='انفجار انجام شد؟')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('block', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.miningblock', verbose_name='بلوک آتشباری')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blasting_details', to='dailyreport_hse.dailyreport')),
            ],
        ),
        migrations.CreateModel(
            name='DrillingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], max_length=10, verbose_name='وضعیت حفاری')),
                ('block', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.miningblock', verbose_name='بلوک حفاری')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drilling_details', to='dailyreport_hse.dailyreport')),
                ('machine', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.miningmachine', verbose_name='دستگاه حفاری')),
            ],
        ),
        migrations.CreateModel(
            name='DumpDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], max_length=10, verbose_name='وضعیت دامپ')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dump_details', to='dailyreport_hse.dailyreport')),
                ('dump', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.dump', verbose_name='دامپ')),
            ],
        ),
        migrations.CreateModel(
            name='FollowupDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='توضیحات')),
                ('files', models.FileField(blank=True, null=True, upload_to='followups/', verbose_name='فایل\u200cهای پیوست')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_details', to='dailyreport_hse.dailyreport')),
            ],
        ),
        migrations.CreateModel(
            name='InspectionDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inspection_done', models.BooleanField(default=False, verbose_name='بازدید انجام شد؟')),
                ('status', models.CharField(blank=True, choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], max_length=10, null=True, verbose_name='وضعیت بازدید')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspection_details', to='dailyreport_hse.dailyreport')),
            ],
        ),
        migrations.CreateModel(
            name='LoadingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], max_length=10, verbose_name='وضعیت بارگیری')),
                ('block', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.miningblock', verbose_name='بلوک بارگیری')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loading_details', to='dailyreport_hse.dailyreport')),
                ('machine', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='BaseInfo.miningmachine', verbose_name='دستگاه بارگیری')),
            ],
        ),
        migrations.CreateModel(
            name='StoppageDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField(verbose_name='علت توقف')),
                ('start_time', models.TimeField(verbose_name='زمان شروع')),
                ('end_time', models.TimeField(verbose_name='زمان پایان')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('daily_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stoppage_details', to='dailyreport_hse.dailyreport')),
            ],
        ),
    ]
