import logging
from typing import Iterable, Optional

from django.contrib.auth.models import Group, User
from django.urls import reverse

from accounts.models import UserProfile
from dashboard.models import Notification


logger = logging.getLogger(__name__)


MANAGER_GROUPS = ['مدیر HSE']


def _safe_notification(
    *,
    user: Optional[User],
    title: str,
    message: str,
    notification_type: str = 'info',
    url: Optional[str] = None,
    actor: Optional[User] = None,
    context: Optional[dict] = None,
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
        extra = context or {}
        extra.update({'user_id': getattr(user, 'id', None), 'title': title})
        logger.error("Failed to create fire report notification", exc_info=True, extra={'context': extra})


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    seen = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for fire report notifications", group_name)
            continue

        for user in group.user_set.all():
            if user.id in seen:
                continue
            seen.add(user.id)
            yield user


def _get_hsec_head_user() -> Optional[User]:
    profile = UserProfile.objects.filter(position__name='رئیس HSEC').select_related('user').first()
    return profile.user if profile else None


def _report_url(report) -> str:
    return reverse('fire_reports:report_detail', args=[report.id])


def _has_unsuitable_status(report) -> bool:
    status_fields = [
        report.horn_status,
        report.hose_status,
        report.monitor_status,
        report.extinguisher_status,
        report.equipment_status,
        report.foam_status,
        report.water_status,
        report.tire_status,
        report.brake_status,
        report.lighting_status,
    ]

    if any(status == 'unsuitable' for status in status_fields if status):
        return True

    for checklist in report.vehicle_checklists.all():
        checklist_statuses = [
            checklist.horn_status,
            checklist.hose_status,
            checklist.monitor_status,
            checklist.extinguisher_status,
            checklist.equipment_status,
            checklist.foam_status,
            checklist.water_status,
            checklist.tire_status,
            checklist.brake_status,
            checklist.lighting_status,
        ]
        if any(status == 'unsuitable' for status in checklist_statuses if status):
            return True
    return False


def notify_fire_report_created(report, *, actor: Optional[User] = None) -> None:
    """Notify stakeholders when a new fire report is submitted."""

    url = _report_url(report)
    has_issue = _has_unsuitable_status(report)
    message_base = f'گزارش آتش‌نشانی شماره {report.id} توسط {report.firefighter.get_full_name() if report.firefighter else "کاربر"} ثبت شد.'

    # Notify shift operator
    shift_operator_user = report.shift_operator
    _safe_notification(
        user=shift_operator_user,
        title='ثبت گزارش آتش‌نشانی',
        message=message_base,
        notification_type='info',
        url=url,
        actor=actor,
        context={'report_id': report.id, 'target': 'shift_operator'},
    )

    # Notify managers
    notification_type = 'warning' if has_issue else 'info'
    manager_message = message_base
    if has_issue:
        manager_message += ' وضعیت تجهیزات نامناسب گزارش شده است.'

    for user in _notify_group_members(MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='ثبت گزارش آتش‌نشانی',
            message=manager_message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            context={'report_id': report.id, 'target_group': 'HSE'},
        )

    # Notify HSEC head if there are issues
    if has_issue:
        hsec_head = _get_hsec_head_user()
        _safe_notification(
            user=hsec_head,
            title='🚨 گزارش آتش‌نشانی با تجهیزات نامناسب',
            message=f'در گزارش آتش‌نشانی شماره {report.id} وضعیت نامناسب تجهیزات ثبت شده است.',
            notification_type='error',
            url=url,
            actor=actor,
            context={'report_id': report.id, 'target': 'HSEC_head'},
        )


def notify_fire_report_approval(report, *, actor: Optional[User] = None) -> None:
    """Notify relevant users when a fire report is approved."""

    url = _report_url(report)
    message = f'گزارش آتش‌نشانی شماره {report.id} تأیید شد.'

    _safe_notification(
        user=report.firefighter,
        title='گزارش تأیید شد',
        message=message,
        notification_type='success',
        url=url,
        actor=actor,
        context={'report_id': report.id, 'target': 'firefighter'},
    )

    hsec_head = _get_hsec_head_user()
    _safe_notification(
        user=hsec_head,
        title='تأیید گزارش آتش‌نشانی',
        message=message,
        notification_type='info',
        url=url,
        actor=actor,
        context={'report_id': report.id, 'target': 'HSEC_head'},
    )


def notify_fire_report_rejection(report, *, reason: str, actor: Optional[User] = None) -> None:
    """Notify firefighter and managers when a report is rejected."""

    url = _report_url(report)
    message = f'گزارش آتش‌نشانی شماره {report.id} رد شد. دلیل: {reason}'

    _safe_notification(
        user=report.firefighter,
        title='گزارش رد شد',
        message=message,
        notification_type='error',
        url=url,
        actor=actor,
        context={'report_id': report.id, 'target': 'firefighter'},
    )

    for user in _notify_group_members(MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='رد گزارش آتش‌نشانی',
            message=message,
            notification_type='warning',
            url=url,
            actor=actor,
            context={'report_id': report.id, 'target_group': 'HSE'},
        )
