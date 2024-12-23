from django.db import models
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from django.contrib.auth.models import User
from accounts.models import UserProfile

from django.db import models

class DailyReport(models.Model):
    SHIFT_CHOICES = [
        ('روزکار اول', 'روزکار اول'),
        ('روزکار دوم', 'روزکار دوم'),
        ('عصرکار اول', 'عصرکار اول'),
        ('عصرکار دوم', 'عصرکار دوم'),
        ('شب کار اول', 'شب کار اول'),
        ('شب کار دوم', 'شب کار دوم'),
        ('OFF اول', 'OFF اول'),
        ('OFF دوم', 'OFF دوم'),
    ]
    GROUP_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="افسر ایمنی")
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, verbose_name="شیفت کاری")
    work_group = models.CharField(max_length=1, choices=GROUP_CHOICES, verbose_name="گروه کاری")
    supervisor_comments = models.TextField(blank=True, verbose_name="توضیحات سرشیفت")

    def __str__(self):
        return f"گزارش {self.user.user} - {self.shift} - {self.created_at.date()}"


# جزئیات آتشباری
class BlastingDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="blasting_details")
    explosion_occurred = models.BooleanField(default=False, verbose_name="انفجار انجام شد؟")
    block = models.ForeignKey(MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بلوک آتشباری")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    def __str__(self):
        return f"آتشباری - بلوک: {self.block} - {self.explosion_occurred}"

# جزئیات حفاری
class DrillingDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="drilling_details")
    block = models.ForeignKey(MiningBlock, on_delete=models.SET_NULL, null=True, verbose_name="بلوک حفاری")
    machine = models.ForeignKey(MiningMachine, on_delete=models.SET_NULL, null=True, verbose_name="دستگاه حفاری")
    status = models.CharField(max_length=10, choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], verbose_name="وضعیت حفاری")

    def __str__(self):
        return f"حفاری - بلوک: {self.block} - دستگاه: {self.machine} - {self.status}"

# جزئیات تخلیه
class DumpDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="dump_details")
    dump = models.ForeignKey(Dump, on_delete=models.SET_NULL, null=True, verbose_name="دامپ")
    status = models.CharField(max_length=10, choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], verbose_name="وضعیت دامپ")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    def __str__(self):
        return f"تخلیه - دامپ: {self.dump} - {self.status}"

# جزئیات بارگیری
class LoadingDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="loading_details")
    block = models.ForeignKey(MiningBlock, on_delete=models.SET_NULL, null=True, verbose_name="بلوک بارگیری")
    machine = models.ForeignKey(MiningMachine, on_delete=models.SET_NULL, null=True, verbose_name="دستگاه بارگیری")
    status = models.CharField(max_length=10, choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], verbose_name="وضعیت بارگیری")

    def __str__(self):
        return f"بارگیری - بلوک: {self.block} - دستگاه: {self.machine} - {self.status}"

# جزئیات بازرسی
class InspectionDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="inspection_details")
    inspection_done = models.BooleanField(default=False, verbose_name="بازدید انجام شد؟")
    status = models.CharField(max_length=10, choices=[('safe', 'ایمن'), ('unsafe', 'ناایمن')], null=True, blank=True, verbose_name="وضعیت بازدید")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    def __str__(self):
        return f"بازرسی - انجام شده: {self.inspection_done} - وضعیت: {self.status}"

# جزئیات توقفات
class StoppageDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="stoppage_details")
    reason = models.TextField(verbose_name="علت توقف")
    start_time = models.TimeField(verbose_name="زمان شروع")
    end_time = models.TimeField(verbose_name="زمان پایان")
    description = models.TextField(blank=True, verbose_name="توضیحات")

    def __str__(self):
        return f"توقف - علت: {self.reason} - زمان: {self.start_time} تا {self.end_time}"

# جزئیات پیگیری
class FollowupDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="followup_details")
    description = models.TextField(verbose_name="توضیحات")
    files = models.FileField(upload_to='followups/%Y/%m/%d//', null=True, blank=True, verbose_name="فایل‌های پیوست")

    def __str__(self):
        return f"پیگیری - توضیحات: {self.description[:30]}..."
