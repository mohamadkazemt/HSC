# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from dashboard.models import Notification

test_user = User.objects.filter(username='mkt').first()

print("\n=== Recent 20 notifications ===\n")
recent = Notification.objects.filter(user=test_user).order_by('-created_at')[:20]
for i, n in enumerate(recent, 1):
    print(f"{i}. [{n.notification_type}] {n.title or '(no title)'}")
    print(f"   {n.message[:80]}")
    print(f"   {n.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    # Check if related to leave
    has_leave_keyword = any([
        'مرخصی' in (n.title or ''),
        'مرخصی' in n.message,
        'جایگزین' in (n.title or ''),
        'جایگزین' in n.message,
        'تایید' in (n.title or '') and 'درخواست' in (n.title or ''),
    ])
    
    if has_leave_keyword:
        print("   *** LEAVE-RELATED ***")
    print()

print("\n=== Searching by keywords ===")
keywords = ['درخواست', 'جایگزین', 'تایید']
for kw in keywords:
    count_title = Notification.objects.filter(user=test_user, title__icontains=kw).count()
    count_msg = Notification.objects.filter(user=test_user, message__icontains=kw).count()
    print(f"{kw}: {count_title} in title, {count_msg} in message")
