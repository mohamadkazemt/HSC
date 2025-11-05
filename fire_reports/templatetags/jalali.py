from django import template
from django.utils.safestring import mark_safe
import jdatetime

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
