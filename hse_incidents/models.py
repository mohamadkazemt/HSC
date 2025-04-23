# hse_incidents/models.py
from django.db import models
from django.utils import timezone
from accounts.models import UserProfile
from contractor_management.models import Contractor, Employee
from anomalis.models import Location, LocationSection


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
    # حذف فیلد incident_location
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="سایت حادثه")
    section = models.ForeignKey(LocationSection, on_delete=models.SET_NULL, null=True, blank=True,
                                verbose_name="محل حادثه")
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
    report_author = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True,
                                      related_name="authored_incidents",
                                      verbose_name="نویسنده گزارش")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")


class HseCompletionReport(models.Model):
    incident_report = models.OneToOneField(IncidentReport, on_delete=models.CASCADE, related_name='hse_completion',verbose_name="گزارش حادثه")
    incident_report_time = models.TimeField(null=True, blank=True, verbose_name="ساعت اعلام حادثه")
    hospital_admission_time = models.TimeField(null=True, blank=True, verbose_name="ساعت پذیرش در بیمارستان")
    # فیلدهای جدید برای شرح حال
    patient_condition_temperature = models.CharField(max_length=10, null=True, blank=True, verbose_name="دمای بدن")
    patient_condition_respiration = models.CharField(max_length=10, null=True, blank=True, verbose_name="تعداد تنفس")
    patient_condition_pulse = models.CharField(max_length=10, null=True, blank=True, verbose_name="نبض")
    patient_condition_blood_pressure = models.CharField(max_length=10, null=True, blank=True, verbose_name="فشار خون")
    patient_condition_sop = models.CharField(max_length=100, null=True, blank=True, verbose_name="وضعیت هوشیاری")

    direct_causes = models.TextField(null=True, blank=True, verbose_name="علل مستقیم بروز حادثه")
    indirect_causes = models.TextField(null=True, blank=True, verbose_name="علل غیر مستقیم بروز حادثه")
    root_causes = models.TextField(null=True, blank=True, verbose_name="علل ریشه ای بروز حادثه")

    social_security_notification = models.BooleanField(default=False, verbose_name="اعلام به بیمه تامین اجتماعی")
    social_security_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست فایل بیمه تامین اجتماعی")

    insurance_notification = models.BooleanField(default=False, verbose_name="اعلام به شرکت های بیمه ای")
    insurance_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست فایل شرکت های بیمه")

    police_notification = models.BooleanField(default=False, verbose_name="اعلام به نیروی انتظامی")
    police_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست فایل نیروی انتظامی")

    traffic_police_notification = models.BooleanField(default=False, verbose_name="اعلام به راهنمایی و رانندگی")
    traffic_police_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست فایل راهنمایی و رانندگی")


    labor_office_notification = models.BooleanField(default=False, verbose_name="اعلام به اداره کار")

    final_injury_outcome = models.TextField(null=True, blank=True, verbose_name="نتیجه نهایی آسیب های ناشی از حادثه")
    estimated_cost = models.CharField(max_length=255, null=True, blank=True, verbose_name="برآورد هزینه تقریبی")
    lost_workdays = models.PositiveIntegerField(null=True, blank=True, verbose_name="روزهای کاری از دست رفته")

    environmental_damage = models.BooleanField(default=False, verbose_name="آسیب به محیط زیست دارد؟")
    environmental_damage_type = models.CharField(max_length=255, null=True, blank=True, verbose_name="نوع آسیب به محیط زیست")
    environmental_damage_description = models.TextField(null=True, blank=True, verbose_name="شرح مختصر آسیب وارد شده به محیط زیست")

    incident_committee_formed = models.BooleanField(default=False, verbose_name="کمیته حوادث تشکیل گردید؟")
    incident_committee_date = models.DateField(null=True, blank=True, verbose_name="تاریخ برگزاری کمیته حوادث")
    incident_committee_details = models.TextField(null=True, blank=True, verbose_name="شرح مختصر جزئیات کمیته حوادث")
    incident_committee_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست صورتجلسه کمیته حوادث")

    corrective_actions = models.TextField(null=True, blank=True, verbose_name="اقدامات اصلاحی و پیشگیرانه")
    lessons_learned = models.BooleanField(default=False, verbose_name="درس آموزی از حادثه دارد؟")
    lessons_learned_file = models.FileField(upload_to='incident_files/', null=True, blank=True, verbose_name="پیوست درس آموزی حادثه")

    class Meta:
        verbose_name = "گزارش تکمیل حادثه"
        verbose_name_plural = "گزارشات تکمیل حوادث"