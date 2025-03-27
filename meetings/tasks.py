# --- START OF FILE tasks.py ---

from celery import shared_task
# from django.core.mail import send_mail # حذف شد چون ایمیل ارسال نمی شود
from django.conf import settings
from .models import Meeting # Notification را اگر لازم نیست حذف کنید
from django.contrib.auth.models import User, Group # Group اضافه شد
# from .services import MeetingService # <<<--- حذف شد برای رفع وابستگی دایره ای
from .sms_utils import ( # وارد کردن توابع مورد نیاز به طور مشخص
    send_meeting_created_sms,
    send_meeting_cancelled_sms,
    send_meeting_reminder_sms
)
from celery.utils.log import get_task_logger
import time
import traceback # اضافه شد برای لاگ دقیق تر خطا

logger = get_task_logger(__name__)

# تابع کمکی برای دریافت هماهنگ کنندگان بدون وابستگی به MeetingService
def _get_transport_coordinators():
    """لیست کاربران گروه transport_coordinator را برمی‌گرداند."""
    try:
        coordinator_group = Group.objects.get(name='transport_coordinator')
        return coordinator_group.user_set.all()
    except Group.DoesNotExist:
        logger.warning("Group 'transport_coordinator' not found.")
        return User.objects.none() # برگرداندن QuerySet خالی
    except Exception as e:
        logger.error(f"Error fetching transport coordinators: {e}", exc_info=True)
        return User.objects.none()

@shared_task
def send_meeting_created_sms_async(meeting_id):
    """تسک آسنکرون برای ارسال پیامک ایجاد جلسه."""
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        logger.info(f"Starting async SMS sending for created meeting {meeting.id} ('{meeting.title}')")
        logger.debug(f"Meeting Date: {meeting.date}, Start Time: {meeting.start_time}, Notify Coordinator: {meeting.notify_transport_coordinator}")

        # ارسال به شرکت‌کنندگان
        logger.info("--- Sending SMS to Participants ---")
        participants = meeting.participants.all()
        logger.info(f"Found {participants.count()} participants.")
        for participant in participants:
            logger.debug(f"Checking participant: {participant.get_full_name()} (ID: {participant.id})")
            if hasattr(participant, 'userprofile') and participant.userprofile and participant.userprofile.mobile:
                mobile = participant.userprofile.mobile
                logger.info(f"Sending creation SMS to participant {participant.username} at {mobile}")
                send_meeting_created_sms(
                    mobile,
                    meeting.id,
                    meeting.title,
                    meeting.date,
                    meeting.start_time
                )
            else:
                logger.warning(f"Participant {participant.username} has no profile or mobile number.")

        # ارسال به شماره‌های دستی
        if meeting.manual_numbers:
            logger.info("--- Sending SMS to Manual Numbers ---")
            numbers = meeting.manual_numbers.split('\n')
            valid_manual_numbers = 0
            for number in numbers:
                num_stripped = number.strip()
                if num_stripped:
                    valid_manual_numbers += 1
                    logger.info(f"Sending creation SMS to manual number {num_stripped}")
                    send_meeting_created_sms(
                        num_stripped,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
            logger.info(f"Processed {len(numbers)} lines, found {valid_manual_numbers} valid manual numbers.")
        else:
            logger.info("No manual numbers provided.")

        # ارسال به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            logger.info("--- Sending SMS to Transport Coordinators ---")
            coordinators = _get_transport_coordinators() # <<<--- استفاده از تابع کمکی
            logger.info(f"Found {coordinators.count()} transport coordinators.")
            for coordinator in coordinators:
                logger.debug(f"Checking coordinator: {coordinator.get_full_name()} (ID: {coordinator.id})")
                if hasattr(coordinator, 'userprofile') and coordinator.userprofile and coordinator.userprofile.mobile:
                    mobile = coordinator.userprofile.mobile
                    logger.info(f"Sending creation SMS to coordinator {coordinator.username} at {mobile}")
                    send_meeting_created_sms(
                        mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
                else:
                    logger.warning(f"Coordinator {coordinator.username} has no profile or mobile number.")
        else:
            logger.info("Notify transport coordinator is False. Skipping coordinator SMS.")

        logger.info(f"Finished async SMS sending for created meeting {meeting.id}")

    except Meeting.DoesNotExist:
         logger.error(f"Meeting with ID {meeting_id} not found in send_meeting_created_sms_async task.")
    except Exception as e:
        # استفاده از exc_info=True برای لاگ کامل traceback
        logger.error(f"Error in send_meeting_created_sms_async for meeting {meeting.id}: {e}", exc_info=True)
        # print(f"خطا در ارسال پیامک‌های جلسه: {str(e)}") # لاگ جایگزین print شد
        # print(f"جزئیات خطا: {traceback.format_exc()}") # لاگ جایگزین print شد
        # raise self.retry(exc=e, countdown=60) # می‌توانید برای خطاهای موقت retry تعریف کنید

@shared_task
def send_notifications_async(meeting_id):
    """
    تسک برای عملیات آسنکرون مربوط به نوتیفیکیشن (در حال حاضر فقط لاگ می‌گیرد).
    این تسک قبلا MeetingService.send_notifications_to_all_users را صدا میزد
    که آن متد فقط Notification دیتابیس را ایجاد می‌کند و دیگر تسکی صدا نمیزند.
    """
    try:
        # فقط وجود جلسه را بررسی می‌کنیم
        meeting_exists = Meeting.objects.filter(id=meeting_id).exists()
        if meeting_exists:
            logger.info(f"send_notifications_async task executed for meeting {meeting_id}. "
                        f"Database notifications should have been created in the service layer.")
            # MeetingService.send_notifications_to_all_users(meeting) # <<<--- حذف شد
        else:
             logger.warning(f"Meeting with ID {meeting_id} not found in send_notifications_async task.")
    except Exception as e:
        logger.error(f"Error in send_notifications_async for meeting {meeting_id}: {e}", exc_info=True)
        # print(f"خطا در ارسال نوتیفیکیشن‌ها: {str(e)}") # لاگ جایگزین شد

@shared_task
def send_sms_reminder(meeting_id):
    """تسک آسنکرون برای ارسال پیامک یادآوری جلسه."""
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        logger.info(f"Starting reminder SMS sending for meeting {meeting.id} ('{meeting.title}')")
        logger.debug(f"Reminder for Date: {meeting.date}, Start Time: {meeting.start_time}")

        # ارسال به شرکت‌کنندگان
        logger.info("--- Sending Reminder SMS to Participants ---")
        participants = meeting.participants.all()
        logger.info(f"Found {participants.count()} participants.")
        for participant in participants:
             logger.debug(f"Checking participant: {participant.get_full_name()} (ID: {participant.id})")
             if hasattr(participant, 'userprofile') and participant.userprofile and participant.userprofile.mobile:
                mobile = participant.userprofile.mobile
                logger.info(f"Sending reminder SMS to participant {participant.username} at {mobile}")
                send_meeting_reminder_sms(
                    mobile,
                    meeting.id,
                    meeting.title,
                    meeting.date,
                    meeting.start_time
                )
             else:
                 logger.warning(f"Participant {participant.username} has no profile or mobile number.")

        # ارسال به شماره‌های دستی
        if meeting.manual_numbers:
            logger.info("--- Sending Reminder SMS to Manual Numbers ---")
            numbers = meeting.manual_numbers.split('\n')
            valid_manual_numbers = 0
            for number in numbers:
                 num_stripped = number.strip()
                 if num_stripped:
                    valid_manual_numbers += 1
                    logger.info(f"Sending reminder SMS to manual number {num_stripped}")
                    send_meeting_reminder_sms(
                        num_stripped,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
            logger.info(f"Processed {len(numbers)} lines, found {valid_manual_numbers} valid manual numbers.")
        else:
             logger.info("No manual numbers provided for reminder.")

        # ارسال به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            logger.info("--- Sending Reminder SMS to Transport Coordinators ---")
            coordinators = _get_transport_coordinators() # <<<--- استفاده از تابع کمکی
            logger.info(f"Found {coordinators.count()} transport coordinators.")
            for coordinator in coordinators:
                logger.debug(f"Checking coordinator: {coordinator.get_full_name()} (ID: {coordinator.id})")
                if hasattr(coordinator, 'userprofile') and coordinator.userprofile and coordinator.userprofile.mobile:
                    mobile = coordinator.userprofile.mobile
                    logger.info(f"Sending reminder SMS to coordinator {coordinator.username} at {mobile}")
                    send_meeting_reminder_sms(
                        mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )
                else:
                    logger.warning(f"Coordinator {coordinator.username} has no profile or mobile number.")
        else:
             logger.info("Notify transport coordinator is False. Skipping coordinator reminder SMS.")

        logger.info(f"Finished reminder SMS sending for meeting {meeting.id}")

    except Meeting.DoesNotExist:
         logger.error(f"Meeting with ID {meeting_id} not found in send_sms_reminder task.")
    except Exception as e:
        logger.error(f"Error in send_sms_reminder for meeting {meeting_id}: {e}", exc_info=True)
        # print(f"خطا در ارسال پیامک یادآوری: {str(e)}") # لاگ جایگزین شد

# --- کد مربوط به ارسال ایمیل که قبلا اشتباها اینجا بود حذف شد ---

@shared_task
def send_cancellation_sms(meeting_id, user_id):
    """تسک آسنکرون برای ارسال پیامک لغو به یک کاربر خاص."""
    try:
        # توجه: این تسک فقط برای یک کاربر ارسال می‌کند.
        # اگر لازم است به همه شرکت کنندگان ارسال شود، منطق باید تغییر کند.
        meeting = Meeting.objects.get(id=meeting_id)
        user = User.objects.get(id=user_id)

        # ارسال پیامک
        if hasattr(user, 'userprofile') and user.userprofile and user.userprofile.mobile:
            mobile = user.userprofile.mobile
            logger.info(f"Sending cancellation SMS to user {user.username} at {mobile} for meeting {meeting.id}")
            # اطمینان از ارسال پارامترهای صحیح به تابع پیامک لغو
            send_meeting_cancelled_sms(
                mobile,
                meeting.id,
                meeting.title,
                meeting.date, # اضافه شد
                meeting.start_time, # اضافه شد
                meeting.cancellation_reason or "دلیل ذکر نشده" # اضافه شد - با مقدار پیش فرض
            )
        else:
            logger.warning(f"User {user.username} (ID: {user_id}) has no profile or mobile for cancellation SMS for meeting {meeting.id}")

    except Meeting.DoesNotExist:
        logger.error(f"Meeting with ID {meeting_id} not found in send_cancellation_sms task.")
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found in send_cancellation_sms task.")
    except Exception as e:
        logger.error(f"Error in send_cancellation_sms for meeting {meeting.id}, user {user_id}: {e}", exc_info=True)


@shared_task
def test_task():
    """تسک ساده برای تست Celery."""
    logger.info("Starting test task")
    time.sleep(5)
    logger.info("Finished test task")
    return "Test task executed successfully"

# @shared_task # تسک ارسال ایمیل که دیگر استفاده نمی‌شود
# def send_notification(user_id, meeting_id):
#     pass
# --- END OF FILE tasks.py ---