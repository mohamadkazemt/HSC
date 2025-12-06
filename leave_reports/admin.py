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
    list_display = ['approver', 'get_criteria_display', 'get_weight_display', 'created_at', 'updated_at']
    list_filter = [
        'work_group', 'section', 'part', 'unit_group', 'position', 
        'created_at', 'updated_at'
    ]
    search_fields = [
        'approver__user__first_name', 
        'approver__user__last_name', 
        'approver__user__username',
        'specific_users__first_name',
        'specific_users__last_name',
        'section__name', 
        'part__name',
        'unit_group__name',
        'position__name'
    ]
    
    fieldsets = (
        ('تأیید کننده', {
            'fields': ('approver',)
        }),
        ('معیارهای تطبیق', {
            'fields': (
                'specific_users',
                'work_group',
                'position',
                'unit_group',
                'part',
                'section',
            ),
            'description': 'حداقل یکی از این فیلدها باید انتخاب شود. قانون با معیارهای بیشتر اولویت بالاتری دارد.'
        }),
        ('اطلاعات زمانی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_criteria_display(self, obj):
        """نمایش معیارهای انتخاب شده"""
        criteria = []
        if obj.specific_users.exists():
            user_names = [user.get_full_name() for user in obj.specific_users.all()]
            if len(user_names) == 1:
                criteria.append(f"کاربر: {user_names[0]}")
            else:
                criteria.append(f"کاربران: {', '.join(user_names[:3])}{' و ...' if len(user_names) > 3 else ''}")
        if obj.work_group:
            criteria.append(f"گروه: {obj.get_work_group_display()}")
        if obj.position:
            criteria.append(f"سمت: {obj.position.name}")
        if obj.unit_group:
            criteria.append(f"گروه واحد: {obj.unit_group.name}")
        if obj.part:
            criteria.append(f"قسمت: {obj.part.name}")
        if obj.section:
            criteria.append(f"بخش: {obj.section.name}")
        
        return " + ".join(criteria) if criteria else "عمومی"
    get_criteria_display.short_description = "معیارها"
    
    def get_weight_display(self, obj):
        """نمایش وزن قانون"""
        return obj.get_weight()
    get_weight_display.short_description = "وزن"
    get_weight_display.admin_order_field = 'id'  # برای مرتب‌سازی بر اساس وزن نیاز به annotation داریم
