from django.contrib import admin

from .models import Broadcast, BroadcastRecipient, MessageTemplate, ReminderLog


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("leave", "role", "target", "status", "triggered_by", "created_at")
    list_filter = ("status", "role")
    search_fields = ("target", "message")
    readonly_fields = [field.name for field in ReminderLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "channel", "is_active", "usage_count", "updated_at")
    list_filter = ("channel", "is_active")
    search_fields = ("title", "text")
    list_editable = ("is_active",)


@admin.register(Broadcast)
class BroadcastAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "channel", "status", "recipients_resolved",
        "recipients_invalid", "scheduled_for", "created_by", "created_at",
    )
    list_filter = ("channel", "status")
    search_fields = ("title", "text")
    readonly_fields = [
        "created_at", "sent_at", "recipients_total",
        "recipients_resolved", "recipients_invalid",
    ]
    actions = ["mark_completed"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="علامت‌گذاری به‌عنوان انجام‌شده")
    def mark_completed(self, request, queryset):
        queryset.update(status=Broadcast.Status.COMPLETED)


@admin.register(BroadcastRecipient)
class BroadcastRecipientAdmin(admin.ModelAdmin):
    list_display = ("broadcast", "mobile", "name", "resolve_status", "send_status", "sent_at")
    list_filter = ("resolve_status", "send_status")
    search_fields = ("mobile", "name")
