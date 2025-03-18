from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from dashboard.models import Notification

class Meeting(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'برنامه‌ریزی شده'),
        ('cancelled', 'لغو شده'),
        ('completed', 'برگزار شده'),
    ]

    title = models.CharField(max_length=200, verbose_name='عنوان جلسه')
    date = models.DateField(verbose_name='تاریخ')
    time = models.TimeField(verbose_name='ساعت')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meetings', verbose_name='ایجادکننده')
    participants = models.ManyToManyField(User, related_name='participated_meetings', verbose_name='شرکت‌کنندگان')
    manual_numbers = models.TextField(blank=True, null=True, verbose_name='شماره‌های دستی')
    notify_transport_coordinator = models.BooleanField(default=False, verbose_name='اعلام به هماهنگ‌کننده حمل و نقل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='وضعیت جلسه')
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name='دلیل لغو')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'جلسه'
        verbose_name_plural = 'جلسات'
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.title} - {self.date}"
