import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .access import gym_access_required
from .models import GymOperator, Referral
from .services import ReferralError, ReferralService


def referral_json(referral):
    return {
        "referralNumber": referral.referral_number,
        "publicToken": str(referral.public_token),
        "beneficiaryName": referral.beneficiary_full_name_snapshot,
        "gymName": referral.gym.name,
        "validFrom": referral.valid_from.isoformat(),
        "validUntil": referral.valid_until.isoformat(),
        "status": referral.status,
        "source": referral.source,
    }


def public_verification_json(referral, status=None):
    """Return only the fields needed to validate a printed referral."""
    return {
        "referralNumber": referral.referral_number,
        "gymName": referral.gym.name,
        "validFrom": referral.valid_from.isoformat(),
        "validUntil": referral.valid_until.isoformat(),
        "status": status or referral.status,
    }


def error_json(exc, status=400):
    payload = {"code": exc.code, "message": exc.message}
    if exc.existing_referral:
        payload["existingReferral"] = referral_json(exc.existing_referral)
    return JsonResponse(payload, status=status)


def _body(request):
    try:
        return json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return None


@login_required
@gym_access_required("gym_referral_create")
@require_POST
def create_referral(request):
    data = _body(request)
    if data is None:
        return JsonResponse({"code": "INVALID_INPUT", "message": "بدنه JSON نامعتبر است."}, status=400)
    try:
        referral, created = ReferralService.create_referral(
            requester=request.user, beneficiary_type=data.get("beneficiaryType"), beneficiary_id=data.get("beneficiaryId"),
            gym_id=data.get("gymId"), source=Referral.Source.WEB,
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return JsonResponse({"created": created, "referral": referral_json(referral)}, status=201 if created else 200)
    except ReferralError as exc:
        return error_json(exc, 409 if exc.code in {"ACTIVE_REFERRAL_ALREADY_EXISTS", "IDEMPOTENCY_KEY_REUSED"} else 400)


@login_required
@gym_access_required("gym_referral_create")
@require_GET
def current_referral(request):
    try:
        _, beneficiary = ReferralService.resolve_beneficiary(request.user, request.GET.get("beneficiaryType"), request.GET.get("beneficiaryId"))
    except ReferralError as exc:
        return error_json(exc, 403 if exc.code == "FORBIDDEN" else 400)
    referral = Referral.objects.select_related("gym").filter(
        beneficiary_key=f"{beneficiary.type}:{beneficiary.account_id}", status=Referral.Status.ACTIVE
    ).first()
    return JsonResponse({"referral": referral_json(referral) if referral and referral.is_active() else None})


@require_GET
def verify_referral(request, public_token):
    try:
        referral = Referral.objects.select_related("gym").get(public_token=public_token)
    except Referral.DoesNotExist:
        return JsonResponse({"valid": False, "code": "REFERRAL_NOT_FOUND", "message": "معرفی‌نامه یافت نشد."}, status=404)
    valid = referral.is_active(timezone.now())
    reported_status = referral.status
    if not valid and reported_status == Referral.Status.ACTIVE:
        reported_status = Referral.Status.EXPIRED
    return JsonResponse({"valid": valid, "referral": public_verification_json(referral, reported_status)})


@login_required
@gym_access_required("gym_referral_history")
@require_POST
def cancel_referral(request, referral_number):
    try:
        referral = Referral.objects.get(referral_number=referral_number, employee=request.user)
        cancelled = ReferralService.cancel(referral, request.user, (_body(request) or {}).get("reason", ""))
        return JsonResponse({"referral": referral_json(cancelled)})
    except Referral.DoesNotExist:
        return JsonResponse({"code": "REFERRAL_NOT_FOUND"}, status=404)
    except ReferralError as exc:
        return error_json(exc, 409)


@login_required
@require_POST
def redeem_referral(request, public_token):
    operator = GymOperator.objects.select_related("gym").filter(user=request.user, is_active=True, gym__is_active=True).first()
    if not operator:
        return JsonResponse({"code": "FORBIDDEN"}, status=403)
    try:
        return JsonResponse({"referral": referral_json(ReferralService.redeem(public_token, request.user, operator.gym))})
    except ReferralError as exc:
        return error_json(exc, 409 if exc.code != "REFERRAL_NOT_FOUND" else 404)
