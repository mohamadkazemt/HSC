from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from leave_reports.models import ShiftReport
from message_center.models import ReminderLog
from message_center.peyamhub_client import normalize_phone
from message_center.services import collect_pending_reminders, send_pending_reminders


def _make_leave(requester, replacement=None, status="pending_replacement"):
    return ShiftReport.objects.create(
        user=requester, leave_type="regular", shift_type="day",
        shift_date=timezone.localdate(), work_group="A",
        status=status, replacement_person=replacement,
    )


class NormalizePhoneTests(TestCase):
    def test_various_formats(self):
        self.assertEqual(normalize_phone("09123456789"), "+989123456789")
        self.assertEqual(normalize_phone("+98 912 345 6789"), "+989123456789")
        self.assertEqual(normalize_phone("00989123456789"), "+989123456789")
        self.assertEqual(normalize_phone("9123456789"), "+989123456789")
        self.assertEqual(normalize_phone(""), "")
        self.assertEqual(normalize_phone("0211234567"), "")  # not a mobile


class CollectPendingRemindersTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user("emp", first_name="علی", last_name="رضایی")
        UserProfile.objects.create(user=self.employee, personnel_code="M1", mobile="09120000001")
        self.replacement = User.objects.create_user("repl", first_name="رضا", last_name="کریمی")
        UserProfile.objects.create(user=self.replacement, personnel_code="M2", mobile="09120000002")

    def test_pending_replacement_is_collected_with_message(self):
        _make_leave(self.employee, replacement=self.replacement)
        result = collect_pending_reminders("replacement")
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["target"], "+989120000002")
        self.assertIn("جانشین", item["message"])
        self.assertIn(self.employee.get_full_name(), item["message"])
        self.assertEqual(item["recipient"], self.replacement)
        self.assertEqual(result["missing"], [])

    def test_rejected_leaves_are_not_collected(self):
        _make_leave(self.employee, replacement=self.replacement, status="rejected")
        self.assertEqual(collect_pending_reminders()["items"], [])

    def test_replacement_without_mobile_is_reported_missing(self):
        no_mobile = User.objects.create_user("nomob", first_name="بی", last_name="موبایل")
        UserProfile.objects.create(user=no_mobile, personnel_code="M3", mobile="")
        _make_leave(self.employee, replacement=no_mobile)
        result = collect_pending_reminders("replacement")
        self.assertEqual(result["items"], [])
        self.assertEqual(len(result["missing"]), 1)

    def test_manager_role_uses_required_approver_profile(self):
        manager = User.objects.create_user("mgr", first_name="مدیر", last_name="واحد")
        manager_profile = UserProfile.objects.create(user=manager, personnel_code="M4", mobile="09120000003")
        _make_leave(self.employee, status="pending_approval")

        with patch.object(ShiftReport, "get_required_approver", return_value=manager_profile):
            result = collect_pending_reminders("manager")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["target"], "+989120000003")
        self.assertEqual(result["items"][0]["recipient"], manager)

    def test_manager_without_approver_is_missing(self):
        _make_leave(self.employee, status="pending_approval")
        with patch.object(ShiftReport, "get_required_approver", return_value=None):
            result = collect_pending_reminders("manager")
        self.assertEqual(result["items"], [])
        self.assertEqual(len(result["missing"]), 1)


class SendPendingRemindersTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user("emp2", first_name="علی", last_name="رضایی")
        UserProfile.objects.create(user=self.employee, personnel_code="S1", mobile="09120000011")
        self.replacement = User.objects.create_user("repl2", first_name="رضا", last_name="کریمی")
        UserProfile.objects.create(user=self.replacement, personnel_code="S2", mobile="09120000012")
        _make_leave(self.employee, replacement=self.replacement)
        self.admin = User.objects.create_superuser("rootx", password="x")

    @patch("message_center.services.send_message")
    def test_send_logs_success_then_dedupes(self, send_mock):
        summary = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(summary["sent"], 1)
        send_mock.assert_called_once()
        self.assertEqual(send_mock.call_args.args[0], "+989120000012")

        log = ReminderLog.objects.get()
        self.assertEqual(log.status, ReminderLog.Status.SENT)
        self.assertEqual(log.triggered_by, self.admin)

        summary2 = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(summary2["skipped_duplicate"], 1)
        self.assertEqual(summary2["sent"], 0)
        send_mock.assert_called_once()  # still once

    @patch("message_center.services.send_message", side_effect=Exception("TOO_REQUESTS"))
    def test_failure_is_logged_and_not_deduplicated(self, send_mock):
        first = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(first["failed"], 1)
        log = ReminderLog.objects.get()
        self.assertEqual(log.status, ReminderLog.Status.FAILED)
        self.assertIn("TOO_REQUESTS", log.error)

        # تلاش مجدد چون قبلی موفق نبوده، دوباره تلاش می‌کند
        send_mock.side_effect = None
        second = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(second["sent"], 1)


class LeaveRemindersPageTests(TestCase):
    def setUp(self):
        self.url = reverse("message_center:leave_reminders")
        self.staff = User.objects.create_superuser("rooty", password="x")

    def test_superuser_sees_page(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "یادآوری تأیید مرخصی")

    def test_regular_user_denied_without_grant(self):
        user = User.objects.create_user("plain", password="x")
        UserProfile.objects.create(user=user, personnel_code="P1")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_dynamic_grant_allows_access(self):
        from permissions.models import UserPermission

        user = User.objects.create_user("granted", password="x")
        UserProfile.objects.create(user=user, personnel_code="P2")
        UserPermission.objects.create(user=user, view_name="send_leave_reminders", can_view=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_permissions_ui_registry_matches_view_gate(self):
        """The grantable name shown in the permissions app must be exactly
        what the view checks, otherwise admin grants have no effect."""
        from permissions.utils import get_all_views_with_labels

        registered = {
            view["name"]
            for view in get_all_views_with_labels()
            if view.get("app_label") == "message_center"
        }
        self.assertEqual(registered, {"send_leave_reminders"})

        # شبیه‌سازی کامل مسیر ادمین: اجازه با همان نامِ UI صادر می‌شود
        from accounts.models import UserProfile as UP
        from permissions.models import UserPermission as UP2

        user = User.objects.create_user("viaui", password="x")
        UP.objects.create(user=user, personnel_code="P3")
        granted_names = [n for n in registered]  # ادمین همین‌ها را می‌بیند و تیک می‌زند
        for n in granted_names:
            UP2.objects.create(user=user, view_name=n, can_view=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_queues_celery_task(self):
        with patch("message_center.views.send_leave_reminders_task") as task_mock:
            task_mock.delay.return_value.id = "abc123"
            self.client.force_login(self.staff)
            response = self.client.post(self.url, {"role": "replacement"})
            self.assertEqual(response.status_code, 302)
            task_mock.delay.assert_called_once_with(role="replacement", actor_id=self.staff.pk)
