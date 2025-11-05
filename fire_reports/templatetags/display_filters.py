from django import template

register = template.Library()

def get_display(obj, field_name):
    """
    Returns the display value for a model field with choices.
    Usage: {{ obj|get_display:'field_name' }}
    """
    method = getattr(obj, f'get_{field_name}_display', None)
    if callable(method):
        return method()
    return getattr(obj, field_name, '')

register.filter('get_display', get_display)
