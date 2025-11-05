from django import template
import jdatetime

register = template.Library()

@register.filter
def to_jalali(value, format='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی
    """
    if value and hasattr(value, "year"):  # بررسی اینکه مقدار ورودی یک شیء تاریخ است
        try:
            return jdatetime.date.fromgregorian(date=value).strftime(format)
        except Exception as e:
            return "تاریخ نامعتبر"
    return "تاریخ نامعتبر"

