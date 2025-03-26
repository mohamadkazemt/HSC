from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone





class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)  # اضافه کردن فیلد url
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)  # اضافه کردن زمان خوانده شدن
    created_at = models.DateTimeField(auto_now_add=True)
    meeting = models.ForeignKey('meetings.Meeting', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده‌شده و ثبت زمان خواندن"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message}'


# dashboard/models.py


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField()
    auth_key = models.CharField(max_length=255)
    p256dh_key = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push Subscription for {self.user.username}"
    






class UserActivity(models.Model):
    """مدل برای ذخیره فعالیت‌های کاربر"""
    
    # انواع فعالیت‌ها
    ACTIVITY_TYPES = (
        ('login', 'ورود به سیستم'),
        ('logout', 'خروج از سیستم'),
        ('create', 'ایجاد'),
        ('update', 'بروزرسانی'),
        ('delete', 'حذف'),
        ('view', 'مشاهده'),
        ('other', 'سایر'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    related_model = models.CharField(max_length=100, blank=True, null=True)  # نام مدل مرتبط
    related_object_id = models.PositiveIntegerField(blank=True, null=True)  # شناسه شیء مرتبط
    url = models.URLField(blank=True, null=True)  # لینک مرتبط با فعالیت
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # آدرس IP کاربر
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'فعالیت کاربر'
        verbose_name_plural = 'فعالیت‌های کاربر'
    
    def __str__(self):
        return f'{self.user.username} - {self.get_activity_type_display()} - {self.created_at}'