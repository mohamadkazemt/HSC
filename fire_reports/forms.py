from django import forms
from django.forms import inlineformset_factory
from .models import FireReport, VehicleStatusReport
from django.contrib.auth import get_user_model
from BaseInfo.models import EmergencyVehicle
from contractor_management.models import Vehicle as ContractorVehicle
import logging

logger = logging.getLogger('fire_reports')
User = get_user_model()

class FireReportForm(forms.ModelForm):
    firefighter = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            'class': 'select2-field w-full',
            'data-placeholder': 'جستجو بر اساس نام یا کد پرسنلی'
        }),
        label='آتش‌نشان'
    )
    shift_operator = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={
            'class': 'select2-field w-full',
            'data-placeholder': 'جستجو بر اساس نام یا کد پرسنلی'
        }),
        label='اپراتور شیفت'
    )
    class Meta:
        model = FireReport
        fields = [
            'shift', 'shift_operator', 'firefighter',
            'incident_dispatch_count', 'personal_incident_count',
            'equipment_incident_count', 'fire_incident_count',
            'additional_notes'
        ]
        widgets = {
            'shift': forms.Select(attrs={'class': 'select2-field w-full', 'data-placeholder': 'شیفت را انتخاب کنید'}),
            'incident_dispatch_count': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'min': '0', 'value': '0'}),
            'personal_incident_count': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'min': '0', 'value': '0'}),
            'equipment_incident_count': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'min': '0', 'value': '0'}),
            'fire_incident_count': forms.NumberInput(attrs={'class': 'form-control form-control-solid', 'min': '0', 'value': '0'}),
            'additional_notes': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 4, 'placeholder': 'توضیحات تکمیلی...'}),
        }
    def __init__(self, *args, **kwargs):
        firefighter_qs = kwargs.pop('firefighter_queryset', None)
        operator_qs = kwargs.pop('operator_queryset', None)
        super().__init__(*args, **kwargs)
        if firefighter_qs is not None:
            self.fields['firefighter'].queryset = firefighter_qs
        if operator_qs is not None:
            self.fields['shift_operator'].queryset = operator_qs
        self.fields['firefighter'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.userprofile.personnel_code})"
        self.fields['shift_operator'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.userprofile.personnel_code})"

class VehicleStatusReportForm(forms.ModelForm):
    VEHICLE_SOURCE_CHOICES = [
        ('company', 'شرکتی'),
        ('contractor', 'پیمانکار'),
    ]
    vehicle_source = forms.ChoiceField(
        choices=VEHICLE_SOURCE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='منبع خودرو'
    )

    class Meta:
        model = VehicleStatusReport
        fields = [
            'vehicle_source', 'company_vehicle', 'contractor_vehicle',
            'horn_status', 'horn_description',
            'hose_status', 'hose_description',
            'monitor_status', 'monitor_description',
            'extinguisher_status', 'extinguisher_description',
            'equipment_status', 'equipment_description',
            'foam_status', 'foam_description',
            'water_status', 'water_description',
            'tire_status', 'tire_description',
            'brake_status', 'brake_description',
            'lighting_status', 'lighting_description',
        ]
        widgets = {
            'company_vehicle': forms.Select(attrs={
                'class': 'select2-field w-full py-2.5 px-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors',
                'data-placeholder': 'خودروی شرکت را انتخاب کنید'
            }),
            'contractor_vehicle': forms.Select(attrs={
                'class': 'select2-field w-full py-2.5 px-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors',
                'data-placeholder': 'خودروی پیمانکار را انتخاب کنید'
            }),
            # Status fields with RadioSelect
            'horn_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'hose_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'monitor_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'extinguisher_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'equipment_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'foam_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'water_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'tire_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'brake_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            'lighting_status': forms.RadioSelect(attrs={'class': 'status-radio'}),
            # Description textareas
            'horn_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'hose_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'monitor_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'extinguisher_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'equipment_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'foam_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'water_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'tire_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'brake_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
            'lighting_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'توضیحات...',
                'class': 'w-full py-2 px-3 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors resize-none'
            }),
        }
    def __init__(self, *args, **kwargs):
        company_vehicles_qs = kwargs.pop('company_vehicles_queryset', None)
        contractor_vehicles_qs = kwargs.pop('contractor_vehicles_queryset', None)
        super().__init__(*args, **kwargs)
        if company_vehicles_qs is not None:
            self.fields['company_vehicle'].queryset = company_vehicles_qs
        if contractor_vehicles_qs is not None:
            self.fields['contractor_vehicle'].queryset = contractor_vehicles_qs

VehicleStatusFormSet = inlineformset_factory(
    FireReport,
    VehicleStatusReport,
    form=VehicleStatusReportForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
