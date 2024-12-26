from django import forms
from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['contractor', 'vehicle', 'status', 'stop_start_time', 'stop_end_time', 'description']
        widgets = {
            'stop_start_time': forms.TimeInput(attrs={'type': 'time'}),
            'stop_end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),

        }

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
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
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
            cleaned_data['description'] = None

        elif status == 'partial':
            if not stop_start_time:
                self.add_error(None, "برای حالت کارکرد ناقص ساعت شروع توقف را وارد کنید")
            if not stop_end_time:
                self.add_error(None, "برای حالت کارکرد ناقص ساعت پایان توقف را وارد کنید")
            if not description:
                self.add_error(None, "برای حالت کارکرد ناقص توضیحات را وارد کنید")

        elif status == 'inactive':
            if not description:
                self.add_error(None, "برای حالت غیر فعال توضیحات را وارد کنید")
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
        return cleaned_data