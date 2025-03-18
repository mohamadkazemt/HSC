from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import Meeting
from dashboard.models import Notification
from django.db import transaction

class MeetingService:
    @staticmethod
    @transaction.atomic
    def create_meeting(title, date, time, creator, participants, manual_numbers, notify_transport_coordinator):
        # بررسی سطح دسترسی کاربر
        if not creator.has_perm('meetings.add_meeting'):
            raise PermissionError("شما مجاز به ایجاد جلسه نیستید")

        # ایجاد جلسه
        meeting = Meeting.objects.create(
            title=title,
            date=date,
            time=time,
            creator=creator,
            manual_numbers=manual_numbers,
            notify_transport_coordinator=notify_transport_coordinator
        )
        meeting.participants.set(participants)

        # زمان‌بندی ارسال پیامک یادآوری
        day_before = date - timedelta(days=1)
        from .tasks import send_sms_reminder
        send_sms_reminder.apply_async(
            args=[meeting.id],
            eta=timezone.make_aware(timezone.datetime.combine(day_before, timezone.time(18, 0)))
        )

        day_of_meeting = date
        send_sms_reminder.apply_async(
            args=[meeting.id],
            eta=timezone.make_aware(timezone.datetime.combine(day_of_meeting, timezone.time(7, 0)))
        )

        # ارسال نوتیفیکیشن به تمام کاربران
        MeetingService.send_notifications_to_all_users(meeting)

        return meeting

    @staticmethod
    def get_transport_coordinators():
        try:
            coordinator_group = Group.objects.get(name='transport_coordinator')
            return coordinator_group.user_set.all()
        except Group.DoesNotExist:
            return []

    @staticmethod
    def get_tomorrow_meetings():
        tomorrow = timezone.now().date() + timedelta(days=1)
        return Meeting.objects.filter(date=tomorrow)

    @staticmethod
    def get_today_meetings():
        today = timezone.now().date()
        return Meeting.objects.filter(date=today)

    @staticmethod
    def get_meetings_list(user, filters=None):
        if not user.has_perm('meetings.view_meeting'):
            raise PermissionError("شما مجاز به مشاهده جلسات نیستید")

        meetings = Meeting.objects.all()

        if filters:
            if filters.get('date'):
                meetings = meetings.filter(date=filters['date'])
            if filters.get('creator'):
                meetings = meetings.filter(creator=filters['creator'])
            if filters.get('participant'):
                meetings = meetings.filter(participants=filters['participant'])

        return meetings

    @staticmethod
    def send_meeting_reminders():
        # ارسال یادآوری برای جلسات فردا
        tomorrow_meetings = MeetingService.get_tomorrow_meetings()
        for meeting in tomorrow_meetings:
            from .tasks import send_sms_reminder
            send_sms_reminder.delay(meeting.id)

        # ارسال یادآوری برای جلسات امروز
        today_meetings = MeetingService.get_today_meetings()
        for meeting in today_meetings:
            from .tasks import send_sms_reminder
            send_sms_reminder.delay(meeting.id)

    @staticmethod
    @transaction.atomic
    def send_notifications_to_all_users(meeting):
        users = User.objects.all()
        notifications = []
        for user in users:
            notifications.append(
                Notification(
                    user=user,
                    message=f'جلسه جدید: {meeting.title}',
                    url=f'/meetings/{meeting.id}/',
                    meeting=meeting
                )
            )
        Notification.objects.bulk_create(notifications)
        
        # ارسال نوتیفیکیشن‌ها به صورت async
        from .tasks import send_notification
        for user in users:
            send_notification.delay(user.id, meeting.id)

        # ارسال نوتیفیکیشن‌ها به صورت async
        from .tasks import send_notification
        for user in users:
            send_notification.delay(user.id, meeting.id)

    @staticmethod
    @transaction.atomic
    def cancel_meeting(meeting_id, user, reason):
        meeting = Meeting.objects.get(id=meeting_id)
        
        # بررسی دسترسی کاربر
        if not user.has_perm('meetings.change_meeting'):
            raise PermissionError("شما مجاز به لغو جلسه نیستید")

        # به‌روزرسانی وضعیت جلسه
        meeting.status = 'cancelled'
        meeting.cancellation_reason = reason
        meeting.save()

        # ارسال نوتیفیکیشن به شرکت‌کنندگان
        notifications = []
        for participant in meeting.participants.all():
            notifications.append(
                Notification(
                    user=participant,
                    message=f'جلسه {meeting.title} لغو شد. دلیل: {reason}',
                    url=f'/meetings/{meeting.id}/',
                    meeting=meeting
                )
            )

        # ارسال نوتیفیکیشن به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            coordinators = MeetingService.get_transport_coordinators()
            for coordinator in coordinators:
                notifications.append(
                    Notification(
                        user=coordinator,
                        message=f'جلسه {meeting.title} لغو شد. لطفاً برنامه حمل و نقل را به‌روزرسانی کنید.',
                        url=f'/meetings/{meeting.id}/',
                        meeting=meeting
                    )
                )

        # ایجاد نوتیفیکیشن‌ها به صورت گروهی
        Notification.objects.bulk_create(notifications)

        # ارسال پیامک به شرکت‌کنندگان
        from .tasks import send_cancellation_sms
        for participant in meeting.participants.all():
            if hasattr(participant, 'phone_number'):
                send_cancellation_sms.delay(meeting.id, participant.id)

        # ارسال پیامک به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            coordinators = MeetingService.get_transport_coordinators()
            for coordinator in coordinators:
                if hasattr(coordinator, 'phone_number'):
                    send_cancellation_sms.delay(meeting.id, coordinator.id)

        return meeting 