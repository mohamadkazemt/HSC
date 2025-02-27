from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError

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
