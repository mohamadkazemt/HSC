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