# meetings/services.py
import logging
from django.db import transaction
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, time
from .models import Meeting
from dashboard.models import Notification
# jdatetime import removed

logger = logging.getLogger(__name__)

class MeetingService:

    # ... (بقیه متدها: get_transport_coordinators, send_notifications_to_all_users) ...
    @staticmethod
    def get_transport_coordinators():
        """لیست کاربران گروه transport_coordinator را برمی‌گرداند."""
        try:
            coordinator_group = Group.objects.get(name='transport_coordinator')
            coordinators = coordinator_group.user_set.all()
            logger.info(f"Found {coordinators.count()} transport coordinators via MeetingService.")
            return coordinators
        except Group.DoesNotExist:
            logger.warning("Group 'transport_coordinator' not found via MeetingService.")
            return User.objects.none()
        except Exception as e:
            logger.error(f"Error fetching transport coordinators via MeetingService: {e}", exc_info=True)
            return User.objects.none()

    @staticmethod
    def send_notifications_to_all_users(meeting):
        """فقط آبجکت‌های Notification را در دیتابیس برای شرکت‌کنندگان جلسه ایجاد می‌کند."""
        participants = meeting.participants.all()
        notifications_to_create = []
        for participant in participants:
            notifications_to_create.append(
                Notification(
                    user=participant,
                    message=f'جلسه جدید: {meeting.title}',
                    url=f'/meetings/{meeting.pk}/', # استفاده از pk
                    meeting=meeting
                )
            )
        if notifications_to_create:
             Notification.objects.bulk_create(notifications_to_create)
             logger.info(f"Created {len(notifications_to_create)} Notification objects in DB via send_notifications_to_all_users for meeting {meeting.pk}")
        else:
             logger.info(f"No participants found to create notifications for meeting {meeting.pk}")


    @staticmethod
    def create_meeting(title, date, start_time, end_time, creator, participants, manual_numbers, notify_transport_coordinator, location=None, description=None):
        logger.info("Starting create_meeting...")
        meeting_instance = None
        try:
            if not creator.has_perm('meetings.add_meeting'):
                logger.warning(f"User {creator.username} does not have permission to create meetings.")
                raise PermissionError("شما مجاز به ایجاد جلسه نیستید")

            with transaction.atomic():
                meeting = Meeting.objects.create(
                    title=title,
                    date=date, # تاریخ اینجا یک تاریخ استاندارد است
                    start_time=start_time,
                    end_time=end_time,
                    creator=creator,
                    manual_numbers=manual_numbers,
                    notify_transport_coordinator=notify_transport_coordinator,
                    location=location,
                    description=description
                )
                meeting_instance = meeting
                logger.info(f"Meeting object created in DB (within transaction): ID {meeting.pk}")
                meeting.participants.set(participants)
                logger.info("Participants set (within transaction)")

                # ثبت تسک ارسال پیامک ایجاد برای اجرا *بعد* از کامیت
                def task_send_creation_sms():
                    try:
                        from .tasks import send_meeting_created_sms_async
                        from kombu.exceptions import OperationalError
                        from redis.exceptions import ConnectionError as RedisConnectionError
                        send_meeting_created_sms_async.delay(meeting.pk)
                        logger.info(f"Creation SMS task triggered via on_commit for meeting {meeting.pk}")
                    except (OperationalError, RedisConnectionError) as e:
                        logger.warning(f"Redis/Celery not available for sending creation SMS for meeting {meeting.pk}: {e}. Meeting created successfully but SMS will not be sent.")
                    except Exception as e:
                        logger.error(f"Unexpected error scheduling creation SMS task for meeting {meeting.pk}: {e}", exc_info=True)
                transaction.on_commit(task_send_creation_sms)

                # ثبت تسک‌های یادآوری برای اجرا *بعد* از کامیت
                try:
                    # تاریخ ورودی اکنون تاریخ میلادی استاندارد است
                    from datetime import date as date_type
                    if isinstance(date, str):
                         # اطمینان از فرمت و تبدیل به شیء date
                         try:
                             gregorian_date = date_type.fromisoformat(date)
                         except ValueError:
                             logger.error(f"Invalid date format '{date}' received for reminder scheduling.")
                             raise ValueError(f"فرمت تاریخ نامعتبر: {date}")
                    elif isinstance(date, date_type):
                         gregorian_date = date
                    else:
                        logger.error(f"Unexpected date type '{type(date)}' received for reminder scheduling.")
                        raise TypeError(f"نوع تاریخ نامشخص: {type(date)}")

                    day_before = gregorian_date - timedelta(days=1)
                    reminder_time_before = timezone.make_aware(timezone.datetime.combine(day_before, time(18, 0)))
                    day_of_meeting = gregorian_date
                    reminder_time_day_of = timezone.make_aware(timezone.datetime.combine(day_of_meeting, time(7, 0)))

                    def task_schedule_reminders():
                        try:
                            from .tasks import send_sms_reminder
                            from kombu.exceptions import OperationalError
                            from redis.exceptions import ConnectionError as RedisConnectionError
                            # فقط اگر جلسه لغو نشده باشد، یادآوری برنامه‌ریزی می‌شود
                            if meeting.status != 'cancelled':
                                send_sms_reminder.apply_async(args=[meeting.pk], eta=reminder_time_before)
                                logger.info(f"Scheduled day_before reminder via on_commit for meeting {meeting.pk} at {reminder_time_before}")
                                send_sms_reminder.apply_async(args=[meeting.pk], eta=reminder_time_day_of)
                                logger.info(f"Scheduled day_of_meeting reminder via on_commit for meeting {meeting.pk} at {reminder_time_day_of}")
                            else:
                                logger.info(f"Meeting {meeting.pk} is cancelled, skipping reminder scheduling")
                        except (OperationalError, RedisConnectionError) as e:
                            logger.warning(f"Redis/Celery not available for scheduling reminders for meeting {meeting.pk}: {e}. Meeting created successfully but reminders will not be scheduled.")
                        except Exception as e:
                            logger.error(f"Unexpected error scheduling reminder tasks for meeting {meeting.pk}: {e}", exc_info=True)
                    transaction.on_commit(task_schedule_reminders)
                    logger.info(f"Reminder tasks registered via on_commit for meeting {meeting.pk}")

                except Exception as celery_err:
                    # فقط خطاهای مربوط به آماده‌سازی داده‌ها (نه اتصال Redis) باعث rollback می‌شوند
                    if 'Connection refused' in str(celery_err) or '6379' in str(celery_err):
                        logger.warning(f"Redis/Celery connection error during reminder scheduling for meeting {meeting.pk}: {celery_err}. Meeting will be created but reminders won't be scheduled.")
                    else:
                        logger.error(f"!!! Error preparing reminder schedule data for meeting {meeting.pk}: {celery_err}", exc_info=True)
                        raise # Rollback transaction only for non-connection errors

                # ایجاد نوتیفیکیشن دیتابیس *داخل* تراکنش
                MeetingService.send_notifications_to_all_users(meeting)


            logger.info(f"create_meeting transaction committed successfully for meeting ID {meeting.pk}.")
            return meeting

        except Exception as e:
            meeting_pk = meeting_instance.pk if meeting_instance else "N/A"
            logger.error(f"!!! Error during create_meeting (Meeting PK if created: {meeting_pk}): {e}", exc_info=True)
            # raise Exception(f"خطا در ایجاد جلسه: {e}") from e # این خطا را به view برمی‌گرداند
            # برای نمایش خطای اصلی jdatetime به کاربر:
            raise Exception(f"خطا در ایجاد جلسه: {str(e)}") from e


