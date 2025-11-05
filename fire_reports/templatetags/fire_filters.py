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
@register.filter
def b64encode(data):
    """
    Base64 encode bytes or string for use in templates.
    """
    import base64
    if data is None:
        return ''
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('utf-8')