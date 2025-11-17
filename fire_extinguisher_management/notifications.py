import logging
from typing import Iterable, Optional

from django.contrib.auth import get_user_model
from django.urls import reverse

from dashboard.models import Notification
from dashboard.notification_utils import safe_notification as _safe_notification


logger = logging.getLogger(__name__)
User = get_user_model()


def notify_users(users: Iterable[object], *, title: str, message: str, notification_type: str = 'warning', url: Optional[str] = None) -> None:
    for user in users:
        _safe_notification(user=user, title=title, message=message, notification_type=notification_type, url=url, actor=None)


def notify_staff(*, title: str, message: str, notification_type: str = 'warning', url: Optional[str] = None) -> None:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    staff_users = User.objects.filter(is_staff=True, is_active=True)
    notify_users(staff_users, title=title, message=message, notification_type=notification_type, url=url)


def build_extinguisher_url(extinguisher) -> str:
    return reverse('fire_extinguisher_management:extinguisher_detail', args=[extinguisher.pk]) if extinguisher.pk else None
