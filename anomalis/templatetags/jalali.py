import jdatetime
from django import template
from django.utils.timezone import localtime

register = template.Library()

@register.filter
def to_jalali(value, fmt='%Y/%m/%d %H:%M'):
    """
    تبدیل تاریخ میلادی به تاریخ و زمان شمسی محلی
    :param value: تاریخ میلادی (datetime)
    :param fmt: فرمت خروجی تاریخ و زمان
    :return: تاریخ شمسی به فرمت مشخص‌شده
    """
    try:
        # تبدیل زمان به زمان محلی
        local_value = localtime(value)
        # تبدیل به تاریخ شمسی
        return jdatetime.datetime.fromgregorian(datetime=local_value).strftime(fmt)
    except Exception as e:
        return value  # در صورت بروز خطا، مقدار اصلی را بازگرداند
