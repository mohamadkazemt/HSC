# hse_docs/templatetags/hse_docs_jalali.py
import jdatetime
from django import template
from django.utils.timezone import localtime
from persiantools import digits as persian_digits

register = template.Library()


@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    """
    تبدیل تاریخ میلادی به تاریخ و زمان شمسی محلی
    :param value: تاریخ میلادی (datetime)
    :param fmt: فرمت خروجی تاریخ و زمان
    :return: تاریخ شمسی به فرمت مشخص‌شده
    """
    if not value:
        return ''
    try:
        # تبدیل زمان به زمان محلی
        if hasattr(value, 'date'):
            # It's a datetime
            local_value = localtime(value)
            j = jdatetime.datetime.fromgregorian(datetime=local_value)
            result = j.strftime(fmt)
        else:
            # It's a date
            j = jdatetime.date.fromgregorian(date=value)
            result = j.strftime(fmt.replace('%H:%M', '').replace('%H:%M:%S', '').strip())
        
        # تبدیل به اعداد فارسی
        return persian_digits.en_to_fa(result)
    except Exception as e:
        return value


@register.filter(name='jalali_date')
def jalali_date(value, fmt="%Y/%m/%d"):
    """Convert a date or datetime to Jalali (Shamsi) string with Persian numerals.

    Usage: {{ mydate|jalali_date }}
    """
    if not value:
        return ''
    try:
        # If it's a datetime, get the date part
        if hasattr(value, 'date'):
            value = value.date()
        # Use jdatetime to convert
        j = jdatetime.date.fromgregorian(date=value)
        s = j.strftime(fmt)
        # Convert to Persian digits
        return persian_digits.en_to_fa(s)
    except Exception:
        return value

