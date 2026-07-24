from datetime import date
from django import template
import jdatetime

register = template.Library()


@register.filter
def to_jalali(value, format='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی
    """
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
            return jdatetime.date.fromgregorian(date=parsed).strftime(format)
        except ValueError:
            return value
    if value and hasattr(value, "year"):
        try:
            return jdatetime.date.fromgregorian(date=value).strftime(format)
        except Exception:
            return "تاریخ نامعتبر"
    return "تاریخ نامعتبر"

