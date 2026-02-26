from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('BaseInfo', '0013_emergencyvehicle_has_brake_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MachineActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='تاریخ')),
                ('shift', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, verbose_name='شیفت')),
                ('operator_name', models.CharField(max_length=150, verbose_name='نام اپراتور')),
                ('start_hour', models.TimeField(blank=True, null=True, verbose_name='ساعت شروع')),
                ('end_hour', models.TimeField(blank=True, null=True, verbose_name='ساعت پایان')),
                ('ready_hours', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='ساعات آماده به کاری')),
                ('work_hours', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='ساعات کارکرد')),
                ('stop_hours', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0)], verbose_name='ساعات توقف')),
                ('stop_reason', models.CharField(blank=True, choices=[('breakdown', 'خرابی'), ('service', 'سرویس'), ('not_ready', 'بی آمادگی'), ('weather', 'جوی')], max_length=20, null=True, verbose_name='علت توقف')),
                ('breakdown_alert_sent', models.BooleanField(default=False, verbose_name='هشدار خرابی ارسال شده')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_machine_activities', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
                ('machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='machine_activities', to='BaseInfo.miningmachine', verbose_name='ماشین')),
            ],
            options={
                'verbose_name': 'فعالیت ماشین',
                'verbose_name_plural': 'فعالیت ماشین ها',
                'ordering': ['-date', 'shift', 'machine__workshop_code'],
                'indexes': [models.Index(fields=['date', 'shift'], name='mining_oper_date_970ab8_idx'), models.Index(fields=['machine', 'date'], name='mining_oper_machine_87e114_idx')],
            },
        ),
        migrations.CreateModel(
            name='LoadingHaulingReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shift', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, verbose_name='شیفت')),
                ('block_number', models.CharField(max_length=60, verbose_name='شماره بلوک')),
                ('service_count', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)], verbose_name='تعداد سرویس')),
                ('date', models.DateField(verbose_name='تاریخ')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_loading_hauling_reports', to=settings.AUTH_USER_MODEL, verbose_name='ایجاد کننده')),
                ('dumper_machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dumper_reports', to='BaseInfo.miningmachine', verbose_name='ماشین حمل کننده')),
                ('loader_machine', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loader_reports', to='BaseInfo.miningmachine', verbose_name='ماشین بارکننده')),
                ('material_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='loading_hauling_reports', to='BaseInfo.mineraltype', verbose_name='نوع ماده معدنی')),
            ],
            options={
                'verbose_name': 'گزارش بارکننده و حمل کننده',
                'verbose_name_plural': 'گزارش های بارکننده و حمل کننده',
                'ordering': ['-date', 'shift', 'loader_machine__workshop_code'],
                'indexes': [models.Index(fields=['date', 'shift'], name='mining_oper_date_f56ce2_idx'), models.Index(fields=['loader_machine', 'dumper_machine'], name='mining_oper_loader__54d07d_idx')],
            },
        ),
    ]
