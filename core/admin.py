from django.contrib import admin
from .models import SiteSettings
from .ai_models import AISettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    pass

@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ['provider', 'model', 'is_active', 'last_test_status', 'last_tested_at', 'updated_at']
    readonly_fields = ['last_tested_at', 'last_test_status', 'last_test_message', 'updated_at']
    fieldsets = (
        ('تنظیمات اصلی', {
            'fields': ('provider', 'api_key', 'api_base_url', 'model', 'is_active')
        }),
        ('تنظیمات پیشرفته', {
            'fields': ('timeout', 'max_retries', 'cache_timeout', 'temperature'),
            'classes': ('collapse',)
        }),
        ('اطلاعات تست', {
            'fields': ('last_tested_at', 'last_test_status', 'last_test_message'),
            'classes': ('collapse',)
        }),
        ('سایر', {
            'fields': ('updated_at',)
        }),
    )
