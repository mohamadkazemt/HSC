from celery import shared_task

from .services import send_pending_reminders


@shared_task
def send_leave_reminders_task(role=None, actor_id=None):
    from django.contrib.auth.models import User

    actor = User.objects.filter(pk=actor_id).first() if actor_id else None
    return send_pending_reminders(role=role, actor=actor)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_broadcast_task(self, broadcast_id: int):
    """ارسال یک پیام گروهی در پس‌زمینه (متناسب با زمان‌بندی یا ارسال فوری)."""
    from .broadcast_service import execute_broadcast, mark_invalid_recipients_canceled
    from .models import Broadcast

    try:
        broadcast = Broadcast.objects.get(pk=broadcast_id)
    except Broadcast.DoesNotExist:
        self.logger.error("Broadcast %s not found", broadcast_id)
        return {"status": "not_found"}

    if broadcast.status != Broadcast.Status.SCHEDULED and broadcast.status != Broadcast.Status.DRAFT:
        # از اجرای دوباره پرهیز کن (قبلاً اجرا/لغو شده)
        if broadcast.status not in (Broadcast.Status.RESOLVED,):
            return {"status": "already_done", "current": broadcast.status}

    mark_invalid_recipients_canceled(broadcast)
    try:
        ok = execute_broadcast(broadcast)
        return {"status": "done", "ok": ok, "id": broadcast_id}
    except Exception as exc:
        self.logger.exception("Broadcast %s failed", broadcast_id)
        try:
            broadcast.status = Broadcast.Status.FAILED
            broadcast.error = str(exc)
            broadcast.save(update_fields=["status", "error"])
        except Exception:
            pass
        try_count = self.request.retries + 1
        if try_count >= self.max_retries:
            return {"status": "failed", "error": str(exc), "id": broadcast_id}
        raise self.retry(exc=exc)
