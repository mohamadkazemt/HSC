# این فیلتر برای اضافه کردن کلاس به فیلدهای فرم استفاده می شود.
# برای استفاده از آن می توانید از فیلتر add_class استفاده نمایید.
# نمونه:
# {{ form.field | add_class:"form-control" }}
from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})



register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})