from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from BaseInfo.models import MiningMachine, TypeMachine
from anomalis.models import LocationSection, AnomalyDescription, Priority, Anomalytype
from accounts.models import UserProfile

class Checklist(models.Model):
    CHECKLIST_TYPE_CHOICES = [
        ('machine', 'ماشین'),
        ('location', 'مکان'),
    ]
    CHECKLIST_SHIFT_CHOICES = [
        ('day', 'روزکاراول'),
        ('day2', 'روزکاردوم'),
        ('evening', 'عصرکاراول'),
        ('evening2', 'عصرکاردوم'),
        ('night', 'شبکاراول'),
        ('night2', 'شبکاردوم')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ثبت کننده", related_name='general_checklists')
    checklist_type = models.CharField(max_length=10, choices=CHECKLIST_TYPE_CHOICES, verbose_name="نوع چک لیست")
    machine = models.ForeignKey(MiningMachine, on_delete=models.CASCADE, null=True, blank=True, verbose_name="ماشین", related_name='general_checklists')
    location_section = models.ForeignKey(LocationSection, on_delete=models.CASCADE, null=True, blank=True, verbose_name="بخش مکانی")
    date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    shift = models.CharField(max_length=50, choices=CHECKLIST_SHIFT_CHOICES, verbose_name="شیفت کاری")
    shift_group = models.CharField(max_length=50, verbose_name="گروه شیفت")

    class Meta:
        verbose_name = "چک لیست"
        verbose_name_plural = "چک لیست ها"

    def __str__(self):
        if self.checklist_type == 'machine':
            return f"چک لیست ماشین {self.machine} - {self.date}"
        else:
            return f"چک لیست مکان {self.location_section} - {self.date}"

    def clean(self):
        if self.checklist_type == 'machine' and not self.machine:
            raise ValidationError('برای چک لیست ماشین، باید ماشین انتخاب شود.')
        elif self.checklist_type == 'location' and not self.location_section:
            raise ValidationError('برای چک لیست مکان، باید بخش مکانی انتخاب شود.')
        if self.machine and self.location_section:
            raise ValidationError('نمی‌توان همزمان هم ماشین و هم بخش مکانی را انتخاب کرد.')

class Question(models.Model):
    QUESTION_SCOPE_CHOICES = [
        ('machine', 'ماشین'),
        ('location', 'مکان'),
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

    question_scope = models.CharField(max_length=10, choices=QUESTION_SCOPE_CHOICES, verbose_name="محدوده سوال")
    machine_type = models.ForeignKey(TypeMachine, on_delete=models.CASCADE, null=True, blank=True, verbose_name="نوع ماشین", related_name='questions')
    location_section = models.ForeignKey(LocationSection, on_delete=models.CASCADE, null=True, blank=True, verbose_name="بخش مکانی")
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
        if self.question_scope == 'machine' and not self.machine_type:
            raise ValidationError('برای سوالات ماشین، باید نوع ماشین انتخاب شود.')
        elif self.question_scope == 'location' and not self.location_section:
            raise ValidationError('برای سوالات مکان، باید بخش مکانی انتخاب شود.')
        if self.machine_type and self.location_section:
            raise ValidationError('نمی‌توان همزمان هم نوع ماشین و هم بخش مکانی را انتخاب کرد.')
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
