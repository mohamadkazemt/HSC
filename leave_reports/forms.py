from django import forms
from .models import ShiftReport, ApprovalHierarchy
from accounts.models import UserProfile, Section, Part, UnitGroup, Position
from django.contrib.auth.models import User
import jdatetime


class LeaveRequestForm(forms.ModelForm):
    """فرم درخواست مرخصی جدید"""
    shift_date = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'jalali-date w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'تاریخ مرخصی را انتخاب کنید',
        }),
        label='تاریخ مرخصی'
    )
    
    replacement_person = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={
            'class': 'select2-ajax w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white',
            'data-placeholder': 'انتخاب جایگزین'
        }),
        label='جایگزین پیشنهادی',
        required=False,
        help_text='فقط برای مرخصی استحقاقی الزامی است'
    )

    
    medical_document = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'w-full text-sm text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700 focus:outline-none',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        label='مدارک پزشکی',
        required=False,
        help_text='برای مرخصی استعلاجی الزامی است (فرمت: PDF, JPG, PNG)'
    )
    
    class Meta:
        model = ShiftReport
        fields = ['leave_type', 'shift_date', 'shift_type', 'leave_hours', 
                  'start_time', 'end_time', 'description', 'replacement_person', 'medical_document']
        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'id': 'id_leave_type'
            }),
            'shift_type': forms.Select(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            }),
            'leave_hours': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'placeholder': 'تعداد ساعات',
                'min': '1'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
                'rows': 4,
                'placeholder': 'توضیحات خود را وارد کنید...'
            }),
        }
        labels = {
            'leave_type': 'نوع مرخصی',
            'shift_type': 'نوع شیفت',
            'leave_hours': 'ساعات مرخصی',
            'start_time': 'ساعت شروع',
            'end_time': 'ساعت پایان',
            'description': 'توضیحات',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # فیلتر کردن لیست جایگزین‌ها براساس بخش کاربر
        if self.user and hasattr(self.user, 'userprofile'):
            user_profile = self.user.userprofile
            if user_profile.section:
                # نمایش کاربران همان بخش (به جز خود کاربر)
                self.fields['replacement_person'].queryset = User.objects.filter(
                    userprofile__section=user_profile.section
                ).exclude(id=self.user.id).select_related('userprofile')

    def clean_shift_date(self):
        shift_date = self.cleaned_data.get('shift_date')
        if shift_date:
            try:
                # تبدیل تاریخ شمسی به میلادی
                if isinstance(shift_date, str):
                    if '/' in shift_date:
                        year, month, day = map(int, shift_date.split('/'))
                    elif '-' in shift_date:
                        year, month, day = map(int, shift_date.split('-'))
                    else:
                        raise ValueError("فرمت تاریخ نامعتبر است")
                    
                    jalali_date = jdatetime.date(year, month, day)
                    return jalali_date.togregorian()
            except (ValueError, TypeError) as e:
                raise forms.ValidationError(f'تاریخ نامعتبر است: {str(e)}')
        return shift_date

    def clean(self):
        cleaned_data = super().clean()
        leave_type = cleaned_data.get('leave_type')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        description = cleaned_data.get('description')
        replacement_person = cleaned_data.get('replacement_person')
        medical_document = cleaned_data.get('medical_document')

        # اعتبارسنجی برای مرخصی ساعتی
        if leave_type == 'hourly':
            if not start_time or not end_time:
                raise forms.ValidationError('برای مرخصی ساعتی باید ساعت شروع و پایان وارد شود.')
            if start_time >= end_time:
                raise forms.ValidationError('ساعت پایان باید بعد از ساعت شروع باشد.')

        # اعتبارسنجی جایگزین - فقط برای مرخصی استحقاقی
        if leave_type == 'regular' and not replacement_person:
            raise forms.ValidationError('برای مرخصی استحقاقی باید جایگزین انتخاب کنید.')
        
        # اعتبارسنجی مدارک پزشکی - فقط برای مرخصی استعلاجی
        if leave_type == 'sick_leave' and not medical_document:
            raise forms.ValidationError('برای مرخصی استعلاجی باید مدارک پزشکی را ضمیمه کنید.')

        # اعتبارسنجی جایگزین
        if replacement_person and self.user and replacement_person == self.user:
            raise forms.ValidationError('نمی‌توانید خودتان را به عنوان جایگزین انتخاب کنید.')

        return cleaned_data


class RejectLeaveForm(forms.Form):
    """فرم رد درخواست مرخصی"""
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'لطفاً دلیل رد درخواست را بنویسید...',
            'required': 'required'
        }),
        label='دلیل رد درخواست',
        required=True,
        min_length=10,
        error_messages={
            'required': 'وارد کردن دلیل رد الزامی است',
            'min_length': 'دلیل رد باید حداقل 10 کاراکتر باشد'
        }
    )


class ApprovalHierarchyForm(forms.ModelForm):
    """فرم مدیریت سلسله مراتب تأیید با قابلیت ترکیب چند شرط"""
    
    approver = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(user__is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب تأیید کننده'
        }),
        label='تأیید کننده',
        required=True,
        help_text='تأیید کننده الزامی است'
    )
    
    specific_user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب کاربر خاص (اختیاری)'
        }),
        label='کاربر خاص',
        required=False,
        help_text='برای تعریف تأیید کننده خاص برای یک کاربر مشخص'
    )
    
    work_group = forms.ChoiceField(
        choices=[('', '--- انتخاب کنید ---')] + UserProfile.GROUP_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب گروه کاری'
        }),
        label='گروه کاری',
        required=False
    )
    
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب بخش'
        }),
        label='بخش',
        required=False
    )
    
    part = forms.ModelChoiceField(
        queryset=Part.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب قسمت'
        }),
        label='قسمت',
        required=False
    )
    
    unit_group = forms.ModelChoiceField(
        queryset=UnitGroup.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب گروه واحد'
        }),
        label='گروه واحد',
        required=False
    )
    
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'انتخاب سمت'
        }),
        label='سمت',
        required=False
    )
    
    class Meta:
        model = ApprovalHierarchy
        fields = [
            'approver', 'specific_user', 'work_group', 
            'section', 'part', 'unit_group', 'position'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظیم queryset برای فیلدهای وابسته
        if self.instance and self.instance.pk:
            # اگر بخش انتخاب شده، فقط قسمت‌های آن بخش را نمایش بده
            if self.instance.section:
                self.fields['part'].queryset = Part.objects.filter(section=self.instance.section)
            else:
                self.fields['part'].queryset = Part.objects.all()
            
            # اگر قسمت انتخاب شده، فقط گروه‌های واحد آن قسمت را نمایش بده
            if self.instance.part:
                self.fields['unit_group'].queryset = UnitGroup.objects.filter(part=self.instance.part)
            else:
                self.fields['unit_group'].queryset = UnitGroup.objects.all()
            
            # اگر گروه واحد انتخاب شده، فقط سمت‌های آن گروه را نمایش بده
            if self.instance.unit_group:
                self.fields['position'].queryset = Position.objects.filter(unit_group=self.instance.unit_group)
            else:
                self.fields['position'].queryset = Position.objects.all()
        else:
            # برای فرم جدید، همه گزینه‌ها را نمایش بده
            self.fields['part'].queryset = Part.objects.all()
            self.fields['unit_group'].queryset = UnitGroup.objects.all()
            self.fields['position'].queryset = Position.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        section = cleaned_data.get('section')
        part = cleaned_data.get('part')
        unit_group = cleaned_data.get('unit_group')
        position = cleaned_data.get('position')
        
        # بررسی اینکه اگر part انتخاب شده، باید section آن را هم داشته باشد
        if part and section:
            if part.section != section:
                raise forms.ValidationError('قسمت انتخاب شده متعلق به بخش انتخاب شده نیست.')
        
        # بررسی اینکه اگر unit_group انتخاب شده، باید part آن را هم داشته باشد
        if unit_group and part:
            if unit_group.part != part:
                raise forms.ValidationError('گروه واحد انتخاب شده متعلق به قسمت انتخاب شده نیست.')
        
        # بررسی اینکه اگر position انتخاب شده، باید unit_group آن را هم داشته باشد
        if position and unit_group:
            if position.unit_group != unit_group:
                raise forms.ValidationError('سمت انتخاب شده متعلق به گروه واحد انتخاب شده نیست.')
        
        # بررسی اینکه حداقل یک معیار (به جز approver) انتخاب شده باشد
        has_criteria = any([
            cleaned_data.get('specific_user'),
            cleaned_data.get('work_group'),
            cleaned_data.get('section'),
            cleaned_data.get('part'),
            cleaned_data.get('unit_group'),
            cleaned_data.get('position'),
        ])
        
        if not has_criteria:
            raise forms.ValidationError(
                'باید حداقل یکی از فیلدهای معیار (کاربر خاص، گروه کاری، بخش، قسمت، گروه واحد، یا سمت) را انتخاب کنید.'
            )
        
        return cleaned_data


class LeaveSearchForm(forms.Form):
    """فرم جستجو در آرشیو مرخصی‌ها"""
    
    user_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'نام یا نام خانوادگی'
        }),
        label='جستجو کاربر'
    )
    
    personnel_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'کد پرسنلی'
        }),
        label='کد پرسنلی'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'همه وضعیت‌ها')] + list(ShiftReport.STATUS_CHOICES),
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
        }),
        label='وضعیت'
    )
    
    leave_type = forms.ChoiceField(
        required=False,
        choices=[('', 'همه انواع')] + list(ShiftReport.LEAVE_TYPE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
        }),
        label='نوع مرخصی'
    )
    
    date_from = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500 jalali-date',
            'placeholder': '1403/01/01',
            'dir': 'ltr'
        }),
        label='از تاریخ'
    )
    
    date_to = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500 jalali-date',
            'placeholder': '1403/12/29',
            'dir': 'ltr'
        }),
        label='تا تاریخ'
    )
    
    shift_type = forms.ChoiceField(
        required=False,
        choices=[('', 'همه شیفت‌ها')] + list(ShiftReport.SHIFT_TYPE_CHOICES),
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500'
        }),
        label='نوع شیفت'
    )
    
    work_group = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': 'نام گروه کاری'
        }),
        label='گروه کاری'
    )
