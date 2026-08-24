"""Collect pending leave approvals and send PeyamHub reminders."""

import logging
from datetime import timedelta

import jdatetime

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from leave_reports.models import ShiftReport
from .models import ReminderLog
from .peyamhub_client import normalize_phone, send_message

logger = logging.getLogger(__name__)

INBOX_URL = "https://miepcoj.ir/leave_reports/inbox/"


def _jalali(date_value):
    return jdatetime.date.fromgregorian(date=date_value).strftime("%Y/%m/%d")


def _dedup_window():
    hours = getattr(settings, "PEYAMHUB_REMINDER_DEDUP_HOURS", 12)
    return timezone.now() - timedelta(hours=hours)


def _recently_sent(leave, role):
    return ReminderLog.objects.filter(
        leave=leave, role=role, status=ReminderLog.Status.SENT, created_at__gte=_dedup_window()
    ).exists()


def _recipient_profile(user):
    return getattr(user, "userprofile", None)


def collect_pending_reminders(role=None):
    """Build the reminder list for pending leaves.

    Returns a list of dicts: leave, role, recipient (User), target (+98...),
    message. Recipients without a usable mobile number are reported in
    ``missing`` instead.
    """
    items, missing = [], []

    if role in (None, ReminderLog.Role.REPLACEMENT):
        pending_replacements = ShiftReport.objects.filter(
            status="pending_replacement", replacement_person__isnull=False
        ).select_related("replacement_person", "user")
        for leave in pending_replacements:
            recipient = leave.replacement_person
            profile = _recipient_profile(recipient)
            target = normalize_phone(profile.mobile) if profile else ""
            requester_name = leave.user.get_full_name() or leave.user.username
            if not target:
                missing.append({"leave": leave, "role": ReminderLog.Role.REPLACEMENT,
                                "recipient": recipient, "reason": "شماره همراه ثبت نشده است."})
                continue
            items.append({
                "leave": leave,
                "role": ReminderLog.Role.REPLACEMENT,
                "recipient": recipient,
                "target": target,
                "message": (
                    f"سلام؛ شما به‌عنوان جانشین {requester_name} انتخاب شده‌اید.\n"
                    f"درخواست مرخصی «{leave.get_leave_type_display()}» برای تاریخ "
                    f"{_jalali(leave.shift_date)} در انتظار تأیید شماست.\n"
                    f"لطفاً از طریق کارتابل بررسی کنید:\n{INBOX_URL}"
                ),
            })

    if role in (None, ReminderLog.Role.MANAGER):
        pending_managers = ShiftReport.objects.filter(status="pending_approval").select_related("user")
        for leave in pending_managers:
            approver_profile = None
            try:
                approver_profile = leave.get_required_approver()
            except Exception:
                logger.exception("get_required_approver failed for leave %s", leave.pk)
            if approver_profile is None:
                missing.append({"leave": leave, "role": ReminderLog.Role.MANAGER,
                                "recipient": None, "reason": "تأییدکننده‌ای یافت نشد."})
                continue
            recipient_user = approver_profile.user
            target = normalize_phone(approver_profile.mobile)
            requester_name = leave.user.get_full_name() or leave.user.username
            if not target:
                missing.append({"leave": leave, "role": ReminderLog.Role.MANAGER,
                                "recipient": recipient_user, "reason": "شماره همراه تأییدکننده ثبت نشده است."})
                continue
            items.append({
                "leave": leave,
                "role": ReminderLog.Role.MANAGER,
                "recipient": recipient_user,
                "target": target,
                "message": (
                    f"سلام؛ درخواست مرخصی «{leave.get_leave_type_display()}» {requester_name} "
                    f"برای تاریخ {_jalali(leave.shift_date)} در انتظار تأیید شماست.\n"
                    f"لطفاً از طریق کارتابل بررسی کنید:\n{INBOX_URL}"
                ),
            })

    return {"items": items, "missing": missing}


def send_pending_reminders(role=None, actor=None):
    """Send reminders with dedup + logging; returns a summary dict."""
    collection = collect_pending_reminders(role)
    sent = failed = skipped_dup = 0

    for item in collection["items"]:
        if _recently_sent(item["leave"], item["role"]):
            ReminderLog.objects.create(
                leave=item["leave"], role=item["role"], recipient=item["recipient"],
                target=item["target"], message=item["message"],
                status=ReminderLog.Status.SKIPPED_DUPLICATE, triggered_by=actor,
            )
            skipped_dup += 1
            continue
        try:
            send_message(item["target"], item["message"])
            status, error = ReminderLog.Status.SENT, ""
            sent += 1
        except Exception as exc:
            status, error = ReminderLog.Status.FAILED, str(exc)
            failed += 1
        ReminderLog.objects.create(
            leave=item["leave"], role=item["role"], recipient=item["recipient"],
            target=item["target"], message=item["message"],
            status=status, error=error, triggered_by=actor,
        )

    return {
        "sent": sent, "failed": failed, "skipped_duplicate": skipped_dup,
        "skipped_no_phone": len(collection["missing"]),
    }
