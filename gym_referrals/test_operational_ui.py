from datetime import timedelta

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserProfile
from permissions.models import UserPermission
from .models import Gym, GymOperator, Referral, ReferralUsage


class OperationalUITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("employee", first_name="علی", last_name="احمدی")
        self.other = User.objects.create_user("other", first_name="رضا", last_name="محمدی")
        self.profile = UserProfile.objects.create(user=self.user, personnel_code="10")
        self.other_profile = UserProfile.objects.create(user=self.other, personnel_code="20")
        self.gym = Gym.objects.create(name="باشگاه آزمون", code="TEST")
        today = timezone.localdate()
        common = dict(gym=self.gym, beneficiary_type=Referral.BeneficiaryType.EMPLOYEE,
                      issue_date=today, valid_from=today, valid_until=today + timedelta(days=30),
                      status=Referral.Status.ACTIVE, source=Referral.Source.WEB)
        self.own = Referral.objects.create(
            referral_number="GR-OWN", employee=self.user, beneficiary_account_id=self.profile.pk,
            employee_full_name_snapshot="علی احمدی", beneficiary_full_name_snapshot="علی احمدی", **common)
        self.foreign = Referral.objects.create(
            referral_number="GR-OTHER", employee=self.other, beneficiary_account_id=self.other_profile.pk,
            employee_full_name_snapshot="رضا محمدی", beneficiary_full_name_snapshot="رضا محمدی", **common)

    def grant(self, *codes):
        self.user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="gym_referrals", codename__in=codes))
        self.user = User.objects.get(pk=self.user.pk)

    def test_employee_detail_is_isolated(self):
        UserPermission.objects.create(user=self.user, view_name="gym_referral_history", can_view=True)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("gym_referrals:referral_detail", args=("GR-OWN",))).status_code, 200)
        self.assertEqual(self.client.get(reverse("gym_referrals:referral_detail", args=("GR-OTHER",))).status_code, 404)

    def test_management_pages_require_model_permissions(self):
        self.client.force_login(self.user)
        for name in ("referral_admin_list", "operator_list", "usage_list", "legacy_list", "reports"):
            self.assertEqual(self.client.get(reverse(f"gym_referrals:{name}")).status_code, 403)

    def test_referral_filter_and_legacy_scope(self):
        self.foreign.source = Referral.Source.PHYSICAL_LEGACY
        self.foreign.legacy_letter_no = "OLD-20"
        self.foreign.save(update_fields=("source", "legacy_letter_no"))
        self.grant("view_referral")
        self.client.force_login(self.user)
        response = self.client.get(reverse("gym_referrals:referral_admin_list"), {"q": "GR-OWN"})
        self.assertContains(response, "GR-OWN")
        self.assertNotContains(response, "GR-OTHER")
        legacy = self.client.get(reverse("gym_referrals:legacy_list"))
        self.assertContains(legacy, "OLD-20")
        self.assertNotIn(self.own, legacy.context["page_obj"].object_list)

    def test_operator_context_cannot_be_overridden_and_mapping_delete_is_safe(self):
        other_gym = Gym.objects.create(name="باشگاه دوم", code="SECOND")
        self.grant("add_gymoperator", "view_gymoperator", "delete_gymoperator")
        self.client.force_login(self.user)
        response = self.client.post(reverse("gym_referrals:gym_operator_create", args=(self.gym.pk,)), {
            "gym": other_gym.pk, "user": self.other.pk, "is_active": "on"})
        self.assertEqual(response.status_code, 302)
        mapping = GymOperator.objects.get(user=self.other)
        self.assertEqual(mapping.gym, self.gym)
        self.client.post(reverse("gym_referrals:operator_delete", args=(mapping.pk,)))
        self.assertFalse(GymOperator.objects.filter(pk=mapping.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.other.pk).exists())

    def test_usage_is_read_only_and_report_hides_finance_without_invoice_permission(self):
        ReferralUsage.objects.create(referral=self.own, gym=self.gym, redeemed_by=self.user)
        self.grant("view_referralusage", "view_referral")
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("gym_referrals:usage_list")), "GR-OWN")
        report = self.client.get(reverse("gym_referrals:reports"))
        self.assertNotContains(report, "وضعیت مالی")
