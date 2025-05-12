from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from fire_extinguisher_management.models import FireExtinguisher, Notification
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

User = get_user_model()

class Command(BaseCommand):
    help = 'Checks for upcoming service dates and sends notifications'

    def handle(self, *args, **options):
        today = timezone.now().date()
        thirty_days_later = today + timedelta(days=30)

        # Get all operational extinguishers
        extinguishers = FireExtinguisher.objects.filter(status='operational')

        # Get all staff users who should receive notifications
        users = User.objects.filter(is_staff=True)

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
                # Create notifications for each user
                for user in users:
                    for message in messages:
                        Notification.objects.create(
                            user=user,
                            message=message,
                            url=f'/fire-extinguisher-management/extinguishers/{extinguisher.pk}/'
                        )

                        # Send SMS if configured
                        if hasattr(settings, 'SMS_ENABLED') and settings.SMS_ENABLED:
                            try:
                                self.send_sms(user.phone_number, message)
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'Failed to send SMS to {user.username}: {str(e)}')
                                )

        self.stdout.write(self.style.SUCCESS('Successfully checked service dates and sent notifications'))

    def send_sms(self, phone_number, message):
        """
        Placeholder for SMS sending functionality.
        Implement your SMS sending logic here.
        """
        # TODO: Implement actual SMS sending logic
        pass 