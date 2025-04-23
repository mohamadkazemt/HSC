from django import template

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