# forms.py
from django import forms
from .models import Report, Vehicle, Contractor, Employee
from django.core.exceptions import ValidationError
from django.forms import Select
# Persian date imports removed
import re
import logging
from django.utils.translation import gettext_lazy as _

# تنظیم لاگر
logger = logging.getLogger(__name__)

def persian_to_english_numbers(string):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return string.translate(translation_table)

# تعریف گزینه‌های شیفت
SHIFT_CHOICES = [
    ('', '-- انتخاب شیفت --'),
    ('روزکار اول', 'روزکار اول'),
    ('روزکار دوم', 'روزکار دوم'),
    ('عصرکار اول', 'عصرکار اول'),
    ('عصرکار دوم', 'عصرکار دوم'),
    ('شب کار اول', 'شب کار اول'),
    ('شب کار دوم', 'شب کار دوم'),
    ('OFF اول', 'OFF اول'),
    ('OFF دوم', 'OFF دوم'),
]

class ReportForm(forms.ModelForm):
    report_date = forms.CharField(
        label='تاریخ گزارش',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_report_date',
            'name': 'report_date',
            'placeholder': 'مثال: 1402/12/29',
            'autocomplete': 'off',
            'required': True
        }),
        required=True,
        error_messages={
            'required': 'لطفاً تاریخ را وارد کنید',
            'invalid': 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)'
        }
    )
    shift = forms.ChoiceField(
        label='شیفت',
        choices=SHIFT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # اجازه می‌دهد که شیفت به صورت خودکار تنظیم شود
    )

    class Meta:
        model = Report
        fields = ['vehicle', 'status', 'stop_start_time', 'stop_end_time', 'description', 'report_date']
        widgets = {
            'stop_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'stop_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control vehicle-select'}),
        }

    def clean_report_date(self):
        """اعتبارسنجی تاریخ - Persian date validation removed"""
        date_str = self.cleaned_data.get('report_date')
        
        if not date_str:
            raise ValidationError('لطفاً تاریخ را وارد کنید')
        
        # Simple validation - Persian date processing removed
        return date_str

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        logger.info(f"مقادیر اولیه فرم: {args}")

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, dict):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})

        self.fields['stop_start_time'].required = False
        self.fields['stop_end_time'].required = False
        self.fields['description'].required = False

        # حالت اولیه: نمایش *همه* خودروها
        self.fields['vehicle'].queryset = Vehicle.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"داده‌های تمیز شده در clean: {cleaned_data}")
        
        status = cleaned_data.get('status')
        stop_start_time = cleaned_data.get('stop_start_time')
        stop_end_time = cleaned_data.get('stop_end_time')
        description = cleaned_data.get('description')

        if status == 'full':
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
            cleaned_data['description'] = None

        elif status == 'partial':
            if not stop_start_time:
                self.add_error('stop_start_time', "لطفاً ساعت شروع توقف را وارد کنید.")
            if not stop_end_time:
                self.add_error('stop_end_time', "لطفاً ساعت پایان توقف را وارد کنید.")
            if not description:
                self.add_error('description', "لطفاً توضیحات را وارد کنید.")

        elif status == 'inactive':
            if not description:
                self.add_error('description', "لطفاً توضیحات را برای حالت غیر فعال وارد کنید.")
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
        
        logger.info(f"داده‌های نهایی پس از اعتبارسنجی: {cleaned_data}")
        return cleaned_data

class ReportFilterForm(forms.Form):
    start_date = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'تاریخ شروع'}
        )
    )
    end_date = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'تاریخ پایان'}
        )
    )
    contractor = forms.ModelChoiceField(
        queryset=Contractor.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="همه پیمانکاران"
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="همه خودروها"
    )
    shift = forms.ChoiceField(
        choices=[('', 'همه شیفت‌ها'), ('صبح', 'صبح'), ('عصر', 'عصر'), ('شب', 'شب')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ChoiceField(
        choices=[('', 'همه گروه‌ها'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )