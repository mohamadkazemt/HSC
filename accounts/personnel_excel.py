from datetime import date, datetime

import jdatetime
import pandas as pd
from django.contrib.auth.models import User
from django.db import transaction

from .models import Part, Position, Section, UnitGroup, UserProfile


EXCEL_COLUMNS = [
    'ردیف',
    'شماره پرسنلی',
    'جنسیت',
    'نام',
    'نام خانوادگی',
    'عنوان شغل کارگاه',
    'عنوان شغل',
    'واحد',
    'بخش',
    'قسمت',
    'گروه',
    'گروه کاری',
    'کد ملی',
    'تاریخ تولد',
    'وضعیت تاهل',
    'نام پدر',
    'تعداد فرزندان',
    'تاریخ استخدام',
    'مقطع تحصیلی',
    'رشته تحصیلی',
    'محل تولد',
    'وضعیت خدمت سربازی',
    'سابقه کار (روز)',
    'شماره تماس',
]

# «ردیف» فقط برای خوانایی فایل است و داده محسوب نمی‌شود.
OPTIONAL_COLUMNS = {'جنسیت'}
REQUIRED_COLUMNS = [column for column in EXCEL_COLUMNS[1:] if column not in OPTIONAL_COLUMNS]

PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')


def clean_value(value):
    if value is None or pd.isna(value):
        return ''
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return ' '.join(str(value).strip().split())


def clean_digits(value):
    return clean_value(value).translate(PERSIAN_DIGITS).translate(ARABIC_DIGITS)


def clean_national_code(value):
    value = clean_digits(value)
    return value.zfill(10) if value.isdigit() and len(value) < 10 else value


def clean_mobile(value):
    value = clean_digits(value)
    if value.isdigit() and len(value) == 10 and value.startswith('9'):
        return f'0{value}'
    return value


def normalize_gender(value):
    value = clean_value(value).lower()
    values = {
        'مرد': 'male', 'مذکر': 'male', 'male': 'male',
        'زن': 'female', 'مونث': 'female', 'مؤنث': 'female', 'female': 'female',
    }
    if not value:
        return ''
    if value not in values:
        raise ValueError('جنسیت باید «مرد» یا «زن» باشد.')
    return values[value]


def clean_non_negative_integer(value, column_name):
    value = clean_digits(value)
    if not value:
        return None
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        raise ValueError(f'مقدار «{column_name}» باید عدد باشد.')
    if number < 0:
        raise ValueError(f'مقدار «{column_name}» نمی‌تواند منفی باشد.')
    return number


def parse_excel_date(value, column_name):
    if value is None or pd.isna(value) or clean_value(value) == '':
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    raw = clean_digits(value).replace('-', '/').replace('.', '/')
    parts = raw.split('/')
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, day = map(int, parts)
        try:
            if year < 1700:
                return jdatetime.date(year, month, day).togregorian()
            return date(year, month, day)
        except (ValueError, OverflowError):
            pass
    raise ValueError(
        f'فرمت «{column_name}» معتبر نیست؛ تاریخ را مانند 1400/01/15 وارد کنید.'
    )


def _find_or_create(model, name, **parents):
    if not name:
        return None
    queryset = model.objects.filter(**parents)
    normalized = clean_value(name)
    for item in queryset:
        if clean_value(item.name) == normalized:
            return item
    return model.objects.create(name=normalized, **parents)


def validate_columns(dataframe):
    return [column for column in REQUIRED_COLUMNS if column not in dataframe.columns]


def sample_dataframe():
    rows = [
        [1, '12345', 'مرد', 'علی', 'رضایی', 'اپراتور کارگاه', 'اپراتور', 'عملیات معدن',
         'تولید', 'عملیات', 'گروه 1', 'A', '0012345678', '1370/01/15', 'متاهل',
         'حسن', 2, '1395/06/01', 'کارشناسی', 'مهندسی معدن', 'کرمان',
         'پایان خدمت', 3650, '09123456789'],
        [2, '67890', 'زن', 'زهرا', 'کاظمی', 'کارشناس کارگاه', 'کارشناس', 'HSE',
         'HSE', 'ایمنی', 'گروه 2', 'B', '0023456789', '1375/08/20', 'مجرد',
         'محمد', 0, '1400/02/10', 'کارشناسی ارشد', 'مهندسی ایمنی', 'یزد',
         'معاف', 1825, '09387654321'],
    ]
    return pd.DataFrame(rows, columns=EXCEL_COLUMNS)


@transaction.atomic
def import_personnel_row(row):
    personnel_code = clean_digits(row.get('شماره پرسنلی'))
    national_code = clean_national_code(row.get('کد ملی'))
    if not personnel_code:
        raise ValueError('شماره پرسنلی خالی است.')
    if not national_code:
        raise ValueError('کد ملی خالی است.')

    section = _find_or_create(Section, clean_value(row.get('بخش')))
    part = _find_or_create(Part, clean_value(row.get('قسمت')), section=section)
    unit_group = _find_or_create(UnitGroup, clean_value(row.get('گروه')), part=part)
    position = _find_or_create(
        Position, clean_value(row.get('عنوان شغل')), unit_group=unit_group
    )

    profile = (
        UserProfile.objects.select_related('user')
        .filter(personnel_code=personnel_code)
        .first()
    )
    created = profile is None
    if profile is None:
        user, user_created = User.objects.get_or_create(
            username=national_code,
            defaults={
                'first_name': clean_value(row.get('نام')),
                'last_name': clean_value(row.get('نام خانوادگی')),
                'email': f'{national_code}@example.com',
            },
        )
        if user_created:
            user.set_unusable_password()
            user.save(update_fields=['password'])
        profile, created = UserProfile.objects.get_or_create(
            user=user, defaults={'personnel_code': personnel_code}
        )

    user = profile.user
    user.first_name = clean_value(row.get('نام'))
    user.last_name = clean_value(row.get('نام خانوادگی'))
    user.save(update_fields=['first_name', 'last_name'])

    values = {
        'personnel_code': personnel_code,
        'national_code': national_code,
        'gender': normalize_gender(row.get('جنسیت')),
        'unit': clean_value(row.get('واحد')),
        'workshop_job_title': clean_value(row.get('عنوان شغل کارگاه')),
        'section': section,
        'part': part,
        'unit_group': unit_group,
        'position': position,
        'group': clean_value(row.get('گروه کاری')).upper(),
        'birth_date': parse_excel_date(row.get('تاریخ تولد'), 'تاریخ تولد'),
        'marital_status': clean_value(row.get('وضعیت تاهل')),
        'father_name': clean_value(row.get('نام پدر')),
        'children_count': clean_non_negative_integer(row.get('تعداد فرزندان'), 'تعداد فرزندان'),
        'hire_date': parse_excel_date(row.get('تاریخ استخدام'), 'تاریخ استخدام'),
        'education_level': clean_value(row.get('مقطع تحصیلی')),
        'field_of_study': clean_value(row.get('رشته تحصیلی')),
        'place_of_birth': clean_value(row.get('محل تولد')),
        'military_service_status': clean_value(row.get('وضعیت خدمت سربازی')),
        'work_experience_days': clean_non_negative_integer(
            row.get('سابقه کار (روز)'), 'سابقه کار (روز)'
        ),
        'mobile': clean_mobile(row.get('شماره تماس')),
    }
    for field, value in values.items():
        setattr(profile, field, value)
    profile.save()
    return profile, created


def import_personnel_dataframe(dataframe):
    missing_columns = validate_columns(dataframe)
    if missing_columns:
        return 0, 0, [], missing_columns

    created_count = 0
    updated_count = 0
    errors = []
    for index, row in dataframe.iterrows():
        try:
            _, created = import_personnel_row(row)
            created_count += int(created)
            updated_count += int(not created)
        except Exception as exc:
            excel_row = index + 2
            errors.append(f'ردیف {excel_row}: {exc}')
    return created_count, updated_count, errors, []
