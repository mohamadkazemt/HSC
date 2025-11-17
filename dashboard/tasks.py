"""Celery tasks for dashboard utilities (SMS / Notifications / Cleanup).

هدف: جدا کردن لایه آسنکرون از منطق سینکرون و افزودن قابلیت retry با backoff.

نکته: برای فعال بودن این تسک‌ها باید celery worker در حال اجرا باشد.
نمونه اجرا (در پاورشل ویندوز):
    celery -A HSCprojects worker -l info

در صورت نیاز می‌توان max_retries و delay را بر اساس نوع خطا تنظیم کرد.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
import random
from typing import List, Dict, Any

from .sms_utils import send_template_sms

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_template_sms_task(self, mobile_number: str, template_id: int, parameters: List[Dict[str, Any]]):
    """ارسال پیامک قالبی با قابلیت retry آسنکرون.

    اگر ارسال موفق نبود، به صورت کنترل‌شده retry می‌شود.
    """
    logger.info(f"[SMS][TASK] شروع ارسال پیامک آسنکرون به {mobile_number} (template={template_id})")
    try:
        ok = send_template_sms(mobile_number, template_id, parameters)
        if ok:
            logger.info(f"[SMS][TASK] پیامک با موفقیت ارسال شد به {mobile_number}")
            return {'status': 'sent'}
        else:
            raise RuntimeError('ارسال پیامک ناموفق بود')
    except Exception as exc:
        try_count = self.request.retries + 1
        if try_count >= self.max_retries:
            logger.error(f"[SMS][TASK] شکست نهایی در ارسال پیامک به {mobile_number}: {exc}")
            return {'status': 'failed', 'error': str(exc)}
        countdown = 20 + random.randint(0, 20)
        logger.warning(f"[SMS][TASK] تلاش {try_count} ناموفق؛ retry بعدی در {countdown}s برای {mobile_number}")
        raise self.retry(exc=exc, countdown=countdown)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def create_notification_task(self, user_id: int, title: str, message: str, notification_type: str = 'info', url: str = None):
    """ایجاد اعلان در پس‌زمینه؛ در صورت نیاز به صف‌های زیاد، می‌توان batching افزود."""
    from django.contrib.auth import get_user_model
    from dashboard.models import Notification

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"[NOTIF][TASK] کاربر با id={user_id} یافت نشد")
        return {'status': 'user_not_found'}

    try:
        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            url=url,
        )
        logger.info(f"[NOTIF][TASK] اعلان ایجاد شد (id={notif.id}, user={user.username})")
        return {'status': 'created', 'id': notif.id}
    except Exception as exc:
        try_count = self.request.retries + 1
        if try_count >= self.max_retries:
            logger.error(f"[NOTIF][TASK] شکست نهایی در ایجاد اعلان برای user_id={user_id}: {exc}")
            return {'status': 'failed', 'error': str(exc)}
        logger.warning(f"[NOTIF][TASK] خطا در ایجاد اعلان؛ تلاش {try_count}; retry در {self.default_retry_delay}s")
        raise self.retry(exc=exc)


@shared_task
def cleanup_old_notifications():
    """پاکسازی اعلان‌های قدیمی (خوانده شده یا قدیمی‌تر از X روز).
    
    این تسک را می‌توانید در celery beat برای اجرای دوره‌ای تنظیم کنید:
    settings.py:
        from celery.schedules import crontab
        CELERY_BEAT_SCHEDULE = {
            'cleanup-notifications-weekly': {
                'task': 'dashboard.tasks.cleanup_old_notifications',
                'schedule': crontab(day_of_week=1, hour=2, minute=0),
            },
        }
    """
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    from dashboard.models import Notification

    retention_days = getattr(settings, 'NOTIFICATION_RETENTION_DAYS', 90)
    cutoff_date = timezone.now() - timedelta(days=retention_days)
    
    deleted_read, _ = Notification.objects.filter(is_read=True, read_at__lt=cutoff_date).delete()
    
    very_old_cutoff = timezone.now() - timedelta(days=retention_days * 2)
    deleted_unread, _ = Notification.objects.filter(is_read=False, created_at__lt=very_old_cutoff).delete()
    
    total = deleted_read + deleted_unread
    logger.info(f"[CLEANUP] پاک‌سازی اعلان‌ها: {deleted_read} خوانده‌شده، {deleted_unread} خوانده‌نشده؛ جمع {total}")
    return {'deleted_read': deleted_read, 'deleted_unread': deleted_unread, 'total': total}


__all__ = [
    'send_template_sms_task',
    'create_notification_task',
    'cleanup_old_notifications',
]
