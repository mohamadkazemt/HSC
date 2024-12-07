from django.db import models
from django_jalali.db import models as jmodels  # برای تاریخ شمسی



class Contractor(models.Model):
    company_name = models.CharField(max_length=255, verbose_name="نام شرکت/پیمانکار")
    manager_name = models.CharField(max_length=255, verbose_name="نام مدیرعامل")
    activity_field = models.CharField(max_length=255, verbose_name="حوزه فعالیت")
    manager_phone = models.CharField(max_length=15, verbose_name="شماره تماس مدیرعامل")
    liability_insurance = models.BooleanField(default=False, verbose_name="بیمه مسئولیت مدنی")
    liability_insurance_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای بیمه مسئولیت مدنی")
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True, verbose_name="قرارداد پیوست شده")
    fire_insurance = models.BooleanField(default=False, verbose_name="بیمه آتش‌سوزی")
    fire_insurance_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای بیمه آتش‌سوزی")
    contractor_certificate_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای صلاحیت پیمانکاری")
    safety_certificate_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای صلاحیت ایمنی")
    hse_plan = models.BooleanField(default=False, verbose_name="طرح ایمنی، بهداشت و محیط زیست")
    hse_plan_file = models.FileField(upload_to='hse_plans/', null=True, blank=True, verbose_name="طرح ایمنی، بهداشت و محیط زیست")
    social_insurance = models.BooleanField(default=False, verbose_name="بیمه تامین اجتماعی")
    number_of_social_insurance = models.CharField(max_length=255, verbose_name="شماره بیمه تامین اجتماعی")

    def __str__(self):
        return self.company_name

    class Meta:
        verbose_name = "پیمانکار"
        verbose_name_plural = "پیمانکاران"


class Employee(models.Model):
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name="employees", verbose_name="پیمانکار")
    first_name = models.CharField(max_length=255, verbose_name="نام")
    last_name = models.CharField(max_length=255, verbose_name="نام خانوادگی")
    national_id = models.CharField(max_length=10, unique=True, verbose_name="کد ملی")
    card_national_img = models.FileField(upload_to='card_national_imgs/', null=True, blank=True, verbose_name="تصویر کارت ملی")
    certificate_img = models.FileField(upload_to='certificate_national_imgs/', null=True, blank=True, verbose_name="تصویر شناسنامه")
    birth_date = jmodels.jDateField(verbose_name="تاریخ تولد")
    phone_number = models.CharField(max_length=15, verbose_name="شماره تماس")
    education = models.CharField(max_length=255, verbose_name="مدرک تحصیلی")
    position = models.CharField(max_length=255, verbose_name="سمت")  # فیلد متنی آزاد
    number_of_insurance = models.CharField(max_length=255, verbose_name="شماره بیمه تامین اجتماعی")
    health_certificate = models.FileField(upload_to='health_certificates/', null=True, blank=True, verbose_name="معاینات سلامت شغلی")
    background_check = models.FileField(upload_to='background_checks/', null=True, blank=True, verbose_name="سو پیشینه و عدم اعتیاد")
    safety_training = models.FileField(upload_to='safety_training/', null=True, blank=True, verbose_name="دوره آموزش ایمنی عمومی")
    other_trainings = models.TextField(null=True, blank=True, verbose_name="سایر آموزش‌های فراگرفته")
    entry_permit_expiration = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای مجوز ورود")

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"


    class Meta:
        verbose_name = "کارمند"
        verbose_name_plural = "کارمندان"

class Vehicle(models.Model):
    contractor = models.ForeignKey(Contractor, on_delete=models.CASCADE, related_name="vehicles", verbose_name="پیمانکار")
    vehicle_type = models.CharField(max_length=255, verbose_name="نوع خودرو")
    vehicle_code = models.CharField(max_length=255, blank=True, null=True, verbose_name="کد کارگاهی خودرو")
    license_plate = models.CharField(max_length=20, unique=True, verbose_name="شماره پلاک خودرو")
    vehicle_card = models.FileField(upload_to='vehicle_cards/', null=True, blank=True, verbose_name="کارت خودرو")
    insurance_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای بیمه‌نامه")
    technical_inspection_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای معاینه فنی")
    driver_name = models.CharField(max_length=255, verbose_name="نام راننده")
    permit_expiry = jmodels.jDateField(null=True, blank=True, verbose_name="تاریخ انقضای آخرین مجوز خودرو")

    def __str__(self):
        return self.license_plate

    class Meta:
        verbose_name = "خودرو"
        verbose_name_plural = "خودروها"