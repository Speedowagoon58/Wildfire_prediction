from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(name="multiply")
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""
