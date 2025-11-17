import logging
from typing import Iterable, Optional

from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse

from dashboard.models import Notification


logger = logging.getLogger(__name__)


from dashboard.notification_utils import safe_notification as _safe_notification


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
