from django.db import models
from django.core.exceptions import ValidationError

from contractor_management.models import Contractor


class MineralType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام سنگ معدنی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع سنگ معدنی"
        verbose_name_plural = "انواع سنگ‌های معدنی"




class MachineryWorkGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام گروه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "گروه کاری"
        verbose_name_plural = "گروه‌های کاری"

class TypeMachine(models.Model):
    machine_workgroup = models.ForeignKey(MachineryWorkGroup, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="گروه کاری")
    name = models.CharField(max_length=100, verbose_name="نوع دستگاه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع دستگاه"
        verbose_name_plural = "نوع های دستگاه"


# مدل اصلی برای دستگاه‌های معدنی
class MiningMachine(models.Model):
    machine_workgroup = models.ForeignKey(MachineryWorkGroup, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="گروه کاری")
    machine_type = models.ForeignKey(TypeMachine, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="نوع دستگاه")
    workshop_code = models.CharField(max_length=20, verbose_name="کد کارگاهی")  # کد کارگاهی
    ownership = models.CharField(max_length=10, choices=[('Company', 'شرکت'), ('Contractor', 'پیمانکار')], default='Company', verbose_name="مالکیت")
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پیمانکار")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return f"{self.workshop_code} - {self.machine_type.name}"

    class Meta:
        verbose_name = "دستگاه معدنی"
        verbose_name_plural = "دستگاه های معدنی"


class MiningBlock(models.Model):
    BLOCK_STATUS_CHOICES = [
        ('initial_preparation', 'آماده سازی اولیه'),
        ('ready_for_drilling', 'آماده حفاری'),
        ('ready_for_blasting', 'آماده آتش باری'),
        ('ready_for_loading', 'آماده بارگیری'),
        ('loading', 'در حال بارگیری'),
        ('completed', 'اتمام بلوک'),
    ]
    BLOCK_TYPE_CHOICES = [
        ('w', 'باطله'),
        ('o', 'سنگ پرعیار'),
        ('w&o', 'ترکیبی')
    ]

    block_name = models.CharField(max_length=100, verbose_name="نام بلوک")
    type = models.CharField(max_length=20, choices=BLOCK_TYPE_CHOICES,default='w', verbose_name="نوع بلوک سنگ")
    status = models.CharField(max_length=20, choices=BLOCK_STATUS_CHOICES, default='initial_preparation',
                              verbose_name="وضعیت بلوک")
    location = models.CharField(max_length=255, verbose_name="موقعیت بلوک", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return f"{self.block_name}"

    class Meta:
        verbose_name = "بلوک معدنی"
        verbose_name_plural = "بلوک‌های معدنی"


class Dump(models.Model):
    dump_name = models.CharField(max_length=100, verbose_name="نام دمپ")
    location = models.CharField(max_length=255, verbose_name="موقعیت دمپ", blank=True)
    mineral_type = models.ForeignKey(MineralType, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="نوع سنگ معدنی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return self.dump_name

    class Meta:
        verbose_name = "دمپ"
        verbose_name_plural = "دمپ‌ها"


class EmergencyVehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('fire_truck', 'خودروی آتش‌نشانی'),
        ('ambulance', 'آمبولانس'),
        ('rescue', 'خودروی امداد و نجات'),
    ]

    STATUS_CHOICES = [
        ('active', 'فعال'),
        ('inactive', 'غیرفعال'),
        ('maintenance', 'در حال تعمیر'),
    ]

    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, verbose_name="نوع خودرو")
    workshop_code = models.CharField(max_length=20, unique=True, verbose_name="کد کارگاهی")
    license_plate = models.CharField(max_length=20, unique=True, verbose_name="شماره پلاک")
    model = models.CharField(max_length=100, verbose_name="مدل خودرو")
    manufacture_year = models.IntegerField(verbose_name="سال ساخت")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name="وضعیت")
    last_maintenance_date = models.DateField(null=True, blank=True, verbose_name="تاریخ آخرین سرویس")
    next_maintenance_date = models.DateField(null=True, blank=True, verbose_name="تاریخ سرویس بعدی")
    insurance_expiry = models.DateField(null=True, blank=True, verbose_name="تاریخ انقضای بیمه")
    technical_inspection_expiry = models.DateField(null=True, blank=True, verbose_name="تاریخ انقضای معاینه فنی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    # فیلدهای جدید برای کنترل نمایش تجهیزات
    has_horn = models.BooleanField(default=True, verbose_name="دارای بوق و چراغ گردان")
    has_hose = models.BooleanField(default=True, verbose_name="دارای شیلنگ و اتصالات")
    has_monitor = models.BooleanField(default=True, verbose_name="دارای مانیتور")
    has_extinguisher = models.BooleanField(default=True, verbose_name="دارای خاموش‌کننده دستی")
    has_equipment = models.BooleanField(default=True, verbose_name="دارای تجهیزات آتش‌نشانی")
    has_foam = models.BooleanField(default=True, verbose_name="دارای پودر و فوم")
    has_water = models.BooleanField(default=True, verbose_name="دارای آب")
    has_tire = models.BooleanField(default=True, verbose_name="دارای لاستیک")
    has_brake = models.BooleanField(default=True, verbose_name="دارای سیستم ترمز")
    has_lighting = models.BooleanField(default=True, verbose_name="دارای سیستم روشنایی")

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.workshop_code}"

    class Meta:
        verbose_name = "خودروی امدادی"
        verbose_name_plural = "خودروهای امدادی"




