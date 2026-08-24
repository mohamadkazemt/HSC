"""Central registration/approval window validation for leave requests.

All enforcement points (web form, model clean, approval views, Rubika bot
flows) must go through this module so the limits stay configurable from a
single place (LeaveSettings, editable in admin/panel). When the relevant
window is disabled in settings, no time restriction applies.
"""

from datetime import timedelta

import jdatetime

from django.utils import timezone


def _jalali(date_value):
    return jdatetime.date.fromgregorian(date=date_value).strftime("%Y/%m/%d")


def validate_submission_date(shift_date):
    """Return None when shift_date may be submitted, else a Persian error message."""
    from .models import LeaveSettings

    if shift_date is None:
        return None
    settings = LeaveSettings.load()
    if not settings.registration_window_enabled:
        return None

    today = timezone.now().date()

    max_registration_date = shift_date + timedelta(days=settings.registration_max_days_after)
    if today > max_registration_date:
        return (
            f"مهلت ثبت این درخواست به پایان رسیده است. "
            f"تاریخ مرخصی: {_jalali(shift_date)}، "
            f"آخرین مهلت ثبت: {_jalali(max_registration_date)}"
        )

    max_future_date = today + timedelta(days=settings.registration_max_days_future)
    if shift_date > max_future_date:
        return (
            f"شما فقط تا {settings.registration_max_days_future} روز آینده می‌توانید درخواست ثبت کنید. "
            f"حداکثر تاریخ مجاز: {_jalali(max_future_date)}"
        )

    return None


def validate_approval_deadline(shift_date):
    """Return None when the request may still be approved, else a Persian error message."""
    from .models import LeaveSettings

    if shift_date is None:
        return None
    settings = LeaveSettings.load()
    if not settings.approval_window_enabled:
        return None

    today = timezone.now().date()
    max_allowed_date = shift_date + timedelta(days=settings.approval_max_days)
    if today > max_allowed_date:
        return (
            f"مهلت تأیید این درخواست به پایان رسیده است. "
            f"تاریخ مرخصی: {_jalali(shift_date)}، "
            f"آخرین مهلت تأیید: {_jalali(max_allowed_date)}"
        )

    return None
