from django import template

register = template.Library()


@register.simple_tag
def field_classes(field, base_classes, error_classes=''):
    """Return class list with error styles when the field has validation issues."""
    base = str(base_classes or '').strip()
    try:
        if getattr(field, 'errors', None):
            return f"{base} {error_classes}".strip()
        return base
    except Exception:
        return base


@register.filter(name='has_errors')
def has_errors(field):
    try:
        return bool(getattr(field, 'errors', None))
    except Exception:
        return False
