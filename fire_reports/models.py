from django.db import models
from django.core.validators import MinValueValidator
from shift_manager.models import InitialShiftSetup, SHIFT_CHOICES
from django.contrib.auth import get_user_model

User = get_user_model()

class FireReport(models.Model):
    STATUS_CHOICES = [
        ('suitable', 'مناسب'),
        ('unsuitable', 'نامناسب'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]

    # اطلاعات کلی شیفت
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name='شیفت کاری')
    report_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ و ساعت گزارش')
    shift_operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fire_shift_operator', verbose_name='متصدی شیفت آتش‌نشانی')
    firefighter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fire_firefighter', verbose_name='آتش‌نشان')
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='وضعیت تأیید')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_fire_reports', verbose_name='تأیید شده توسط')
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تأیید')
    rejection_reason = models.TextField(null=True, blank=True, verbose_name='دلیل رد')

    # وضعیت تجهیزات و خودرو
    horn_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت بوق و چراغ گردان')
    horn_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت بوق و چراغ گردان')
    
    hose_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت شیلنگ‌ها و اتصالات')
    hose_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت شیلنگ‌ها و اتصالات')
    
    monitor_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت مانیتور')
    monitor_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت مانیتور')
    
    extinguisher_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت خاموش‌کننده‌های دستی')
    extinguisher_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت خاموش‌کننده‌های دستی')
    
    equipment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت تجهیزات آتش‌نشانی')
    equipment_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت تجهیزات آتش‌نشانی')
    
    foam_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت پودر و فوم خودرو')
    foam_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت پودر و فوم خودرو')
    
    water_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت آب')
    water_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت آب')
    
    tire_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت لاستیک‌ها')
    tire_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت لاستیک‌ها')
    
    brake_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت سیستم ترمز خودرو')
    brake_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت سیستم ترمز خودرو')
    
    lighting_status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='وضعیت سیستم روشنایی')
    lighting_description = models.TextField(blank=True, null=True, verbose_name='توضیحات وضعیت سیستم روشنایی')

    # گزارش حوادث
    incident_dispatch_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد اعزام به محل حادثه')
    personal_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث فردی')
    equipment_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث تجهیزاتی')
    fire_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث آتش‌سوزی')

    # سایر اقدامات
    additional_notes = models.TextField(blank=True, null=True, verbose_name='توضیحات تکمیلی')

    class Meta:
        verbose_name = 'گزارش آتش‌نشانی'
        verbose_name_plural = 'گزارشات آتش‌نشانی'
        ordering = ['-report_date']

    def __str__(self):
        return f'گزارش آتش‌نشانی - {self.shift} - {self.report_date}'
