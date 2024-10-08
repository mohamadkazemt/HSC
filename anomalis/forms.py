from django import forms
from .models import Anomaly, Priority
from django_select2.forms import Select2TagWidget




class AnomalyForm(forms.ModelForm):


    class Meta:
        model = Anomaly
        fields = ('location', 'anomalytype', 'followup', 'description', 'action', 'correctiveaction', 'priority', 'image')
        labels = {
            'location': 'محل آنومالی ',
            'anomalytype': 'نوع آنومالی',
            'followup': 'پیگیری',
            'description': 'شرح',
            'action': 'وضعیت',
            'correctiveaction': 'اقدامات اصلاحی',
            'priority': 'اولویت',
            'image': 'تصویر آنومالی'
        }
        widgets = {
            'location': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'anomalytype': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'followup': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 3, 'placeholder': 'یاداشت افسر ایمنی'}),
            'action': forms.CheckboxInput(attrs={'class': 'form-check-input form-check-solid'}),
            'correctiveaction': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'priority': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-solid'}),

        }
