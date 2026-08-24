from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from gym_referrals.models import GymContract, GymInvoice, Referral


class Command(BaseCommand):
    help = "Read-only database/model smoke check for gym referrals."

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            GymContract.objects.count()
            Referral.objects.count()
            GymInvoice.objects.count()
        except Exception as exc:
            raise CommandError("Gym referral health check failed.") from exc
        self.stdout.write(self.style.SUCCESS("Gym referral database and models are healthy."))

