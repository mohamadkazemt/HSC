from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.staticfiles import finders
import jdatetime

from accounts.models import Dependent, UserProfile
from permissions.models import UserPermission
from .models import Gym, GymContract


class GymReferralUITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("employee", first_name="محمد", last_name="احمدی")
        self.profile = UserProfile.objects.create(user=self.user, personnel_code="100")
        self.dependent = Dependent.objects.create(
            personnel=self.profile, first_name="زهرا", last_name="احمدی",
            national_code="0012345678", relationship="همسر",
        )
        self.gym = Gym.objects.create(name="باشگاه انقلاب", code="ENG", phone="021")
        today = timezone.localdate()
        self.contract = GymContract.objects.create(
            gym=self.gym, start_date=today - timedelta(days=5), end_date=today + timedelta(days=30),
            price_per_referral=Decimal("1250000"), billing_policy=GymContract.BillingPolicy.ISSUED,
        )

    def grant(self, *codenames):
        self.user.user_permissions.add(*Permission.objects.filter(content_type__app_label="gym_referrals", codename__in=codenames))
        self.user = User.objects.get(pk=self.user.pk)

    def grant_dynamic(self, *view_names):
        for view_name in view_names:
            UserPermission.objects.create(user=self.user, view_name=view_name, can_view=True)
        self.user = User.objects.get(pk=self.user.pk)

    def test_referral_select_labels_are_rendered(self):
        self.grant_dynamic("gym_referral_create")
        self.client.force_login(self.user)
        html = self.client.get(reverse("gym_referrals:create")).content.decode()
        self.assertIn("محمد احمدی — خودم", html)
        self.assertIn("زهرا احمدی — همسر", html)
        self.assertIn("باشگاه انقلاب", html)
        self.assertIn("فرد موردنظر را انتخاب کنید", html)
        self.assertIn("باشگاه موردنظر را انتخاب کنید", html)
        self.assertNotIn("---------", html)
        self.assertIn("gym-native-select", html)
        self.assertIn(f'value="EMPLOYEE:{self.profile.pk}"', html)
        self.assertIn(f'value="DEPENDENT:{self.dependent.pk}"', html)

    def test_unauthorized_management_is_denied(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("gym_referrals:gym_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("gym_referrals:contract_list")).status_code, 403)

    def test_authorized_gym_list_create_edit_and_inactive_status(self):
        self.grant("view_gym", "add_gym", "change_gym")
        self.client.force_login(self.user)
        response = self.client.get(reverse("gym_referrals:gym_list"))
        self.assertContains(response, "باشگاه انقلاب")
        created = self.client.post(reverse("gym_referrals:gym_create"), {"name": "باشگاه آزادی", "code": "AZD", "phone": "", "address": "تهران", "accepts_male": "on", "accepts_female": "on", "is_active": "on"})
        gym = Gym.objects.get(code="AZD")
        self.assertRedirects(created, reverse("gym_referrals:gym_detail", args=(gym.pk,)))
        self.client.post(reverse("gym_referrals:gym_edit", args=(gym.pk,)), {"name": gym.name, "code": gym.code, "phone": "", "address": gym.address, "accepts_male": "on", "accepts_female": "on"})
        gym.refresh_from_db()
        self.assertFalse(gym.is_active)
        self.assertContains(self.client.get(reverse("gym_referrals:gym_list")), "غیرفعال")

    def test_authorized_contract_list_create_edit_and_validation(self):
        self.grant("view_gym", "view_gymcontract", "add_gymcontract", "change_gymcontract")
        self.client.force_login(self.user)
        response = self.client.get(reverse("gym_referrals:contract_list"))
        self.assertContains(response, "1,250,000 ریال")
        self.assertContains(response, "معرفی‌نامه‌های صادرشده")
        invalid = self.client.post(reverse("gym_referrals:contract_create"), {"gym": self.gym.pk, "start_date": "1405/05/29", "end_date": "1405/05/19", "price_per_referral": "0", "billing_policy": "ISSUED", "is_active": "on"})
        self.assertEqual(invalid.status_code, 200)
        self.assertContains(invalid, "تعرفه باید بزرگ‌تر از صفر باشد")
        self.assertContains(invalid, "تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد")
        start, end = timezone.localdate(), timezone.localdate() + timedelta(days=60)
        jstart, jend = jdatetime.date.fromgregorian(date=start).strftime("%Y/%m/%d"), jdatetime.date.fromgregorian(date=end).strftime("%Y/%m/%d")
        created = self.client.post(reverse("gym_referrals:contract_create"), {"gym": self.gym.pk, "start_date": jstart, "end_date": jend, "price_per_referral": "250000", "billing_policy": "USED", "is_active": "on"})
        new_contract = GymContract.objects.exclude(pk=self.contract.pk).get()
        self.assertRedirects(created, reverse("gym_referrals:gym_detail", args=(self.gym.pk,)))
        edited = self.client.post(reverse("gym_referrals:contract_edit", args=(new_contract.pk,)), {"gym": self.gym.pk, "start_date": jstart, "end_date": jend, "price_per_referral": "300000", "billing_policy": "USED", "is_active": "on"})
        self.assertEqual(edited.status_code, 302)
        new_contract.refresh_from_db()
        self.assertEqual(new_contract.price_per_referral, Decimal("300000"))

    def test_gym_context_contract_uses_server_gym_and_jalali_dates(self):
        other = Gym.objects.create(name="باشگاه دیگر", code="OTHER")
        self.grant("view_gym", "add_gymcontract")
        self.client.force_login(self.user)
        url = reverse("gym_referrals:gym_contract_create", args=(self.gym.pk,))
        page = self.client.get(url)
        self.assertContains(page, "قرارداد جدید برای")
        self.assertContains(page, self.gym.name)
        self.assertNotContains(page, 'name="gym"')
        self.assertNotContains(page, 'type="date"')
        response = self.client.post(url, {"gym": other.pk, "start_date": "۱۴۰۵/۰۱/۱۵", "end_date": "۱۴۰۵/۱۲/۲۹", "price_per_referral": "۱,۵۰۰,۰۰۰", "billing_policy": "ISSUED", "is_active": "on"})
        created = GymContract.objects.exclude(pk=self.contract.pk).get()
        self.assertEqual(created.gym, self.gym)
        self.assertEqual(created.start_date, jdatetime.date(1405, 1, 15).togregorian())
        self.assertEqual(created.price_per_referral, Decimal("1500000"))
        self.assertRedirects(response, reverse("gym_referrals:gym_detail", args=(self.gym.pk,)))
        self.assertContains(self.client.get(reverse("gym_referrals:gym_detail", args=(self.gym.pk,))), "1405/01/15")

    def test_invalid_jalali_date_is_rejected(self):
        self.grant("add_gymcontract")
        self.client.force_login(self.user)
        response = self.client.post(reverse("gym_referrals:gym_contract_create", args=(self.gym.pk,)), {"start_date": "۱۴۰۵/۱۳/۴۰", "end_date": "۱۴۰۵/۱۲/۲۹", "price_per_referral": "100", "billing_policy": "USED", "is_active": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "تاریخ شمسی معتبر وارد کنید")

    def test_all_feature_selects_use_contrast_safe_native_style(self):
        self.grant("add_gymcontract", "change_gymcontract", "view_gyminvoice", "generate_gym_invoice")
        self.grant_dynamic("gym_referral_create", "gym_contract_manage", "gym_invoice_view")
        self.client.force_login(self.user)
        responses = [
            self.client.get(reverse("gym_referrals:create")),
            self.client.get(reverse("gym_referrals:contract_create")),
            self.client.get(reverse("gym_referrals:contract_edit", args=(self.contract.pk,))),
            self.client.get(reverse("gym_referrals:invoice_list")),
        ]
        for response in responses:
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertNotIn("---------", html)
            self.assertEqual(html.count("<select"), html.count("gym-native-select"))
        contract_html = responses[1].content.decode()
        self.assertIn("معرفی‌نامه‌های صادرشده", contract_html)
        self.assertIn("معرفی‌نامه‌های استفاده‌شده", contract_html)

    def test_native_option_palette_stays_dark_on_light_os_popup(self):
        css_path = finders.find("css/styles.css")
        with open(css_path, encoding="utf-8") as css_file:
            css = css_file.read()
        dark_option_rule = css.split(".dark .gym-native-select option", 1)[1].split("}", 1)[0]
        self.assertIn("color: #111827", dark_option_rule)
        self.assertIn("background-color: #fff", dark_option_rule)
        self.assertNotIn("color: #f9fafb", dark_option_rule)

    def test_choices_component_assets_and_scoped_theme_are_enabled(self):
        self.grant_dynamic("gym_referral_create")
        self.client.force_login(self.user)
        html = self.client.get(reverse("gym_referrals:create")).content.decode()
        self.assertIn("vendor/css/choices.min.css", html)
        self.assertIn("vendor/js/choices.min.js", html)
        js_path = finders.find("js/main.js")
        css_path = finders.find("css/styles.css")
        with open(js_path, encoding="utf-8") as js_file:
            js = js_file.read()
        with open(css_path, encoding="utf-8") as css_file:
            css = css_file.read()
        self.assertIn("select.gym-native-select", js)
        self.assertIn("gym-choices", js)
        self.assertIn(".dark .gym-choices .choices__list--dropdown", css)
        self.assertIn("background: #1f2937", css)

    def test_sidebar_is_permission_aware_and_active(self):
        self.grant_dynamic("gym_referral_create")
        self.client.force_login(self.user)
        html = self.client.get(reverse("gym_referrals:create")).content.decode()
        self.assertIn("معرفی‌نامه باشگاه", html)
        self.assertNotIn("مدیریت باشگاه‌ها", html)
        self.assertNotIn("قراردادهای باشگاه‌ها", html)
        self.assertNotIn("صورتحساب باشگاه‌ها", html)
        # A dynamic grant alone reveals the management link.
        self.grant_dynamic("gym_manage")
        html = self.client.get(reverse("gym_referrals:create")).content.decode()
        self.assertIn("مدیریت باشگاه‌ها", html)
        # Django model permissions reveal the remaining links (dual path).
        self.grant("view_gymcontract", "view_gyminvoice")
        html = self.client.get(reverse("gym_referrals:create")).content.decode()
        self.assertIn("قراردادهای باشگاه‌ها", html)
        self.assertIn("صورتحساب باشگاه‌ها", html)
        self.assertIn("bg-indigo-50 font-semibold", html)
