"""
Management command برای پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY

استفاده:
    python manage.py fix_encrypted_fields
"""

from django.core.management.base import BaseCommand
from django.db import connection
from rubika_bot.models import RubikaBotSettings


class Command(BaseCommand):
    help = 'پاک کردن فیلدهای رمزگذاری‌شده که بعد از تغییر SECRET_KEY خراب شده‌اند'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY'))
        self.stdout.write(self.style.WARNING('=' * 60))

        try:
            # استفاده از raw SQL برای جلوگیری از decode کردن فیلدهای رمزگذاری‌شده
            # استفاده از quote_name برای امنیت بیشتر
            db_table = RubikaBotSettings._meta.db_table
            table_name = connection.ops.quote_name(db_table)
            
            self.stdout.write(self.style.SUCCESS(f'\n📋 جدول: {table_name}'))
            
            # بررسی وجود رکورد
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT id FROM {table_name} WHERE id = 1")
                row = cursor.fetchone()
                
                if not row:
                    self.stdout.write(self.style.WARNING('⚠️  رکورد تنظیمات یافت نشد. در حال ایجاد...'))
                    # استفاده از CURRENT_TIMESTAMP که در PostgreSQL و SQL Server کار می‌کند
                    cursor.execute(
                        f"INSERT INTO {table_name} (id, bot_username, updated_at, proxy_enabled, proxy_scheme) "
                        f"VALUES (1, NULL, CURRENT_TIMESTAMP, false, 'socks5')"
                    )
                    self.stdout.write(self.style.SUCCESS('✅ رکورد جدید ایجاد شد'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'✅ رکورد تنظیمات پیدا شد (ID: {row[0]})'))
                
                # پاک کردن فیلدهای رمزگذاری‌شده با raw SQL
                self.stdout.write(self.style.WARNING('\n🔄 در حال پاک کردن فیلدهای رمزگذاری‌شده...'))
                
                # پاک کردن token
                cursor.execute(
                    f"UPDATE {table_name} SET token = NULL WHERE id = 1"
                )
                self.stdout.write(self.style.SUCCESS('✅ Token پاک شد'))
                
                # پاک کردن proxy_password
                cursor.execute(
                    f"UPDATE {table_name} SET proxy_password = NULL WHERE id = 1"
                )
                self.stdout.write(self.style.SUCCESS('✅ Proxy password پاک شد'))
                
                # بررسی نتیجه
                cursor.execute(
                    f"SELECT id, bot_username, token, proxy_password FROM {table_name} WHERE id = 1"
                )
                result = cursor.fetchone()
                
                self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
                self.stdout.write(self.style.SUCCESS('✅ عملیات با موفقیت انجام شد!'))
                self.stdout.write(self.style.SUCCESS('=' * 60))
                self.stdout.write(self.style.SUCCESS('\n📊 وضعیت فعلی:'))
                self.stdout.write(self.style.SUCCESS(f'   ID: {result[0]}'))
                self.stdout.write(self.style.SUCCESS(f'   Bot Username: {result[1] or "خالی"}'))
                self.stdout.write(self.style.SUCCESS(f'   Token: {"NULL" if result[2] is None else "پاک شده"}'))
                self.stdout.write(self.style.SUCCESS(f'   Proxy Password: {"NULL" if result[3] is None else "پاک شده"}'))
                self.stdout.write(self.style.SUCCESS('\n📝 مراحل بعدی:'))
                self.stdout.write(self.style.SUCCESS('   1. به صفحه تنظیمات ربات بروید: /rubika-bot/settings/'))
                self.stdout.write(self.style.SUCCESS('   2. توکن و proxy password جدید را وارد کنید'))
                self.stdout.write(self.style.SUCCESS('   3. تنظیمات را ذخیره کنید'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ خطا: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

