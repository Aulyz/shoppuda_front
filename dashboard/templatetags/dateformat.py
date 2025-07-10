from django import template

register = template.Library()

@register.filter
def formatdate(value, format_string="%Y-%m-%d"):
    if value:
        return value.strftime(format_string)
    return ""