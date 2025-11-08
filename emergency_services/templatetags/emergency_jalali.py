import datetime
import jdatetime
from django import template
from django.utils.timezone import localtime

register = template.Library()


@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    try:
        if isinstance(value, datetime.datetime):
            local_value = localtime(value)
            return jdatetime.datetime.fromgregorian(datetime=local_value).strftime(fmt)
        if isinstance(value, datetime.date):
            return jdatetime.date.fromgregorian(date=value).strftime(fmt.replace('%H:%M', '').strip())
        return value
    except Exception:
        return value

