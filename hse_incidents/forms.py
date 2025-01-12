# hse_incidents/forms.py
from django import forms
from .models import IncidentReport, HseCompletionReport


class IncidentReportForm(forms.ModelForm):
    class Meta:
        model = IncidentReport
        fields = [
            'incident_date', 'incident_time', 'location', 'section',
            'involved_person', 'involved_equipment',
            'injury_type', 'affected_body_part', 'damage_description',
            'related_entity', 'related_contractor','related_contractor_employees',
            'fire_truck_needed', 'ambulance_needed', 'hospitalized', 'transportation_type',
            'full_description', 'initial_cause',
        ]
        widgets = {
            'incident_date': forms.DateInput(attrs={'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'type': 'time'})
        }


class HseCompletionReportForm(forms.ModelForm):
    class Meta:
        model = HseCompletionReport
        fields = [
            'incident_report_time',
            'hospital_admission_time',
            'patient_condition_temperature',
            'patient_condition_respiration',
            'patient_condition_pulse',
            'patient_condition_blood_pressure',
            'patient_condition_sop',
            'direct_causes',
            'indirect_causes',
            'root_causes',
            'social_security_notification',
            'social_security_file',
            'insurance_notification',
            'insurance_file',
            'police_notification',
            'police_file',
            'traffic_police_notification',
            'traffic_police_file',
            'labor_office_notification',
            'final_injury_outcome',
            'estimated_cost',
            'lost_workdays',
            'environmental_damage',
            'environmental_damage_type',
            'environmental_damage_description',
            'incident_committee_formed',
            'incident_committee_date',
            'incident_committee_details',
            'incident_committee_file',
            'corrective_actions',
            'lessons_learned',
            'lessons_learned_file',
        ]

        widgets = {
            'incident_report_time': forms.TimeInput(attrs={'type': 'time'}),
            'hospital_admission_time': forms.TimeInput(attrs={'type': 'time'}),
            'incident_committee_date': forms.DateInput(attrs={'type': 'date'}),
        }