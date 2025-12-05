# corrective_actions/models.py
from django.db import models
from django.utils import timezone
from accounts.models import UserProfile


class CorrectiveAction(models.Model):
    """
    مدل اصلی برای اقدام اصلاحی/پیشگیرانه
    مطابق با فرم MIE-MD-M-FR-025-V02
    """
    
    # نوع اقدام
    ACTION_TYPE_CHOICES = [
        ('correction', 'اصلاح'),
        ('corrective', 'اصلاحی'),
        ('preventive', 'پیشگیرانه'),
        ('improvement', 'توصیه بهبود'),
    ]
    
    # موضوع
    TOPIC_CHOICES = [
        ('quality', 'کیفیت'),
        ('hse', 'ایمنی، بهداشت و محیط زیست'),
    ]
    
    # ورودی عدم انطباق
    SOURCE_CHOICES = [
        ('audit', 'ممیزی داخلی/خارجی'),
        ('incident', 'رویدادها و حوادث'),
        ('risk', 'ریسک‌ها و فرصت‌ها'),
        ('inspection', 'بازرسی'),
        ('feedback', 'شکایات/بازخورد'),
        ('other', 'سایر'),
    ]
    
    # وضعیت
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('open', 'در حال اجرا'),
        ('review', 'بررسی اثربخشی'),
        ('closed', 'بسته شده'),
    ]
    
    # فیلدهای اصلی
    tracking_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="شماره اقدام"
    )
    
    created_at = models.DateField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )
    
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPE_CHOICES,
        verbose_name="نوع اقدام"
    )
    
    topic = models.CharField(
        max_length=20,
        choices=TOPIC_CHOICES,
        verbose_name="موضوع"
    )
    
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        verbose_name="ورودی عدم انطباق"
    )
    
    description = models.TextField(
        verbose_name="شرح عدم انطباق"
    )
    
    root_cause_analysis = models.TextField(
        blank=True,
        null=True,
        verbose_name="علل ریشه‌ای عدم انطباق"
    )
    
    # روابط با کاربران
    requester = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_corrective_actions',
        verbose_name="درخواست کننده"
    )
    
    receiver = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_corrective_actions',
        verbose_name="پذیرنده / مسئول رسیدگی"
    )
    
    # روابط با سایر اپلیکیشن‌ها
    related_incident = models.ForeignKey(
        'hse_incidents.IncidentReport',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions',
        verbose_name="رویداد مرتبط"
    )
    
    related_risk = models.ForeignKey(
        'risk_assessment.RiskAssessment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions',
        verbose_name="ریسک مرتبط"
    )
    
    related_anomaly = models.ForeignKey(
        'anomalis.Anomaly',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrective_actions',
        verbose_name="آنومالی مرتبط"
    )
    
    # نتیجه اثربخشی
    effectiveness_result = models.BooleanField(
        null=True,
        blank=True,
        verbose_name="نتیجه اثربخشی",
        help_text="True = موثر، False = غیرموثر"
    )
    
    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="وضعیت"
    )
    
    created_at_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="زمان آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "اقدام اصلاحی/پیشگیرانه"
        verbose_name_plural = "اقدامات اصلاحی/پیشگیرانه"
        ordering = ['-created_at', '-created_at_time']
        indexes = [
            models.Index(fields=['tracking_code']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.tracking_code} - {self.get_action_type_display()}"


class ActionStep(models.Model):
    """
    مدل برای اقدامات اصلاحی/پیشگیرانه (جدول اقدامات)
    """
    
    corrective_action = models.ForeignKey(
        CorrectiveAction,
        on_delete=models.CASCADE,
        related_name='action_steps',
        verbose_name="اقدام اصلاحی/پیشگیرانه"
    )
    
    description = models.CharField(
        max_length=500,
        verbose_name="شرح اقدام"
    )
    
    responsible = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='action_steps',
        verbose_name="متولی اجرا"
    )
    
    deadline = models.DateField(
        verbose_name="مهلت اقدام"
    )
    
    completion_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="تاریخ انجام"
    )
    
    is_done = models.BooleanField(
        default=False,
        verbose_name="انجام شد"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="زمان آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "مرحله اقدام"
        verbose_name_plural = "مراحل اقدام"
        ordering = ['deadline', 'created_at']
    
    def __str__(self):
        return f"{self.corrective_action.tracking_code} - {self.description[:50]}"


class SideEffectRisk(models.Model):
    """
    مدل برای ارزیابی ریسک ناشی از اقدام (صفحه 2 فرم)
    """
    
    corrective_action = models.ForeignKey(
        CorrectiveAction,
        on_delete=models.CASCADE,
        related_name='side_effect_risks',
        verbose_name="اقدام اصلاحی/پیشگیرانه"
    )
    
    hazard = models.CharField(
        max_length=255,
        verbose_name="خطر / جنبه"
    )
    
    event = models.CharField(
        max_length=255,
        verbose_name="رویداد"
    )
    
    consequence = models.CharField(
        max_length=500,
        verbose_name="پیامد"
    )
    
    control_measure = models.CharField(
        max_length=500,
        verbose_name="اقدام کنترلی پیشنهادی"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="زمان آخرین بروزرسانی"
    )
    
    class Meta:
        verbose_name = "ریسک ناشی از اقدام"
        verbose_name_plural = "ریسک‌های ناشی از اقدام"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.corrective_action.tracking_code} - {self.hazard}"
