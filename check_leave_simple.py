# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from dashboard.models import Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print('\n=== Leave Notification Analysis ===\n')

# Search for leave-related keywords
last_30 = timezone.now() - timedelta(days=30)
last_7 = timezone.now() - timedelta(days=7)

# Count notifications with different keywords
keywords = {
    'leave_title': Notification.objects.filter(title__icontains='مرخصی').count(),
    'approval_title': Notification.objects.filter(title__icontains='تأیید').count(),
    'approval2_title': Notification.objects.filter(title__icontains='تایید').count(),
    'replacement_title': Notification.objects.filter(title__icontains='جایگزین').count(),
}

print('Keyword counts in title:')
for k, v in keywords.items():
    print(f'  {k}: {v}')

# Recent leave notifications (last 30 days)
recent_leave = Notification.objects.filter(
    created_at__gte=last_30,
    title__icontains='مرخصی'
)

print(f'\nLeave notifications (last 30 days): {recent_leave.count()}')

if recent_leave.count() == 0:
    print('\nNo recent leave notifications! Checking all time...')
    all_leave = Notification.objects.filter(title__icontains='مرخصی').order_by('-created_at')[:10]
    print(f'Total leave notifications: {all_leave.count()}')
    
    if all_leave.exists():
        print('\nLast 10 leave notifications:')
        for n in all_leave:
            print(f'  {n.id} | {n.user.username} | {n.title} | {n.created_at.strftime("%Y-%m-%d %H:%M")}')

# Check unique titles
print('\n=== Unique leave-related titles (last 50) ===')
unique = Notification.objects.filter(
    title__icontains='مرخصی'
).values_list('title', flat=True).distinct()[:50]

for title in unique:
    count = Notification.objects.filter(title=title).count()
    print(f'{count:4}x  {title}')

print('\n=== END ===\n')
