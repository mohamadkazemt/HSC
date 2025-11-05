from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Meeting
from dashboard.models import Notification

@receiver(post_save, sender=Meeting)
def create_notifications(sender, instance, created, **kwargs):
    if created:
        # ارسال نوتیفیکیشن فقط به شرکت‌کنندگان جلسه
        for participant in instance.participants.all():
            notification = Notification.objects.create(
                meeting=instance,
                user=participant,
                title='جلسه جدید',
                message=f'جلسه جدید "{instance.title}" ایجاد شد.',
                notification_type='meeting',
                url=f'/meetings/{instance.pk}/'
            )
            # send_notification.delay(user.id, instance.id)  # موقتاً غیرفعال شده 