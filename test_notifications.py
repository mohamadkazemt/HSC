# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from dashboard.models import Notification

print("\n" + "="*60)
print("  Check Notifications")
print("="*60 + "\n")

# 1. Check users
users = User.objects.filter(is_active=True)
print(f"Total active users: {users.count()}")

if users.count() == 0:
    print("No active users found!")
    exit()

# 2. Select first user
test_user = users.first()
print(f"Test user: {test_user.username}\n")

# 3. Check notifications
all_notifs = Notification.objects.filter(user=test_user)
unread_notifs = all_notifs.filter(is_read=False)
read_notifs = all_notifs.filter(is_read=True)

print(f"Total notifications: {all_notifs.count()}")
print(f"Unread notifications: {unread_notifs.count()}")
print(f"Read notifications: {read_notifs.count()}\n")

# 4. Show unread notifications
if unread_notifs.count() > 0:
    print("Unread notifications:\n")
    for i, notif in enumerate(unread_notifs[:10], 1):
        print(f"{i}. [{notif.notification_type}]")
        print(f"   Title: {notif.title or '(no title)'}")
        print(f"   Message: {notif.message[:80]}{'...' if len(notif.message) > 80 else ''}")
        print(f"   Time: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
else:
    print("No unread notifications!\n")

# 5. Check leave notifications
leave_notifs = all_notifs.filter(
    title__icontains='مرخصی'
).order_by('-created_at')

print(f"Leave notifications: {leave_notifs.count()}")

if leave_notifs.count() > 0:
    print("\nLeave notifications list:\n")
    for i, notif in enumerate(leave_notifs[:5], 1):
        status = "UNREAD" if not notif.is_read else "READ"
        print(f"{i}. {status}")
        print(f"   Title: {notif.title}")
        print(f"   Message: {notif.message[:80]}{'...' if len(notif.message) > 80 else ''}")
        print(f"   Time: {notif.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
else:
    print("No leave notifications found!\n")

# 6. Create test notification
print("\n" + "-"*60)
create = input("Create test notification? (y/n): ")

if create.lower() == 'y':
    test_notif = Notification.objects.create(
        user=test_user,
        title='TEST: Leave notification',
        message='This is a test notification to check header display.',
        notification_type='warning'
    )
    print(f"\nTest notification created (ID: {test_notif.id})")
    print("Now refresh the page and check the bell icon.")
    
    # Check Rubika connection
    from rubika_bot.models import RubikaUser
    try:
        rubika_profile = test_user.rubika_profile
        if rubika_profile and rubika_profile.chat_id:
            print(f"User connected to bot (Chat ID: {rubika_profile.chat_id})")
            print("Signal should trigger and send message to bot.")
        else:
            print("User not connected to bot!")
    except:
        print("User has no Rubika profile!")

print("\n" + "="*60)
print("  End of check")
print("="*60 + "\n")
