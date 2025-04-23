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
    section = models.ForeignKey('Section', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="بخش")
    part = models.ForeignKey('Part', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="قسمت")
    unit_group = models.ForeignKey('UnitGroup', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="گروه")
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="سمت")
    group = models.CharField(max_length=2, choices=GROUP_CHOICES, blank=True, verbose_name="گروه کاری")
    mobile = models.CharField(max_length=11, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_generated_at = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='profile_pics', blank=True)
    signature = models.ImageField(upload_to='signatures/', blank=True, null=True, verbose_name="امضای کاربر")

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.code_generated_at = now()
        self.save()

    def save(self, *args, **kwargs):
        if self.signature and hasattr(self.signature, 'file'):
            try:
                # حذف پس‌زمینه تصویر امضا
                img_no_bg = remove_background(self.signature.file)
                if img_no_bg:
                    # ذخیره تصویر بدون پس‌زمینه
                    buffer = BytesIO()
                    img_no_bg.save(buffer, format='PNG')
                    filename = f'{os.path.splitext(self.signature.name)[0]}_no_bg.png'
                    contentfile = ContentFile(buffer.getvalue())
                    self.signature.save(filename, contentfile, save=False)
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
    front_image = models.ImageField(upload_to='license_images/', verbose_name='عکس روی گواهینامه')
    back_image = models.ImageField(upload_to='license_images/', verbose_name='عکس پشت گواهینامه')
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