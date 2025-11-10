import logging
from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.urls import reverse

from dashboard.models import Notification


logger = logging.getLogger(__name__)
User = get_user_model()


def _safe_notification(
    *,
    user,
    title: str,
    message: str,
    notification_type: str,
    url: Optional[str],
) -> None:
    if not user:
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
            "Failed to create fire extinguisher notification",
            exc_info=True,
            extra={'user_id': getattr(user, 'id', None), 'title': title},
        )


def notify_users(users: Iterable[User], *, title: str, message: str, notification_type: str = 'warning', url: Optional[str] = None) -> None:
    for user in users:
        _safe_notification(user=user, title=title, message=message, notification_type=notification_type, url=url)


def notify_staff(*, title: str, message: str, notification_type: str = 'warning', url: Optional[str] = None) -> None:
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    notify_users(staff_users, title=title, message=message, notification_type=notification_type, url=url)


def build_extinguisher_url(extinguisher) -> str:
    return reverse('fire_extinguisher_management:extinguisher_detail', args=[extinguisher.pk]) if extinguisher.pk else None
