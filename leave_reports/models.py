from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from accounts.models import UserProfile

class ShiftReport(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('regular', 'مرخصی'),
        ('absence', 'غیبت'),
        ('hourly', 'مرخصی ساعت')
    ]
    leave_type = models.CharField(max_length=10, choices=LEAVE_TYPE_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # کاربر (پرسنل)
    shift_date = models.DateField(default=now)  # مقدار پیش‌فرض تاریخ فعلی
    leave_hours = models.IntegerField(null=True, blank=True)  # ساعات مرخصی در صورت نیاز
    start_time = models.TimeField(null=True, blank=True)  # ساعت شروع در صورت مرخصی ساعتی
    end_time = models.TimeField(null=True, blank=True)  # ساعت پایان در صورت مرخصی ساعتی
    status = models.CharField(max_length=10, default='reported')  # وضعیت (گزارش‌شده یا پردازش‌شده)
    crate_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    work_group = models.CharField(max_length=100)  # فیلد گروه کاری
    created_at = models.DateTimeField(auto_now_add=True)  # تاریخ ثبت گزارش

    def save(self, *args, **kwargs):
        if not self.work_group:  # اگر گروه کاری مشخص نشده باشد
            self.work_group = self.user.userprofile.group  # گروه کاری بر اساس پروفایل کاربر
        super(ShiftReport, self).save(*args, **kwargs)
