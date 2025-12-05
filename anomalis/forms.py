from django import forms
from .models import Anomaly, Priority, Comment
from django_select2.forms import Select2TagWidget
from .models import Anomaly, UserProfile
from .models import Location, Anomalytype, AnomalyDescription, HSE, CorrectiveAction, Priority, UserProfile
from django.core.exceptions import ValidationError
from .utils import validate_image_file
import os
import jdatetime

class AnomalyForm(forms.ModelForm):
    followup = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(user__groups__name='مسئول پیگیری'),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-solid modal-select2',
            'data-control': 'select2',
            'data-dropdown-parent': '#kt_modal_new_target .modal-body',
            'data-placeholder': 'مسئول پیگیری را انتخاب کنید',
            'aria-hidden': 'true',
            'data-kt-initialized': '1',
            'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
            'oninput': "this.setCustomValidity('')"
        }),
        label="مسئول پیگیری",
    )
    # Override the action field to set default to False
    action = forms.BooleanField(
        required=False,  # Make the field optional
        initial=False,   # Set default value to False
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input form-check-solid'
        }),
        label="وضعیت آنومالی"
    )
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # استفاده از تابع اعتبارسنجی از utils
            is_valid, error_message = validate_image_file(image)
            if not is_valid:
                raise forms.ValidationError(error_message)
            
            # بررسی حجم فایل (حداکثر 10 مگابایت قبل از فشرده‌سازی)
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('حجم تصویر نباید بیشتر از 10 مگابایت باشد')

        return image

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            # حداقل تعداد کاراکتر
            if len(description.strip()) < 10:
                raise forms.ValidationError('توضیحات باید حداقل 10 کاراکتر باشد')

            # حداکثر تعداد کاراکتر
            if len(description) > 1000:
                raise forms.ValidationError('توضیحات نمی‌تواند بیشتر از 1000 کاراکتر باشد')

        return description

    def clean(self):
        cleaned_data = super().clean()

        # بررسی ارتباط بین location و section
        location = cleaned_data.get('location')
        section = cleaned_data.get('section')
        if location and section and section.location != location:
            self.add_error('section', 'بخش انتخاب شده باید متعلق به محل انتخاب شده باشد')

        # بررسی ارتباط بین anomalytype و anomalydescription
        anomalytype = cleaned_data.get('anomalytype')
        anomalydescription = cleaned_data.get('anomalydescription')
        if anomalytype and anomalydescription and anomalydescription.anomalytype != anomalytype:
            self.add_error('anomalydescription', 'شرح آنومالی باید مرتبط با نوع آنومالی انتخاب شده باشد')

        # بررسی ارتباط بین anomalydescription و correctiveaction
        correctiveaction = cleaned_data.get('correctiveaction')
        if anomalydescription and correctiveaction and correctiveaction.anomali_type != anomalydescription:
            self.add_error('correctiveaction', 'اقدام اصلاحی باید مرتبط با شرح آنومالی باشد')

        return cleaned_data

    class Meta:
        model = Anomaly
        fields = ('location', 'section', 'anomalytype', 'followup', 'description', 'action',
                  'correctiveaction', 'priority', 'image', 'anomalydescription', 'hse_type')

        error_messages = {
            'location': {
                'required': 'لطفا محل آنومالی را انتخاب کنید',
            },
            'anomalytype': {
                'required': 'لطفا نوع آنومالی را انتخاب کنید',
            },
            'followup': {
                'required': 'لطفا مسئول پیگیری را انتخاب کنید',
            },
            'description': {
                'required': 'لطفا توضیحات را وارد کنید',
                'max_length': 'توضیحات نمی‌تواند بیشتر از 1000 کاراکتر باشد',
            },
            'priority': {
                'required': 'لطفا سطح اولویت را انتخاب کنید',
            },
            'anomalydescription': {
                'required': 'لطفا شرح آنومالی را انتخاب کنید',
            },
            'correctiveaction': {
                'required': 'لطفا اقدام اصلاحی را انتخاب کنید',
            },
        }

        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'محل آنومالی را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'section': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'بخش محل آنومالی را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"

            }),
            'anomalytype': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-hide-search': 'false',
                'data-placeholder': 'نوع آنومالی را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-solid',
                'rows': 3,
                'placeholder': 'یادداشت بازرس ایمنی',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'action': forms.CheckboxInput(attrs={
                'class': 'form-check-input form-check-solid',
                'checked': False
            }),
            'correctiveaction': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'readonly': True,
                'data-placeholder': 'اقدام اصلاحی را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'اولویت را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-solid',
                'accept': 'image/*'
            }),
            'anomalydescription': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-hide-search': 'false',
                'data-placeholder': 'شرح آنومالی را انتخاب کنید',
                'oninvalid': "this.setCustomValidity('لطفا این فیلد را پر کنید')",
                'oninput': "this.setCustomValidity('')"
            }),
            'hse_type': forms.TextInput(attrs={
                'class': 'form-control form-control-solid',
                'readonly': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields:
            if 'class' in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] += ' error-field'
            else:
                self.fields[field].widget.attrs['class'] = 'error-field'

        # فیلتر کردن اقدامات اصلاحی بر اساس anomalydescription
        instance = kwargs.get('instance')
        if instance and instance.anomalydescription:
            # اگر instance وجود دارد و anomalydescription دارد، فقط اقدامات مرتبط را نمایش بده
            self.fields['correctiveaction'].queryset = CorrectiveAction.objects.filter(
                anomali_type=instance.anomalydescription
            )
        else:
            # اگر instance وجود ندارد، queryset را خالی کن تا از طریق JavaScript پر شود
            self.fields['correctiveaction'].queryset = CorrectiveAction.objects.none()

        # تنظیم اجباری بودن فیلدها
        required_fields = ['location', 'anomalytype', 'followup', 'anomalydescription',
                           'correctiveaction', 'priority']
        for field_name in required_fields:
            self.fields[field_name].required = True

        # تنظیم CSS کلاس‌ها برای تمام فیلدهای select
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select) and field_name != 'hse_type':
                field.widget.attrs.update({
                    'class': 'form-select form-select-solid modal-select2',
                    'data-control': 'select2',
                    'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                    'aria-hidden': 'true',
                    'data-kt-initialized': '1'
                })

        # اضافه کردن placeholder برای فیلدها
        placeholders = {
            'location': 'محل آنومالی را انتخاب کنید',
            'section': 'بخش محل آنومالی را انتخاب کنید',
            'anomalytype': 'نوع آنومالی را انتخاب کنید',
            'followup': 'مسئول پیگیری را انتخاب کنید',
            'description': 'توضیحات خود را وارد کنید',
            'correctiveaction': 'اقدام اصلاحی را انتخاب کنید',
            'priority': 'اولویت را انتخاب کنید',
            'anomalydescription': 'شرح آنومالی را انتخاب کنید'
        }

        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['data-placeholder'] = placeholder


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment', 'file']  # Add 'file' field
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'نظر خود را بنویسید...',
                'maxlength': 500  # Add max length
            }),
            'file': forms.FileInput(attrs={  # Add file input widget
                'class': 'form-control',
                'accept': 'image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt' # Limit file types
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')  # Use get() to handle missing key
        comment = ' '.join(comment.split())
        if comment and len(comment) < 2:
            raise forms.ValidationError("کامنت باید حداقل 2 کاراکتر باشد")
        bad_words = ['spam', 'bad', 'word']  # Add your list
        if comment and any(word in comment.lower() for word in bad_words):
            raise forms.ValidationError("لطفا از کلمات نامناسب استفاده نکنید")
        return comment

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError("حجم فایل نباید بیشتر از 10 مگابایت باشد.")
        return file




class AnomalyReportForm(forms.Form):
    start_date = forms.CharField(
        label='تاریخ شروع (شمسی)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY/MM/DD'}),
        required=False
    )
    end_date = forms.CharField(
        label='تاریخ پایان (شمسی)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY/MM/DD'}),
        required=False
    )
