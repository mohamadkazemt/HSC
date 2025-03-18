from django.contrib import admin
from .models import Meeting

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'creator', 'notify_transport_coordinator')
    list_filter = ('date', 'creator', 'notify_transport_coordinator')
    search_fields = ('title', 'creator__username', 'creator__first_name', 'creator__last_name')
    filter_horizontal = ('participants',)
    date_hierarchy = 'date'
    ordering = ('-date', '-time')
