from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile, DriverLicense, Section, Part, UnitGroup, Position
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'ایمیل یا نام کاربری'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'رمز عبور',
        'autocomplete': 'current-password',
        'id': 'passwordField'
    }))

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']  # فیلدهایی که کاربر اجازه ویرایش دارد
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid mb-3 mb-lg-0', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'ایمیل'})
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['mobile', 'image']  # فقط فیلدهایی که کاربر اجازه ویرایش دارد
        widgets = {
            'mobile': forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'شماره موبایل'}),
            'image': forms.FileInput(attrs={'class': 'd-none'})
        }

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg form-control-solid',
        'placeholder': 'رمز عبور فعلی'
    }), label='رمز عبور فعلی', required=False)
    
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg form-control-solid',
        'placeholder': 'رمز عبور جدید'
    }), label='رمز عبور جدید', required=False)
    
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg form-control-solid',
        'placeholder': 'تکرار رمز عبور جدید'
    }), label='تکرار رمز عبور جدید', required=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if old_password and not self.user.check_password(old_password):
            raise ValidationError('رمز عبور فعلی اشتباه است.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        old_password = cleaned_data.get('old_password')

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError('رمز عبور جدید و تکرار آن یکسان نیستند.')
        
        if new_password1 and not old_password:
            raise ValidationError('لطفا رمز عبور فعلی را وارد کنید.')

        return cleaned_data


class PersonnelEditForm(forms.ModelForm):
    first_name = forms.CharField(label='نام', max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'نام'}))
    last_name = forms.CharField(label='نام خانوادگی', max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'نام خانوادگی'}))

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'personnel_code', 'mobile', 'section', 'part', 'unit_group', 'position', 'group']
        widgets = {
            'personnel_code': forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'کد پرسنلی'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control form-control-lg form-control-solid', 'placeholder': 'شماره موبایل'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'part': forms.Select(attrs={'class': 'form-select'}),
            'unit_group': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.pop('user_instance', None)
        super().__init__(*args, **kwargs)
        # Populate user fields initial values
        if user_instance:
            self.fields['first_name'].initial = user_instance.first_name
            self.fields['last_name'].initial = user_instance.last_name

        # Ensure proper querysets for dropdowns
        self.fields['section'].queryset = Section.objects.all()
        self.fields['part'].queryset = Part.objects.all()
        self.fields['unit_group'].queryset = UnitGroup.objects.all()
        self.fields['position'].queryset = Position.objects.all()

    def save(self, commit=True):
        profile = super().save(commit=False)
        # Update related User's first_name/last_name
        if profile.user_id:
            if 'first_name' in self.cleaned_data:
                profile.user.first_name = self.cleaned_data.get('first_name', profile.user.first_name)
            if 'last_name' in self.cleaned_data:
                profile.user.last_name = self.cleaned_data.get('last_name', profile.user.last_name)
            if commit:
                profile.user.save()
        if commit:
            profile.save()
        return profile
class PasswordResetSMSForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'نام کاربری'
    }))


# accounts/forms.py
from django import forms

class PasswordResetConfirmForm(forms.Form):
    code = forms.CharField(max_length=6, required=True, label='کد تأیید')
    new_password = forms.CharField(widget=forms.PasswordInput, min_length=8, required=True, label='رمز عبور جدید')
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True, label='تکرار رمز عبور جدید')
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')


        if new_password and confirm_password and new_password != confirm_password:
             self.add_error('confirm_password', "رمز عبور جدید و تکرار آن یکسان نیستند.")
        return cleaned_data

class DriverLicenseForm(forms.ModelForm):
    license_base = forms.ChoiceField(
        choices=DriverLicense.LICENSE_BASE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    special_codes = forms.MultipleChoiceField(
        choices=DriverLicense.SPECIAL_CODES,
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control form-control-lg form-control-solid select2',
            'data-control': 'select2',
            'data-placeholder': 'کدهای ویژه را انتخاب کنید',
            'multiple': 'multiple'
        })
    )

    class Meta:
        model = DriverLicense
        fields = ['license_base', 'expiry_date', 'has_special', 'special_codes', 'front_image', 'back_image']
        widgets = {
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control form-control-lg form-control-solid',
                'type': 'text',
                'id': 'id_expiry_date'
            }),
            'has_special': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'has_special'
            }),
            'front_image': forms.FileInput(attrs={
                'class': 'form-control form-control-lg form-control-solid',
                'accept': 'image/jpeg,image/png'
            }),
            'back_image': forms.FileInput(attrs={
                'class': 'form-control form-control-lg form-control-solid',
                'accept': 'image/jpeg,image/png'
            })
        }


    def clean_front_image(self):
        image = self.cleaned_data.get('front_image')
        # Validate ONLY when a NEW file is uploaded in this request
        if 'front_image' in self.files and image:
            if image.size > 2 * 1024 * 1024:  # 2MB
                raise ValidationError('حجم فایل نباید بیشتر از ۲ مگابایت باشد.')
            if getattr(image, 'content_type', '') not in ['image/jpeg', 'image/png']:
                raise ValidationError('فرمت فایل باید jpg یا png باشد.')
        return image

    def clean_back_image(self):
        image = self.cleaned_data.get('back_image')
        # Validate ONLY when a NEW file is uploaded in this request
        if 'back_image' in self.files and image:
            if image.size > 2 * 1024 * 1024:  # 2MB
                raise ValidationError('حجم فایل نباید بیشتر از ۲ مگابایت باشد.')
            if getattr(image, 'content_type', '') not in ['image/jpeg', 'image/png']:
                raise ValidationError('فرمت فایل باید jpg یا png باشد.')
        return image

    def clean(self):
        cleaned_data = super().clean()
        has_special = cleaned_data.get('has_special')
        special_codes = cleaned_data.get('special_codes')

        if has_special and not special_codes:
            self.add_error('special_codes', 'لطفا حداقل یک کد ویژه را انتخاب کنید.')
        
        # اطمینان از اینکه special_codes به صورت لیست ذخیره می‌شود
        if special_codes:
            cleaned_data['special_codes'] = list(special_codes)
        else:
            cleaned_data['special_codes'] = []

        return cleaned_data
