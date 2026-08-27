import hashlib
import hmac
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from leave_reports.models import ShiftReport
from message_center.models import InboundMessage, ReminderLog, WebhookConfig, generate_webhook_secret
from message_center.peyamhub_client import normalize_phone
from message_center.services import collect_pending_reminders, send_pending_reminders
from permissions.models import UserPermission


def _make_leave(requester, replacement=None, status="pending_replacement", day_offset=0):
    return ShiftReport.objects.create(
        user=requester, leave_type="regular", shift_type="day",
        shift_date=timezone.localdate() + timedelta(days=day_offset), work_group="A",
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

    def test_pending_replacement_is_collected_with_details(self):
        _make_leave(self.employee, replacement=self.replacement)
        result = collect_pending_reminders("replacement")
        self.assertEqual(len(result["items"]), 1)
        item = result["items"][0]
        self.assertEqual(item["target"], "+989120000002")
        self.assertEqual(item["recipient"], self.replacement)
        self.assertIn(self.employee.get_full_name(), item["requester_name"])
        self.assertEqual(result["missing"], [])

    def test_grouping_builds_single_combined_message(self):
        """دو درخواستِ یک جانشین → یک پیام جمع‌بندی‌شده."""
        from message_center.services import _build_message, _group_for_recipient

        _make_leave(self.employee, replacement=self.replacement)
        _make_leave(self.employee, replacement=self.replacement, day_offset=1)

        result = collect_pending_reminders("replacement")
        groups = _group_for_recipient(result["items"])
        self.assertEqual(len(groups), 1)
        text = _build_message(groups[0])
        self.assertIn("جانشین", text)
        self.assertIn("کارتابل", text)

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
        self.admin = User.objects.create_superuser("rootx", password="x")

    def _run(self, role="replacement"):
        with patch("message_center.services.time.sleep"), \
             patch("message_center.services.send_message") as send_mock:
            summary = send_pending_reminders(role=role, actor=self.admin)
        return summary, send_mock

    def test_send_logs_success_then_dedupes(self):
        _make_leave(self.employee, replacement=self.replacement)
        with patch("message_center.services.time.sleep"), \
             patch("message_center.services.send_message") as send_mock:
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

    def test_multiple_leaves_same_recipient_are_grouped_into_one_message(self):
        """جانشینِ چند درخواست فقط یک پیام جمع‌بندی‌شده می‌گیرد."""
        _make_leave(self.employee, replacement=self.replacement)
        _make_leave(self.employee, replacement=self.replacement, day_offset=1)

        summary, send_mock = self._run()
        self.assertEqual(summary["sent"], 1)          # فقط یک پیام
        self.assertEqual(send_mock.call_count, 1)
        text = send_mock.call_args.args[1]
        self.assertIn("۲ درخواست" if "۲" in text else "2 درخواست", text)
        # برای هر دو برگه لاگ جدا ثبت می‌شود
        self.assertEqual(ReminderLog.objects.filter(status="sent").count(), 2)

    @patch("message_center.services.send_message",
           side_effect=[None, Exception("روبیکا به‌طور موقت درخواست را محدود کرده است (دسترسی شما تا تاریخ 1405/06/03 03:03:02)")])
    def test_rate_limit_aborts_the_run(self, send_mock):
        other_repl = User.objects.create_user("repl3", first_name="سارا", last_name="احمدی")
        UserProfile.objects.create(user=other_repl, personnel_code="S3", mobile="09120000013")
        _make_leave(self.employee, replacement=self.replacement)
        _make_leave(self.employee, replacement=other_repl, day_offset=1)

        with patch("message_center.services.time.sleep"):
            summary = send_pending_reminders(role="replacement", actor=self.admin)

        self.assertTrue(summary["aborted_rate_limited"])
        self.assertEqual(summary["sent"], 1)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["remaining_not_sent"], 0)
        # بعد از تشخیص محدودیت، دیگر پیامی ارسال نشده
        self.assertEqual(send_mock.call_count, 2)
        statuses = list(ReminderLog.objects.values_list("status", flat=True))
        self.assertEqual(statuses.count("sent"), 1)
        self.assertEqual(statuses.count("failed"), 1)

    def test_permanent_failure_never_retried(self):
        _make_leave(self.employee, replacement=self.replacement)
        with patch("message_center.services.time.sleep"), \
             patch("message_center.services.send_message", side_effect=Exception(
                 "شماره 989120000012 در روبیکا ثبت نشده است (کاربر روبیکا نیست) و امکان ارسال به آن وجود ندارد.")):
            first = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(first["failed"], 1)
        log = ReminderLog.objects.get()
        self.assertEqual(log.status, ReminderLog.Status.FAILED_PERMANENT)

        second, send_mock2 = self._run()
        self.assertEqual(second["skipped_invalid"], 1)
        self.assertEqual(second["sent"], 0)
        self.assertFalse(send_mock2.called)
        # هیچ لاگ تکراری هم ساخته نمی‌شود
        self.assertEqual(ReminderLog.objects.count(), 1)

    def test_transient_failure_is_retryable(self):
        _make_leave(self.employee, replacement=self.replacement)
        with patch("message_center.services.time.sleep"), \
             patch("message_center.services.send_message", side_effect=[Exception("خطای شبکه"), None]):
            first = send_pending_reminders(role="replacement", actor=self.admin)
            second = send_pending_reminders(role="replacement", actor=self.admin)
        self.assertEqual(first["failed"], 1)
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
        self.assertEqual(
            registered,
            {"send_leave_reminders", "message_webhook_settings", "message_broadcast_send"},
        )

        # شبیه‌سازی کامل مسیر ادمین: اجازه با همان نامِ UI صادر می‌شود
        user = User.objects.create_user("viaui", password="x")
        UserProfile.objects.create(user=user, personnel_code="P3")
        for name in ("send_leave_reminders",):
            UserPermission.objects.create(user=user, view_name=name, can_view=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_post_queues_celery_task(self):
        with patch("message_center.views.send_leave_reminders_task") as task_mock:
            task_mock.delay.return_value.id = "abc123"
            self.client.force_login(self.staff)
            response = self.client.post(self.url, {"role": "replacement"})
            self.assertEqual(response.status_code, 302)
            task_mock.delay.assert_called_once_with(role="replacement", actor_id=self.staff.pk)


class InboundWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse("message_center:webhook_inbound")
        self.config = WebhookConfig.load()
        self.secret = self.config.secret

    def sign(self, body):
        return hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()

    def _payload(self, text="سلام، درخواست تایید شد."):
        import json

        return json.dumps({
            "event": "message",
            "account": "کاراوران",
            "phone": "+989982134558",
            "message": {
                "id": 1, "message_id": "mid-1", "chat_guid": "g0ABC",
                "author_guid": "u0XYZ", "type": "Text",
                "text": text, "received_at": "2026-08-24T10:00:00Z",
            },
        }, ensure_ascii=False).encode("utf-8")

    def test_valid_signature_stores_message(self):
        body = self._payload()
        response = self.client.post(
            self.url, data=body, content_type="application/json",
            headers={"X-Rubika-Signature": self.sign(body)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InboundMessage.objects.count(), 1)
        msg = InboundMessage.objects.get()
        self.assertEqual(msg.account_phone, "+989982134558")
        self.assertIn("تایید", msg.text)

    def test_missing_or_bad_signature_rejected(self):
        body = self._payload()
        # بدون امضا
        r1 = self.client.post(self.url, data=body, content_type="application/json")
        self.assertEqual(r1.status_code, 403)
        # امضای اشتباه
        r2 = self.client.post(
            self.url, data=body, content_type="application/json",
            headers={"X-Rubika-Signature": "0" * 64},
        )
        self.assertEqual(r2.status_code, 403)
        self.assertEqual(InboundMessage.objects.count(), 0)

    def test_inactive_webhook_returns_503(self):
        self.config.is_active = False
        self.config.save(update_fields=("is_active",))
        body = self._payload()
        response = self.client.post(
            self.url, data=body, content_type="application/json",
            headers={"X-Rubika-Signature": self.sign(body)},
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(InboundMessage.objects.count(), 0)

    def test_secret_rotation_invalidates_old_signatures(self):
        body = self._payload()
        old_sig = self.sign(body)
        self.config.secret = generate_webhook_secret()
        self.config.save(update_fields=("secret",))
        response = self.client.post(
            self.url, data=body, content_type="application/json",
            headers={"X-Rubika-Signature": old_sig},
        )
        self.assertEqual(response.status_code, 403)


class WebhookSettingsPageTests(TestCase):
    def setUp(self):
        self.url = reverse("message_center:webhook_settings")
        self.staff = User.objects.create_superuser("rootw", password="x")

    def test_superuser_sees_url_and_secret(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/message-center/webhook/inbound/")
        config = WebhookConfig.load()
        self.assertContains(response, config.secret)

    def test_regular_user_denied(self):
        user = User.objects.create_user("plain2", password="x")
        UserProfile.objects.create(user=user, personnel_code="W1")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_registry_name_matches_gate(self):
        from permissions.utils import get_all_views_with_labels

        registered = {
            v["name"] for v in get_all_views_with_labels()
            if v.get("app_label") == "message_center"
        }
        self.assertIn("message_webhook_settings", registered)
        user = User.objects.create_user("viaui2", password="x")
        UserProfile.objects.create(user=user, personnel_code="W2")
        UserPermission.objects.create(user=user, view_name="message_webhook_settings", can_view=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_regenerate_rotates_secret(self):
        self.client.force_login(self.staff)
        old = WebhookConfig.load().secret
        self.client.post(self.url, {"action": "regenerate_secret"})
        self.assertNotEqual(WebhookConfig.load().secret, old)
