from django.contrib import admin

# Register your models here.
from .models import IncidentReport, InjuryType, HseCompletionReport, IncidentDashboardSettings


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'incident_date', 'get_incident_type_display', 'location', 'is_severe_production_stoppage', 'is_completed']
    list_filter = ['incident_date', 'incident_type', 'is_severe_production_stoppage', 'is_completed', 'fire_truck_needed', 'ambulance_needed']
    search_fields = ['full_description', 'initial_cause', 'location__name']
    date_hierarchy = 'incident_date'
    
    def get_incident_type_display(self, obj):
        return obj.get_incident_type_display() if obj.incident_type else '-'
    get_incident_type_display.short_description = 'نوع حادثه'


@admin.register(InjuryType)
class InjuryTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(HseCompletionReport)
class HseCompletionReportAdmin(admin.ModelAdmin):
    list_display = ['incident_report', 'lost_workdays', 'social_security_notification']
    list_filter = ['social_security_notification', 'insurance_notification', 'police_notification']
    search_fields = ['incident_report__full_description']


@admin.register(IncidentDashboardSettings)
class IncidentDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['days_without_incident_start_date', 'average_man_hours_per_day', 'updated_at', 'updated_by']
    
    def has_add_permission(self, request):
        # فقط یک رکورد مجاز است
        return not IncidentDashboardSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # حذف مجاز نیست
        return False