from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """دریافت مقدار از دیکشنری با کلید"""
    return dictionary.get(key, '')