from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import UserProfile
from contractor_management.models import Contractor, Employee
from django.utils.translation import gettext_lazy as _

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
    name = models.CharField(_("نام دارو"), max_length=200)
    category = models.ForeignKey(MedicineCategory, on_delete=models.SET_NULL, null=True, verbose_name=_("دسته‌بندی"))
    quantity = models.PositiveIntegerField(_("موجودی فعلی"))
    expiry_date = models.DateField(_("تاریخ انقضا"))
    critical_threshold = models.PositiveIntegerField(_("حد بحرانی هشدار"))
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
    
    def save(self, *args, **kwargs):
        """اعمال منطق موجودی و تاریخ انقضا"""
        if self.is_expired():
            self.is_active = False
        super().save(*args, **kwargs)
        
        # ایجاد نوتیفیکیشن در صورت رسیدن به حد بحرانی
        if self.is_critical():
            from dashboard.models import Notification
            Notification.objects.create(
                title=f"هشدار موجودی دارو",
                message=f"موجودی داروی {self.name} به حد بحرانی رسیده است ({self.quantity} عدد)",
                notification_type="warning",
                is_read=False
            )


class MedicalService(models.Model):
    """خدمات درمانی"""
    name = models.CharField(_("نام خدمت"), max_length=200)
    description = models.TextField(_("توضیحات"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("خدمت درمانی")
        verbose_name_plural = _("خدمات درمانی")
    
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


class MedicineUsage(models.Model):
    """استفاده از دارو در ویزیت"""
    visit = models.ForeignKey(MedicalVisit, on_delete=models.CASCADE, related_name="medicine_usages", verbose_name=_("مراجعه"))
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, verbose_name=_("دارو"))
    quantity = models.PositiveIntegerField(_("تعداد"))
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("استفاده دارو")
        verbose_name_plural = _("استفاده‌های دارو")
    
    def __str__(self):
        return f"{self.medicine.name} ({self.quantity}) - {self.visit}"
    
    def save(self, *args, **kwargs):
        """کاهش موجودی دارو پس از ثبت"""
        if not self.pk:  # فقط برای رکوردهای جدید
            # بررسی موجودی کافی
            if self.medicine.quantity < self.quantity:
                raise ValidationError(_("موجودی دارو کافی نیست."))
            
            # بررسی تاریخ انقضا
            if self.medicine.is_expired():
                raise ValidationError(_("این دارو منقضی شده است."))
            
            # کاهش موجودی
            self.medicine.quantity -= self.quantity
            self.medicine.save()
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """افزایش موجودی دارو پس از حذف"""
        self.medicine.quantity += self.quantity
        self.medicine.save()
        super().delete(*args, **kwargs)


class MedicineReturn(models.Model):
    """برگشت دارو به انبار"""
    usage = models.ForeignKey(MedicineUsage, on_delete=models.CASCADE, verbose_name=_("مصرف دارو"))
    quantity = models.PositiveIntegerField(_("تعداد برگشتی"))
    return_reason = models.TextField(_("دلیل برگشت"))
    returned_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, verbose_name=_("برگشت دهنده"))
    created_at = models.DateTimeField(_("تاریخ ثبت"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("برگشت دارو")
        verbose_name_plural = _("برگشت‌های دارو")
    
    def __str__(self):
        return f"برگشت {self.quantity} عدد {self.usage.medicine.name}"
    
    def clean(self):
        """اعتبارسنجی تعداد برگشتی"""
        if self.quantity > self.usage.quantity:
            raise ValidationError(_("تعداد برگشتی نمی‌تواند از تعداد مصرف شده بیشتر باشد."))
    
    def save(self, *args, **kwargs):
        """افزایش موجودی دارو پس از برگشت"""
        if not self.pk:  # فقط برای رکوردهای جدید
            self.clean()
            # افزایش موجودی
            self.usage.medicine.quantity += self.quantity
            self.usage.medicine.save()
            
            # بروزرسانی مصرف
            self.usage.quantity -= self.quantity
            self.usage.save()
        
        super().save(*args, **kwargs) 