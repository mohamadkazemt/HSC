"""ابزار مرکزی اعلان‌ها برای جلوگیری از تکرار _safe_notification در هر اپ.

ویژگی‌ها:
- جلوگیری از اعلان به actor (مگر skip_actor_check=True)
- لاگ ساخت اعلان یا خطا بدون توقف جریان اصلی
- امکان توسعه برای صف آسنکرون (Celery) در آینده
- API یکنواخت

نمونه استفاده:
    from dashboard.notification_utils import safe_notification
    safe_notification(user=request.user, title="پیام", message="متن", notification_type="info")

پیکربندی:
    می‌توانید در settings.py ثابت های زیر را تعریف کنید:
        NOTIFICATION_SKIP_ACTOR_DEFAULT = True

"""
from __future__ import annotations

import logging
from typing import Optional
from django.contrib.auth import get_user_model
from django.conf import settings

from dashboard.models import Notification

logger = logging.getLogger(__name__)

User = get_user_model()


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.contrib.auth.models import User

def safe_notification(
    *,
    user: Optional[object],
    title: str,
    message: str,
    notification_type: str = 'info',
    url: Optional[str] = None,
    actor: Optional[object] = None,
    skip_actor_check: bool = False,
    extra_log_context: Optional[dict] = None,
) -> bool:
    """ارسال اعلان ایمن.

    بازگشت True در صورت تلاش موفق برای ایجاد، False در صورت رد یا خطا.
    خطاها لاگ می‌شوند و استثناء پرتاب نمی‌شود.
    """
    if not user:
        logger.debug("[NOTIF] Skipped: user is None (title=%s)", title)
        return False

    # سیاست پیش‌فرض می‌تواند از settings کنترل شود
    global_skip_actor_default = getattr(settings, 'NOTIFICATION_SKIP_ACTOR_DEFAULT', True)
    effective_skip_check = skip_actor_check is False and global_skip_actor_default is True

    if effective_skip_check and actor and actor == user:
        logger.debug("[NOTIF] Skipped: actor == user (user=%s, title=%s)", user.username, title)
        return False

    try:
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
        logger.info("[NOTIF] Created (id=%s user=%s type=%s title=%s)", notif.id, user.username, notification_type, title)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        ctx = extra_log_context or {}
        ctx.update({'user_id': getattr(user, 'id', None), 'title': title})
        logger.error("[NOTIF] Failed to create", exc_info=True, extra={'context': ctx})
        return False

__all__ = ["safe_notification"]
