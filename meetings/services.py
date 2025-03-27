# meetings/services.py
import logging
from django.db import transaction
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import timedelta, time
from .models import Meeting
from dashboard.models import Notification # اطمینان از وارد کردن Notification

logger = logging.getLogger(__name__)

class MeetingService:

    # --- متد get_transport_coordinators را هم اضافه می کنیم اگر لازم است ---
    # (اگر فقط در tasks.py استفاده می شود، نیازی نیست اینجا باشد)
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


    # --- متد ارسال نوتیفیکیشن دیتابیس ---
    @staticmethod
    # @transaction.atomic # نیازی نیست چون در create_meeting داخل تراکنش صدا زده می شود
    def send_notifications_to_all_users(meeting):
        """فقط آبجکت‌های Notification را در دیتابیس برای همه کاربران ایجاد می‌کند."""
        all_users = User.objects.all()
        notifications_to_create = []
        for user in all_users:
            notifications_to_create.append(
                Notification(
                    user=user,
                    message=f'جلسه جدید: {meeting.title}',
                    url=f'/meetings/{meeting.pk}/', # استفاده از pk
                    meeting=meeting
                )
            )
        if notifications_to_create:
             # چون این متد ممکن است خارج از تراکنش هم صدا زده شود، بهتر است bulk_create را اینجا انجام دهیم
             Notification.objects.bulk_create(notifications_to_create)
             logger.info(f"Created {len(notifications_to_create)} Notification objects in DB via send_notifications_to_all_users for meeting {meeting.pk}")
        else:
             logger.info(f"No users found to create notifications for meeting {meeting.pk}")

        # --- اطمینان از عدم فراخوانی تسک ایمیل ---
        # from .tasks import send_notification
        # for user in all_users:
        #     if user.email:
        #         send_notification.delay(user.id, meeting.id)


    # --- متد create_meeting (با تغییرات قبلی on_commit) ---
    @staticmethod
    def create_meeting(title, date, start_time, end_time, creator, participants, manual_numbers, notify_transport_coordinator, location=None, description=None):
        logger.info("Starting create_meeting...")
        meeting_instance = None # برای دسترسی به pk در لاگ خطا
        try:
            if not creator.has_perm('meetings.add_meeting'):
                logger.warning(f"User {creator.username} does not have permission to create meetings.")
                raise PermissionError("شما مجاز به ایجاد جلسه نیستید")

            with transaction.atomic():
                meeting = Meeting.objects.create(
                    title=title,
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    creator=creator,
                    manual_numbers=manual_numbers,
                    notify_transport_coordinator=notify_transport_coordinator,
                    location=location,
                    description=description
                )
                meeting_instance = meeting # ذخیره نمونه برای استفاده احتمالی در لاگ خطا
                logger.info(f"Meeting object created in DB (within transaction): ID {meeting.pk}")
                meeting.participants.set(participants)
                logger.info("Participants set (within transaction)")

                # ثبت تسک ارسال پیامک ایجاد برای اجرا *بعد* از کامیت
                def task_send_creation_sms():
                    from .tasks import send_meeting_created_sms_async
                    send_meeting_created_sms_async.delay(meeting.pk)
                    logger.info(f"Creation SMS task triggered via on_commit for meeting {meeting.pk}")
                transaction.on_commit(task_send_creation_sms)

                # ثبت تسک‌های یادآوری برای اجرا *بعد* از کامیت
                try:
                    jalali_date = jdatetime.date.fromisoformat(str(date))
                    gregorian_date = jalali_date.togregorian()
                    day_before = gregorian_date - timedelta(days=1)
                    reminder_time_before = timezone.make_aware(timezone.datetime.combine(day_before, time(18, 0)))
                    day_of_meeting = gregorian_date
                    reminder_time_day_of = timezone.make_aware(timezone.datetime.combine(day_of_meeting, time(7, 0)))

                    def task_schedule_reminders():
                        from .tasks import send_sms_reminder
                        send_sms_reminder.apply_async(args=[meeting.pk], eta=reminder_time_before)
                        logger.info(f"Scheduled day_before reminder via on_commit for meeting {meeting.pk} at {reminder_time_before}")
                        send_sms_reminder.apply_async(args=[meeting.pk], eta=reminder_time_day_of)
                        logger.info(f"Scheduled day_of_meeting reminder via on_commit for meeting {meeting.pk} at {reminder_time_day_of}")
                    transaction.on_commit(task_schedule_reminders)
                    logger.info(f"Reminder tasks registered via on_commit for meeting {meeting.pk}")

                except Exception as celery_err:
                    logger.error(f"!!! Error preparing reminder schedule data for meeting {meeting.pk}: {celery_err}", exc_info=True)
                    raise # Rollback transaction

                # ایجاد نوتیفیکیشن دیتابیس *داخل* تراکنش
                MeetingService.send_notifications_to_all_users(meeting)


            logger.info(f"create_meeting transaction committed successfully for meeting ID {meeting.pk}.")
            return meeting

        except Exception as e:
            # اگر meeting_instance ایجاد شده باشد، pk آن را لاگ می کنیم
            meeting_pk = meeting_instance.pk if meeting_instance else "N/A"
            logger.error(f"!!! Error during create_meeting (Meeting PK if created: {meeting_pk}): {e}", exc_info=True)
            # اطمینان از اینکه پیام خطا به view می رسد
            # raise # خطا را دوباره صادر کنید
            # یا اگر می خواهید پیام عمومی تری برگردانید:
            raise Exception(f"خطا در ایجاد جلسه: {e}") from e