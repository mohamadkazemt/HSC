from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms.fields import DateField
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget

from .models import (
    MedicalVisit, 
    MedicineUsage, 
    Medicine, 
    MedicineCategory, 
    MedicalService,
    MedicineReturn
)
from accounts.models import UserProfile
from contractor_management.models import Employee


class MedicineSelectForm(forms.Form):
    """فرم انتخاب دارو و تعداد"""
    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(is_active=True),
        label=_("دارو"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        label=_("تعداد"),
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # نمایش موجودی فعلی در کنار نام دارو
        medicines = Medicine.objects.filter(is_active=True)
        choices = [
            (medicine.id, f"{medicine.name} (موجودی: {medicine.quantity})") 
            for medicine in medicines
        ]
        self.fields['medicine'].choices = [('', '---------')] + choices

    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity')

        if medicine and quantity:
            # بررسی موجودی کافی
            if medicine.quantity < quantity:
                raise ValidationError(
                    _("موجودی کافی نیست. موجودی فعلی: %(current)d"),
                    code='invalid',
                    params={'current': medicine.quantity},
                )
            
            # بررسی تاریخ انقضا
            if medicine.is_expired():
                raise ValidationError(_("این دارو منقضی شده است و قابل استفاده نیست."))

        return cleaned_data


class MedicalVisitForm(forms.ModelForm):
    """فرم ثبت مراجعه پزشکی"""
    personnel_type = forms.ChoiceField(
        choices=MedicalVisit.PERSONNEL_TYPE_CHOICES,
        label=_("نوع پرسنل"),
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    company_personnel = forms.ModelChoiceField(
        queryset=UserProfile.objects.all(),
        label=_("پرسنل شرکت"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    
    contractor_personnel = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label=_("پرسنل پیمانکار"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    
    visit_reason = forms.CharField(
        label=_("علت مراجعه"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    doctor_recommendation = forms.CharField(
        label=_("توصیه پزشک"),
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    services = forms.ModelMultipleChoiceField(
        queryset=MedicalService.objects.all(),
        label=_("خدمات درمانی انجام‌شده"),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = MedicalVisit
        fields = [
            'personnel_type', 'company_personnel', 'contractor_personnel',
            'visit_reason', 'visit_time', 'doctor_recommendation', 'services'
        ]
        widgets = {
            'visit_time': forms.DateTimeInput(attrs={'class': 'form-control datetime-picker'})
        }
    
    def clean(self):
        cleaned_data = super().clean()
        personnel_type = cleaned_data.get('personnel_type')
        company_personnel = cleaned_data.get('company_personnel')
        contractor_personnel = cleaned_data.get('contractor_personnel')
        
        if personnel_type == 'company' and not company_personnel:
            self.add_error('company_personnel', _("برای پرسنل شرکت باید یک نفر را انتخاب کنید."))
        
        if personnel_type == 'contractor' and not contractor_personnel:
            self.add_error('contractor_personnel', _("برای پرسنل پیمانکار باید یک نفر را انتخاب کنید."))
        
        return cleaned_data


class MedicineCategoryForm(forms.ModelForm):
    """فرم دسته‌بندی دارو"""
    class Meta:
        model = MedicineCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MedicineForm(forms.ModelForm):
    """فرم مدیریت دارو"""
    class Meta:
        model = Medicine
        fields = ['name', 'category', 'quantity', 'expiry_date', 'critical_threshold', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select select2'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'critical_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # استفاده از DateField معمولی به جای JalaliDateField
        # چون تبدیل تاریخ در views.py انجام می‌شود
        self.fields['expiry_date'] = DateField(
            label=_('تاریخ انقضا'),
            widget=forms.DateInput(attrs={'class': 'form-control jalali-datepicker'})
        )


class MedicalServiceForm(forms.ModelForm):
    """فرم خدمات درمانی"""
    class Meta:
        model = MedicalService
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MedicineReturnForm(forms.ModelForm):
    """فرم برگشت دارو"""
    class Meta:
        model = MedicineReturn
        fields = ['quantity', 'return_reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'return_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, usage=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.usage = usage
        
        if usage:
            self.fields['quantity'].help_text = _(f"حداکثر {usage.quantity} عدد")
            self.fields['quantity'].widget.attrs['max'] = usage.quantity
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity > self.usage.quantity:
            raise ValidationError(
                _("تعداد برگشتی نمی‌تواند از تعداد مصرف شده (%(used)d) بیشتر باشد."),
                code='invalid',
                params={'used': self.usage.quantity},
            )
        return quantity 