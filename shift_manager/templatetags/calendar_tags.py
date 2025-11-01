from django import template
import jdatetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except:
        return None

@register.filter
def split(str, sep):
  return str.split(sep)

@register.filter
def to_jalali(date):
    """Converts a Gregorian date to Jalali date."""
    if date:
        jdate = jdatetime.date.fromgregorian(date=date)
        return jdate.strftime("%Y/%m/%d")
    return ''

@register.filter
def datetime_to_jalali(datetime_obj):
    """Converts a Gregorian datetime to Jalali datetime string."""
    if datetime_obj:
        try:
            jdatetime_obj = jdatetime.datetime.fromgregorian(datetime=datetime_obj)
            return jdatetime_obj.strftime("%Y/%m/%d %H:%M")
        except:
            return str(datetime_obj)
    return ''

@register.filter
def persian_weekday(day):
    weekdays = {
        'Saturday': 'شنبه',
        'Sunday': 'یکشنبه',
        'Monday': 'دوشنبه',
        'Tuesday': 'سه‌شنبه',
        'Wednesday': 'چهارشنبه',
        'Thursday': 'پنج‌شنبه',
        'Friday': 'جمعه'
    }
    return weekdays.get(day, day)