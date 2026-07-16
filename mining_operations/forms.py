from django import forms
from django.db.models import Q
from django.utils import timezone
from datetime import date as date_type, datetime
import logging
import jdatetime
from crispy_forms.helper import FormHelper

from .models import (
    DumpCountEvent,
    DumpCountSession,
    LoadingHaulingReport,
    MachineActivity,
    ShiftChoices,
)
from BaseInfo.models import MiningMachine
from BaseInfo.models import MiningBlock, Dump, MineralType
from accounts.models import UserProfile
from shift_manager.utils import get_current_shift_and_group

logger = logging.getLogger(__name__)

INPUT_CLASS = (
    'w-full rounded-xl border border-gray-300 dark:border-gray-600 '
    'bg-white dark:bg-gray-900 px-4 py-3.5 text-base shadow-sm '
    'focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition'
)


def build_time_choices(step_minutes=15):
    choices = [('', '---')]
    for hour in range(24):
        for minute in range(0, 60, step_minutes):
            label = f'{hour:02d}:{minute:02d}'
            choices.append((label, label))
    return choices


def normalize_digits(value):
    if not value:
        return value
    map_digits = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    }
    return str(value).replace('٫', ':').replace('،', ':').replace('٫', ':').translate(str.maketrans(map_digits))


def get_default_shift():
    now = timezone.localtime().hour
    if 6 <= now < 12:
        return ShiftChoices.A
    if 12 <= now < 18:
        return ShiftChoices.B
    if 18 <= now <= 23:
        return ShiftChoices.C
    return ShiftChoices.D


def get_shift_from_manager(user=None):
    shift_label, group = get_current_shift_and_group(user)
    if group in {'A', 'B', 'C', 'D'}:
        return group
    return None


def parse_jalali_date(value):
    if isinstance(value, date_type):
        return value
    if not value:
        return value
    raw = str(value).strip()
    if not raw:
        return value
    try:
        if '/' in raw:
            parts = raw.split('/')
        else:
            parts = raw.split('-')
        if len(parts) != 3:
            return value
        year, month, day = [int(p) for p in parts]
    except Exception:
        return value

    # Heuristic: Jalali years are usually < 1700 in this system
    if year < 1700:
        return jdatetime.date(year, month, day).togregorian()
    return date_type(year, month, day)


def format_jalali_date(value):
    if not value:
        return ''
    if isinstance(value, date_type):
        return jdatetime.date.fromgregorian(date=value).strftime('%Y/%m/%d')
    return str(value)


class MachineActivityForm(forms.ModelForm):
    date = forms.CharField()
    operator_name = forms.ChoiceField(label='نام اپراتور')
    start_hour = forms.CharField(
        label='ساعت شروع',
        required=False,
        widget=forms.TextInput(attrs={'class': f'{INPUT_CLASS} ptimepicker', 'placeholder': 'HH:mm'}),
    )
    end_hour = forms.CharField(
        label='ساعت پایان',
        required=False,
        widget=forms.TextInput(attrs={'class': f'{INPUT_CLASS} ptimepicker', 'placeholder': 'HH:mm'}),
    )
    class Meta:
        model = MachineActivity
        fields = [
            'machine',
            'date',
            'shift',
            'operator_name',
            'start_hour',
            'end_hour',
            'ready_hours',
            'work_hours',
            'stop_hours',
            'stop_reason',
            'stop_description',
        ]
        widgets = {
            'machine': forms.Select(attrs={'class': INPUT_CLASS}),
            'date': forms.DateInput(attrs={'class': f'{INPUT_CLASS} jalali-date', 'placeholder': 'YYYY/MM/DD'}),
            'shift': forms.Select(attrs={'class': INPUT_CLASS}),
            'operator_name': forms.Select(attrs={'class': f'{INPUT_CLASS} select2-personnel', 'data-placeholder': 'انتخاب اپراتور'}),
            'ready_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.25', 'min': '0'}),
            'work_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.25', 'min': '0'}),
            'stop_hours': forms.NumberInput(attrs={'class': INPUT_CLASS, 'step': '0.25', 'min': '0'}),
            'stop_reason': forms.Select(attrs={'class': INPUT_CLASS}),
            'stop_description': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'شرح علت توقف (اختیاری)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        shift = kwargs.pop('shift', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.fields['machine'].queryset = (
            MiningMachine.objects.filter(is_active=True)
            .select_related('machine_type')
            .order_by('workshop_code')
        )

        if not self.is_bound:
            if self.instance.pk:
                self.fields['date'].initial = format_jalali_date(self.instance.date)
            else:
                self.fields['date'].initial = format_jalali_date(timezone.localdate())
                self.fields['shift'].initial = get_default_shift()

        self.fields['stop_reason'].required = False
        self.fields['stop_description'].required = False

        if not shift:
            shift = self.data.get('shift') or self.initial.get('shift')
        operator_choices = DumpCountSessionForm._get_personnel_choices(shift, user, role=None)
        self.fields['operator_name'].choices = operator_choices

        if user and hasattr(user, 'userprofile'):
            profile = user.userprofile
            default_label = DumpCountSessionForm._format_personnel_label(profile)
            available_values = {value for value, _ in operator_choices}
            if default_label in available_values:
                self.fields['operator_name'].initial = default_label

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['date'] = parse_jalali_date(cleaned_data.get('date'))
        ready_hours = cleaned_data.get('ready_hours') or 0
        work_hours = cleaned_data.get('work_hours') or 0
        stop_hours = cleaned_data.get('stop_hours') or 0

        if ready_hours + work_hours + stop_hours > 24:
            raise forms.ValidationError('مجموع ساعات وارد شده نباید بیشتر از 24 باشد.')

        if stop_hours > 0 and not (cleaned_data.get('stop_reason') or cleaned_data.get('stop_description')):
            raise forms.ValidationError('برای ثبت توقف، تعیین علت توقف الزامی است.')

        return cleaned_data

    def clean_start_hour(self):
        raw_value = self.cleaned_data.get('start_hour')
        value = normalize_digits(raw_value)
        if not value:
            return None
        value = value.strip()
        try:
            return datetime.strptime(value, '%H:%M').time()
        except ValueError:
            try:
                return datetime.strptime(value, '%H:%M:%S').time()
            except ValueError:
                logger.warning("Invalid start_hour format. raw=%r normalized=%r", raw_value, value)
                raise forms.ValidationError('یک زمان معتبر وارد کنید.')

    def clean_end_hour(self):
        raw_value = self.cleaned_data.get('end_hour')
        value = normalize_digits(raw_value)
        if not value:
            return None
        value = value.strip()
        try:
            return datetime.strptime(value, '%H:%M').time()
        except ValueError:
            try:
                return datetime.strptime(value, '%H:%M:%S').time()
            except ValueError:
                logger.warning("Invalid end_hour format. raw=%r normalized=%r", raw_value, value)
                raise forms.ValidationError('یک زمان معتبر وارد کنید.')


class LoadingHaulingReportForm(forms.ModelForm):
    date = forms.CharField()
    class Meta:
        model = LoadingHaulingReport
        fields = [
            'loader_machine',
            'loader_operator_name',
            'dumper_machine',
            'dumper_operator_name',
            'date',
            'shift',
            'material_type',
            'block',
            'dump',
            'service_count',
        ]
        widgets = {
            'loader_machine': forms.Select(attrs={'class': INPUT_CLASS}),
            'loader_operator_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'نام بارکننده'}),
            'dumper_machine': forms.Select(attrs={'class': INPUT_CLASS}),
            'dumper_operator_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'نام راننده دامپ'}),
            'date': forms.DateInput(attrs={'class': f'{INPUT_CLASS} jalali-date', 'placeholder': 'YYYY/MM/DD'}),
            'shift': forms.Select(attrs={'class': INPUT_CLASS}),
            'material_type': forms.Select(attrs={'class': INPUT_CLASS}),
            'block': forms.Select(attrs={'class': INPUT_CLASS}),
            'dump': forms.Select(attrs={'class': INPUT_CLASS}),
            'service_count': forms.NumberInput(attrs={'class': INPUT_CLASS, 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        active_machines = MiningMachine.objects.filter(is_active=True).select_related(
            'machine_type',
            'machine_workgroup',
            'machine_type__machine_workgroup',
        )

        loader_filter = (
            Q(machine_type__name__icontains='لودر')
            | Q(machine_type__name__icontains='بیل')
            | Q(machine_type__name__icontains='بارکننده')
            | Q(machine_workgroup__name__icontains='بارکننده')
            | Q(machine_type__machine_workgroup__name__icontains='بارکننده')
        )
        dumper_filter = (
            Q(machine_type__name__icontains='دامپ')
            | Q(machine_type__name__icontains='دامپتراک')
            | Q(machine_type__name__icontains='تراک')
            | Q(machine_workgroup__name__icontains='حمل')
            | Q(machine_type__machine_workgroup__name__icontains='حمل')
        )

        loader_qs = active_machines.filter(loader_filter).order_by('workshop_code').distinct()
        dumper_qs = active_machines.filter(dumper_filter).order_by('workshop_code').distinct()

        self.fields['loader_machine'].queryset = loader_qs if loader_qs.exists() else active_machines.order_by('workshop_code')
        self.fields['dumper_machine'].queryset = dumper_qs if dumper_qs.exists() else active_machines.order_by('workshop_code')
        self.fields['block'].queryset = MiningBlock.objects.filter(is_active=True).order_by('block_name')
        self.fields['dump'].queryset = Dump.objects.filter(is_active=True).order_by('dump_name')
        self.fields['block'].required = True
        self.fields['dump'].required = True

        if not self.is_bound:
            if self.instance.pk:
                self.fields['date'].initial = format_jalali_date(self.instance.date)
            else:
                self.fields['date'].initial = format_jalali_date(timezone.localdate())
                self.fields['shift'].initial = get_default_shift()

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['date'] = parse_jalali_date(cleaned_data.get('date'))
        loader_machine = cleaned_data.get('loader_machine')
        dumper_machine = cleaned_data.get('dumper_machine')

        if loader_machine and dumper_machine and loader_machine == dumper_machine:
            raise forms.ValidationError('ماشین بارکننده و حمل کننده نباید یکسان باشند.')

        return cleaned_data


class DumpCountSessionForm(forms.ModelForm):
    date = forms.CharField()
    counter_name = forms.ChoiceField(label='نام کنترچی')
    loader_operator_name = forms.ChoiceField(required=False, label='نام راننده/بارکننده')

    class Meta:
        model = DumpCountSession
        fields = [
            'date',
            'shift',
            'mineral_type',
            'block',
            'dump',
            'loader_machine',
            'counter_name',
            'loader_operator_name',
            'start_time',
            'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': f'{INPUT_CLASS} jalali-date', 'placeholder': 'YYYY/MM/DD'}),
            'shift': forms.Select(attrs={'class': INPUT_CLASS}),
            'mineral_type': forms.Select(attrs={'class': INPUT_CLASS}),
            'block': forms.Select(attrs={'class': INPUT_CLASS}),
            'dump': forms.Select(attrs={'class': INPUT_CLASS}),
            'loader_machine': forms.Select(attrs={'class': INPUT_CLASS}),
            'counter_name': forms.Select(attrs={'class': f'{INPUT_CLASS} select2-personnel', 'data-placeholder': 'انتخاب کنترچی'}),
            'loader_operator_name': forms.Select(attrs={'class': f'{INPUT_CLASS} select2-personnel', 'data-placeholder': 'انتخاب راننده/بارکننده'}),
            'start_time': forms.TimeInput(attrs={'class': INPUT_CLASS, 'type': 'time'}),
            'notes': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'توضیح کوتاه (اختیاری)'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        shift = kwargs.pop('shift', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        counter_choices = self._get_personnel_choices(shift, user, role='counter')
        loader_choices = self._get_personnel_choices(shift, user, role='loader_operator')
        self.fields['counter_name'].choices = counter_choices
        self.fields['loader_operator_name'].choices = [('', '---')] + loader_choices[1:]

        if not self.is_bound:
            if self.instance.pk:
                self.fields['date'].initial = format_jalali_date(self.instance.date)
            else:
                self.fields['date'].initial = format_jalali_date(timezone.localdate())
                shift_from_manager = get_shift_from_manager(user)
                self.fields['shift'].initial = shift_from_manager or get_default_shift()
                self.fields['start_time'].initial = timezone.localtime().strftime('%H:%M')
        self.fields['block'].queryset = MiningBlock.objects.filter(is_active=True).order_by('block_name')
        self.fields['dump'].queryset = Dump.objects.filter(is_active=True).order_by('dump_name')
        self.fields['mineral_type'].queryset = MineralType.objects.all().order_by('name')
        self.fields['mineral_type'].required = True
        self.fields['block'].required = True
        self.fields['dump'].required = True
        self.fields['loader_machine'].queryset = self._get_loader_machines()
        self.fields['loader_machine'].required = True

        if user and hasattr(user, 'userprofile'):
            profile = user.userprofile
            default_label = self._format_personnel_label(profile)
            available_values = {value for value, _ in counter_choices}
            if default_label in available_values:
                self.fields['counter_name'].initial = default_label

    @classmethod
    def _get_personnel_choices(cls, shift, user, role=None):
        qs = UserProfile.objects.select_related('user').filter(user__is_active=True)
        if shift in {'A', 'B', 'C', 'D'}:
            qs = qs.filter(group=shift)
        else:
            qs = qs.filter(group__in=['A', 'B', 'C', 'D'])

        role_keywords = {
            'counter': [
                'کنترل چی',
                'کنترلچی',
                'کنترچی',
                'کنترل‌چی',
                'کنترلچي',
                'کنترچي',
            ],
            'loader_operator': [
                'اپراتور شاول',
                'اپراتور بیل شاول',
                'اپراتور لودر',
                'اپراتور بیل مکانیکی',
                'اپراتور بیل مکانیکی و چکش',
                'اپراتور بیل',
                'بارکننده',
                'اپراتور بارکننده',
                'بارگیری',
                'دستگاه بارگیری',
            ],
            'driver': [
                'اپراتور دامپتراک',
                'اپراتور دامپ تراک',
                'اپراتور دامپتراک 80 تن',
                'اپراتور دامپتراک 80تنی',
                'دامپتراک',
                'کامیون معدنی',
            ],
        }

        if role in role_keywords and role != 'counter':
            position_filter = Q()
            for key in role_keywords[role]:
                position_filter |= Q(position__name__icontains=key)
            qs = qs.filter(position_filter)

        qs = qs.order_by('user__first_name', 'user__last_name', 'personnel_code')
        choices = [('', 'انتخاب کنید...')]
        seen = set()

        for profile in qs:
            if role in role_keywords:
                if not cls._profile_matches_role(profile, role_keywords[role]):
                    continue
            label = cls._format_personnel_label(profile)
            if label not in seen:
                choices.append((label, label))
                seen.add(label)

        # Only include current user if they match the role filter (or no role filter)
        if user and hasattr(user, 'userprofile'):
            profile = user.userprofile
            should_include = True
            if role in role_keywords:
                should_include = cls._profile_matches_role(profile, role_keywords[role])
            if should_include:
                label = cls._format_personnel_label(profile)
                if label and label not in seen:
                    choices.insert(1, (label, label))

        return choices

    @staticmethod
    def _profile_matches_role(profile, keywords):
        if not profile or not profile.position or not profile.position.name:
            return False
        name = profile.position.name
        normalized = (
            name.replace('‌', '').replace(' ', '').replace('/', '')
            .replace('ي', 'ی').replace('ك', 'ک')
        )
        for key in keywords:
            key_norm = (
                key.replace('‌', '').replace(' ', '').replace('/', '')
                .replace('ي', 'ی').replace('ك', 'ک')
            )
            if key_norm and key_norm in normalized:
                return True
        return False

    @staticmethod
    def _get_loader_machines():
        active_machines = MiningMachine.objects.filter(is_active=True).select_related(
            'machine_type',
            'machine_workgroup',
            'machine_type__machine_workgroup',
        )
        loader_filter = (
            Q(machine_type__name__icontains='لودر')
            | Q(machine_type__name__icontains='بیل')
            | Q(machine_type__name__icontains='بارکننده')
            | Q(machine_workgroup__name__icontains='بارکننده')
            | Q(machine_type__machine_workgroup__name__icontains='بارکننده')
        )
        loader_qs = active_machines.filter(loader_filter).order_by('workshop_code').distinct()
        return loader_qs if loader_qs.exists() else active_machines.order_by('workshop_code')

    @staticmethod
    def _format_personnel_label(profile):
        name = profile.user.get_full_name() or profile.user.username
        code = profile.personnel_code or ''
        return f'{name} ({code})' if code else name

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['date'] = parse_jalali_date(cleaned_data.get('date'))
        return cleaned_data


class DumpCountEventForm(forms.ModelForm):
    driver_name = forms.ChoiceField(required=False, label='نام راننده')
    class Meta:
        model = DumpCountEvent
        fields = ['dumper_machine', 'driver_name', 'note']
        widgets = {
            'dumper_machine': forms.Select(attrs={'class': INPUT_CLASS}),
            'driver_name': forms.Select(attrs={'class': f'{INPUT_CLASS} select2-personnel', 'data-placeholder': 'انتخاب راننده'}),
            'note': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'توضیح (اختیاری)'}),
        }

    def __init__(self, *args, **kwargs):
        session = kwargs.pop('session', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

        dumper_filter = (
            Q(machine_type__name__icontains='دامپ')
            | Q(machine_type__name__icontains='دامپتراک')
            | Q(machine_type__name__icontains='تراک')
            | Q(machine_workgroup__name__icontains='حمل')
            | Q(machine_type__machine_workgroup__name__icontains='حمل')
        )
        active_machines = MiningMachine.objects.filter(is_active=True).select_related(
            'machine_type', 'machine_workgroup', 'machine_type__machine_workgroup'
        )
        dumper_qs = active_machines.filter(dumper_filter).order_by('workshop_code').distinct()
        self.fields['dumper_machine'].queryset = dumper_qs if dumper_qs.exists() else active_machines.order_by('workshop_code')
        self.fields['dumper_machine'].required = False

        shift = session.shift if session else None
        personnel_choices = DumpCountSessionForm._get_personnel_choices(shift, user, role='driver')
        self.fields['driver_name'].choices = [('', 'انتخاب کنید...')] + personnel_choices[1:]
