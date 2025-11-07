# Migration خالی برای sync کردن migration state
# این migration جدول را ایجاد نمی‌کند چون از قبل وجود دارد

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0007_webhooklog_webhooklog_rubika_bot__created_6120d9_idx_and_more'),
    ]

    operations = [
        # هیچ عملیاتی انجام نمی‌دهیم چون جدول از قبل وجود دارد
        # این migration فقط برای sync کردن migration state است
    ]
