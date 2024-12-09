from django.db import models
from BaseInfo.models import MiningBlock, MiningMachine, Dump


class ShiftReport(models.Model):
    shift_date = models.DateField(verbose_name="تاریخ شیفت")
    shift_time = models.CharField(
        max_length=50, choices=[('Day', 'روز'), ('Night', 'شب')], verbose_name="شیفت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد گزارش")

    def __str__(self):
        return f"گزارش {self.shift_date} - {self.shift_time}"

    class Meta:
        verbose_name = "گزارش روزانه"
        verbose_name_plural = "گزارش‌های روزانه"


class BlastingOperation(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="blasting_operations"
    )
    blasting_done = models.BooleanField(
        default=False, verbose_name="آیا انفجار انجام شده است؟"
    )
    block = models.ForeignKey(
        MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بلوک آتش‌باری"
    )

    class Meta:
        verbose_name = "عملیات آتش‌باری"
        verbose_name_plural = "عملیات‌های آتش‌باری"


class DrillingOperation(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="drilling_operations"
    )
    site = models.ForeignKey(
        MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سایت حفاری"
    )
    machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="دستگاه حفاری",
    )
    approved = models.BooleanField(default=True, verbose_name="وضعیت تایید سایت")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "عملیات حفاری"
        verbose_name_plural = "عملیات‌های حفاری"


class LoadingOperation(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="loading_operations"
    )
    workface = models.ForeignKey(
        MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="جبهه کاری"
    )
    dump = models.ForeignKey(
        Dump, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="دمپ"
    )
    approved = models.BooleanField(default=True, verbose_name="وضعیت تایید")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "عملیات بارگیری"
        verbose_name_plural = "عملیات‌های بارگیری"


class WorkshopInspection(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="workshop_inspections"
    )
    inspection_done = models.BooleanField(
        default=False, verbose_name="آیا بازدید انجام شده است؟"
    )
    approved = models.BooleanField(default=True, verbose_name="وضعیت تایید")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "بازدید تعمیرگاه"
        verbose_name_plural = "بازدیدهای تعمیرگاه"


class SafetyIssue(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="safety_issues"
    )
    issue_description = models.TextField(verbose_name="توضیحات مشکل ایمنی")

    class Meta:
        verbose_name = "مشکل ایمنی"
        verbose_name_plural = "مشکلات ایمنی"


class ShiftFollowUp(models.Model):
    shift_report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="follow_ups"
    )
    follow_up_description = models.TextField(verbose_name="شرح موارد پیگیری در شیفت بعد")

    class Meta:
        verbose_name = "پیگیری شیفت بعد"
        verbose_name_plural = "پیگیری‌های شیفت بعد"
