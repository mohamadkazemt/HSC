from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.forms.fields import DateField
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import PasswordChangeForm
# from jalali_date.fields import JalaliDateField, JalaliDateTimeField
# from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime
from django.forms import RadioSelect, CheckboxSelectMultiple

from .models import (
    MedicalVisit, 
    MedicineUsage, 
    Medicine, 
    MedicineCategory, 
    MedicalService,
    MedicineReturn,
    Hospital,
    EmergencyEquipment
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
        required=False,
        label=_("تعداد"),
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': '1'})
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

        if medicine:
            # اگر تعداد وارد نشده باشد، 1 درنظر بگیریم
            if not quantity:
                quantity = 1
                self.cleaned_data['quantity'] = quantity
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


class HospitalForm(forms.ModelForm):
    """فرم بیمارستان"""
    class Meta:
        model = Hospital
        fields = ['name', 'address', 'phone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MedicalVisitForm(forms.ModelForm):
    """فرم مراجعه پزشکی"""
    visit_time = forms.DateTimeField(
        label=_('زمان مراجعه'),
        widget=forms.TextInput(attrs={'class': 'form-control jalali-datetime'})
    )
    hospital_admission_time = forms.DateTimeField(
        label=_('زمان بستری در بیمارستان'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control jalali-datetime'})
    )
    hospital_discharge_time = forms.DateTimeField(
        label=_('زمان ترخیص از بیمارستان'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control jalali-datetime'})
    )
    
    class Meta:
        model = MedicalVisit
        fields = [
            'personnel_type', 'company_personnel', 'contractor_personnel',
            'visit_reason', 'visit_time', 'doctor_recommendation', 'services',
            'hospital', 'hospital_admission_time', 'hospital_discharge_time', 'hospital_diagnosis'
        ]
        widgets = {
            'personnel_type': RadioSelect(attrs={'class': 'form-check-input'}),
            'company_personnel': forms.Select(attrs={'class': 'form-select'}),
            'contractor_personnel': forms.Select(attrs={'class': 'form-select'}),
            'visit_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'doctor_recommendation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'services': CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'hospital': forms.Select(attrs={'class': 'form-select'}),
            'hospital_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['personnel_type'].choices = [choice for choice in self.fields['personnel_type'].choices if choice[0] != '']

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


class EmergencyPersonnelForm(forms.ModelForm):
    """فرم مدیریت پرسنل اورژانس"""
    ROLE_CHOICES = [
        ('EmergencyManager', _('مدیر اورژانس')),
        ('EmergencyDoctor', _('پزشک اورژانس')),
        ('EmergencyNurse', _('پرستار اورژانس')),
    ]
    
    first_name = forms.CharField(
        label=_('نام'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_('نام خانوادگی'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        label=_('نقش'),
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    password = forms.CharField(
        label=_('رمز عبور'),
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_('در صورت ویرایش، برای تغییر رمز عبور مقدار جدید را وارد کنید.')
    )
    password_confirm = forms.CharField(
        label=_('تکرار رمز عبور'),
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    is_active = forms.BooleanField(
        label=_('فعال'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # در صورت ویرایش، گروه فعلی را تعیین کن
            user_groups = self.instance.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse'])
            if user_groups.exists():
                self.fields['role'].initial = user_groups.first().name
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['password_confirm'].required = True
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if self.instance.pk:
            # در حالت ویرایش، چک کن که username تکراری نباشد (به جز خود کاربر)
            if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_('این نام کاربری قبلاً استفاده شده است.'))
        else:
            # در حالت ایجاد، چک کن که username تکراری نباشد
            if User.objects.filter(username=username).exists():
                raise ValidationError(_('این نام کاربری قبلاً استفاده شده است.'))
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        # اگر رمز عبور وارد شده، باید تکرار آن هم وارد شده باشد
        if password or password_confirm:
            if password != password_confirm:
                self.add_error('password_confirm', _('رمز عبور و تکرار آن مطابقت ندارند.'))
        
        # در حالت ایجاد، رمز عبور الزامی است
        if not self.instance.pk and not password:
            self.add_error('password', _('رمز عبور الزامی است.'))
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        # تنظیم رمز عبور
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
            
            # حذف گروه‌های قبلی اورژانس
            user.groups.filter(name__in=['EmergencyManager', 'EmergencyDoctor', 'EmergencyNurse']).delete()
            
            # افزودن به گروه جدید
            role = self.cleaned_data['role']
            group, created = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        
        return user


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
    expiry_date = forms.DateField(
        label=_('تاریخ انقضا'),
        widget=forms.TextInput(attrs={'class': 'form-control jalali-date'})
    )
    
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


class EmergencyEquipmentForm(forms.ModelForm):
    """فرم مدیریت تجهیزات اورژانس"""
    last_calibration_date = forms.DateField(
        label=_('تاریخ آخرین کالیبراسیون'),
        widget=forms.TextInput(attrs={'class': 'form-control jalali-date'})
    )
    next_calibration_date = forms.DateField(
        label=_('تاریخ کالیبراسیون بعدی'),
        widget=forms.TextInput(attrs={'class': 'form-control jalali-date'})
    )
    
    class Meta:
        model = EmergencyEquipment
        fields = ['name', 'serial_number', 'description', 'last_calibration_date', 'next_calibration_date', 'calibration_alert_days', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'calibration_alert_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        last_calibration = cleaned_data.get('last_calibration_date')
        next_calibration = cleaned_data.get('next_calibration_date')
        
        if last_calibration and next_calibration:
            if last_calibration > next_calibration:
                self.add_error('next_calibration_date', _("تاریخ کالیبراسیون بعدی نمی‌تواند قبل از تاریخ آخرین کالیبراسیون باشد."))
        
        return cleaned_data 