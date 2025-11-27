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
            'risk_source',
            'risk_source_other',
            'activity_component',
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
        
        # تنظیم فیلدهای اختیاری
        self.fields['people_at_risk'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        errors = {}
        
        # اگر منشا "سایر" انتخاب شده، باید توضیح داده شود
        if cleaned_data.get('risk_source') == 'other' and not cleaned_data.get('risk_source_other'):
            errors['risk_source_other'] = 'لطفاً منشا را توضیح دهید.'
        
        # اگر الزام قانونی وجود دارد، باید شرح داده شود
        if cleaned_data.get('has_legal_requirement'):
            if not cleaned_data.get('legal_requirement_desc'):
                errors['legal_requirement_desc'] = 'لطفاً الزام قانونی را شرح دهید.'
            if cleaned_data.get('is_legal_compliant') is None:
                errors['is_legal_compliant'] = 'لطفاً وضعیت رعایت الزام قانونی را مشخص کنید.'
        
        # اگر نیاز به اقدام اصلاحی است، فیلدهای مربوطه باید پر شوند
        if cleaned_data.get('corrective_action_required'):
            if not cleaned_data.get('action_deadline'):
                errors['action_deadline'] = 'لطفاً مهلت اقدام را مشخص کنید.'
            if not cleaned_data.get('responsible_person'):
                errors['responsible_person'] = 'لطفاً مسئول اجرا را مشخص کنید.'
            
            # بررسی منطقی بودن تاریخ‌ها
            action_date = cleaned_data.get('action_date')
            action_deadline = cleaned_data.get('action_deadline')
            if action_date and action_deadline:
                if action_date > action_deadline:
                    errors['action_deadline'] = 'مهلت اقدام نمی‌تواند قبل از تاریخ اقدام باشد.'
        
        # اگر MUE فعال است، باید کد آن وارد شود
        if cleaned_data.get('is_mue') and not cleaned_data.get('mue_code'):
            errors['mue_code'] = 'لطفاً کد MUE را وارد کنید.'
        
        # اگر شرایط اضطراری فعال است، باید کد آن وارد شود
        if cleaned_data.get('is_emergency') and not cleaned_data.get('emergency_code'):
            errors['emergency_code'] = 'لطفاً کد شرایط اضطراری را وارد کنید.'
        
        # بررسی وجود حداقل یکی از فیلدهای اصلی
        if not cleaned_data.get('activity_component'):
            errors['activity_component'] = 'این فیلد الزامی است.'
        
        if not cleaned_data.get('hazard'):
            errors['hazard'] = 'لطفاً نوع خطر را انتخاب کنید.'
        
        if not cleaned_data.get('potential_event'):
            errors['potential_event'] = 'لطفاً رویداد احتمالی را مشخص کنید.'
        
        if not cleaned_data.get('causes'):
            errors['causes'] = 'لطفاً علل احتمالی وقوع را شرح دهید.'
        
        if not cleaned_data.get('consequence'):
            errors['consequence'] = 'لطفاً نوع پیامد را انتخاب کنید.'
        
        if not cleaned_data.get('existing_controls'):
            errors['existing_controls'] = 'لطفاً کنترل‌های موجود را شرح دهید.'
        
        if not cleaned_data.get('control_failure_causes'):
            errors['control_failure_causes'] = 'لطفاً علل احتمالی شکست کنترل‌ها را شرح دهید.'
        
        # بررسی probability و severity
        probability = cleaned_data.get('probability')
        severity = cleaned_data.get('severity')
        
        if not probability:
            errors['probability'] = 'لطفاً احتمال وقوع را انتخاب کنید.'
        elif probability not in [1, 2, 3, 4, 5]:
            errors['probability'] = 'مقدار احتمال باید بین 1 تا 5 باشد.'
        
        if not severity:
            errors['severity'] = 'لطفاً شدت پیامد را انتخاب کنید.'
        elif severity not in [1, 2, 3, 4, 5]:
            errors['severity'] = 'مقدار شدت باید بین 1 تا 5 باشد.'
        
        # اگر خطا داریم، raise ValidationError
        if errors:
            raise ValidationError(errors)
        
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
        errors = {}
        
        # هر سه فیلد باید با هم پر شوند
        date = cleaned_data.get('re_evaluation_date')
        prob = cleaned_data.get('residual_probability')
        sev = cleaned_data.get('residual_severity')
        
        if any([date, prob, sev]) and not all([date, prob, sev]):
            if not date:
                errors['re_evaluation_date'] = 'تاریخ ارزیابی مجدد الزامی است.'
            if not prob:
                errors['residual_probability'] = 'احتمال باقی‌مانده الزامی است.'
            if not sev:
                errors['residual_severity'] = 'شدت باقی‌مانده الزامی است.'
        
        # بررسی محدوده مقادیر
        if prob and prob not in [1, 2, 3, 4, 5]:
            errors['residual_probability'] = 'مقدار احتمال باید بین 1 تا 5 باشد.'
        
        if sev and sev not in [1, 2, 3, 4, 5]:
            errors['residual_severity'] = 'مقدار شدت باید بین 1 تا 5 باشد.'
        
        # بررسی تاریخ منطقی
        if date:
            from django.utils import timezone
            if date > timezone.now().date():
                errors['re_evaluation_date'] = 'تاریخ ارزیابی مجدد نمی‌تواند در آینده باشد.'
        
        if errors:
            raise ValidationError(errors)
        
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


class ExcelImportForm(forms.Form):
    """فرم آپلود فایل Excel برای import ریسک‌ها"""
    excel_file = forms.FileField(
        label="فایل Excel",
        help_text="فقط فایل‌های .xlsx پذیرفته می‌شود",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx',
        })
    )
    
    def clean_excel_file(self):
        file = self.cleaned_data.get('excel_file')
        if file:
            if not file.name.endswith('.xlsx'):
                raise ValidationError('فقط فایل‌های Excel (.xlsx) پذیرفته می‌شود.')
            if file.size > 10 * 1024 * 1024:  # 10 MB
                raise ValidationError('حجم فایل نباید بیشتر از 10 مگابایت باشد.')
        return file