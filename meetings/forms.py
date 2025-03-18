from django import forms
from django.contrib.auth.models import User
from .models import Meeting
from django.utils.translation import gettext_lazy as _
from django_jalali.forms.widgets import jDateInput
# برای فرم های معمولی
# from django_jalali.forms.widgets import jDateInput
# برای فرم های ادمین
# from jalali_date.widgets import AdminJalaliDateWidget

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

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(
                _('زمان پایان جلسه باید بعد از زمان شروع باشد.')
            )

        return cleaned_data 