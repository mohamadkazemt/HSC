from django.contrib import admin
from .models import RubikaUser, RubikaBotSettings, RubikaConnectionCode, WebhookLog, LeaveRequestState


@admin.register(RubikaUser)
class RubikaUserAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'user', 'first_name', 'last_name', 'last_seen', 'created_at')
    search_fields = ('chat_id', 'first_name', 'last_name', 'user__username')


@admin.register(RubikaBotSettings)
class RubikaBotSettingsAdmin(admin.ModelAdmin):
    list_display = ('token', 'bot_username', 'updated_at')
    list_editable = ('bot_username',)


@admin.register(RubikaConnectionCode)
class RubikaConnectionCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'used', 'expires_at', 'used_at')
    search_fields = ('code', 'user__username')
    list_filter = ('used',)


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ('log_type', 'title', 'message_preview', 'created_at')
    list_filter = ('log_type', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'پیام'


@admin.register(LeaveRequestState)
class LeaveRequestStateAdmin(admin.ModelAdmin):
    list_display = ('rubika_user', 'step', 'started_at', 'updated_at')
    list_filter = ('step', 'started_at')
    search_fields = ('rubika_user__chat_id', 'rubika_user__first_name', 'rubika_user__last_name')
    readonly_fields = ('started_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Prevent manual addition - states are created automatically
        return False