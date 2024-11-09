from django import forms
from django.forms import formset_factory
from .models import LoadingOperation, ShiftLeave, VehicleReport, LoaderStatus
from BaseInfo.models import MiningMachine, MiningBlock

class LoadingOperationForm(forms.ModelForm):
    class Meta:
        model = LoadingOperation
        fields = ['stone_type', 'load_count']
        labels = {
            'stone_type': 'نوع سنگ',
            'load_count': 'تعداد بار',
        }
        widgets = {
            'stone_type': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'نوع سنگ را انتخاب کنید',
                'data-hide-search': 'true'
            }),
            'load_count': forms.NumberInput(attrs={
                'class': 'form-control form-control-solid',
                'placeholder': 'تعداد بار را وارد کنید'
            })
        }

class LoaderStatusForm(forms.ModelForm):
    class Meta:
        model = LoaderStatus
        fields = ['loader', 'block', 'status', 'inactive_reason']
        widgets = {
            'loader': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'لودر را انتخاب کنید'
            }),
            'block': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'بلوک را انتخاب کنید'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'وضعیت را انتخاب کنید'
            }),
            'inactive_reason': forms.Textarea(attrs={
                'class': 'form-control form-control-solid',
                'rows': 3,
                'placeholder': 'در صورت غیرفعال بودن، دلیل را وارد کنید'
            })
        }

class ShiftLeaveForm(forms.ModelForm):
    class Meta:
        model = ShiftLeave
        fields = ['personnel_name', 'leave_status']
        widgets = {
            'personnel_name': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'پرسنل را انتخاب کنید'
            }),
            'leave_status': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'وضعیت مرخصی را انتخاب کنید'
            })
        }

class VehicleReportForm(forms.ModelForm):
    class Meta:
        model = VehicleReport
        fields = ['vehicle_name', 'is_active', 'inactive_time_start', 'inactive_time_end']
        widgets = {
            'vehicle_name': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'خودرو را انتخاب کنید'
            }),
            'is_active': forms.Select(attrs={
                'class': 'form-select form-select-solid select2-hidden-accessible',
                'data-control': 'select2',
                'data-placeholder': 'وضعیت را انتخاب کنید'
            }),
            'inactive_time_start': forms.TimeInput(attrs={
                'class': 'form-control form-control-solid',
                'type': 'time'
            }),
            'inactive_time_end': forms.TimeInput(attrs={
                'class': 'form-control form-control-solid',
                'type': 'time'
            })
        }

class ShiftReportForm(forms.Form):
    supervisor_comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control form-control-solid',
            'rows': 4,
            'placeholder': 'توضیحات سرشیفت را وارد کنید'
        }),
        required=True
    )
    attached_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control form-control-solid',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
        }),
        required=False
    )