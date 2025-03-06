from django import forms
from .models import FireReport
from shift_manager.models import SHIFT_CHOICES
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger('fire_reports')

User = get_user_model()

class FireReportForm(forms.ModelForm):
    # فیلدهای چک‌باکس برای نمایش/مخفی کردن توضیحات
    show_horn_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_hose_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_monitor_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_extinguisher_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_equipment_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_foam_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_water_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_tire_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_brake_description = forms.BooleanField(required=False, label='افزودن توضیحات')
    show_lighting_description = forms.BooleanField(required=False, label='افزودن توضیحات')

    class Meta:
        model = FireReport
        fields = [
            'shift', 'shift_operator', 'firefighter',
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
            'incident_dispatch_count', 'personal_incident_count',
            'equipment_incident_count', 'fire_incident_count',
            'additional_notes'
        ]
        widgets = {
            'shift': forms.Select(attrs={'class': 'form-select form-select-solid'}),
            'shift_operator': forms.HiddenInput(),
            'firefighter': forms.HiddenInput(),
            'horn_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'hose_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'monitor_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'extinguisher_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'equipment_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'foam_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'water_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'tire_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'brake_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'lighting_status': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'horn_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'hose_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'monitor_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'extinguisher_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'equipment_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'foam_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'water_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'tire_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'brake_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'lighting_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control form-control-solid description-field',
                'style': 'display: none;',
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
            'incident_dispatch_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0',
                'placeholder': 'تعداد را وارد کنید'
            }),
            'personal_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0',
                'placeholder': 'تعداد را وارد کنید'
            }),
            'equipment_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0',
                'placeholder': 'تعداد را وارد کنید'
            }),
            'fire_incident_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'min': '0',
                'value': '0',
                'placeholder': 'تعداد را وارد کنید'
            }),
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control form-control-solid',
                'rows': 4,
                'placeholder': 'توضیحات تکمیلی خود را وارد کنید...'
            }),
        }
        labels = {
            'shift': 'شیفت کاری',
            'horn_status': 'وضعیت بوق و چراغ گردان',
            'hose_status': 'وضعیت شیلنگ‌ها و اتصالات',
            'monitor_status': 'وضعیت مانیتور',
            'extinguisher_status': 'وضعیت خاموش‌کننده‌های دستی',
            'equipment_status': 'وضعیت تجهیزات آتش‌نشانی',
            'foam_status': 'وضعیت پودر و فوم',
            'water_status': 'وضعیت آب',
            'tire_status': 'وضعیت لاستیک‌ها',
            'brake_status': 'وضعیت سیستم ترمز',
            'lighting_status': 'وضعیت سیستم روشنایی',
            'incident_dispatch_count': 'تعداد اعزام به محل حادثه',
            'personal_incident_count': 'تعداد حوادث فردی',
            'equipment_incident_count': 'تعداد حوادث تجهیزاتی',
            'fire_incident_count': 'تعداد حوادث آتش‌سوزی',
            'additional_notes': 'توضیحات تکمیلی'
        }
        help_texts = {
            'horn_status': 'وضعیت بوق و چراغ گردان خودرو را مشخص کنید',
            'hose_status': 'وضعیت شیلنگ‌ها و اتصالات را مشخص کنید',
            'monitor_status': 'وضعیت مانیتور را مشخص کنید',
            'extinguisher_status': 'وضعیت خاموش‌کننده‌های دستی را مشخص کنید',
            'equipment_status': 'وضعیت تجهیزات آتش‌نشانی را مشخص کنید',
            'foam_status': 'وضعیت پودر و فوم را مشخص کنید',
            'water_status': 'وضعیت آب را مشخص کنید',
            'tire_status': 'وضعیت لاستیک‌ها را مشخص کنید',
            'brake_status': 'وضعیت سیستم ترمز را مشخص کنید',
            'lighting_status': 'وضعیت سیستم روشنایی را مشخص کنید',
            'incident_dispatch_count': 'تعداد دفعاتی که به محل حادثه اعزام شده‌اید را وارد کنید',
            'personal_incident_count': 'تعداد حوادث فردی رخ داده را وارد کنید',
            'equipment_incident_count': 'تعداد حوادث تجهیزاتی رخ داده را وارد کنید',
            'fire_incident_count': 'تعداد حوادث آتش‌سوزی رخ داده را وارد کنید',
            'additional_notes': 'هر گونه توضیحات تکمیلی را در این قسمت وارد کنید'
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
        
        logger.info(f"Form fields: {self.fields.keys()}")
        logger.info(f"Initial values: shift_operator={self.fields['shift_operator'].initial}, firefighter={self.fields['firefighter'].initial}")

    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"Cleaned data: {cleaned_data}")
        return cleaned_data

    def is_valid(self):
        is_valid = super().is_valid()
        if not is_valid:
            logger.error(f"Form validation errors: {self.errors}")
        return is_valid