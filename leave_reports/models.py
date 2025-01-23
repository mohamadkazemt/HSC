from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from accounts.models import UserProfile
from django.core.exceptions import ValidationError


class ShiftReport(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('regular', 'مرخصی'),
        ('absence', 'غیبت'),
        ('hourly', 'مرخصی ساعتی'),
        ('sick_leave', 'مرخصی استعلاجی')
    ]
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shift_date = models.DateField(default=now)
    leave_hours = models.IntegerField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, default='reported')
    crate_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    work_group = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)  # توضیحات برای غیبت و استعلاجی

    def clean(self):
        # بررسی تکراری بودن گزارش برای یک کاربر در یک تاریخ خاص
        existing_report = ShiftReport.objects.filter(
            user=self.user,
            shift_date=self.shift_date
        ).exclude(pk=self.pk).first()  # تغییر برای دریافت شیء

        if existing_report:
            raise ValidationError(
                f'برای کاربر {self.user.get_full_name()} در تاریخ {self.shift_date} قبلا گزارش ثبت شده است.')

    def save(self, *args, **kwargs):
        self.full_clean()  # اعتبارسنجی قبل از ذخیره
        super(ShiftReport, self).save(*args, **kwargs)