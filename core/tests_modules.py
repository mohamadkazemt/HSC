from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from .admin import ModuleSettingAdminForm
from .models import ModuleSetting


class ModuleSwitchTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="module-admin",
            email="admin@example.com",
            password="Strong-test-password-123",
        )
        self.module = ModuleSetting.objects.get(module_key="anomalis")

    def test_disabled_module_public_and_admin_urls_return_404(self):
        self.module.is_active = False
        self.module.save()

        self.assertEqual(self.client.get("/anomalis/").status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/admin/anomalis/anomaly/").status_code, 404)

        response = self.client.get("/admin/")
        self.assertNotContains(response, "ناهنجاری")
        self.assertContains(response, "فعال/غیرفعال‌سازی ماژول‌ها")

        change_response = self.client.get(
            f"/admin/core/modulesetting/{self.module.pk}/change/"
        )
        self.assertEqual(change_response.status_code, 200)
        self.assertContains(change_response, "رمز عبور مدیر برای فعال‌سازی")

    def test_reactivation_requires_current_admin_password(self):
        self.module.is_active = False
        self.module.save()
        request = RequestFactory().post("/admin/core/modulesetting/")
        request.user = self.user

        invalid_form = ModuleSettingAdminForm(
            data={"module_key": "anomalis", "is_active": True, "activation_password": "wrong"},
            instance=self.module,
        )
        invalid_form.request = request
        self.assertFalse(invalid_form.is_valid())

        valid_form = ModuleSettingAdminForm(
            data={
                "module_key": "anomalis",
                "is_active": True,
                "activation_password": "Strong-test-password-123",
            },
            instance=self.module,
        )
        valid_form.request = request
        self.assertTrue(valid_form.is_valid(), valid_form.errors)

    def test_list_toggle_deactivates_and_password_protects_activation(self):
        self.client.force_login(self.user)
        toggle_url = f"/admin/core/modulesetting/{self.module.pk}/toggle/"

        response = self.client.post(toggle_url, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)

        response = self.client.post(
            toggle_url,
            {"is_active": "true", "activation_password": "wrong"},
        )
        self.assertEqual(response.status_code, 400)
        self.module.refresh_from_db()
        self.assertFalse(self.module.is_active)

        response = self.client.post(
            toggle_url,
            {
                "is_active": "true",
                "activation_password": "Strong-test-password-123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.module.refresh_from_db()
        self.assertTrue(self.module.is_active)

        list_response = self.client.get("/admin/core/modulesetting/")
        self.assertContains(list_response, "module-status-toggle")
