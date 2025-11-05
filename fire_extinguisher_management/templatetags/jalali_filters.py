from django import template
import jdatetime
from persiantools import digits as persian_digits

register = template.Library()

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
