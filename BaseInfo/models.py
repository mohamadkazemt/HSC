from django.db import models
from django.core.exceptions import ValidationError



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


# مدل اصلی برای دستگاه‌های معدنی
class MiningMachine(models.Model):
    MACHINE_TYPE_CHOICES = [
        ('Loader', 'بارکننده'),
        ('Transporter', 'حمل کننده'),
        ('RoadBuilder', 'جاده سازی'),
        ('Driller', 'حفاری'),
    ]
    OWNERSHIP_CHOICES = [
        ('Company', 'شرکت'),
        ('Contractor', 'پیمانکار'),
    ]

    machine_type = models.CharField(max_length=20, choices=MACHINE_TYPE_CHOICES, verbose_name="نوع دستگاه")
    machine_name = models.CharField(max_length=100, verbose_name="نام دستگاه")
    workshop_code = models.CharField(max_length=20, verbose_name="کد کارگاهی")  # کد کارگاهی
    ownership = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES, verbose_name="مالکیت")
    contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="پیمانکار",
                                   help_text="در صورت مالکیت پیمانکار، پیمانکار را انتخاب کنید.")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return f"{self.machine_name} - {self.get_machine_type_display()}"


    def clean(self):
        # بررسی برای انتخاب پیمانکار در صورت مالکیت پیمانکار
        if self.ownership == 'Contractor' and not self.contractor:
            raise ValidationError('لطفاً پیمانکار را برای این دستگاه انتخاب کنید.')
        # بررسی عدم انتخاب پیمانکار در صورت مالکیت شرکت
        if self.ownership == 'Company' and self.contractor:
            raise ValidationError('اگر مالکیت شرکت است، نباید پیمانکار انتخاب شود.')


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
