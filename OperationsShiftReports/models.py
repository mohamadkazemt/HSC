from django.db import models
from shift_manager.utils import get_shift_for_date
from accounts.models import UserProfile


# مدل شیفت برای هر عملیات بارگیری
class LoadingOperation(models.Model):
    stone_type_list = [
        ('w', 'باطله'),
        ('O', 'آهن'),
        ('T', 'آهن کم عیار')
    ]

    stone_type = models.CharField(max_length=50, verbose_name="نوع سنگ", choices=stone_type_list, default='w')
    load_count = models.IntegerField(verbose_name="تعداد بار", default=0)

    def __str__(self):
        return f"{self.stone_type} - {self.load_count} بار"


# مدل مرخصی شیفت
class ShiftLeave(models.Model):
    personnel_name = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    leave_status = models.CharField(max_length=50, choices=[('authorized', 'مجاز'), ('unauthorized', 'غیر مجاز')], default= 'unauthorized', verbose_name="وضعیت مرخصی")

    def __str__(self):
        return f"{self.personnel_name} - {self.get_leave_status_display()}"


# مدل برای گزارش خودروها
class VehicleReport(models.Model):
    vehicle_name = models.CharField(max_length=100, verbose_name="نام خودرو")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    inactive_time_start = models.TimeField(null=True, blank=True, verbose_name="زمان شروع غیر فعال بودن")
    inactive_time_end = models.TimeField(null=True, blank=True, verbose_name="زمان پایان غیر فعال بودن")

    def __str__(self):
        return f"{self.vehicle_name} - {'فعال' if self.is_active else 'غیر فعال'}"


# مدل برای دستگاه‌های معدنی
class MiningMachineReport(models.Model):
    machine_name = models.CharField(max_length=100, verbose_name="نام دستگاه")
    machine_type = models.CharField(max_length=50, verbose_name="نوع دستگاه")
    block = models.CharField(max_length=100, verbose_name="نام بلوک")

    def __str__(self):
        return f"{self.machine_name} - {self.machine_type} در بلوک {self.block}"





class ShiftReport(models.Model):
    shift_date = models.DateField(verbose_name="تاریخ شیفت")
    supervisor_comments = models.TextField(blank=True, verbose_name="توضیحات سرشیفت")
    group = models.CharField(max_length=1, choices=UserProfile.GROUP_CHOICES, verbose_name="گروه کاری")
    attached_file = models.FileField(upload_to='shift_reports', blank=True, verbose_name="فایل ضمیمه")
    loading_operations = models.ManyToManyField('LoadingOperation', related_name='shift_reports', blank=True)
    shift_leaves = models.ManyToManyField('ShiftLeave', related_name='shift_reports', blank=True)
    vehicle_reports = models.ManyToManyField('VehicleReport', related_name='shift_reports', blank=True)

    def __str__(self):
        return f"شیفت {self.get_group_display()} - {self.shift_date}"

    class Meta:
        verbose_name = 'گزارش شیفت'
        verbose_name_plural = 'گزارشات شیفت'