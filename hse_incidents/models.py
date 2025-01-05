# models.py
from django.db import models
from django.contrib.auth.models import User
from accounts.models import UserProfile
from contractor_management.models import Contractor
from shift_manager.utils import get_current_shift_and_group_without_user
from django.utils import timezone


class IncidentReport(models.Model):
    incident_date = models.DateField("تاریخ وقوع حادثه")
    incident_time = models.TimeField("ساعت وقوع")
    incident_location = models.TextField("محل وقوع")

    involved_person = models.ManyToManyField(UserProfile, blank=True, verbose_name="شخص/اشخاص مرتبط با حادثه",
                                             related_name="involved_in_incidents")
    involved_equipment = models.TextField("تجهیزات مرتبط با حادثه", blank=True, null=True)

    injury_type_choices = [
        ('جراحت', 'جراحت و بریدگی'),
        ('شکستگی', 'شکستگی'),
        ('سوختگی', 'سوختگی'),
        ('نقص_عضو', 'نقص عضو'),
        ('فوت', 'فوت')
    ]
    injury_type = models.ManyToManyField('InjuryType', blank=True, verbose_name="نوع جراحت",
                                         related_name="incident_reports")
    affected_body_part = models.CharField("عضو آسیب دیده", max_length=100)
    damage_description = models.TextField("شرح آسیب وارده")

    related_entity_choices = [
        ('کاراوران', 'شرکت کاراوران'),
        ('پیمانکار', 'پیمانکاران')
    ]
    related_entity = models.CharField("نوع ارتباط", max_length=10, choices=related_entity_choices)
    related_contractor = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,
                                           verbose_name="پیمانکار")

    fire_truck_needed = models.BooleanField("آیا خودرو آتش نشانی اعزام گردید", default=False)
    ambulance_needed = models.BooleanField("آیا آمبولانس اعزام گردید", default=False)
    hospitalized = models.BooleanField("آیا فرد حادثه به بیمارستان اعزام گردید", default=False)
    transportation_type_choices = [
        ('آمبولانس', 'آمبولانس'),
        ('خودرو_شخصی', 'خودرو شخصی')
    ]
    transportation_type = models.CharField("نوع وسیله نقلیه", max_length=15, choices=transportation_type_choices,
                                           blank=True, null=True)

    full_description = models.TextField("شرح کامل حادثه با ذکر جزئیات")
    initial_cause = models.TextField("علت وقوع حادثه در بررسی های اولیه انجام شده")

    report_author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="فرد گزارش دهنده", related_name="authored_incidents")
    report_date = models.DateTimeField(default=timezone.now, editable=False, verbose_name="تاریخ ثبت گزارش")
    report_shift = models.CharField(max_length=20, blank=True, verbose_name="شیفت ثبت گزارش", editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"گزارش حادثه #{self.id}"

    def save(self, *args, **kwargs):
        current_shift, group = get_current_shift_and_group_without_user()
        if current_shift:
            self.report_shift = current_shift
        super().save(*args, **kwargs)


class InjuryType(models.Model):
    name = models.CharField(max_length=100, verbose_name="نوع جراحت")

    def __str__(self):
        return self.name