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

logger = logging.getLogger(__name__)

class MeetingService:
    @staticmethod
    @transaction.atomic
    def create_meeting(title, date, start_time, end_time, creator, participants, manual_numbers, notify_transport_coordinator):
        print("\n=== شروع ایجاد جلسه جدید ===")
        print(f"عنوان جلسه: {title}")
        print(f"تاریخ جلسه: {date}")
        print(f"زمان شروع جلسه: {start_time}")
        print(f"زمان پایان جلسه: {end_time}")
        print(f"ایجاد کننده: {creator}")
        print(f"تعداد شرکت‌کنندگان: {len(participants)}")
        print(f"شماره‌های دستی: {manual_numbers}")
        print(f"اعلان به هماهنگ‌کننده حمل و نقل: {notify_transport_coordinator}")

        # بررسی سطح دسترسی کاربر
        if not creator.has_perm('meetings.add_meeting'):
            print("خطا: کاربر مجاز به ایجاد جلسه نیست")
            raise PermissionError("شما مجاز به ایجاد جلسه نیستید")

        # ایجاد جلسه
        meeting = Meeting.objects.create(
            title=title,
            date=date,
            start_time=start_time,
            end_time=end_time,
            creator=creator,
            manual_numbers=manual_numbers,
            notify_transport_coordinator=notify_transport_coordinator
        )
        meeting.participants.set(participants)
        print(f"جلسه با شناسه {meeting.id} ایجاد شد")

        # ارسال پیامک به شرکت‌کنندگان
        for participant in participants:
            if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                print(f"ارسال پیامک به شرکت‌کننده {participant.userprofile.mobile}")
                send_meeting_created_sms(
                    participant.userprofile.mobile,
                    meeting.id,
                    meeting.title,
                    meeting.date,
                    meeting.start_time
                )

        # ارسال پیامک به هماهنگ‌کنندگان حمل و نقل
        if notify_transport_coordinator:
            coordinators = MeetingService.get_transport_coordinators()
            for coordinator in coordinators:
                if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                    print(f"ارسال پیامک به هماهنگ‌کننده حمل و نقل {coordinator.userprofile.mobile}")
                    send_meeting_created_sms(
                        coordinator.userprofile.mobile,
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )

        # ارسال پیامک به شماره‌های دستی
        if manual_numbers:
            numbers = manual_numbers.split('\n')
            for number in numbers:
                if number.strip():
                    print(f"ارسال پیامک به شماره دستی {number.strip()}")
                    send_meeting_created_sms(
                        number.strip(),
                        meeting.id,
                        meeting.title,
                        meeting.date,
                        meeting.start_time
                    )

        # زمان‌بندی ارسال پیامک یادآوری
        print("\n=== زمان‌بندی پیامک‌های یادآوری ===")
        try:
            # تبدیل تاریخ شمسی به میلادی
            jalali_date = jdatetime.date.fromisoformat(str(date))
            gregorian_date = jalali_date.togregorian()
            
            # تنظیم زمان یادآوری روز قبل
            day_before = gregorian_date - timedelta(days=1)
            print(f"یادآوری روز قبل (میلادی): {day_before}")
            from .tasks import send_sms_reminder
            send_sms_reminder.apply_async(
                args=[meeting.id],
                eta=timezone.make_aware(timezone.datetime.combine(day_before, time(18, 0)))
            )

            # تنظیم زمان یادآوری روز جلسه
            day_of_meeting = gregorian_date
            print(f"یادآوری روز جلسه (میلادی): {day_of_meeting}")
            send_sms_reminder.apply_async(
                args=[meeting.id],
                eta=timezone.make_aware(timezone.datetime.combine(day_of_meeting, time(7, 0)))
            )
        except Exception as e:
            print(f"خطا در زمان‌بندی پیامک‌های یادآوری: {str(e)}")
            logger.error(f"خطا در زمان‌بندی پیامک‌های یادآوری: {str(e)}")

        # ارسال نوتیفیکیشن به صورت async
        from .tasks import send_notifications_async
        send_notifications_async.delay(meeting.id)

        print("\n=== پایان ایجاد جلسه ===")
        return meeting

    @staticmethod
    def get_transport_coordinators():
        try:
            coordinator_group = Group.objects.get(name='transport_coordinator')
            coordinators = coordinator_group.user_set.all()
            print(f"\n=== دریافت لیست هماهنگ‌کنندگان حمل و نقل ===")
            print(f"تعداد هماهنگ‌کنندگان: {len(coordinators)}")
            for coordinator in coordinators:
                print(f"هماهنگ‌کننده: {coordinator.get_full_name()}")
                if hasattr(coordinator, 'userprofile'):
                    print(f"شماره موبایل: {coordinator.userprofile.mobile}")
            return coordinators
        except Group.DoesNotExist:
            print("خطا: گروه transport_coordinator یافت نشد")
            return []
        except Exception as e:
            print(f"خطا در دریافت هماهنگ‌کنندگان: {str(e)}")
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
            if hasattr(participant, 'userprofile') and participant.userprofile.mobile:
                send_cancellation_sms.delay(meeting.id, participant.id)

        # ارسال پیامک به هماهنگ‌کننده حمل و نقل
        if meeting.notify_transport_coordinator:
            coordinators = MeetingService.get_transport_coordinators()
            for coordinator in coordinators:
                if hasattr(coordinator, 'userprofile') and coordinator.userprofile.mobile:
                    send_cancellation_sms.delay(meeting.id, coordinator.id)

        return meeting 