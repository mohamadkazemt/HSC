# -*- coding: utf-8 -*-
"""
تست signal نوتیفیکیشن‌های مرخصی
"""
from django.contrib.auth import get_user_model
from dashboard.models import Notification
from django.utils import timezone

User = get_user_model()

print('\n=== Testing Leave Notification Signal ===\n')

# Get test user
test_user = User.objects.filter(username='mkt').first()
if not test_user:
    print('ERROR: User mkt not found!')
    exit()

print(f'Test user: {test_user.username}')

# Check if user has Rubika profile
rubika_profile = getattr(test_user, 'rubika_profile', None)
if rubika_profile and rubika_profile.chat_id:
    print(f'Rubika: Connected (chat_id: {rubika_profile.chat_id})')
else:
    print('Rubika: NOT connected (notifications will be skipped by signal)')

print('\n' + '='*60)
print('Creating test notifications...')
print('='*60 + '\n')

# Test 1: Notification with approval buttons (should be skipped by signal)
test_cases = [
    {
        'title': 'درخواست جایگزینی مرخصی',
        'message': 'تست درخواست جایگزینی',
        'should_skip': True,
        'reason': 'Has approval buttons - sent via send_leave_approval_request'
    },
    {
        'title': 'درخواست تأیید مرخصی',
        'message': 'تست درخواست تأیید',
        'should_skip': True,
        'reason': 'Has approval buttons - sent via send_leave_approval_request'
    },
    {
        'title': 'تأیید نهایی مرخصی',
        'message': 'تست تأیید نهایی',
        'should_skip': False,
        'reason': 'Simple notification - should be sent via signal'
    },
    {
        'title': 'تأیید جایگزینی مرخصی',
        'message': 'تست تأیید جایگزینی',
        'should_skip': False,
        'reason': 'Simple notification - should be sent via signal'
    },
    {
        'title': 'رد جایگزینی مرخصی',
        'message': 'تست رد جایگزینی',
        'should_skip': False,
        'reason': 'Simple notification - should be sent via signal'
    },
]

created_ids = []
for i, test in enumerate(test_cases, 1):
    notif = Notification.objects.create(
        user=test_user,
        title=test['title'],
        message=test['message'],
        notification_type='info'
    )
    created_ids.append(notif.id)
    
    skip_status = '✅ SKIP' if test['should_skip'] else '📤 SEND'
    print(f'{i}. {skip_status} | ID={notif.id} | {test["title"]}')
    print(f'   Reason: {test["reason"]}')
    print()

print('='*60)
print('Check logs to see if signal processed correctly!')
print('='*60)
print('\nExpected behavior:')
print('- Notifications 1-2: Signal should SKIP (logged as "has approval buttons")')
print('- Notifications 3-5: Signal should process (if user has chat_id)')
print('                     or log "no rubika profile" (if user has no chat_id)')

print(f'\nCreated notification IDs: {created_ids}')
print('\nCleanup: Delete test notifications? (y/n)')
