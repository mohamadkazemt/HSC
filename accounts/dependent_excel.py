import pandas as pd
from django.db import transaction

from .models import Dependent, UserProfile
from .personnel_excel import (
    clean_digits, clean_mobile, clean_national_code, clean_value, parse_excel_date,
)


EXCEL_COLUMNS = [
    'کد پرسنلی', 'نام', 'نام خانوادگی', 'نام پدر', 'کد ملی',
    'شماره شناسنامه', 'تاریخ تولد', 'جنسیت', 'شماره تماس', 'نسبت', 'نوع بیماری',
]


def sample_dataframe():
    return pd.DataFrame([
        ['12345', 'مریم', 'رضایی', 'حسن', '0012345678', '1234',
         '1372/05/10', 'زن', '09123456789', 'همسر', ''],
        ['12345', 'امیر', 'رضایی', 'علی', '0023456789', '5678',
         '1398/02/20', 'مرد', '', 'فرزند', 'آسم'],
    ], columns=EXCEL_COLUMNS)


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


@transaction.atomic
def import_dependent_row(row):
    personnel_code = clean_digits(row.get('کد پرسنلی'))
    national_code = clean_national_code(row.get('کد ملی'))
    if not personnel_code:
        raise ValueError('کد پرسنلی خالی است.')
    if not national_code:
        raise ValueError('کد ملی خالی است.')

    profiles = UserProfile.objects.filter(personnel_code=personnel_code)
    count = profiles.count()
    if count == 0:
        raise ValueError(f'پرسنلی با کد «{personnel_code}» یافت نشد.')
    if count > 1:
        raise ValueError(f'کد پرسنلی «{personnel_code}» برای بیش از یک پرسنل ثبت شده است.')

    defaults = {
        'first_name': clean_value(row.get('نام')),
        'last_name': clean_value(row.get('نام خانوادگی')),
        'father_name': clean_value(row.get('نام پدر')),
        'birth_certificate_number': clean_digits(row.get('شماره شناسنامه')),
        'birth_date': parse_excel_date(row.get('تاریخ تولد'), 'تاریخ تولد'),
        'gender': normalize_gender(row.get('جنسیت')),
        'mobile': clean_mobile(row.get('شماره تماس')),
        'relationship': clean_value(row.get('نسبت')),
        'disease_type': clean_value(row.get('نوع بیماری')),
    }
    if not defaults['first_name'] or not defaults['last_name']:
        raise ValueError('نام و نام خانوادگی الزامی است.')
    if not defaults['relationship']:
        raise ValueError('نسبت الزامی است.')

    return Dependent.objects.update_or_create(
        personnel=profiles.first(), national_code=national_code, defaults=defaults
    )


def import_dependents_dataframe(dataframe):
    dataframe.columns = [clean_value(column) for column in dataframe.columns]
    missing = [column for column in EXCEL_COLUMNS if column not in dataframe.columns]
    if missing:
        return 0, 0, [], missing

    created_count = updated_count = 0
    errors = []
    for index, row in dataframe.iterrows():
        if all(not clean_value(row.get(column)) for column in EXCEL_COLUMNS):
            continue
        try:
            _, created = import_dependent_row(row)
            created_count += int(created)
            updated_count += int(not created)
        except Exception as exc:
            errors.append(f'ردیف {index + 2}: {exc}')
    return created_count, updated_count, errors, []
