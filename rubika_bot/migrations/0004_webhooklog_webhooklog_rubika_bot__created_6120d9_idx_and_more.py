# Migration خالی برای sync کردن migration state
# این migration هیچ عملیاتی انجام نمی‌دهد چون indexes در migration 0003 اضافه شده‌اند

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0003_webhooklog_webhooklog_rubika_bot__created_6120d9_idx_and_more'),
    ]

    operations = [
        # هیچ عملیاتی انجام نمی‌دهیم
        # این migration فقط برای sync کردن migration state است
    ]

