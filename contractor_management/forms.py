# forms.py
from django import forms
from .models import Report, Vehicle, Contractor
from django.core.exceptions import ValidationError
from django.forms import Select
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget







class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['vehicle', 'status', 'stop_start_time', 'stop_end_time', 'description'] # contractor حذف شد
        widgets = {
            'stop_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'stop_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control vehicle-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)

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
        return cleaned_data

class ReportFilterForm(forms.Form):
    start_date = forms.CharField(
        required=False,
        widget=AdminJalaliDateWidget(
            attrs={'class': 'form-control jalali_date-date', 'placeholder': 'تاریخ شروع'}
        )
    )
    end_date = forms.CharField(
        required=False,
        widget=AdminJalaliDateWidget(
            attrs={'class': 'form-control jalali_date-date', 'placeholder': 'تاریخ پایان'}
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