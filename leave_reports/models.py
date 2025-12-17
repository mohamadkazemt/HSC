from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.db.models import Q
from accounts.models import UserProfile, Section, Part, UnitGroup, Position
from django.core.exceptions import ValidationError
import threading


class ApprovalHierarchy(models.Model):
    """
    تعریف سلسله مراتب تأیید برای درخواست‌های مرخصی با قابلیت ترکیب چند شرط
    از قوانین با وزن بالاتر (مشخص‌تر) برای تطبیق استفاده می‌شود
    """
    # Thread-local storage برای جلوگیری از recursion در __str__
    _str_lock = threading.local()
    
    # تأیید کننده (الزامی)
    approver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="تأیید کننده")
    
    # فیلدهای معیار (همه اختیاری - برای ترکیب قوانین)
    specific_users = models.ManyToManyField(
        User, 
        blank=True, 
        verbose_name="کاربران خاص",
        help_text="برای تعریف تأیید کننده خاص برای چند کاربر مشخص"
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

    def clean(self):
        """
        اعتبارسنجی: حداقل یکی از فیلدهای معیار باید انتخاب شده باشد
        """
        if not self.has_any_criteria():
            raise ValidationError(
                'باید حداقل یکی از فیلدهای معیار (کاربران خاص، گروه کاری، بخش، قسمت، گروه واحد، یا سمت) را انتخاب کنید.'
            )
        
        # بررسی اینکه اگر part انتخاب شده، باید section آن را هم داشته باشد
        if self.part and self.section:
            if self.part.section != self.section:
                raise ValidationError('قسمت انتخاب شده متعلق به بخش انتخاب شده نیست.')
        
        # بررسی اینکه اگر unit_group انتخاب شده، باید part آن را هم داشته باشد
        if self.unit_group and self.part:
            if self.unit_group.part != self.part:
                raise ValidationError('گروه واحد انتخاب شده متعلق به قسمت انتخاب شده نیست.')
        
        # بررسی اینکه اگر position انتخاب شده، باید unit_group آن را هم داشته باشد
        if self.position and self.unit_group:
            if self.position.unit_group != self.unit_group:
                raise ValidationError('سمت انتخاب شده متعلق به گروه واحد انتخاب شده نیست.')

    def save(self, *args, **kwargs):
        """
        اعتبارسنجی قبل از ذخیره
        """
        self.full_clean()
        super().save(*args, **kwargs)

    def _has_specific_users(self):
        """
        بررسی امن وجود کاربران خاص بدون ایجاد خطای ValueError برای instance های ذخیره‌نشده
        """
        # اگر instance هنوز ذخیره نشده باشد، دسترسی مستقیم به m2m خطا می‌دهد
        if not self.pk:
            cached = getattr(self, '_specific_users_cache', None)
            return bool(cached) if cached is not None else False
        try:
            return self.specific_users.exists()
        except ValueError:
            return False

    class Meta:
        verbose_name = "سلسله مراتب تأیید"
        verbose_name_plural = "سلسله مراتب تأیید"
        # حذف unique_together چون حالا می‌توان چند قانون برای یک بخش/قسمت داشت
        indexes = [
            models.Index(fields=['work_group', 'section', 'part']),
            models.Index(fields=['position', 'unit_group']),
        ]

    def get_weight(self):
        """
        محاسبه وزن قانون برای تعیین میزان مشخص بودن آن
        وزن بالاتر = قانون مشخص‌تر = اولویت بیشتر
        """
        weight = 0
        
        if self._has_specific_users():
            weight += 100  # بالاترین اولویت برای کاربران خاص
        
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

    def has_any_criteria(self):
        """
        بررسی اینکه آیا این قانون حداقل یک معیار دارد
        """
        return any([
            self._has_specific_users(),
            self.work_group,
            self.section,
            self.part,
            self.unit_group,
            self.position,
        ])
    
    def get_criteria_count(self):
        """
        شمارش تعداد معیارهای انتخاب شده در این قانون
        برای تعیین دقیق‌ترین تطبیق
        """
        count = 0
        if self._has_specific_users():
            count += 1
        if self.work_group:
            count += 1
        if self.section:
            count += 1
        if self.part:
            count += 1
        if self.unit_group:
            count += 1
        if self.position:
            count += 1
        return count
    
    def matches_user_profile(self, user_profile):
        """
        بررسی اینکه آیا این قانون با پروفایل کاربر تطبیق دارد
        یک قانون تطبیق دارد اگر:
        - همه فیلدهای تعریف شده در قانون با پروفایل کاربر مطابقت داشته باشند
        - یا فیلد در قانون None باشد (یعنی نادیده گرفته شود)
        
        نکته: اگر قانون هیچ معیاری نداشته باشد (قانون عمومی)، False برمی‌گرداند
        تا از اعمال قوانین عمومی جلوگیری شود
        """
        # اگر قانون هیچ معیاری نداشته باشد، تطبیق ندارد
        if not self.has_any_criteria():
            return False
        
        # بررسی specific_users
        if self._has_specific_users():
            # استفاده از all() که از prefetch cache استفاده می‌کند اگر موجود باشد
            # و در غیر این صورت query جدید اجرا می‌کند
            specific_user_ids = set(self.specific_users.values_list('id', flat=True))
            if user_profile.user.id not in specific_user_ids:
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
        # جلوگیری از recursion با استفاده از thread-local storage
        if not hasattr(ApprovalHierarchy._str_lock, 'active_ids'):
            ApprovalHierarchy._str_lock.active_ids = set()
        
        # اگر این instance در حال stringify شدن است، از نمایش ساده استفاده کن
        if self.pk and self.pk in ApprovalHierarchy._str_lock.active_ids:
            return f"{self.__class__.__name__}(id={self.pk})"
        
        # اضافه کردن id به set برای جلوگیری از recursion
        if self.pk:
            ApprovalHierarchy._str_lock.active_ids.add(self.pk)
        
        try:
            parts = []
            
            # فقط اگر instance ذخیره شده باشد، به related fields دسترسی پیدا کن
            if self.pk:
                try:
                    # استفاده از count() به جای exists() برای جلوگیری از recursion
                    count = self.specific_users.count()
                    if count > 0:
                        user_names = [user.get_full_name() or user.username for user in self.specific_users.all()[:3]]
                        if count == 1:
                            parts.append(f"کاربر: {user_names[0]}")
                        else:
                            parts.append(f"کاربران: {', '.join(user_names)}{' و ...' if count > 3 else ''}")
                except (AttributeError, ValueError, TypeError, RecursionError):
                    # در صورت بروز خطا (مثلاً instance هنوز ذخیره نشده یا recursion)، از این بخش صرف نظر کن
                    pass
            
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
            # استفاده از getattr برای جلوگیری از recursion در approver
            approver_name = getattr(self.approver, 'user', None)
            if approver_name:
                approver_str = approver_name.get_full_name() or approver_name.username
            else:
                approver_str = "بدون تأیید کننده"
            
            return f"{approver_str} ({criteria})"
        finally:
            # حذف id از set بعد از اتمام
            if self.pk and hasattr(ApprovalHierarchy._str_lock, 'active_ids'):
                ApprovalHierarchy._str_lock.active_ids.discard(self.pk)


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
        
        منطق انتخاب:
        1. ابتدا همه قوانین تطبیق‌دار را پیدا می‌کند
        2. از بین آنها، قانونی که بیشترین تعداد معیار را دارد (دقیق‌ترین تطبیق) را انتخاب می‌کند
        3. اگر چند قانون با همان تعداد معیار وجود داشت، آن‌ها را بر اساس وزن مرتب می‌کند
        4. قانون با بیشترین معیار و در صورت تساوی، با بالاترین وزن انتخاب می‌شود
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
            'approver', 'approver__user', 'section', 'part', 'unit_group', 'position'
        ).prefetch_related('specific_users').all():
            if rule.matches_user_profile(requester_profile):
                criteria_count = rule.get_criteria_count()
                weight = rule.get_weight()
                matching_rules.append((criteria_count, weight, rule))
                logger.info(f"   ✅ Rule matched: {rule} (criteria_count: {criteria_count}, weight: {weight})")
        
        if not matching_rules:
            logger.warning(f"⚠️ No matching approval rule found for user {self.user.username}")
            return None
        
        # مرتب‌سازی: اول بر اساس تعداد معیارها (نزولی)، سپس بر اساس وزن (نزولی)
        # قانون با بیشترین معیار و در صورت تساوی، با بالاترین وزن اولویت دارد
        matching_rules.sort(key=lambda x: (x[0], x[1]), reverse=True)
        
        # برگرداندن تأیید کننده از قانون با بیشترین معیار و بالاترین وزن
        best_rule = matching_rules[0][2]
        approver = best_rule.approver
        
        logger.info(f"✅ Best matching rule: {best_rule} (criteria_count: {matching_rules[0][0]}, weight: {matching_rules[0][1]})")
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
