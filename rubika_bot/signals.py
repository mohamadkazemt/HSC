import logging

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from dashboard.models import Notification

from .tasks import send_rubika_message

logger = logging.getLogger(__name__)

# These notifications are already delivered by the interactive Rubika task.
INTERACTIVE_NOTIFICATION_TITLES = {
    'درخواست جایگزینی مرخصی',
    'درخواست تأیید مرخصی',
}

TYPE_ICONS = {
    'info': 'ℹ️',
    'success': '✅',
    'warning': '⚠️',
    'error': '❌',
    'meeting': '📅',
}


def format_notification_message(notification: Notification) -> str:
    """Build the plain-text representation sent to Rubika."""
    lines = []
    if notification.title:
        icon = TYPE_ICONS.get(notification.notification_type, TYPE_ICONS['info'])
        lines.extend([f'{icon} {notification.title}', ''])
    lines.append(notification.message)
    if notification.url:
        lines.extend(['', 'برای مشاهده جزئیات به پنل وب مراجعه کنید.'])
    return '\n'.join(lines)


def queue_notification_to_rubika(notification: Notification) -> bool:
    """Queue one persisted notification for its linked Rubika user."""
    if notification.title in INTERACTIVE_NOTIFICATION_TITLES:
        logger.debug(
            "Notification %s uses the interactive Rubika delivery path",
            notification.pk,
        )
        return False

    profile = getattr(notification.user, 'rubika_profile', None)
    if not profile or not profile.chat_id:
        logger.debug(
            "User %s has no linked Rubika chat; notification %s stays in-app only",
            notification.user_id,
            notification.pk,
        )
        return False

    chat_id = str(profile.chat_id)
    text = format_notification_message(notification)

    def enqueue() -> None:
        try:
            send_rubika_message.delay(chat_id, text)
        except Exception:
            # Notification persistence must never depend on broker availability.
            logger.exception(
                "Could not enqueue Rubika delivery for notification %s",
                notification.pk,
            )

    transaction.on_commit(enqueue)
    return True


@receiver(
    post_save,
    sender=Notification,
    dispatch_uid='rubika_bot.notification_delivery',
)
def send_notification_to_rubika(sender, instance: Notification, created, **kwargs):
    """Deliver every newly-created dashboard notification to its linked user."""
    if created:
        queue_notification_to_rubika(instance)
