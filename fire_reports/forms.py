from django import forms
from django.forms import inlineformset_factory
from .models import FireReport, VehicleStatusReport
from shift_manager.models import SHIFT_CHOICES
from django.contrib.auth import get_user_model
from BaseInfo.models import EmergencyVehicle
from contractor_management.models import Vehicle as ContractorVehicle
import logging

logger = logging.getLogger('fire_reports')

User = get_user_model()

class VehicleStatusReportForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('suitable', 'مناسب'),
        ('unsuitable', 'نامناسب'),
    ]

    vehicle_source = forms.ChoiceField(
        choices=VehicleStatusReport.VEHICLE_SOURCE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='company',
        label='نوع خودرو'
    )

    horn_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت بوق و چراغ گردان'
    )
    hose_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت شیلنگ‌ها و اتصالات'
    )
    monitor_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت مانیتور'
    )
    extinguisher_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت خاموش‌کننده‌های دستی'
    )
    equipment_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت تجهیزات آتش‌نشانی'
    )
    foam_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت پودر و فوم خودرو'
    )
    water_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت آب'
    )
    tire_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت لاستیک‌ها'
    )
    brake_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت سیستم ترمز خودرو'
    )
    lighting_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت سیستم روشنایی'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # فیلتر کردن خودروهای امدادی فعال
        self.fields['company_vehicle'].queryset = EmergencyVehicle.objects.filter(
            status='active',
            vehicle_type='fire_truck'
        )
        
        # فیلتر کردن خودروهای پیمانکار آتش‌نشانی
        self.fields['contractor_vehicle'].queryset = ContractorVehicle.objects.filter(
            contractor__company_name__icontains='آتش نشانی'
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
            'vehicle_source': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'company_vehicle': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'contractor_vehicle': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'horn_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'hose_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'monitor_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'extinguisher_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'equipment_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'foam_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'water_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'tire_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'brake_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'lighting_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
        }

class FireReportForm(forms.ModelForm):
    class Meta:
        model = FireReport
        fields = [
            'shift', 'shift_operator', 'firefighter',
            'incident_dispatch_count', 'personal_incident_count',
            'equipment_incident_count', 'fire_incident_count',
            'additional_notes'
        ]
        widgets = {
            'shift': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'shift_operator': forms.HiddenInput(),
            'firefighter': forms.HiddenInput(),
            'incident_dispatch_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0'
            }),
            'personal_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0'
            }),
            'equipment_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0'
            }),
            'fire_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control form-control-solid',
                'rows': 4,
                'placeholder': 'توضیحات تکمیلی خود را وارد کنید...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing FireReportForm")
        
        # تنظیم مقادیر اولیه برای فیلدهای مخفی
        if 'initial' in kwargs:
            if 'shift_operator' in kwargs['initial']:
                self.fields['shift_operator'].initial = kwargs['initial']['shift_operator']
            if 'firefighter' in kwargs['initial']:
                self.fields['firefighter'].initial = kwargs['initial']['firefighter']
        
        # تنظیم مقادیر پیش‌فرض برای فیلدهای تعداد حوادث
        if not self.instance.pk:  # فقط برای فرم ایجاد گزارش جدید
            self.fields['incident_dispatch_count'].initial = 0
            self.fields['personal_incident_count'].initial = 0
            self.fields['equipment_incident_count'].initial = 0
            self.fields['fire_incident_count'].initial = 0

# ایجاد Formset برای گزارش وضعیت خودروها
VehicleStatusFormSet = inlineformset_factory(
    FireReport,
    VehicleStatusReport,
    form=VehicleStatusReportForm,
    extra=2,  # تعداد فرم‌های خالی افزایش یافت به 3
    can_delete=True,  # امکان حذف گزارش خودرو
    min_num=1,  # حداقل تعداد خودرو
    validate_min=True,  # اجباری بودن حداقل تعداد
)