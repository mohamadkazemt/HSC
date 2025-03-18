from django import forms
from django.contrib.auth.models import User
from .models import Meeting

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
        fields = ['title', 'date', 'time', 'participants', 'manual_numbers', 'notify_transport_coordinator']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notify_transport_coordinator': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': 'عنوان جلسه',
            'date': 'تاریخ',
            'time': 'ساعت',
            'notify_transport_coordinator': 'اعلام به هماهنگ‌کننده حمل و نقل',
        } 