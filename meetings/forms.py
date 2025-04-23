from django import forms
from django.contrib.auth.models import User
from .models import Meeting
from django.utils.translation import gettext_lazy as _
from django_jalali.forms.widgets import jDateInput
from accounts.models import UserProfile
import jdatetime
import re
import logging

logger = logging.getLogger(__name__)

def convert_persian_to_english(text):
    persian_numbers = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    for persian, english in persian_numbers.items():
        text = text.replace(persian, english)
    return text

class MeetingForm(forms.ModelForm):
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label='شرکت‌کنندگان'
    )
    manual_numbers = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        required=False,
        label='شماره‌های دستی'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تغییر نمایش شرکت‌کنندگان
        self.fields['participants'].queryset = User.objects.all()
        self.fields['participants'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        try:
            profile = UserProfile.objects.get(user=obj)
            return f"{obj.get_full_name()} - {profile.personnel_code}"
        except UserProfile.DoesNotExist:
            return obj.get_full_name() or obj.username

    class Meta:
        model = Meeting
        fields = ['title', 'date', 'start_time', 'end_time', 'location', 'description', 'participants', 'manual_numbers', 'notify_transport_coordinator']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان جلسه را وارد کنید',
                'data-bs-toggle': 'tooltip',
                'title': 'عنوان جلسه را وارد کنید'
            }),
            'date': jDateInput(attrs={
                'class': 'form-control persian-date-picker',
                'placeholder': 'تاریخ جلسه را انتخاب کنید',
                'data-bs-toggle': 'tooltip',
                'title': 'برای انتخاب تاریخ کلیک کنید'
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'data-bs-toggle': 'tooltip',
                'title': 'زمان شروع جلسه را انتخاب کنید'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'data-bs-toggle': 'tooltip',
                'title': 'زمان پایان جلسه را انتخاب کنید'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مکان جلسه را وارد کنید',
                'data-bs-toggle': 'tooltip',
                'title': 'مکان جلسه را وارد کنید'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات جلسه را وارد کنید',
                'data-bs-toggle': 'tooltip',
                'title': 'توضیحات جلسه را وارد کنید'
            }),
            'participants': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-bs-toggle': 'tooltip',
                'title': 'شرکت‌کنندگان جلسه را انتخاب کنید'
            }),
            'manual_numbers': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'هر شماره را در یک خط وارد کنید',
                'data-bs-toggle': 'tooltip',
                'title': 'شماره‌های دستی را وارد کنید'
            }),
            'notify_transport_coordinator': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-bs-toggle': 'tooltip',
                'title': 'در صورت نیاز به هماهنگی حمل و نقل این گزینه را فعال کنید'
            })
        }
        labels = {
            'title': 'عنوان جلسه',
            'date': 'تاریخ',
            'start_time': 'زمان شروع',
            'end_time': 'زمان پایان',
            'location': 'مکان',
            'description': 'توضیحات',
            'notify_transport_coordinator': 'اعلام به هماهنگ‌کننده حمل و نقل',
        } 

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if isinstance(date, str):
            try:
                # تبدیل اعداد فارسی به انگلیسی
                date = convert_persian_to_english(date)
                
                # بررسی فرمت تاریخ
                if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
                    raise forms.ValidationError('فرمت تاریخ باید به صورت YYYY-MM-DD باشد.')
                
                # بررسی معتبر بودن تاریخ شمسی
                year, month, day = map(int, date.split('-'))
                
                # بررسی معتبر بودن تاریخ شمسی
                if not (1 <= month <= 12 and 1 <= day <= 31):
                    raise forms.ValidationError('تاریخ وارد شده معتبر نیست.')
                
                try:
                    # بررسی معتبر بودن تاریخ شمسی
                    jdatetime.date(year, month, day)
                    return date  # برگرداندن تاریخ شمسی
                except ValueError as e:
                    logger.error(f"Error validating Persian date: {str(e)}")
                    raise forms.ValidationError('تاریخ شمسی وارد شده معتبر نیست.')
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error processing date: {str(e)}")
                raise forms.ValidationError('لطفاً یک تاریخ معتبر وارد کنید.')
        return date

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                _('زمان پایان جلسه باید بعد از زمان شروع باشد.')
            )

        return cleaned_data 