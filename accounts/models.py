# models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    GROUP_CHOICES = [
        ('A', 'گروه A'),
        ('B', 'گروه B'),
        ('C', 'گروه C'),
        ('D', 'گروه D'),
        ('G', 'گروه G'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    # اول بدون unique اضافه میکنیم
    personnel_code = models.CharField(max_length=10, default='', blank=True, verbose_name='کد پرسنلی')
    image = models.ImageField(upload_to='profile_pics', blank=True)
    mobile = models.CharField(max_length=11, blank=True)
    group = models.CharField(max_length=1, choices=GROUP_CHOICES, blank=True)

    def __str__(self):
        name = f'{self.user.first_name} {self.user.last_name} {self.personnel_code}'.strip()
        return name if name else self.user.username

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل کاربران'