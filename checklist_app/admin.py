from django.contrib import admin
from .models import Checklist, Question, Answer

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('id', 'checklist_type', 'get_item', 'date', 'shift', 'shift_group', 'user')
    list_filter = ('checklist_type', 'date', 'shift', 'shift_group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'machine__workshop_code', 'location_section__section')
    date_hierarchy = 'date'

    def get_item(self, obj):
        if obj.checklist_type == 'machine':
            return obj.machine
        return obj.location_section
    get_item.short_description = 'آیتم'

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
