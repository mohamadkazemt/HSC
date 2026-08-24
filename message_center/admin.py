from django.contrib import admin

from .models import ReminderLog


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
