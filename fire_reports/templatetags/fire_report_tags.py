from django import template

register = template.Library()

@register.filter
def get_field(form, field_name):
    """Get a form field by its name"""
    try:
        return form[field_name]
    except KeyError:
        return None

@register.filter
def get_field_label(form, field_name):
    """Get a form field's label by its base name"""
    status_field = f"{field_name}_status"
    try:
        return form[status_field].label
    except KeyError:
        return field_name.title()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter"""
    return value.split(delimiter)

@register.filter
def get_description_field(form, field_name):
    try:
        return form[f"{field_name}_description"]
    except:
        return None
