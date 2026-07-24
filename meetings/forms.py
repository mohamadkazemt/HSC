import re

import jdatetime
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Meeting


_DIGIT_TRANSLATION = str.maketrans(
    '۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩',
    '01234567890123456789',
)


def convert_persian_to_english(value):
    return str(value).translate(_DIGIT_TRANSLATION)


class JalaliDateField(forms.DateField):
    """Accept Gregorian dates and common YYYY/MM/DD Jalali input."""

    def to_python(self, value):
        if isinstance(value, str):
            normalized = convert_persian_to_english(value.strip()).replace('-', '/')
            match = re.fullmatch(r'(\d{4})/(\d{1,2})/(\d{1,2})', normalized)
            if match:
                year, month, day = map(int, match.groups())
                if 1300 <= year <= 1500:
                    try:
                        return jdatetime.date(year, month, day).togregorian()
                    except (TypeError, ValueError):
                        raise forms.ValidationError(
                            _('تاریخ شمسی واردشده معتبر نیست.'),
                            code='invalid',
                        )
        return super().to_python(value)


class MeetingForm(forms.ModelForm):
    date = JalaliDateField(
        label='تاریخ جلسه',
        widget=forms.TextInput(attrs={
            'class': 'form-control jalali-date',
            'placeholder': 'مثلاً ۱۴۰۵/۰۵/۱۰',
            'autocomplete': 'off',
            'inputmode': 'numeric',
        }),
    )
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        label='شرکت‌کنندگان',
    )
    manual_numbers = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'هر شماره موبایل را در یک خط وارد کنید',
            'inputmode': 'tel',
        }),
        required=False,
        label='شماره‌های موبایل خارج از سامانه',
    )

    class Meta:
        model = Meeting
        fields = [
            'title', 'date', 'start_time', 'end_time', 'location',
            'description', 'participants', 'manual_numbers',
            'notify_transport_coordinator',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موضوع جلسه',
                'maxlength': 200,
                'autocomplete': 'off',
            }),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اتاق، ساختمان یا لینک جلسه',
                'maxlength': 200,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'دستور جلسه یا توضیحات تکمیلی',
            }),
            'notify_transport_coordinator': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'title': 'عنوان جلسه',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'location': 'مکان یا لینک جلسه',
            'description': 'توضیحات',
            'notify_transport_coordinator': 'هماهنگی حمل‌ونقل لازم است',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['participants'].queryset = (
            User.objects.filter(is_active=True)
            .select_related('userprofile')
            .order_by('first_name', 'last_name', 'username')
        )
        self.fields['participants'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(user):
        name = user.get_full_name() or user.username
        profile = getattr(user, 'userprofile', None)
        personnel_code = getattr(profile, 'personnel_code', '') if profile else ''
        return f'{name} - {personnel_code}' if personnel_code else name

    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError('عنوان جلسه باید حداقل ۳ نویسه باشد.')
        return title

    def clean_manual_numbers(self):
        raw_value = self.cleaned_data.get('manual_numbers', '')
        if not raw_value:
            return ''

        normalized_numbers = []
        invalid_numbers = []
        for raw_number in re.split(r'[\n,،;]+', convert_persian_to_english(raw_value)):
            if not raw_number.strip():
                continue
            number = re.sub(r'[\s\-()]', '', raw_number.strip())
            if number.startswith('+98'):
                number = '0' + number[3:]
            elif number.startswith('0098'):
                number = '0' + number[4:]
            elif number.startswith('98') and len(number) == 12:
                number = '0' + number[2:]

            if not re.fullmatch(r'09\d{9}', number):
                invalid_numbers.append(raw_number.strip())
                continue
            if number not in normalized_numbers:
                normalized_numbers.append(number)

        if invalid_numbers:
            raise forms.ValidationError(
                'شماره موبایل نامعتبر است: %(numbers)s',
                params={'numbers': '، '.join(invalid_numbers)},
            )
        return '\n'.join(normalized_numbers)

    def clean(self):
        cleaned_data = super().clean()
        meeting_date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'ساعت پایان باید بعد از ساعت شروع باشد.')

        if meeting_date and start_time and not self.instance.pk:
            starts_at = timezone.make_aware(
                timezone.datetime.combine(meeting_date, start_time),
                timezone.get_current_timezone(),
            )
            if starts_at <= timezone.now():
                self.add_error('date', 'زمان جلسه باید در آینده باشد.')

        return cleaned_data