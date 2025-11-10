import logging
from typing import Iterable, Optional

from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse

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
            "Failed to create accounts notification",
            exc_info=True,
            extra={'user_id': getattr(user, 'id', None), 'title': title},
        )


def _profile_url(user: User) -> Optional[str]:
    if not hasattr(user, 'userprofile'):
        return None

    try:
        return reverse('accounts:profile')
    except NoReverseMatch:
        logger.warning("Profile URL reverse failed for user %s", getattr(user, 'id', None), exc_info=True)
        return None


def notify_profile_updated(user: User, *, actor: Optional[User] = None) -> None:
    _safe_notification(
        user=user,
        title='به‌روزرسانی اطلاعات کاربری',
        message='اطلاعات شخصی شما توسط مدیریت به‌روزرسانی شد.',
        notification_type='info',
        url=_profile_url(user),
        actor=actor,
    )


def notify_organizational_updated(user: User, *, actor: Optional[User] = None) -> None:
    _safe_notification(
        user=user,
        title='به‌روزرسانی اطلاعات سازمانی',
        message='اطلاعات سازمانی شما در سیستم تغییر کرد. لطفاً جزئیات جدید را بررسی کنید.',
        notification_type='info',
        url=_profile_url(user),
        actor=actor,
    )


def notify_password_reset(user: User, *, actor: Optional[User] = None) -> None:
    _safe_notification(
        user=user,
        title='تغییر رمز عبور',
        message='رمز عبور حساب شما توسط مدیریت تغییر داده شد. در اولین ورود آن را تغییر دهید.',
        notification_type='warning',
        url=None,
        actor=actor,
    )
