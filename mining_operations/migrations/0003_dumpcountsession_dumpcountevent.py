from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import mining_operations.models


class Migration(migrations.Migration):

    dependencies = [
        ('BaseInfo', '0013_emergencyvehicle_has_brake_and_more'),
        ('mining_operations', '0002_rename_mining_oper_date_f56ce2_idx_mining_oper_date_3b458c_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DumpCountSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='تاریخ')),
                ('shift', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, verbose_name='شیفت')),
                ('block_number', models.CharField(max_length=60, verbose_name='شماره بلوک')),
                ('counter_name', models.CharField(max_length=150, verbose_name='نام کنترچی')),
                ('loader_operator_name', models.CharField(blank=True, max_length=150, verbose_name='نام راننده/بارکننده')),
                ('start_time', models.TimeField(default=mining_operations.models.current_local_time, verbose_name='ساعت شروع شیفت')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='ساعت پایان شیفت')),
                ('notes', models.CharField(blank=True, max_length=255, verbose_name='توضیحات')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_dump_count_sessions', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
            ],
            options={
                'verbose_name': 'شیفت شمارش دامپ',
                'verbose_name_plural': 'شیفت های شمارش دامپ',
                'ordering': ['-date', '-created_at'],
                'indexes': [models.Index(fields=['date', 'shift'], name='mining_oper_date_43c403_idx')],
            },
        ),
        migrations.CreateModel(
            name='DumpCountEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dumper_code', models.CharField(blank=True, max_length=50, verbose_name='کد دامپتراک')),
                ('driver_name', models.CharField(blank=True, max_length=150, verbose_name='نام راننده')),
                ('load_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='زمان ثبت سرویس')),
                ('note', models.CharField(blank=True, max_length=255, verbose_name='توضیحات')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_dump_count_events', to=settings.AUTH_USER_MODEL, verbose_name='ثبت کننده')),
                ('dumper_machine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='counted_dumps', to='BaseInfo.miningmachine', verbose_name='دامپتراک')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dump_events', to='mining_operations.dumpcountsession', verbose_name='شیفت شمارش')),
            ],
            options={
                'verbose_name': 'رکورد شمارش دامپ',
                'verbose_name_plural': 'رکوردهای شمارش دامپ',
                'ordering': ['-load_time'],
                'indexes': [models.Index(fields=['session', 'load_time'], name='mining_oper_session_4e6f58_idx')],
            },
        ),
    ]

