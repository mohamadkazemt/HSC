from django.db import models
from django.contrib.auth.models import User
from django.conf import settings





# Create your models here.
class UserProfile(models.Model):
    GROUP_CHOICES = [
        ('A', 'گروه A'),
        ('B', 'گروه B'),
        ('C', 'گروه C'),
        ('D', 'گروه D'),
        ('G', 'گروه G'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    image = models.ImageField(upload_to='profile_pics', blank=True)
    mobile = models.CharField(max_length=10, blank=True)
    group = models.CharField(max_length=1, choices=GROUP_CHOICES, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'