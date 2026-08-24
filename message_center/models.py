import secrets

from django.conf import settings
from django.db import models


class ReminderLog(models.Model):
    """One outbound leave-approval reminder through PeyamHub."""

    class Role(models.TextChoices):
        REPLACEMENT = "replacement", "جانشین"
        MANAGER = "manager", "مدیر تأییدکننده"

    class Status(models.TextChoices):
        SENT = "sent", "ارسال شد"
        FAILED = "failed", "ناموفق"
        FAILED_PERMANENT = "failed_permanent", "شماره نامعتبر (تلاش نمی‌شود)"
        SKIPPED_NO_PHONE = "skipped_no_phone", "بدون شماره همراه"
        SKIPPED_DUPLICATE = "skipped_duplicate", "اخیراً ارسال شده"

    leave = models.ForeignKey(
        "leave_reports.ShiftReport", on_delete=models.CASCADE, related_name="reminder_logs"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    target = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices)
    error = models.TextField(blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "لاگ یادآوری"
        verbose_name_plural = "لاگ‌های یادآوری"

    def __str__(self):
        return f"{self.get_role_display()} -> {self.target} ({self.get_status_display()})"


def generate_webhook_secret():
    return secrets.token_hex(32)


class WebhookConfig(models.Model):
    """تنظیمات وب‌هوک دریافتی PeyamHub (تک‌ردیفی).

    PeyamHub برای هر پیام ورودی، بدنه JSON را با HMAC-SHA256 امضا می‌کند و
    در هدر `X-Rubika-Signature` قرار می‌دهد. این کد امنیتی باید عیناً در
    پنل PeyamHub (بخش وب‌هوک‌ها) ثبت شود.
    """

    secret = models.CharField(
        max_length=100, default=generate_webhook_secret, verbose_name="کد امنیتی"
    )
    is_active = models.BooleanField(default=True, verbose_name="دریافت فعال باشد")
    last_received_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین دریافت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        verbose_name = "تنظیمات وب‌هوک پیام"
        verbose_name_plural = "تنظیمات وب‌هوک پیام"

    def save(self, *args, **kwargs):
        self.pk = 1  # singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "وب‌هوک مرکز پیام"


class InboundMessage(models.Model):
    """پیام دریافتی از PeyamHub (روبیکای اکانت متصل)."""

    account_phone = models.CharField(max_length=20, blank=True, default="")
    chat_guid = models.CharField(max_length=40, blank=True, default="")
    author_guid = models.CharField(max_length=40, blank=True, default="")
    message_type = models.CharField(max_length=30, blank=True, default="")
    text = models.TextField(blank=True, default="")
    message_id = models.CharField(max_length=64, blank=True, default="")
    received_at = models.DateTimeField(null=True, blank=True)
    raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "پیام دریافتی"
        verbose_name_plural = "پیام‌های دریافتی"

    def __str__(self):
        return f"{self.account_phone}: {self.text[:40]}"
