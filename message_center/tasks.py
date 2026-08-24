from celery import shared_task

from .services import send_pending_reminders


@shared_task
def send_leave_reminders_task(role=None, actor_id=None):
    from django.contrib.auth.models import User

    actor = User.objects.filter(pk=actor_id).first() if actor_id else None
    return send_pending_reminders(role=role, actor=actor)
