from django.db import models
from accounts.models import Position, UserProfile
from anomalis.models import AnomalyDescription
from hse_incidents.models import InjuryType


class JobTask(models.Model):
    """جزء / فعالیت شغل که می‌تواند در ارزیابی ریسک انتخاب شود"""
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='job_tasks',
        verbose_name="شغل مرتبط"
    )
    name = models.CharField(max_length=150, verbose_name="عنوان فعالیت/جزء")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال؟")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        ordering = ['position', 'order', 'name']
        verbose_name = "جزء فعالیت شغل"
        verbose_name_plural = "اجزای فعالیت مشاغل"
        unique_together = ('position', 'name')

    def __str__(self):
        return f"{self.position.name} - {self.name}"


class RiskAssessment(models.Model):
    """
    مدل ارزیابی ریسک بر اساس ماتریس ۵×۵
    شامل شناسایی خطر، محاسبه ریسک اولیه و باقی‌مانده
    """
    
    # منابع شناسایی ریسک
    SOURCE_CHOICES = [
        ('site_visit', 'بازدیدهای میدانی و آنومالی ریپورت'),
        ('consultation', 'مشارکت و مشاوره کارکنان'),
        ('audit', 'نتایج ممیزی‌ها'),
        ('incidents', 'حوادث و شبه حوادث'),
        ('changes', 'تغییرات'),
        ('physical', 'عوامل فیزیکی'),
        ('chemical', 'عوامل شیمیایی'),
        ('biological', 'عوامل محیط زیستی و بیولوژیکی'),
        ('ergonomic', 'عوامل ارگونومیک و انسانی'),
        ('activities', 'فعالیت‌ها و عملیات کاری'),
        ('energy', 'انرژی‌های خطرناک'),
        ('environmental', 'وضعیت‌های محیطی'),
        ('other', 'سایر'),
    ]
    
    # ماتریس ریسک ۵×۵ - احتمال وقوع
    PROBABILITY_CHOICES = [
        (1, '1 - خیلی کم (کمتر از یک بار در ۵ سال)'),
        (2, '2 - کم (۵ سال یکبار)'),
        (3, '3 - متوسط (وقوع سالیانه)'),
        (4, '4 - زیاد (چند بار در سال)'),
        (5, '5 - خیلی زیاد (چند بار در ماه)'),
    ]
    
    # ماتریس ریسک ۵×۵ - شدت پیامد
    SEVERITY_CHOICES = [
        (1, '1 - آسیب جزئی (بدون استراحت)'),
        (2, '2 - آسیب شدید (1 تا 14 روز استراحت)'),
        (3, '3 - آسیب خیلی شدید (قطع عضو/بیش از 15 روز)'),
        (4, '4 - ناتوانی و از کار افتادگی دائم'),
        (5, '5 - مرگ'),
    ]
    
    # سطوح ریسک
    RISK_LEVEL_CHOICES = [
        ('Low', 'پایین (سبز) - قابل پذیرش'),
        ('Medium', 'متوسط (زرد) - نیاز به کاهش'),
        ('High', 'بالا (قرمز) - غیرقابل پذیرش'),
    ]

    # ====== فیلدهای اصلی شناسایی ======
    position = models.ForeignKey(
        Position, 
        on_delete=models.CASCADE, 
        verbose_name="شغل/سمت", 
        related_name='risk_assessments'
    )

    related_positions = models.ManyToManyField(
        Position,
        blank=True,
        related_name='shared_risks',
        verbose_name="مشاغل مشترک",
        help_text="در صورت مشترک بودن این ریسک در چند شغل دیگر انتخاب کنید"
    )
    
    risk_source = models.CharField(
        max_length=50, 
        choices=SOURCE_CHOICES, 
        verbose_name="منشا شناسایی ریسک"
    )
    
    risk_source_other = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="سایر منشاها (در صورت انتخاب سایر)"
    )
    
    # ====== مشخصات فعالیت ======
    activity_component = models.CharField(
        max_length=255, 
        verbose_name="اجزا شغل/فعالیت/تجهیز"
    )

    job_tasks = models.ManyToManyField(
        JobTask,
        blank=True,
        related_name='risks',
        verbose_name="اجزای فعالیت انتخابی",
        help_text="از بین اجزای ثبت‌شده برای شغل، موارد مرتبط با این ریسک را انتخاب کنید"
    )
    
    is_routine = models.BooleanField(
        default=True, 
        verbose_name="روتین است؟"
    )
    
    # ====== شناسایی خطر ======
    hazard = models.ForeignKey(
        AnomalyDescription, 
        on_delete=models.PROTECT, 
        verbose_name="خطر (منبع آسیب)",
        help_text="نوع خطری که شناسایی شده است"
    )
    
    people_at_risk = models.ManyToManyField(
        Position, 
        related_name='risks_exposed_to', 
        verbose_name="افراد در معرض خطر",
        help_text="سمت‌هایی که در معرض این خطر هستند"
    )
    
    # ====== پیامد و علل ======
    potential_event = models.CharField(
        max_length=255, 
        verbose_name="رویداد محتمل",
        help_text="چه اتفاقی ممکن است بیفتد"
    )
    
    causes = models.TextField(
        verbose_name="علل احتمالی وقوع",
        help_text="چرا این رویداد ممکن است رخ دهد"
    )
    
    consequence = models.ForeignKey(
        InjuryType, 
        on_delete=models.PROTECT, 
        verbose_name="شرح پیامد احتمالی (نوع آسیب)",
        help_text="نوع آسیب یا صدمه احتمالی"
    )
    
    # ====== کنترل‌های موجود ======
    existing_controls = models.TextField(
        verbose_name="کنترل‌های موجود",
        help_text="اقدامات کنترلی که در حال حاضر اجرا می‌شود"
    )
    
    control_failure_causes = models.TextField(
        verbose_name="علل احتمالی شکست کنترل‌ها",
        help_text="چرا کنترل‌های فعلی ممکن است ناکام بمانند"
    )
    
    # ====== الزامات قانونی ======
    has_legal_requirement = models.BooleanField(
        default=False, 
        verbose_name="الزام قانونی دارد؟"
    )
    
    legal_requirement_desc = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name="شرح الزام قانونی"
    )
    
    is_legal_compliant = models.BooleanField(
        null=True, 
        blank=True, 
        verbose_name="رعایت شده است؟"
    )
    
    # ====== محاسبه ریسک اولیه ======
    probability = models.IntegerField(
        choices=PROBABILITY_CHOICES, 
        verbose_name="احتمال وقوع (P)"
    )
    
    severity = models.IntegerField(
        choices=SEVERITY_CHOICES, 
        verbose_name="شدت پیامد (S)"
    )
    
    risk_number = models.IntegerField(
        editable=False, 
        verbose_name="عدد ریسک (RPN = P × S)"
    )
    
    risk_level = models.CharField(
        max_length=20, 
        choices=RISK_LEVEL_CHOICES,
        editable=False, 
        verbose_name="سطح ریسک"
    )
    
    # ====== کنترل‌های پیشنهادی (Hierarchy of Controls) ======
    control_elimination = models.TextField(
        blank=True, 
        verbose_name="1. حذف خطر (Elimination)",
        help_text="حذف کامل خطر از محیط کار"
    )
    
    control_substitution = models.TextField(
        blank=True, 
        verbose_name="2. جایگزینی (Substitution)",
        help_text="جایگزین کردن با چیز کم‌خطرتر"
    )
    
    control_engineering = models.TextField(
        blank=True, 
        verbose_name="3. کنترل مهندسی (Engineering)",
        help_text="کنترل‌های فنی و مهندسی"
    )
    
    control_admin = models.TextField(
        blank=True, 
        verbose_name="4. کنترل اداری (Administrative)",
        help_text="دستورالعمل‌ها، آموزش، تابلوها"
    )
    
    control_ppe = models.TextField(
        blank=True, 
        verbose_name="5. لوازم حفاظت فردی (PPE)",
        help_text="تجهیزات حفاظت شخصی"
    )
    
    # ====== اقدامات اصلاحی ======
    corrective_action_required = models.BooleanField(
        default=False, 
        verbose_name="نیاز به اقدام اصلاحی دارد؟"
    )
    
    action_number = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="شماره اقدام",
        help_text="شماره اقدام اصلاحی در سیستم"
    )
    
    action_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ اقدام"
    )
    
    action_deadline = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="مهلت اقدام"
    )
    
    responsible_person = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="مسئول اجرا",
        related_name='responsible_risks'
    )
    
    # ====== MUE و شرایط اضطراری ======
    is_mue = models.BooleanField(
        default=False, 
        verbose_name="قابلیت تبدیل به MUE (Unacceptable)",
        help_text="آیا این ریسک می‌تواند به وضعیت غیرقابل پذیرش تبدیل شود؟"
    )
    
    mue_code = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="کد MUE"
    )
    
    is_emergency = models.BooleanField(
        default=False, 
        verbose_name="قابلیت تبدیل به شرایط اضطراری",
        help_text="آیا می‌تواند منجر به شرایط اضطراری شود؟"
    )
    
    emergency_code = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name="کد شرایط اضطراری"
    )
    
    # ====== ارزیابی مجدد (ریسک باقی‌مانده) ======
    re_evaluation_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name="تاریخ محاسبه مجدد"
    )
    
    residual_probability = models.IntegerField(
        choices=PROBABILITY_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name="احتمال مجدد (پس از اقدامات)"
    )
    
    residual_severity = models.IntegerField(
        choices=SEVERITY_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name="شدت مجدد (پس از اقدامات)"
    )
    
    residual_risk_number = models.IntegerField(
        editable=False, 
        null=True, 
        blank=True, 
        verbose_name="عدد ریسک باقی‌مانده"
    )
    
    residual_risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        editable=False,
        null=True,
        blank=True,
        verbose_name="سطح ریسک باقی‌مانده"
    )
    
    # ====== تاریخچه ======
    created_by = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="ایجاد شده توسط",
        related_name='created_risks'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین بروزرسانی"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها"
    )

    def save(self, *args, **kwargs):
        """محاسبه خودکار RPN و ثبت تاریخچه تغییرات"""
        # گرفتن نسخه قبلی برای مقایسه تغییرات
        old_instance = None
        if self.pk:
            try:
                old_instance = RiskAssessment.objects.get(pk=self.pk)
            except RiskAssessment.DoesNotExist:
                old_instance = None

        # محاسبه RPN اولیه
        self.risk_number = self.probability * self.severity

        # تعیین سطح ریسک اولیه بر اساس ماتریس ۵×۵
        if self.risk_number >= 17:
            self.risk_level = 'High'
        elif self.risk_number >= 7:
            self.risk_level = 'Medium'
        else:
            self.risk_level = 'Low'

        # محاسبه ریسک باقی‌مانده اگر داده شد
        if self.residual_probability and self.residual_severity:
            self.residual_risk_number = self.residual_probability * self.residual_severity
            if self.residual_risk_number >= 17:
                self.residual_risk_level = 'High'
            elif self.residual_risk_number >= 7:
                self.residual_risk_level = 'Medium'
            else:
                self.residual_risk_level = 'Low'

        super().save(*args, **kwargs)

        # ایجاد تاریخچه اگر تغییر مهم رخ داده باشد یا رکورد جدید باشد
        significant_fields_changed = False
        change_type = 'initial'
        if old_instance:
            if (
                old_instance.probability != self.probability or
                old_instance.severity != self.severity or
                old_instance.risk_number != self.risk_number or
                old_instance.residual_risk_number != self.residual_risk_number or
                old_instance.residual_probability != self.residual_probability or
                old_instance.residual_severity != self.residual_severity
            ):
                significant_fields_changed = True
                change_type = 'update'
            if (
                old_instance.residual_probability != self.residual_probability or
                old_instance.residual_severity != self.residual_severity
            ) and (self.residual_probability and self.residual_severity):
                change_type = 'reevaluation'
        else:
            significant_fields_changed = True

        if significant_fields_changed:
            RiskAssessmentHistory.objects.create(
                risk=self,
                probability=self.probability,
                severity=self.severity,
                risk_number=self.risk_number,
                risk_level=self.risk_level,
                residual_probability=self.residual_probability,
                residual_severity=self.residual_severity,
                residual_risk_number=self.residual_risk_number,
                residual_risk_level=self.residual_risk_level,
                change_type=change_type,
            )
    
    def get_risk_color(self):
        """دریافت رنگ بر اساس سطح ریسک"""
        colors = {
            'Low': 'success',      # سبز
            'Medium': 'warning',   # زرد
            'High': 'danger',      # قرمز
        }
        return colors.get(self.risk_level, 'secondary')
    
    def get_residual_risk_color(self):
        """دریافت رنگ بر اساس سطح ریسک باقی‌مانده"""
        if not self.residual_risk_level:
            return 'secondary'
        colors = {
            'Low': 'success',
            'Medium': 'warning',
            'High': 'danger',
        }
        return colors.get(self.residual_risk_level, 'secondary')
    
    def get_risk_level_display_fa(self):
        """نمایش فارسی سطح ریسک"""
        levels = {
            'Low': 'پایین',
            'Medium': 'متوسط',
            'High': 'بالا',
        }
        return levels.get(self.risk_level, '-')
    
    def is_action_overdue(self):
        """بررسی اینکه آیا مهلت اقدام گذشته است"""
        if self.action_deadline:
            from django.utils import timezone
            return timezone.now().date() > self.action_deadline
        return False

    class Meta:
        verbose_name = "ارزیابی ریسک"
        verbose_name_plural = "ارزیابی‌های ریسک"
        ordering = ['-created_at', '-risk_number']
        indexes = [
            models.Index(fields=['position', 'risk_level']),
            models.Index(fields=['risk_number']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.position.name} - {self.activity_component} (RPN: {self.risk_number})"


class RiskAssessmentHistory(models.Model):
    """تاریخچه تغییرات ارزیابی ریسک"""
    CHANGE_CHOICES = [
        ('initial', 'ایجاد اولیه'),
        ('update', 'بروزرسانی'),
        ('reevaluation', 'ارزیابی مجدد'),
    ]
    risk = models.ForeignKey(RiskAssessment, on_delete=models.CASCADE, related_name='history', verbose_name="ریسک")
    change_type = models.CharField(max_length=20, choices=CHANGE_CHOICES, verbose_name="نوع تغییر")
    probability = models.IntegerField(verbose_name="احتمال")
    severity = models.IntegerField(verbose_name="شدت")
    risk_number = models.IntegerField(verbose_name="عدد ریسک")
    risk_level = models.CharField(max_length=20, verbose_name="سطح ریسک")
    residual_probability = models.IntegerField(blank=True, null=True, verbose_name="احتمال باقی‌مانده")
    residual_severity = models.IntegerField(blank=True, null=True, verbose_name="شدت باقی‌مانده")
    residual_risk_number = models.IntegerField(blank=True, null=True, verbose_name="عدد ریسک باقی‌مانده")
    residual_risk_level = models.CharField(max_length=20, blank=True, null=True, verbose_name="سطح ریسک باقی‌مانده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ثبت")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "سطر تاریخچه ریسک"
        verbose_name_plural = "تاریخچه ارزیابی‌های ریسک"
        indexes = [
            models.Index(fields=['risk', 'created_at']),
        ]

    def __str__(self):
        return f"History #{self.id} for Risk {self.risk_id} ({self.change_type})"
