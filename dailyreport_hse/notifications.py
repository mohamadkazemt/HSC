import logging
from typing import Iterable, List, Optional

from django.contrib.auth.models import Group, User
from django.urls import reverse

from dashboard.notification_utils import safe_notification as _safe_notification


logger = logging.getLogger(__name__)


HSE_MANAGER_GROUPS = ['مدیر HSE']


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    """Get all active users from specified Django groups."""
    seen_ids = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for daily report notifications", group_name)
            continue

        for user in group.user_set.filter(is_active=True):
            if user.id in seen_ids:
                continue
            seen_ids.add(user.id)
            yield user


def notify_daily_report_created(daily_report, *, issues: List[str], actor: Optional[User] = None) -> None:
    """Send notification after a daily report is created.
    
    فقط به مدیران HSE که در گروه‌های Django تعریف شده‌اند اطلاع داده می‌شود.
    """
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

    # فقط به مدیران HSE اطلاع داده می‌شود
    for user in _notify_group_members(HSE_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='گزارش روزانه HSE',
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
        )
