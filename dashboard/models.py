from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone





class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)  # اضافه کردن فیلد url
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)  # اضافه کردن زمان خوانده شدن
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده‌شده و ثبت زمان خواندن"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    def __str__(self):
        return f'Notification for {self.user.username}: {self.message}'
