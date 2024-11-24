# models.py
from django.db import models
from django.contrib.auth.models import User
import random
from django.utils.timezone import now
from datetime import timedelta

class UserProfile(models.Model):
    GROUP_CHOICES = [
        ('A', 'گروه A'),
        ('B', 'گروه B'),
        ('C', 'گروه C'),
        ('D', 'گروه D'),
        ('G', 'گروه G'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    personnel_code = models.CharField(max_length=10, default='', blank=True, verbose_name='کد پرسنلی')
    image = models.ImageField(upload_to='profile_pics', blank=True)
    mobile = models.CharField(max_length=11, blank=True)
    group = models.CharField(max_length=1, choices=GROUP_CHOICES, blank=True)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_generated_at = models.DateTimeField(blank=True, null=True)

    def generate_verification_code(self):
        self.verification_code = str(random.randint(100000, 999999))
        self.code_generated_at = now()
        self.save()
    def __str__(self):
        name = f'{self.user.first_name} {self.user.last_name} {self.personnel_code}'.strip()
        return name if name else self.user.username

    class Meta:
        verbose_name = 'پروفایل کاربر'
        verbose_name_plural = 'پروفایل کاربران'