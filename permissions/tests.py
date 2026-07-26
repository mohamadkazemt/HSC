from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserPermission
from .utils import get_all_views_with_labels
from .utils import check_permission


class TogglePermissionTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password='pass', is_staff=True)
        self.target = User.objects.create_user('target', password='pass')
        self.permission = UserPermission.objects.create(
            user=self.target,
            view_name='example_view',
            can_view=False,
        )
        self.url = reverse('permissions:toggle_permission', args=[self.permission.id])

    def test_staff_can_toggle_allowed_field(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {'type': 'user', 'field': 'can_view'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': True})
        self.permission.refresh_from_db()
        self.assertTrue(self.permission.can_view)

    def test_rejects_unknown_field(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url, {'type': 'user', 'field': 'view_name'})

        self.assertEqual(response.status_code, 400)
        self.permission.refresh_from_db()
        self.assertEqual(self.permission.view_name, 'example_view')

    def test_non_staff_cannot_toggle(self):
        self.client.force_login(self.target)
        response = self.client.post(self.url, {'type': 'user', 'field': 'can_view'})

        self.assertEqual(response.status_code, 302)
        self.permission.refresh_from_db()
        self.assertFalse(self.permission.can_view)


class DashboardPermissionCatalogTests(TestCase):
    def test_dashboard_management_statistics_are_available_for_assignment(self):
        permissions = {
            item['name']: item['label']
            for item in get_all_views_with_labels()
        }

        self.assertEqual(
            permissions['dashboard_personnel_statistics'],
            'داشبورد_آمار مدیریتی پرسنل',
        )
        self.assertEqual(
            permissions['dashboard_dependent_statistics'],
            'داشبورد_آمار مدیریتی افراد تحت تکفل',
        )

    def test_superuser_needs_explicit_dashboard_statistics_permission(self):
        superuser = User.objects.create_superuser(
            username='dashboard-admin',
            email='admin@example.com',
            password='pass',
        )

        self.assertFalse(
            check_permission(
                superuser, 'dashboard_dependent_statistics'
            ).get('can_view', False)
        )

        UserPermission.objects.create(
            user=superuser,
            view_name='dashboard_dependent_statistics',
            can_view=True,
        )

        self.assertTrue(
            check_permission(
                superuser, 'dashboard_dependent_statistics'
            ).get('can_view', False)
        )
