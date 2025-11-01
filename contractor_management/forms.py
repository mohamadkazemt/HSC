# forms.py
from django import forms
from .models import Report, Vehicle, Contractor, Employee
from django.core.exceptions import ValidationError
from django.forms import Select
# Persian date imports removed
import re
import logging
from django.utils.translation import gettext_lazy as _

# تنظیم لاگر
logger = logging.getLogger(__name__)

def persian_to_english_numbers(string):
    """تبدیل اعداد فارسی به انگلیسی"""
    persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
    english_numbers = '0123456789'
    translation_table = str.maketrans(persian_numbers, english_numbers)
    return string.translate(translation_table)

# تعریف گزینه‌های شیفت
SHIFT_CHOICES = [
    ('', '-- انتخاب شیفت --'),
    ('روزکار اول', 'روزکار اول'),
    ('روزکار دوم', 'روزکار دوم'),
    ('عصرکار اول', 'عصرکار اول'),
    ('عصرکار دوم', 'عصرکار دوم'),
    ('شب کار اول', 'شب کار اول'),
    ('شب کار دوم', 'شب کار دوم'),
    ('OFF اول', 'OFF اول'),
    ('OFF دوم', 'OFF دوم'),
]

class ReportForm(forms.ModelForm):
    report_date = forms.CharField(
        label='تاریخ گزارش',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_report_date',
            'name': 'report_date',
            'placeholder': 'مثال: 1402/12/29',
            'autocomplete': 'off',
            'required': True
        }),
        required=True,
        error_messages={
            'required': 'لطفاً تاریخ را وارد کنید',
            'invalid': 'لطفاً تاریخ را به فرمت صحیح وارد کنید (مثال: 1402/12/29)'
        }
    )
    shift = forms.ChoiceField(
        label='شیفت',
        choices=SHIFT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False  # اجازه می‌دهد که شیفت به صورت خودکار تنظیم شود
    )

    class Meta:
        model = Report
        fields = ['vehicle', 'status', 'stop_start_time', 'stop_end_time', 'description', 'report_date']
        widgets = {
            'stop_start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'stop_end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control vehicle-select'}),
        }

    def clean_report_date(self):
        """اعتبارسنجی تاریخ - Persian date validation removed"""
        date_str = self.cleaned_data.get('report_date')
        
        if not date_str:
            raise ValidationError('لطفاً تاریخ را وارد کنید')
        
        # Simple validation - Persian date processing removed
        return date_str

    def __init__(self, *args, **kwargs):
        super(ReportForm, self).__init__(*args, **kwargs)
        logger.info(f"مقادیر اولیه فرم: {args}")

        for field_name, field in self.fields.items():
            if not isinstance(field.widget, dict):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})

        self.fields['stop_start_time'].required = False
        self.fields['stop_end_time'].required = False
        self.fields['description'].required = False

        # حالت اولیه: نمایش *همه* خودروها
        self.fields['vehicle'].queryset = Vehicle.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        logger.info(f"داده‌های تمیز شده در clean: {cleaned_data}")
        
        status = cleaned_data.get('status')
        stop_start_time = cleaned_data.get('stop_start_time')
        stop_end_time = cleaned_data.get('stop_end_time')
        description = cleaned_data.get('description')

        if status == 'full':
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
            cleaned_data['description'] = None

        elif status == 'partial':
            if not stop_start_time:
                self.add_error('stop_start_time', "لطفاً ساعت شروع توقف را وارد کنید.")
            if not stop_end_time:
                self.add_error('stop_end_time', "لطفاً ساعت پایان توقف را وارد کنید.")
            if not description:
                self.add_error('description', "لطفاً توضیحات را وارد کنید.")

        elif status == 'inactive':
            if not description:
                self.add_error('description', "لطفاً توضیحات را برای حالت غیر فعال وارد کنید.")
            cleaned_data['stop_start_time'] = None
            cleaned_data['stop_end_time'] = None
        
        logger.info(f"داده‌های نهایی پس از اعتبارسنجی: {cleaned_data}")
        return cleaned_data

class ReportFilterForm(forms.Form):
    start_date = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'تاریخ شروع'}
        )
    )
    end_date = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'تاریخ پایان'}
        )
    )
    contractor = forms.ModelChoiceField(
        queryset=Contractor.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="همه پیمانکاران"
    )
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="همه خودروها"
    )
    shift = forms.ChoiceField(
        choices=SHIFT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    group = forms.ChoiceField(
        choices=[('', 'همه گروه‌ها'), ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ContractorForm(forms.ModelForm):
    """Form for creating and editing contractors"""
    
    # Treat date inputs as text to allow Jalali strings and convert in clean_*
    liability_insurance_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    fire_insurance_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    contractor_certificate_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    safety_certificate_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تبدیل تاریخ‌های میلادی به جلالی برای نمایش در حالت ویرایش
        if self.instance and self.instance.pk:
            date_fields = [
                'liability_insurance_expiry',
                'fire_insurance_expiry', 
                'contractor_certificate_expiry',
                'safety_certificate_expiry'
            ]
            for field_name in date_fields:
                gregorian_date = getattr(self.instance, field_name, None)
                if gregorian_date:
                    jalali_str = self._gregorian_to_jalali_str(gregorian_date)
                    self.initial[field_name] = jalali_str
    
    def _gregorian_to_jalali_str(self, gregorian_date):
        """تبدیل تاریخ میلادی به رشته جلالی"""
        try:
            import jdatetime
            if gregorian_date:
                j_date = jdatetime.date.fromgregorian(date=gregorian_date)
                return j_date.strftime('%Y/%m/%d')
        except Exception as e:
            logger.error(f"خطا در تبدیل تاریخ به جلالی: {e}")
        return None

    def clean_liability_insurance_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('liability_insurance_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def clean_fire_insurance_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('fire_insurance_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def clean_contractor_certificate_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('contractor_certificate_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def clean_safety_certificate_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('safety_certificate_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def _convert_persian_date(self, date_str):
        """تبدیل تاریخ جلالی به میلادی"""
        try:
            from datetime import datetime, date
            import jdatetime
            
            # چک برای مقادیر خالی
            if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
                return None
            
            # اگر قبلاً یک date object است
            if isinstance(date_str, date):
                return date_str
            
            # اگر تاریخ string است
            if isinstance(date_str, str):
                # حذف اعداد فارسی
                date_str = persian_to_english_numbers(date_str).strip()
                
                # چک مجدد برای empty string
                if not date_str:
                    return None
                
                # تلاش برای parse کردن به عنوان تاریخ جلالی
                parts = date_str.replace('/', '-').split('-')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    j_date = jdatetime.date(year, month, day)
                    return j_date.togregorian()
            
            return None
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"خطا در تبدیل تاریخ: {date_str}, خطا: {e}")
            return None
    
    class Meta:
        model = Contractor
        fields = [
            'company_name', 'manager_name', 'manager_phone',
            'activity_field', 'liability_insurance_expiry',
            'fire_insurance_expiry', 'contractor_certificate_expiry',
            'safety_certificate_expiry', 'number_of_social_insurance'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام شرکت'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام مدیرعامل'}),
            'manager_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'}),
            'activity_field': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'حوزه فعالیت'}),
            # Widgets for date fields are defined by explicit CharField declarations above
        }
        labels = {
            'company_name': 'نام شرکت',
            'manager_name': 'نام مدیرعامل',
            'manager_phone': 'شماره تماس',
            'activity_field': 'حوزه فعالیت',
            'liability_insurance_expiry': 'تاریخ انقضای بیمه مسئولیت',
            'fire_insurance_expiry': 'تاریخ انقضای بیمه آتش‌سوزی',
            'contractor_certificate_expiry': 'تاریخ انقضای صلاحیت پیمانکاری',
            'safety_certificate_expiry': 'تاریخ انقضای صلاحیت ایمنی',
        }


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees"""
    
    # Accept Jalali input as text, then convert in clean_*
    birth_date = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'مثال: 1370/01/15'}))
    entry_permit_expiration = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تبدیل تاریخ‌های میلادی به جلالی برای نمایش در حالت ویرایش
        if self.instance and self.instance.pk:
            if self.instance.birth_date:
                self.initial['birth_date'] = self._gregorian_to_jalali_str(self.instance.birth_date)
            if self.instance.entry_permit_expiration:
                self.initial['entry_permit_expiration'] = self._gregorian_to_jalali_str(self.instance.entry_permit_expiration)
    
    def _gregorian_to_jalali_str(self, gregorian_date):
        """تبدیل تاریخ میلادی به رشته جلالی"""
        try:
            import jdatetime
            if gregorian_date:
                j_date = jdatetime.date.fromgregorian(date=gregorian_date)
                return j_date.strftime('%Y/%m/%d')
        except Exception as e:
            logger.error(f"خطا در تبدیل تاریخ به جلالی: {e}")
        return None
    
    def clean_birth_date(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('birth_date')
        if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
            raise ValidationError(_('تاریخ تولد الزامی است'))
        
        converted = self._convert_persian_date(date_str)
        if converted is None:
            raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1370/01/15'))
        return converted
    
    def clean_entry_permit_expiration(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('entry_permit_expiration')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def _convert_persian_date(self, date_str):
        """تبدیل تاریخ جلالی به میلادی"""
        try:
            from datetime import datetime, date
            import jdatetime
            
            # چک برای مقادیر خالی
            if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
                return None
            
            # اگر قبلاً یک date object است
            if isinstance(date_str, date):
                return date_str
            
            if isinstance(date_str, str):
                date_str = persian_to_english_numbers(date_str).strip()
                if not date_str:
                    return None
                    
                parts = date_str.replace('/', '-').split('-')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    j_date = jdatetime.date(year, month, day)
                    return j_date.togregorian()
            
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"خطا در تبدیل تاریخ: {date_str}, خطا: {e}")
            return None
    
    class Meta:
        model = Employee
        fields = [
            'contractor', 'first_name', 'last_name', 'national_id',
            'birth_date', 'position', 'phone_number', 'education',
            'number_of_insurance', 'entry_permit_expiration'
        ]
        widgets = {
            'contractor': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'}),
            'birth_date': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'سمت'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'}),
            'education': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مدرک تحصیلی'}),
            'number_of_insurance': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'شماره بیمه'}),
            'entry_permit_expiration': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }
        labels = {
            'contractor': 'پیمانکار',
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'national_id': 'کد ملی',
            'birth_date': 'تاریخ تولد',
            'position': 'سمت',
            'phone_number': 'شماره تماس',
            'education': 'مدرک تحصیلی',
            'number_of_insurance': 'شماره بیمه',
            'entry_permit_expiration': 'تاریخ انقضای مجوز ورود',
        }


class ContractorEmployeeForm(forms.ModelForm):
    """فرم افزودن پرسنل توسط پیمانکار (بدون انتخاب پیمانکار)"""
    # ورودی جلالی به صورت متن؛ تبدیل در clean_birth_date انجام می‌شود
    birth_date = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off', 'placeholder': 'مثال: 1370/01/15'}))

    def clean_birth_date(self):
        date_str = self.cleaned_data.get('birth_date')
        if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
            raise ValidationError(_('تاریخ تولد الزامی است'))
        converted = self._convert_persian_date(date_str)
        if converted is None:
            raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1370/01/15'))
        return converted

    def _convert_persian_date(self, date_str):
        try:
            from datetime import date
            import jdatetime
            # خالی
            if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
                return None
            # اگر قبلاً date است
            if isinstance(date_str, date):
                return date_str
            if isinstance(date_str, str):
                s = persian_to_english_numbers(date_str).strip()
                if not s:
                    return None
                parts = s.replace('/', '-').split('-')
                if len(parts) == 3:
                    y, m, d = map(int, parts)
                    j_date = jdatetime.date(y, m, d)
                    return j_date.togregorian()
            return None
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"خطا در تبدیل تاریخ: {date_str}, خطا: {e}")
            return None

    class Meta:
        model = Employee
        fields = [
            'first_name', 'last_name', 'national_id', 'birth_date', 'position', 'phone_number', 'education', 'number_of_insurance'
        ]


class EmployeeDocumentForm(forms.ModelForm):
    """فرم بارگذاری مدارک پرسنل"""
    class Meta:
        model = Employee
        fields = ['card_national_img', 'certificate_img', 'health_certificate', 'background_check', 'safety_training']
        widgets = {
            'card_national_img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'certificate_img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'health_certificate': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'background_check': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'safety_training': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class ContractorVehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['license_plate', 'vehicle_type', 'vehicle_category', 'vehicle_code', 'driver_name']
        widgets = {
            'license_plate': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_category': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_code': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ContractorUserManagementForm(forms.Form):
    """فرم مدیریت حساب کاربری پیمانکار برای ادمین سایت"""
    from django.contrib.auth.models import User
    username = forms.CharField(required=False, label='نام کاربری', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(required=False, label='رمز عبور', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(required=False, label='تکرار رمز عبور', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    existing_user = forms.ModelChoiceField(required=False, label='انتخاب کاربر موجود', queryset=None, widget=forms.Select(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        super().__init__(*args, **kwargs)
        # فقط کاربرانی که به هیچ پیمانکاری لینک نشده‌اند
        self.fields['existing_user'].queryset = User.objects.filter(contractor_profile__isnull=True)

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        action = (self.data.get('action') or '').strip()
        if action in ['create', 'change_password']:
            if not password or not confirm:
                raise ValidationError('رمز عبور و تکرار آن الزامی است')
            if password != confirm:
                raise ValidationError('رمز عبور و تکرار آن یکسان نیستند')
        return cleaned


class VehicleForm(forms.ModelForm):
    """Form for creating and editing vehicles"""
    
    # Accept Jalali input as text, then convert in clean_*
    insurance_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    technical_inspection_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    permit_expiry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تبدیل تاریخ‌های میلادی به جلالی برای نمایش در حالت ویرایش
        if self.instance and self.instance.pk:
            if self.instance.insurance_expiry:
                self.initial['insurance_expiry'] = self._gregorian_to_jalali_str(self.instance.insurance_expiry)
            if self.instance.technical_inspection_expiry:
                self.initial['technical_inspection_expiry'] = self._gregorian_to_jalali_str(self.instance.technical_inspection_expiry)
            if self.instance.permit_expiry:
                self.initial['permit_expiry'] = self._gregorian_to_jalali_str(self.instance.permit_expiry)
    
    def _gregorian_to_jalali_str(self, gregorian_date):
        """تبدیل تاریخ میلادی به رشته جلالی"""
        try:
            import jdatetime
            if gregorian_date:
                j_date = jdatetime.date.fromgregorian(date=gregorian_date)
                return j_date.strftime('%Y/%m/%d')
        except Exception as e:
            logger.error(f"خطا در تبدیل تاریخ به جلالی: {e}")
        return None
    
    def clean_insurance_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('insurance_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def clean_technical_inspection_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('technical_inspection_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def clean_permit_expiry(self):
        """تبدیل تاریخ جلالی به میلادی"""
        date_str = self.cleaned_data.get('permit_expiry')
        if date_str:
            converted = self._convert_persian_date(date_str)
            if converted is None:
                raise ValidationError(_('فرمت تاریخ نامعتبر است. مثال: 1402/12/29'))
            return converted
        return None
    
    def _convert_persian_date(self, date_str):
        """تبدیل تاریخ جلالی به میلادی"""
        try:
            from datetime import datetime, date
            import jdatetime
            
            # چک برای مقادیر خالی
            if not date_str or (isinstance(date_str, str) and date_str.strip() == ''):
                return None
            
            # اگر قبلاً یک date object است
            if isinstance(date_str, date):
                return date_str
            
            if isinstance(date_str, str):
                date_str = persian_to_english_numbers(date_str).strip()
                if not date_str:
                    return None
                    
                parts = date_str.replace('/', '-').split('-')
                if len(parts) == 3:
                    year, month, day = map(int, parts)
                    j_date = jdatetime.date(year, month, day)
                    return j_date.togregorian()
            
            return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"خطا در تبدیل تاریخ: {date_str}, خطا: {e}")
            return None
    
    class Meta:
        model = Vehicle
        fields = [
            'contractor', 'license_plate', 'vehicle_type', 'vehicle_category',
            'vehicle_code', 'driver_name', 'insurance_expiry',
            'technical_inspection_expiry', 'permit_expiry'
        ]
        widgets = {
            'contractor': forms.Select(attrs={'class': 'form-control'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'پلاک'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع خودرو'}),
            'vehicle_category': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد کارگاهی'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام راننده'}),
            'insurance_expiry': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'technical_inspection_expiry': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'permit_expiry': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
        }
        labels = {
            'contractor': 'پیمانکار',
            'license_plate': 'پلاک',
            'vehicle_type': 'نوع خودرو',
            'vehicle_category': 'دسته‌بندی',
            'vehicle_code': 'کد کارگاهی',
            'driver_name': 'نام راننده',
            'insurance_expiry': 'تاریخ انقضای بیمه',
            'technical_inspection_expiry': 'تاریخ انقضای معاینه فنی',
            'permit_expiry': 'تاریخ انقضای مجوز',
        }
