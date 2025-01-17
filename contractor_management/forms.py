from django import forms
from .models import Report
from django.core.exceptions import ValidationError
from django.forms import Select
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['contractor', 'vehicle', 'status', 'stop_start_time', 'stop_end_time', 'description']
        widgets = {
            'stop_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'stop_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not isinstance(field.widget.attrs, dict):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})

        # Custom requirements for optional fields
        self.fields['contractor'].widget.attrs.update({'class': 'form-control'})
        self.fields['vehicle'].widget.attrs.update({'class': 'form-control'})
        self.fields['stop_start_time'].required = False
        self.fields['stop_end_time'].required = False
        self.fields['description'].required = False


    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        stop_start_time = cleaned_data.get('stop_start_time')
        stop_end_time = cleaned_data.get('stop_end_time')
        description = cleaned_data.get('description')

        if status == 'full':
            # برای حالت کارکرد کامل نیازی به این فیلدها نیست
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
            cleaned_data['description'] = None

        elif status == 'partial':
            # اعتبارسنجی برای حالت کارکرد ناقص
            if not stop_start_time:
                self.add_error('stop_start_time', "لطفاً ساعت شروع توقف را وارد کنید.")
            if not stop_end_time:
                self.add_error('stop_end_time', "لطفاً ساعت پایان توقف را وارد کنید.")
            if not description:
                self.add_error('description', "لطفاً توضیحات را وارد کنید.")

        elif status == 'inactive':
            # اعتبارسنجی برای حالت غیر فعال
            if not description:
                self.add_error('description', "لطفاً توضیحات را برای حالت غیر فعال وارد کنید.")
            # فیلدهای غیر ضروری را خالی کنید
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
        return cleaned_data



class ReportFilterForm(forms.Form):
    start_date = JalaliDateField(
        label="تاریخ شروع",
        widget=AdminJalaliDateWidget(),
        required=False
    )
    end_date = JalaliDateField(
        label="تاریخ پایان",
        widget=AdminJalaliDateWidget(),
        required=False
    )
    contractor = forms.ModelChoiceField(
        queryset=Report.objects.values_list('contractor__company_name',flat=True).distinct(),
        label="پیمانکار",
        widget=Select(attrs={'class': 'form-control django-select2'}),
        required=False,
        empty_label='همه پیمانکاران'
    )
    vehicle = forms.ModelChoiceField(
        queryset=Report.objects.values_list('vehicle__license_plate',flat=True).distinct(),
        label="خودرو",
        widget=Select(attrs={'class': 'form-control django-select2'}),
        required=False,
        empty_label='همه خودروها'
    )
    shift = forms.CharField(
        label="شیفت",
        widget=forms.Select(choices=[('', 'همه شیفت ها'), ('روزکار اول', 'روزکار اول'), ('روزکار دوم', 'روزکار دوم'), ('عصرکار اول', 'عصرکار اول'),
                                     ('عصرکار دوم', 'عصرکار دوم'), ('شب کار اول', 'شب کار اول'), ('شب کار دوم', 'شب کار دوم'),
                                     ('OFF اول', 'OFF دوم'), ('OFF دوم', 'OFF دوم')],
                            attrs={'class': 'form-control django-select2'}),
        required=False,
    )

    group = forms.CharField(
        label="گروه",
        widget=forms.Select(choices=[('', 'همه گروه ها'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
                            attrs = {'class': 'form-control django-select2'}),


    required=False,
)