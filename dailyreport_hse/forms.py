from django import forms
from .models import (
    DailyReport, BlastingDetail, DrillingDetail,
    DumpDetail, LoadingDetail, InspectionDetail,
    StoppageDetail, FollowupDetail
)
from BaseInfo.models import MiningBlock, MiningMachine, Dump

# فرم گزارش اصلی
class DailyReportForm(forms.ModelForm):
    class Meta:
        model = DailyReport
        fields = ['shift', 'supervisor_comments']
        labels = {
            'shift': 'شیفت کاری',
            'supervisor_comments': 'توضیحات سرشیفت'
        }

# فرم جزئیات آتشباری
class BlastingDetailForm(forms.ModelForm):
    class Meta:
        model = BlastingDetail
        fields = ['block', 'description']
        labels = {
            'block': 'بلوک آتشباری',
            'description': 'توضیحات'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['block'].queryset = MiningBlock.objects.filter(is_active=True)

# فرم جزئیات حفاری
class DrillingDetailForm(forms.ModelForm):
    class Meta:
        model = DrillingDetail
        fields = ['block', 'machine', 'status']
        labels = {
            'block': 'بلوک حفاری',
            'machine': 'دستگاه حفاری',
            'status': 'وضعیت'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['block'].queryset = MiningBlock.objects.filter(is_active=True)
        self.fields['machine'].queryset = MiningMachine.objects.filter(is_active=True)

# فرم جزئیات تخلیه
class DumpDetailForm(forms.ModelForm):
    class Meta:
        model = DumpDetail
        fields = ['dump', 'status', 'description']
        labels = {
            'dump': 'دامپ',
            'status': 'وضعیت دامپ',
            'description': 'توضیحات'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dump'].queryset = Dump.objects.filter(is_active=True)

# فرم جزئیات بارگیری
class LoadingDetailForm(forms.ModelForm):
    class Meta:
        model = LoadingDetail
        fields = ['block', 'machine', 'status']
        labels = {
            'block': 'بلوک بارگیری',
            'machine': 'دستگاه بارگیری',
            'status': 'وضعیت بارگیری'
        }

# فرم جزئیات بازرسی
class InspectionDetailForm(forms.ModelForm):
    class Meta:
        model = InspectionDetail
        fields = ['inspection_done', 'status', 'description']
        labels = {
            'inspection_done': 'آیا بازدید انجام شد؟',
            'status': 'وضعیت بازدید',
            'description': 'توضیحات'
        }

# فرم جزئیات توقفات
class StoppageDetailForm(forms.ModelForm):
    class Meta:
        model = StoppageDetail
        fields = ['reason', 'start_time', 'end_time', 'description']
        labels = {
            'reason': 'علت توقف',
            'start_time': 'زمان شروع',
            'end_time': 'زمان پایان',
            'description': 'توضیحات'
        }

# فرم جزئیات پیگیری
class FollowupDetailForm(forms.ModelForm):
    class Meta:
        model = FollowupDetail
        fields = ['description', 'files']
        labels = {
            'description': 'توضیحات',
            'files': 'فایل‌های پیوست'
        }
