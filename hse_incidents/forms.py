# forms.py
from django import forms
from .models import IncidentReport

class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = [
            'incident_date', 'incident_time', 'incident_location',
            'involved_person', 'involved_equipment',
            'injury_type', 'affected_body_part', 'damage_description',
            'related_entity', 'related_contractor',
            'fire_truck_needed', 'ambulance_needed', 'hospitalized', 'transportation_type',
            'full_description', 'initial_cause',
        ] # حذف فیلد های اتوماتیک
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'type': 'time'})
        }