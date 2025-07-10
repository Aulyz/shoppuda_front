# dashboard/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta, datetime
from orders.models import Order
from products.models import Product
from platforms.models import Platform

@login_required
def dashboard_home(request):
    """대시보드 홈 페이지"""
    today = timezone.now().date()
    
    # 기본 통계
    context = {
        'total_orders': Order.objects.count(),
        'total_sales': Order.objects.filter(
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_products': Product.objects.filter(status='ACTIVE').count(),
        'low_stock_count': Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count(),
        'today_orders': Order.objects.filter(order_date__date=today).count(),
        'today_sales': Order.objects.filter(
            order_date__date=today,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'new_products_week': Product.objects.filter(
            created_at__date__gte=today - timedelta(days=7)
        ).count(),
        'connected_platforms': Platform.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'dashboard/home.html', context)

@login_required
def dashboard_recent_orders(request):
    """최근 주문 API"""
    recent_orders = Order.objects.select_related().order_by('-order_date')[:5]
    
    orders_data = []
    for order in recent_orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name or order.customer_email,
            'total_amount': float(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display(),
            'order_date': order.order_date.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({
        'orders': orders_data
    })

@login_required
def dashboard_chart_data(request):
    """차트 데이터 API"""
    chart_type = request.GET.get('type', 'sales')
    period = request.GET.get('period', '7')
    
    try:
        days = int(period)
        if days not in [7, 14, 30, 90]:
            days = 7
    except (ValueError, TypeError):
        days = 7
    
    today = timezone.now().date()
    start_date = today - timedelta(days=days-1)
    
    if chart_type == 'sales':
        # 일별 매출 데이터
        sales_data = []
        labels = []
        
        # 날짜별로 매출 조회
        for i in range(days):
            date = start_date + timedelta(days=i)
            daily_sales = Order.objects.filter(
                order_date__date=date,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            sales_data.append(float(daily_sales))
            labels.append(date.strftime('%m/%d'))
        
        return JsonResponse({
            'labels': labels,
            'data': sales_data,
            'currency': '원'
        })
    
    elif chart_type == 'category':
        # 카테고리별 판매량
        category_data = Product.objects.filter(
            status='ACTIVE'
        ).values('category').annotate(
            count=Count('id')
        ).order_by('-count')[:5]  # 상위 5개 카테고리
        
        labels = [item['category'] for item in category_data]
        data = [item['count'] for item in category_data]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
    
    elif chart_type == 'orders':
        # 주문 상태별 데이터
        order_statuses = Order.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
        
        labels = [item['status'] for item in order_statuses]
        data = [item['count'] for item in order_statuses]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
    
    elif chart_type == 'platforms':
        # 플랫폼별 상품 수
        platform_data = Platform.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).values('name', 'product_count')
        
        labels = [item['name'] for item in platform_data]
        data = [item['product_count'] for item in platform_data]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
    
    return JsonResponse({'error': '지원하지 않는 차트 타입입니다.'}, status=400)

@login_required
def dashboard_stats(request):
    """실시간 통계 API"""
    if request.method != 'GET':
        return JsonResponse({'error': '잘못된 요청입니다.'}, status=405)
    
    try:
        today = timezone.now().date()
        
        # 오늘 통계
        today_stats = {
            'todayOrders': Order.objects.filter(order_date__date=today).count(),
            'todaySales': float(Order.objects.filter(
                order_date__date=today,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0),
            'new_customers': Order.objects.filter(
                order_date__date=today
            ).values('customer_email').distinct().count()
        }
        
        # 이번 주 통계
        week_ago = today - timedelta(days=7)
        week_stats = {
            'orders': Order.objects.filter(order_date__date__gte=week_ago).count(),
            'sales': float(Order.objects.filter(
                order_date__date__gte=week_ago,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0)
        }
        
        # 재고 알림
        low_stock = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count()
        
        out_of_stock = Product.objects.filter(
            stock_quantity=0,
            status='ACTIVE'
        ).count()
        
        # 플랫폼 상태
        platform_status = {
            'total': Platform.objects.count(),
            'active': Platform.objects.filter(is_active=True).count(),
            'sync_errors': Platform.objects.filter(
                last_sync_status='error'
            ).count()
        }
        
        # 전체 통계
        total_stats = {
            'totalOrders': Order.objects.count(),
            'totalSales': float(Order.objects.filter(
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0),
            'totalProducts': Product.objects.filter(status='ACTIVE').count(),
            'connectedPlatforms': Platform.objects.filter(is_active=True).count(),
            'lowStock': low_stock
        }
        
        return JsonResponse({
            'today': today_stats,
            'week': week_stats,
            'inventory': {
                'low_stock': low_stock,
                'out_of_stock': out_of_stock
            },
            'platforms': platform_status,
            'total': total_stats,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'통계 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=500)