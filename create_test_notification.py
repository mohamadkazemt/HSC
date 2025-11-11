# -*- coding: utf-8 -*-
"""
Test script to verify notification display in header
"""
from django.contrib.auth.models import User
from dashboard.models import Notification
from django.utils import timezone

# Get user
user = User.objects.filter(username='mkt').first()
if not user:
    print("User 'mkt' not found!")
    exit()

print(f"\n=== Testing notifications for user: {user.username} ===\n")

# Create a test notification
test_notif = Notification.objects.create(
    user=user,
    title='🧪 TEST: Leave Notification',
    message='This is a test notification for leave request. Please check if it appears in the header bell icon.',
    notification_type='warning',
    is_read=False
)

print(f"✅ Created test notification (ID: {test_notif.id})")
print(f"   Title: {test_notif.title}")
print(f"   Type: {test_notif.notification_type}")
print(f"   Read: {test_notif.is_read}")
print(f"   Created: {test_notif.created_at}")

# Check unread count
unread_count = Notification.objects.filter(user=user, is_read=False).count()
print(f"\n📊 Total unread notifications: {unread_count}")

# List recent unread
print("\n📋 Recent unread notifications:")
recent_unread = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
for i, n in enumerate(recent_unread, 1):
    print(f"{i}. [{n.notification_type}] {n.title}")
    print(f"   {n.message[:60]}")

print("\n" + "="*60)
print("✅ Test notification created successfully!")
print("="*60)
print("\n📱 Next steps:")
print("1. Open browser and login as 'mkt'")
print("2. Refresh the page (Ctrl+F5 for hard refresh)")
print("3. Click the bell icon in header")
print("4. You should see the test notification at the top")
print("\n💡 If not visible:")
print("   - Check browser console for errors (F12)")
print("   - Check if Alpine.js is loaded")
print("   - Check if notification count badge appears")
print(f"   - Current count should be: {unread_count}")
