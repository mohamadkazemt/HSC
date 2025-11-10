import logging
from typing import Iterable, List, Optional

from django.contrib.auth.models import User
from django.urls import reverse

from accounts.models import UserProfile
from dashboard.models import Notification


logger = logging.getLogger(__name__)


HSE_MANAGER_GROUPS = ['مدیر HSE']


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
            "Failed to create daily report notification",
            exc_info=True,
            extra={'user_id': getattr(user, 'id', None), 'title': title},
        )


def _get_group_users(group_code: Optional[str]) -> Iterable[User]:
    if not group_code:
        return []
    profiles = UserProfile.objects.filter(group=group_code, user__is_active=True).select_related('user')
    return [profile.user for profile in profiles]


def _get_hse_managers() -> Iterable[User]:
    profiles = UserProfile.objects.filter(user__is_active=True, user__groups__name__in=HSE_MANAGER_GROUPS).select_related('user')
    return [profile.user for profile in profiles]


def notify_daily_report_created(daily_report, *, issues: List[str], actor: Optional[User] = None) -> None:
    url = reverse('dailyreport_hse:daily_report_detail', args=[daily_report.id]) if daily_report.id else None
    message = f'گزارش روزانه HSE گروه {daily_report.work_group} در شیفت {daily_report.shift} ثبت شد.'

    if issues:
        summary = ' ؛ '.join(issues[:3])
        if len(issues) > 3:
            summary += ' و ...'
        message += f' موارد نیازمند توجه: {summary}'
        notification_type = 'warning'
    else:
        notification_type = 'info'

    recipients = set()
    for user in _get_group_users(daily_report.work_group):
        recipients.add(user)
    for user in _get_hse_managers():
        recipients.add(user)

    recipients.add(daily_report.user)

    for user in recipients:
        _safe_notification(
            user=user,
            title='گزارش روزانه HSE',
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
        )
