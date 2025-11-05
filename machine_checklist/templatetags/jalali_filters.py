from django import template
import jdatetime
from django.utils.timezone import localtime

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    """Convert a datetime to Jalali (Shamsi) string."""
    if not value:
        return ''
    try:
        if hasattr(value, 'date'):
            # It's a datetime
            local_value = localtime(value)
            j = jdatetime.datetime.fromgregorian(datetime=local_value)
            return j.strftime(fmt)
        else:
            # It's a date
            j = jdatetime.date.fromgregorian(date=value)
            return j.strftime(fmt.replace('%H:%M', '').strip())
    except Exception:
        return value

