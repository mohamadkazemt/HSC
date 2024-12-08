from django import forms
from .models import (
    WorkFrontStatus, DumpStatus, DrillingSiteStatus, Incident,
    HSEParticipation, SafetyStop, HSEReport
)

class StyledForm(forms.ModelForm):
    """
    پایه‌ای برای فرم‌ها با کلاس‌های CSS اضافه شده.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({'class': 'form-control', 'placeholder': field.label})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control', 'rows': 4, 'placeholder': field.label})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select select2', 'data-control': 'select2'})

class WorkFrontStatusForm(StyledForm):
    class Meta:
        model = WorkFrontStatus
        fields = ['workfront', 'status', 'comments']

class DumpStatusForm(StyledForm):
    class Meta:
        model = DumpStatus
        fields = ['dump', 'status', 'comments']

class DrillingSiteStatusForm(StyledForm):
    class Meta:
        model = DrillingSiteStatus
        fields = ['drilling_site', 'status', 'comments']

class IncidentForm(StyledForm):
    class Meta:
        model = Incident
        fields = ['person_type', 'person', 'user_profile', 'description']

class HSEParticipationForm(StyledForm):
    class Meta:
        model = HSEParticipation
        fields = ['person_type', 'person', 'user_profile', 'description']

class SafetyStopForm(StyledForm):
    class Meta:
        model = SafetyStop
        fields = ['reason', 'duration_hours']

class HSEReportForm(StyledForm):
    class Meta:
        model = HSEReport
        fields = ['shift_date', 'supervisor', 'next_shift_tasks']
