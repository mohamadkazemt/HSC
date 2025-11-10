from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from dashboard.models import Notification
from fire_extinguisher_management.models import FireExtinguisherType, FireExtinguisher
from fire_extinguisher_management.notifications import notify_staff, build_extinguisher_url


class FireExtinguisherNotificationTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.staff_user = self.User.objects.create_user(
            username='staff',
            password='testpass123',
            is_staff=True,
            is_active=True,
        )

        self.extinguisher_type = FireExtinguisherType.objects.create(
            name='پودر خشک',
            agent='Dry Chemical',
            use_class='کلاس ABC',
            inspection_interval_months=6,
            service_interval_years=1,
            pressure_test_interval_years=5,
        )

        today = timezone.now().date()
        self.extinguisher = FireExtinguisher.objects.create(
            serial_tag='FE-001',
            extinguisher_type=self.extinguisher_type,
            capacity_value=6,
            capacity_unit='kg',
            manufacturer='ACME',
            model_number='X1',
            purchase_date=today,
            manufacture_date=today,
            commission_date=today,
            expected_lifespan_years=10,
            status='operational',
        )

    def test_notify_staff_creates_notification_for_each_staff_user(self):
        notify_staff(title='هشدار کپسول', message='کپسول نیاز به بررسی دارد.', notification_type='warning')

        notification = Notification.objects.get(user=self.staff_user)
        self.assertEqual(notification.title, 'هشدار کپسول')
        self.assertEqual(notification.notification_type, 'warning')

    def test_build_extinguisher_url_contains_pk(self):
        url = build_extinguisher_url(self.extinguisher)
        self.assertIsNotNone(url)
        self.assertIn(str(self.extinguisher.pk), url)

    def test_build_extinguisher_url_unsaved_returns_none(self):
        unsaved = FireExtinguisher(
            serial_tag='FE-002',
            extinguisher_type=self.extinguisher_type,
            capacity_value=6,
            capacity_unit='kg',
            manufacturer='ACME',
            model_number='X2',
            purchase_date=timezone.now().date(),
            manufacture_date=timezone.now().date(),
            commission_date=timezone.now().date(),
            expected_lifespan_years=10,
        )
        self.assertIsNone(build_extinguisher_url(unsaved))
