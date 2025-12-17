from django import template

register = template.Library()

@register.filter
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter
def get_item(dictionary, key):
    """دریافت مقدار از dictionary با استفاده از کلید"""
    if dictionary is None:
        return None
    return dictionary.get(key)