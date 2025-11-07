# Migration برای sync کردن migration state
# این migration indexes را اضافه می‌کند (اگر وجود ندارند)

from django.db import migrations, connection


def create_indexes_forward(apps, schema_editor):
    """ایجاد indexes با توجه به نوع دیتابیس"""
    vendor = connection.vendor
    
    if vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'rubika_bot_webhooklog_created_at_idx'
                        AND tablename = 'rubika_bot_webhooklog'
                    ) THEN
                        CREATE INDEX rubika_bot_webhooklog_created_at_idx 
                        ON rubika_bot_webhooklog(created_at);
                    END IF;
                END $$;
            """)
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_indexes 
                        WHERE indexname = 'rubika_bot_webhooklog_log_type_created_at_idx'
                        AND tablename = 'rubika_bot_webhooklog'
                    ) THEN
                        CREATE INDEX rubika_bot_webhooklog_log_type_created_at_idx 
                        ON rubika_bot_webhooklog(log_type, created_at);
                    END IF;
                END $$;
            """)
    elif vendor == 'sqlite':
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS rubika_bot_webhooklog_created_at_idx ON rubika_bot_webhooklog(created_at);")
            except Exception:
                pass
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS rubika_bot_webhooklog_log_type_created_at_idx ON rubika_bot_webhooklog(log_type, created_at);")
            except Exception:
                pass


def create_indexes_reverse(apps, schema_editor):
    """حذف indexes"""
    vendor = connection.vendor
    with connection.cursor() as cursor:
        try:
            cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_created_at_idx;")
            cursor.execute("DROP INDEX IF EXISTS rubika_bot_webhooklog_log_type_created_at_idx;")
        except Exception:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('rubika_bot', '0006_webhooklog_webhooklog_rubika_bot__created_6120d9_idx_and_more'),
    ]

    operations = [
        migrations.RunPython(
            create_indexes_forward,
            reverse_code=create_indexes_reverse,
        ),
    ]

