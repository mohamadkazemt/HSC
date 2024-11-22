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
    mobile = forms.CharField(max_length=11, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'شماره موبایل'
    }))


class PasswordResetConfirmForm(forms.Form):
    code = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'کد تأیید'
    }))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'رمز عبور جدید'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'تأیید رمز عبور جدید'
    }))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password != confirm_password:
            raise forms.ValidationError("رمز عبور و تأیید آن مطابقت ندارند.")
        return cleaned_data
