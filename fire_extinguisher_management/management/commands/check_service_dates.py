from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from fire_extinguisher_management.models import FireExtinguisher
from fire_extinguisher_management.notifications import notify_staff, build_extinguisher_url
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks for upcoming service dates and sends notifications'

    def handle(self, *args, **options):
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)

        # Get all operational extinguishers
        extinguishers = FireExtinguisher.objects.filter(status='operational')

        User = get_user_model()
        staff_users = User.objects.filter(is_staff=True, is_active=True)

        for extinguisher in extinguishers:
            messages = []

            # Check service date
            if extinguisher.next_service_date and extinguisher.next_service_date <= thirty_days_later:
                days_until_service = (extinguisher.next_service_date - today).days
                messages.append(
                    f'کپسول {extinguisher.serial_tag} نیاز به سرویس دارد. '
                    f'تعداد روزهای باقی‌مانده: {days_until_service} روز'
                )

            # Check pressure test date
            if extinguisher.next_pressure_test_date and extinguisher.next_pressure_test_date <= thirty_days_later:
                days_until_test = (extinguisher.next_pressure_test_date - today).days
                messages.append(
                    f'کپسول {extinguisher.serial_tag} نیاز به تست فشار دارد. '
                    f'تعداد روزهای باقی‌مانده: {days_until_test} روز'
                )

            if messages:
                for message in messages:
                    notify_staff(
                        title='هشدار سرویس کپسول',
                        message=message,
                        notification_type='warning',
                        url=build_extinguisher_url(extinguisher),
                    )

                    if hasattr(settings, 'SMS_ENABLED') and settings.SMS_ENABLED:
                        # ارسال SMS به صورت سفارشی (در صورت نیاز)
                        try:
                            for staff_user in staff_users.exclude(phone_number__isnull=True):
                                if staff_user.phone_number:
                                    self.send_sms(staff_user.phone_number, message)
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'Failed to send SMS: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Successfully checked service dates and sent notifications'))

    def send_sms(self, phone_number, message):
        """
        Placeholder for SMS sending functionality.
        Implement your SMS sending logic here.
        """
        # TODO: Implement actual SMS sending logic
        pass 