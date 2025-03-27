from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Meeting, Notification
from django.contrib.auth.models import User
from .sms_utils import send_meeting_created_sms, send_meeting_cancelled_sms, send_meeting_reminder_sms
from .services import MeetingService
import logging
from celery.utils.log import get_task_logger
import time

logger = get_task_logger(__name__)

@shared_task
def send_meeting_created_sms_async(meeting_id):
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        print("\n=== شروع ارسال پیامک‌های جلسه ===")
        print(f"عنوان جلسه: {meeting.title}")
        print(f"تاریخ جلسه: {meeting.date}")
        print(f"زمان شروع: {meeting.start_time}")
        print(f"اعلان به هماهنگ‌کننده حمل و نقل: {meeting.notify_transport_coordinator}")
        
        # ارسال به شرکت‌کنندگان
        print("\n=== ارسال پیامک به شرکت‌کنندگان ===")
        for participant in meeting.participants.all():
            print(f"بررسی شرکت‌کننده: {participant.get_full_name()}")
            if hasattr(participant, 'userprofile'):
                print(f"شماره موبایل: {participant.userprofile.mobile}")
                if participant.userprofile.mobile:
                    print(f"ارسال پیامک به شماره {participant.userprofile.mobile}")
                    send_meeting_created_sms(
                        participant.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
            else:
                print(f"کاربر {participant.get_full_name()} پروفایل ندارد")

        # ارسال به شماره‌های دستی
        if meeting.manual_numbers:
            print("\n=== ارسال پیامک به شماره‌های دستی ===")
            numbers = meeting.manual_numbers.split('\n')
            for number in numbers:
                if number.strip():
                    print(f"ارسال پیامک به شماره {number.strip()}")
                    send_meeting_created_sms(
                        number.strip(),
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )

        # ارسال به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            print("\n=== ارسال پیامک به هماهنگ‌کننده حمل و نقل ===")
            coordinators = MeetingService.get_transport_coordinators()
            print(f"تعداد هماهنگ‌کنندگان: {len(coordinators)}")
            for coordinator in coordinators:
                print(f"بررسی هماهنگ‌کننده: {coordinator.get_full_name()}")
                if hasattr(coordinator, 'userprofile'):
                    print(f"شماره موبایل: {coordinator.userprofile.mobile}")
                    if coordinator.userprofile.mobile:
                        print(f"ارسال پیامک به شماره {coordinator.userprofile.mobile}")
                        send_meeting_created_sms(
                            coordinator.userprofile.mobile,
                            meeting.id,
                            meeting.title,
                            meeting.date,
                            meeting.start_time
                        )
                    else:
                        print(f"هماهنگ‌کننده {coordinator.get_full_name()} شماره موبایل ندارد")
                else:
                    print(f"کاربر {coordinator.get_full_name()} پروفایل ندارد")
        else:
            print("\nاعلان به هماهنگ‌کننده حمل و نقل غیرفعال است")
            
    except Exception as e:
        logger.error(f"خطا در ارسال پیامک‌های جلسه: {str(e)}")
        print(f"خطا در ارسال پیامک‌های جلسه: {str(e)}")
        import traceback
        print(f"جزئیات خطا: {traceback.format_exc()}")

@shared_task
def send_notifications_async(meeting_id):
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        print("\n=== ارسال نوتیفیکیشن به کاربران ===")
        MeetingService.send_notifications_to_all_users(meeting)
    except Exception as e:
        logger.error(f"خطا در ارسال نوتیفیکیشن‌ها: {str(e)}")
        print(f"خطا در ارسال نوتیفیکیشن‌ها: {str(e)}")

@shared_task
def send_sms_reminder(meeting_id):
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        from .sms_utils import send_meeting_reminder_sms
        
        # ارسال به شرکت‌کنندگان
        for participant in meeting.participants.all():
            if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                send_meeting_reminder_sms(
                    participant.userprofile.mobile,
                    meeting.id,
                    meeting.title,
                    meeting.date,
                    meeting.start_time
                )
        
        # ارسال به شماره‌های دستی
        if meeting.manual_numbers:
            numbers = meeting.manual_numbers.split('\n')
            for number in numbers:
                if number.strip():
                    send_meeting_reminder_sms(
                        number.strip(),
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
        
        # ارسال به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            coordinators = MeetingService.get_transport_coordinators()
            for coordinator in coordinators:
                if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                    send_meeting_reminder_sms(
                        coordinator.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
    except Exception as e:
        logger.error(f"خطا در ارسال پیامک یادآوری: {str(e)}")
        print(f"خطا در ارسال پیامک یادآوری: {str(e)}")


    meeting = Meeting.objects.get(id=meeting_id)
    user = meeting.participants.get(id=user_id)
    
    # ارسال ایمیل
    subject = f'یادآوری جلسه: {meeting.title}'
    message = f'''
    سلام {user.get_full_name() or user.username}،
    
    این ایمیل برای یادآوری جلسه {meeting.title} است که در تاریخ {meeting.date} ساعت {meeting.start_time} برگزار خواهد شد.
    
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
    if hasattr(user, 'userprofile') and user.userprofile.mobile:
        send_meeting_cancelled_sms(
            user.userprofile.mobile,
            meeting.id,
            meeting.title,
            meeting.cancellation_reason
        )

@shared_task
def test_task():
    logger.info("شروع تسک تست")
    time.sleep(5)  # تاخیر 5 ثانیه‌ای برای شبیه‌سازی کار
    logger.info("پایان تسک تست")
    return "تسک تست با موفقیت اجرا شد" 