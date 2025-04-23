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
    list_display = ('id', 'question_scope', 'get_scope_item', 'text', 'is_required', 'question_type')
    list_filter = ('question_scope', 'is_required', 'question_type')
    search_fields = ('text', 'machine_type__name', 'location_section__section')

    def get_scope_item(self, obj):
        if obj.question_scope == 'machine':
            return obj.machine_type
        return obj.location_section
    get_scope_item.short_description = 'آیتم محدوده'

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
