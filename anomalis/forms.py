from django import forms
from .models import Anomaly, Priority, Comment
from django_select2.forms import Select2TagWidget
from .models import Anomaly, UserProfile


class AnomalyForm(forms.ModelForm):
    followup = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(user__groups__name='مسئول پیگیری'),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-solid modal-select2',
            'data-control': 'select2',
            'data-dropdown-parent': '#kt_modal_new_target .modal-body',
            'data-placeholder': 'مسئول پیگیری را انتخاب کنید',
            'aria-hidden': 'true',
            'data-kt-initialized': '1'
        }),
        label="پیگیری"
    )
    # Override the action field to set default to False
    action = forms.BooleanField(
        required=False,  # Make the field optional
        initial=False,   # Set default value to False
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input form-check-solid'
        })
    )

    class Meta:
        model = Anomaly
        fields = ('location', 'section','anomalytype', 'followup', 'description', 'action',
                  'correctiveaction', 'priority', 'image', 'anomalydescription', 'hse_type')
        labels = {
            'location': 'محل آنومالی',
            'section' : 'بخش محل',
            'anomalytype': 'نوع آنومالی',
            'followup': 'پیگیری',
            'description': 'شرح',
            'action': 'وضعیت',
            'correctiveaction': 'اقدامات اصلاحی',
            'priority': 'سطح ریسک',
            'image': 'تصویر آنومالی',
            'anomalydescription': 'شرح آنومالی',
            'hse_type': 'حوزه HSE',
        }
        widgets = {
            'location': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'محل آنومالی را انتخاب کنید'
            }),
            'section': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'بخش محل آنومالی را انتخاب کنید'
            }),
            'anomalytype': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-hide-search': 'false',
                'data-placeholder': 'نوع آنومالی را انتخاب کنید'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-solid',
                'rows': 3,
                'placeholder': 'یادداشت افسر ایمنی'
            }),
            'action': forms.CheckboxInput(attrs={
                'class': 'form-check-input form-check-solid'
            }),
            'correctiveaction': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'readonly': True,
                'data-placeholder': 'اقدام اصلاحی را انتخاب کنید'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select form-select-solid modal-select2',
                'data-control': 'select2',
                'data-dropdown-parent': '#kt_modal_new_target .modal-body',
                'aria-hidden': 'true',
                'data-kt-initialized': '1',
                'data-placeholder': 'اولویت را انتخاب کنید'
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
                'data-placeholder': 'شرح آنومالی را انتخاب کنید'
            }),
            'hse_type': forms.TextInput(attrs={
                'class': 'form-control form-control-solid',
                'readonly': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'نظر خود را بنویسید...',
                'maxlength': 500  # Add max length
            }),
        }

    def clean_comment(self):
        comment = self.cleaned_data['comment']
        # Remove extra whitespace
        comment = ' '.join(comment.split())

        # Check minimum length
        if len(comment) < 2:
            raise forms.ValidationError("کامنت باید حداقل 2 کاراکتر باشد")

        # Check for bad words or spam
        bad_words = ['spam', 'bad', 'word']  # Add your list
        if any(word in comment.lower() for word in bad_words):
            raise forms.ValidationError("لطفا از کلمات نامناسب استفاده نکنید")

        return comment