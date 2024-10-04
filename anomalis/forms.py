from django import forms
from taggit.models import Tag

from .models import Anomaly, Tags
from django_select2.forms import Select2TagWidget




class AnomalyForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tags.objects.all(),
        widget=Select2TagWidget(attrs={'class': 'form-control form-control-solid', 'data-tags': 'true', 'data-control': 'select2'}),
        required=False
    )

    class Meta:
        model = Anomaly
        fields = ('location', 'anomalytype', 'created_by', 'followup', 'description', 'action', 'correctiveaction', 'tag')
        labels = {
            'location': 'محل ناهنجاری',
            'anomalytype': 'نوع ناهنجاری',
            'created_by': 'ایجاد کننده',
            'followup': 'پیگیری',
            'description': 'شرح',
            'action': 'وضعیت',
            'correctiveaction': 'اقدامات اصلاحی',
            'tag': 'برچسب'
        }
        widgets = {
            'location': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'anomalytype': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'created_by': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'followup': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 3, 'placeholder': 'یاداشت افسر ایمنی'}),
            'action': forms.CheckboxInput(attrs={'class': 'form-check-input form-check-solid'}),
            'correctiveaction': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
        }





