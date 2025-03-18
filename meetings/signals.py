from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Meeting, Notification
from .tasks import send_notification

@receiver(post_save, sender=Meeting)
def create_notifications(sender, instance, created, **kwargs):
    if created:
        # ارسال نوتیفیکیشن به تمام کاربران
        users = User.objects.all()
        for user in users:
            notification = Notification.objects.create(meeting=instance, user=user)
            send_notification.delay(user.id, instance.id) 