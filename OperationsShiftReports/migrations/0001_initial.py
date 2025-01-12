# Generated by Django 5.1.2 on 2024-10-26 16:06

import shift_manager.utils
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoadingOperation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stone_type', models.CharField(choices=[('w', 'باطله'), ('O', 'آهن'), ('T', 'آهن کم عیار')], default='w', max_length=50, verbose_name='نوع سنگ')),
                ('load_count', models.IntegerField(default=0, verbose_name='تعداد بار')),
            ],
        ),
        migrations.CreateModel(
            name='MiningMachineReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('machine_name', models.CharField(max_length=100, verbose_name='نام دستگاه')),
                ('machine_type', models.CharField(max_length=50, verbose_name='نوع دستگاه')),
                ('block', models.CharField(max_length=100, verbose_name='نام بلوک')),
            ],
        ),
        migrations.CreateModel(
            name='ShiftLeave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('personnel_name', models.CharField(max_length=100, verbose_name='نام پرسنل')),
                ('leave_status', models.CharField(choices=[('authorized', 'مجاز'), ('unauthorized', 'غیر مجاز')], default='unauthorized', max_length=50, verbose_name='وضعیت مرخصی')),
            ],
        ),
        migrations.CreateModel(
            name='VehicleReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_name', models.CharField(max_length=100, verbose_name='نام خودرو')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('inactive_time_start', models.TimeField(blank=True, null=True, verbose_name='زمان شروع غیر فعال بودن')),
                ('inactive_time_end', models.TimeField(blank=True, null=True, verbose_name='زمان پایان غیر فعال بودن')),
            ],
        ),
        migrations.CreateModel(
            name='ShiftReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift_date', models.DateField(default=shift_manager.utils.get_shift_for_date, verbose_name='تاریخ شیفت')),
                ('supervisor_comments', models.TextField(blank=True, verbose_name='توضیحات سرشیفت برای شیفت بعد')),
                ('loading_operations', models.ManyToManyField(to='OperationsShiftReports.loadingoperation', verbose_name='عملیات بارگیری')),
                ('mining_machine_reports', models.ManyToManyField(to='OperationsShiftReports.miningmachinereport', verbose_name='گزارش\u200cهای دستگاه\u200cهای معدنی')),
                ('shift_leaves', models.ManyToManyField(to='OperationsShiftReports.shiftleave', verbose_name='مرخصی\u200cهای شیفت')),
                ('vehicle_reports', models.ManyToManyField(to='OperationsShiftReports.vehiclereport', verbose_name='گزارش\u200cهای خودرو')),
            ],
        ),
    ]
