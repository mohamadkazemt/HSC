from django.contrib import admin
from .models import Meeting

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'start_time', 'end_time', 'location', 'participants_list', 'status')
    list_filter = ('date', 'status', 'participants')
    search_fields = ('title', 'description', 'location')
    filter_horizontal = ('participants',)
    date_hierarchy = 'date'
    ordering = ('-date', 'start_time')

    def participants_list(self, obj):
        return ", ".join([p.get_full_name() for p in obj.participants.all()])
    participants_list.short_description = "شرکت‌کنندگان"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(participants=request.user)
        return queryset

    def save_model(self, request, obj, form, change):
        if not obj.creator:
            obj.creator = request.user
        super().save_model(request, obj, form, change)
