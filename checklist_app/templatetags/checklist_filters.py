from django import template
from django.utils import timezone
from datetime import datetime
import jdatetime
import base64

register = template.Library()

@register.filter(name='to_jalali')
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    if value is None:
        return ''
    
    # Handle date objects
    from datetime import date
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())
    
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
        return jalali_date.strftime(fmt)
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

@register.filter(name='image_to_data_uri')
def image_to_data_uri(data):
    """
    تبدیل داده‌های باینری تصویر به یک URL داده.
    """
    if data:
        return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
    return '' 