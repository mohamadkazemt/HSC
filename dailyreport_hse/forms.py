from django import forms
from django.forms import modelformset_factory
from .models import (
    DailyReport,
    BlastingDetail,
    DrillingDetail,
    DumpDetail,
    LoadingDetail,
    InspectionDetail,
    StoppageDetail,
    FollowupDetail,
)

class DailyReportForm(forms.ModelForm):
    """
    فرم اصلی گزارش روزانه
    """
    class Meta:
        model = DailyReport
        fields = []  # فیلدهای خودکار مدیریت می‌شوند

class BlastingDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله آتشباری
    """
    class Meta:
        model = BlastingDetail
        fields = ['status','block',  'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DrillingDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله حفاری
    """
    class Meta:
        model = DrillingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control'}),
            'machine': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DumpDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله دامپ‌ها
    """
    class Meta:
        model = DumpDetail
        fields = ['dump', 'status', 'description']
        widgets = {
            'dump': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LoadingDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله بارگیری
    """
    class Meta:
        model = LoadingDetail
        fields = ['block', 'machine', 'status', 'description']
        widgets = {
            'block': forms.Select(attrs={'class': 'form-control'}),
            'machine': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InspectionDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله تعمیرگاه
    """
    class Meta:
        model = InspectionDetail
        fields = ['status', 'status_detail', 'description']
        widgets = {
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status_detail': forms.Select(choices=[('safe', 'ایمن'), ('unsafe', 'غیر ایمن')], attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class StoppageDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله توقفات
    """
    class Meta:
        model = StoppageDetail
        fields = ['reason', 'duration']
        widgets = {
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class FollowupDetailForm(forms.ModelForm):
    """
    فرم جزئیات مرحله پیگیری
    """
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
    can_delete=True,
)

DrillingDetailFormset = modelformset_factory(
    DrillingDetail,
    form=DrillingDetailForm,
    extra=1,
    can_delete=True,
)

DumpDetailFormset = modelformset_factory(
    DumpDetail,
    form=DumpDetailForm,
    extra=1,
    can_delete=True,
)

LoadingDetailFormset = modelformset_factory(
    LoadingDetail,
    form=LoadingDetailForm,
    extra=1,
    can_delete=True,
)
