from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Meeting
from .forms import MeetingForm


class MeetingViewRegressionTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(username='creator', password='pass')
        self.participant = User.objects.create_user(username='participant', password='pass')
        self.outsider = User.objects.create_user(username='outsider', password='pass')
        self.meeting = Meeting.objects.create(
            title='Existing meeting',
            date=date(2026, 8, 10),
            start_time=time(9, 0),
            end_time=time(10, 0),
            creator=self.creator,
            manual_numbers='09120000000',
            approval_status='approved',
        )
        self.meeting.participants.add(self.participant)

    @patch('meetings.views._can_view_all_meetings', return_value=False)
    @patch('meetings.views.check_permission', return_value=True)
    def test_detail_ajax_rejects_authenticated_non_participant(
        self, _check_permission, _view_all
    ):
        self.client.force_login(self.outsider)

        response = self.client.get(
            reverse('meetings:meeting_detail_ajax', args=[self.meeting.pk])
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, '09120000000', status_code=403)

    @patch('meetings.views.check_permission', return_value=True)
    def test_detail_ajax_allows_participant(self, _check_permission):
        self.client.force_login(self.participant)

        response = self.client.get(
            reverse('meetings:meeting_detail_ajax', args=[self.meeting.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.meeting.pk)
        self.assertFalse(response.json()['can_edit'])

    @patch('meetings.views.check_permission', return_value=True)
    def test_standard_create_persists_location_and_description(self, _check_permission):
        self.creator.user_permissions.add(Permission.objects.get(codename='add_meeting'))
        self.client.force_login(self.creator)

        with self.captureOnCommitCallbacks(execute=False):
            response = self.client.post(
                reverse('meetings:meeting_create'),
                {
                    'title': 'Created from form',
                    'date': '2026-08-11',
                    'start_time': '11:00',
                    'end_time': '12:00',
                    'location': 'Conference room',
                    'description': 'Quarterly review',
                    'participants': [self.participant.pk],
                    'manual_numbers': '',
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('meetings:meeting_list'))
        created = Meeting.objects.get(title='Created from form')
        self.assertEqual(created.location, 'Conference room')
        self.assertEqual(created.description, 'Quarterly review')

    @patch('permissions.utils.check_permission', return_value={'can_edit': True})
    def test_cancel_persists_audit_fields(self, _check_permission):
        self.client.force_login(self.creator)

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            response = self.client.post(
                reverse('meetings:meeting_cancel', args=[self.meeting.pk]),
                {'cancellation_reason': 'Schedule conflict'},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('meetings:meeting_list'))
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, 'cancelled')
        self.assertEqual(self.meeting.cancellation_reason, 'Schedule conflict')
        self.assertEqual(self.meeting.cancelled_by, self.creator)
        self.assertIsNotNone(self.meeting.cancelled_at)
        self.assertEqual(len(callbacks), 1)
    @patch('rubika_bot.signals.send_rubika_message.delay')
    def test_creation_notifications_are_forwarded_to_rubika(self, mock_delay):
        from dashboard.models import Notification
        from rubika_bot.models import RubikaUser

        from .services import MeetingService

        RubikaUser.objects.create(chat_id='meeting-chat', user=self.participant)
        with self.captureOnCommitCallbacks(execute=True):
            MeetingService.send_notifications_to_all_users(self.meeting)

        self.assertTrue(
            Notification.objects.filter(user=self.participant, meeting=self.meeting).exists()
        )
        mock_delay.assert_called_once()
        self.assertEqual(mock_delay.call_args.args[0], 'meeting-chat')
    def test_calendar_is_personal_for_regular_user(self):
        private_meeting = Meeting.objects.create(
            title='Private meeting',
            date=date(2026, 8, 12),
            start_time=time(8, 0),
            end_time=time(9, 0),
            creator=self.creator,
            approval_status='approved',
        )
        private_meeting.participants.add(self.outsider)
        self.client.force_login(self.participant)

        with patch('meetings.views._can_view_all_meetings', return_value=False):
            response = self.client.get(reverse('meetings:meeting_events_json'))

        ids = {event['id'] for event in response.json()}
        self.assertIn(self.meeting.pk, ids)
        self.assertNotIn(private_meeting.pk, ids)

    def test_creator_sees_own_pending_meeting(self):
        pending = Meeting.objects.create(
            title='Pending meeting',
            date=date(2026, 8, 13),
            start_time=time(8, 0),
            end_time=time(9, 0),
            creator=self.creator,
            approval_status='pending',
        )
        self.client.force_login(self.creator)

        with patch('meetings.views._can_view_all_meetings', return_value=False):
            response = self.client.get(reverse('meetings:meeting_events_json'))

        ids = {event['id'] for event in response.json()}
        self.assertIn(pending.pk, ids)

    def test_view_all_permission_exposes_all_meetings(self):
        other = Meeting.objects.create(
            title='Other meeting',
            date=date(2026, 8, 14),
            start_time=time(8, 0),
            end_time=time(9, 0),
            creator=self.creator,
            approval_status='approved',
        )
        self.client.force_login(self.outsider)

        with patch('meetings.views._can_view_all_meetings', return_value=True):
            response = self.client.get(reverse('meetings:meeting_events_json'))

        ids = {event['id'] for event in response.json()}
        self.assertIn(other.pk, ids)
        self.assertIn(self.meeting.pk, ids)

    def test_calendar_api_filters_fullcalendar_date_range(self):
        outside = Meeting.objects.create(
            title='Outside visible range',
            date=date(2026, 8, 13),
            start_time=time(8, 0),
            end_time=time(9, 0),
            creator=self.creator,
            approval_status='approved',
        )
        outside.participants.add(self.participant)
        self.client.force_login(self.participant)

        with patch('meetings.views._can_view_all_meetings', return_value=False):
            response = self.client.get(
                reverse('meetings:meeting_events_json'),
                {'start': '2026-08-01T00:00:00+03:30', 'end': '2026-08-11T00:00:00+03:30'},
            )

        self.assertEqual(response.status_code, 200)
        ids = {event['id'] for event in response.json()}
        self.assertIn(self.meeting.pk, ids)
        self.assertNotIn(outside.pk, ids)

    def test_invalid_calendar_range_returns_400(self):
        self.client.force_login(self.participant)
        response = self.client.get(reverse('meetings:meeting_events_json'), {'start': 'invalid'})
        self.assertEqual(response.status_code, 400)
    def test_pending_creation_has_no_notifications_or_delivery_callbacks(self):
        from dashboard.models import Notification
        from .services import MeetingService

        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            pending = MeetingService.create_meeting(
                title='Needs approval',
                date=date(2026, 8, 15),
                start_time=time(8, 0),
                end_time=time(9, 0),
                creator=self.creator,
                participants=[self.participant],
                manual_numbers='',
                notify_transport_coordinator=False,
            )

        self.assertEqual(pending.approval_status, 'pending')
        self.assertFalse(Notification.objects.filter(meeting=pending).exists())
        self.assertEqual(callbacks, [])

    @patch('meetings.tasks.send_sms_reminder.apply_async')
    @patch('meetings.tasks.send_meeting_created_sms_async.delay')
    @patch('meetings.views._can_approve_meetings', return_value=True)
    def test_approval_activates_notifications_and_sms(
        self,
        _can_approve,
        mock_created_sms,
        mock_reminder,
    ):
        from dashboard.models import Notification

        self.meeting.approval_status = 'pending'
        self.meeting.save(update_fields=['approval_status'])
        self.client.force_login(self.creator)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse('meetings:meeting_approve_action', args=[self.meeting.pk])
            )

        self.meeting.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.meeting.approval_status, 'approved')
        self.assertEqual(self.meeting.approved_by, self.creator)
        self.assertTrue(Notification.objects.filter(meeting=self.meeting).exists())
        mock_created_sms.assert_called_once_with(self.meeting.pk)
    def test_form_accepts_persian_digits_jalali_date(self):
        import jdatetime

        future_date = timezone.localdate() + timedelta(days=5)
        jalali = jdatetime.date.fromgregorian(date=future_date).strftime('%Y/%m/%d')
        persian_digits = jalali.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
        form = MeetingForm(data={
            'title': 'جلسه برنامه ریزی',
            'date': persian_digits,
            'start_time': '10:00',
            'end_time': '11:00',
            'participants': [self.participant.pk],
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['date'], future_date)

    def test_form_normalizes_and_deduplicates_manual_mobile_numbers(self):
        future_date = timezone.localdate() + timedelta(days=5)
        form = MeetingForm(data={
            'title': 'جلسه شماره تماس',
            'date': future_date.isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'participants': [self.participant.pk],
            'manual_numbers': '+98 912 123 4567\n۰۹۱۲۱۲۳۴۵۶۷',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['manual_numbers'], '09121234567')

    def test_form_rejects_invalid_mobile_and_end_time(self):
        future_date = timezone.localdate() + timedelta(days=5)
        form = MeetingForm(data={
            'title': 'جلسه نامعتبر',
            'date': future_date.isoformat(),
            'start_time': '12:00',
            'end_time': '11:00',
            'participants': [self.participant.pk],
            'manual_numbers': '12345',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('manual_numbers', form.errors)
        self.assertIn('end_time', form.errors)

    def test_form_rejects_inactive_participant(self):
        self.participant.is_active = False
        self.participant.save(update_fields=['is_active'])
        future_date = timezone.localdate() + timedelta(days=5)
        form = MeetingForm(data={
            'title': 'جلسه کاربر غیرفعال',
            'date': future_date.isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'participants': [self.participant.pk],
        })

        self.assertFalse(form.is_valid())
        self.assertIn('participants', form.errors)

    @patch('meetings.views._has_named_access', return_value=True)
    def test_ajax_creation_persists_normalized_form_data(self, _access):
        future_date = timezone.localdate() + timedelta(days=5)
        self.client.force_login(self.creator)

        response = self.client.post(reverse('meetings:meeting_create_ajax'), {
            'title': '  جلسه کامل  ',
            'date': future_date.isoformat(),
            'start_time': '10:00',
            'end_time': '11:30',
            'location': 'اتاق جلسات',
            'description': 'مرور برنامه',
            'participants': [self.participant.pk],
            'manual_numbers': '0098-912-123-4567',
            'notify_transport_coordinator': 'on',
        })

        self.assertEqual(response.status_code, 200, response.content)
        meeting = Meeting.objects.get(pk=response.json()['meeting_id'])
        self.assertEqual(meeting.title, 'جلسه کامل')
        self.assertEqual(meeting.date, future_date)
        self.assertEqual(meeting.manual_numbers, '09121234567')
        self.assertEqual(meeting.location, 'اتاق جلسات')
        self.assertEqual(meeting.description, 'مرور برنامه')
        self.assertTrue(meeting.notify_transport_coordinator)
        self.assertEqual(meeting.approval_status, 'pending')
        self.assertEqual(list(meeting.participants.all()), [self.participant])
    @patch('meetings.tasks.send_meeting_reminder_sms')
    @patch('rubika_bot.signals.send_rubika_message.delay')
    def test_reminder_creates_notification_and_forwards_to_rubika(
        self, mock_rubika, _mock_sms
    ):
        from dashboard.models import Notification
        from rubika_bot.models import RubikaUser
        from .tasks import send_sms_reminder

        RubikaUser.objects.create(chat_id='reminder-chat', user=self.participant)
        with self.captureOnCommitCallbacks(execute=True):
            send_sms_reminder(self.meeting.pk)

        notification = Notification.objects.get(
            meeting=self.meeting,
            user=self.participant,
            title='یادآوری جلسه',
        )
        self.assertIn(self.meeting.title, notification.message)
        mock_rubika.assert_called_once()
        chat_id, message = mock_rubika.call_args.args
        self.assertEqual(chat_id, 'reminder-chat')
        self.assertIn('یادآوری جلسه', message)

    @patch('meetings.tasks.send_meeting_reminder_sms')
    @patch('rubika_bot.signals.send_rubika_message.delay')
    def test_cancelled_meeting_skips_all_reminders(self, mock_rubika, mock_sms):
        from dashboard.models import Notification
        from .tasks import send_sms_reminder

        self.meeting.status = 'cancelled'
        self.meeting.save(update_fields=['status'])
        send_sms_reminder(self.meeting.pk)

        self.assertFalse(
            Notification.objects.filter(meeting=self.meeting, title='یادآوری جلسه').exists()
        )
        mock_sms.assert_not_called()
        mock_rubika.assert_not_called()
    @patch('meetings.sms_utils.send_template_sms', return_value=True)
    def test_meeting_sms_sends_jalali_date_and_short_time(self, mock_send):
        from .sms_utils import MEETING_TEMPLATE, send_meeting_reminder_sms

        result = send_meeting_reminder_sms(
            '09121234567',
            self.meeting.pk,
            self.meeting.title,
            date(2026, 7, 24),
            time(9, 5),
        )

        self.assertTrue(result)
        mobile, template_id, parameters = mock_send.call_args.args
        self.assertEqual(mobile, '09121234567')
        self.assertEqual(template_id, MEETING_TEMPLATE)
        values = {item['Name']: item['Value'] for item in parameters}
        self.assertEqual(values['MEETING_DATE'], '1405/05/02')
        self.assertEqual(values['MEETING_TIME'], '09:05')

    @patch('meetings.sms_utils.send_template_sms', return_value=True)
    def test_meeting_sms_converts_gregorian_string_date(self, mock_send):
        from .sms_utils import send_meeting_created_sms

        send_meeting_created_sms(
            '09121234567', self.meeting.pk, self.meeting.title, '2026-07-24', '09:05:00'
        )

        parameters = mock_send.call_args.args[2]
        values = {item['Name']: item['Value'] for item in parameters}
        self.assertEqual(values['MEETING_DATE'], '1405/05/02')
        self.assertEqual(values['MEETING_TIME'], '09:05')
