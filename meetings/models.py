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
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]

    title = models.CharField(max_length=200, verbose_name='عنوان جلسه')
    date = models.DateField(verbose_name='تاریخ')
    start_time = models.TimeField(verbose_name='ساعت شروع')
    end_time = models.TimeField(verbose_name='ساعت پایان')
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name='مکان')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_meetings', verbose_name='ایجادکننده')
    participants = models.ManyToManyField(User, related_name='participated_meetings', verbose_name='شرکت‌کنندگان')
    manual_numbers = models.TextField(blank=True, null=True, verbose_name='شماره‌های دستی')
    notify_transport_coordinator = models.BooleanField(default=False, verbose_name='اعلام به هماهنگ‌کننده حمل و نقل')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='وضعیت جلسه')
    cancellation_reason = models.TextField(blank=True, null=True, verbose_name='دلیل لغو')
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت تأیید',
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_meetings',
        verbose_name='تأییدکننده',
    )
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name='زمان تأیید')
    rejection_reason = models.TextField(blank=True, verbose_name='دلیل رد')
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cancelled_meetings',
        verbose_name='لغوکننده',
    )
    cancelled_at = models.DateTimeField(blank=True, null=True, verbose_name='زمان لغو')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')

    class Meta:
        verbose_name = 'جلسه'
        verbose_name_plural = 'جلسات'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f"{self.title} - {self.date} - {self.start_time}"
