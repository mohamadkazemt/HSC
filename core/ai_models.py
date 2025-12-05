# core/ai_models.py
"""
مدل‌های مربوط به تنظیمات هوش مصنوعی
"""
from django.db import models
from django_cryptography.fields import encrypt
from django_cryptography.core.signing import BadSignature
import logging

logger = logging.getLogger(__name__)


class AISettings(models.Model):
    """
    تنظیمات هوش مصنوعی - Singleton pattern
    """
    
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('google', 'Google AI Studio (Gemini)'),
        ('local', 'Local API (Ollama)'),
    ]
    
    # Provider و API Key
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='openai',
        verbose_name='ارائه‌دهنده AI'
    )
    
    api_key = encrypt(
        models.CharField(
            max_length=500,
            blank=True,
            null=True,
            verbose_name='API Key',
            help_text='کلید API (به صورت رمزگذاری‌شده ذخیره می‌شود)'
        )
    )
    
    api_base_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='آدرس پایه API',
        help_text='برای Google AI Studio: https://generativelanguage.googleapis.com/v1beta'
    )
    
    model = models.CharField(
        max_length=100,
        default='gpt-4',
        verbose_name='مدل',
        help_text='نام مدل استفاده شده (مثلاً: gpt-4, gemini-pro, claude-3-opus)'
    )
    
    # تنظیمات پیشرفته
    timeout = models.IntegerField(
        default=30,
        verbose_name='Timeout (ثانیه)',
        help_text='حداکثر زمان انتظار برای پاسخ API'
    )
    
    max_retries = models.IntegerField(
        default=3,
        verbose_name='تعداد تلاش مجدد',
        help_text='تعداد دفعات تلاش مجدد در صورت خطا'
    )
    
    cache_timeout = models.IntegerField(
        default=3600,
        verbose_name='زمان کش (ثانیه)',
        help_text='زمان نگهداری نتایج در کش (1 ساعت = 3600 ثانیه)'
    )
    
    temperature = models.FloatField(
        default=0.7,
        verbose_name='Temperature',
        help_text='میزان خلاقیت پاسخ‌ها (0-1)'
    )
    
    # وضعیت
    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال',
        help_text='آیا سرویس AI فعال است؟'
    )
    
    # اطلاعات اضافی
    last_tested_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='آخرین تست اتصال'
    )
    
    last_test_status = models.BooleanField(
        null=True,
        blank=True,
        verbose_name='وضعیت آخرین تست',
        help_text='True = موفق، False = ناموفق'
    )
    
    last_test_message = models.TextField(
        blank=True,
        null=True,
        verbose_name='پیام آخرین تست'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ آخرین بروزرسانی'
    )
    
    class Meta:
        verbose_name = 'تنظیمات AI'
        verbose_name_plural = 'تنظیمات AI'
    
    def __str__(self):
        return f'AI Settings - {self.get_provider_display()}'
    
    @classmethod
    def get_solo(cls):
        """دریافت تنظیمات (ایجاد در صورت عدم وجود)"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
    
    def get_api_key_safe(self) -> str | None:
        """دریافت ایمن API Key با مدیریت خطا"""
        try:
            return self.api_key if self.api_key else None
        except BadSignature:
            logger.warning("خطا در رمزگشایی API Key")
            return None
    
    def get_default_api_base_url(self) -> str:
        """دریافت آدرس پایه پیش‌فرض بر اساس provider"""
        defaults = {
            'openai': 'https://api.openai.com/v1',
            'anthropic': 'https://api.anthropic.com/v1',
            'google': 'https://generativelanguage.googleapis.com/v1beta',
            'local': 'http://localhost:11434/v1',
        }
        return defaults.get(self.provider, defaults['openai'])
    
    def save(self, *args, **kwargs):
        """ذخیره با تنظیمات پیش‌فرض"""
        # تنظیم آدرس پایه پیش‌فرض در صورت خالی بودن
        if not self.api_base_url:
            self.api_base_url = self.get_default_api_base_url()
        super().save(*args, **kwargs)
