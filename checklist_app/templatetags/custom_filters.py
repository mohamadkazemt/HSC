from django import template
from django.utils import timezone
from datetime import datetime
import jdatetime

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
    
    try:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_date.strftime('%Y/%m/%d %H:%M')
    except:
        return value

@register.filter(name='to_jalali_date')
def to_jalali_date(value):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    
    try:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_date.strftime('%Y/%m/%d')
    except:
        return value 