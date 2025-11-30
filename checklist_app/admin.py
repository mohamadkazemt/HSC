from django.contrib import admin
from .models import Checklist, Question, Answer, ChecklistSchedule, ScheduledChecklistInstance

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('id', 'checklist_type', 'get_item', 'machine_status', 'date', 'shift', 'shift_group', 'user', 'has_scheduled_instance')
    list_filter = ('checklist_type', 'date', 'shift', 'shift_group', 'machine_status')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'machine__workshop_code', 'location_section__section')
    date_hierarchy = 'date'

    def get_item(self, obj):
        if obj.checklist_type == 'machine':
            return obj.machine
        elif obj.checklist_type == 'location':
            return obj.location_section
        elif obj.checklist_type == 'contractor_vehicle':
            return obj.contractor_vehicle
        return '-'
    get_item.short_description = 'آیتم'
    
    def has_scheduled_instance(self, obj):
        return '✓' if obj.scheduled_instance else '-'
    has_scheduled_instance.short_description = 'برنامه‌ریزی شده'

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_question_scopes', 'get_scope_items', 'text', 'is_required', 'question_type')
    list_filter = ('is_required', 'question_type')
    search_fields = ('text', 'machine_types__name', 'location_sections__section')
    filter_horizontal = ('machine_types', 'location_sections')

    def get_question_scopes(self, obj):
        return ", ".join(obj.question_scopes)
    get_question_scopes.short_description = 'محدوده‌های سوال'

    def get_scope_items(self, obj):
        items = []
        if 'machine' in obj.question_scopes:
            items.extend([str(mt) for mt in obj.machine_types.all()])
        if 'location' in obj.question_scopes:
            items.extend([str(ls) for ls in obj.location_sections.all()])
        if 'contractor_vehicle' in obj.question_scopes:
            items.extend(obj.vehicle_categories)
        return ", ".join(items) if items else "-"
    get_scope_items.short_description = 'آیتم‌های محدوده'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'checklist', 'question', 'get_answer', 'is_unacceptable')
    list_filter = ('question__question_type', 'checklist__checklist_type')
    search_fields = ('checklist__user__username', 'question__text', 'answer_text', 'selected_option')

    def get_answer(self, obj):
        if obj.question.question_type == 'option':
            return obj.selected_option
        return obj.answer_text
    get_answer.short_description = 'پاسخ'

@admin.register(ChecklistSchedule)
class ChecklistScheduleAdmin(admin.ModelAdmin):
    list_display = ('name', 'checklist_type', 'schedule_type', 'get_target', 'is_active', 'created_at')
    list_filter = ('checklist_type', 'schedule_type', 'is_active', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'
    
    def get_target(self, obj):
        if obj.checklist_type == 'machine':
            return obj.target_machine
        elif obj.checklist_type == 'location':
            return obj.target_location_section
        elif obj.checklist_type == 'contractor_vehicle':
            return obj.target_contractor_vehicle
        return '-'
    get_target.short_description = 'هدف'

@admin.register(ScheduledChecklistInstance)
class ScheduledChecklistInstanceAdmin(admin.ModelAdmin):
    list_display = ('schedule', 'due_date', 'status', 'completed_by', 'completed_at', 'created_at')
    list_filter = ('status', 'due_date', 'schedule__checklist_type', 'schedule__is_active')
    search_fields = ('schedule__name', 'completed_by__username', 'completed_by__first_name', 'completed_by__last_name')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('schedule', 'completed_by')
