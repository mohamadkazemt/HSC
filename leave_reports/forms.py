# app/forms.py
from django import forms
from .models import ShiftReport


class ShiftReportForm(forms.ModelForm):
    class Meta:
        model = ShiftReport
        fields = ['leave_type', 'user', 'shift_date', 'leave_hours', 'start_time', 'end_time', 'status']
        widgets = {
            'shift_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if leave_type == 'hourly' and (not start_time or not end_time):
            raise forms.ValidationError('برای مرخصی ساعتی باید ساعت شروع و پایان وارد شود.')

        if leave_type != 'hourly' and (start_time or end_time):
            raise forms.ValidationError('برای نوع مرخصی غیر ساعتی، ساعت شروع و پایان وارد نمی‌شود.')

        return cleaned_data
