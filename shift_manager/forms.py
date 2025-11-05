from django import forms
from .models import InitialShiftSetup, SHIFT_CHOICES


class InitialShiftSetupForm(forms.ModelForm):
    class Meta:
        model = InitialShiftSetup
        fields = ['start_date', 'group_A_shift', 'group_B_shift', 'group_C_shift', 'group_D_shift']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'jalali-date form-control form-control-solid w-full',
                'placeholder': 'تاریخ شروع را انتخاب کنید',
                'type': 'text',
            }),
            'group_A_shift': forms.Select(attrs={
                'class': 'select2-field w-full',
                'data-placeholder': 'شیفت گروه A را انتخاب کنید',
            }),
            'group_B_shift': forms.Select(attrs={
                'class': 'select2-field w-full',
                'data-placeholder': 'شیفت گروه B را انتخاب کنید',
            }),
            'group_C_shift': forms.Select(attrs={
                'class': 'select2-field w-full',
                'data-placeholder': 'شیفت گروه C را انتخاب کنید',
            }),
            'group_D_shift': forms.Select(attrs={
                'class': 'select2-field w-full',
                'data-placeholder': 'شیفت گروه D را انتخاب کنید',
            }),
        }
        labels = {
            'start_date': 'تاریخ شروع',
            'group_A_shift': 'گروه A',
            'group_B_shift': 'گروه B',
            'group_C_shift': 'گروه C',
            'group_D_shift': 'گروه D',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set choices for all shift fields
        for field_name in ['group_A_shift', 'group_B_shift', 'group_C_shift', 'group_D_shift']:
            self.fields[field_name].choices = SHIFT_CHOICES

