from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS classes to a BoundField's widget while rendering.

    Usage in templates: {{ form.field|add_class:'class1 class2' }}
    If anything goes wrong, returns the field rendered as-is.
    """
    try:
        # If a BoundField is passed, update the widget attrs
        widget = getattr(field, 'field', None)
        if widget is not None:
            existing = field.field.widget.attrs.get('class', '')
            classes = (existing + ' ' + str(css_class)).strip()
            return field.as_widget(attrs={**field.field.widget.attrs, 'class': classes})

        # Fallback: attempt to render as string
        return format_html(str(field))
    except Exception:
        # On error, return the original unmodified field (best-effort)
        try:
            return field
        except Exception:
            return ''


@register.simple_tag
def field_classes(field, base_classes, error_classes=''):
    """Return base classes with error styles appended when field has errors."""
    try:
        base = str(base_classes or '')
        if field is None:
            return base
        errors = getattr(field, 'errors', None)
        if errors:
            return f"{base} {error_classes}".strip()
        return base
    except Exception:
        return base_classes


@register.filter(name='has_errors')
def has_errors(field):
    """Check whether a bound field contains validation errors."""
    try:
        return bool(getattr(field, 'errors', None))
    except Exception:
        return False


@register.filter(name='split')
def split(value, sep=None):
    """Split a string into a list by the given separator.

    Usage in templates:
        {% for part in 'a b c'|split:' ' %}
    If sep is None, splits on whitespace.
    """
    try:
        if value is None:
            return []
        if sep is None:
            return str(value).split()
        return str(value).split(sep)
    except Exception:
        return []


@register.filter(name='get_attr')
def get_attr(obj, attr_name):
    """Return attribute or dict key from an object safely in templates.

    Usage: {{ obj|get_attr:'field_name' }}
    """
    try:
        if obj is None:
            return ''
        # try attribute access
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        # try dict-like access
        try:
            return obj[attr_name]
        except Exception:
            pass
        # fallback: try getattr anyway (may raise)
        return getattr(obj, attr_name)
    except Exception:
        return ''
