# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from dashboard.models import Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print('\n=== Notification audit ===\n')

total = Notification.objects.count()
print(f'Total notifications: {total}')

unread = Notification.objects.filter(is_read=False).count()
print(f'Unread notifications: {unread}')

last_7_days = Notification.objects.filter(created_at__gte=timezone.now()-timedelta(days=7)).count()
print(f'Notifications in last 7 days: {last_7_days}\n')

print('Recent 100 notifications (id | user | has_rubika | title)')
recent = Notification.objects.select_related('user').order_by('-created_at')[:100]
for n in recent:
    user = n.user
    has_rubika = False
    rubika_info = 'no profile'
    try:
        profile = getattr(user, 'rubika_profile', None)
        if profile and getattr(profile, 'chat_id', None):
            has_rubika = True
            rubika_info = f'chat_id={profile.chat_id}'
    except Exception:
        rubika_info = 'profile error'

    print(f'{n.id} | {user.username} | {"YES" if has_rubika else "NO"} | {rubika_info} | {n.title or "(no title)"}')

print('\nList users with notifications but no rubika_profile (unique)')
users_no_rubika = set()
for n in recent:
    user = n.user
    profile = getattr(user, 'rubika_profile', None)
    if not profile or not getattr(profile, 'chat_id', None):
        users_no_rubika.add(user.username)

print(f'Count: {len(users_no_rubika)}')
for u in sorted(users_no_rubika)[:50]:
    print(' -', u)

print('\n=== End of audit ===\n')
