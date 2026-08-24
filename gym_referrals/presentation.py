import jdatetime
from django.utils import timezone


def format_jalali(value, with_time=False):
    if value is None:
        return "-"
    if hasattr(value, "tzinfo") and value.tzinfo is not None:
        value = timezone.localtime(value)
    gregorian_date = value.date() if hasattr(value, "date") else value
    result = jdatetime.date.fromgregorian(date=gregorian_date).strftime("%Y/%m/%d")
    if with_time and hasattr(value, "strftime"):
        result += value.strftime(" %H:%M")
    return result
