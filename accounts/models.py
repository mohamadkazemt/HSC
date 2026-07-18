# models.py
from django.db import models
from django.contrib.auth.models import User
import random
from django.utils.timezone import now
from datetime import timedelta
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
import os
import uuid
from core.validators import validate_image_file, validate_signature_image

def remove_background(image_file):
    try:
        img = Image.open(image_file)
        # تبدیل تصویر به حالت RGBA
        img = img.convert('RGBA')
        
        # پیکسل‌های سفید و نزدیک به سفید را شفاف می‌کنیم
        data = img.getdata()
        new_data = []
        for item in data:
            # اگر پیکسل نزدیک به سفید است
            if item[0] > 240 and item[1] > 240 and item[2] > 240:
                # آن را کاملاً شفاف می‌کنیم
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
                
        img.putdata(new_data)
        return img
    except Exception as e:
        print(f"خطا در حذف پس‌زمینه: {str(e)}")
        return None

class UserProfile(models.Model):
    GROUP_CHOICES = [
        ('A', 'گروه A'),
        ('B', 'گروه B'),
        ('C', 'گروه C'),
        ('D', 'گروه D'),
        ('G', 'گروه G'),
        ('G2', 'گروه G2'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    personnel_code = models.CharField(max_length=10, default='', blank=True, verbose_name='کد پرسنلی')
    national_code = models.CharField(max_length=10, blank=True, null=True, verbose_name='کد ملی')
    section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بخش")
    part = models.ForeignKey('Part', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="قسمت")
    unit_group = models.ForeignKey('UnitGroup', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="گروه")
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سمت")
    group = models.CharField(max_length=2, choices=GROUP_CHOICES, blank=True, verbose_name="گروه کاری")
    unit = models.CharField(max_length=100, blank=True, verbose_name="واحد")
    workshop_job_title = models.CharField(max_length=150, blank=True, verbose_name="عنوان شغل کارگاه")
    birth_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تولد")
    marital_status = models.CharField(max_length=30, blank=True, verbose_name="وضعیت تاهل")
    father_name = models.CharField(max_length=150, blank=True, verbose_name="نام پدر")
    children_count = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="تعداد فرزندان")
    hire_date = models.DateField(null=True, blank=True, verbose_name="تاریخ استخدام")
    education_level = models.CharField(max_length=100, blank=True, verbose_name="مقطع تحصیلی")
    field_of_study = models.CharField(max_length=150, blank=True, verbose_name="رشته تحصیلی")
    place_of_birth = models.CharField(max_length=100, blank=True, verbose_name="محل تولد")
    military_service_status = models.CharField(max_length=50, blank=True, verbose_name="وضعیت خدمت سربازی")
    work_experience_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="سابقه کار (روز)")
    mobile = models.CharField(max_length=11, blank=True, verbose_name="شماره تماس")
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_generated_at = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='profile_pics', blank=True, validators=[validate_image_file])
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True, verbose_name="امضای کاربر", validators=[validate_signature_image])

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.code_generated_at = now()
        self.save()

    def save(self, *args, **kwargs):
        """
        Only process the signature image when a NEW file is uploaded in the current request.
        This avoids FileNotFoundError when the previous file is missing and prevents nested paths.
        """
        # Check if signature is a new uploaded file
        # In Django, when a new file is uploaded, the field contains an UploadedFile object with .file attribute
        # When editing without uploading, it's a FieldFile object (existing file) without .file attribute
        signature_is_new_upload = (
            getattr(self, 'signature', None) and 
            hasattr(self.signature, 'file')
        )

        if signature_is_new_upload:
            try:
                # حذف پس‌زمینه تصویر امضا - work directly with in-memory uploaded file
                img_no_bg = remove_background(self.signature.file)
                if img_no_bg:
                    # ذخیره تصویر بدون پس‌زمینه با جلوگیری از مسیر تو در تو
                    buffer = BytesIO()
                    img_no_bg.save(buffer, format='PNG')
                    new_name = self.signature.name if hasattr(self.signature, 'name') else 'signature.png'
                    base = os.path.splitext(os.path.basename(new_name))[0]
                    filename = f'{base}_no_bg.png'
                    # Get upload_to from the model field definition
                    signature_field = self._meta.get_field('signature')
                    upload_dir = 'signatures/'  # Default from field definition
                    if hasattr(signature_field, 'upload_to'):
                        upload_dir = signature_field.upload_to
                        if callable(upload_dir):
                            # If upload_to is a callable, use default directory
                            upload_dir = 'signatures/'
                    # Ensure we save back into the original upload_to directory (e.g., 'signatures/')
                    final_name = os.path.join(upload_dir.strip('/'), filename) if upload_dir else filename
                    contentfile = ContentFile(buffer.getvalue())
                    self.signature.save(final_name, contentfile, save=False)
            except Exception as e:
                print(f"خطا در پردازش تصویر: {str(e)}")

        super().save(*args, **kwargs)

    def __str__(self):
        name = f'{self.user.first_name} {self.user.last_name} {self.personnel_code}'.strip()
        return name if name else self.user.username

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل کاربران'


class Section(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام بخش")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "بخش"
        verbose_name_plural = "بخش‌ها"


class Part(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, verbose_name="بخش",null=True, blank=True)
    name = models.CharField(max_length=50, verbose_name="نام قسمت")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "قسمت"
        verbose_name_plural = "قسمت‌ها"

class UnitGroup(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name="قسمت",null=True, blank=True)
    name = models.CharField(max_length=50, verbose_name="نام گروه")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "گروه"
        verbose_name_plural = "گروه‌ها"


class Position(models.Model):
    unit_group = models.ForeignKey(UnitGroup, on_delete=models.CASCADE, verbose_name="گروه", blank=True, null=True)
    name = models.CharField(max_length=50, verbose_name="نام سمت")
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "سمت"
        verbose_name_plural = "سمت‌ها"

class DriverLicense(models.Model):
    LICENSE_BASE_CHOICES = [
        ('1', 'پایه یک'),
        ('2', 'پایه دو'),
        ('3', 'پایه سه'),
    ]
    
    SPECIAL_CODES = [
        ('38', 'لیفتراک'),
        ('37', 'تراکتور'),
        ('36', 'گریدر'),
        ('39', 'لودر'),
        ('56', 'بکهو'),
        ('52', 'بیل مکانیکی'),
        ('47', 'دامپر'),
        ('42', 'جرثقیل'),
        ('43', 'بلدوزر'),
        ('54', 'دامپتراک'),
        ('53', 'چکش تخریب'),
        ('48', 'فینیشر'),
        ('45', 'کامباین'),
        ('46', 'آسفالت تراش'),
        ('41', 'غلطک'),
        ('62', 'شاول'),
        ('63', 'دریل حفاری'),
        ('61', 'دریل واگن'),
        ('55', 'اسکیپر'),
        ('57', 'اسکریپر'),
        ('49', 'مینی لودر'),
        ('65', 'بالابر تلسکوپی'),
        ('55', 'ریچ استاکر'),
        ('51', 'ساید بوم'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_license')
    license_base = models.CharField(max_length=1, choices=LICENSE_BASE_CHOICES, verbose_name='پایه گواهینامه')
    expiry_date = models.DateField(verbose_name='تاریخ انقضا')
    has_special = models.BooleanField(default=False, verbose_name='ویژه دارد')
    special_codes = models.JSONField(default=list, blank=True, verbose_name='کدهای ویژه')
    front_image = models.ImageField(upload_to='license_images/', verbose_name='عکس روی گواهینامه', validators=[validate_image_file])
    back_image = models.ImageField(upload_to='license_images/', verbose_name='عکس پشت گواهینامه', validators=[validate_image_file])
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'گواهینامه {self.user.get_full_name()} - پایه {self.get_license_base_display()}'

    class Meta:
        verbose_name = 'گواهینامه'
        verbose_name_plural = 'گواهینامه‌ها'

    def is_complete(self):
        """بررسی کامل بودن اطلاعات گواهینامه"""
        return all([
            self.license_base,
            self.expiry_date,
            self.front_image,
            self.back_image,
            (not self.has_special or (self.has_special and self.special_codes))
        ])


def payslip_upload_path(instance, filename):
    """تولید مسیر امن برای فایل فیش حقوقی با نام تصادفی"""
    # استفاده از UUID برای نام فایل برای امنیت بیشتر
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f'payslips/{instance.year}/{instance.month:02d}/{filename}'


class Payslip(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='payslips', verbose_name="پروفایل کاربر")
    file = models.FileField(upload_to=payslip_upload_path, verbose_name="فایل فیش حقوقی")
    month = models.IntegerField(verbose_name="ماه")
    year = models.IntegerField(verbose_name="سال")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ بارگذاری")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="بارگذاری شده توسط")

    class Meta:
        verbose_name = "فیش حقوقی"
        verbose_name_plural = "فیش‌های حقوقی"
        unique_together = ('user_profile', 'year', 'month')  # جلوگیری از ثبت فیش تکراری برای یک ماه
        ordering = ['-year', '-month']

    def __str__(self):
        return f"فیش حقوقی {self.user_profile.user.get_full_name()} برای {self.year}/{self.month}"
