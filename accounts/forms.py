from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

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
        fields = ['username', 'first_name', 'last_name', 'email']  # فیلدهای مورد نظر از مدل User
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),

        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['personnel_code', 'image', 'mobile', 'group']
        widgets = {
            'personnel_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد پرسنلی'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره موبایل'}),
            'group': forms.Select(attrs={'class': 'form-control'})
        }


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
