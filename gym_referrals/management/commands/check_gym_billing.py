from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils import timezone

from gym_referrals.models import Gym, GymContract


class Command(BaseCommand):
    help = "Read-only production readiness check for gym billing."

    def handle(self, *args, **options):
        try:
            today = timezone.localdate()
            active_gyms = Gym.objects.filter(is_active=True)
            active_contracts = GymContract.objects.filter(is_active=True)
            invalid_tariff = active_contracts.filter(price_per_referral__lte=0)
            missing_policy = active_contracts.exclude(billing_policy__in=GymContract.BillingPolicy.values)
            expired = active_contracts.filter(end_date__lt=today)
            gyms_without_contract = active_gyms.exclude(
                contracts__is_active=True, contracts__start_date__lte=today, contracts__end_date__gte=today
            ).distinct()
            self.stdout.write(f"Active gyms: {active_gyms.count()}")
            self.stdout.write(f"Active contracts: {active_contracts.count()}")
            self.stdout.write(f"Zero/invalid tariff contracts: {invalid_tariff.count()}")
            self.stdout.write(f"Missing/invalid billing policy: {missing_policy.count()}")
            self.stdout.write(f"Expired active contracts: {expired.count()}")
            self.stdout.write(f"Active gyms without current contract: {gyms_without_contract.count()}")
            if invalid_tariff.exists() or missing_policy.exists() or gyms_without_contract.exists():
                raise CommandError("Gym billing is not production-ready.")
        except DatabaseError as exc:
            raise CommandError("Gym billing check failed; apply the gym_referrals migrations first.") from exc
        self.stdout.write(self.style.SUCCESS("Gym billing readiness check passed."))
