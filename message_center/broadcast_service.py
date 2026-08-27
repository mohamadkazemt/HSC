"""سرویس ارسال پیام گروهی (مرکز پیام).

دو کانال ارسال پشتیبانی می‌شود:
  1. پیامک (SMS) از طریق sms.ir — متد ``send_bulk_sms`` برای متن دلخواه.
  2. روبیکا از طریق PeyamHub — ``POST /api/v1/send``.

منطق این ماژول:
  - تفکیک/تشخیص گیرنده‌ها از شماره موبایل و کد پرسنلی.
  - ذخیره نتیجه در مدل‌های Broadcast / BroadcastRecipient.
  - ارسال نهایی یک پیام گروهی (سینک، برای فراخوانی از تسک سلری).
"""
from __future__ import annotations

import logging
import re

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Broadcast, BroadcastRecipient, MessageTemplate
from .peyamhub_client import PeyamHubError, normalize_phone

logger = logging.getLogger(__name__)

MOBILE_REGEX_IR = re.compile(r"^(?:\+?98|0)?9\d{9}$")

User = get_user_model()


def _get_sms_client():
    """بازگشت سرویس گیرنده sms.ir (همان نمونه مرکزی)."""
    from core.sms_service import _get_client

    return _get_client()


def normalize_mobile(value: str) -> str:
    """نرمال‌سازی شماره موبایل ایرانی به فرمت 0912...."""
    if not value:
        return ""
    digits = "".join(ch for ch in str(value).strip() if ch.isdigit())
    if digits.startswith("0098"):
        digits = "0" + digits[4:]
    elif digits.startswith("+98"):
        digits = "0" + digits[3:]
    elif digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    if len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    if not MOBILE_REGEX_IR.match(digits):
        return ""
    return digits


def valid_mobile(value: str) -> bool:
    return bool(normalize_mobile(value))


def _profile_mobile_normalized(profile) -> str:
    if not profile or not profile.mobile:
        return ""
    raw = profile.mobile
    digits = "".join(ch for ch in str(raw).strip() if ch.isdigit())
    for prefix in ("0098", "+98", "98"):
        if digits.startswith(prefix.lstrip("+")):
            digits = digits[len(prefix.lstrip("+")):]
    # fallback به نرمال‌سازی عمومی
    return normalize_mobile(raw) or normalize_mobile(digits) or ""


def resolve_recipients(mobile_numbers, personnel_codes):
    """تشخیص گیرنده‌ها از لیست شماره موبایل و کد پرسنلی.

    Returns: list of dicts با کلیدهای:
        mobile, user, name, resolve_status, resolve_note
    """
    from accounts.models import UserProfile

    recipients = []
    seen_mobiles = set()

    # ۱) شماره‌های موبایل مستقیم
    for raw in mobile_numbers or []:
        mobile = normalize_mobile(raw)
        if not mobile:
            recipients.append({
                "mobile": str(raw or "").strip(),
                "user": None,
                "name": "",
                "resolve_status": BroadcastRecipient.ResolveStatus.INVALID,
                "resolve_note": "شماره موبایل نامعتبر است",
            })
            continue
        if mobile in seen_mobiles:
            continue
        seen_mobiles.add(mobile)
        profile = (
            UserProfile.objects.filter(mobile=mobile).select_related("user").first()
            or UserProfile.objects.filter(mobile="0" + mobile[1:]).select_related("user").first()
        )
        recipients.append({
            "mobile": mobile,
            "user": profile.user if profile else None,
            "name": f"{profile.user.get_full_name() or profile.user.username}" if profile else "",
            "resolve_status": BroadcastRecipient.ResolveStatus.OK,
            "resolve_note": "",
        })

    # ۲) کدهای پرسنلی
    seen_codes = set()
    for code in personnel_codes or []:
        code = str(code or "").strip()
        if not code:
            continue
        if code in seen_codes:
            continue
        seen_codes.add(code)
        profile = (
            UserProfile.objects.filter(personnel_code=code).select_related("user").first()
            or UserProfile.objects.filter(personnel_code__iexact=code).select_related("user").first()
        )
        if not profile:
            recipients.append({
                "mobile": "",
                "user": None,
                "name": "",
                "resolve_status": BroadcastRecipient.ResolveStatus.NOT_FOUND,
                "resolve_note": "کاربر با این کد پرسنلی یافت نشد",
            })
            continue
        mobile = _profile_mobile_normalized(profile)
        if not mobile:
            recipients.append({
                "mobile": "",
                "user": profile.user,
                "name": f"{profile.user.get_full_name() or profile.user.username}",
                "resolve_status": BroadcastRecipient.ResolveStatus.NO_PHONE,
                "resolve_note": "شماره همراه برای این کاربر ثبت نشده است",
            })
            continue
        if mobile in seen_mobiles:
            continue
        seen_mobiles.add(mobile)
        recipients.append({
            "mobile": mobile,
            "user": profile.user,
            "name": f"{profile.user.get_full_name() or profile.user.username}",
            "resolve_status": BroadcastRecipient.ResolveStatus.OK,
            "resolve_note": "",
        })

    return recipients


def _persist_recipients(broadcast, resolved):
    """ذخیره گیرنده‌ها در مدل BroadcastRecipient و به‌روزرسانی شمارنده‌ها."""
    for item in resolved:
        BroadcastRecipient.objects.create(
            broadcast=broadcast,
            mobile=item["mobile"],
            user=item["user"],
            name=item["name"],
            resolve_status=item["resolve_status"],
            resolve_note=item["resolve_note"],
        )

    ok = sum(1 for i in resolved if i["resolve_status"] == BroadcastRecipient.ResolveStatus.OK)
    ivalid = len(resolved) - ok
    broadcast.recipients_total = len(resolved)
    broadcast.recipients_resolved = ok
    broadcast.recipients_invalid = ivalid
    broadcast.status = (
        Broadcast.Status.RESOLVED
        if ok
        else Broadcast.Status.CANCELLED
    )
    broadcast.save(update_fields=[
        "recipients_total", "recipients_resolved", "recipients_invalid",
        "status",
    ])


def prepare_broadcast(broadcast: Broadcast):
    """تشخیص و ذخیره گیرنده‌های یک پیام گروهی (پیش از پیش‌نمایش/ارسال)."""
    BroadcastRecipient.objects.filter(broadcast=broadcast).delete()
    resolved = resolve_recipients(broadcast.mobile_numbers, broadcast.personnel_codes)
    _persist_recipients(broadcast, resolved)
    return resolved


# ---------------------------------------------------------------------------
# ارسال
# ---------------------------------------------------------------------------

def _send_sms_numbers(client, numbers, message):
    """ارسال پیامک دلخواه (bulk) به لیستی از شماره‌ها؛ بازگشت (ok, error)."""
    if not numbers:
        return True, ""
    line = getattr(settings, "SMSIR_LINE_NUMBER", "")
    response = client.send_bulk_sms(numbers=numbers, message=message, linenumber=line)
    status_code = getattr(response, "status_code", None)
    if status_code != 200:
        body = getattr(response, "text", "")[:250]
        return False, f"HTTP {status_code}: {body}"

    payload = {}
    try:
        payload = response.json() if hasattr(response, "json") else (response if isinstance(response, dict) else {})
    except Exception:
        payload = {}
    status = payload.get("status")
    is_ok = payload.get("IsSuccessful") is True or status == 1
    if not is_ok:
        return False, str(payload.get("Message") or payload.get("message") or "ارسال ناموفق")
    return True, ""


def _send_sms_broadcast(broadcast: Broadcast, numbers):
    """ارسال پیامک گروهی؛ شماره‌ها را بسته به محدودیت هر بسته تقسیم می‌کند."""
    client = _get_sms_client()
    ok, error = _send_sms_numbers(client, numbers, broadcast.text)
    if not ok:
        raise RuntimeError(error or "خطا در ارسال پیامک")
    return ok


def _send_rubika_broadcast(broadcast: Broadcast, recipients):
    """ارسال پیام روبیکا به گیرنده‌های معتبر. (عدد‌ها به +98 تبدیل می‌شوند)."""
    from .peyamhub_client import send_message

    for rec in recipients:
        target = normalize_phone(rec.mobile)
        if not target:
            rec.send_status = BroadcastRecipient.SendStatus.CANCELED
            rec.error = "شماره برای روبیکا نرمال نشد"
            rec.save(update_fields=["send_status", "error"])
            continue
        try:
            send_message(target, broadcast.text)
            rec.send_status = BroadcastRecipient.SendStatus.SENT
            rec.sent_at = rec.sent_at or __import__("django.utils.timezone", fromlist=["now"]).now()
            rec.save(update_fields=["send_status", "sent_at"])
        except PeyamHubError as exc:
            rec.send_status = BroadcastRecipient.SendStatus.FAILED
            rec.error = str(exc)
            rec.save(update_fields=["send_status", "error"])


def execute_broadcast(broadcast: Broadcast) -> bool:
    """ارسال واقعی یک پیام گروهی؛ مفروض است گیرنده‌ها از قبل ذخیره شده‌اند."""
    from django.utils import timezone

    recipients = list(
        broadcast.recipients.filter(resolve_status=BroadcastRecipient.ResolveStatus.OK)
    )
    if not recipients:
        broadcast.status = Broadcast.Status.FAILED
        broadcast.error = "گیرنده معتبری وجود ندارد."
        broadcast.save(update_fields=["status", "error"])
        return False

    if broadcast.channel == Broadcast.Channel.RUBIKA:
        broadcast.status = Broadcast.Status.SENDING
        broadcast.sent_at = timezone.now()
        broadcast.save(update_fields=["status", "sent_at"])
        _send_rubika_broadcast(broadcast, recipients)
    else:
        numbers = [r.mobile for r in recipients]
        broadcast.status = Broadcast.Status.SENDING
        broadcast.sent_at = timezone.now()
        broadcast.save(update_fields=["status", "sent_at"])
        try:
            ok = _send_sms_broadcast(broadcast, numbers)
            if ok:
                failed = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.FAILED).count()
                for rec in recipients:
                    rec.send_status = BroadcastRecipient.SendStatus.SENT
                    rec.sent_at = timezone.now()
                    rec.save(update_fields=["send_status", "sent_at"])
                failed = 0
                broadcast.status = (
                    Broadcast.Status.COMPLETED if failed == 0 else Broadcast.Status.PARTIAL
                )
                broadcast.save(update_fields=["status"])
            else:
                broadcast.status = Broadcast.Status.FAILED
                broadcast.error = "ارسال پیامک ناموفق بود."
                broadcast.save(update_fields=["status", "error"])
                return False
        except Exception as exc:
            logger.exception("SMS broadcast failed for %s: %s", broadcast.pk, exc)
            broadcast.status = Broadcast.Status.FAILED
            broadcast.error = str(exc)
            broadcast.save(update_fields=["status", "error"])
            return False

    # به‌روزرسانی وضعیت نهایی بر اساس گیرنده‌ها (برای روبیکا)
    if broadcast.channel == Broadcast.Channel.RUBIKA:
        sent = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.SENT).count()
        failed = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.FAILED).count()
        if failed == 0:
            broadcast.status = Broadcast.Status.COMPLETED
        elif sent > 0:
            broadcast.status = Broadcast.Status.PARTIAL
        else:
            broadcast.status = Broadcast.Status.FAILED
        broadcast.save(update_fields=["status"])

    # افزایش استفاده قالب اگر از قالب بوده
    return True


def mark_invalid_recipients_canceled(broadcast: Broadcast):
    """گیرنده‌های نامعتبر/بدون شماره را به‌صورت لغو علامت‌گذاری می‌کند."""
    broadcast.recipients.exclude(resolve_status=BroadcastRecipient.ResolveStatus.OK).update(
        send_status=BroadcastRecipient.SendStatus.CANCELED,
        error="گیرنده نامعتبر / بدون شماره",
    )


__all__ = [
    "normalize_mobile",
    "valid_mobile",
    "resolve_recipients",
    "prepare_broadcast",
    "execute_broadcast",
    "mark_invalid_recipients_canceled",
]
