from django import forms
from .models import Anomaly, Priority, Comment
from django_select2.forms import Select2TagWidget
from .models import Anomaly, UserProfile

class AnomalyForm(forms.ModelForm):
    followup = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(user__groups__name='مسئول پیگیری'),
        widget=forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2'}),
        label="پیگیری"
    )

    class Meta:
        model = Anomaly
        fields = ('location', 'anomalytype', 'followup', 'description', 'action', 'correctiveaction', 'priority', 'image', 'anomalydescription', 'hse_type')
        labels = {
            'location': 'محل آنومالی',
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
            'anomalytype': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2', 'data-hide-search': 'false'}),
            'followup': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2', 'data-hide-search': 'false'}),
            'description': forms.Textarea(attrs={'class': 'form-control form-control-solid', 'rows': 3, 'placeholder': 'یاداشت افسر ایمنی'}),
            'action': forms.CheckboxInput(attrs={'class': 'form-check-input form-check-solid'}),
            'correctiveaction': forms.Select(attrs={'class': 'form-control form-control-solid', 'readonly': True}),
            'priority': forms.Select(attrs={'class': 'form-control form-control-solid', 'data-control': 'select2'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control form-control-solid'}),
            'anomalydescription': forms.Select(attrs={'class': 'form-select form-select-solid', 'data-control': 'select2', 'data-hide-search': 'false'}),
            'hse_type': forms.TextInput(attrs={'class': 'form-control form-control-solid', 'readonly': True}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']  # Only include the comment text
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'نوشتن نظر شما..'}),
        }