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
import random
import re
import time

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

def _send_sms_numbers(client, numbers, message, return_data: bool = False):
    """ارسال پیامک دلخواه (bulk) به لیستی از شماره‌ها؛ بازگشت (ok, error) یا (ok, error, data)."""
    if not numbers:
        return (True, "", {}) if return_data else (True, "")
    line = getattr(settings, "SMSIR_LINE_NUMBER", "")
    response = client.send_bulk_sms(numbers=numbers, message=message, linenumber=line)
    status_code = getattr(response, "status_code", None)
    if status_code != 200:
        body = getattr(response, "text", "")[:250]
        err_msg = f"HTTP {status_code}: {body}"
        return (False, err_msg, {}) if return_data else (False, err_msg)

    payload = {}
    try:
        payload = response.json() if hasattr(response, "json") else (response if isinstance(response, dict) else {})
    except Exception:
        payload = {}
    status = payload.get("status")
    is_ok = payload.get("IsSuccessful") is True or status == 1
    data = payload.get("data") or {}
    if not is_ok:
        err_msg = str(payload.get("Message") or payload.get("message") or "ارسال ناموفق")
        return (False, err_msg, data) if return_data else (False, err_msg)
    return (True, "", data) if return_data else (True, "")


def _send_sms_broadcast(broadcast: Broadcast, recipients):
    """ارسال پیامک گروهی و ذخیره شناسه پیام‌ها برای رهگیری گزارش تحویل."""
    from django.utils import timezone

    client = _get_sms_client()
    # در صورتی که لیستی از آبجکت‌های BroadcastRecipient نباشد، آنها را بازیابی کن
    if recipients and hasattr(recipients[0], "mobile"):
        rec_list = recipients
        numbers = [r.mobile for r in rec_list if r.mobile]
    else:
        rec_list = list(broadcast.recipients.filter(resolve_status=BroadcastRecipient.ResolveStatus.OK))
        numbers = [r.mobile for r in rec_list if r.mobile]

    ok, error, data = _send_sms_numbers(client, numbers, broadcast.text, return_data=True)
    if not ok:
        raise RuntimeError(error or "خطا در ارسال پیامک")

    pack_id = data.get("packId") or ""
    if pack_id:
        broadcast.sms_pack_id = str(pack_id)
        broadcast.save(update_fields=["sms_pack_id"])

    message_ids = data.get("messageIds") or []
    now_time = timezone.now()
    for i, rec in enumerate(rec_list):
        if i < len(message_ids):
            rec.message_id = str(message_ids[i])
        rec.send_status = BroadcastRecipient.SendStatus.SENT
        rec.sent_at = now_time
        rec.save(update_fields=["message_id", "send_status", "sent_at"])

    return ok


def _send_rubika_broadcast(broadcast: Broadcast, recipients):
    """ارسال هوشمند پیام روبیکا با سناریوی ضداسپم و چند لایه:

    ۱. لایه اول (ربات رسمی شرکت):
       اگر گیرنده عضو ربات رسمی روبیکای شرکت باشد (RubikaUser با chat_id فعال)، پیام
       مستقیماً از طریق ربات رسمی ارسال می‌شود (سریع، رایگان، بدون هیچ‌گونه محدودیت اکانت).

    ۲. لایه دوم (PeyamHub با تاخیر محافظتی - Pacing):
       برای گیرندگانی که هنوز به ربات متصل نشده‌اند، پیام از طریق وب‌سرویس PeyamHub
       با ایجاد تاخیر کنترل‌شده و تصادفی (بین ۴ تا ۶.۵ ثانیه) ارسال می‌شود تا الگوریتم
       ضداسپم روبیکا رفتار انسانی تشخیص دهد و از Flood-Wait جلوگیری شود.

    ۳. لایه سوم (مدارشکن - Circuit Breaker):
       اگر در حین ارسال از PeyamHub، خطای محدودیت زمانی روبیکا دریافت شد، ادامه ارسال
       از طریق اکانت بلافاصله متوقف می‌شود تا مدت مسدودیت موقت اکانت تمدید نگردد.

    ۴. لایه چهارم (فال‌بک خودکار به پیامک - Smart SMS Fallback):
       برای شماره‌هایی که اصلاً در روبیکا ثبت نیستند یا گیرندگانی که به دلیل فعال شدن
       مدارشکن پیام دریافت نکرده‌اند، پیام به صورت خودکار به عنوان پیامک مخابراتی (SMS)
       ارسال می‌شود تا هیچ پیامی نسوزد و ۱۰۰٪ پرسنل پیام را دریافت کنند.
    """
    import random
    import time
    from django.utils import timezone
    from .peyamhub_client import PeyamHubError, send_message
    from .services import RATE_LIMIT_MARKERS, PERMANENT_MARKERS

    sms_client = None
    try:
        sms_client = _get_sms_client()
    except Exception as e:
        logger.warning("[broadcast] Could not load SMS client for fallback: %s", e)

    base_delay = float(getattr(settings, "PEYAMHUB_SEND_DELAY_SECONDS", 5))
    fallback_enabled = getattr(settings, "RUBIKA_SMS_FALLBACK_ENABLED", True)

    circuit_broken = False
    rate_limit_reason = ""
    peyamhub_send_count = 0

    for rec in recipients:
        now_time = timezone.now()
        target = normalize_phone(rec.mobile)

        if not target and not rec.user:
            rec.send_status = BroadcastRecipient.SendStatus.CANCELED
            rec.error = "شماره برای روبیکا نامعتبر است"
            rec.save(update_fields=["send_status", "error"])
            continue

        # ۱) اولویت اول: بررسی عضویت در ربات رسمی روبیکای شرکت
        rubika_user = None
        if rec.user:
            try:
                from rubika_bot.models import RubikaUser
                rubika_user = RubikaUser.objects.filter(user=rec.user).first()
            except Exception:
                rubika_user = None

        if rubika_user and rubika_user.chat_id:
            try:
                from rubika_bot.services import RubPyIntegrationService
                service = RubPyIntegrationService.get_instance()
                service.send_text_message(rubika_user.chat_id, broadcast.text)
                rec.send_status = BroadcastRecipient.SendStatus.SENT
                rec.sent_at = now_time
                rec.error = "ارسال شد (ربات رسمی روبیکا)"
                rec.save(update_fields=["send_status", "sent_at", "error"])
                logger.info("[broadcast %s] Sent to user %s via official Rubika bot", broadcast.pk, rec.user)
                continue
            except Exception as exc:
                logger.warning(
                    "[broadcast %s] Official bot send failed for %s (%s): %s; falling back",
                    broadcast.pk, rec.user, rubika_user.chat_id, exc
                )

        # ۲) اگر مدارشکن فعال شده باشد (اکانت روبیکا محدود شده است) -> فال‌بک مستقیم به پیامک
        if circuit_broken:
            if fallback_enabled and sms_client and rec.mobile:
                ok, err = _send_sms_numbers(sms_client, [rec.mobile], broadcast.text)
                if ok:
                    rec.send_status = BroadcastRecipient.SendStatus.SENT
                    rec.sent_at = now_time
                    rec.error = "ارسال شد (پیامک جایگزین - اکانت روبیکا موقتاً محدود است)"
                    rec.save(update_fields=["send_status", "sent_at", "error"])
                else:
                    rec.send_status = BroadcastRecipient.SendStatus.FAILED
                    rec.error = f"محدودیت روبیکا و شکست پیامک: {err}"
                    rec.save(update_fields=["send_status", "error"])
            else:
                rec.send_status = BroadcastRecipient.SendStatus.FAILED
                rec.error = f"اکانت روبیکا محدود است: {rate_limit_reason}"
                rec.save(update_fields=["send_status", "error"])
            continue

        if not target:
            rec.send_status = BroadcastRecipient.SendStatus.CANCELED
            rec.error = "شماره برای روبیکا نامعتبر است"
            rec.save(update_fields=["send_status", "error"])
            continue

        # ۳) تاخیر محافظتی (Pacing) قبل از فراخوانی PeyamHub
        if peyamhub_send_count > 0 and base_delay > 0:
            delay_time = random.uniform(base_delay, base_delay + 2.0)
            logger.debug("[broadcast %s] Sleeping %.2fs before next PeyamHub send", broadcast.pk, delay_time)
            time.sleep(delay_time)

        peyamhub_send_count += 1

        try:
            send_message(target, broadcast.text)
            rec.send_status = BroadcastRecipient.SendStatus.SENT
            rec.sent_at = now_time
            rec.error = "ارسال شد (روبیکا)"
            rec.save(update_fields=["send_status", "sent_at", "error"])
        except (PeyamHubError, Exception) as exc:
            err_msg = str(exc)
            is_rate_limit = any(m in err_msg for m in RATE_LIMIT_MARKERS)
            is_permanent = any(m in err_msg for m in PERMANENT_MARKERS)

            if is_rate_limit:
                circuit_broken = True
                rate_limit_reason = err_msg
                logger.error(
                    "[broadcast %s] Rubika rate limit hit (%s). Tripping circuit breaker for remaining recipients.",
                    broadcast.pk, err_msg
                )
                if fallback_enabled and sms_client and rec.mobile:
                    ok, err = _send_sms_numbers(sms_client, [rec.mobile], broadcast.text)
                    if ok:
                        rec.send_status = BroadcastRecipient.SendStatus.SENT
                        rec.sent_at = now_time
                        rec.error = "ارسال شد (پیامک جایگزین - محدودیت موقت روبیکا)"
                        rec.save(update_fields=["send_status", "sent_at", "error"])
                    else:
                        rec.send_status = BroadcastRecipient.SendStatus.FAILED
                        rec.error = f"محدودیت روبیکا و شکست پیامک: {err}"
                        rec.save(update_fields=["send_status", "error"])
                else:
                    rec.send_status = BroadcastRecipient.SendStatus.FAILED
                    rec.error = err_msg
                    rec.save(update_fields=["send_status", "error"])

            elif is_permanent:
                logger.info("[broadcast %s] Target %s is not registered on Rubika; falling back to SMS", broadcast.pk, target)
                if fallback_enabled and sms_client and rec.mobile:
                    ok, err = _send_sms_numbers(sms_client, [rec.mobile], broadcast.text)
                    if ok:
                        rec.send_status = BroadcastRecipient.SendStatus.SENT
                        rec.sent_at = now_time
                        rec.error = "ارسال شد (پیامک جایگزین - کاربر عضو روبیکا نبود)"
                        rec.save(update_fields=["send_status", "sent_at", "error"])
                    else:
                        rec.send_status = BroadcastRecipient.SendStatus.FAILED
                        rec.error = f"کاربر عضو روبیکا نبود و پیامک ناموفق شد: {err}"
                        rec.save(update_fields=["send_status", "error"])
                else:
                    rec.send_status = BroadcastRecipient.SendStatus.FAILED
                    rec.error = err_msg
                    rec.save(update_fields=["send_status", "error"])
            else:
                logger.warning("[broadcast %s] PeyamHub send failed for %s: %s", broadcast.pk, target, err_msg)
                if fallback_enabled and sms_client and rec.mobile:
                    ok, err = _send_sms_numbers(sms_client, [rec.mobile], broadcast.text)
                    if ok:
                        rec.send_status = BroadcastRecipient.SendStatus.SENT
                        rec.sent_at = now_time
                        rec.error = f"ارسال شد (پیامک جایگزین - خطای روبیکا: {err_msg[:40]})"
                        rec.save(update_fields=["send_status", "sent_at", "error"])
                        continue
                rec.send_status = BroadcastRecipient.SendStatus.FAILED
                rec.error = err_msg
                rec.save(update_fields=["send_status", "error"])

    if circuit_broken:
        broadcast.error = f"حساب روبیکا موقتاً به سقف ارسال برخورد کرد؛ پیام‌های باقیمانده به پیامک هدایت شدند. ({rate_limit_reason[:100]})"
        broadcast.save(update_fields=["error"])


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
        broadcast.status = Broadcast.Status.SENDING
        broadcast.sent_at = timezone.now()
        broadcast.save(update_fields=["status", "sent_at"])
        try:
            ok = _send_sms_broadcast(broadcast, recipients)
            if ok:
                failed = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.FAILED).count()
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

    return True


def retry_broadcast_failed_recipients(broadcast: Broadcast, channel: str = "sms") -> dict:
    """ارسال مجدد پیام فقط برای گیرندگانی که در ارسال قبلی ناموفق بوده‌اند."""
    from django.utils import timezone

    failed_recs = list(
        broadcast.recipients.filter(
            resolve_status=BroadcastRecipient.ResolveStatus.OK,
            send_status=BroadcastRecipient.SendStatus.FAILED,
        )
    )
    if not failed_recs:
        return {"retried": 0, "sent": 0, "failed": 0, "message": "هیچ گیرنده ناموفقی یافت نشد."}

    now_time = timezone.now()
    if channel == Broadcast.Channel.SMS or channel == "sms":
        client = _get_sms_client()
        mobiles = [r.mobile for r in failed_recs if r.mobile]
        try:
            ok, err = _send_sms_numbers(client, mobiles, broadcast.text)
        except Exception as exc:
            ok, err = False, str(exc)

        if ok:
            for r in failed_recs:
                r.send_status = BroadcastRecipient.SendStatus.SENT
                r.sent_at = now_time
                r.error = "ارسال شد (پیامک مجدد به ناموفق‌ها)"
                r.save(update_fields=["send_status", "sent_at", "error"])
        else:
            for r in failed_recs:
                r.error = f"خطا در ارسال پیامک مجدد: {err}"
                r.save(update_fields=["error"])
    else:
        # کانال روبیکا با سناریوی ۴ لایه ضداسپم
        for r in failed_recs:
            r.send_status = BroadcastRecipient.SendStatus.PENDING
            r.save(update_fields=["send_status"])
        _send_rubika_broadcast(broadcast, failed_recs)

    # به‌روزرسانی وضعیت پیام گروهی
    sent_count = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.SENT).count()
    failed_count = broadcast.recipients.filter(send_status=BroadcastRecipient.SendStatus.FAILED).count()
    if failed_count == 0:
        broadcast.status = Broadcast.Status.COMPLETED
    elif sent_count > 0:
        broadcast.status = Broadcast.Status.PARTIAL
    else:
        broadcast.status = Broadcast.Status.FAILED
    broadcast.save(update_fields=["status"])

    return {
        "retried": len(failed_recs),
        "sent": sent_count,
        "failed": failed_count,
        "channel": channel,
    }


def sync_broadcast_delivery_reports(broadcast: Broadcast) -> dict:
    """استعلام و به‌روزرسانی گزارش تحویل پیامک‌ها از وب‌سرویس SMS.ir.

    برای هر گیرنده:
      - تطبیق با شناسه پیامک (message_id) یا شماره موبایل (۱۰ رقم انتهایی).
      - کدهای وضعیت پیامک در سامانه SMS.ir:
          1: تحویل داده شد (رسیده به گوشی) -> send_status = DELIVERED
          2: نرسیده به گوشی (خاموش/مسدود) -> send_status = FAILED
          3: رسیده به مخابرات
          4, 5: خطای اپراتور -> send_status = FAILED
          7: در صف ارسال اپراتور به گوشی
      - ذخیره زمان تحویل (delivered_at) در صورت وجود.

    Returns:
        dict: آمار خلاصه وضعیت تحویل
    """
    from datetime import datetime, timezone as dt_timezone
    from django.utils import timezone

    client = _get_sms_client()
    recipients = list(broadcast.recipients.filter(
        resolve_status=BroadcastRecipient.ResolveStatus.OK
    ))

    # ۱) نگاشت بر اساس message_id
    by_msg_id = {str(r.message_id).strip(): r for r in recipients if r.message_id}
    # ۲) نگاشت بر اساس ۱۰ رقم آخر شماره همراه
    by_mobile_last10 = {}
    for r in recipients:
        if r.mobile:
            digits = "".join(ch for ch in str(r.mobile) if ch.isdigit())
            if len(digits) >= 10:
                by_mobile_last10[digits[-10:]] = r

    reports_map = {}

    # مرحله اول: استعلام از گزارش پیام‌های امروز SMS.ir
    try:
        page = 1
        max_pages = 5
        while page <= max_pages:
            resp = client.report_today(page_size=100, page_number=page)
            if getattr(resp, "status_code", None) != 200:
                break
            payload = resp.json() if hasattr(resp, "json") else {}
            items = payload.get("data") or []
            if not items:
                break
            for item in items:
                msg_id = str(item.get("messageId") or "")
                mob = str(item.get("mobile") or "")
                mob_digits = "".join(ch for ch in mob if ch.isdigit())
                last10 = mob_digits[-10:] if len(mob_digits) >= 10 else ""

                matched_rec = None
                if msg_id and msg_id in by_msg_id:
                    matched_rec = by_msg_id[msg_id]
                elif last10 and last10 in by_mobile_last10:
                    matched_rec = by_mobile_last10[last10]

                if matched_rec and matched_rec.id not in reports_map:
                    reports_map[matched_rec.id] = item

            if len(items) < 100:
                break
            page += 1
    except Exception as exc:
        logger.warning("[sync_delivery %s] Failed to fetch report_today: %s", broadcast.pk, exc)

    # مرحله دوم: استعلام تکی پیام برای رکوردهایی که هنوز یافت نشده‌اند ولی message_id دارند
    for r in recipients:
        if r.id not in reports_map and r.message_id:
            try:
                msg_id_int = int(r.message_id)
                res = client.report_message(msg_id_int)
                if getattr(res, "status_code", None) == 200:
                    data = res.json().get("data") or {}
                    if data:
                        reports_map[r.id] = data
            except Exception as e:
                logger.debug("[sync_delivery %s] report_message failed for msg %s: %s", broadcast.pk, r.message_id, e)

    # مرحله سوم: اعمال نتایج روی رکوردها
    stats = {
        "total": len(recipients),
        "delivered": 0,
        "queued": 0,
        "failed": 0,
        "operator": 0,
        "not_found": 0,
    }

    for r in recipients:
        report = reports_map.get(r.id)
        if not report:
            if r.send_status == BroadcastRecipient.SendStatus.DELIVERED:
                stats["delivered"] += 1
            elif r.send_status == BroadcastRecipient.SendStatus.FAILED:
                stats["failed"] += 1
            else:
                stats["not_found"] += 1
            continue

        state = report.get("deliveryState")
        msg_id = report.get("messageId")
        if msg_id and not r.message_id:
            r.message_id = str(msg_id)

        r.delivery_state = state
        delivery_dt = report.get("deliveryDateTime")
        if delivery_dt and isinstance(delivery_dt, (int, float)):
            try:
                r.delivered_at = datetime.fromtimestamp(delivery_dt, tz=dt_timezone.utc)
            except Exception:
                pass

        if state == 1:
            r.send_status = BroadcastRecipient.SendStatus.DELIVERED
            stats["delivered"] += 1
        elif state == 2:
            r.send_status = BroadcastRecipient.SendStatus.FAILED
            r.error = "نرسیده به گوشی (خاموش یا مسدود)"
            stats["failed"] += 1
        elif state in (4, 5):
            r.send_status = BroadcastRecipient.SendStatus.FAILED
            r.error = f"خطای اپراتور (کد {state})"
            stats["failed"] += 1
        elif state == 7:
            stats["queued"] += 1
        elif state == 3:
            stats["operator"] += 1
        else:
            if r.send_status == BroadcastRecipient.SendStatus.DELIVERED:
                stats["delivered"] += 1
            elif r.send_status == BroadcastRecipient.SendStatus.FAILED:
                stats["failed"] += 1

        r.save(update_fields=["message_id", "delivery_state", "delivered_at", "send_status", "error"])

    return stats


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
    "sync_broadcast_delivery_reports",
    "retry_broadcast_failed_recipients",
    "mark_invalid_recipients_canceled",
]

