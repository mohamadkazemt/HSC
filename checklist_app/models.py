from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime
from BaseInfo.models import MiningMachine, TypeMachine
from contractor_management.models import Vehicle
from anomalis.models import LocationSection, AnomalyDescription, Priority, Anomalytype
from accounts.models import UserProfile

class Checklist(models.Model):
    CHECKLIST_TYPE_CHOICES = [
        ('machine', 'ماشین'),
        ('location', 'مکان'),
        ('contractor_vehicle', 'ماشین‌آلات پیمانکار'),
    ]
    CHECKLIST_SHIFT_CHOICES = [
        ('day', 'روزکاراول'),
        ('day2', 'روزکاردوم'),
        ('evening', 'عصرکاراول'),
        ('evening2', 'عصرکاردوم'),
        ('night', 'شبکاراول'),
        ('night2', 'شبکاردوم')
    ]
    MACHINE_STATUS_CHOICES = [
        ('healthy', 'سالم'),
        ('broken', 'خراب/در حال تعمیر'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ثبت کننده", related_name='general_checklists')
    checklist_type = models.CharField(max_length=20, choices=CHECKLIST_TYPE_CHOICES, verbose_name="نوع چک لیست")
    machine = models.ForeignKey(MiningMachine, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ماشین", related_name='general_checklists')
    location_section = models.ForeignKey(LocationSection, on_delete=models.CASCADE, null=True, blank=True, verbose_name="بخش مکانی")
    contractor_vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ماشین‌آلات پیمانکار", related_name='general_checklists')
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    shift = models.CharField(max_length=50, choices=CHECKLIST_SHIFT_CHOICES, verbose_name="شیفت کاری")
    shift_group = models.CharField(max_length=50, verbose_name="گروه شیفت")
    machine_status = models.CharField(
        max_length=20,
        choices=MACHINE_STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name="وضعیت ماشین",
        help_text="فقط برای چک‌لیست‌های ماشین: وضعیت ماشین قبل از شروع چک‌لیست"
    )
    scheduled_instance = models.ForeignKey(
        'ScheduledChecklistInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_checklists',
        verbose_name="نمونه برنامه‌ریزی شده",
        help_text="اگر این چک‌لیست از یک برنامه زمان‌بندی شده ایجاد شده باشد"
    )

    class Meta:
        verbose_name = "چک لیست"
        verbose_name_plural = "چک لیست ها"

    def __str__(self):
        if self.checklist_type == 'machine':
            return f"چک لیست ماشین {self.machine} - {self.date}"
        elif self.checklist_type == 'location':
            return f"چک لیست مکان {self.location_section} - {self.date}"
        else:
            return f"چک لیست ماشین‌آلات پیمانکار {self.contractor_vehicle} - {self.date}"

    def clean(self):
        if self.checklist_type == 'machine' and not self.machine:
            raise ValidationError('برای چک لیست ماشین، باید ماشین انتخاب شود.')
        elif self.checklist_type == 'location' and not self.location_section:
            raise ValidationError('برای چک لیست مکان، باید بخش مکانی انتخاب شود.')
        elif self.checklist_type == 'contractor_vehicle' and not self.contractor_vehicle:
            raise ValidationError('برای چک لیست ماشین‌آلات پیمانکار، باید ماشین پیمانکار انتخاب شود.')
        if (self.machine and self.location_section) or (self.machine and self.contractor_vehicle) or (self.location_section and self.contractor_vehicle):
            raise ValidationError('نمی‌توان همزمان بیش از یک نوع ماشین یا مکان را انتخاب کرد.')
        # اعتبارسنجی وضعیت ماشین
        if self.checklist_type == 'machine' and not self.machine_status:
            raise ValidationError('برای چک لیست ماشین، باید وضعیت ماشین (سالم/خراب) مشخص شود.')
        if self.machine_status and self.checklist_type != 'machine':
            raise ValidationError('وضعیت ماشین فقط برای چک لیست‌های ماشین قابل استفاده است.')

class Question(models.Model):
    QUESTION_SCOPE_CHOICES = [
        ('machine', 'ماشین'),
        ('location', 'مکان'),
        ('contractor_vehicle', 'ماشین‌آلات پیمانکار'),
    ]
    QUESTION_TYPE_CHOICES = [
        ('text', 'متنی'),
        ('option', 'گزینه‌ای'),
    ]
    HSE_TYPE_CHOICES = [
        ('H', 'Health'),
        ('S', 'Safety'),
        ('E', 'Environment'),
    ]

    question_scopes = models.JSONField(
        default=list,
        verbose_name="محدوده‌های سوال",
        help_text="لیست محدوده‌هایی که این سوال در آن‌ها نمایش می‌شود"
    )
    machine_types = models.ManyToManyField(
        TypeMachine,
        blank=True,
        verbose_name="انواع ماشین",
        related_name='questions'
    )
    location_sections = models.ManyToManyField(
        LocationSection,
        blank=True,
        verbose_name="بخش‌های مکانی"
    )
    vehicle_categories = models.JSONField(
        default=list,
        blank=True,
        verbose_name="دسته‌بندی‌های خودرو"
    )
    text = models.TextField(verbose_name="متن سوال")
    is_required = models.BooleanField(default=True, verbose_name="اجباری")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE_CHOICES, verbose_name="نوع سوال")
    options = models.TextField(null=True, blank=True, verbose_name="گزینه‌ها")
    
    # فیلدهای مربوط به آنومالی
    anomaly_type = models.ForeignKey(
        'anomalis.Anomalytype',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="نوع آنومالی پیش‌فرض"
    )
    hse_type = models.CharField(
        max_length=1,
        choices=HSE_TYPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="نوع HSE پیش‌فرض"
    )
    default_priority_on_fail = models.ForeignKey(
        'anomalis.Priority',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="اولویت آنومالی پیش‌فرض"
    )
    default_corrective_action = models.TextField(
        null=True,
        blank=True,
        verbose_name="اقدام اصلاحی پیش‌فرض"
    )
    default_anomaly_description = models.ForeignKey(
        'anomalis.AnomalyDescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="شرح آنومالی پیش‌فرض",
        help_text="شرح پیش‌فرض آنومالی که در صورت پاسخ غیرقابل قبول ایجاد می‌شود"
    )
    unacceptable_options = models.TextField(
        null=True,
        blank=True,
        verbose_name="گزینه‌های غیرقابل قبول",
        help_text="گزینه‌هایی که در صورت انتخاب منجر به ایجاد آنومالی می‌شوند (با کاما جدا شوند)"
    )

    class Meta:
        verbose_name = "سوال چک لیست"
        verbose_name_plural = "سوالات چک لیست"

    def __str__(self):
        return self.text[:50]

    def clean(self):
        if not self.question_scopes:
            raise ValidationError('حداقل یک محدوده سوال باید انتخاب شود.')
        
        if 'machine' in self.question_scopes and not self.machine_types.exists():
            raise ValidationError('برای سوالات ماشین، باید حداقل یک نوع ماشین انتخاب شود.')
        
        if 'location' in self.question_scopes and not self.location_sections.exists():
            raise ValidationError('برای سوالات مکان، باید حداقل یک بخش مکانی انتخاب شود.')
        
        if 'contractor_vehicle' in self.question_scopes and not self.vehicle_categories:
            raise ValidationError('برای سوالات ماشین‌آلات پیمانکار، باید حداقل یک دسته‌بندی خودرو انتخاب شود.')
        
        if self.question_type == 'option' and not self.options:
            raise ValidationError('برای سوالات گزینه‌ای، باید گزینه‌ها تعریف شوند.')
        
        if self.unacceptable_options and self.question_type != 'option':
            raise ValidationError('گزینه‌های غیرقابل قبول فقط برای سوالات گزینه‌ای قابل تعریف است.')

class Answer(models.Model):
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, verbose_name="چک لیست")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="سوال")
    answer_text = models.TextField(null=True, blank=True, verbose_name="پاسخ متنی")
    selected_option = models.CharField(max_length=100, null=True, blank=True, verbose_name="گزینه انتخاب شده")
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات")

    class Meta:
        verbose_name = "پاسخ"
        verbose_name_plural = "پاسخ‌ها"

    def __str__(self):
        return f"پاسخ به {self.question.text[:30]}"

    @property
    def is_unacceptable(self):
        """بررسی می‌کند که آیا پاسخ غیرقابل قبول است یا خیر"""
        if self.question.question_type == 'option' and self.question.unacceptable_options:
            unacceptable_list = [opt.strip() for opt in self.question.unacceptable_options.split(',')]
            return self.selected_option in unacceptable_list
        return False

    def clean(self):
        if self.question.question_type == 'option' and not self.selected_option:
            raise ValidationError('برای سوالات گزینه‌ای، باید یک گزینه انتخاب شود.')
        elif self.question.question_type == 'text' and not self.answer_text:
            raise ValidationError('برای سوالات متنی، باید پاسخ وارد شود.')


class ChecklistSchedule(models.Model):
    """
    مدل برای تعریف برنامه زمان‌بندی چک‌لیست‌ها
    """
    SCHEDULE_TYPE_CHOICES = [
        ('monthly_days', 'روزهای مشخص ماه (مثلاً 1 و 15 هر ماه)'),
        ('specific_dates', 'تاریخ‌های مشخص'),
        ('weekly', 'هفتگی'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="نام برنامه")
    checklist_type = models.CharField(
        max_length=20,
        choices=Checklist.CHECKLIST_TYPE_CHOICES,
        verbose_name="نوع چک لیست"
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=SCHEDULE_TYPE_CHOICES,
        verbose_name="نوع برنامه‌ریزی"
    )
    
    # برای monthly_days: روزهای ماه (مثلاً [1, 15])
    monthly_days = models.JSONField(
        default=list,
        blank=True,
        verbose_name="روزهای ماه",
        help_text="لیست روزهای ماه که چک‌لیست باید انجام شود (مثلاً [1, 15])"
    )
    
    # برای specific_dates: تاریخ‌های مشخص
    specific_dates = models.JSONField(
        default=list,
        blank=True,
        verbose_name="تاریخ‌های مشخص",
        help_text="لیست تاریخ‌های مشخص (فرمت: YYYY-MM-DD)"
    )
    
    # هدف: ماشین، مکان، یا نوع چک‌لیست (چندین مقدار)
    target_machines = models.JSONField(
        default=list,
        blank=True,
        verbose_name="ماشین‌های هدف",
        help_text="لیست ID ماشین‌های هدف (مثلاً [1, 2, 3])"
    )
    target_location_sections = models.JSONField(
        default=list,
        blank=True,
        verbose_name="بخش‌های مکانی هدف",
        help_text="لیست ID بخش‌های مکانی هدف (مثلاً [1, 2, 3])"
    )
    target_contractor_vehicles = models.JSONField(
        default=list,
        blank=True,
        verbose_name="ماشین‌های پیمانکار هدف",
        help_text="لیست ID ماشین‌های پیمانکار هدف (مثلاً [1, 2, 3])"
    )
    
    # نگه‌داری فیلدهای قدیمی برای سازگاری با migration
    target_machine = models.ForeignKey(
        MiningMachine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ماشین هدف (قدیمی)",
        related_name='scheduled_checklists_old'
    )
    target_location_section = models.ForeignKey(
        LocationSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="بخش مکانی هدف (قدیمی)",
        related_name='scheduled_checklists_old'
    )
    target_contractor_vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ماشین پیمانکار هدف (قدیمی)",
        related_name='scheduled_checklists_old'
    )
    
    # فعال/غیرفعال
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")
    
    class Meta:
        verbose_name = "برنامه زمان‌بندی چک لیست"
        verbose_name_plural = "برنامه‌های زمان‌بندی چک لیست"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_checklist_type_display()}"
    
    def clean(self):
        # بررسی هدف بر اساس نوع چک‌لیست
        if self.checklist_type == 'machine':
            # استفاده از target_machines (جدید) یا target_machine (قدیمی)
            if not self.target_machines and not self.target_machine:
                raise ValidationError('برای چک لیست ماشین، باید حداقل یک ماشین هدف انتخاب شود.')
        elif self.checklist_type == 'location':
            # استفاده از target_location_sections (جدید) یا target_location_section (قدیمی)
            if not self.target_location_sections and not self.target_location_section:
                raise ValidationError('برای چک لیست مکان، باید حداقل یک بخش مکانی هدف انتخاب شود.')
        elif self.checklist_type == 'contractor_vehicle':
            # استفاده از target_contractor_vehicles (جدید) یا target_contractor_vehicle (قدیمی)
            if not self.target_contractor_vehicles and not self.target_contractor_vehicle:
                raise ValidationError('برای چک لیست ماشین‌آلات پیمانکار، باید حداقل یک ماشین پیمانکار هدف انتخاب شود.')
        
        if self.schedule_type == 'monthly_days' and not self.monthly_days:
            raise ValidationError('برای برنامه‌ریزی ماهانه، باید حداقل یک روز ماه مشخص شود.')
        elif self.schedule_type == 'specific_dates' and not self.specific_dates:
            raise ValidationError('برای برنامه‌ریزی با تاریخ‌های مشخص، باید حداقل یک تاریخ وارد شود.')


class ScheduledChecklistInstance(models.Model):
    """
    مدل برای ردیابی نمونه‌های چک‌لیست برنامه‌ریزی شده (Pending/Completed)
    """
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('skipped', 'رد شده'),
    ]
    
    schedule = models.ForeignKey(
        ChecklistSchedule,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name="برنامه زمان‌بندی"
    )
    due_date = models.DateField(verbose_name="تاریخ موعد")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت"
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_scheduled_checklists',
        verbose_name="تکمیل شده توسط"
    )
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تکمیل")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "نمونه چک لیست برنامه‌ریزی شده"
        verbose_name_plural = "نمونه‌های چک لیست برنامه‌ریزی شده"
        unique_together = ('schedule', 'due_date')
        ordering = ['-due_date', 'status']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['schedule', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.schedule.name} - {self.due_date} ({self.get_status_display()})"
    
    def mark_completed(self, user):
        """علامت‌گذاری به عنوان تکمیل شده توسط کاربر"""
        from django.db import transaction
        with transaction.atomic():
            # استفاده از select_for_update برای جلوگیری از race condition
            instance = ScheduledChecklistInstance.objects.select_for_update().get(pk=self.pk)
            if instance.status == 'pending':
                instance.status = 'completed'
                instance.completed_by = user
                instance.completed_at = timezone.now()
                instance.save()
                return True
            return False
