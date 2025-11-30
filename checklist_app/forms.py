from django import forms
from .models import ChecklistSchedule
from BaseInfo.models import MiningMachine
from anomalis.models import LocationSection
from contractor_management.models import Vehicle


class ChecklistScheduleForm(forms.ModelForm):
    """فرم ایجاد و ویرایش برنامه زمان‌بندی چک‌لیست"""
    
    # فیلدهای پویا برای روزهای ماه
    monthly_days_input = forms.CharField(
        required=False,
        label="روزهای ماه",
        help_text="روزهای ماه را با کاما جدا کنید (مثلاً: 1, 15, 30)",
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            'placeholder': 'مثلاً: 1, 15'
        })
    )
    
    # فیلد پنهان برای ذخیره تاریخ‌های انتخاب شده
    specific_dates_input = forms.CharField(
        required=False,
        label="تاریخ‌های مشخص",
        help_text="تاریخ‌ها را با datepicker انتخاب کنید",
        widget=forms.HiddenInput()
    )
    
    # فیلدهای چند انتخابی برای هدف
    target_machines = forms.ModelMultipleChoiceField(
        queryset=MiningMachine.objects.filter(is_active=True),
        required=False,
        label="ماشین‌های هدف",
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            'multiple': 'multiple'
        })
    )
    
    target_location_sections = forms.ModelMultipleChoiceField(
        queryset=LocationSection.objects.all(),
        required=False,
        label="بخش‌های مکانی هدف",
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            'multiple': 'multiple'
        })
    )
    
    target_contractor_vehicles = forms.ModelMultipleChoiceField(
        queryset=Vehicle.objects.all(),
        required=False,
        label="ماشین‌های پیمانکار هدف",
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            'multiple': 'multiple'
        })
    )
    
    class Meta:
        model = ChecklistSchedule
        fields = [
            'name',
            'checklist_type',
            'schedule_type',
            'target_machine',
            'target_location_section',
            'target_contractor_vehicle',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
                'placeholder': 'نام برنامه (مثلاً: چک‌لیست ماهانه ماشین A)'
            }),
            'checklist_type': forms.Select(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            }),
            'schedule_type': forms.Select(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            }),
            'target_machine': forms.Select(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            }),
            'target_location_section': forms.Select(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            }),
            'target_contractor_vehicle': forms.Select(attrs={
                'class': 'w-full rounded-md border border-gray-300 px-3 py-2',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-indigo-600 rounded'
            }),
        }
        labels = {
            'name': 'نام برنامه',
            'checklist_type': 'نوع چک‌لیست',
            'schedule_type': 'نوع برنامه‌ریزی',
            'target_machine': 'ماشین هدف',
            'target_location_section': 'بخش مکانی هدف',
            'target_contractor_vehicle': 'ماشین پیمانکار هدف',
            'is_active': 'فعال',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تنظیم queryset برای فیلدهای هدف (قدیمی)
        self.fields['target_machine'].queryset = MiningMachine.objects.filter(is_active=True)
        self.fields['target_location_section'].queryset = LocationSection.objects.all()
        # مدل Vehicle فیلد is_active ندارد، پس از all() استفاده می‌کنیم
        self.fields['target_contractor_vehicle'].queryset = Vehicle.objects.all()
        
        # تنظیم queryset برای فیلدهای چند انتخابی (جدید)
        self.fields['target_machines'].queryset = MiningMachine.objects.filter(is_active=True)
        self.fields['target_location_sections'].queryset = LocationSection.objects.all()
        self.fields['target_contractor_vehicles'].queryset = Vehicle.objects.all()
        
        # اگر instance وجود دارد، مقادیر JSON را به رشته تبدیل می‌کنیم
        if self.instance and self.instance.pk:
            if self.instance.monthly_days:
                self.fields['monthly_days_input'].initial = ', '.join(map(str, self.instance.monthly_days))
            if self.instance.specific_dates:
                # تبدیل لیست تاریخ‌ها به رشته با کاما
                self.fields['specific_dates_input'].initial = ', '.join(self.instance.specific_dates)
            
            # بارگذاری مقادیر چند انتخابی از JSONField
            if self.instance.target_machines:
                self.fields['target_machines'].initial = self.instance.target_machines
            if self.instance.target_location_sections:
                self.fields['target_location_sections'].initial = self.instance.target_location_sections
            if self.instance.target_contractor_vehicles:
                self.fields['target_contractor_vehicles'].initial = self.instance.target_contractor_vehicles
    
    def clean_monthly_days_input(self):
        """تبدیل رشته به لیست اعداد"""
        data = self.cleaned_data.get('monthly_days_input', '')
        if not data:
            return []
        
        try:
            days = [int(day.strip()) for day in data.split(',') if day.strip()]
            # اعتبارسنجی: روزها باید بین 1 تا 31 باشند
            for day in days:
                if day < 1 or day > 31:
                    raise forms.ValidationError(f'روز {day} نامعتبر است. روزها باید بین 1 تا 31 باشند.')
            return days
        except ValueError:
            raise forms.ValidationError('لطفاً روزهای ماه را به صورت عدد وارد کنید (مثلاً: 1, 15, 30)')
    
    def clean_specific_dates_input(self):
        """تبدیل رشته به لیست تاریخ‌ها"""
        data = self.cleaned_data.get('specific_dates_input', '')
        if not data:
            return []
        
        dates = []
        for date_str in data.split(','):
            date_str = date_str.strip()
            if not date_str:
                continue
            
            # اعتبارسنجی فرمت تاریخ (پشتیبانی از YYYY-MM-DD)
            try:
                from datetime import datetime
                # تبدیل تاریخ شمسی به میلادی اگر نیاز باشد
                datetime.strptime(date_str, '%Y-%m-%d')
                dates.append(date_str)
            except ValueError:
                # اگر فرمت YYYY-MM-DD نبود، سعی می‌کنیم تاریخ شمسی را تبدیل کنیم
                try:
                    import jdatetime
                    # فرض می‌کنیم فرمت YYYY/MM/DD است (شمسی)
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        jdate = jdatetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                        gdate = jdate.togregorian()
                        dates.append(gdate.strftime('%Y-%m-%d'))
                    else:
                        raise forms.ValidationError(f'تاریخ "{date_str}" نامعتبر است. فرمت صحیح: YYYY-MM-DD یا YYYY/MM/DD')
                except:
                    raise forms.ValidationError(f'تاریخ "{date_str}" نامعتبر است. فرمت صحیح: YYYY-MM-DD یا YYYY/MM/DD')
        
        return dates
    
    def clean(self):
        cleaned_data = super().clean()
        checklist_type = cleaned_data.get('checklist_type')
        schedule_type = cleaned_data.get('schedule_type')
        
        # اعتبارسنجی نوع چک‌لیست و هدف (استفاده از فیلدهای جدید چند انتخابی)
        if checklist_type == 'machine':
            target_machines = cleaned_data.get('target_machines', [])
            if not target_machines:
                raise forms.ValidationError({'target_machines': 'برای چک‌لیست ماشین، باید حداقل یک ماشین هدف انتخاب شود.'})
        elif checklist_type == 'location':
            target_location_sections = cleaned_data.get('target_location_sections', [])
            if not target_location_sections:
                raise forms.ValidationError({'target_location_sections': 'برای چک‌لیست مکان، باید حداقل یک بخش مکانی هدف انتخاب شود.'})
        elif checklist_type == 'contractor_vehicle':
            target_contractor_vehicles = cleaned_data.get('target_contractor_vehicles', [])
            if not target_contractor_vehicles:
                raise forms.ValidationError({'target_contractor_vehicles': 'برای چک‌لیست ماشین‌آلات پیمانکار، باید حداقل یک ماشین پیمانکار هدف انتخاب شود.'})
        
        # اعتبارسنجی نوع برنامه‌ریزی
        if schedule_type == 'monthly_days':
            monthly_days = cleaned_data.get('monthly_days_input', [])
            if not monthly_days:
                raise forms.ValidationError({'monthly_days_input': 'برای برنامه‌ریزی ماهانه، باید حداقل یک روز ماه مشخص شود.'})
            cleaned_data['monthly_days'] = monthly_days
            cleaned_data['specific_dates'] = []
        
        elif schedule_type == 'specific_dates':
            specific_dates = cleaned_data.get('specific_dates_input', [])
            if not specific_dates:
                raise forms.ValidationError({'specific_dates_input': 'برای برنامه‌ریزی با تاریخ‌های مشخص، باید حداقل یک تاریخ وارد شود.'})
            cleaned_data['specific_dates'] = specific_dates
            cleaned_data['monthly_days'] = []
        
        elif schedule_type == 'weekly':
            cleaned_data['monthly_days'] = []
            cleaned_data['specific_dates'] = []
        
        return cleaned_data
    
    def _post_clean(self):
        """
        Override _post_clean to set JSONField values before model.clean() is called
        """
        # تنظیم فیلدهای JSON روی instance قبل از clean() مدل
        instance = self.instance
        
        # تنظیم فیلدهای JSON
        if self.cleaned_data.get('monthly_days'):
            instance.monthly_days = self.cleaned_data['monthly_days']
        if self.cleaned_data.get('specific_dates'):
            instance.specific_dates = self.cleaned_data['specific_dates']
        
        # تنظیم فیلدهای JSON برای چندین انتخاب
        checklist_type = self.cleaned_data.get('checklist_type')
        if checklist_type == 'machine':
            target_machines = self.cleaned_data.get('target_machines', [])
            instance.target_machines = [m.id for m in target_machines] if target_machines else []
        elif checklist_type == 'location':
            target_location_sections = self.cleaned_data.get('target_location_sections', [])
            instance.target_location_sections = [l.id for l in target_location_sections] if target_location_sections else []
        elif checklist_type == 'contractor_vehicle':
            target_contractor_vehicles = self.cleaned_data.get('target_contractor_vehicles', [])
            instance.target_contractor_vehicles = [v.id for v in target_contractor_vehicles] if target_contractor_vehicles else []
        
        # حالا super()._post_clean() را صدا می‌زنیم که clean() مدل را فراخوانی می‌کند
        # در این مرحله مقادیر JSONField قبلاً تنظیم شده‌اند
        super()._post_clean()
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # تنظیم فیلدهای JSON (برای اطمینان)
        if self.cleaned_data.get('monthly_days'):
            instance.monthly_days = self.cleaned_data['monthly_days']
        if self.cleaned_data.get('specific_dates'):
            instance.specific_dates = self.cleaned_data['specific_dates']
        
        checklist_type = self.cleaned_data.get('checklist_type')
        if checklist_type == 'machine':
            target_machines = self.cleaned_data.get('target_machines', [])
            instance.target_machines = [m.id for m in target_machines] if target_machines else []
        elif checklist_type == 'location':
            target_location_sections = self.cleaned_data.get('target_location_sections', [])
            instance.target_location_sections = [l.id for l in target_location_sections] if target_location_sections else []
        elif checklist_type == 'contractor_vehicle':
            target_contractor_vehicles = self.cleaned_data.get('target_contractor_vehicles', [])
            instance.target_contractor_vehicles = [v.id for v in target_contractor_vehicles] if target_contractor_vehicles else []
        
        if commit:
            instance.save()
            # ایجاد instances برای این schedule
            from .services import create_instances_for_schedule
            create_instances_for_schedule(instance)
        
        return instance

