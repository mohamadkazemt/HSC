from django.db.models.signals import post_save
from django.dispatch import receiver
from dashboard.models import Notification
from .tasks import send_rubika_message


@receiver(post_save, sender=Notification)
def send_notification_to_rubika(sender, instance: Notification, created, **kwargs):
    if not created:
        return
    user = instance.user
    profile = getattr(user, 'rubika_profile', None)
    if profile and profile.chat_id:
        text = instance.title + "\n" + instance.message if instance.title else instance.message
        send_rubika_message.delay(profile.chat_id, text)