from django import forms

from .models import Location, Anomalytype, Anomaly


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ('name',)
        labels = {
            'name': 'نام محل',
        }


class AnomalytypeForm(forms.ModelForm):
    class Meta:
        model = Anomalytype
        fields = ('type', 'description')



class AnomalyForm(forms.ModelForm):
    class Meta:
        model = Anomaly
        fields = ('location', 'anomalytype', 'created_by', 'followup', 'description')
        labels = {
            'location': 'محل ناهنجاری',
            'anomalytype': 'نوع ناهنجاری',
            'created_by': 'ایجاد کننده',
            'followup': 'پیگیری',
            'description': 'شرح',
        }
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'placeholder': 'عنوان'}),
            'anomalytype': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'created_by': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'followup': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 3, 'placeholder': 'نوع جزییات'}),
        }
