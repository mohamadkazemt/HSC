from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from .models import RiskAssessment
from accounts.models import Position


class RiskAssessmentForm(forms.ModelForm):
    """فرم ایجاد و ویرایش ارزیابی ریسک"""
    
    class Meta:
        model = RiskAssessment
        fields = [
            'position',
            'risk_source',
            'risk_source_other',
            'activity_component',
            'job_tasks',
            'related_positions',
            'is_routine',
            'hazard',
            'people_at_risk',
            'potential_event',
            'causes',
            'consequence',
            'existing_controls',
            'control_failure_causes',
            'has_legal_requirement',
            'legal_requirement_desc',
            'is_legal_compliant',
            'probability',
            'severity',
            'control_elimination',
            'control_substitution',
            'control_engineering',
            'control_admin',
            'control_ppe',
            'corrective_action_required',
            'action_number',
            'action_date',
            'action_deadline',
            'responsible_person',
            'is_mue',
            'mue_code',
            'is_emergency',
            'emergency_code',
            'notes',
        ]
        
        widgets = {
            'risk_source': forms.Select(attrs={'class': 'form-select'}),
            'risk_source_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'توضیح دهید...'}),
            'activity_component': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: راهبری لودر'}),
            'job_tasks': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
            'related_positions': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '6'}),
            'is_routine': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hazard': forms.Select(attrs={'class': 'form-select'}),
            'people_at_risk': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'potential_event': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: واژگونی خودرو'}),
            'causes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'consequence': forms.Select(attrs={'class': 'form-select'}),
            'existing_controls': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'control_failure_causes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'has_legal_requirement': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'legal_requirement_desc': forms.TextInput(attrs={'class': 'form-control'}),
            'is_legal_compliant': forms.Select(choices=[(None, '---'), (True, 'بله'), (False, 'خیر')], attrs={'class': 'form-select'}),
            'probability': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'control_elimination': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'control_substitution': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'control_engineering': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'control_admin': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'control_ppe': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'corrective_action_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'action_number': forms.TextInput(attrs={'class': 'form-control'}),
            'action_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'action_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'is_mue': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mue_code': forms.TextInput(attrs={'class': 'form-control'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'emergency_code': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        
    def clean(self):
        cleaned_data = super().clean()
        
        # اگر منشا "سایر" انتخاب شده، باید توضیح داده شود
        if cleaned_data.get('risk_source') == 'other' and not cleaned_data.get('risk_source_other'):
            raise ValidationError({'risk_source_other': 'لطفاً منشا را توضیح دهید.'})
        
        # اگر الزام قانونی وجود دارد، باید شرح داده شود
        if cleaned_data.get('has_legal_requirement') and not cleaned_data.get('legal_requirement_desc'):
            raise ValidationError({'legal_requirement_desc': 'لطفاً الزام قانونی را شرح دهید.'})
        
        # اگر نیاز به اقدام اصلاحی است، باید مهلت تعیین شود
        if cleaned_data.get('corrective_action_required'):
            if not cleaned_data.get('action_deadline'):
                raise ValidationError({'action_deadline': 'لطفاً مهلت اقدام را مشخص کنید.'})
            if not cleaned_data.get('responsible_person'):
                raise ValidationError({'responsible_person': 'لطفاً مسئول اجرا را مشخص کنید.'})
        
        return cleaned_data


class RiskReEvaluationForm(forms.ModelForm):
    """فرم ارزیابی مجدد ریسک (پس از اقدامات اصلاحی)"""
    
    class Meta:
        model = RiskAssessment
        fields = [
            're_evaluation_date',
            'residual_probability',
            'residual_severity',
        ]
        
        widgets = {
            're_evaluation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'residual_probability': forms.Select(attrs={'class': 'form-select'}),
            'residual_severity': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
    def clean(self):
        cleaned_data = super().clean()
        
        # هر سه فیلد باید با هم پر شوند
        date = cleaned_data.get('re_evaluation_date')
        prob = cleaned_data.get('residual_probability')
        sev = cleaned_data.get('residual_severity')
        
        if any([date, prob, sev]) and not all([date, prob, sev]):
            raise ValidationError('برای ارزیابی مجدد باید هر سه فیلد تاریخ، احتمال و شدت را پر کنید.')
        
        return cleaned_data


class RiskFilterForm(forms.Form):
    """فرم فیلتر کردن ریسک‌ها"""
    
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        empty_label="همه مشاغل",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    risk_level = forms.ChoiceField(
        choices=[('', 'همه سطوح')] + list(RiskAssessment.RISK_LEVEL_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    risk_source = forms.ChoiceField(
        choices=[('', 'همه منابع')] + list(RiskAssessment.SOURCE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_routine = forms.ChoiceField(
        choices=[('', 'همه'), ('true', 'روتین'), ('false', 'غیر روتین')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    corrective_action_required = forms.ChoiceField(
        choices=[('', 'همه'), ('true', 'دارد'), ('false', 'ندارد')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="نیاز به اقدام اصلاحی"
    )
