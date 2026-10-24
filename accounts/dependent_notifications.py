"""SMS/Rubika notifications for the dependent-information workflow.

Sending is best-effort: a broken SMS gateway or an unreachable bot must never
break the user's submission or the HR decision.  Everything is wrapped in
try/except and logged.
"""

from __future__ import annotations

import logging

from .dependent_service import FIELD_LABELS, normalize_mobile

logger = logging.getLogger('accounts')

ACTION_LABELS = {
    'create': 'افزودن',
    'update': 'ویرایش',
    'delete': 'حذف',
}


def _personnel_name(profile) -> str:
    user = getattr(profile, 'user', None)
    if user is None:
        return 'همکار گرامی'
    return user.get_full_name() or user.username


def _display_name(change) -> str:
    data = change.new_data or change.old_data or {}
    name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    return name or 'فرد تحت تکفل'


def _send_sms(mobile: str, text: str) -> bool:
    mobile = normalize_mobile(mobile)
    if not mobile:
        return False
    try:
        from message_center.broadcast_service import _get_sms_client, _send_sms_numbers

        client = _get_sms_client()
        ok, error = _send_sms_numbers(client, [mobile], text)
        if not ok:
            logger.warning("[dependents] SMS failed to %s: %s", mobile, error)
        return ok
    except Exception:  # pragma: no cover - network/gateway failures
        logger.exception("[dependents] SMS exception for %s", mobile)
        return False


def _send_rubika(profile, text: str) -> bool:
    try:
        from rubika_bot.models import RubikaUser
        from rubika_bot.tasks import send_rubika_message

        rubika_user = RubikaUser.objects.filter(user=profile.user).first()
        if not rubika_user:
            return False
        send_rubika_message.delay(rubika_user.chat_id, text)
        return True
    except Exception:  # pragma: no cover - broker/bot failures
        logger.exception("[dependents] Rubika notification failed for %s", profile)
        return False


def notify_change_submitted(change) -> None:
    personnel = change.personnel
    action = ACTION_LABELS.get(change.action, 'تغییر')
    name = _display_name(change)
    text = (
        f"{_personnel_name(personnel)} عزیز،\n"
        f"درخواست {action} اطلاعات «{name}» با موفقیت ثبت شد.\n"
        f"کد پیگیری: {change.pk}\n"
        "پس از بررسی توسط منابع انسانی، نتیجه به شما اطلاع داده می‌شود."
    )
    _send_sms(personnel.mobile, text)
    _send_rubika(personnel, text)


def notify_change_reviewed(change) -> None:
    personnel = change.personnel
    action = ACTION_LABELS.get(change.action, 'تغییر')
    name = _display_name(change)
    if change.status == 'approved':
        text = (
            f"{_personnel_name(personnel)} عزیز،\n"
            f"درخواست {action} اطلاعات «{name}» تایید و در سامانه اعمال شد.\n"
            f"کد پیگیری: {change.pk}"
        )
    else:
        note = f"\nتوضیح: {change.review_note}" if change.review_note else ''
        text = (
            f"{_personnel_name(personnel)} عزیز،\n"
            f"درخواست {action} اطلاعات «{name}» رد شد.{note}\n"
            f"کد پیگیری: {change.pk}"
        )
    _send_sms(personnel.mobile, text)
    _send_rubika(personnel, text)


def field_label(field: str) -> str:
    return FIELD_LABELS.get(field, field)
