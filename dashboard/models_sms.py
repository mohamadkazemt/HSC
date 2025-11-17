"""مدل لاگ پیامک برای ردیابی تمام پیامک‌های ارسال‌شده."""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class SMSLog(models.Model):
    """لاگ تمام پیامک‌های ارسال‌شده با جزئیات کامل."""
    
    STATUS_CHOICES = [
        ('pending', 'در صف ارسال'),
        ('sent', 'ارسال شده'),
        ('delivered', 'تحویل داده شده'),
        ('failed', 'ناموفق'),
        ('rate_limited', 'محدود شده (Rate Limit)'),
    ]
    
    # اطلاعات پایه
    mobile_number = models.CharField(max_length=20, db_index=True, verbose_name='شماره موبایل')
    template_id = models.IntegerField(verbose_name='شناسه قالب')
    parameters = models.JSONField(default=dict, verbose_name='پارامترهای قالب')
    
    # اطلاعات کاربر
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='sms_logs', verbose_name='کاربر')
    
    # وضعیت ارسال
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', 
                             db_index=True, verbose_name='وضعیت')
    
    # پاسخ سرویس
    response_data = models.JSONField(null=True, blank=True, verbose_name='پاسخ SMS.ir')
    track_id = models.CharField(max_length=100, null=True, blank=True, 
                               db_index=True, verbose_name='شناسه رهگیری')
    error_message = models.TextField(null=True, blank=True, verbose_name='پیام خطا')
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='زمان ایجاد')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان ارسال')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تحویل')
    
    # هزینه (اختیاری - برای محاسبات آتی)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, 
                                        verbose_name='هزینه تقریبی (ریال)')
    
    # متادیتا
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='آی‌پی درخواست')
    user_agent = models.TextField(null=True, blank=True, verbose_name='User Agent')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['mobile_number', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['template_id', '-created_at']),
        ]
        verbose_name = 'لاگ پیامک'
        verbose_name_plural = 'لاگ‌های پیامک'
    
    def __str__(self):
        return f"SMS to {self.mobile_number} - {self.get_status_display()} - {self.created_at}"
    
    def mark_as_sent(self, track_id=None, response_data=None):
        """علامت‌گذاری به عنوان ارسال‌شده."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        if track_id:
            self.track_id = track_id
        if response_data:
            self.response_data = response_data
        self.save()
    
    def mark_as_failed(self, error_message):
        """علامت‌گذاری به عنوان ناموفق."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
    
    def mark_as_rate_limited(self, reason):
        """علامت‌گذاری به عنوان محدود شده."""
        self.status = 'rate_limited'
        self.error_message = reason
        self.save()


class SMSTemplate(models.Model):
    """مدیریت قالب‌های پیامک."""
    
    name = models.CharField(max_length=100, unique=True, verbose_name='نام قالب')
    template_id = models.IntegerField(unique=True, verbose_name='شناسه قالب در SMS.ir')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    
    # محتوای قالب برای پیش‌نمایش
    template_text = models.TextField(verbose_name='متن قالب', 
                                    help_text='از {PARAM_NAME} برای پارامترها استفاده کنید')
    parameters = models.JSONField(default=list, verbose_name='لیست پارامترها',
                                 help_text='مثال: ["NAME", "DATE", "TIME"]')
    
    # تنظیمات
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    usage_count = models.IntegerField(default=0, verbose_name='تعداد استفاده')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'قالب پیامک'
        verbose_name_plural = 'قالب‌های پیامک'
    
    def __str__(self):
        return f"{self.name} (ID: {self.template_id})"
    
    def increment_usage(self):
        """افزایش شمارنده استفاده."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
    
    def preview(self, params_dict):
        """پیش‌نمایش قالب با پارامترهای نمونه."""
        text = self.template_text
        for key, value in params_dict.items():
            text = text.replace(f"{{{key}}}", str(value))
        return text
