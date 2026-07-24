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
        participants = list(meeting.participants.all())
        for participant in participants:
            Notification.objects.create(
                user=participant,
                title='جلسه جدید',
                message=f'جلسه جدید: {meeting.title}',
                notification_type='meeting',
                url=f'/meetings/{meeting.pk}/',
                meeting=meeting,
            )
        if participants:
            logger.info(
                "Created %s notifications for meeting %s",
                len(participants),
                meeting.pk,
            )
        else:
            logger.info("No participants found for meeting %s", meeting.pk)


    @staticmethod
    def create_meeting(title, date, start_time, end_time, creator, participants, manual_numbers, notify_transport_coordinator, location=None, description=None):
        """Create a pending meeting without notifying participants."""
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
                description=description,
                approval_status='pending',
            )
            meeting.participants.set(participants)
        logger.info("Meeting %s created and is waiting for approval", meeting.pk)
        return meeting

    @staticmethod
    def _register_approved_delivery(meeting):
        """Register notifications, SMS, and reminders after approval."""
        MeetingService.send_notifications_to_all_users(meeting)

        def enqueue_tasks():
            try:
                from .tasks import send_meeting_created_sms_async, send_sms_reminder
                send_meeting_created_sms_async.delay(meeting.pk)
                reminder_times = (
                    timezone.make_aware(timezone.datetime.combine(meeting.date - timedelta(days=1), time(18, 0))),
                    timezone.make_aware(timezone.datetime.combine(meeting.date, time(7, 0))),
                )
                now = timezone.now()
                for eta in reminder_times:
                    if eta > now:
                        send_sms_reminder.apply_async(args=[meeting.pk], eta=eta)
            except Exception:
                logger.exception("Could not enqueue approved meeting %s deliveries", meeting.pk)

        transaction.on_commit(enqueue_tasks)

    @staticmethod
    def approve_meeting(meeting_id, approver):
        """Approve a pending meeting once and activate its deliveries."""
        with transaction.atomic():
            meeting = Meeting.objects.select_for_update().get(pk=meeting_id)
            if meeting.approval_status != 'pending':
                raise ValueError('این جلسه قبلاً بررسی شده است.')
            meeting.approval_status = 'approved'
            meeting.approved_by = approver
            meeting.approved_at = timezone.now()
            meeting.rejection_reason = ''
            meeting.save(update_fields=['approval_status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])
            MeetingService._register_approved_delivery(meeting)
        return meeting