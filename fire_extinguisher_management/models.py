from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class FireExtinguisherType(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("نام"))
    agent = models.CharField(max_length=100, verbose_name=_("عامل خاموش کننده"))
    use_class = models.CharField(max_length=100, verbose_name=_("کلاس کاربری"))
    inspection_interval_months = models.PositiveIntegerField(verbose_name=_("فاصله بازرسی (ماه)"))
    service_interval_years = models.PositiveIntegerField(verbose_name=_("فاصله سرویس (سال)"))
    pressure_test_interval_years = models.PositiveIntegerField(verbose_name="فاصله تست فشار (سال)")
    notes = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = _("نوع کپسول آتش‌نشانی")
        verbose_name_plural = _("انواع کپسول‌های آتش‌نشانی")

    def __str__(self):
        return self.name

class FireExtinguisher(models.Model):
    STATUS_CHOICES = [
        ('operational', _('عملیاتی')),
        ('needs_maintenance', _('نیازمند تعمیر')),
        ('expired', _('منقضی شده')),
        ('under_test', _('در انتظار تست')),
        ('disposed', _('مستهلک شده')),
        ('reserved', _('رزرو شده')),
    ]

    serial_tag = models.CharField(max_length=50, unique=True, verbose_name=_("کد سریال"))
    extinguisher_type = models.ForeignKey(FireExtinguisherType, on_delete=models.PROTECT, verbose_name=_("نوع کپسول"))
    capacity_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("ظرفیت"))
    capacity_unit = models.CharField(max_length=20, choices=[('kg', 'کیلوگرم'), ('L', 'لیتر')], verbose_name=_("واحد ظرفیت"))
    manufacturer = models.CharField(max_length=100, verbose_name=_("سازنده"))
    model_number = models.CharField(max_length=50, verbose_name=_("شماره مدل"))
    purchase_date = models.DateField(verbose_name=_("تاریخ خرید"))
    manufacture_date = models.DateField(verbose_name=_("تاریخ ساخت"))
    commission_date = models.DateField(verbose_name=_("تاریخ بهره‌برداری"))
    expected_lifespan_years = models.PositiveIntegerField(verbose_name=_("عمر مفید (سال)"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational', verbose_name=_("وضعیت"))
    
    # Location fields
    location_type = models.CharField(max_length=20, choices=[
        ('section', _('بخش')),
        ('machine', _('دستگاه'))
    ], default='section', verbose_name=_("نوع مکان"))
    location_section = models.ForeignKey('anomalis.LocationSection', on_delete=models.SET_NULL, 
                                       null=True, blank=True, verbose_name=_("بخش"))
    location_machine = models.ForeignKey('BaseInfo.MiningMachine', on_delete=models.SET_NULL, 
                                       null=True, blank=True, verbose_name=_("دستگاه"))

    # Service Information
    last_serviced_date = models.DateField(null=True, blank=True, verbose_name=_("تاریخ آخرین سرویس"))
    next_scheduled_service_date = models.DateField(null=True, blank=True, verbose_name=_("تاریخ سرویس بعدی"))
    pressure_test_due_date = models.DateField(null=True, blank=True, verbose_name=_("تاریخ تست فشار"))
    
    # Replacement Information
    replaced_by_extinguisher = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='replacement_for', verbose_name=_("جایگزین شده با"))
    replaces_extinguisher = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='replaced_from', verbose_name=_("جایگزین شده از"))
    replacement_notes = models.TextField(blank=True, verbose_name=_("توضیحات جایگزینی"))

    # Additional Information
    notes = models.TextField(blank=True, verbose_name=_("توضیحات"))

    class Meta:
        verbose_name = _("کپسول آتش‌نشانی")
        verbose_name_plural = _("کپسول‌های آتش‌نشانی")
        ordering = ['-commission_date']

    def __str__(self):
        return f"{self.serial_tag} - {self.extinguisher_type.name}"

    @property
    def location_object(self):
        if self.location_type == 'section' and self.location_section:
            return self.location_section
        elif self.location_type == 'machine' and self.location_machine:
            return self.location_machine
        return None

    def clean(self):
        if self.location_type == 'section' and not self.location_section:
            raise ValidationError(_("برای مکان از نوع بخش، باید بخش را انتخاب کنید."))
        if self.location_type == 'machine' and not self.location_machine:
            raise ValidationError(_("برای مکان از نوع دستگاه، باید دستگاه را انتخاب کنید."))
        if self.location_type == 'section' and self.location_machine:
            raise ValidationError(_("برای مکان از نوع بخش، نمی‌توانید دستگاه انتخاب کنید."))
        if self.location_type == 'machine' and self.location_section:
            raise ValidationError(_("برای مکان از نوع دستگاه، نمی‌توانید بخش انتخاب کنید."))

    def calculate_next_service_date(self):
        if self.last_serviced_date:
            return self.last_serviced_date + timedelta(days=365 * self.extinguisher_type.service_interval_years)
        return None

    def calculate_pressure_test_date(self):
        if self.last_serviced_date:
            return self.last_serviced_date + timedelta(days=365 * self.extinguisher_type.pressure_test_interval_years)
        return None

class ServiceRecord(models.Model):
    SERVICE_TYPE_CHOICES = [
        ('inspection', _('بازرسی')),
        ('maintenance', _('تعمیر و نگهداری')),
        ('pressure_test', _('تست فشار')),
        ('refill', _('پر کردن مجدد')),
    ]

    OUTCOME_CHOICES = [
        ('passed', _('قبول')),
        ('failed', _('رد')),
        ('needs_repair', _('نیازمند تعمیر')),
    ]

    extinguisher = models.ForeignKey(FireExtinguisher, on_delete=models.CASCADE, verbose_name=_("کپسول"))
    service_date = models.DateField(verbose_name=_("تاریخ سرویس"))
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPE_CHOICES, verbose_name=_("نوع سرویس"))
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, verbose_name=_("نتیجه"))
    
    # Service Provider Information
    performed_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name=_("انجام دهنده (کاربر)"))
    performed_by_external = models.CharField(max_length=100, blank=True, verbose_name=_("انجام دهنده (خارجی)"))
    
    # Measurements
    pressure_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                         verbose_name=_("فشار"))
    weight_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       verbose_name=_("وزن"))
    
    # Service Details
    actions_taken = models.TextField(verbose_name=_("اقدامات انجام شده"))
    notes = models.TextField(blank=True, verbose_name=_("توضیحات"))

    class Meta:
        verbose_name = _("سابقه سرویس")
        verbose_name_plural = _("سوابق سرویس")
        ordering = ['-service_date']

    def __str__(self):
        return f"{self.extinguisher.serial_tag} - {self.get_service_type_display()} - {self.service_date}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("کاربر"))
    message = models.TextField(verbose_name=_("پیام"))
    url = models.CharField(max_length=200, blank=True, null=True, verbose_name="لینک")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("تاریخ ایجاد"))
    is_read = models.BooleanField(default=False, verbose_name=_("خوانده شده"))

    class Meta:
        verbose_name = _("اعلان")
        verbose_name_plural = _("اعلان‌ها")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"
