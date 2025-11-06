from django import template
import base64

register = template.Library()

@register.filter
def image_to_data_uri(data):
    """
    تبدیل داده‌های باینری تصویر به یک URL داده.
    """
    if data:
        return f"data:image/png;base64,{base64.b64encode(data).decode('utf-8')}"
    return '' 