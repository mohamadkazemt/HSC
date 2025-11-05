from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    try:
        return field.as_widget(attrs={**getattr(field.field.widget, 'attrs', {}), 'class': css})
    except AttributeError:
        # If field is already rendered as string, just return it
        return field
