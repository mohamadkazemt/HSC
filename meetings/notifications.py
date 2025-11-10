import logging
from typing import Iterable, Optional

from django.contrib.auth.models import User
from django.urls import reverse

from dashboard.models import Notification

from .services import MeetingService


logger = logging.getLogger(__name__)


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
        logger.error("Failed to create meeting notification", exc_info=True, extra={'context': extra})


def _meeting_url(meeting) -> str:
    return reverse('meetings:meeting_detail', args=[meeting.id])


def _notify_participants(meeting, *, title: str, message: str, notification_type: str, actor: Optional[User]) -> None:
    url = _meeting_url(meeting)
    for participant in meeting.participants.all():
        _safe_notification(
            user=participant,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            context={'meeting_id': meeting.id, 'target': 'participant'},
        )


def _notify_transport_coordinators(meeting, *, title: str, message: str, notification_type: str, actor: Optional[User]) -> None:
    if not meeting.notify_transport_coordinator:
        return

    url = _meeting_url(meeting)
    for coordinator in MeetingService.get_transport_coordinators():
        _safe_notification(
            user=coordinator,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
            actor=actor,
            context={'meeting_id': meeting.id, 'target': 'transport_coordinator'},
        )


def notify_meeting_updated(meeting, *, actor: Optional[User] = None) -> None:
    message = f'برنامه جلسه "{meeting.title}" برای تاریخ {meeting.date} و ساعت {meeting.start_time} بروزرسانی شد.'
    _notify_participants(meeting, title='بروزرسانی جلسه', message=message, notification_type='info', actor=actor)
    _notify_transport_coordinators(meeting, title='بروزرسانی جلسه', message=message, notification_type='info', actor=actor)


def notify_meeting_cancelled(meeting, *, reason: str, actor: Optional[User] = None) -> None:
    message = f'جلسه "{meeting.title}" که برای تاریخ {meeting.date} برنامه‌ریزی شده بود لغو شد. دلیل: {reason}.'
    _notify_participants(meeting, title='لغو جلسه', message=message, notification_type='warning', actor=actor)
    _notify_transport_coordinators(meeting, title='لغو جلسه', message=message, notification_type='warning', actor=actor)


def notify_meeting_deleted(meeting, *, actor: Optional[User] = None) -> None:
    message = f'جلسه "{meeting.title}" حذف شد و دیگر برگزار نخواهد شد.'
    _notify_participants(meeting, title='حذف جلسه', message=message, notification_type='error', actor=actor)
    _notify_transport_coordinators(meeting, title='حذف جلسه', message=message, notification_type='error', actor=actor)
