"""Shared business rules for dependent information.

The public web form, the Rubika bot wizard and the HR review panel all use
these helpers so that every path validates and applies data identically.
"""

from __future__ import annotations

import re
from datetime import date, datetime

import jdatetime
from django.utils import timezone

from .models import (
    EDUCATION_LEVEL_CHOICES,
    EDUCATION_STATUS_CHOICES,
    GENDER_CHOICES,
    MARITAL_STATUS_CHOICES,
    MILITARY_STATUS_CHOICES,
    RELATIONSHIP_CHOICES,
    Dependent,
    DependentChangeRequest,
)

ADULT_AGE = 18

GENDER_LABELS = dict(GENDER_CHOICES)
RELATIONSHIP_LABELS = dict(RELATIONSHIP_CHOICES)
MARITAL_STATUS_LABELS = dict(MARITAL_STATUS_CHOICES)
EDUCATION_STATUS_LABELS = dict(EDUCATION_STATUS_CHOICES)
EDUCATION_LEVEL_LABELS = dict(EDUCATION_LEVEL_CHOICES)
LEVELS_REQUIRING_MAJOR = {'high', 'diploma', 'associate', 'bachelor', 'master', 'phd'}
MILITARY_STATUS_LABELS = dict(MILITARY_STATUS_CHOICES)

FIELD_LABELS = {
    'first_name': 'نام',
    'last_name': 'نام خانوادگی',
    'father_name': 'نام پدر',
    'national_code': 'کد ملی',
    'birth_certificate_number': 'شماره شناسنامه',
    'birth_date': 'تاریخ تولد',
    'gender': 'جنسیت',
    'mobile': 'شماره تماس',
    'relationship': 'نسبت',
    'marital_status': 'وضعیت تاهل',
    'address': 'آدرس محل سکونت',
    'education_status': 'وضعیت تحصیلی',
    'education_level': 'مقطع تحصیلی',
    'field_of_study': 'رشته تحصیلی',
    'study_place': 'محل تحصیل',
    'job': 'شغل',
    'military_status': 'وضعیت نظام وظیفه',
    'disease_type': 'نوع بیماری',
}

EDITABLE_FIELDS = tuple(FIELD_LABELS)

PERSIAN_DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
MOBILE_RE = re.compile(r'^09\d{9}$')


def normalize_digits(value) -> str:
    if value is None:
        return ''
    return str(value).translate(PERSIAN_DIGITS).strip()


def normalize_mobile(value) -> str:
    digits = re.sub(r'\D', '', normalize_digits(value))
    if digits.startswith('0098'):
        digits = '0' + digits[4:]
    elif digits.startswith('98') and len(digits) == 12:
        digits = '0' + digits[2:]
    elif digits.startswith('9') and len(digits) == 10:
        digits = '0' + digits
    return digits


def normalize_national_code(value) -> str:
    return re.sub(r'\D', '', normalize_digits(value))


def is_valid_national_code(code: str) -> bool:
    """Validate an Iranian national code including its checksum."""
    code = normalize_national_code(code)
    if len(code) != 10 or len(set(code)) == 1:
        return False
    check = int(code[9])
    total = sum(int(code[i]) * (10 - i) for i in range(9)) % 11
    return (total < 2 and check == total) or (total >= 2 and check == 11 - total)


def parse_date(value, today=None) -> date | None:
    """Accept a ``date``/``datetime`` or an ISO ``YYYY-MM-DD`` string."""
    if value in (None, ''):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except (TypeError, ValueError):
        return None


def calculate_age(birth_date, today=None) -> int | None:
    birth_date = parse_date(birth_date)
    if birth_date is None:
        return None
    today = today or timezone.localdate()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def is_adult(birth_date, today=None) -> bool:
    age = calculate_age(birth_date, today=today)
    return age is not None and age >= ADULT_AGE


def to_jalali(value) -> str:
    value = parse_date(value)
    if value is None:
        return ''
    return jdatetime.date.fromgregorian(date=value).strftime('%Y/%m/%d')


def parse_jalali(year, month, day) -> date | None:
    try:
        y, m, d = int(year), int(month), int(day)
    except (TypeError, ValueError):
        return None
    if not (y and 1 <= m <= 12 and 1 <= d <= 31):
        return None
    try:
        return jdatetime.date(y, m, d).togregorian()
    except ValueError:
        return None


def humanize(field: str, value) -> str:
    if value in (None, ''):
        return '—'
    if field == 'birth_date':
        return to_jalali(value) or str(value)
    labels = {
        'gender': GENDER_LABELS,
        'relationship': RELATIONSHIP_LABELS,
        'marital_status': MARITAL_STATUS_LABELS,
        'education_status': EDUCATION_STATUS_LABELS,
        'education_level': EDUCATION_LEVEL_LABELS,
        'military_status': MILITARY_STATUS_LABELS,
    }.get(field)
    if labels:
        return labels.get(value, str(value))
    return str(value)


def validate_dependent_data(data, *, today=None) -> tuple[dict, dict]:
    """Validate a raw payload and return ``(cleaned, errors)``.

    Every field is required, except the ones that are meaningless for the
    person (e.g. military service for women or children).  See the rules in
    ``_required_rules``.
    """
    errors: dict[str, str] = {}
    cleaned: dict[str, object] = {}

    def text(field, max_length=None):
        value = normalize_digits(data.get(field))
        if max_length and len(value) > max_length:
            value = value[:max_length]
        return value

    cleaned['first_name'] = text('first_name', 150)
    cleaned['last_name'] = text('last_name', 150)
    cleaned['father_name'] = text('father_name', 150)
    cleaned['birth_certificate_number'] = text('birth_certificate_number', 20)
    cleaned['national_code'] = normalize_national_code(data.get('national_code'))
    cleaned['mobile'] = normalize_mobile(data.get('mobile'))
    cleaned['address'] = text('address')
    cleaned['job'] = text('job', 150)
    cleaned['field_of_study'] = text('field_of_study', 150)
    cleaned['study_place'] = text('study_place', 150)
    cleaned['disease_type'] = text('disease_type', 255)

    cleaned['gender'] = text('gender')
    cleaned['relationship'] = text('relationship')
    cleaned['marital_status'] = text('marital_status')
    cleaned['education_status'] = text('education_status')
    cleaned['education_level'] = text('education_level')
    cleaned['military_status'] = text('military_status')

    birth_date = parse_date(data.get('birth_date'))
    cleaned['birth_date'] = birth_date

    # --- choices ---------------------------------------------------------
    if cleaned['gender'] not in GENDER_LABELS:
        errors['gender'] = 'جنسیت را انتخاب کنید.'
    if cleaned['relationship'] not in RELATIONSHIP_LABELS:
        errors['relationship'] = 'نسبت را انتخاب کنید.'
    if cleaned['education_status'] not in EDUCATION_STATUS_LABELS:
        errors['education_status'] = 'وضعیت تحصیلی را انتخاب کنید.'

    if cleaned['marital_status'] and cleaned['marital_status'] not in MARITAL_STATUS_LABELS:
        errors['marital_status'] = 'وضعیت تاهل نامعتبر است.'
    if cleaned['education_level'] and cleaned['education_level'] not in EDUCATION_LEVEL_LABELS:
        errors['education_level'] = 'مقطع تحصیلی نامعتبر است.'
    if cleaned['military_status'] and cleaned['military_status'] not in MILITARY_STATUS_LABELS:
        errors['military_status'] = 'وضعیت نظام وظیفه نامعتبر است.'

    # --- always required ------------------------------------------------
    for field in ('first_name', 'last_name'):
        if not cleaned[field]:
            errors[field] = 'این فیلد الزامی است.'
    if not cleaned['national_code']:
        errors['national_code'] = 'کد ملی الزامی است.'
    elif not is_valid_national_code(cleaned['national_code']):
        errors['national_code'] = 'کد ملی وارد شده معتبر نیست.'
    if birth_date is None:
        errors['birth_date'] = 'تاریخ تولد الزامی است.'
    elif birth_date > (today or timezone.localdate()):
        errors['birth_date'] = 'تاریخ تولد نمی‌تواند در آینده باشد.'

    adult = is_adult(birth_date, today=today) if birth_date else False

    # --- adult-only fields ---------------------------------------------
    if adult:
        if cleaned['marital_status'] not in MARITAL_STATUS_LABELS:
            errors['marital_status'] = 'وضعیت تاهل را انتخاب کنید.'
        if not cleaned['mobile']:
            errors['mobile'] = 'شماره تماس الزامی است.'
        elif not MOBILE_RE.match(cleaned['mobile']):
            errors['mobile'] = 'شماره تماس باید ۱۱ رقم و با ۰۹ شروع شود.'
        if not cleaned['address']:
            errors['address'] = 'آدرس محل سکونت الزامی است.'
        if not cleaned['job']:
            errors['job'] = 'شغل الزامی است. اگر شاغل نیستید «بدون شغل» بنویسید.'
    else:
        # Irrelevant for minors: keep values only if valid, otherwise blank.
        if not cleaned['marital_status']:
            cleaned['marital_status'] = ''
        if not cleaned['mobile']:
            cleaned['mobile'] = ''
        if not cleaned['address']:
            cleaned['address'] = ''
        if not cleaned['job']:
            cleaned['job'] = ''
        if cleaned['mobile'] and not MOBILE_RE.match(cleaned['mobile']):
            errors['mobile'] = 'شماره تماس معتبر نیست.'

    # --- education-dependent fields ------------------------------------
    if cleaned['education_status'] in ('studying', 'graduated', 'dropped'):
        if not cleaned['education_level']:
            errors['education_level'] = 'مقطع تحصیلی را انتخاب کنید.'
        if cleaned['education_level'] in LEVELS_REQUIRING_MAJOR:
            if not cleaned['field_of_study']:
                errors['field_of_study'] = 'رشته تحصیلی را وارد کنید.'
        else:
            # Primary, middle, and other education levels don't have a required major
            if not cleaned['field_of_study']:
                cleaned['field_of_study'] = ''
        if not cleaned['study_place']:
            errors['study_place'] = 'محل تحصیل یا نام مدرسه را وارد کنید.'
    else:
        cleaned['education_level'] = ''
        cleaned['field_of_study'] = ''
        cleaned['study_place'] = ''

    # --- military status (adult men only) ------------------------------
    if adult and cleaned['gender'] == 'male':
        if not cleaned['military_status']:
            errors['military_status'] = 'وضعیت نظام وظیفه را انتخاب کنید.'
    else:
        cleaned['military_status'] = ''

    return {key: (value or None) if key != 'birth_date' else value
            for key, value in cleaned.items()}, errors


def _coerce(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, str):
        try:
            import json
            return json.loads(data)
        except (TypeError, ValueError):
            return {}
    return {}


def dependent_snapshot(dependent: Dependent) -> dict:
    snapshot = {}
    for field in EDITABLE_FIELDS:
        value = getattr(dependent, field, None)
        if field == 'birth_date' and value:
            value = value.isoformat()
        snapshot[field] = '' if value is None else value
    return snapshot


def build_diff(old_data: dict, new_data: dict) -> list[dict]:
    old_data = _coerce(old_data)
    new_data = _coerce(new_data)
    rows = []
    for field in EDITABLE_FIELDS:
        old_value = old_data.get(field, '')
        new_value = new_data.get(field, '')
        if str(old_value or '') == str(new_value or ''):
            continue
        rows.append({
            'field': field,
            'label': FIELD_LABELS.get(field, field),
            'old': humanize(field, old_value),
            'new': humanize(field, new_value),
        })
    return rows


def _json_safe(data):
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            elif isinstance(value, dict):
                cleaned[key] = _json_safe(value)
            elif isinstance(value, list):
                cleaned[key] = [_json_safe(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        return cleaned
    return data


class ChangeRequestError(Exception):
    """Raised when a change request cannot be created or applied."""


def create_change_request(
    personnel,
    action: str,
    new_data: dict,
    *,
    dependent: Dependent | None = None,
    channel: str = DependentChangeRequest.Channel.WEB,
    submitted_by=None,
    ip_address: str | None = None,
) -> DependentChangeRequest:
    """Persist a pending change request, refusing silent duplicates."""
    from django.db import transaction

    new_data = _coerce(new_data)

    if action not in DependentChangeRequest.Action.values:
        raise ChangeRequestError('نوع درخواست نامعتبر است.')

    pending = DependentChangeRequest.objects.filter(
        personnel=personnel, status=DependentChangeRequest.Status.PENDING
    )
    if dependent is not None:
        if pending.filter(dependent=dependent).exists():
            raise ChangeRequestError('برای این فرد یک درخواست در انتظار بررسی وجود دارد.')
    elif action == DependentChangeRequest.Action.CREATE:
        national_code = (new_data or {}).get('national_code') or ''
        if national_code and pending.filter(
            action=DependentChangeRequest.Action.CREATE,
            new_data__national_code=national_code,
        ).exists():
            raise ChangeRequestError('برای این کد ملی یک درخواست در انتظار بررسی وجود دارد.')

    old_data = dependent_snapshot(dependent) if dependent is not None else {}

    with transaction.atomic():
        request = DependentChangeRequest.objects.create(
            personnel=personnel,
            dependent=dependent,
            action=action,
            old_data=_json_safe(old_data),
            new_data=_json_safe(new_data),
            channel=channel,
            submitted_by=submitted_by if getattr(submitted_by, 'pk', None) else None,
            ip_address=ip_address,
        )
    return request


def _apply_field_to_dependent(dependent: Dependent, field: str, value):
    """Set field on Dependent model respecting model constraints."""
    if field == 'birth_date' and isinstance(value, str) and value:
        from django.utils.dateparse import parse_date
        value = parse_date(value) or value

    try:
        model_field = Dependent._meta.get_field(field)
    except Exception:
        setattr(dependent, field, value)
        return

    if model_field.null:
        setattr(dependent, field, value or None)
    else:
        setattr(dependent, field, '' if value is None else str(value))


def apply_change_request(change: DependentChangeRequest, *, reviewer=None, note: str = '') -> None:
    """Apply an approved request to the database (create/update/delete)."""
    from django.db import transaction

    new_data = _coerce(change.new_data)

    with transaction.atomic():
        if change.action == DependentChangeRequest.Action.CREATE:
            dependent = Dependent(personnel=change.personnel)
            for field in EDITABLE_FIELDS:
                _apply_field_to_dependent(dependent, field, new_data.get(field))
            dependent.save()
            change.dependent = dependent
        elif change.action == DependentChangeRequest.Action.UPDATE:
            dependent = change.dependent
            if dependent is None:
                raise ChangeRequestError('فرد تحت تکفل مورد نظر یافت نشد.')
            for field in EDITABLE_FIELDS:
                _apply_field_to_dependent(dependent, field, new_data.get(field))
            dependent.save()
        elif change.action == DependentChangeRequest.Action.DELETE:
            if change.dependent is not None:
                change.dependent.delete()
                change.dependent = None
        else:  # pragma: no cover - guarded by the model choices
            raise ChangeRequestError('نوع درخواست نامعتبر است.')


        change.status = DependentChangeRequest.Status.APPROVED
        change.reviewed_by = reviewer if getattr(reviewer, 'pk', None) else None
        change.reviewed_at = timezone.now()
        change.review_note = note or ''
        change.new_data = _json_safe(new_data)
        change.save()


def reject_change_request(change: DependentChangeRequest, *, reviewer=None, note: str = '') -> None:
    change.status = DependentChangeRequest.Status.REJECTED
    change.reviewed_by = reviewer if getattr(reviewer, 'pk', None) else None
    change.reviewed_at = timezone.now()
    change.review_note = note or ''
    change.save()
