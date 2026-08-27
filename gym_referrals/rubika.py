from asgiref.sync import sync_to_async
from django.utils import timezone

from accounts.models import UserProfile
from .models import Gym, GymContract, GymOperator, Referral
from .services import ReferralError, ReferralService


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


def _ensure_operator(rubika_user, gym_id):
    """Return the active gym the linked user manages, or raise PermissionError."""
    if not rubika_user.user_id:
        raise PermissionError("Rubika account is not linked")
    gym = None
    if gym_id:
        gym = Gym.objects.filter(pk=gym_id, is_active=True).first()
    if not gym:
        raise PermissionError("Gym not found or inactive")
    if not GymOperator.objects.filter(user=rubika_user.user, gym=gym, is_active=True).exists():
        raise PermissionError("User does not manage this gym")
    return gym


class RubikaGymOperatorAdapter:
    """Rubika-side operator panel: review, verify and redeem referrals."""

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def operator_gyms(rubika_user):
        if not rubika_user.user_id:
            raise PermissionError("Rubika account is not linked")
        return list(Gym.objects.filter(
            operators__user=rubika_user.user, operators__is_active=True, is_active=True,
        ).distinct().values("id", "name", "code"))

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def list_referrals(rubika_user, gym_id, limit=15):
        gym = _ensure_operator(rubika_user, gym_id)
        today = timezone.localdate()
        queryset = Referral.objects.filter(gym=gym).order_by("-created_at")[:limit]
        return [{
            "referral_number": r.referral_number,
            "beneficiary": r.beneficiary_full_name_snapshot,
            "issue_date": r.issue_date,
            "valid_until": r.valid_until,
            "status": r.status,
            "is_valid": r.is_active(at=today),
        } for r in queryset]

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def statistics(rubika_user, gym_id):
        gym = _ensure_operator(rubika_user, gym_id)
        today = timezone.localdate()
        return {
            "total": Referral.objects.filter(gym=gym).count(),
            "active": Referral.objects.filter(
                gym=gym, status=Referral.Status.ACTIVE, valid_until__gte=today,
            ).count(),
            "used": Referral.objects.filter(gym=gym, status=Referral.Status.USED).count(),
            "used_today": Referral.objects.filter(
                gym=gym, status=Referral.Status.USED, redeemed_at__date=today,
            ).count(),
        }

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def verify_code(rubika_user, gym_id, code):
        """Read-only status check for a referral code belonging to the gym."""
        gym = _ensure_operator(rubika_user, gym_id)
        referral = ReferralService.find_referral(code)
        if not referral:
            raise ReferralError("REFERRAL_NOT_FOUND", "معرفی‌نامه یافت نشد.")
        if referral.gym_id != gym.pk:
            raise ReferralError("REFERRAL_GYM_MISMATCH", "این معرفی‌نامه متعلق به باشگاه دیگری است.")
        today = timezone.localdate()
        return {
            "referral_number": referral.referral_number,
            "beneficiary": referral.beneficiary_full_name_snapshot,
            "employee": referral.employee_full_name_snapshot,
            "issue_date": referral.issue_date,
            "valid_until": referral.valid_until,
            "status": referral.status,
            "is_valid": referral.is_active(at=today),
        }

    @staticmethod
    @sync_to_async(thread_sensitive=True)
    def redeem_code(rubika_user, gym_id, code):
        """Redeem a referral (register the in-person visit) on behalf of the gym."""
        gym = _ensure_operator(rubika_user, gym_id)
        referral = ReferralService.find_referral(code)
        if not referral:
            raise ReferralError("REFERRAL_NOT_FOUND", "معرفی‌نامه یافت نشد.")
        if referral.gym_id != gym.pk:
            raise ReferralError("REFERRAL_GYM_MISMATCH", "این معرفی‌نامه متعلق به باشگاه دیگری است.")
        return ReferralService.redeem(referral.public_token, rubika_user.user, gym)
