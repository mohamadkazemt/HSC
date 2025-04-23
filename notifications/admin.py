from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'user')
    search_fields = ('message', 'user__username', 'user__email')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',) 