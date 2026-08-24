"""Collect pending leave approvals and send PeyamHub reminders safely.

Rubika aggressively rate-limits accounts that send too fast (the account
gets temporarily banned with a Persian message containing «محدود شده»).
To stay permanently below the limits this module enforces:

1. **Recipient grouping** — a person who is the approver/replacement of
   several pending leaves receives ONE combined message instead of one
   message per leave.
2. **Pacing** — a configurable pause (``PEYAMHUB_SEND_DELAY_SECONDS``)
   between consecutive sends.
3. **Abort on ban** — the moment Rubika replies with its temporary-ban
   error the whole run stops; remaining recipients are left untouched so
   we never push traffic against an active ban.
4. **Permanent-failure memory** — numbers that are not registered on
   Rubika (or missing from the sender's contact book) are marked
   ``failed_permanent`` once and never retried automatically.
"""

import logging
import time
from datetime import timedelta

import jdatetime

from django.conf import settings
from django.utils import timezone

from leave_reports.models import ShiftReport
from .models import ReminderLog
from .peyamhub_client import normalize_phone, send_message

logger = logging.getLogger(__name__)

INBOX_URL = "https://miepcoj.ir/leave_reports/inbox/"

RATE_LIMIT_MARKERS = ("محدود شده", "محدود کرده", "TOO_REQUESTS", "rate limit", "429")
PERMANENT_MARKERS = ("ثبت نشده است", "کاربر روبیکا نیست")


def _jalali(date_value):
    return jdatetime.date.fromgregorian(date=date_value).strftime("%Y/%m/%d")


def _send_delay():
    return float(getattr(settings, "PEYAMHUB_SEND_DELAY_SECONDS", 4))


def _dedup_window():
    hours = getattr(settings, "PEYAMHUB_REMINDER_DEDUP_HOURS", 12)
    return timezone.now() - timedelta(hours=hours)


def _latest_log(leave, role):
    return (
        ReminderLog.objects.filter(leave=leave, role=role)
        .order_by("-created_at")
        .first()
    )


def _classify_error(text):
    text = text or ""
    lowered = text.lower()
    if any(marker.lower() in lowered for marker in RATE_LIMIT_MARKERS):
        return "rate_limit"
    if any(marker in text for marker in PERMANENT_MARKERS):
        return "permanent"
    return "transient"


def _recipient_profile(user):
    return getattr(user, "userprofile", None)


def collect_pending_reminders(role=None):
    """Build the reminder list for pending leaves (one entry per LEAVE).

    Recipients without a usable mobile number are reported in ``missing``.
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
                "requester_name": requester_name,
                "shift_date": leave.shift_date,
                "leave_type": leave.get_leave_type_display(),
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
            target = normalize_phone(approver_profile.mobile)
            requester_name = leave.user.get_full_name() or leave.user.username
            if not target:
                missing.append({"leave": leave, "role": ReminderLog.Role.MANAGER,
                                "recipient": approver_profile.user,
                                "reason": "شماره همراه تأییدکننده ثبت نشده است."})
                continue
            items.append({
                "leave": leave,
                "role": ReminderLog.Role.MANAGER,
                "recipient": approver_profile.user,
                "target": target,
                "requester_name": requester_name,
                "shift_date": leave.shift_date,
                "leave_type": leave.get_leave_type_display(),
            })

    return {"items": items, "missing": missing}


def _group_for_recipient(items):
    """Merge per-leave items of the same (role, target) into one group."""
    groups = {}
    order = []
    for item in items:
        key = (item["role"], item["target"])
        if key not in groups:
            groups[key] = {"role": item["role"], "target": item["target"],
                           "recipient": item["recipient"], "leaves": []}
            order.append(key)
        groups[key]["leaves"].append(item)
    return [groups[key] for key in order]


def _build_message(group):
    leaves = group["leaves"]
    lines = []
    if len(leaves) == 1:
        leaf = leaves[0]
        if group["role"] == ReminderLog.Role.REPLACEMENT:
            header = f"سلام؛ شما به‌عنوان جانشین {leaf['requester_name']} انتخاب شده‌اید."
        else:
            header = f"سلام؛ درخواست مرخصی {leaf['requester_name']} در انتظار تأیید شماست."
        lines.append(header)
        lines.append(
            f"جزئیات: «{leaf['leave_type']}» — تاریخ {_jalali(leaf['shift_date'])}"
        )
    else:
        lines.append(
            f"سلام؛ شما برای {len(leaves)} درخواست مرخصی "
            f"{'به‌عنوان جانشین' if group['role'] == ReminderLog.Role.REPLACEMENT else 'به‌عنوان تأییدکننده'} "
            f"در انتظار بررسی هستید:"
        )
        for index, leaf in enumerate(leaves, 1):
            lines.append(f"{index}. {leaf['requester_name']} — {_jalali(leaf['shift_date'])}")
    lines.append(f"لطفاً از طریق کارتابل بررسی کنید:\n{INBOX_URL}")
    return "\n".join(lines)


def send_pending_reminders(role=None, actor=None):
    """Send grouped reminders with pacing, ban-abort and dedup."""
    collection = collect_pending_reminders(role)
    delay = _send_delay()
    sent = failed = skipped_dup = skipped_invalid = 0
    aborted = False
    remaining_after_abort = 0

    groups = _group_for_recipient(collection["items"])
    # حذف گروه‌هایی که همه برگه‌هایشان اخیراً ارسال/رد قطعی شده‌اند
    eligible_groups = []
    for group in groups:
        pending_leaves = []
        for leaf_item in group["leaves"]:
            latest = _latest_log(leaf_item["leave"], group["role"])
            if latest is None:
                pending_leaves.append(leaf_item)
            elif latest.status == ReminderLog.Status.SENT and latest.created_at >= _dedup_window():
                skipped_dup += 1
            elif latest.status == ReminderLog.Status.FAILED_PERMANENT:
                skipped_invalid += 1
            else:
                pending_leaves.append(leaf_item)
        if pending_leaves:
            group["leaves"] = pending_leaves
            eligible_groups.append(group)

    for index, group in enumerate(eligible_groups):
        if index > 0 and delay > 0:
            time.sleep(delay)

        message = _build_message(group)
        try:
            send_message(group["target"], message)
            status, error = ReminderLog.Status.SENT, ""
            sent += 1
        except Exception as exc:
            error = str(exc)
            kind = _classify_error(error)
            if kind == "rate_limit":
                status = ReminderLog.Status.FAILED
                failed += 1
                aborted = True
                remaining_after_abort = len(eligible_groups) - index - 1
                logger.error("Rubika ban detected; aborting reminder run (%s)", error[:120])
                for leaf_item in group["leaves"]:
                    ReminderLog.objects.create(
                        leave=leaf_item["leave"], role=group["role"],
                        recipient=group["recipient"], target=group["target"],
                        message=message, status=status, error=error,
                        triggered_by=actor,
                    )
                break
            elif kind == "permanent":
                status = ReminderLog.Status.FAILED_PERMANENT
                failed += 1
            else:
                status = ReminderLog.Status.FAILED
                failed += 1

        for leaf_item in group["leaves"]:
            ReminderLog.objects.create(
                leave=leaf_item["leave"], role=group["role"],
                recipient=group["recipient"], target=group["target"],
                message=message, status=status, error=error,
                triggered_by=actor,
            )

    return {
        "sent": sent,
        "failed": failed,
        "skipped_duplicate": skipped_dup,
        "skipped_invalid": skipped_invalid,
        "skipped_no_phone": len(collection["missing"]),
        "aborted_rate_limited": aborted,
        "remaining_not_sent": remaining_after_abort,
    }
