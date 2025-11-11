"""
اسکریپت تست نمایش نوتیفیکیشن‌ها در header
"""

# راهنمای استفاده:
# python manage.py shell
# exec(open('check_notifications.py').read())

from django.contrib.auth.models import User
from dashboard.models import Notification

print("\n" + "="*60)
print("  بررسی نوتیفیکیشن‌ها")
print("="*60 + "\n")

# 1. بررسی وجود کاربران
users = User.objects.filter(is_active=True)
print(f"📊 تعداد کل کاربران فعال: {users.count()}")

if users.count() == 0:
    print("❌ هیچ کاربر فعالی وجود ندارد!")
    exit()

# 2. انتخاب اولین کاربر
test_user = users.first()
print(f"👤 کاربر تست: {test_user.username}\n")

# 3. بررسی نوتیفیکیشن‌های موجود
all_notifs = Notification.objects.filter(user=test_user)
unread_notifs = all_notifs.filter(is_read=False)
read_notifs = all_notifs.filter(is_read=True)

print(f"📬 تعداد کل نوتیفیکیشن‌ها: {all_notifs.count()}")
print(f"📭 نوتیفیکیشن‌های خوانده نشده: {unread_notifs.count()}")
print(f"✅ نوتیفیکیشن‌های خوانده شده: {read_notifs.count()}\n")

# 4. نمایش نوتیفیکیشن‌های خوانده نشده
if unread_notifs.count() > 0:
    print("📋 لیست نوتیفیکیشن‌های خوانده نشده:\n")
    for i, notif in enumerate(unread_notifs[:10], 1):
        icon = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'meeting': '📅',
        }.get(notif.notification_type, '📢')
        
        print(f"{i}. {icon} [{notif.notification_type}]")
        print(f"   عنوان: {notif.title or '(بدون عنوان)'}")
        print(f"   پیام: {notif.message[:80]}{'...' if len(notif.message) > 80 else ''}")
        print(f"   زمان: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
else:
    print("⚠️  هیچ نوتیفیکیشن خوانده نشده‌ای وجود ندارد!\n")

# 5. بررسی نوتیفیکیشن‌های مرخصی
leave_notifs = all_notifs.filter(
    title__icontains='مرخصی'
).order_by('-created_at')

print(f"🏖️  نوتیفیکیشن‌های مرخصی: {leave_notifs.count()}")

if leave_notifs.count() > 0:
    print("\n📋 لیست نوتیفیکیشن‌های مرخصی:\n")
    for i, notif in enumerate(leave_notifs[:5], 1):
        status = "❌ خوانده نشده" if not notif.is_read else "✅ خوانده شده"
        print(f"{i}. {status}")
        print(f"   عنوان: {notif.title}")
        print(f"   پیام: {notif.message[:80]}{'...' if len(notif.message) > 80 else ''}")
        print(f"   زمان: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
else:
    print("⚠️  هیچ نوتیفیکیشن مرخصی‌ای یافت نشد!\n")

# 6. ایجاد نوتیفیکیشن تستی
print("\n" + "-"*60)
create_test = input("آیا می‌خواهید یک نوتیفیکیشن تستی ایجاد کنید؟ (y/n): ")

if create_test.lower() == 'y':
    test_notif = Notification.objects.create(
        user=test_user,
        title='🧪 تست نوتیفیکیشن مرخصی',
        message='این یک نوتیفیکیشن تستی برای بررسی نمایش در header است.',
        notification_type='warning'
    )
    print(f"\n✅ نوتیفیکیشن تستی ایجاد شد (ID: {test_notif.id})")
    print("📱 حالا صفحه را refresh کنید و زنگوله را بررسی کنید.")
    
    # بررسی ارسال به ربات
    from rubika_bot.models import RubikaUser
    rubika_profile = getattr(test_user, 'rubika_profile', None)
    if rubika_profile and rubika_profile.chat_id:
        print(f"🤖 کاربر به ربات متصل است (Chat ID: {rubika_profile.chat_id})")
        print("   Signal باید trigger شود و پیام به ربات ارسال شود.")
    else:
        print("⚠️  کاربر به ربات متصل نیست!")

print("\n" + "="*60)
print("  پایان بررسی")
print("="*60 + "\n")

# راهنمای بعدی
print("💡 مراحل بعدی:")
print("   1. صفحه داشبورد را refresh کنید")
print("   2. روی زنگوله کلیک کنید")
print("   3. نوتیفیکیشن‌ها باید نمایش داده شوند")
print()
print("🐛 اگر نوتیفیکیشن‌ها نمایش داده نشدند:")
print("   1. Console مرورگر را باز کنید (F12)")
print("   2. بررسی کنید که خطایی وجود ندارد")
print("   3. بررسی کنید که Alpine.js لود شده است")
print()
