from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Meeting, Notification

@receiver(post_save, sender=Meeting)
def create_notifications(sender, instance, created, **kwargs):
    if created:
        # ارسال نوتیفیکیشن فقط به شرکت‌کنندگان جلسه
        for participant in instance.participants.all():
            notification = Notification.objects.create(
                meeting=instance,
                user=participant,
                message=f'جلسه جدید "{instance.title}" ایجاد شد.'
            )
            # send_notification.delay(user.id, instance.id)  # موقتاً غیرفعال شده 