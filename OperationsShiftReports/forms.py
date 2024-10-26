from django import forms
from django.forms import formset_factory  # این خط را اضافه کنید
from .models import LoadingOperation, ShiftLeave, VehicleReport, MiningMachineReport


class LoadingOperationForm(forms.ModelForm):
    class Meta:
        model = LoadingOperation
        fields = ['stone_type', 'load_count']
        labels = {
            'stone_type': 'نوع سنگ',
            'load_count': 'تعداد بار',
        }


# ایجاد فرم تکرارشونده برای ثبت حداکثر 3 نوع سنگ
LoadingOperationFormSet = formset_factory(LoadingOperationForm, extra=3, max_num=3)

class ShiftLeaveForm(forms.ModelForm):
    class Meta:
        model = ShiftLeave
        fields = ['personnel_name', 'leave_status']
        labels = {
            'personnel_name': 'نام پرسنل',
            'leave_status': 'وضعیت مرخصی',
        }

# فرم تکرارشونده برای مرخصی‌ها
ShiftLeaveFormSet = formset_factory(ShiftLeaveForm, extra=3, max_num=10)  # قابلیت وارد کردن تا 10 نفر


class VehicleForm(forms.ModelForm):
    class Meta:
        model = VehicleReport
        fields = ['vehicle_name', 'is_active', 'inactive_time_start', 'inactive_time_end']
        labels = {
            'vehicle_name': 'نام خودرو',
            'is_active': 'فعال بودن',
            'inactive_time_start': 'زمان شروع غیر فعال بودن',
            'inactive_time_end': 'زمان پایان غیر فعال بودن',
        }


class MiningMachineForm(forms.ModelForm):
    class Meta:
        model = MiningMachineReport
        fields = ['machine_name', 'machine_type', 'block']
        labels = {
            'machine_name': 'نام دستگاه',
            'machine_type': 'نوع دستگاه',
            'block': 'نام بلوک',
        }
