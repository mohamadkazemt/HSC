from django import forms
from .models import Anomaly, Priority
from django_select2.forms import Select2TagWidget
from .models import Comments



class AnomalyForm(forms.ModelForm):


    class Meta:
        model = Anomaly
        fields = ('location', 'anomalytype', 'followup', 'description', 'action', 'correctiveaction', 'priority', 'image', 'anomalydescription', 'hse_type')
        labels = {
            'location': 'محل آنومالی ',
            'anomalytype': 'نوع آنومالی',
            'followup': 'پیگیری',
            'description': 'شرح',
            'action': 'وضعیت',
            'correctiveaction': 'اقدامات اصلاحی',
            'priority': 'اولویت',
            'image': 'تصویر آنومالی',
            'anomalydescription': 'شرح آنومالی',
            'hse_type': 'نوع HSE',
        }
        widgets = {
            'location': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'anomalytype': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'followup': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 3, 'placeholder': 'یاداشت افسر ایمنی'}),
            'action': forms.CheckboxInput(attrs={'class': 'form-check-input form-check-solid'}),
            'correctiveaction': forms.Select(attrs={'class': 'form-control form-control-solid', 'readonly': True}),
            'priority': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-solid'}),
            'anomalydescription': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
            'hse_type': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'readonly': True}),

        }




from django import forms
from .models import Comments  # مطمئن شوید که نام مدل درست باشد

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments  # استفاده از مدل درست
        fields = ['comment']  # استفاده از فیلد comment به جای content
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'نظر خود را وارد کنید'}),
        }
        labels = {
            'comment': 'نظر شما',
        }
