from django import template
from gym_referrals.presentation import format_jalali

register = template.Library()


@register.filter
def gym_jalali(value, with_time=False):
    return format_jalali(value, bool(with_time))


@register.filter
def money(value):
    try:
        return f"{value:,.0f}"
    except (TypeError, ValueError):
        return value
