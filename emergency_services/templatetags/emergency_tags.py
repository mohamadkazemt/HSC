from django import template

register = template.Library()

@register.filter
def has_group(user, group_name):
    """چک کردن عضویت کاربر در گروه"""
    return user.groups.filter(name=group_name).exists()

@register.filter
def get_emergency_role(user):
    """دریافت نقش اورژانسی کاربر"""
    if user.groups.filter(name='EmergencyManager').exists():
        return 'مدیر اورژانس'
    elif user.groups.filter(name='EmergencyDoctor').exists():
        return 'پزشک اورژانس'
    elif user.groups.filter(name='EmergencyNurse').exists():
        return 'پرستار اورژانس'
    elif user.is_superuser:
        return 'مدیر سیستم'
    return 'کاربر سیستم'
