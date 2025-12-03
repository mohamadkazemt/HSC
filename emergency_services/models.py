from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from contractor_management.models import Contractor, Employee
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class MedicineCategory(models.Model):
    """دسته‌بندی دارو"""
    name = models.CharField(_("نام دسته‌بندی"), max_length=100)
    description = models.TextField(_("توضیحات"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("دسته‌بندی دارو")
        verbose_name_plural = _("دسته‌بندی‌های دارو")
    
    def __str__(self):
        return self.name

class Medicine(models.Model):
    """مدل دارو"""
    DRUG_TYPE_CHOICES = [
        ('Solid', _('جامد (قرص/آمپول)')),
        ('Liquid', _('مایع (شربت)')),
    ]
    
    name = models.CharField(_("نام دارو"), max_length=200)
    category = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True, verbose_name=_("دسته‌بندی"))
    drug_type = models.CharField(_("نوع دارو"), max_length=10, choices=DRUG_TYPE_CHOICES, default='Solid')
    quantity = models.DecimalField(_("موجودی فعلی"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_unit_volume = models.DecimalField(_("حجم کل واحد (سی‌سی)"), max_digits=10, decimal_places=2, null=True, blank=True, 
                                           help_text=_("برای داروهای مایع: حجم کل یک واحد (مثلاً 100 برای یک شیشه 100 سی‌سی)"))
    expiry_date = models.DateField(_("تاریخ انقضا"))
    critical_threshold = models.DecimalField(_("حد بحرانی هشدار"), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("دارو")
        verbose_name_plural = _("داروها")
    
    def __str__(self):
        return self.name
    
    def is_expired(self):
        """بررسی منقضی بودن دارو"""
        return self.expiry_date < timezone.now().date()
    
    def is_critical(self):
        """بررسی رسیدن به حد بحرانی"""
        return self.quantity <= self.critical_threshold
    
    def clean(self):
        """اعتبارسنجی فیلدها"""
        if self.drug_type == 'Liquid':
            if not self.total_unit_volume or self.total_unit_volume <= 0:
                raise ValidationError({
                    'total_unit_volume': _("برای داروهای مایع، حجم کل واحد (سی‌سی) باید مقدار مثبت داشته باشد.")
                })
    
    def save(self, *args, **kwargs):
        """اعمال منطق موجودی و تاریخ انقضا"""
        # اعتبارسنجی قبل از ذخیره
        self.full_clean()
        
        if self.is_expired():
            self.is_active = False
        super().save(*args, **kwargs)
        
        # ایجاد نوتیفیکیشن در صورت رسیدن به حد بحرانی یا منقضی شدن
        from dashboard.models import Notification
        from django.contrib.auth.models import User, Group
        
        # دریافت گروه‌های مدیر HSE و مدیر اورژانس
        try:
            hse_group = Group.objects.get(name='مدیر HSE')
            emergency_group = Group.objects.get(name='مدیر اورژانس')
            
            # دریافت کاربران این گروه‌ها
            hse_managers = User.objects.filter(groups=hse_group)
            emergency_managers = User.objects.filter(groups=emergency_group)
            
            # ترکیب لیست مدیران
            managers = list(hse_managers) + list(emergency_managers)
            
            if self.is_critical():
                # تعیین واحد نمایش بر اساس نوع دارو
                unit_display = "سی‌سی" if self.drug_type == 'Liquid' else "عدد"
                # ارسال نوتیفیکیشن هشدار موجودی به همه مدیران
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        title=f"هشدار موجودی دارو",
                        message=f"موجودی داروی {self.name} به حد بحرانی رسیده است ({self.quantity} {unit_display})",
                        notification_type="warning",
                        is_read=False
                    )
            
            if self.is_expired():
                # ارسال نوتیفیکیشن انقضا به همه مدیران
                for manager in managers:
                    Notification.objects.create(
                        user=manager,
                        title=f"هشدار انقضای دارو",
                        message=f"داروی {self.name} منقضی شده است",
                        notification_type="error",
                        is_read=False
                    )
        except Group.DoesNotExist:
            # اگر گروه‌ها وجود نداشتند، از ارسال نوتیفیکیشن صرف‌نظر می‌کنیم
            pass


class MedicalService(models.Model):
    """خدمات درمانی"""
    name = models.CharField(_("نام خدمت"), max_length=200)
    description = models.TextField(_("توضیحات"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("خدمت درمانی")
        verbose_name_plural = _("خدمات درمانی")
    
    def __str__(self):
        return self.name


class Hospital(models.Model):
    """مدل بیمارستان"""
    name = models.CharField(_("نام بیمارستان"), max_length=200)
    address = models.TextField(_("آدرس"))
    phone = models.CharField(_("شماره تماس"), max_length=20)
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("بیمارستان")
        verbose_name_plural = _("بیمارستان‌ها")
    
    def __str__(self):
        return self.name


class MedicalVisit(models.Model):
    """مدل مراجعه و خدمات درمانی"""
    PERSONNEL_TYPE_CHOICES = [
        ('company', _('پرسنل شرکت')),
        ('contractor', _('پرسنل پیمانکار')),
    ]
    
    company_personnel = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("پرسنل شرکت"))
    contractor_personnel = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("پرسنل پیمانکار"))
    personnel_type = models.CharField(_("نوع پرسنل"), max_length=20, choices=PERSONNEL_TYPE_CHOICES)
    
    visit_reason = models.TextField(_("علت مراجعه"))
    visit_time = models.DateTimeField(_("زمان مراجعه"), default=timezone.now)
    doctor_recommendation = models.TextField(_("توصیه پزشک"))
    services = models.ManyToManyField(MedicalService, verbose_name=_("خدمات درمانی"))
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("بیمارستان"))
    hospital_admission_time = models.DateTimeField(_("زمان پذیرش در بیمارستان"), null=True, blank=True)
    hospital_discharge_time = models.DateTimeField(_("زمان ترخیص از بیمارستان"), null=True, blank=True)
    hospital_diagnosis = models.TextField(_("تشخیص بیمارستان"), blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="created_visits", verbose_name=_("ثبت کننده"))
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("مراجعه پزشکی")
        verbose_name_plural = _("مراجعات پزشکی")
    
    def __str__(self):
        if self.personnel_type == 'company':
            return f"مراجعه {self.company_personnel} - {self.visit_time}"
        else:
            return f"مراجعه {self.contractor_personnel} - {self.visit_time}"
    
    def clean(self):
        """اعتبارسنجی نوع پرسنل و انتخاب صحیح"""
        if self.personnel_type == 'company' and not self.company_personnel:
            raise ValidationError(_("برای پرسنل شرکت باید یک پرسنل انتخاب شود."))
        elif self.personnel_type == 'contractor' and not self.contractor_personnel:
            raise ValidationError(_("برای پرسنل پیمانکار باید یک پیمانکار انتخاب شود."))
        
        # اعتبارسنجی زمان‌های بیمارستان
        if self.hospital:
            if self.hospital_admission_time and self.hospital_discharge_time:
                if self.hospital_admission_time > self.hospital_discharge_time:
                    raise ValidationError(_("زمان ترخیص نمی‌تواند قبل از زمان پذیرش باشد."))
            if self.hospital_admission_time and self.hospital_admission_time < self.visit_time:
                raise ValidationError(_("زمان پذیرش در بیمارستان نمی‌تواند قبل از زمان مراجعه باشد."))


class MedicineUsage(models.Model):
    """استفاده از دارو در ویزیت"""
    visit = models.ForeignKey(MedicalVisit, on_delete=models.CASCADE, related_name="medicine_usages", verbose_name=_("مراجعه"))
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, verbose_name=_("دارو"))
    quantity = models.DecimalField(_("تعداد/حجم (سی‌سی برای مایعات)"), max_digits=10, decimal_places=2, 
                                   help_text=_("برای داروهای مایع: مقدار بر اساس سی‌سی وارد شود. برای سایر داروها: تعداد واحد"))
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("استفاده دارو")
        verbose_name_plural = _("استفاده‌های دارو")
    
    def __str__(self):
        unit = "سی‌سی" if self.medicine.drug_type == 'Liquid' else "عدد"
        return f"{self.medicine.name} ({self.quantity} {unit}) - {self.visit}"
    
    def _calculate_deduction_amount(self):
        """
        محاسبه مقدار کسر از موجودی بر اساس نوع دارو
        برای داروهای مایع: مقدار CC را به تعداد شیشه تبدیل می‌کند
        برای سایر داروها: همان مقدار وارد شده کسر می‌شود
        """
        if self.medicine.drug_type == 'Liquid':
            # برای داروهای مایع: مقدار CC را بر حجم کل واحد تقسیم می‌کنیم
            if not self.medicine.total_unit_volume or self.medicine.total_unit_volume <= 0:
                raise ValidationError(_("حجم کل واحد برای این داروی مایع تعریف نشده است."))
            # محاسبه تعداد شیشه مصرف شده
            bottles_consumed = Decimal(str(self.quantity)) / Decimal(str(self.medicine.total_unit_volume))
            return bottles_consumed
        else:
            # برای داروهای جامد: همان مقدار وارد شده
            return Decimal(str(self.quantity))
    
    def save(self, *args, **kwargs):
        """کاهش موجودی دارو پس از ثبت"""
        if not self.pk:  # فقط برای رکوردهای جدید
            # بررسی تاریخ انقضا
            if self.medicine.is_expired():
                raise ValidationError(_("این دارو منقضی شده است."))
            
            # محاسبه مقدار کسر از موجودی
            deduction_amount = self._calculate_deduction_amount()
            
            # بررسی موجودی کافی
            if self.medicine.quantity < deduction_amount:
                unit = "شیشه" if self.medicine.drug_type == 'Liquid' else "عدد"
                raise ValidationError(
                    _("موجودی دارو کافی نیست. موجودی فعلی: %(current)s %(unit)s"),
                    code='insufficient_stock',
                    params={
                        'current': self.medicine.quantity,
                        'unit': unit
                    }
                )
            
            # کاهش موجودی
            self.medicine.quantity -= deduction_amount
            self.medicine.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """افزایش موجودی دارو پس از حذف"""
        # محاسبه مقدار برگشتی به موجودی
        return_amount = self._calculate_deduction_amount()
        self.medicine.quantity += return_amount
        self.medicine.save()
        super().delete(*args, **kwargs)


class MedicineReturn(models.Model):
    """برگشت دارو به انبار"""
    usage = models.ForeignKey(MedicineUsage, on_delete=models.CASCADE, verbose_name=_("مصرف دارو"))
    quantity = models.DecimalField(_("تعداد/حجم برگشتی (سی‌سی برای مایعات)"), max_digits=10, decimal_places=2,
                                   help_text=_("برای داروهای مایع: مقدار بر اساس سی‌سی وارد شود. برای سایر داروها: تعداد واحد"))
    return_reason = models.TextField(_("دلیل برگشت"))
    returned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, verbose_name=_("برگشت دهنده"))
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("برگشت دارو")
        verbose_name_plural = _("برگشت‌های دارو")
    
    def __str__(self):
        unit = "سی‌سی" if self.usage.medicine.drug_type == 'Liquid' else "عدد"
        return f"برگشت {self.quantity} {unit} {self.usage.medicine.name}"
    
    def _calculate_return_amount(self):
        """
        محاسبه مقدار برگشتی به موجودی بر اساس نوع دارو
        برای داروهای مایع: مقدار CC را به تعداد شیشه تبدیل می‌کند
        برای سایر داروها: همان مقدار وارد شده اضافه می‌شود
        """
        if self.usage.medicine.drug_type == 'Liquid':
            # برای داروهای مایع: مقدار CC را بر حجم کل واحد تقسیم می‌کنیم
            if not self.usage.medicine.total_unit_volume or self.usage.medicine.total_unit_volume <= 0:
                raise ValidationError(_("حجم کل واحد برای این داروی مایع تعریف نشده است."))
            # محاسبه تعداد شیشه برگشتی
            bottles_returned = Decimal(str(self.quantity)) / Decimal(str(self.usage.medicine.total_unit_volume))
            return bottles_returned
        else:
            # برای داروهای جامد: همان مقدار وارد شده
            return Decimal(str(self.quantity))
    
    def clean(self):
        """اعتبارسنجی تعداد برگشتی"""
        if self.quantity > self.usage.quantity:
            unit = "سی‌سی" if self.usage.medicine.drug_type == 'Liquid' else "عدد"
            raise ValidationError(
                _("تعداد/حجم برگشتی نمی‌تواند از تعداد/حجم مصرف شده (%(used)s %(unit)s) بیشتر باشد."),
                code='invalid',
                params={
                    'used': self.usage.quantity,
                    'unit': unit
                }
            )
    
    def save(self, *args, **kwargs):
        """افزایش موجودی دارو پس از برگشت"""
        if not self.pk:  # فقط برای رکوردهای جدید
            self.clean()
            
            # محاسبه مقدار برگشتی به موجودی
            return_amount = self._calculate_return_amount()
            
            # افزایش موجودی
            self.usage.medicine.quantity += return_amount
            self.usage.medicine.save()
            
            # بروزرسانی مصرف
            self.usage.quantity -= self.quantity
            self.usage.save()
        
        super().save(*args, **kwargs)


class EmergencyEquipment(models.Model):
    """مدل تجهیزات اورژانس"""
    name = models.CharField(_("نام تجهیز"), max_length=200)
    serial_number = models.CharField(_("شماره سریال"), max_length=100, unique=True)
    description = models.TextField(_("توضیحات"), blank=True, null=True)
    last_calibration_date = models.DateField(_("تاریخ آخرین کالیبراسیون"))
    next_calibration_date = models.DateField(_("تاریخ کالیبراسیون بعدی"))
    calibration_alert_days = models.PositiveIntegerField(_("تعداد روز هشدار قبل از کالیبراسیون"), default=30)
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ بروزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("تجهیز اورژانس")
        verbose_name_plural = _("تجهیزات اورژانس")
    
    def __str__(self):
        return f"{self.name} - {self.serial_number}"
    
    def is_calibration_due(self):
        """بررسی نیاز به کالیبراسیون"""
        today = timezone.now().date()
        days_until_calibration = (self.next_calibration_date - today).days
        return days_until_calibration <= self.calibration_alert_days
    
    def save(self, *args, **kwargs):
        """اعمال منطق کالیبراسیون و ارسال نوتیفیکیشن"""
        super().save(*args, **kwargs)
        
        # ایجاد نوتیفیکیشن در صورت نزدیک شدن به تاریخ کالیبراسیون
        from dashboard.models import Notification
        from django.contrib.auth.models import User, Group
        
        # دریافت گروه‌های مدیر HSE و مدیر اورژانس
        hse_group = Group.objects.get(name='مدیر HSE')
        emergency_group = Group.objects.get(name='مدیر اورژانس')
        
        # دریافت کاربران این گروه‌ها
        hse_managers = User.objects.filter(groups=hse_group)
        emergency_managers = User.objects.filter(groups=emergency_group)
        
        # ترکیب لیست مدیران
        managers = list(hse_managers) + list(emergency_managers)
        
        if self.is_calibration_due():
            days_until_calibration = (self.next_calibration_date - timezone.now().date()).days
            # ارسال نوتیفیکیشن هشدار کالیبراسیون به همه مدیران
            for manager in managers:
                Notification.objects.create(
                    user=manager,
                    title=f"هشدار کالیبراسیون تجهیز",
                    message=f"تجهیز {self.name} با شماره سریال {self.serial_number} نیاز به کالیبراسیون دارد. {days_until_calibration} روز تا تاریخ کالیبراسیون باقی مانده است.",
                    notification_type="warning",
                    is_read=False
                )


class ExpiredMedicineLog(models.Model):
    """ثبت تاریخچه داروهای منقضی برای دیدگاه بازرسان"""
    medicine_name = models.CharField(_("نام دارو"), max_length=200)
    medicine_category = models.CharField(_("دسته‌بندی"), max_length=100, blank=True)
    quantity = models.DecimalField(_("موجودی هنگام انقضا"), max_digits=10, decimal_places=2)
    expiry_date = models.DateField(_("تاریخ انقضا"))
    detected_date = models.DateField(_("تاریخ تشخیص منقضی"), auto_now_add=True)
    disposal_date = models.DateField(_("تاریخ حذف/دفع"), null=True, blank=True)
    disposal_method = models.CharField(
        _("روش دفع"),
        max_length=50,
        choices=[
            ('deleted', 'حذف از سیستم'),
            ('incinerated', 'سوزانده شده'),
            ('donated', 'اهدا شده'),
            ('returned', 'برگشت به تولیدکننده'),
            ('other', 'سایر'),
        ],
        default='deleted'
    )
    notes = models.TextField(_("یادداشت‌ها"), blank=True, null=True)
    disposal_by_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("حذف شده توسط"),
        related_name='medicine_disposals'
    )
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ آخرین بروزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("گزارش دارو منقضی")
        verbose_name_plural = _("گزارش‌های داروهای منقضی")
        ordering = ['-disposal_date', '-detected_date']
        indexes = [
            models.Index(fields=['-disposal_date']),
            models.Index(fields=['-detected_date']),
        ]
    
    def __str__(self):
        return f"{self.medicine_name} - {self.expiry_date}"
