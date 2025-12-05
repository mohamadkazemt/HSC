# core/ai_forms.py
"""
فرم‌های مربوط به تنظیمات AI
"""
from django import forms
from .ai_models import AISettings


class AISettingsForm(forms.ModelForm):
    """فرم تنظیمات AI"""
    
    class Meta:
        model = AISettings
        fields = [
            'provider',
            'api_key',
            'api_base_url',
            'model',
            'timeout',
            'max_retries',
            'cache_timeout',
            'temperature',
            'is_active',
        ]
        
        widgets = {
            'provider': forms.Select(attrs={
                'class': 'form-select w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'id': 'id_provider'
            }),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'API Key را وارد کنید',
                'autocomplete': 'new-password'
            }),
            'api_base_url': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'آدرس پایه API'
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'placeholder': 'مثلاً: gpt-4, gemini-pro'
            }),
            'timeout': forms.NumberInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'min': 1,
                'max': 300
            }),
            'max_retries': forms.NumberInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'min': 0,
                'max': 10
            }),
            'cache_timeout': forms.NumberInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'min': 0
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-input w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white',
                'min': 0,
                'max': 1,
                'step': 0.1
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-checkbox h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600'
            }),
        }
        
        labels = {
            'provider': 'ارائه‌دهنده AI',
            'api_key': 'API Key',
            'api_base_url': 'آدرس پایه API',
            'model': 'مدل',
            'timeout': 'Timeout (ثانیه)',
            'max_retries': 'تعداد تلاش مجدد',
            'cache_timeout': 'زمان کش (ثانیه)',
            'temperature': 'Temperature',
            'is_active': 'فعال',
        }
        
        help_texts = {
            'api_key': 'کلید API از سایت ارائه‌دهنده (به صورت رمزگذاری‌شده ذخیره می‌شود)',
            'api_base_url': 'برای Google AI Studio: https://generativelanguage.googleapis.com/v1beta',
            'model': 'نام مدل استفاده شده (مثلاً: gpt-4, gemini-pro, claude-3-opus)',
            'timeout': 'حداکثر زمان انتظار برای پاسخ API (ثانیه)',
            'max_retries': 'تعداد دفعات تلاش مجدد در صورت خطا',
            'cache_timeout': 'زمان نگهداری نتایج در کش (1 ساعت = 3600 ثانیه)',
            'temperature': 'میزان خلاقیت پاسخ‌ها (0-1). مقدار پایین = دقیق‌تر، مقدار بالا = خلاق‌تر',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # اگر instance وجود دارد و api_key دارد، نشان دادن placeholder
        if self.instance and self.instance.pk:
            api_key = self.instance.get_api_key_safe()
            if api_key:
                self.fields['api_key'].widget.attrs['placeholder'] = '•••••••• (برای تغییر، مقدار جدید وارد کنید)'
                self.fields['api_key'].required = False
    
    def clean_api_key(self):
        """اعتبارسنجی API Key"""
        api_key = self.cleaned_data.get('api_key')
        # اگر خالی است و instance وجود دارد، از مقدار قبلی استفاده کن
        if not api_key and self.instance and self.instance.pk:
            return self.instance.api_key
        return api_key
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # اگر api_key خالی است و instance قبلی وجود دارد، تغییر نده
        if not self.cleaned_data.get('api_key') and self.instance and self.instance.pk:
            # api_key را تغییر نده
            pass
        if commit:
            instance.save()
        return instance
