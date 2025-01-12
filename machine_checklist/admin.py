# checklist/admin.py
from django.contrib import admin
from .models import Checklist, Question, Answer

class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('user', 'machine', 'date', 'shift', 'shift_group')
admin.site.register(Checklist, ChecklistAdmin)
admin.site.register(Question)
admin.site.register(Answer)