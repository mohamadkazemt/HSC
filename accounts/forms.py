from django import forms
from django.contrib.auth.forms import AuthenticationForm

class User(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'ایمیل یا نام کاربری'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'رمز عبور'
    }))



class UserEditForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'ایمیل'
    }))
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'نام کاربری'
    }))
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'نام'
    }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'نام خانوادگی'
    }))
    mobile = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'شماره موبایل'
    }))
    image = forms.ImageField(widget=forms.FileInput(attrs={
        'class': 'form-control'
    }))
