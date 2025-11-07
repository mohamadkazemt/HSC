# Generated manually to fix duplicate table issue
# این migration فقط indexes را اضافه می‌کند چون جدول از قبل وجود دارد

from django.db import migrations, connection


def create_indexes_forward(apps, schema_editor):
    """ایجاد indexes با توجه به نوع دیتابیس"""
    vendor = connection.vendor
    
    if vendor == 'postgresql':
        # PostgreSQL syntax
        with connection.cursor() as cursor:
            # Index برای created_at
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'rubika_bot_webhooklog_rubika_bot__created_6120d9_idx'
                    ) THEN
                        CREATE INDEX rubika_bot_webhooklog_rubika_bot__created_6120d9_idx 
                        ON rubika_bot_webhooklog(created_at);
                    END IF;
                END $$;
            """)
            
            # Index برای log_type و created_at
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'rubika_bot_webhooklog_rubika_bot__log_type_created_6120d9_idx'
                    ) THEN
                        CREATE INDEX rubika_bot_webhooklog_rubika_bot__log_type_created_6120d9_idx 
                        ON rubika_bot_webhooklog(log_type, created_at);
                    END IF;
                END $$;
            """)
    elif vendor == 'sqlite':
        # SQLite syntax - استفاده از IF NOT EXISTS
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS rubika_bot_webhooklog_rubika_bot__created_6120d9_idx 
                    ON rubika_bot_webhooklog(created_at);
                """)
            except Exception:
                pass  # اگر index وجود داشت، خطا نده
            
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS rubika_bot_webhooklog_rubika_bot__log_type_created_6120d9_idx 
                    ON rubika_bot_webhooklog(log_type, created_at);
                """)
            except Exception:
                pass  # اگر index وجود داشت، خطا نده


def create_indexes_reverse(apps, schema_editor):
    """حذف indexes"""
    vendor = connection.vendor
    
    if vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_rubika_bot__created_6120d9_idx;")
            cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_rubika_bot__log_type_created_6120d9_idx;")
    elif vendor == 'sqlite':
        with connection.cursor() as cursor:
            try:
                cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_rubika_bot__created_6120d9_idx;")
            except Exception:
                pass
            try:
                cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_rubika_bot__log_type_created_6120d9_idx;")
            except Exception:
                pass


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0002_rubikabotsettings_bot_username_and_more'),
    ]

    operations = [
        # فقط indexes را اضافه می‌کنیم، نه جدول را
        # چون جدول rubika_bot_webhooklog از قبل در دیتابیس وجود دارد
        migrations.RunPython(
            create_indexes_forward,
            reverse_code=create_indexes_reverse,
        ),
    ]

