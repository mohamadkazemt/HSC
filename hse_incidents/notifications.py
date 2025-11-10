import logging
from typing import Iterable, Optional

from django.contrib.auth.models import Group, User
from django.urls import reverse

from dashboard.models import Notification


logger = logging.getLogger(__name__)


INCIDENT_MANAGER_GROUPS = ['مدیر HSE']
INCIDENT_ESCALATION_GROUPS = ['افسر HSE', 'مدیر HSE']


def _safe_notification(
    *,
    user: Optional[User],
    title: str,
    message: str,
    notification_type: str = 'info',
    url: Optional[str] = None,
    actor: Optional[User] = None,
    extra: Optional[dict] = None,
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
        context = extra or {}
        context.update({'user_id': getattr(user, 'id', None), 'title': title})
        logger.error("Failed to create notification", exc_info=True, extra={'context': context})


def _notify_group_members(group_names: Iterable[str]) -> Iterable[User]:
    seen_ids = set()
    for group_name in group_names:
        try:
            group = Group.objects.get(name=group_name)
        except Group.DoesNotExist:
            logger.warning("Group '%s' not found for incident notifications", group_name)
            continue

        for user in group.user_set.all():
            if user.id in seen_ids:
                continue
            seen_ids.add(user.id)
            yield user


def _incident_url(incident) -> str:
    return reverse('hse_incidents:report_details', args=[incident.id])


def notify_incident_report_created(incident, *, actor: Optional[User] = None) -> None:
    """Notify key stakeholders that a new incident report has been created."""

    url = _incident_url(incident)
    location_name = incident.location.name if incident.location else 'محل نامشخص'
    severity = _determine_incident_severity(incident)

    base_title = 'گزارش حادثه جدید'
    base_message = (
        f'حادثه شماره {incident.id} در {location_name} ثبت شد. '
        f'گزارش دهنده: {incident.report_author.user.get_full_name() if incident.report_author else "نامشخص"}.'
    )

    notification_type = 'error' if severity == 'critical' else 'warning'

    for user in _notify_group_members(INCIDENT_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title=base_title,
            message=base_message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            extra={'incident_id': incident.id, 'severity': severity},
        )

    # Escalate for critical incidents
    if severity == 'critical':
        critical_message = (
            f'🚨 حادثه با شدت بالا شماره {incident.id} در {location_name} ثبت شد. '
            f'نیاز به اقدام فوری دارد.'
        )
        for user in _notify_group_members(INCIDENT_ESCALATION_GROUPS):
            _safe_notification(
                user=user,
                title='حادثه با اولویت بحرانی',
                message=critical_message,
                notification_type='error',
                url=url,
                actor=actor,
                extra={'incident_id': incident.id, 'severity': severity},
            )

    # Confirmation for the author
    author_user = incident.report_author.user if incident.report_author else None
    _safe_notification(
        user=author_user,
        title='ثبت گزارش حادثه',
        message=f'گزارش حادثه شما با شماره {incident.id} ثبت شد و در انتظار پیگیری است.',
        notification_type='success',
        url=url,
        actor=None,
        extra={'incident_id': incident.id, 'target': 'author_confirmation'},
    )


def notify_incident_completion(incident, *, actor: Optional[User] = None) -> None:
    """Notify stakeholders when an incident completion report is submitted."""

    url = _incident_url(incident)
    location_name = incident.location.name if incident.location else 'محل نامشخص'

    # Report author gets notified
    author_user = incident.report_author.user if incident.report_author else None
    _safe_notification(
        user=author_user,
        title='گزارش حادثه تکمیل شد',
        message=f'جزئیات تکمیلی حادثه شماره {incident.id} در {location_name} ثبت شد.',
        notification_type='success',
        url=url,
        actor=None,
        extra={'incident_id': incident.id, 'target': 'author'},
    )

    # Managers get notified
    for user in _notify_group_members(INCIDENT_MANAGER_GROUPS):
        _safe_notification(
            user=user,
            title='تکمیل گزارش حادثه',
            message=f'گزارش تکمیلی حادثه شماره {incident.id} ({location_name}) ثبت شد و نیاز به بررسی دارد.',
            notification_type='info',
            url=url,
            actor=actor,
            extra={'incident_id': incident.id, 'target_group': 'managers'},
        )


def _determine_incident_severity(incident) -> str:
    """Return 'critical' if incident contains critical attributes, otherwise 'standard'."""

    if incident.injury_type.exists():
        return 'critical'
    if incident.hospitalized or incident.ambulance_needed or incident.fire_truck_needed:
        return 'critical'
    return 'standard'
