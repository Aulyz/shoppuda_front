from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def split(value, arg):
    """
    문자열을 지정된 구분자로 분할합니다.
    사용법: {{ "apple,banana,orange"|split:"," }}
    """
    try:
        return value.split(arg)
    except (AttributeError, ValueError):
        return []

@register.filter
def get_item(dictionary, key):
    """
    딕셔너리에서 키로 값을 가져옵니다.
    사용법: {{ mydict|get_item:key }}
    """
    return dictionary.get(key)

@register.filter
def currency(value):
    """
    숫자를 통화 형식으로 포맷합니다.
    사용법: {{ 1000000|currency }}
    """
    try:
        return f"₩{int(value):,}"
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, total):
    """
    백분율을 계산합니다.
    사용법: {{ value|percentage:total }}
    """
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0