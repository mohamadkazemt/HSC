"""
اسکریپت برای پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY

این اسکریپت را در Django shell اجرا کنید:
python manage.py shell
>>> exec(open('rubika_bot/fix_encrypted_fields.py').read())
"""

import os
import django

# تنظیم Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')
django.setup()

from rubika_bot.models import RubikaBotSettings
from django_cryptography.core.signing import BadSignature

print("=" * 60)
print("پاک کردن فیلدهای رمزگذاری‌شده بعد از تغییر SECRET_KEY")
print("=" * 60)

try:
    settings_obj = RubikaBotSettings.get_solo()
    print(f"\n✅ تنظیمات پیدا شد (ID: {settings_obj.id})")
    
    # بررسی و پاک کردن token
    try:
        token_value = settings_obj.token
        print(f"✅ Token قابل خواندن است: {token_value[:10] if token_value else 'None'}...")
    except BadSignature:
        print("⚠️  Token خراب است (BadSignature) - در حال پاک کردن...")
        settings_obj.token = None
        settings_obj.save(update_fields=['token'])
        print("✅ Token پاک شد")
    
    # بررسی و پاک کردن proxy_password
    try:
        proxy_pass = settings_obj.proxy_password
        print(f"✅ Proxy password قابل خواندن است: {'***' if proxy_pass else 'None'}")
    except BadSignature:
        print("⚠️  Proxy password خراب است (BadSignature) - در حال پاک کردن...")
        settings_obj.proxy_password = None
        settings_obj.save(update_fields=['proxy_password'])
        print("✅ Proxy password پاک شد")
    
    print("\n" + "=" * 60)
    print("✅ عملیات با موفقیت انجام شد!")
    print("=" * 60)
    print("\n📝 حالا می‌توانید:")
    print("   1. به صفحه تنظیمات ربات بروید: /rubika-bot/settings/")
    print("   2. توکن و proxy password جدید را وارد کنید")
    print("   3. تنظیمات را ذخیره کنید")
    
except Exception as e:
    print(f"\n❌ خطا: {e}")
    import traceback
    traceback.print_exc()

