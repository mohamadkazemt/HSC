from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Q
from accounts.models import UserProfile, Section, Part, UnitGroup, Position
from django.core.exceptions import ValidationError


class ApprovalHierarchy(models.Model):
    """
    تعریف سلسله مراتب تأیید برای درخواست‌های مرخصی با قابلیت ترکیب چند شرط
    از قوانین با وزن بالاتر (مشخص‌تر) برای تطبیق استفاده می‌شود
    """
    # تأیید کننده (الزامی)
    approver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="تأیید کننده")
    
    # فیلدهای معیار (همه اختیاری - برای ترکیب قوانین)
    specific_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="کاربر خاص",
        help_text="برای تعریف تأیید کننده خاص برای یک کاربر مشخص"
    )
    work_group = models.CharField(
        max_length=2, 
        choices=UserProfile.GROUP_CHOICES, 
        null=True, 
        blank=True, 
        verbose_name="گروه کاری"
    )
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="بخش"
    )
    part = models.ForeignKey(
        Part, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="قسمت"
    )
    unit_group = models.ForeignKey(
        UnitGroup, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="گروه"
    )
    position = models.ForeignKey(
        Position, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="سمت"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "سلسله مراتب تأیید"
        verbose_name_plural = "سلسله مراتب تأیید"
        # حذف unique_together چون حالا می‌توان چند قانون برای یک بخش/قسمت داشت
        indexes = [
            models.Index(fields=['work_group', 'section', 'part']),
            models.Index(fields=['specific_user']),
            models.Index(fields=['position', 'unit_group']),
        ]

    def get_weight(self):
        """
        محاسبه وزن قانون برای تعیین میزان مشخص بودن آن
        وزن بالاتر = قانون مشخص‌تر = اولویت بیشتر
        """
        weight = 0
        
        if self.specific_user:
            weight += 100  # بالاترین اولویت برای کاربر خاص
        
        if self.position:
            weight += 50
        
        if self.work_group:
            weight += 40
        
        if self.unit_group:
            weight += 30
        
        if self.part:
            weight += 20
        
        if self.section:
            weight += 10
        
        return weight

    def matches_user_profile(self, user_profile):
        """
        بررسی اینکه آیا این قانون با پروفایل کاربر تطبیق دارد
        یک قانون تطبیق دارد اگر:
        - همه فیلدهای تعریف شده در قانون با پروفایل کاربر مطابقت داشته باشند
        - یا فیلد در قانون None باشد (یعنی نادیده گرفته شود)
        """
        # بررسی specific_user
        if self.specific_user:
            if user_profile.user != self.specific_user:
                return False
        
        # بررسی work_group
        if self.work_group:
            if user_profile.group != self.work_group:
                return False
        
        # بررسی section
        if self.section:
            if user_profile.section != self.section:
                return False
        
        # بررسی part
        if self.part:
            if user_profile.part != self.part:
                return False
        
        # بررسی unit_group
        if self.unit_group:
            if user_profile.unit_group != self.unit_group:
                return False
        
        # بررسی position
        if self.position:
            if user_profile.position != self.position:
                return False
        
        return True

    def __str__(self):
        parts = []
        if self.specific_user:
            parts.append(f"کاربر: {self.specific_user.get_full_name()}")
        if self.work_group:
            parts.append(f"گروه: {self.get_work_group_display()}")
        if self.position:
            parts.append(f"سمت: {self.position.name}")
        if self.unit_group:
            parts.append(f"گروه واحد: {self.unit_group.name}")
        if self.part:
            parts.append(f"قسمت: {self.part.name}")
        if self.section:
            parts.append(f"بخش: {self.section.name}")
        
        criteria = " + ".join(parts) if parts else "عمومی"
        return f"{self.approver} ({criteria})"


class ShiftReport(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('regular', 'مرخصی استحقاقی'),
        ('absence', 'غیبت'),
        ('hourly', 'مرخصی ساعتی'),
        ('sick_leave', 'مرخصی استعلاجی')
    ]
    SHIFT_TYPE_CHOICES = [
        ('day', 'روزکار اول'),
        ('day2', 'روزکار دوم'),
        ('evening', 'عصرکار اول'),
        ('evening2', 'عصرکار دوم'),
        ('night', 'شبکار اول'),
        ('night2', 'شبکار دوم')
    ]
    STATUS_CHOICES = [
        ('pending_replacement', 'در انتظار تأیید جایگزین'),
        ('pending_approval', 'در انتظار تأیید مدیر'),
        ('approved', 'تأیید شده'),
        ('rejected', 'رد شده'),
    ]
    registration_CHOICES = [
        (True, 'ثبت شده'),
        (False, 'ثبت نشده')
    ]
    
    # اطلاعات اصلی درخواست
    leave_type = models.CharField(max_length=15, choices=LEAVE_TYPE_CHOICES, verbose_name="نوع مرخصی")
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True, related_name='leave_requests', verbose_name="درخواست دهنده")
    shift_date = models.DateField(db_index=True, verbose_name="تاریخ مرخصی")
    leave_hours = models.IntegerField(null=True, blank=True, verbose_name="ساعات مرخصی")
    start_time = models.TimeField(null=True, blank=True, verbose_name="ساعت شروع")
    end_time = models.TimeField(null=True, blank=True, verbose_name="ساعت پایان")
    work_group = models.CharField(max_length=100, db_index=True, verbose_name="گروه کاری")
    shift_type = models.CharField(max_length=10, choices=SHIFT_TYPE_CHOICES, verbose_name="نوع شیفت")
    description = models.TextField(null=True, blank=True, verbose_name="توضیحات")
    
    # فایل مدارک پزشکی (برای مرخصی استعلاجی)
    medical_document = models.FileField(upload_to='leave_medical_docs/', null=True, blank=True, 
                                       verbose_name="مدارک پزشکی")
    
    # فیلدهای جدید برای فرآیند تأیید
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending_replacement', verbose_name="وضعیت")
    replacement_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                           related_name='replacement_requests', verbose_name="جایگزین پیشنهادی")
    replacement_approved = models.BooleanField(default=False, verbose_name="تأیید جایگزین")
    replacement_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تأیید جایگزین")
    
    final_approver = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='approved_leaves', verbose_name="تأیید کننده نهایی")
    final_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ تأیید نهایی")
    
    rejection_reason = models.TextField(null=True, blank=True, verbose_name="دلیل رد")
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='rejected_leaves', verbose_name="رد کننده")
    rejected_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ رد")
    
    # فیلدهای قدیمی (حفظ برای سازگاری)
    registration = models.BooleanField(choices=registration_CHOICES, default=False, verbose_name='وضعیت ثبت')
    crate_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='created_leaves', verbose_name="ایجاد کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    # فیلدهای قدیمی (حفظ برای سازگاری)
    registration = models.BooleanField(choices=registration_CHOICES, default=False, verbose_name='وضعیت ثبت')
    crate_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='created_leaves', verbose_name="ایجاد کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    exported_to_excel = models.BooleanField(default=False, verbose_name='خروجی اکسل گرفته شده')

    class Meta:
        verbose_name = "درخواست مرخصی"
        verbose_name_plural = "درخواست‌های مرخصی"
        ordering = ['-created_at']

    def clean(self):
        # بررسی تکراری بودن گزارش برای یک کاربر در یک تاریخ خاص
        # فقط اگر user وجود داشته باشد این چک انجام شود
        if self.user_id:
            existing_report = ShiftReport.objects.filter(
                user=self.user,
                shift_date=self.shift_date
            ).exclude(pk=self.pk).first()

            if existing_report:
                raise ValidationError(
                    f'برای کاربر {self.user.get_full_name()} در تاریخ {self.shift_date} قبلاً گزارش ثبت شده است.')
        
        # اعتبارسنجی برای مرخصی ساعتی
        if self.leave_type == 'hourly' and (not self.start_time or not self.end_time):
            raise ValidationError('برای مرخصی ساعتی باید ساعت شروع و پایان وارد شود.')
        
        # نکته: اعتبارسنجی medical_document و replacement_person در فرم انجام می‌شود
        # چون در زمان clean() مدل، فایل ممکن است هنوز آپلود نشده باشد


    def save(self, *args, **kwargs):
        self.full_clean()  # اعتبارسنجی قبل از ذخیره
        super(ShiftReport, self).save(*args, **kwargs)

    def get_status_display_color(self):
        """بازگشت رنگ مناسب برای هر وضعیت"""
        colors = {
            'pending_replacement': 'warning',  # زرد
            'pending_approval': 'info',  # آبی
            'approved': 'success',  # سبز
            'rejected': 'danger',  # قرمز
        }
        return colors.get(self.status, 'secondary')

    def get_status_icon(self):
        """بازگشت آیکون مناسب برای هر وضعیت"""
        icons = {
            'pending_replacement': 'fa-clock',
            'pending_approval': 'fa-hourglass-half',
            'approved': 'fa-check-circle',
            'rejected': 'fa-times-circle',
        }
        return icons.get(self.status, 'fa-question-circle')

    def get_required_approver(self):
        """
        پیدا کردن تأیید کننده مورد نیاز بر اساس بهترین تطبیق با قوانین ApprovalHierarchy
        از قوانین با وزن بالاتر (مشخص‌تر) استفاده می‌کند
        """
        import logging
        logger = logging.getLogger(__name__)
        
        requester_profile = getattr(self.user, 'userprofile', None)
        if not requester_profile:
            logger.warning(f"❌ Requester {self.user.username} has no profile")
            return None
        
        logger.info(f"🔍 Finding approver for user: {self.user.username}")
        logger.info(f"   Profile: group={requester_profile.group}, section={requester_profile.section}, "
                   f"part={requester_profile.part}, unit_group={requester_profile.unit_group}, "
                   f"position={requester_profile.position}")
        
        # پیدا کردن همه قوانینی که با پروفایل کاربر تطبیق دارند
        matching_rules = []
        
        for rule in ApprovalHierarchy.objects.select_related(
            'approver', 'approver__user', 'section', 'part', 'unit_group', 'position', 'specific_user'
        ).all():
            if rule.matches_user_profile(requester_profile):
                weight = rule.get_weight()
                matching_rules.append((weight, rule))
                logger.info(f"   ✅ Rule matched: {rule} (weight: {weight})")
        
        if not matching_rules:
            logger.warning(f"⚠️ No matching approval rule found for user {self.user.username}")
            return None
        
        # مرتب‌سازی بر اساس وزن (نزولی) - قانون با وزن بالاتر اولویت دارد
        matching_rules.sort(key=lambda x: x[0], reverse=True)
        
        # برگرداندن تأیید کننده از قانون با بالاترین وزن
        best_rule = matching_rules[0][1]
        approver = best_rule.approver
        
        logger.info(f"✅ Best matching rule: {best_rule} (weight: {matching_rules[0][0]})")
        logger.info(f"   Approver: {approver}")
        
        return approver

    def can_be_approved_by(self, user):
        """بررسی اینکه آیا کاربر می‌تواند این درخواست را تأیید کند"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔍 can_be_approved_by called - user: {user}, request status: {self.status}")
        
        # جایگزین می‌تواند درخواست را تأیید کند
        if self.status == 'pending_replacement' and self.replacement_person == user:
            logger.info(f"✅ User is replacement person")
            return True
        
        # مدیر می‌تواند درخواست را تأیید کند
        if self.status == 'pending_approval':
            logger.info(f"  Status is pending_approval, checking manager access...")
            
            user_profile = getattr(user, 'userprofile', None)
            logger.info(f"  Current user profile: {user_profile}")
            if not user_profile:
                logger.warning(f"❌ User has no profile")
                return False
            
            # استفاده از متد جدید برای پیدا کردن تأیید کننده مورد نیاز
            required_approver = self.get_required_approver()
            
            if not required_approver:
                logger.warning(f"❌ No approver found for this request")
                return False
            
            if required_approver == user_profile:
                logger.info(f"✅ User is authorized approver")
                return True
            else:
                logger.warning(f"❌ User is not the approver. Required: {required_approver}, Current: {user_profile}")
        
        logger.warning(f"❌ No matching approval condition")
        return False

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_leave_type_display()} - {self.shift_date}"
