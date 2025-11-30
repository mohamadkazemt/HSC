from django.contrib import admin
from django.utils.html import format_html
from .models import FireExtinguisherType, FireExtinguisher, ServiceRecord, MonthlyInspection

@admin.register(FireExtinguisherType)
class FireExtinguisherTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent', 'use_class')
    search_fields = ('name', 'agent', 'use_class')
    list_filter = ('agent', 'use_class')

@admin.register(FireExtinguisher)
class FireExtinguisherAdmin(admin.ModelAdmin):
    list_display = ('serial_tag', 'extinguisher_type', 'manufacturer', 'status', 'location_display', 'next_service_date')
    list_filter = ('status', 'extinguisher_type', 'manufacturer', 'location_type')
    search_fields = ('serial_tag', 'manufacturer', 'model_number')
    readonly_fields = ('replaced_by_extinguisher', 'replaces_extinguisher', 'next_charge_date')
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('serial_tag', 'extinguisher_type', 'capacity_value', 'capacity_unit', 'manufacturer', 'model_number', 'status')
        }),
        ('تاریخ‌ها', {
            'fields': ('purchase_date', 'manufacture_date', 'commission_date', 'expected_lifespan_years')
        }),
        ('خدمات', {
            'fields': ('last_serviced_date', 'next_scheduled_service_date', 'pressure_test_due_date')
        }),
        ('شارژ', {
            'fields': ('last_charge_date', 'next_charge_date')
        }),
        ('مکان', {
            'fields': ('location_type', 'location_section', 'location_machine')
        }),
        ('جایگزینی', {
            'fields': ('replaced_by_extinguisher', 'replaces_extinguisher', 'replacement_notes')
        }),
        ('توضیحات', {
            'fields': ('notes',)
        })
    )

    def location_display(self, obj):
        if obj.location_type == 'section' and obj.location_section:
            return str(obj.location_section)
        elif obj.location_type == 'machine' and obj.location_machine:
            return str(obj.location_machine)
        return '-'
    location_display.short_description = 'مکان'

    def next_service_date(self, obj):
        if obj.next_scheduled_service_date:
            return obj.next_scheduled_service_date
        elif obj.pressure_test_due_date:
            return f"تست فشار: {obj.pressure_test_due_date}"
        return '-'
    next_service_date.short_description = 'تاریخ خدمت بعدی'

@admin.register(ServiceRecord)
class ServiceRecordAdmin(admin.ModelAdmin):
    list_display = ('extinguisher', 'service_type', 'service_date', 'outcome', 'performed_by_display')
    list_filter = ('service_type', 'outcome', 'service_date')
    search_fields = ('extinguisher__serial_tag', 'performed_by_user__username', 'notes')
    readonly_fields = ('extinguisher',)

    def performed_by_display(self, obj):
        if obj.performed_by_user:
            return obj.performed_by_user.get_full_name() or obj.performed_by_user.username
        elif obj.performed_by_external:
            return obj.performed_by_external
        return '-'
    performed_by_display.short_description = 'انجام دهنده'

@admin.register(MonthlyInspection)
class MonthlyInspectionAdmin(admin.ModelAdmin):
    list_display = ('extinguisher', 'inspection_date', 'inspector_display', 'is_passed_display', 'all_checks_passed')
    list_filter = ('inspection_date', 'pressure_charge_status', 'gauge_status', 'hose_nozzle_status', 
                   'body_condition', 'safety_pin_seal_status')
    search_fields = ('extinguisher__serial_tag', 'inspector__username', 'notes')
    readonly_fields = ('is_passed',)
    fieldsets = (
        ('اطلاعات بازدید', {
            'fields': ('extinguisher', 'inspector', 'inspection_date')
        }),
        ('چک‌لیست بازدید', {
            'fields': ('pressure_charge_status', 'gauge_status', 'hose_nozzle_status', 
                      'body_condition', 'safety_pin_seal_status', 'is_passed')
        }),
        ('توضیحات', {
            'fields': ('notes',)
        })
    )

    def inspector_display(self, obj):
        if obj.inspector:
            return obj.inspector.get_full_name() or obj.inspector.username
        return '-'
    inspector_display.short_description = 'بازدید کننده'

    def is_passed_display(self, obj):
        if obj.is_passed:
            return format_html('<span style="color: green;">✓ قبول</span>')
        return format_html('<span style="color: red;">✗ رد</span>')
    is_passed_display.short_description = 'نتیجه'

    def all_checks_passed(self, obj):
        checks = [
            ('شارژ', obj.pressure_charge_status),
            ('گیج', obj.gauge_status),
            ('شیلنگ/نازل', obj.hose_nozzle_status),
            ('بدنه', obj.body_condition),
            ('ضامن/پلمپ', obj.safety_pin_seal_status),
        ]
        passed = [name for name, status in checks if status]
        failed = [name for name, status in checks if not status]
        result = []
        if passed:
            result.append(format_html('<span style="color: green;">✓ {}</span>', ', '.join(passed)))
        if failed:
            result.append(format_html('<span style="color: red;">✗ {}</span>', ', '.join(failed)))
        return format_html('<br>'.join(result)) if result else '-'
    all_checks_passed.short_description = 'جزئیات چک‌لیست'
