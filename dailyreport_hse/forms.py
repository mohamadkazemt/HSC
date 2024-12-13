from django import forms
from django.forms import modelformset_factory
from .models import DailyReport, BlastingDetail, DrillingDetail, DumpDetail, LoadingDetail, InspectionDetail, StoppageDetail, FollowupDetail

class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = []  # Removed 'report_time' and 'user' as they are auto-handled in views or models

class BlastingDetailForm(forms.ModelForm):
    class Meta:
        model = BlastingDetail
        fields = ['block', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control select2'}),
            'status': forms.CheckboxInput(),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DrillingDetailForm(forms.ModelForm):
    class Meta:
        model = DrillingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control select2'}),
            'machine': forms.Select(attrs={'class': 'form-control select2'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DumpDetailForm(forms.ModelForm):
    class Meta:
        model = DumpDetail
        fields = ['dump', 'status', 'description']
        widgets = {
            'dump': forms.Select(attrs={'class': 'form-control select2'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LoadingDetailForm(forms.ModelForm):
    class Meta:
        model = LoadingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control select2'}),
            'machine': forms.Select(attrs={'class': 'form-control select2'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InspectionDetailForm(forms.ModelForm):
    class Meta:
        model = InspectionDetail
        fields = ['status', 'status_detail', 'description']
        widgets = {
            'status': forms.CheckboxInput(),
            'status_detail': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StoppageDetailForm(forms.ModelForm):
    class Meta:
        model = StoppageDetail
        fields = ['reason', 'duration']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FollowupDetailForm(forms.ModelForm):
    class Meta:
        model = FollowupDetail
        fields = ['description', 'files']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'files': forms.FileInput(attrs={'class': 'form-control'}),
        }


# تعریف فرمست‌ها برای مراحل مختلف
BlastingDetailFormset = modelformset_factory(
    BlastingDetail,
    form=BlastingDetailForm,
    extra=1,
    can_delete=True
)

DrillingDetailFormset = modelformset_factory(
    DrillingDetail,
    form=DrillingDetailForm,
    extra=1,
    can_delete=True
)

DumpDetailFormset = modelformset_factory(
    DumpDetail,
    form=DumpDetailForm,
    extra=1,
    can_delete=True
)

LoadingDetailFormset = modelformset_factory(
    LoadingDetail,
    form=LoadingDetailForm,
    extra=1,
    can_delete=True
)