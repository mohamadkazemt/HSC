from django.contrib.auth.models import User
from django.db import models

from accounts.models import UserProfile


class Location(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "محل آنومالی"
        verbose_name_plural = "محل‌های آنومالی"

    def __str__(self):
        return self.name


class Anomalytype(models.Model):
    type = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        verbose_name = "نوع آنومالی"
        verbose_name_plural = "نوع‌های آنومالی"

    def __str__(self):
        return self.type



class HSE(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        verbose_name = "نوع آنومالی HSE"
        verbose_name_plural = "نوع‌های آنومالی HSE"

    def __str__(self):
        return self.name




class AnomalyDescription(models.Model):

    description = models.TextField(max_length=500, verbose_name="شرح آنومالی")
    anomalytype = models.ForeignKey(Anomalytype, on_delete=models.CASCADE, verbose_name="نوع آنومالی")
    hse_type = models.CharField(
        max_length=1,
        choices=[('H', 'Health'), ('S', 'Safety'), ('E', 'Environment')],
        verbose_name="نوع HSE"
    )

    class Meta:
        verbose_name = "شرح آنومالی"
        verbose_name_plural = "شرح‌های آنومالی"



    def __str__(self):
        return self.description



class CorrectiveAction(models.Model):
    anomali_type = models.ForeignKey(AnomalyDescription, on_delete=models.CASCADE, verbose_name="نوع آنومالی")
    description = models.TextField(max_length=500, verbose_name="شرح عملیات اصلاحی")

    class Meta:
        verbose_name = "عملیات اصلاحی"
        verbose_name_plural = "عملیات‌های اصلاحی"

    def __str__(self):
        return self.description



class Priority(models.Model):
    priority = models.CharField(max_length=20,verbose_name='اولویت')

    class Meta:
        verbose_name = 'اولویت '
        verbose_name_plural = 'اولویت ها'

    def __str__(self):
        return  self.priority





class Anomaly(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, verbose_name="محل آنومالی")
    anomalytype = models.ForeignKey(Anomalytype, on_delete=models.CASCADE, verbose_name="نوع آنومالی")
    anomalydescription = models.ForeignKey(AnomalyDescription, on_delete=models.CASCADE, verbose_name="شرح آنومالی")
    hse_type = models.CharField(max_length=1, choices=[('H', 'Health'), ('S', 'Safety'), ('E', 'Environment')], verbose_name="نوع HSE")
    correctiveaction = models.ForeignKey(CorrectiveAction, on_delete=models.CASCADE, verbose_name="عملیات اصلاحی")
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='created_anomalies', verbose_name="ایجاد کننده")
    followup = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='followup_anomalies', verbose_name="پیگیری")
    group = models.CharField(max_length=1, choices=UserProfile.GROUP_CHOICES, verbose_name="گروه کاری")
    description = models.TextField(verbose_name="شرح آنومالی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    action = models.BooleanField(default=True, verbose_name="وضعیت")
    priority = models.ForeignKey(Priority, on_delete=models.CASCADE, verbose_name="اولویت")
    image = models.ImageField(upload_to='anomalies/%Y/%m/%d', verbose_name="تصویر آنومالی", blank=True, null=True)





    class Meta:
        verbose_name = "آنومالی"
        verbose_name_plural = "آنومالی ها"

    def __str__(self):
        return self.description