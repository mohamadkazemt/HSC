from django.db import models
from django.utils.timezone import now
from contractor_management.models import Contractor, Employee
from BaseInfo.models import MiningBlock
from accounts.models import UserProfile


class WorkFrontStatus(models.Model):
    workfront = models.ForeignKey(MiningBlock, on_delete=models.CASCADE, verbose_name="جبهه کاری")
    status = models.BooleanField(verbose_name="تایید شده")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.workfront.block_name} - {'تایید' if self.status else 'رد'}"


class DumpStatus(models.Model):
    dump = models.ForeignKey(MiningBlock, on_delete=models.CASCADE, verbose_name="دمپ")
    status = models.BooleanField(verbose_name="تایید شده")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.dump.block_name} - {'تایید' if self.status else 'رد'}"


class DrillingSiteStatus(models.Model):
    drilling_site = models.ForeignKey(MiningBlock, on_delete=models.CASCADE, verbose_name="سایت حفاری")
    status = models.BooleanField(verbose_name="تایید شده")
    comments = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return f"{self.drilling_site.block_name} - {'تایید' if self.status else 'رد'}"


class Incident(models.Model):
    PERSON_TYPE_CHOICES = [
        ('employee', 'پرسنل'),
        ('contractor', 'پیمانکار')
    ]
    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, verbose_name="نوع فرد")
    person = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="فرد مرتبط")
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پرسنل مرتبط")
    description = models.TextField(verbose_name="شرح حادثه")

    def __str__(self):
        return f"{self.person or self.user_profile} - {self.description[:50]}"


class HSEParticipation(models.Model):
    PERSON_TYPE_CHOICES = [
        ('employee', 'پرسنل'),
        ('contractor', 'پیمانکار')
    ]
    person_type = models.CharField(max_length=20, choices=PERSON_TYPE_CHOICES, verbose_name="نوع فرد")
    person = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="فرد مرتبط")
    user_profile = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پرسنل مرتبط")
    description = models.TextField(verbose_name="شرح مشارکت")

    def __str__(self):
        return f"{self.person or self.user_profile} - {self.description[:50]}"

class SafetyStop(models.Model):
    report = models.ForeignKey('HSEReport', on_delete=models.CASCADE, related_name="safety_stops", verbose_name="گزارش ایمنی")
    reason = models.TextField(verbose_name="دلیل توقف")
    duration_hours = models.FloatField(verbose_name="مدت زمان توقف (ساعت)")

    def __str__(self):
        return f"توقف: {self.reason} - {self.duration_hours} ساعت"



class HSEReport(models.Model):
    shift_date = models.DateField(default=now, verbose_name="تاریخ شیفت")
    supervisor = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, verbose_name="سرشیفت")
    workfront_statuses = models.ManyToManyField(WorkFrontStatus, blank=True, verbose_name="وضعیت جبهه‌های کاری")
    dump_statuses = models.ManyToManyField(DumpStatus, blank=True, verbose_name="وضعیت دمپ‌ها")
    drilling_site_statuses = models.ManyToManyField(DrillingSiteStatus, blank=True, verbose_name="وضعیت سایت‌های حفاری")
    repair_shop_visit = models.BooleanField(default=False, verbose_name="بازدید از تعمیرگاه")
    repair_shop_status = models.BooleanField(default=False, verbose_name="وضعیت تعمیرگاه")
    repair_shop_comments = models.TextField(blank=True, null=True, verbose_name="توضیحات تعمیرگاه")
    blasting = models.BooleanField(default=False, verbose_name="آتشباری")
    blasting_location = models.ForeignKey(MiningBlock, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="محل آتشباری")
    incidents = models.ManyToManyField(Incident, blank=True, verbose_name="حوادث رخ داده")
    near_misses = models.ManyToManyField(Incident, blank=True, related_name="near_misses", verbose_name="شبه‌حوادث")
    hospital_dispatches = models.ManyToManyField(Incident, blank=True, related_name="hospital_dispatches", verbose_name="اعزام به بیمارستان")
    rewards = models.ManyToManyField(Incident, blank=True, related_name="rewards", verbose_name="موارد تشویق")
    penalties = models.ManyToManyField(Incident, blank=True, related_name="penalties", verbose_name="موارد تنبیه")
    safety_stops = models.ManyToManyField(SafetyStop, blank=True, related_name="reports", verbose_name="توقفات ناشی از ایمنی")
    hse_participation = models.ManyToManyField(HSEParticipation, blank=True, verbose_name="مشارکت کارکنان")
    next_shift_tasks = models.TextField(blank=True, null=True, verbose_name="موارد پیگیری برای شیفت بعد")

    def __str__(self):
        return f"گزارش ایمنی - {self.shift_date}"
