# -*- coding: utf-8 -*-
"""
بررسی دقیق نوتیفیکیشن‌های مرخصی
"""
from django.contrib.auth import get_user_model
from dashboard.models import Notification
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print('\n=== بررسی نوتیفیکیشن‌های مرخصی ===\n')

# کلیدواژه‌هایی که در نوتیفیکیشن‌های مرخصی استفاده می‌شوند
keywords = [
    'مرخصی',
    'جایگزین',
    'جایگزینی',
    'تأیید',
    'تایید',
    'درخواست',
]

print('جستجوی نوتیفیکیشن‌ها با کلیدواژه‌های مرخصی:\n')

for kw in keywords:
    # جستجو در عنوان
    count_title = Notification.objects.filter(title__icontains=kw).count()
    # جستجو در متن
    count_message = Notification.objects.filter(message__icontains=kw).count()
    # جستجوی ترکیبی
    count_both = Notification.objects.filter(
        title__icontains=kw
    ).filter(message__icontains=kw).count()
    
    print(f'{kw:15} -> Title: {count_title:4}, Message: {count_message:4}, Both: {count_both:4}')

print('\n' + '='*60)
print('نوتیفیکیشن‌های مرخصی در 30 روز اخیر:')
print('='*60 + '\n')

last_30_days = timezone.now() - timedelta(days=30)
leave_notifs = Notification.objects.filter(
    created_at__gte=last_30_days
).filter(
    title__icontains='مرخصی'
).order_by('-created_at')

print(f'تعداد کل: {leave_notifs.count()}\n')

if leave_notifs.exists():
    print('نمونه‌های نوتیفیکیشن‌های مرخصی:')
    print('-' * 60)
    for i, n in enumerate(leave_notifs[:10], 1):
        user = n.user
        has_rubika = False
        chat_id = 'NO'
        try:
            profile = getattr(user, 'rubika_profile', None)
            if profile and getattr(profile, 'chat_id', None):
                has_rubika = True
                chat_id = profile.chat_id[:10] + '...'
        except:
            pass
        
        print(f'{i}. [{n.notification_type}] {n.title}')
        print(f'   کاربر: {user.username} | Rubika: {chat_id}')
        print(f'   پیام: {n.message[:80]}')
        print(f'   زمان: {n.created_at.strftime("%Y-%m-%d %H:%M")}')
        print(f'   خوانده شده: {"بله" if n.is_read else "خیر"}')
        print()
else:
    print('❌ هیچ نوتیفیکیشن مرخصی در 30 روز اخیر یافت نشد!')
    print('\nبررسی نوتیفیکیشن‌های قدیمی‌تر...\n')
    
    old_leave = Notification.objects.filter(
        title__icontains='مرخصی'
    ).order_by('-created_at')[:5]
    
    if old_leave.exists():
        print(f'پنج نوتیفیکیشن قدیمی‌تر:')
        for n in old_leave:
            print(f'  - {n.title} ({n.created_at.strftime("%Y-%m-%d")})')

print('\n' + '='*60)
print('بررسی عناوین نوتیفیکیشن‌های مرخصی (Unique):')
print('='*60 + '\n')

unique_titles = Notification.objects.filter(
    title__icontains='مرخصی'
).values_list('title', flat=True).distinct()

for title in unique_titles[:20]:
    count = Notification.objects.filter(title=title).count()
    print(f'{count:4}x  {title}')

print('\n=== پایان بررسی ===\n')
