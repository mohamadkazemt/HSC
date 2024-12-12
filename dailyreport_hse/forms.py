from django import forms
from .models import DailyReport, BlastingDetail, DrillingDetail, DumpDetail, LoadingDetail

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = []
        widgets = {
            'created_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'updated_at': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class BlastingDetailForm(forms.ModelForm):
    class Meta:
        model = BlastingDetail
        fields = ['block', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-select select2'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DrillingDetailForm(forms.ModelForm):
    class Meta:
        model = DrillingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-select select2'}),
            'machine': forms.Select(attrs={'class': 'form-select select2'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DumpDetailForm(forms.ModelForm):
    class Meta:
        model = DumpDetail
        fields = ['dump', 'status', 'description']
        widgets = {
            'dump': forms.Select(attrs={'class': 'form-select select2'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LoadingDetailForm(forms.ModelForm):
    class Meta:
        model = LoadingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-select select2'}),
            'machine': forms.Select(attrs={'class': 'form-select select2'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }