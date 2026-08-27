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


class MessageTemplate(models.Model):
    """قالب پیام آماده برای ارسال سریع پیام گروهی."""

    class Channel(models.TextChoices):
        SMS = "sms", "پیامک (SMS)"
        RUBIKA = "rubika", "روبیکا"

    title = models.CharField(max_length=150, verbose_name="عنوان قالب")
    text = models.TextField(verbose_name="متن قالب")
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.SMS, verbose_name="کانال ارسال"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="تعداد استفاده")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "قالب پیام"
        verbose_name_plural = "قالب‌های پیام"

    def __str__(self):
        return self.title

    def increment_usage(self):
        self.usage_count += 1
        self.save(update_fields=["usage_count"])


class Broadcast(models.Model):
    """یک پیام گروهی (به sms.ir یا روبیکا) همراه با وضعیت ارسال."""

    class Channel(models.TextChoices):
        SMS = "sms", "پیامک (SMS)"
        RUBIKA = "rubika", "روبیکا"

    class Status(models.TextChoices):
        DRAFT = "draft", "پیش‌نویس"
        RESOLVED = "resolved", "آماده ارسال"
        SCHEDULED = "scheduled", "زمان‌بندی شده"
        SENDING = "sending", "در حال ارسال"
        COMPLETED = "completed", "انجام شد"
        PARTIAL = "partial", "با خطا انجام شد"
        FAILED = "failed", "ناموفق"
        CANCELLED = "cancelled", "لغو شد"

    title = models.CharField(max_length=200, blank=True, default="", verbose_name="عنوان پیام")
    text = models.TextField(verbose_name="متن پیام")
    channel = models.CharField(
        max_length=10, choices=Channel.choices, default=Channel.SMS, verbose_name="کانال ارسال"
    )

    mobile_numbers = models.JSONField(default=list, blank=True, verbose_name="شماره‌های موبایل")
    personnel_codes = models.JSONField(default=list, blank=True, verbose_name="کدهای پرسنلی")

    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.DRAFT, verbose_name="وضعیت"
    )

    recipients_total = models.PositiveIntegerField(default=0, verbose_name="دریافت‌کنندگان کل")
    recipients_resolved = models.PositiveIntegerField(default=0, verbose_name="دریافت‌کنندگان قابل ارسال")
    recipients_invalid = models.PositiveIntegerField(default=0, verbose_name="دریافت‌کنندگان نامعتبر")

    scheduled_for = models.DateTimeField(null=True, blank=True, verbose_name="زمان‌بندی ارسال")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")

    source_file_name = models.CharField(max_length=255, blank=True, default="", verbose_name="نام فایل منبع")
    error = models.TextField(blank=True, default="", verbose_name="پیام خطا")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "پیام گروهی"
        verbose_name_plural = "پیام‌های گروهی"

    def __str__(self):
        return f"{self.title or ('پیام ' + self.get_channel_display())} ({self.get_status_display()})"


class BroadcastRecipient(models.Model):
    """گیرنده یک پیام گروهی با وضعیت تشخیص و ارسال مجزا."""

    class ResolveStatus(models.TextChoices):
        OK = "ok", "یافت شد"
        NO_PHONE = "no_phone", "بدون شماره همراه"
        NOT_FOUND = "not_found", "کاربر یافت نشد"
        INVALID = "invalid", "شماره نامعتبر"

    class SendStatus(models.TextChoices):
        PENDING = "pending", "در انتظار"
        SENDING = "sending", "در حال ارسال"
        SENT = "sent", "ارسال شد"
        FAILED = "failed", "ناموفق"
        CANCELED = "canceled", "لغو شد"

    broadcast = models.ForeignKey(
        Broadcast, on_delete=models.CASCADE, related_name="recipients"
    )
    mobile = models.CharField(max_length=30, blank=True, default="", verbose_name="شماره موبایل")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="کاربر مرتبط",
    )
    name = models.CharField(max_length=150, blank=True, default="", verbose_name="نام")

    resolve_status = models.CharField(
        max_length=15, choices=ResolveStatus.choices, default=ResolveStatus.OK, verbose_name="وضعیت تشخیص"
    )
    resolve_note = models.CharField(max_length=200, blank=True, default="", verbose_name="توضیح تشخیص")

    send_status = models.CharField(
        max_length=12, choices=SendStatus.choices, default=SendStatus.PENDING, verbose_name="وضعیت ارسال"
    )
    error = models.TextField(blank=True, default="", verbose_name="خطای ارسال")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")

    class Meta:
        verbose_name = "گیرنده پیام گروهی"
        verbose_name_plural = "گیرندگان پیام گروهی"

    def __str__(self):
        return f"{self.mobile or self.name or self.user} ({self.get_send_status_display()})"
