from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from accounts.models import UserProfile, Section, Part
from django.core.exceptions import ValidationError


class ApprovalHierarchy(models.Model):
    """
    تعریف سلسله مراتب تأیید برای درخواست‌های مرخصی
    """
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, verbose_name="بخش")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, null=True, blank=True, verbose_name="قسمت")
    approver = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name="تأیید کننده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "سلسله مراتب تأیید"
        verbose_name_plural = "سلسله مراتب تأیید"
        unique_together = ['section', 'part']  # یک تأیید کننده برای هر بخش/قسمت

    def __str__(self):
        if self.part:
            return f"تأیید کننده {self.part.name}: {self.approver}"
        elif self.section:
            return f"تأیید کننده {self.section.name}: {self.approver}"
        return f"تأیید کننده: {self.approver}"


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
            
            requester_profile = getattr(self.user, 'userprofile', None)
            logger.info(f"  Requester profile: {requester_profile}")
            if not requester_profile:
                logger.warning(f"❌ Requester has no profile")
                return False
            
            logger.info(f"  Requester part: {requester_profile.part}, section: {requester_profile.section}")
            
            # بررسی سلسله مراتب تأیید
            # اول بررسی می‌کنیم آیا برای Part خاص تأیید کننده‌ای تعریف شده یا نه
            hierarchy = None
            if requester_profile.part:
                # اول سلسله مراتب خاص Part را بررسی می‌کنیم
                hierarchy = ApprovalHierarchy.objects.filter(part=requester_profile.part).first()
                logger.info(f"  Looking for hierarchy by part: {requester_profile.part} -> Found: {hierarchy}")
                
                # اگر برای Part خاص تأیید کننده‌ای نبود، سلسله مراتب کلی Section را بررسی می‌کنیم
                if not hierarchy and requester_profile.section:
                    hierarchy = ApprovalHierarchy.objects.filter(
                        section=requester_profile.section, 
                        part__isnull=True
                    ).first()
                    logger.info(f"  No part hierarchy, looking for section hierarchy: {requester_profile.section} -> Found: {hierarchy}")
            elif requester_profile.section:
                # فقط سلسله مراتب کلی Section را بررسی می‌کنیم
                hierarchy = ApprovalHierarchy.objects.filter(
                    section=requester_profile.section, 
                    part__isnull=True
                ).first()
                logger.info(f"  Looking for hierarchy by section: {requester_profile.section} -> Found: {hierarchy}")
            else:
                logger.warning(f"❌ Requester has no part or section")
                return False
            
            logger.info(f"  Hierarchy found: {hierarchy}")
            if hierarchy:
                logger.info(f"  Hierarchy approver: {hierarchy.approver}, Current user: {user_profile}")
            
            if hierarchy and hierarchy.approver == user_profile:
                logger.info(f"✅ User is authorized approver")
                return True
            else:
                logger.warning(f"❌ User is not the approver for this hierarchy")
        
        logger.warning(f"❌ No matching approval condition")
        return False

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_leave_type_display()} - {self.shift_date}"
