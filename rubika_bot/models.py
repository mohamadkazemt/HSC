from django.conf import settings
from django.db import models
from django.utils import timezone
from django_cryptography.fields import encrypt
import uuid

from .constants import CONNECTION_CODE_TTL_MINUTES
from .validators import validate_rubika_token


class RubikaBotSettings(models.Model):
    """Singleton-like settings to store bot token and metadata."""
    token = encrypt(
        models.CharField(
            max_length=255,
            blank=True,
            null=True,
            validators=[validate_rubika_token],
            help_text="توکن ربات روبیکا (به صورت رمزگذاری‌شده ذخیره می‌شود).",
        )
    )
    bot_username = models.CharField(max_length=150, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rubika Bot Settings'
        verbose_name_plural = 'Rubika Bot Settings'

    def __str__(self):
        return 'Rubika Bot Settings'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RubikaUser(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='rubika_profile'
    )
    chat_id = models.CharField(max_length=50, unique=True, primary_key=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['first_name']),
            models.Index(fields=['last_name']),
        ]

    def __str__(self):
        return f'{self.chat_id} ({self.user.username if self.user else "unlinked"})'

    # Manager-like helpers migrated from user_manager
    @classmethod
    def get_or_create_by_chat(cls, chat_id, defaults=None):
        obj, _ = cls.objects.get_or_create(chat_id=chat_id, defaults=defaults or {})
        return obj

    def touch_seen(self):
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class RubikaConnectionCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rubika_connection_codes')
    code = models.CharField(max_length=64, unique=True, db_index=True)
    used = models.BooleanField(default=False)
    chat_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'used']),
        ]

    def __str__(self):
        return f'{self.user_id}:{self.code} (used={self.used})'

    @classmethod
    def generate_for_user(cls, user, ttl_minutes: int = CONNECTION_CODE_TTL_MINUTES):
        code = uuid.uuid4().hex
        expires = timezone.now() + timezone.timedelta(minutes=ttl_minutes)
        return cls.objects.create(user=user, code=code, expires_at=expires)

    def mark_used(self, chat_id=None):
        self.used = True
        self.chat_id = chat_id or self.chat_id
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'chat_id', 'used_at'])


class WebhookLog(models.Model):
    """ذخیره لاگ‌های webhook برای نمایش در پنل"""
    LOG_TYPES = (
        ('incoming', 'دریافتی'),
        ('outgoing', 'ارسالی'),
        ('error', 'خطا'),
        ('info', 'اطلاعات'),
    )
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, default='info')
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['log_type', 'created_at']),
        ]
    
    def __str__(self):
        return f'[{self.log_type}] {self.title} - {self.created_at}'
    
    @classmethod
    def log_incoming(cls, title, message, data=None):
        """لاگ پیام دریافتی"""
        return cls.objects.create(
            log_type='incoming',
            title=title,
            message=message,
            data=data
        )
    
    @classmethod
    def log_outgoing(cls, title, message, data=None):
        """لاگ پیام ارسالی"""
        return cls.objects.create(
            log_type='outgoing',
            title=title,
            message=message,
            data=data
        )
    
    @classmethod
    def log_error(cls, title, message, data=None):
        """لاگ خطا"""
        return cls.objects.create(
            log_type='error',
            title=title,
            message=message,
            data=data
        )
    
    @classmethod
    def log_info(cls, title, message, data=None):
        """لاگ اطلاعات"""
        return cls.objects.create(
            log_type='info',
            title=title,
            message=message,
            data=data
        )
    
    @classmethod
    def log_warning(cls, title, message, data=None):
        """لاگ هشدار"""
        return cls.objects.create(
            log_type='error',  # استفاده از error type برای warning
            title=f'⚠️ {title}',
            message=message,
            data=data
        )
    
    @classmethod
    def cleanup_old_logs(cls, days=7):
        """حذف لاگ‌های قدیمی‌تر از X روز"""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(created_at__lt=cutoff).delete()