"""
Management command برای پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY

استفاده:
    python manage.py fix_encrypted_fields
"""

from django.core.management.base import BaseCommand
from rubika_bot.models import RubikaBotSettings
from django_cryptography.core.signing import BadSignature


class Command(BaseCommand):
    help = 'پاک کردن فیلدهای رمزگذاری‌شده که بعد از تغییر SECRET_KEY خراب شده‌اند'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY'))
        self.stdout.write(self.style.WARNING('=' * 60))

        try:
            settings_obj = RubikaBotSettings.get_solo()
            self.stdout.write(self.style.SUCCESS(f'\n✅ تنظیمات پیدا شد (ID: {settings_obj.id})'))
            
            # بررسی و پاک کردن token
            try:
                token_value = settings_obj.token
                if token_value:
                    self.stdout.write(self.style.SUCCESS(f'✅ Token قابل خواندن است: {token_value[:10]}...'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Token خالی است'))
            except BadSignature:
                self.stdout.write(self.style.WARNING('⚠️  Token خراب است (BadSignature) - در حال پاک کردن...'))
                settings_obj.token = None
                settings_obj.save(update_fields=['token'])
                self.stdout.write(self.style.SUCCESS('✅ Token پاک شد'))
            
            # بررسی و پاک کردن proxy_password
            try:
                proxy_pass = settings_obj.proxy_password
                if proxy_pass:
                    self.stdout.write(self.style.SUCCESS('✅ Proxy password قابل خواندن است'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Proxy password خالی است'))
            except BadSignature:
                self.stdout.write(self.style.WARNING('⚠️  Proxy password خراب است (BadSignature) - در حال پاک کردن...'))
                settings_obj.proxy_password = None
                settings_obj.save(update_fields=['proxy_password'])
                self.stdout.write(self.style.SUCCESS('✅ Proxy password پاک شد'))
            
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
            self.stdout.write(self.style.SUCCESS('✅ عملیات با موفقیت انجام شد!'))
            self.stdout.write(self.style.SUCCESS('=' * 60))
            self.stdout.write(self.style.SUCCESS('\n📝 حالا می‌توانید:'))
            self.stdout.write(self.style.SUCCESS('   1. به صفحه تنظیمات ربات بروید: /rubika-bot/settings/'))
            self.stdout.write(self.style.SUCCESS('   2. توکن و proxy password جدید را وارد کنید'))
            self.stdout.write(self.style.SUCCESS('   3. تنظیمات را ذخیره کنید'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ خطا: {e}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))

