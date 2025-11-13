from django.conf import settings
from django.db import models
from django.utils import timezone
from django_cryptography.fields import encrypt
import uuid
from urllib.parse import quote

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

    proxy_enabled = models.BooleanField(default=False)
    proxy_scheme = models.CharField(
        max_length=10,
        choices=(
            ('socks5', 'SOCKS5'),
            ('http', 'HTTP'),
            ('https', 'HTTPS'),
        ),
        default='socks5',
    )
    proxy_host = models.CharField(max_length=255, blank=True, null=True)
    proxy_port = models.PositiveIntegerField(blank=True, null=True)
    proxy_username = models.CharField(max_length=255, blank=True, null=True)
    proxy_password = encrypt(models.CharField(max_length=255, blank=True, null=True))

    class Meta:
        verbose_name = 'Rubika Bot Settings'
        verbose_name_plural = 'Rubika Bot Settings'

    def __str__(self):
        return 'Rubika Bot Settings'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def build_proxy_url(self) -> str:
        if not self.proxy_enabled:
            return ''
        host = (self.proxy_host or '').strip()
        port = self.proxy_port
        if not host or not port:
            return ''
        auth = ''
        username = (self.proxy_username or '').strip()
        password = self.proxy_password or ''
        if username:
            auth = quote(username, safe='')
            if password:
                auth += f':{quote(password, safe="")}'
            auth += '@'
        return f'{self.proxy_scheme}://{auth}{host}:{port}'

    def get_masked_proxy_url(self) -> str:
        if not self.proxy_enabled:
            return ''
        host = (self.proxy_host or '').strip()
        port = self.proxy_port
        if not host or not port:
            return ''
        username = (self.proxy_username or '').strip()
        if username:
            return f'{self.proxy_scheme}://{username}@{host}:{port}'
        return f'{self.proxy_scheme}://{host}:{port}'


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


class LeaveRequestState(models.Model):
    """ذخیره state فرایند درخواست مرخصی کاربران در ربات"""
    rubika_user = models.OneToOneField(
        RubikaUser,
        on_delete=models.CASCADE,
        related_name='leave_request_state'
    )
    
    # State management
    step = models.CharField(
        max_length=50,
        default='idle',
        help_text='مرحله فعلی: idle, leave_type, date, shift_type, replacement, hourly_times, description, confirm'
    )
    
    # Collected data (stored as JSON)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='داده‌های جمع‌آوری شده شامل: leave_type, date, shift_type, replacement_id, start_time, end_time, description'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'وضعیت درخواست مرخصی'
        verbose_name_plural = 'وضعیت‌های درخواست مرخصی'
        indexes = [
            models.Index(fields=['rubika_user', 'step']),
        ]
    
    def __str__(self):
        return f'{self.rubika_user.chat_id} - {self.step}'
    
    def reset(self):
        """بازنشانی state به حالت اولیه"""
        self.step = 'idle'
        self.data = {}
        self.save()
    
    def update_step(self, step, data_update=None):
        """به‌روزرسانی مرحله و داده‌ها"""
        self.step = step
        if data_update:
            self.data.update(data_update)
        self.save()
    
    @classmethod
    def get_or_create_for_user(cls, rubika_user):
        """دریافت یا ساخت state برای یک کاربر"""
        obj, created = cls.objects.get_or_create(rubika_user=rubika_user)
        return obj


class ConnectionRequestState(models.Model):
    """ذخیره state فرایند اتصال از طریق SMS"""
    rubika_user = models.OneToOneField(
        RubikaUser,
        on_delete=models.CASCADE,
        related_name='connection_request_state'
    )
    
    # State management
    step = models.CharField(
        max_length=50,
        default='idle',
        help_text='مرحله فعلی: idle, national_code, personnel_code, confirm'
    )
    
    # Collected data
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='داده‌های جمع‌آوری شده شامل: national_code, personnel_code'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'وضعیت درخواست اتصال'
        verbose_name_plural = 'وضعیت‌های درخواست اتصال'
        indexes = [
            models.Index(fields=['rubika_user', 'step']),
        ]
    
    def __str__(self):
        return f'{self.rubika_user.chat_id} - {self.step}'
    
    def reset(self):
        """بازنشانی state به حالت اولیه"""
        self.step = 'idle'
        self.data = {}
        self.save()
    
    def update_step(self, step, data_update=None):
        """به‌روزرسانی مرحله و داده‌ها"""
        self.step = step
        if data_update:
            self.data.update(data_update)
        self.save()
    
    @classmethod
    def get_or_create_for_user(cls, rubika_user):
        """دریافت یا ساخت state برای یک کاربر"""
        obj, created = cls.objects.get_or_create(rubika_user=rubika_user)
        return obj
