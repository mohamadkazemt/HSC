from django import forms
from .models import SiteSettings

TW_BASE_INPUT = 'block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm'
TW_TEXTAREA = TW_BASE_INPUT + ' min-h-[120px]'
TW_FILE = 'block w-full text-sm text-gray-900 dark:text-gray-100 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 dark:file:bg-gray-700 dark:file:text-gray-100'

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'site_name': forms.TextInput(attrs={'class': TW_BASE_INPUT, 'placeholder': 'نام سایت'}),
            'contact_email': forms.EmailInput(attrs={'class': TW_BASE_INPUT, 'placeholder': 'ایمیل تماس'}),
            'phone_number': forms.TextInput(attrs={'class': TW_BASE_INPUT, 'placeholder': 'شماره تماس'}),
            'address': forms.Textarea(attrs={'class': TW_TEXTAREA, 'placeholder': 'آدرس'}),
            'seo_description': forms.Textarea(attrs={'class': TW_TEXTAREA, 'placeholder': 'توضیحات سئو'}),
            'site_favicon': forms.ClearableFileInput(attrs={'class': TW_FILE, 'accept': 'image/*'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': TW_FILE, 'accept': 'image/*'}),
        }
