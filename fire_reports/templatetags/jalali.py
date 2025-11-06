from django import template
from django.utils.safestring import mark_safe
import jdatetime

try:
    from persiantools import digits as persian_digits
    HAS_PERSIAN_TOOLS = True
except ImportError:
    HAS_PERSIAN_TOOLS = False

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    try:
        if not value:
            return ''
        if hasattr(value, 'strftime'):
            gdate = value
        else:
            return value
        jdate = jdatetime.datetime.fromgregorian(datetime=gdate)
        return jdate.strftime(fmt)
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
        # Convert to Persian digits if persiantools is available
        if HAS_PERSIAN_TOOLS:
            return persian_digits.en_to_fa(s)
        return s
    except Exception:
        return value
