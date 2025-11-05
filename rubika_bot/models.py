from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class RubikaBotSettings(models.Model):
    """Singleton-like settings to store bot token and metadata."""
    token = models.CharField(max_length=255, blank=True, null=True)
    base_api_url = models.URLField(default='https://rubika.ir/bot')
    bot_username = models.CharField(max_length=150, blank=True, null=True)
    deeplink_template = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Use {bot_username} and {code}, e.g. https://rubika.ir/{bot_username}?start={code}"
    )
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
    def generate_for_user(cls, user, ttl_minutes=30):
        code = uuid.uuid4().hex
        expires = timezone.now() + timezone.timedelta(minutes=ttl_minutes)
        return cls.objects.create(user=user, code=code, expires_at=expires)

    def mark_used(self, chat_id=None):
        self.used = True
        self.chat_id = chat_id or self.chat_id
        self.used_at = timezone.now()
        self.save(update_fields=['used', 'chat_id', 'used_at'])