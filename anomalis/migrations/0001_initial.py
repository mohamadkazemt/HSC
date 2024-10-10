# Generated by Django 5.1.1 on 2024-10-10 16:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Anomalytype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'نوع آنومالی',
                'verbose_name_plural': 'نوع\u200cهای آنومالی',
            },
        ),
        migrations.CreateModel(
            name='HSE',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
            options={
                'verbose_name': 'نوع آنومالی HSE',
                'verbose_name_plural': 'نوع\u200cهای آنومالی HSE',
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': 'محل آنومالی',
                'verbose_name_plural': 'محل\u200cهای آنومالی',
            },
        ),
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('priority', models.CharField(max_length=20, verbose_name='اولویت')),
            ],
            options={
                'verbose_name': 'اولویت ',
                'verbose_name_plural': 'اولویت ها',
            },
        ),
        migrations.CreateModel(
            name='AnomalyDescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(max_length=500, verbose_name='شرح آنومالی')),
                ('hse_type', models.CharField(choices=[('H', 'Health'), ('S', 'Safety'), ('E', 'Environment')], max_length=1, verbose_name='نوع HSE')),
                ('anomalytype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalytype', verbose_name='نوع آنومالی')),
            ],
            options={
                'verbose_name': 'شرح آنومالی',
                'verbose_name_plural': 'شرح\u200cهای آنومالی',
            },
        ),
        migrations.CreateModel(
            name='CorrectiveAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(max_length=500, verbose_name='شرح عملیات اصلاحی')),
                ('anomali_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalytype', verbose_name='نوع آنومالی')),
            ],
            options={
                'verbose_name': 'عملیات اصلاحی',
                'verbose_name_plural': 'عملیات\u200cهای اصلاحی',
            },
        ),
        migrations.CreateModel(
            name='Anomaly',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(verbose_name='شرح آنومالی')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('action', models.BooleanField(default=True, verbose_name='وضعیت')),
                ('image', models.ImageField(blank=True, null=True, upload_to='anomalies/%Y/%m/%d', verbose_name='تصویر آنومالی')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_anomalies', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
                ('followup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followup_anomalies', to=settings.AUTH_USER_MODEL, verbose_name='پیگیری')),
                ('anomalydescription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalydescription', verbose_name='شرح آنومالی')),
                ('anomalytype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.anomalytype', verbose_name='نوع آنومالی')),
                ('correctiveaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.correctiveaction', verbose_name='عملیات اصلاحی')),
                ('hse_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.hse', verbose_name='نوع HSE')),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.location', verbose_name='محل آنومالی')),
                ('priority', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='anomalis.priority', verbose_name='اولویت')),
            ],
            options={
                'verbose_name': 'آنومالی',
                'verbose_name_plural': 'آنومالی ها',
            },
        ),
    ]
