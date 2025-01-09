# models.py
from django.db import models
from django.utils import timezone
from accounts.models import UserProfile
from contractor_management.models import Contractor, Employee

class InjuryType(models.Model):
    name = models.CharField(max_length=255, verbose_name="نوع جراحت")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نوع جراحت"
        verbose_name_plural = "انواع جراحت"

class IncidentReport(models.Model):
    incident_date = models.DateField(verbose_name="تاریخ وقوع حادثه")
    incident_time = models.TimeField(verbose_name="ساعت وقوع حادثه")
    incident_location = models.TextField(verbose_name="محل وقوع حادثه")
    involved_person = models.ManyToManyField(UserProfile, blank=True, related_name="involved_incidents",
                                            verbose_name="اشخاص مرتبط با حادثه")
    involved_equipment = models.TextField(blank=False, default="", verbose_name="تجهیزات مرتبط با حادثه")
    injury_type = models.ManyToManyField(InjuryType, blank=True, related_name="incidents", verbose_name="نوع جراحت")
    affected_body_part = models.CharField(max_length=255, verbose_name="عضو آسیب دیده")
    damage_description = models.TextField(verbose_name="شرح آسیب وارده")
    related_entity = models.CharField(max_length=255, verbose_name="نوع ارتباط")
    related_contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name="incidents", verbose_name="پیمانکار مرتبط")
    related_contractor_employees = models.ManyToManyField(Employee, blank=True, related_name="contractor_incidents",
                                                         verbose_name="پرسنل پیمانکار مرتبط")
    fire_truck_needed = models.BooleanField(default=False, verbose_name="خودرو آتش نشانی اعزام گردید؟")
    fire_truck_arrival_time = models.TimeField(null=True, blank=True, verbose_name="زمان رسیدن خودرو آتش نشانی")
    ambulance_needed = models.BooleanField(default=False, verbose_name="آمبولانس اعزام گردید؟")
    ambulance_arrival_time = models.TimeField(null=True, blank=True, verbose_name="زمان رسیدن آمبولانس")
    hospitalized = models.BooleanField(default=False, verbose_name="فرد به بیمارستان اعزام گردید؟")
    hospitalized_time = models.TimeField(null=True, blank=True, verbose_name="زمان اعزام به بیمارستان")
    transportation_type = models.CharField(max_length=255, blank=True, verbose_name="نوع وسیله نقلیه جهت اعزام")
    full_description = models.TextField(verbose_name="شرح کامل حادثه با ذکر جزئیات")
    initial_cause = models.TextField(verbose_name="علت وقوع حادثه در بررسی های اولیه انجام شده")
    report_author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name="authored_incidents",
                                     verbose_name="نویسنده گزارش")

    def __str__(self):
        return f"گزارش حادثه {self.incident_date} - {self.incident_location}"

    class Meta:
        verbose_name = "گزارش حادثه"
        verbose_name_plural = "گزارشات حوادث"