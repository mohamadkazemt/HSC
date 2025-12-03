import logging
from typing import Iterable, List, Optional

from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import UserProfile
from dashboard.models import Notification


logger = logging.getLogger(__name__)


def _safe_notification(
    *,
    user: Optional[User],
    title: str,
    message: str,
    notification_type: str,
    url: Optional[str],
    actor: Optional[User],
) -> None:
    if not user:
        return

    if actor and actor == user:
        return

    try:
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
    except Exception as exc:  # pragma: no cover
        logger.error(
            "Failed to create operations shift report notification",
            exc_info=True,
            extra={'user_id': getattr(user, 'id', None), 'title': title},
        )


def _get_group_users(group_code: Optional[str]) -> Iterable[User]:
    if not group_code:
        return []
    profiles = UserProfile.objects.filter(group=group_code, user__is_active=True).select_related('user')
    return [profile.user for profile in profiles]


def _get_operations_staff() -> Iterable[User]:
    return User.objects.filter(is_staff=True, is_active=True)


def notify_shift_report_created(shift_report, *, inactive_loaders: List[dict], actor: Optional[User] = None) -> None:
    """Send notification when shift report is created.
    
    فقط به افرادی که مرتبط هستند اطلاع داده می‌شود:
    - نویسنده گزارش
    - اعضای گروه کاری مرتبط
    """
    url = reverse('OperationsShiftReports:shift_report_detail', args=[shift_report.id]) if shift_report.id else None
    date = shift_report.shift_date.strftime('%Y/%m/%d') if shift_report.shift_date else 'نامشخص'
    base_message = f'گزارش شیفت گروه {shift_report.group} برای تاریخ {date} ثبت شد.'

    if inactive_loaders:
        loader_texts = []
        for loader in inactive_loaders[:3]:
            loader_texts.append(f"{loader['loader']} ({loader['block']})")
        if len(inactive_loaders) > 3:
            loader_texts.append('...')
        base_message += ' بارکننده‌های غیرفعال: ' + ' ؛ '.join(loader_texts)
        notification_type = 'warning'
    else:
        notification_type = 'info'

    recipients = set()

    # اعضای گروه کاری
    for user in _get_group_users(shift_report.group):
        recipients.add(user)

    # نویسنده گزارش (عموما از همین گروه هست اما برای اطمینان)
    if hasattr(shift_report, 'user') and shift_report.user:
        recipients.add(shift_report.user)

    for user in recipients:
        _safe_notification(
            user=user,
            title='گزارش شیفت عملیات',
            message=base_message,
            notification_type=notification_type,
            url=url,
            actor=actor,
        )
