from django.db import models
from django.core.exceptions import ValidationError

class MineralType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام سنگ معدنی")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع سنگ معدنی"
        verbose_name_plural = "انواع سنگ‌های معدنی"

class Contractor(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام پیمانکار")
    contact_info = models.CharField(max_length=255, verbose_name="اطلاعات تماس", blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "پیمانکار"
        verbose_name_plural = "پیمانکاران"


class ContractorVehicle(models.Model):
    OWNERSHIP_CHOICES = [
        ('Company', 'شرکت'),
        ('Contractor', 'پیمانکار'),
    ]
    number_car = models.CharField(max_length=15, unique=True, null=True, blank=True, verbose_name="شماره خودرو")
    vehicle_name = models.CharField(max_length=100, verbose_name="نام خودرو")
    license_plate = models.CharField(max_length=15, unique=True, verbose_name="پلاک خودرو")
    vehicle_type = models.CharField(max_length=50, choices=[('pickup truck', 'وانت'), ('riding', 'سواری'), ('bus', 'اتوبوس'), ('minibus', 'مینی بوس'), ('van', 'ون')], verbose_name="نوع خودرو")
    ownership = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES, null=True, blank=True, verbose_name="مالکیت")
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="پیمانکار",
                                   help_text="در صورت مالکیت پیمانکار، پیمانکار را انتخاب کنید.")
    is_active = models.BooleanField(default=True, verbose_name="فعال")


    def __str__(self):
        return f"{self.vehicle_name} - {self.contractor.name}"

    class Meta:
        verbose_name = "خودرو"
        verbose_name_plural = "خودروها"

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
    ownership = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="مالکیت")
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
        return f"{self.block_name} - {self.get_status_display()}"

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




