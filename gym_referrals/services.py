import hashlib
import random
import re
import string
import uuid
from dataclasses import dataclass
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import Dependent, UserProfile
from .models import Gym, GymContract, GymOperator, Referral, ReferralAuditLog, ReferralIdempotencyKey, ReferralSequence, ReferralUsage


def generate_gym_username(gym_code, try_base=None):
    """Build a safe, unique username for a gym account."""
    base = re.sub(r"[^A-Za-z0-9_-]", "", str(gym_code or "")).strip("_") or "gym"
    base = (try_base or f"gym_{base}").lower()
    UserModel = get_user_model()
    candidate, suffix = base, 1
    while UserModel.objects.filter(username=candidate).exists():
        candidate = f"{base}{suffix}"
        suffix += 1
    return candidate


def generate_gym_password(length=10):
    alphabet = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(alphabet) for _ in range(length))


def create_gym_account(gym, *, username=None, password=None):
    """Create the gym's login account and link it as an active operator.

    Returns ``(user, raw_password)`` where ``raw_password`` is the password that
    was actually set (generated when none was provided).
    """
    UserModel = get_user_model()
    raw_password = password or generate_gym_password()
    with transaction.atomic():
        user = UserModel.objects.create_user(
            username=generate_gym_username(gym.code, username),
            password=raw_password,
            first_name=gym.name[:80], last_name="", is_active=True,
        )
        gym.account_user = user
        gym.save(update_fields=("account_user", "updated_at"))
        GymOperator.objects.update_or_create(
            gym=gym, user=user, defaults={"is_active": True},
        )
    return user, raw_password


def reset_gym_account_password(gym, password=None):
    """Reset a gym account password and return ``(user, raw_password)``.

    If the gym has no account yet, one is created on the fly.
    """
    new_password = password or generate_gym_password()
    UserModel = get_user_model()
    with transaction.atomic():
        user = getattr(gym, "account_user", None)
        if user is None:
            user = UserModel.objects.create_user(
                username=generate_gym_username(gym.code),
                password=new_password,
                first_name=gym.name[:80], last_name="", is_active=True,
            )
            gym.account_user = user
            gym.save(update_fields=("account_user", "updated_at"))
        user.set_password(new_password)
        user.is_active = True
        user.save(update_fields=("password", "is_active"))
        GymOperator.objects.update_or_create(gym=gym, user=user, defaults={"is_active": True})
    return user, new_password


class ReferralError(Exception):
    def __init__(self, code, message, *, existing_referral=None):
        self.code, self.message, self.existing_referral = code, message, existing_referral
        super().__init__(message)


@dataclass(frozen=True)
class BeneficiarySnapshot:
    type: str
    account_id: int
    full_name: str
    relation: str


def is_referral_active(referral, current_datetime=None):
    return referral.is_active(current_datetime or timezone.now())


def _full_name(user):
    return user.get_full_name().strip() or user.username


class ReferralService:
    @staticmethod
    def find_referral(code):
        """Find a referral by its public token or its referral number."""
        code = str(code or "").strip()
        if not code:
            return None
        try:
            uuid.UUID(code)
        except (ValueError, TypeError, AttributeError):
            pass
        else:
            referral = Referral.objects.select_related("gym").filter(public_token=code).first()
            if referral:
                return referral
        return Referral.objects.select_related("gym").filter(referral_number__iexact=code).first()

    @staticmethod
    def resolve_beneficiary(requester, beneficiary_type, beneficiary_id):
        try:
            profile = UserProfile.objects.select_related("user").get(user=requester)
        except UserProfile.DoesNotExist as exc:
            raise ReferralError("BENEFICIARY_NOT_ELIGIBLE", "پروفایل پرسنلی یافت نشد.") from exc
        if not requester.is_active:
            raise ReferralError("BENEFICIARY_NOT_ELIGIBLE", "پرسنل فعال نیست.")
        try:
            beneficiary_id = int(beneficiary_id)
        except (TypeError, ValueError) as exc:
            raise ReferralError("INVALID_INPUT", "شناسه ذی‌نفع نامعتبر است.") from exc
        if beneficiary_type == Referral.BeneficiaryType.EMPLOYEE:
            if beneficiary_id != profile.pk:
                raise ReferralError("FORBIDDEN", "دسترسی به این ذی‌نفع مجاز نیست.")
            return profile, BeneficiarySnapshot(beneficiary_type, profile.pk, _full_name(requester), "خود")
        if beneficiary_type == Referral.BeneficiaryType.DEPENDENT:
            try:
                dependent = profile.dependents.get(pk=beneficiary_id)
            except Dependent.DoesNotExist as exc:
                raise ReferralError("FORBIDDEN", "فرد تحت تکفل متعلق به کاربر نیست.") from exc
            return profile, BeneficiarySnapshot(beneficiary_type, dependent.pk, f"{dependent.first_name} {dependent.last_name}".strip(), dependent.relationship)
        raise ReferralError("INVALID_BENEFICIARY_TYPE", "نوع ذی‌نفع نامعتبر است.")

    @classmethod
    def create_referral(cls, *, requester, beneficiary_type, beneficiary_id, gym_id, source, idempotency_key=None, issue_date=None, valid_from=None, valid_until=None, legacy_letter_no=None, notes="", actor=None):
        profile, beneficiary = cls.resolve_beneficiary(requester, beneficiary_type, beneficiary_id)
        today = timezone.localdate()
        try:
            gym = Gym.objects.get(pk=gym_id, is_active=True)
        except Gym.DoesNotExist as exc:
            raise ReferralError("GYM_NOT_ACTIVE", "باشگاه فعال نیست.") from exc
        if not GymContract.objects.filter(gym=gym, is_active=True, start_date__lte=today, end_date__gte=today).exists():
            raise ReferralError("GYM_CONTRACT_EXPIRED", "قرارداد معتبر باشگاه یافت نشد.")
        fingerprint = hashlib.sha256(f"{beneficiary.type}:{beneficiary.account_id}:{gym_id}:{source}".encode()).hexdigest()
        effective_from = valid_from or today
        effective_until = valid_until or (today + timedelta(days=30))
        if effective_until < effective_from:
            raise ReferralError("INVALID_VALIDITY_RANGE", "بازه اعتبار معرفی‌نامه نامعتبر است.")
        initial_status = Referral.Status.EXPIRED if effective_until < today else Referral.Status.ACTIVE
        try:
            with transaction.atomic():
                UserProfile.objects.select_for_update().get(pk=profile.pk)
                if idempotency_key:
                    old = ReferralIdempotencyKey.objects.select_related("referral").filter(requester=requester, key=idempotency_key).first()
                    if old:
                        if old.request_fingerprint != fingerprint:
                            raise ReferralError("IDEMPOTENCY_KEY_REUSED", "کلید تکرار برای درخواست دیگری استفاده شده است.")
                        return old.referral, False
                key = f"{beneficiary.type}:{beneficiary.account_id}"
                Referral.objects.filter(beneficiary_key=key, status=Referral.Status.ACTIVE, valid_until__lt=today).update(status=Referral.Status.EXPIRED)
                existing = Referral.objects.select_related("gym").filter(beneficiary_key=key, status=Referral.Status.ACTIVE, valid_from__lte=today, valid_until__gte=today).first()
                if existing:
                    raise ReferralError("ACTIVE_REFERRAL_ALREADY_EXISTS", "این فرد معرفی‌نامه فعال دارد.", existing_referral=existing)
                year = today.year
                sequence_row, _ = ReferralSequence.objects.select_for_update().get_or_create(year=year)
                sequence_row.value += 1
                sequence_row.save(update_fields=("value",))
                prefix = f"GYM-{year}-"
                sequence = sequence_row.value
                referral = Referral.objects.create(
                    referral_number=f"{prefix}{sequence:06d}", employee=requester,
                    beneficiary_type=beneficiary.type, beneficiary_account_id=beneficiary.account_id,
                    relation_snapshot=beneficiary.relation, employee_full_name_snapshot=_full_name(requester),
                    beneficiary_full_name_snapshot=beneficiary.full_name,
                    personnel_no_snapshot=profile.personnel_code, gym=gym, issue_date=issue_date or today,
                    valid_from=effective_from, valid_until=effective_until, status=initial_status,
                    source=source, legacy_letter_no=legacy_letter_no, notes=notes, created_by=actor or requester,
                )
                ReferralAuditLog.objects.create(referral=referral, action="CREATED", actor=actor or requester, metadata={"source": source})
                if idempotency_key:
                    ReferralIdempotencyKey.objects.create(requester=requester, key=idempotency_key, request_fingerprint=fingerprint, referral=referral)
                return referral, True
        except IntegrityError as exc:
            existing = Referral.objects.select_related("gym").filter(beneficiary_key=f"{beneficiary.type}:{beneficiary.account_id}", status=Referral.Status.ACTIVE).first()
            if existing:
                raise ReferralError("ACTIVE_REFERRAL_ALREADY_EXISTS", "این فرد معرفی‌نامه فعال دارد.", existing_referral=existing) from exc
            raise ReferralError("REFERRAL_CREATE_CONFLICT", "صدور معرفی‌نامه به علت تعارض داده انجام نشد.") from exc

    @staticmethod
    @transaction.atomic
    def cancel(referral, actor, reason):
        locked = Referral.objects.select_for_update().get(pk=referral.pk)
        if not locked.is_active():
            raise ReferralError("REFERRAL_NOT_ACTIVE", "معرفی‌نامه فعال نیست.")
        locked.status, locked.cancelled_at, locked.cancelled_by, locked.cancellation_reason = Referral.Status.CANCELLED, timezone.now(), actor, reason
        locked.save(update_fields=("status", "cancelled_at", "cancelled_by", "cancellation_reason", "updated_at"))
        ReferralAuditLog.objects.create(referral=locked, action="CANCELLED", actor=actor, metadata={"reason": reason})
        return locked

    @staticmethod
    @transaction.atomic
    def verify(public_token, actor=None):
        try:
            referral = Referral.objects.select_for_update().select_related("gym").get(public_token=public_token)
        except Referral.DoesNotExist as exc:
            raise ReferralError("REFERRAL_NOT_FOUND", "معرفی‌نامه یافت نشد.") from exc
        if referral.status == Referral.Status.CANCELLED:
            raise ReferralError("REFERRAL_CANCELLED", "معرفی‌نامه لغو شده است.")
        if referral.status == Referral.Status.USED:
            raise ReferralError("REFERRAL_ALREADY_USED", "معرفی‌نامه قبلاً استفاده شده است.")
        if not referral.is_active():
            if referral.status == Referral.Status.ACTIVE:
                referral.status = Referral.Status.EXPIRED
                referral.save(update_fields=("status", "updated_at"))
            raise ReferralError("REFERRAL_EXPIRED", "اعتبار معرفی‌نامه پایان یافته است.")
        referral.verified_at = timezone.now()
        referral.save(update_fields=("verified_at", "updated_at"))
        ReferralAuditLog.objects.create(referral=referral, action="VERIFIED", actor=actor)
        return referral

    @classmethod
    @transaction.atomic
    def redeem(cls, public_token, actor, gym):
        referral = cls.verify(public_token, actor)
        if referral.gym_id != gym.pk:
            raise ReferralError("REFERRAL_GYM_MISMATCH", "این معرفی‌نامه متعلق به باشگاه دیگری است.")
        if hasattr(referral, "usage"):
            raise ReferralError("REFERRAL_ALREADY_USED", "معرفی‌نامه قبلاً استفاده شده است.")
        now = timezone.now()
        ReferralUsage.objects.create(referral=referral, gym=gym, redeemed_by=actor, redeemed_at=now)
        referral.status, referral.redeemed_at = Referral.Status.USED, now
        referral.save(update_fields=("status", "redeemed_at", "updated_at"))
        ReferralAuditLog.objects.create(referral=referral, action="REDEEMED", actor=actor, metadata={"gym_id": gym.pk})
        return referral
