from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from permissions.models import UserPermission
from .models import LeaveSettings, ShiftReport
from .registration_window import validate_approval_deadline, validate_submission_date


class RegistrationWindowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("worker", password="pass")
        self.profile = UserProfile.objects.create(user=self.user, personnel_code="L1")
        self.settings = LeaveSettings.load()

    def test_defaults_are_disabled(self):
        self.assertFalse(self.settings.registration_window_enabled)
        self.assertFalse(self.settings.approval_window_enabled)

    def test_old_and_future_dates_allowed_when_disabled(self):
        old = timezone.localdate() - timedelta(days=30)
        future = timezone.localdate() + timedelta(days=30)
        self.assertIsNone(validate_submission_date(old))
        self.assertIsNone(validate_submission_date(future))
        report = ShiftReport(user=self.user, leave_type="regular", shift_date=old, work_group="A")
        report.clean()  # must not raise

    def test_enabled_window_blocks_stale_and_far_future_dates(self):
        settings = LeaveSettings.load()
        settings.registration_window_enabled = True
        settings.save(update_fields=["registration_window_enabled"])

        stale = timezone.localdate() - timedelta(days=10)
        error = validate_submission_date(stale)
        self.assertIn("مهلت ثبت", error)
        with self.assertRaises(Exception):
            ShiftReport(user=self.user, leave_type="regular", shift_date=stale, work_group="A").clean()

        far_future = timezone.localdate() + timedelta(days=10)
        self.assertIn("حداکثر تاریخ مجاز", validate_submission_date(far_future))

        inside = timezone.localdate() + timedelta(days=2)
        self.assertIsNone(validate_submission_date(inside))

    def test_custom_limits_are_respected(self):
        settings = LeaveSettings.load()
        settings.registration_window_enabled = True
        settings.registration_max_days_after = 7
        settings.save(update_fields=["registration_window_enabled", "registration_max_days_after"])
        six_days_late = timezone.localdate() - timedelta(days=6)
        self.assertIsNone(validate_submission_date(six_days_late))
        nine_days_late = timezone.localdate() - timedelta(days=9)
        self.assertIsNotNone(validate_submission_date(nine_days_late))

    def test_approval_deadline_toggle(self):
        stale = timezone.localdate() - timedelta(days=5)
        self.assertIsNone(validate_approval_deadline(stale))
        settings = LeaveSettings.load()
        settings.approval_window_enabled = True
        settings.approval_max_days = 3
        settings.save()
        self.assertIn("مهلت تأیید", validate_approval_deadline(stale))

    def test_rejected_request_does_not_block_resubmission(self):
        rejected = ShiftReport.objects.create(
            user=self.user, leave_type="regular", shift_type="day",
            shift_date=timezone.localdate(), work_group="A", status="rejected",
        )
        self.assertEqual(rejected.status, "rejected")
        fresh = ShiftReport(user=self.user, leave_type="regular", shift_type="day",
                            shift_date=timezone.localdate(), work_group="A")
        fresh.clean()  # must not raise

    def test_pending_or_approved_still_block_duplicates(self):
        for status in ("pending_replacement", "pending_approval", "approved"):
            ShiftReport.objects.create(
                user=self.user, leave_type="regular", shift_type="day",
                shift_date=timezone.localdate(), work_group="A", status=status,
            )
            with self.assertRaises(Exception):
                ShiftReport(user=self.user, leave_type="regular", shift_type="day",
                            shift_date=timezone.localdate(), work_group="A").clean()
            ShiftReport.objects.filter(status=status).delete()


class RegistrationWindowSettingsPageTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("root", password="x")
        self.url = reverse("leave_reports:registration_window_settings")

    def test_superuser_sees_settings_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تنظیمات مهلت ثبت و تأیید")
        # سوییچ‌ها و فیلدهای وابسته رندر شده‌اند
        self.assertContains(response, 'name="registration_window_enabled"')
        self.assertContains(response, 'name="approval_window_enabled"')
        self.assertContains(response, "switch-track")
        # تاریخ آخرین تغییر به شمسی نمایش داده می‌شود
        self.assertNotContains(response, "updated_at|date")

    def test_regular_user_without_grant_is_denied(self):
        user = User.objects.create_user("plain", password="x")
        UserProfile.objects.create(user=user, personnel_code="L2")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_dynamic_grant_allows_access_and_save(self):
        user = User.objects.create_user("granted", password="x")
        UserProfile.objects.create(user=user, personnel_code="L3")
        UserPermission.objects.create(user=user, view_name="leave_settings", can_view=True, can_edit=True)
        self.client.force_login(user)
        response = self.client.post(self.url, {
            "registration_window_enabled": "on",
            "registration_max_days_after": "5",
            "registration_max_days_future": "4",
            "approval_max_days": "3",
        })
        self.assertEqual(response.status_code, 302)
        settings = LeaveSettings.load()
        self.assertTrue(settings.registration_window_enabled)
        self.assertEqual(settings.registration_max_days_after, 5)
        self.assertFalse(settings.approval_window_enabled)  # unchecked box stays off

    def test_permissions_ui_registry_matches_view_gate(self):
        """نامی که در UI پرمیشن نمایش داده می‌شود باید همان باشد که ویو چک می‌کند."""
        from permissions.utils import get_all_views_with_labels

        registered = {
            view["name"]
            for view in get_all_views_with_labels()
            if view.get("app_label") == "leave_reports"
        }
        self.assertIn("leave_settings", registered)

        # شبیه‌سازی مسیر ادمین: کاربر عادی با اجازه‌ای که از UI صادر شده
        user = User.objects.create_user("viaui", password="x")
        UserProfile.objects.create(user=user, personnel_code="L4")
        UserPermission.objects.create(user=user, view_name="leave_settings", can_view=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
