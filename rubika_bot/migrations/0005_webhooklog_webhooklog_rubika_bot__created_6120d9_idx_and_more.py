# Migration خالی برای sync کردن migration state
# این migration هیچ عملیاتی انجام نمی‌دهد چون جدول از قبل وجود دارد
# Django ممکن است فکر کند باید جدول را ایجاد کند، اما ما می‌دانیم که از قبل وجود دارد

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0004_webhooklog_webhooklog_rubika_bot__created_6120d9_idx_and_more'),
    ]

    operations = [
        # هیچ عملیاتی انجام نمی‌دهیم
        # این migration فقط برای sync کردن migration state است
    ]

