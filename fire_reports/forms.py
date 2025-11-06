from django import forms
from .models import FireReport
from shift_manager.models import SHIFT_CHOICES
from django.contrib.auth import get_user_model
from BaseInfo.models import EmergencyVehicle
from contractor_management.models import Vehicle as ContractorVehicle
import logging

logger = logging.getLogger('fire_reports')

User = get_user_model()

STATUS_CHOICES = [
    ('suitable', 'مناسب'),
    ('unsuitable', 'نامناسب'),
]

VEHICLE_SOURCE_CHOICES = [
    ('company', 'خودروی شرکت'),
    ('contractor', 'خودروی پیمانکار'),
]

class FireReportForm(forms.ModelForm):
    # این فیلدها برای backward compatibility هستند
    # در حالت جدید، خودروها در VehicleChecklist ذخیره می‌شوند
    vehicle_source = forms.ChoiceField(
        choices=VEHICLE_SOURCE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='company',
        label='نوع خودرو',
        required=False  # اختیاری برای پشتیبانی از چندین خودرو
    )

    # فیلدهای وضعیت تجهیزات - اختیاری برای پشتیبانی از چندین خودرو
    horn_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت بوق و چراغ گردان',
        required=False
    )
    hose_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت شیلنگ‌ها و اتصالات',
        required=False
    )
    monitor_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت مانیتور',
        required=False
    )
    extinguisher_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت خاموش‌کننده‌های دستی',
        required=False
    )
    equipment_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت تجهیزات آتش‌نشانی',
        required=False
    )
    foam_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت پودر و فوم خودرو',
        required=False
    )
    water_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت آب',
        required=False
    )
    tire_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت لاستیک‌ها',
        required=False
    )
    brake_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت سیستم ترمز خودرو',
        required=False
    )
    lighting_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='suitable',
        label='وضعیت سیستم روشنایی',
        required=False
    )

    class Meta:
        model = FireReport
        fields = [
            # اطلاعات کلی شیفت
            'shift', 'shift_operator', 'firefighter',
            # اطلاعات خودرو
            'vehicle_source', 'company_vehicle', 'contractor_vehicle',
            # وضعیت تجهیزات
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
            # گزارش حوادث
            'incident_dispatch_count', 'personal_incident_count',
            'equipment_incident_count', 'fire_incident_count',
            # سایر
            'additional_notes'
        ]
        widgets = {
            'shift': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'shift_operator': forms.HiddenInput(),
            'firefighter': forms.HiddenInput(),
            'company_vehicle': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'contractor_vehicle': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'horn_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'hose_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'monitor_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'extinguisher_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'equipment_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'foam_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'water_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'tire_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'brake_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'lighting_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
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
        
        # فیلتر کردن خودروهای امدادی فعال
        self.fields['company_vehicle'].queryset = EmergencyVehicle.objects.filter(
            status='active',
            vehicle_type='fire_truck'
        )
        
        # فیلتر کردن خودروهای پیمانکار آتش‌نشانی
        self.fields['contractor_vehicle'].queryset = ContractorVehicle.objects.filter(
            contractor__company_name__icontains='آتش نشانی'
        )
        
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

    def clean(self):
        cleaned_data = super().clean()
        vehicle_source = cleaned_data.get('vehicle_source')
        company_vehicle = cleaned_data.get('company_vehicle')
        contractor_vehicle = cleaned_data.get('contractor_vehicle')
        
        # فقط در صورتی که از فرم قدیمی استفاده شده باشد (vehicle_source وجود داشته باشد)
        # این اعتبارسنجی را انجام بده
        if vehicle_source:
            if vehicle_source == 'company' and not company_vehicle:
                raise forms.ValidationError({
                    'company_vehicle': 'برای خودروی شرکت باید یک خودروی امدادی انتخاب شود.'
                })
            elif vehicle_source == 'contractor' and not contractor_vehicle:
                raise forms.ValidationError({
                    'contractor_vehicle': 'برای خودروی پیمانکار باید یک خودرو انتخاب شود.'
                })
            
            if company_vehicle and contractor_vehicle:
                raise forms.ValidationError('نمی‌توانید همزمان خودروی شرکت و پیمانکار را انتخاب کنید.')
        
        return cleaned_data
