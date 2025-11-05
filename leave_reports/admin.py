from django.contrib import admin
from .models import ShiftReport, ApprovalHierarchy


@admin.register(ShiftReport)
class ShiftReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'shift_date', 'status', 'replacement_person', 'created_at']
    list_filter = ['status', 'leave_type', 'shift_date', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'description']
    date_hierarchy = 'shift_date'
    readonly_fields = ['created_at', 'replacement_approved_at', 'final_approved_at', 'rejected_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'leave_type', 'shift_date', 'shift_type', 'work_group', 'description')
        }),
        ('جزئیات زمانی', {
            'fields': ('leave_hours', 'start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('فرآیند تأیید', {
            'fields': ('status', 'replacement_person', 'replacement_approved', 'replacement_approved_at',
                      'final_approver', 'final_approved_at')
        }),
        ('رد درخواست', {
            'fields': ('rejection_reason', 'rejected_by', 'rejected_at'),
            'classes': ('collapse',)
        }),
        ('سایر اطلاعات', {
            'fields': ('registration', 'crate_by', 'created_at', 'exported_to_excel'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ApprovalHierarchy)
class ApprovalHierarchyAdmin(admin.ModelAdmin):
    list_display = ['get_location', 'approver', 'created_at']
    list_filter = ['section', 'part']
    search_fields = ['approver__user__first_name', 'approver__user__last_name', 'section__name', 'part__name']
    
    def get_location(self, obj):
        if obj.part:
            return f"{obj.part.name} ({obj.part.section.name})"
        elif obj.section:
            return obj.section.name
        return "-"
    get_location.short_description = "بخش/قسمت"
