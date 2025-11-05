from django.db import models
from django.core.validators import MinValueValidator
from shift_manager.models import InitialShiftSetup, SHIFT_CHOICES
from django.contrib.auth import get_user_model
from contractor_management.models import Vehicle as ContractorVehicle
from BaseInfo.models import EmergencyVehicle
from django.core.exceptions import ValidationError

User = get_user_model()

class VehicleStatusReport(models.Model):
    """مدل برای نگهداری وضعیت هر خودرو در گزارش"""
    STATUS_CHOICES = [
        ('suitable', 'مناسب'),
        ('unsuitable', 'نامناسب'),
    ]

    VEHICLE_SOURCE_CHOICES = [
        ('company', 'خودروی شرکت'),
        ('contractor', 'خودروی پیمانکار'),
    ]

    fire_report = models.ForeignKey('FireReport', on_delete=models.CASCADE, related_name='vehicle_reports', verbose_name='گزارش آتش‌نشانی')
    vehicle_source = models.CharField(max_length=20, choices=VEHICLE_SOURCE_CHOICES, verbose_name='منبع خودرو')
    company_vehicle = models.ForeignKey(EmergencyVehicle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='خودروی امدادی شرکت')
    contractor_vehicle = models.ForeignKey(ContractorVehicle, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='خودروی پیمانکار')

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

    def clean(self):
        if self.vehicle_source == 'company' and not self.company_vehicle:
            raise ValidationError({
                'company_vehicle': 'برای خودروی شرکت باید یک خودروی امدادی انتخاب شود.'
            })
        elif self.vehicle_source == 'contractor' and not self.contractor_vehicle:
            raise ValidationError({
                'contractor_vehicle': 'برای خودروی پیمانکار باید یک خودرو انتخاب شود.'
            })
        
        if self.company_vehicle and self.contractor_vehicle:
            raise ValidationError('نمی‌توانید همزمان خودروی شرکت و پیمانکار را انتخاب کنید.')

        # بررسی تجهیزات بر اساس نوع خودرو
        if self.vehicle_source == 'company' and self.company_vehicle:
            vehicle = self.company_vehicle
            if not vehicle.has_horn:
                self.horn_status = 'suitable'
                self.horn_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_hose:
                self.hose_status = 'suitable'
                self.hose_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_monitor:
                self.monitor_status = 'suitable'
                self.monitor_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_extinguisher:
                self.extinguisher_status = 'suitable'
                self.extinguisher_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_equipment:
                self.equipment_status = 'suitable'
                self.equipment_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_foam:
                self.foam_status = 'suitable'
                self.foam_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_water:
                self.water_status = 'suitable'
                self.water_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_tire:
                self.tire_status = 'suitable'
                self.tire_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_brake:
                self.brake_status = 'suitable'
                self.brake_description = 'این تجهیز در این خودرو موجود نیست.'
            if not vehicle.has_lighting:
                self.lighting_status = 'suitable'
                self.lighting_description = 'این تجهیز در این خودرو موجود نیست.'

    def get_vehicle(self):
        """Return the selected vehicle regardless of its source"""
        return self.company_vehicle if self.vehicle_source == 'company' else self.contractor_vehicle

    def __str__(self):
        vehicle = self.get_vehicle()
        return f'گزارش وضعیت {vehicle} - {self.fire_report.shift}'

    class Meta:
        verbose_name = 'گزارش وضعیت خودرو'
        verbose_name_plural = 'گزارشات وضعیت خودرو'

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

    VEHICLE_SOURCE_CHOICES = [
        ('company', 'خودروی شرکت'),
        ('contractor', 'خودروی پیمانکار'),
    ]

    # اطلاعات کلی شیفت
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, verbose_name='شیفت کاری')
    report_date = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ و ساعت گزارش')
    shift_operator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fire_shift_operator', verbose_name='متصدی شیفت آتش‌نشانی')
    firefighter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fire_firefighter', verbose_name='آتش‌نشان')
    
    # اطلاعات خودرو
    # وضعیت تأیید
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default='pending', verbose_name='وضعیت تأیید')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_fire_reports', verbose_name='تأیید شده توسط')
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تأیید')
    rejection_reason = models.TextField(null=True, blank=True, verbose_name='دلیل رد')

    # گزارش حوادث
    incident_dispatch_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد اعزام به محل حادثه')
    personal_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث فردی')
    equipment_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث تجهیزاتی')
    fire_incident_count = models.IntegerField(validators=[MinValueValidator(0)], verbose_name='تعداد حوادث آتش‌سوزی')

    # سایر اقدامات
    additional_notes = models.TextField(blank=True, null=True, verbose_name='توضیحات تکمیلی')

    def clean(self):
        # FireReport no longer stores per-vehicle equipment status fields.
        # Vehicle-specific information lives in VehicleStatusReport instances.
        super().clean()


    def __str__(self):
        return f'گزارش آتش‌نشانی - {self.shift} - {self.report_date}'

    class Meta:
        verbose_name = 'گزارش آتش‌نشانی'
        verbose_name_plural = 'گزارشات آتش‌نشانی'
        ordering = ['-report_date']
