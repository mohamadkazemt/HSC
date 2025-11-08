from django import template
import jdatetime

register = template.Library()


@register.filter
def to_jalali(value, format='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی
    """
    if value and hasattr(value, "year"):
        try:
            return jdatetime.date.fromgregorian(date=value).strftime(format)
        except Exception:
            return "تاریخ نامعتبر"
    return "تاریخ نامعتبر"

