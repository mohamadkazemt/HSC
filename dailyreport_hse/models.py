from django.db import models
from BaseInfo.models import MiningBlock, MiningMachine, Dump
from accounts.models import UserProfile  # Import UserProfile from your app
from django.contrib.auth.models import User

class DailyReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")
    report_time = models.TimeField(auto_now_add=True, verbose_name="زمان ثبت گزارش")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_reports", verbose_name="کاربر ایجاد کننده"
    )
    user_group = models.CharField(max_length=1,verbose_name="گروه کاری",editable=False)

    def save(self, *args, **kwargs):
        if not self.user_group and self.user:
            user_profile = UserProfile.objects.get(user=self.user)
            self.user_group = user_profile.group
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "گزارش روزانه"
        verbose_name_plural = "گزارش‌های روزانه"

    def __str__(self):
        return f"گزارش روزانه {self.id}"


class BlastingDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="blasting_details", verbose_name="گزارش روزانه")
    block = models.ForeignKey( MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بلوک آتشباری")
    status = models.BooleanField(default=False,verbose_name="وضعیت آتشباری" )
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات آتشباری")


class DrillingDetail(models.Model):
    daily_report = models.ForeignKey(DailyReport, on_delete=models.CASCADE, related_name="drilling_details", verbose_name="گزارش روزانه" )
    block = models.ForeignKey(MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بلوک حفاری")
    machine = models.ForeignKey(MiningMachine, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دستگاه حفاری" )
    status = models.CharField(
        max_length=10,
        choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')],
        verbose_name="وضعیت حفاری"
    )
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات حفاری")


class DumpDetail(models.Model):
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.CASCADE, related_name="dump_details", verbose_name="گزارش روزانه"
    )
    dump = models.ForeignKey(
        Dump, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="نام دامپ"
    )
    status = models.CharField(
        max_length=10,
        choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')],
        verbose_name="وضعیت دامپ"
    )
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات دامپ")


class LoadingDetail(models.Model):
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.CASCADE, related_name="loading_details", verbose_name="گزارش روزانه"
    )
    block = models.ForeignKey(
        MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بلوک بارگیری"
    )
    machine = models.ForeignKey(
        MiningMachine, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دستگاه بارگیری"
    )
    status = models.CharField(
        max_length=10,
        choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')],
        verbose_name="وضعیت بارگیری"
    )
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات بارگیری")


class InspectionDetail(models.Model):
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.CASCADE, related_name="inspection_details", verbose_name="گزارش روزانه"
    )
    status = models.BooleanField(default=False, verbose_name="بازدید انجام شده")
    status_detail = models.CharField(
        max_length=10,
        choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')],
        null=True,
        blank=True,
        verbose_name="وضعیت بازدید"
    )
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات بازدید")


class StoppageDetail(models.Model):
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.CASCADE, related_name="stoppage_details", verbose_name="گزارش روزانه"
    )
    reason = models.TextField(null=True, blank=True, verbose_name="علت توقف")
    duration = models.IntegerField(null=True, blank=True, verbose_name="مدت زمان توقف (دقیقه)")


class FollowupDetail(models.Model):
    daily_report = models.ForeignKey(
        DailyReport, on_delete=models.CASCADE, related_name="followup_details", verbose_name="گزارش روزانه"
    )
    description = models.TextField(null=True, blank=True, verbose_name="موارد پیگیری در شیفت بعد")
    files = models.FileField(upload_to='followups/', null=True, blank=True, verbose_name="فایل‌ها")