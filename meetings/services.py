from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta, time
from .models import Meeting
from dashboard.models import Notification
from django.db import transaction
from .sms_utils import send_meeting_created_sms
import logging
import jdatetime
from .tasks import send_sms_reminder, send_notifications_async, send_meeting_created_sms_async # اضافه کردن تسک پیامک ایجاد

logger = logging.getLogger(__name__)

class MeetingService:
    @staticmethod
    @transaction.atomic
    def create_meeting(title, date, start_time, end_time, creator, participants, manual_numbers, notify_transport_coordinator, location=None, description=None): # اضافه کردن location و description
        logger.info("Starting create_meeting...")
        try:
            if not creator.has_perm('meetings.add_meeting'):
                logger.warning(f"User {creator.username} does not have permission to create meetings.")
                raise PermissionError("شما مجاز به ایجاد جلسه نیستید")

            meeting = Meeting.objects.create(
                title=title,
                date=date,
                start_time=start_time,
                end_time=end_time,
                creator=creator,
                manual_numbers=manual_numbers,
                notify_transport_coordinator=notify_transport_coordinator,
                location=location, # اضافه شد
                description=description # اضافه شد
            )
            logger.info(f"Meeting object created in DB (pre-commit): ID {meeting.id}")
            meeting.participants.set(participants)
            logger.info("Participants set (pre-commit)")

            # --- حذف ارسال پیامک مستقیم از اینجا ---
            # for participant in participants:
            #    if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
            #        logger.debug(f"Direct SMS to participant {participant.userprofile.mobile}") # تغییر به debug
            #        send_meeting_created_sms(...) # حذف شود
            # if notify_transport_coordinator:
            #    coordinators = MeetingService.get_transport_coordinators()
            #    for coordinator in coordinators:
            #        if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
            #            logger.debug(f"Direct SMS to coordinator {coordinator.userprofile.mobile}") # تغییر به debug
            #            send_meeting_created_sms(...) # حذف شود
            # if manual_numbers:
            #    numbers = manual_numbers.split('\n')
            #    for number in numbers:
            #        if number.strip():
            #            logger.debug(f"Direct SMS to manual number {number.strip()}") # تغییر به debug
            #            send_meeting_created_sms(...) # حذف شود
            # logger.info("Direct SMS sending attempts completed.")

            # --- فراخوانی تسک آسنکرون برای ارسال پیامک ایجاد ---
            send_meeting_created_sms_async.delay(meeting.id)
            logger.info(f"Called send_meeting_created_sms_async task for meeting {meeting.id}")

            # --- زمان‌بندی تسک‌های یادآوری (بدون تغییر) ---
            logger.info("Attempting to schedule reminder Celery tasks.")
            try:
                # ... (کد زمان بندی send_sms_reminder با eta) ...
                 # تبدیل تاریخ شمسی به میلادی
                jalali_date = jdatetime.date.fromisoformat(str(date))
                gregorian_date = jalali_date.togregorian()

                # تنظیم زمان یادآوری روز قبل
                day_before = gregorian_date - timedelta(days=1)
                reminder_time_before = timezone.make_aware(timezone.datetime.combine(day_before, time(18, 0)))
                send_sms_reminder.apply_async(args=[meeting.id], eta=reminder_time_before)
                logger.info(f"Scheduled day_before reminder for meeting {meeting.id} at {reminder_time_before}")

                # تنظیم زمان یادآوری روز جلسه
                day_of_meeting = gregorian_date
                reminder_time_day_of = timezone.make_aware(timezone.datetime.combine(day_of_meeting, time(7, 0)))
                send_sms_reminder.apply_async(args=[meeting.id], eta=reminder_time_day_of)
                logger.info(f"Scheduled day_of_meeting reminder for meeting {meeting.id} at {reminder_time_day_of}")

            except Exception as celery_err:
                logger.error(f"!!! Celery reminder scheduling failed: {celery_err}", exc_info=True)
                raise # Rollback transaction

            # --- ارسال نوتیفیکیشن دیتابیس (بدون تغییر) ---
            MeetingService.send_notifications_to_all_users(meeting) # این متد دیگر ایمیل نمیفرستد

            logger.info(f"create_meeting completed successfully for ID {meeting.id}. Committing transaction.")
            return meeting

        except Exception as e:
            logger.error(f"!!! Error during create_meeting execution: {e}", exc_info=True)
            raise