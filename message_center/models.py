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
