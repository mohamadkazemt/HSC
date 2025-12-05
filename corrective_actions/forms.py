# corrective_actions/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import CorrectiveAction, ActionStep, SideEffectRisk
from accounts.models import UserProfile


class CorrectiveActionForm(forms.ModelForm):
    """فرم ایجاد و ویرایش اقدام اصلاحی/پیشگیرانه"""
    
    class Meta:
        model = CorrectiveAction
        fields = [
            'tracking_code',
            'action_type',
            'topic',
            'source',
            'description',
            'root_cause_analysis',
            'requester',
            'receiver',
            'related_incident',
            'related_risk',
            'related_anomaly',
            'effectiveness_result',
            'status',
        ]
        
        widgets = {
            'tracking_code': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'شماره اقدام را وارد کنید'
            }),
            'action_type': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'topic': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'source': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 4,
                'placeholder': 'شرح عدم انطباق را وارد کنید'
            }),
            'root_cause_analysis': forms.Textarea(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'rows': 4,
                'placeholder': 'علل ریشه‌ای عدم انطباق را وارد کنید'
            }),
            'requester': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'receiver': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'related_incident': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'related_risk': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'related_anomaly': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'effectiveness_result': forms.NullBooleanSelect(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract related_incident_id, related_risk_id and related_anomaly_id from kwargs if passed
        related_incident_id = kwargs.pop('related_incident_id', None)
        related_risk_id = kwargs.pop('related_risk_id', None)
        related_anomaly_id = kwargs.pop('related_anomaly_id', None)
        super().__init__(*args, **kwargs)
        
        # Set queryset for UserProfile fields
        self.fields['requester'].queryset = UserProfile.objects.all().select_related('user')
        self.fields['receiver'].queryset = UserProfile.objects.all().select_related('user')
        self.fields['requester'].empty_label = 'انتخاب کنید'
        self.fields['receiver'].empty_label = 'انتخاب کنید'
        
        # Set queryset for related_incident if hse_incidents app exists
        try:
            from hse_incidents.models import IncidentReport
            self.fields['related_incident'].queryset = IncidentReport.objects.all().order_by('-incident_date')
            self.fields['related_incident'].empty_label = 'انتخاب کنید'
        except ImportError:
            self.fields['related_incident'].widget = forms.HiddenInput()
        
        # Set queryset for related_risk if risk_assessment app exists
        try:
            from risk_assessment.models import RiskAssessment
            self.fields['related_risk'].queryset = RiskAssessment.objects.all().order_by('-created_at')
            self.fields['related_risk'].empty_label = 'انتخاب کنید'
        except ImportError:
            self.fields['related_risk'].widget = forms.HiddenInput()
        
        # Set queryset for related_anomaly if anomalis app exists
        try:
            from anomalis.models import Anomaly
            self.fields['related_anomaly'].queryset = Anomaly.objects.all().order_by('-created_at')
            self.fields['related_anomaly'].empty_label = 'انتخاب کنید'
        except ImportError:
            self.fields['related_anomaly'].widget = forms.HiddenInput()
        
        # Pre-fill related_incident if provided
        if related_incident_id:
            self.fields['related_incident'].initial = related_incident_id
        
        # Pre-fill related_risk if provided
        if related_risk_id:
            self.fields['related_risk'].initial = related_risk_id
        
        # Pre-fill related_anomaly if provided
        if related_anomaly_id:
            try:
                # تبدیل به integer در صورت نیاز
                anomaly_id = int(related_anomaly_id) if isinstance(related_anomaly_id, str) else related_anomaly_id
                self.fields['related_anomaly'].initial = anomaly_id
                # اگر instance وجود دارد، مقدار را مستقیماً تنظیم کن
                if not self.instance.pk:
                    self.instance.related_anomaly_id = anomaly_id
                # اگر anomaly_id از URL آمده، فیلد را required کن
                self.fields['related_anomaly'].required = True
            except (ValueError, TypeError):
                pass
        
        # Add created_at field manually (since it's auto_now_add, we can't include it in Meta.fields)
        # For new instances, it will be set automatically by auto_now_add
        # For existing instances, show it as readonly
        if self.instance and self.instance.pk:
            # Show existing date as readonly
            self.fields['created_at'] = forms.DateField(
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white jalali-date',
                    'autocomplete': 'off',
                    'readonly': True,
                }),
                label='تاریخ ثبت'
            )
            # Convert to Jalali for display
            try:
                import jdatetime
                if self.instance.created_at:
                    jalali_date = jdatetime.date.fromgregorian(date=self.instance.created_at)
                    self.fields['created_at'].initial = jalali_date.strftime('%Y/%m/%d')
            except:
                if self.instance.created_at:
                    self.fields['created_at'].initial = self.instance.created_at.strftime('%Y-%m-%d')
    
    def save(self, commit=True):
        """Override save to ensure created_at is not modified"""
        instance = super().save(commit=False)
        # Remove created_at from cleaned_data if it exists (it's readonly for existing instances)
        if 'created_at' in self.cleaned_data and self.instance and self.instance.pk:
            # Don't update created_at for existing instances
            pass
        if commit:
            instance.save()
        return instance


class ActionStepForm(forms.ModelForm):
    """فرم برای مراحل اقدام"""
    
    class Meta:
        model = ActionStep
        fields = [
            'description',
            'responsible',
            'deadline',
            'completion_date',
            'is_done',
        ]
        
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'شرح اقدام را وارد کنید'
            }),
            'responsible': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white'
            }),
            'deadline': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white jalali-date',
                'autocomplete': 'off'
            }),
            'completion_date': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white jalali-date',
                'autocomplete': 'off'
            }),
            'is_done': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['responsible'].queryset = UserProfile.objects.all().select_related('user')
        self.fields['responsible'].empty_label = 'انتخاب کنید'


class SideEffectRiskForm(forms.ModelForm):
    """فرم برای ریسک‌های ناشی از اقدام"""
    
    class Meta:
        model = SideEffectRisk
        fields = [
            'hazard',
            'event',
            'consequence',
            'control_measure',
        ]
        
        widgets = {
            'hazard': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'خطر / جنبه را وارد کنید'
            }),
            'event': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'رویداد را وارد کنید'
            }),
            'consequence': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'پیامد را وارد کنید'
            }),
            'control_measure': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'اقدام کنترلی پیشنهادی را وارد کنید'
            }),
        }


# Formsets using inlineformset_factory
ActionStepFormSet = inlineformset_factory(
    CorrectiveAction,
    ActionStep,
    form=ActionStepForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

SideEffectRiskFormSet = inlineformset_factory(
    CorrectiveAction,
    SideEffectRisk,
    form=SideEffectRiskForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)

