# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from dashboard.models import Notification

test_user = User.objects.filter(username='mkt').first()

print("\n=== Checking all notifications with 'مرخصی' ===\n")

# Different search methods
queries = [
    ("title__icontains='مرخصی'", Notification.objects.filter(user=test_user, title__icontains='مرخصی')),
    ("title__contains='مرخصی'", Notification.objects.filter(user=test_user, title__contains='مرخصی')),
    ("message__icontains='مرخصی'", Notification.objects.filter(user=test_user, message__icontains='مرخصی')),
]

for label, qs in queries:
    print(f"{label}: {qs.count()} notifications")
    if qs.count() > 0:
        for n in qs[:3]:
            print(f"  - [{n.notification_type}] {n.title}")
            print(f"    {n.message[:60]}")
        print()

print("\n=== Recent notifications (last 10) ===\n")
recent = Notification.objects.filter(user=test_user).order_by('-created_at')[:10]
for i, n in enumerate(recent, 1):
    print(f"{i}. Title: {n.title or '(no title)'}")
    print(f"   Message: {n.message[:60]}")
    print(f"   Created: {n.created_at}")
    print()
