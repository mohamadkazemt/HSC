# Generated migration for LeaveRequestState model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0002_proxy_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaveRequestState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step', models.CharField(default='idle', help_text='مرحله فعلی: idle, leave_type, date, shift_type, replacement, hourly_times, description, confirm', max_length=50)),
                ('data', models.JSONField(blank=True, default=dict, help_text='داده‌های جمع‌آوری شده شامل: leave_type, date, shift_type, replacement_id, start_time, end_time, description')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('rubika_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='leave_request_state', to='rubika_bot.rubikauser')),
            ],
            options={
                'verbose_name': 'وضعیت درخواست مرخصی',
                'verbose_name_plural': 'وضعیت‌های درخواست مرخصی',
                'indexes': [
                    models.Index(fields=['rubika_user', 'step'], name='rubika_bot_rubika__7e8a9f_idx'),
                ],
            },
        ),
    ]

