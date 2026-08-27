from django import template
from django.utils import timezone
from datetime import datetime
import jdatetime

register = template.Library()


@register.filter(name="to_jalali")
def to_jalali(value, fmt="%Y/%m/%d %H:%M"):
    if value is None:
        return ""

    from datetime import date

    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())

    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                value = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return value

    try:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=value)
        return jalali_date.strftime(fmt)
    except Exception:
        return value
