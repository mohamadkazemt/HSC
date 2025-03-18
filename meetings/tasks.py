from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Meeting, Notification
from django.contrib.auth.models import User

@shared_task
def send_sms_reminder(meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    
    # ارسال پیامک به شرکت‌کنندگان
    for participant in meeting.participants.all():
        if hasattr(participant, 'phone_number'):
            # اینجا کد ارسال پیامک قرار می‌گیرد
            pass

    # ارسال پیامک به شماره‌های دستی
    if meeting.manual_numbers:
        numbers = meeting.manual_numbers.split('\n')
        for number in numbers:
            if number.strip():
                # اینجا کد ارسال پیامک قرار می‌گیرد
                pass

    # ارسال پیامک به هماهنگ‌کننده حمل و نقل
    if meeting.notify_transport_coordinator:
        from django.contrib.auth.models import Group
        try:
            coordinator_group = Group.objects.get(name='transport_coordinator')
            coordinators = coordinator_group.user_set.all()
            for coordinator in coordinators:
                if hasattr(coordinator, 'phone_number'):
                    # اینجا کد ارسال پیامک قرار می‌گیرد
                    pass
        except Group.DoesNotExist:
            pass

@shared_task
def send_notification(user_id, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    user = meeting.participants.get(id=user_id)
    
    # ارسال ایمیل
    subject = f'یادآوری جلسه: {meeting.title}'
    message = f'''
    سلام {user.get_full_name() or user.username}،
    
    این ایمیل برای یادآوری جلسه {meeting.title} است که در تاریخ {meeting.date} ساعت {meeting.time} برگزار خواهد شد.
    
    با تشکر
    '''
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

@shared_task
def send_cancellation_sms(meeting_id, user_id):
    meeting = Meeting.objects.get(id=meeting_id)
    user = User.objects.get(id=user_id)
    
    # ارسال پیامک
    if hasattr(user, 'phone_number'):
        message = f'''
        با سلام
        جلسه {meeting.title} که قرار بود در تاریخ {meeting.date} ساعت {meeting.time} برگزار شود، لغو شده است.
        دلیل لغو: {meeting.cancellation_reason}
        '''
        # اینجا کد ارسال پیامک قرار می‌گیرد
        pass 