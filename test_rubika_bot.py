#!/usr/bin/env python
"""
اسکریپت تست و عیب‌یابی ربات روبیکا
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HSCprojects.settings')
django.setup()

from django.contrib.auth.models import User
from rubika_bot.models import RubikaUser, RubikaBotSettings
from dashboard.models import Notification
from rubika_bot.tasks import send_rubika_message


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def check_bot_settings():
    print_header("1️⃣  بررسی تنظیمات ربات")
    
    try:
        settings = RubikaBotSettings.get_solo()
        print(f"✅ تنظیمات ربات یافت شد")
        print(f"   Bot username: {settings.bot_username or 'تنظیم نشده'}")
        print(f"   Token exists: {'✅ بله' if settings.token else '❌ خیر'}")
        print(f"   Proxy enabled: {'✅ بله' if settings.proxy_enabled else '❌ خیر'}")
        
        if not settings.token:
            print("\n⚠️  هشدار: توکن ربات تنظیم نشده است!")
            return False
        
        return True
    except Exception as e:
        print(f"❌ خطا در دریافت تنظیمات: {e}")
        return False


def check_connected_users():
    print_header("2️⃣  بررسی کاربران متصل")
    
    total_rubika_users = RubikaUser.objects.count()
    connected_users = RubikaUser.objects.filter(user__isnull=False)
    
    print(f"📊 تعداد کل کاربران روبیکا: {total_rubika_users}")
    print(f"📊 تعداد کاربران متصل: {connected_users.count()}")
    
    if connected_users.count() == 0:
        print("\n⚠️  هشدار: هیچ کاربری به ربات متصل نیست!")
        print("   📝 برای اتصال کاربران:")
        print("      1. کاربر باید کد اتصال را از پنل وب دریافت کند")
        print("      2. در ربات دستور /connect [کد] را ارسال کند")
        return False
    
    print("\n👥 لیست کاربران متصل:")
    for ru in connected_users[:10]:
        print(f"   - {ru.user.username} (Chat ID: {ru.chat_id})")
    
    if connected_users.count() > 10:
        print(f"   ... و {connected_users.count() - 10} کاربر دیگر")
    
    return True


def check_celery():
    print_header("3️⃣  بررسی Celery")
    
    from celery import current_app
    
    try:
        # بررسی اینکه Celery worker در حال اجرا است
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print(f"✅ Celery worker در حال اجرا است")
            print(f"   تعداد worker ها: {len(stats)}")
            for worker_name, worker_stats in stats.items():
                print(f"   - {worker_name}")
        else:
            print("⚠️  Celery worker در حال اجرا نیست یا قابل دسترسی نیست")
            print("   💡 برای اجرای worker:")
            print("      celery -A HSCprojects worker -l info")
            return False
        
        return True
    except Exception as e:
        print(f"❌ خطا در بررسی Celery: {e}")
        return False


def test_notification():
    print_header("4️⃣  تست ارسال نوتیفیکیشن")
    
    connected_users = RubikaUser.objects.filter(user__isnull=False)
    
    if connected_users.count() == 0:
        print("⏭️  رد شد - هیچ کاربری متصل نیست")
        return False
    
    test_user = connected_users.first().user
    print(f"📤 ارسال نوتیفیکیشن تستی به: {test_user.username}")
    
    try:
        notif = Notification.objects.create(
            user=test_user,
            title='🧪 تست ربات روبیکا',
            message='این یک پیام تستی از سیستم عیب‌یابی است. اگر این پیام را دریافت کردید، یعنی سیستم به درستی کار می‌کند.',
            notification_type='info'
        )
        print(f"✅ نوتیفیکیشن ایجاد شد (ID: {notif.id})")
        print(f"   📊 Signal باید trigger شود و پیام به Celery queue اضافه شود")
        print(f"   📱 کاربر باید در چند ثانیه آینده پیام را در ربات دریافت کند")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ایجاد نوتیفیکیشن: {e}")
        return False


def test_direct_send():
    print_header("5️⃣  تست ارسال مستقیم")
    
    connected_users = RubikaUser.objects.filter(user__isnull=False)
    
    if connected_users.count() == 0:
        print("⏭️  رد شد - هیچ کاربری متصل نیست")
        return False
    
    test_rubika_user = connected_users.first()
    print(f"📤 ارسال مستقیم پیام به: {test_rubika_user.user.username}")
    print(f"   Chat ID: {test_rubika_user.chat_id}")
    
    try:
        test_message = "🧪 تست ارسال مستقیم\n\nاین پیام مستقیماً از طریق Celery task ارسال شده است."
        
        # ارسال task
        result = send_rubika_message.delay(test_rubika_user.chat_id, test_message)
        
        print(f"✅ Task به queue اضافه شد")
        print(f"   Task ID: {result.id}")
        print(f"   📊 لاگ‌های Celery را بررسی کنید:")
        print(f"      journalctl -u celery.service -f")
        
        return True
    except Exception as e:
        print(f"❌ خطا در ارسال task: {e}")
        return False


def main():
    print("\n")
    print("🔧 " + "=" * 58 + " 🔧")
    print("       اسکریپت تست و عیب‌یابی ربات روبیکا")
    print("🔧 " + "=" * 58 + " 🔧")
    
    results = []
    
    # تست 1: تنظیمات
    results.append(("تنظیمات ربات", check_bot_settings()))
    
    # تست 2: کاربران متصل
    results.append(("کاربران متصل", check_connected_users()))
    
    # تست 3: Celery
    results.append(("Celery", check_celery()))
    
    # تست 4: نوتیفیکیشن
    results.append(("تست نوتیفیکیشن", test_notification()))
    
    # تست 5: ارسال مستقیم
    results.append(("تست ارسال مستقیم", test_direct_send()))
    
    # خلاصه نتایج
    print_header("📊 خلاصه نتایج")
    
    for test_name, result in results:
        status = "✅ موفق" if result else "❌ ناموفق"
        print(f"   {status} - {test_name}")
    
    success_count = sum(1 for _, r in results if r)
    total_count = len(results)
    
    print(f"\n📈 نتیجه کلی: {success_count}/{total_count} تست موفق")
    
    if success_count == total_count:
        print("\n🎉 همه چیز به درستی کار می‌کند!")
    else:
        print("\n⚠️  برخی مشکلات وجود دارد. لطفاً خطاهای بالا را بررسی کنید.")
        print("\n📚 برای راهنمای بیشتر:")
        print("   - RUBIKA_BOT_CONNECTION_GUIDE.md")
        print("   - LEAVE_APPROVAL_VIA_RUBIKA_BOT.md")


if __name__ == '__main__':
    main()
