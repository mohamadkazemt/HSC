from asgiref.sync import sync_to_async
from django.utils import timezone

from accounts.models import UserProfile
from .models import Gym, GymContract, Referral
from .services import ReferralService


class RubikaReferralAdapter:
    """Thin adapter: callers must pass the persisted RubikaUser, never payload identity."""

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def create(rubika_user, beneficiary_type, beneficiary_id, gym_id, idempotency_key):
        if not rubika_user.user_id:
            raise PermissionError("Rubika account is not linked")
        return ReferralService.create_referral(
            requester=rubika_user.user, beneficiary_type=beneficiary_type, beneficiary_id=beneficiary_id,
            gym_id=gym_id, source=Referral.Source.RUBIKA, idempotency_key=idempotency_key,
        )

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def active(rubika_user, beneficiary_type, beneficiary_id):
        if not rubika_user.user_id:
            raise PermissionError("Rubika account is not linked")
        _, beneficiary = ReferralService.resolve_beneficiary(rubika_user.user, beneficiary_type, beneficiary_id)
        today = timezone.localdate()
        return Referral.objects.select_related("gym").filter(
            beneficiary_key=f"{beneficiary.type}:{beneficiary.account_id}", status=Referral.Status.ACTIVE,
            valid_from__lte=today, valid_until__gte=today,
        ).first()

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def beneficiaries(rubika_user):
        if not rubika_user.user_id:
            raise PermissionError("Rubika account is not linked")
        profile = UserProfile.objects.prefetch_related("dependents").get(user=rubika_user.user)
        result = [{
            "type": Referral.BeneficiaryType.EMPLOYEE,
            "id": profile.pk,
            "name": rubika_user.user.get_full_name().strip() or rubika_user.user.username,
            "relation": "خودم",
        }]
        result.extend({
            "type": Referral.BeneficiaryType.DEPENDENT,
            "id": dependent.pk,
            "name": f"{dependent.first_name} {dependent.last_name}".strip(),
            "relation": dependent.relationship,
        } for dependent in profile.dependents.all())
        return result

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def gyms():
        today = timezone.localdate()
        return list(Gym.objects.filter(
            is_active=True, contracts__is_active=True,
            contracts__start_date__lte=today, contracts__end_date__gte=today,
        ).distinct().values("id", "name", "code"))

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def gym(gym_id):
        today = timezone.localdate()
        return Gym.objects.filter(
            pk=gym_id, is_active=True, contracts__is_active=True,
            contracts__start_date__lte=today, contracts__end_date__gte=today,
        ).distinct().first()

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def cancel(rubika_user, referral_number, reason="لغو توسط کاربر روبیکا"):
        if not rubika_user.user_id:
            raise PermissionError("Rubika account is not linked")
        referral = Referral.objects.filter(referral_number=referral_number, employee=rubika_user.user).first()
        if not referral:
            raise PermissionError("Referral does not belong to user")
        return ReferralService.cancel(referral, rubika_user.user, reason)
