from django import forms
from .models import ShiftReport

class ShiftReportForm(forms.ModelForm):
    class Meta:
        model = ShiftReport
        fields = ['leave_type', 'user', 'leave_hours', 'start_time', 'end_time', 'status','description']  # اضافه شدن 'description'
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),  # ویجت ساعت شروع
            'end_time': forms.TimeInput(attrs={'type': 'time'}),  # ویجت ساعت پایان
        }

    def clean(self):
        cleaned_data = super().clean()  # Get cleaned data from parent
        leave_type = cleaned_data.get('leave_type')  # دریافت نوع مرخصی
        start_time = cleaned_data.get('start_time')  # دریافت ساعت شروع
        end_time = cleaned_data.get('end_time')  # دریافت ساعت پایان
        description = cleaned_data.get('description')  # دریافت توضیحات

        # اعتبارسنجی برای مرخصی ساعتی
        if leave_type == 'hourly' and (not start_time or not end_time):
            raise forms.ValidationError('برای مرخصی ساعتی باید ساعت شروع و پایان وارد شود.')

        # اعتبارسنجی برای سایر انواع مرخصی (غیرساعتی)
        if leave_type != 'hourly' and (start_time or end_time):
            raise forms.ValidationError('برای نوع مرخصی غیر ساعتی، ساعت شروع و پایان وارد نمی‌شود.')

        # اعتبارسنجی برای غیبت و استعلاجی
        if leave_type in ['absence', 'sick_leave'] and not description:
            raise forms.ValidationError('برای غیبت و مرخصی استعلاجی باید توضیحات وارد شود.')

        if leave_type not in ['absence', 'sick_leave'] and description:
            raise forms.ValidationError('فقط برای غیبت و مرخصی استعلاجی توضیحات وارد میشود')
        return cleaned_data