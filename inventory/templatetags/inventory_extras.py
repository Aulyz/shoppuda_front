# inventory/templatetags/inventory_extras.py
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter
def add_comma(value):
    """숫자에 천 단위 구분자 추가"""
    try:
        return intcomma(int(value))
    except (ValueError, TypeError):
        return value

@register.filter
def currency(value):
    """통화 형식으로 포맷"""
    try:
        return f"₩{intcomma(int(value))}"
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, decimal_places=1):
    """퍼센티지 형식으로 포맷"""
    try:
        return f"{float(value):.{decimal_places}f}%"
    except (ValueError, TypeError):
        return value

@register.filter
def stock_status_class(stock_quantity, min_stock):
    """재고 상태에 따른 CSS 클래스 반환"""
    try:
        stock = int(stock_quantity)
        min_stock = int(min_stock)
        
        if stock == 0:
            return "text-red-600 dark:text-red-400"
        elif stock <= min_stock:
            return "text-yellow-600 dark:text-yellow-400"
        else:
            return "text-green-600 dark:text-green-400"
    except (ValueError, TypeError):
        return "text-gray-600 dark:text-gray-400"

@register.filter
def stock_status_badge(stock_quantity, min_stock):
    """재고 상태에 따른 배지 클래스 반환"""
    try:
        stock = int(stock_quantity)
        min_stock = int(min_stock)
        
        if stock == 0:
            return "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400"
        elif stock <= min_stock:
            return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400"
        else:
            return "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
    except (ValueError, TypeError):
        return "bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400"

@register.filter
def stock_status_text(stock_quantity, min_stock):
    """재고 상태 텍스트 반환"""
    try:
        stock = int(stock_quantity)
        min_stock = int(min_stock)
        
        if stock == 0:
            return "품절"
        elif stock <= min_stock:
            return "부족"
        else:
            return "정상"
    except (ValueError, TypeError):
        return "알 수 없음"

@register.simple_tag
def movement_type_badge(movement_type):
    """재고 이동 타입에 따른 배지 HTML 반환"""
    type_classes = {
        'IN': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
        'OUT': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
        'ADJUST': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
        'TRANSFER': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
        'RETURN': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
        'DAMAGE': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
        'SALE': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
        'PURCHASE': 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
        'CANCEL': 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
        'CORRECTION': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    }
    
    type_names = {
        'IN': '입고',
        'OUT': '출고',
        'ADJUST': '조정',
        'TRANSFER': '이동',
        'RETURN': '반품',
        'DAMAGE': '손상',
        'SALE': '판매',
        'PURCHASE': '구매',
        'CANCEL': '취소',
        'CORRECTION': '수정',
    }
    
    css_class = type_classes.get(movement_type, type_classes['ADJUST'])
    display_name = type_names.get(movement_type, movement_type)
    
    return f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {css_class}">{display_name}</span>'

@register.inclusion_tag('inventory/partials/stock_level_indicator.html')
def stock_level_indicator(product):
    """재고 수준 표시기"""
    context = {
        'product': product,
        'stock_percentage': 0,
        'status': 'normal'
    }
    
    try:
        if product.max_stock_level > 0:
            context['stock_percentage'] = min(100, (product.stock_quantity / product.max_stock_level) * 100)
        
        if product.stock_quantity == 0:
            context['status'] = 'critical'
        elif product.stock_quantity <= product.min_stock_level:
            context['status'] = 'warning'
        else:
            context['status'] = 'normal'
    except (AttributeError, ZeroDivisionError):
        pass
    
    return context

@register.filter
def multiply(value, arg):
    """두 값을 곱하기"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """두 값을 나누기"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """두 값을 빼기"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.simple_tag
def calculate_stock_value(quantity, price):
    """재고 가치 계산"""
    try:
        return float(quantity) * float(price)
    except (ValueError, TypeError):
        return 0

@register.filter
def days_since(value):
    """날짜로부터 경과일 계산"""
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        if isinstance(value, str):
            from django.utils.dateparse import parse_datetime
            value = parse_datetime(value)
        
        if value:
            diff = timezone.now() - value
            return diff.days
    except (ValueError, TypeError):
        pass
    
    return 0

@register.filter
def format_date(value, date_format='%Y-%m-%d'):
    """날짜 형식 지정"""
    try:
        if isinstance(value, str):
            from django.utils.dateparse import parse_datetime
            value = parse_datetime(value)
        
        if value:
            return value.strftime(date_format)
    except (ValueError, TypeError):
        pass
    
    return value

@register.inclusion_tag('inventory/partials/trend_indicator.html')
def trend_indicator(current_value, previous_value, show_percentage=True):
    """증감 추세 표시기"""
    context = {
        'current': current_value,
        'previous': previous_value,
        'change': 0,
        'change_percentage': 0,
        'trend': 'neutral',
        'show_percentage': show_percentage
    }
    
    try:
        current = float(current_value or 0)
        previous = float(previous_value or 0)
        
        if previous > 0:
            context['change'] = current - previous
            context['change_percentage'] = ((current - previous) / previous) * 100
            
            if context['change'] > 0:
                context['trend'] = 'up'
            elif context['change'] < 0:
                context['trend'] = 'down'
            else:
                context['trend'] = 'neutral'
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    
    return context