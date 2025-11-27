# hse_docs/forms.py
from django import forms
from .models import Document, TopicCategory
from accounts.models import Section, UnitGroup


class DocumentForm(forms.ModelForm):
    """Form for uploading HSE documents"""
    
    class Meta:
        model = Document
        fields = [
            'title',
            'file',
            'topic_category',
            'section',
            'unit_group',
            'version',
            'description',
            'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white',
                'placeholder': 'عنوان سند'
            }),
            'file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png'
            }),
            'topic_category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white select2',
                'required': True
            }),
            'section': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white select2'
            }),
            'unit_group': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white select2'
            }),
            'version': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white',
                'placeholder': '1.0'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:text-white',
                'rows': 4,
                'placeholder': 'توضیحات اختیاری'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500'
            })
        }
        labels = {
            'title': 'عنوان سند',
            'file': 'فایل',
            'topic_category': 'دسته‌بندی موضوع *',
            'section': 'بخش',
            'unit_group': 'گروه',
            'version': 'نسخه',
            'description': 'توضیحات',
            'is_active': 'فعال'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make topic_category required
        self.fields['topic_category'].required = True
        self.fields['file'].required = True
        
        # Add empty option for section and unit_group
        self.fields['section'].queryset = Section.objects.all().order_by('name')
        self.fields['section'].empty_label = "--- انتخاب نشده (سند عمومی) ---"
        self.fields['section'].required = False
        
        self.fields['unit_group'].queryset = UnitGroup.objects.all().order_by('name')
        self.fields['unit_group'].empty_label = "--- انتخاب نشده (سند عمومی) ---"
        self.fields['unit_group'].required = False

    def clean(self):
        cleaned_data = super().clean()
        section = cleaned_data.get('section')
        unit_group = cleaned_data.get('unit_group')
        
        if section and unit_group:
            raise forms.ValidationError({
                'section': 'یک سند نمی‌تواند همزمان به یک بخش و یک گروه اختصاص یابد.',
                'unit_group': 'یک سند نمی‌تواند همزمان به یک بخش و یک گروه اختصاص یابد.'
            })
        
        return cleaned_data


class DocumentSearchForm(forms.Form):
    """Simple search form for documents"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجوی عنوان سند...',
            'autocomplete': 'off'
        }),
        label='جستجو'
    )

