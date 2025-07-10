# reports/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse, Http404
from django.db.models import Sum, Count, Avg, F, Q, Case, When, Value, CharField
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.urls import reverse_lazy
from datetime import datetime, timedelta, date
import json
import csv
import io
import xlsxwriter
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from .forms import *
from django.views.generic import TemplateView
from django.db.models import DecimalField

# 모델 임포트
from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportBookmark
from products.models import Product, Category, Brand
from orders.models import Order, OrderItem
from platforms.models import Platform, PlatformProduct
from inventory.models import StockMovement

# 보고서 생성 유틸리티
from .utils import ReportGenerator, ChartDataGenerator, ExportManager

@login_required
def reports_dashboard(request):
    """보고서 대시보드"""
    # 날짜 계산
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    # ===== 기본 통계 =====
    context = {
        'current_time': timezone.now(),
    }
    
    # 총 매출 (30일)
    try:
        total_revenue = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 이전 30일과 비교
        previous_month = month_ago - timedelta(days=30)
        previous_revenue = Order.objects.filter(
            order_date__date__gte=previous_month,
            order_date__date__lt=month_ago,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        if previous_revenue > 0:
            growth_rate = ((total_revenue - previous_revenue) / previous_revenue) * 100
        else:
            growth_rate = 100 if total_revenue > 0 else 0
            
    except Exception:
        total_revenue = 0
        growth_rate = 0
    
    # 총 주문 (30일)
    try:
        total_orders = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).count()
        
        # 평균 주문 금액
        avg_order_value = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
    except Exception:
        total_orders = 0
        avg_order_value = 0
    
    # 상품 통계
    try:
        total_products = Product.objects.filter(status='ACTIVE').count()
        low_stock_count = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count()
    except Exception:
        total_products = 0
        low_stock_count = 0
    
    # 플랫폼 연동
    try:
        connected_platforms = Platform.objects.filter(is_active=True).count()
    except Exception:
        connected_platforms = 0
    
    # 오늘의 성과
    try:
        today_orders = Order.objects.filter(order_date__date=today,
                                            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']).count()
        today_revenue = Order.objects.filter(
            order_date__date=today,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        today_stock_movements = StockMovement.objects.filter(
            created_at__date=today
        ).count()
        
        new_products_week = Product.objects.filter(
            created_at__date__gte=week_ago
        ).count()
        
    except Exception as e:
        today_orders = 0
        today_revenue = 0
        today_stock_movements = 0
        new_products_week = 0
    
    # 컨텍스트 업데이트
    context.update({
        'total_revenue': total_revenue,
        'growth_rate': growth_rate,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'connected_platforms': connected_platforms,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'today_stock_movements': today_stock_movements,
        'new_products_week': new_products_week,
    })
    
    return render(request, 'reports/dashboard.html', context)

@login_required
def inventory_reports(request):
    """재고 보고서"""
    # 필터링 파라미터
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    stock_status = request.GET.get('stock_status')
    
    # 기본 쿼리셋
    products = Product.objects.select_related('category', 'brand').filter(status='ACTIVE')
    
    # 필터 적용
    if category_id:
        products = products.filter(category_id=category_id)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # 재고 상태 필터
    if stock_status == 'low':
        products = products.filter(stock_quantity__lte=F('min_stock_level'))
    elif stock_status == 'out':
        products = products.filter(stock_quantity=0)
    elif stock_status == 'normal':
        products = products.filter(stock_quantity__gt=F('min_stock_level'))
    
    # 재고 통계
    total_products = products.count()
    total_stock_value = products.aggregate(
        total=Sum(F('stock_quantity') * F('selling_price'))
    )['total'] or 0
    
    low_stock_products = products.filter(stock_quantity__lte=F('min_stock_level'))
    out_of_stock_products = products.filter(stock_quantity=0)
    
    # 카테고리별 재고 현황
    category_stats = products.values('category__name').annotate(
        total_products=Count('id'),
        total_stock=Sum('stock_quantity'),
        total_value=Sum(F('stock_quantity') * F('selling_price')),
        low_stock_count=Count(Case(
            When(stock_quantity__lte=F('min_stock_level'), then=1),
            output_field=CharField()
        ))
    ).order_by('-total_value')[:10]
    
    # 페이지네이션
    paginator = Paginator(products.order_by('-updated_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 필터 옵션
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'page_obj': page_obj,
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock_products.count(),
        'category_stats': category_stats,
        'categories': categories,
        'brands': brands,
        'current_category': category_id,
        'current_brand': brand_id,
        'current_stock_status': stock_status,
    }
    
    return render(request, 'reports/inventory.html', context)

@login_required
def sales_reports(request):
    """매출 보고서"""
    # 기간 설정
    period = request.GET.get('period', '30')
    end_date = timezone.now().date()
    
    if period == '7':
        start_date = end_date - timedelta(days=7)
        period_name = '최근 7일'
    elif period == '30':
        start_date = end_date - timedelta(days=30)
        period_name = '최근 30일'
    elif period == '90':
        start_date = end_date - timedelta(days=90)
        period_name = '최근 90일'
    elif period == '365':
        start_date = end_date - timedelta(days=365)
        period_name = '최근 1년'
    else:
        start_date = end_date - timedelta(days=30)
        period_name = '최근 30일'
    
    # 기본 매출 통계
    orders = Order.objects.filter(
        order_date__date__gte=start_date,
        order_date__date__lte=end_date
    )
    
    total_revenue = orders.filter(
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_orders = orders.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # 일별 매출 (차트 데이터)
    daily_sales = []
    current_date = start_date
    while current_date <= end_date:
        daily_revenue = orders.filter(
            order_date__date=current_date,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        daily_orders = orders.filter(order_date__date=current_date).count()
        
        daily_sales.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'revenue': float(daily_revenue),
            'orders': daily_orders
        })
        current_date += timedelta(days=1)
    
    # 상품별 매출 순위
    try:
        top_products = OrderItem.objects.filter(
            order__order_date__date__gte=start_date,
            order__order_date__date__lte=end_date,
            order__status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).values(
            'product__name', 'product__sku'
        ).annotate(
            total_revenue=Sum('total_price'),
            total_quantity=Sum('quantity'),
            order_count=Count('order', distinct=True)
        ).order_by('-total_revenue')[:10]
    except Exception:
        top_products = []
    
    # 플랫폼별 매출
    try:
        platform_sales = orders.filter(
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).values('platform__name').annotate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('-total_revenue')
    except Exception:
        platform_sales = []
    
    context = {
        'period_name': period_name,
        'current_period': period,
        'start_date': start_date,
        'end_date': end_date,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'avg_order_value': avg_order_value,
        'daily_sales': json.dumps(daily_sales),
        'top_products': top_products,
        'platform_sales': platform_sales,
    }
    
    return render(request, 'reports/sales.html', context)

@login_required
def financial_reports(request):
    """재무 보고서"""
    # 기간 설정
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_end = current_month_start - timedelta(days=1)
    
    # 이번 달 매출
    current_month_revenue = Order.objects.filter(
        order_date__date__gte=current_month_start,
        order_date__date__lte=today,
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # 지난 달 매출
    last_month_revenue = Order.objects.filter(
        order_date__date__gte=last_month_start,
        order_date__date__lte=last_month_end,
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # 성장률 계산
    if last_month_revenue > 0:
        growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
    else:
        growth_rate = 100 if current_month_revenue > 0 else 0
    
    # 재고 자산 가치
    total_inventory_value = Product.objects.filter(
        status='ACTIVE'
    ).aggregate(
        total=Sum(F('stock_quantity') * F('selling_price'))
    )['total'] or 0
    
    # 월별 매출 추이 (최근 12개월)
    monthly_revenue = []
    for i in range(11, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        
        if i == 0:
            month_end = today
        else:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
        
        month_revenue = Order.objects.filter(
            order_date__date__gte=month_start,
            order_date__date__lte=month_end,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(month_revenue)
        })
    
    # 주요 KPI
    total_customers = Order.objects.values('customer_email').distinct().count() if hasattr(Order, 'customer_email') else Order.objects.count()
    avg_order_value = Order.objects.filter(
        order_date__date__gte=current_month_start,
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    context = {
        'current_month_revenue': current_month_revenue,
        'last_month_revenue': last_month_revenue,
        'growth_rate': growth_rate,
        'total_inventory_value': total_inventory_value,
        'monthly_revenue': json.dumps(monthly_revenue),
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'current_month': current_month_start.strftime('%Y년 %m월'),
        'last_month': last_month_start.strftime('%Y년 %m월'),
    }
    
    return render(request, 'reports/financial.html', context)

@login_required
def get_chart_data(request):
    """차트 데이터 API"""
    chart_type = request.GET.get('type', 'sales')
    period = request.GET.get('period', '7')
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=int(period))
    
    if chart_type == 'sales':
        # 일별 매출 데이터
        data = []
        current_date = start_date
        while current_date <= end_date:
            daily_revenue = Order.objects.filter(
                order_date__date=current_date,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data.append({
                'date': current_date.strftime('%m/%d'),
                'value': float(daily_revenue)
            })
            current_date += timedelta(days=1)
        
        return JsonResponse({
            'labels': [item['date'] for item in data],
            'data': [item['value'] for item in data]
        })
    
    elif chart_type == 'category':
        # 카테고리별 판매 데이터
        try:
            category_data = OrderItem.objects.filter(
                order__order_date__date__gte=start_date,
                order__status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).values(
                'product__category__name'
            ).annotate(
                total=Sum('total_price')
            ).order_by('-total')[:5]
            
            labels = [item['product__category__name'] or '미분류' for item in category_data]
            data = [float(item['total']) for item in category_data]
            
        except Exception:
            labels = ['전자제품', '의류', '생활용품']
            data = [300000, 250000, 200000]
        
        return JsonResponse({
            'labels': labels,
            'data': data
        })
    
    return JsonResponse({'error': 'Invalid chart type'}, status=400)

@login_required
def export_report(request, report_type):
    """보고서 내보내기"""
    format_type = request.GET.get('format', 'excel')
    
    if report_type == 'inventory':
        return export_inventory_report(request, format_type)
    elif report_type == 'sales':
        return export_sales_report(request, format_type)
    elif report_type == 'financial':
        return export_financial_report(request, format_type)
    else:
        messages.error(request, '지원하지 않는 보고서 유형입니다.')
        return redirect('reports:dashboard')

def export_inventory_report(request, format_type):
    """재고 보고서 내보내기"""
    products = Product.objects.select_related('category', 'brand').filter(status='ACTIVE')
    
    if format_type == 'excel':
        # Excel 파일 생성
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('재고 보고서')
        
        # 헤더 스타일
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F46E5',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        # 데이터 스타일
        data_format = workbook.add_format({'border': 1, 'align': 'center'})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        currency_format = workbook.add_format({'border': 1, 'num_format': '#,##0"원"'})
        
        # 헤더 작성
        headers = ['SKU', '상품명', '카테고리', '브랜드', '현재재고', '최소재고', '판매가격', '재고가치', '상태']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터 작성
        for row, product in enumerate(products, 1):
            stock_value = product.stock_quantity * product.selling_price
            status = '재고부족' if product.stock_quantity <= product.min_stock_level else '정상'
            
            worksheet.write(row, 0, product.sku, data_format)
            worksheet.write(row, 1, product.name, data_format)
            worksheet.write(row, 2, product.category.name if product.category else '', data_format)
            worksheet.write(row, 3, product.brand.name if product.brand else '', data_format)
            worksheet.write(row, 4, product.stock_quantity, number_format)
            worksheet.write(row, 5, product.min_stock_level, number_format)
            worksheet.write(row, 6, product.selling_price, currency_format)
            worksheet.write(row, 7, stock_value, currency_format)
            worksheet.write(row, 8, status, data_format)
        
        # 컬럼 너비 조정
        worksheet.set_column('A:A', 15)  # SKU
        worksheet.set_column('B:B', 30)  # 상품명
        worksheet.set_column('C:C', 15)  # 카테고리
        worksheet.set_column('D:D', 15)  # 브랜드
        worksheet.set_column('E:E', 10)  # 현재재고
        worksheet.set_column('F:F', 10)  # 최소재고
        worksheet.set_column('G:G', 12)  # 판매가격
        worksheet.set_column('H:H', 15)  # 재고가치
        worksheet.set_column('I:I', 10)  # 상태
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="재고보고서_{timezone.now().strftime("%Y%m%d")}.xlsx"'
        return response
    
    elif format_type == 'csv':
        # CSV 파일 생성
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="재고보고서_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        # BOM 추가 (Excel에서 한글 깨짐 방지)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['SKU', '상품명', '카테고리', '브랜드', '현재재고', '최소재고', '판매가격', '재고가치', '상태'])
        
        for product in products:
            stock_value = product.stock_quantity * product.selling_price
            status = '재고부족' if product.stock_quantity <= product.min_stock_level else '정상'
            
            writer.writerow([
                product.sku,
                product.name,
                product.category.name if product.category else '',
                product.brand.name if product.brand else '',
                product.stock_quantity,
                product.min_stock_level,
                product.selling_price,
                stock_value,
                status
            ])
        
        return response
    
    else:
        messages.error(request, '지원하지 않는 파일 형식입니다.')
        return redirect('reports:inventory')

def export_sales_report(request, format_type):
    """매출 보고서 내보내기"""
    period = request.GET.get('period', '30')
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=int(period))
    
    orders = Order.objects.filter(
        order_date__date__gte=start_date,
        order_date__date__lte=end_date,
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).select_related('platform')
    
    if format_type == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('매출 보고서')
        
        # 스타일 정의
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#059669',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        data_format = workbook.add_format({'border': 1})
        currency_format = workbook.add_format({'border': 1, 'num_format': '#,##0"원"'})
        date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        
        # 헤더
        headers = ['주문번호', '주문일', '플랫폼', '주문금액', '상태', '고객정보']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터
        for row, order in enumerate(orders, 1):
            worksheet.write(row, 0, order.order_number, data_format)
            worksheet.write(row, 1, order.order_date, date_format)
            worksheet.write(row, 2, order.platform.name if order.platform else '', data_format)
            worksheet.write(row, 3, order.total_amount, currency_format)
            worksheet.write(row, 4, order.get_status_display(), data_format)
            worksheet.write(row, 5, getattr(order, 'customer_email', ''), data_format)
        
        # 요약 정보 추가
        summary_row = len(orders) + 3
        worksheet.write(summary_row, 0, '총 주문 수:', header_format)
        worksheet.write(summary_row, 1, len(orders), data_format)
        
        worksheet.write(summary_row + 1, 0, '총 매출:', header_format)
        total_revenue = sum(order.total_amount for order in orders)
        worksheet.write(summary_row + 1, 1, total_revenue, currency_format)
        
        worksheet.write(summary_row + 2, 0, '평균 주문금액:', header_format)
        avg_order = total_revenue / len(orders) if orders else 0
        worksheet.write(summary_row + 2, 1, avg_order, currency_format)
        
        # 컬럼 너비 조정
        worksheet.set_column('A:A', 20)  # 주문번호
        worksheet.set_column('B:B', 12)  # 주문일
        worksheet.set_column('C:C', 15)  # 플랫폼
        worksheet.set_column('D:D', 15)  # 주문금액
        worksheet.set_column('E:E', 12)  # 상태
        worksheet.set_column('F:F', 25)  # 고객정보
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="매출보고서_{start_date}_{end_date}.xlsx"'
        return response
    
    elif format_type == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="매출보고서_{start_date}_{end_date}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['주문번호', '주문일', '플랫폼', '주문금액', '상태', '고객정보'])
        
        for order in orders:
            writer.writerow([
                order.order_number,
                order.order_date.strftime('%Y-%m-%d'),
                order.platform.name if order.platform else '',
                order.total_amount,
                order.get_status_display(),
                getattr(order, 'customer_email', '')
            ])
        
        return response
    
    else:
        messages.error(request, '지원하지 않는 파일 형식입니다.')
        return redirect('reports:sales')

def export_financial_report(request, format_type):
    """재무 보고서 내보내기"""
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # 최근 12개월 데이터
    monthly_data = []
    for i in range(11, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i*30)
        month_start = month_date.replace(day=1)
        
        if i == 0:
            month_end = today
        else:
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            month_end = next_month - timedelta(days=1)
        
        month_revenue = Order.objects.filter(
            order_date__date__gte=month_start,
            order_date__date__lte=month_end,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        month_orders = Order.objects.filter(
            order_date__date__gte=month_start,
            order_date__date__lte=month_end
        ).count()
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': month_revenue,
            'orders': month_orders,
            'avg_order': month_revenue / month_orders if month_orders > 0 else 0
        })
    
    if format_type == 'excel':
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('재무 보고서')
        
        # 스타일
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#7C3AED',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        currency_format = workbook.add_format({'border': 1, 'num_format': '#,##0"원"'})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        data_format = workbook.add_format({'border': 1})
        
        # 헤더
        headers = ['월', '매출액', '주문수', '평균주문금액']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터
        for row, data in enumerate(monthly_data, 1):
            worksheet.write(row, 0, data['month'], data_format)
            worksheet.write(row, 1, data['revenue'], currency_format)
            worksheet.write(row, 2, data['orders'], number_format)
            worksheet.write(row, 3, data['avg_order'], currency_format)
        
        # 총계
        total_row = len(monthly_data) + 2
        total_revenue = sum(data['revenue'] for data in monthly_data)
        total_orders = sum(data['orders'] for data in monthly_data)
        
        worksheet.write(total_row, 0, '총계', header_format)
        worksheet.write(total_row, 1, total_revenue, currency_format)
        worksheet.write(total_row, 2, total_orders, number_format)
        worksheet.write(total_row, 3, total_revenue / total_orders if total_orders > 0 else 0, currency_format)
        
        # 컬럼 너비 조정
        worksheet.set_column('A:A', 10)  # 월
        worksheet.set_column('B:B', 15)  # 매출액
        worksheet.set_column('C:C', 10)  # 주문수
        worksheet.set_column('D:D', 15)  # 평균주문금액
        
        workbook.close()
        output.seek(0)
        
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="재무보고서_{today.strftime("%Y%m")}.xlsx"'
        return response
    
    elif format_type == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="재무보고서_{today.strftime("%Y%m")}.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow(['월', '매출액', '주문수', '평균주문금액'])
        
        for data in monthly_data:
            writer.writerow([
                data['month'],
                data['revenue'],
                data['orders'],
                data['avg_order']
            ])
        
        return response
    
    else:
        messages.error(request, '지원하지 않는 파일 형식입니다.')
        return redirect('reports:financial')

# ===== 클래스 기반 뷰 =====

class ReportTemplateListView(LoginRequiredMixin, ListView):
    """보고서 템플릿 목록"""
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ReportTemplate.objects.filter(is_active=True)
        report_type = self.request.GET.get('type')
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        return queryset.order_by('-created_at')

class GeneratedReportListView(LoginRequiredMixin, ListView):
    """생성된 보고서 목록"""
    model = GeneratedReport
    template_name = 'reports/generated_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return GeneratedReport.objects.filter(
            generated_by=self.request.user
        ).order_by('-generated_at')

@login_required
def download_report(request, report_id):
    """보고서 다운로드"""
    try:
        report = get_object_or_404(GeneratedReport, report_id=report_id)
        
        # 권한 확인
        if report.generated_by != request.user and not request.user.is_staff:
            raise Http404("보고서를 찾을 수 없습니다.")
        
        # 만료 확인
        if report.is_expired:
            messages.error(request, '만료된 보고서입니다.')
            return redirect('reports:generated_list')
        
        # 파일 존재 확인
        if not report.file_path or not os.path.exists(report.file_path):
            messages.error(request, '보고서 파일을 찾을 수 없습니다.')
            return redirect('reports:generated_list')
        
        # 접근 로그 기록
        from .models import ReportAccess
        ReportAccess.objects.create(
            report=report,
            user=request.user,
            action='DOWNLOAD',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # 파일 다운로드
        with open(report.file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            filename = os.path.basename(report.file_path)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except Exception as e:
        messages.error(request, f'다운로드 중 오류가 발생했습니다: {str(e)}')
        return redirect('reports:generated_list')

# ===== API 뷰 =====

@login_required
def api_report_status(request, report_id):
    """보고서 생성 상태 확인 API"""
    try:
        report = get_object_or_404(GeneratedReport, report_id=report_id, generated_by=request.user)
        return JsonResponse({
            'status': report.status,
            'progress': 100 if report.status == 'COMPLETED' else 0,
            'message': '보고서 생성이 완료되었습니다.' if report.status == 'COMPLETED' else '보고서를 생성 중입니다...'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required 
def api_dashboard_summary(request):
    """대시보드 요약 정보 API"""
    today = timezone.now().date()
    
    # 오늘의 주요 지표
    today_orders = Order.objects.filter(order_date__date=today).count()
    today_revenue = Order.objects.filter(
        order_date__date=today,
        status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # 대기 중인 주문
    pending_orders = Order.objects.filter(status='PENDING').count()
    
    # 재고 부족 상품
    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).count()
    
    return JsonResponse({
        'today_orders': today_orders,
        'today_revenue': float(today_revenue),
        'pending_orders': pending_orders,
        'low_stock_count': low_stock_count,
        'last_updated': timezone.now().isoformat()
    })

#====
class ReportTemplateCreateView(LoginRequiredMixin, CreateView):
    """보고서 템플릿 생성"""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '보고서 템플릿이 성공적으로 생성되었습니다.')
        return super().form_valid(form)

class ReportTemplateUpdateView(LoginRequiredMixin, UpdateView):
    """보고서 템플릿 수정"""
    model = ReportTemplate
    form_class = ReportTemplateForm
    template_name = 'reports/template_form.html'
    success_url = reverse_lazy('reports:template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(
            Q(created_by=self.request.user) | Q(is_public=True)
        )
    
    def form_valid(self, form):
        messages.success(self.request, '보고서 템플릿이 성공적으로 수정되었습니다.')
        return super().form_valid(form)

class ReportTemplateDeleteView(LoginRequiredMixin,  DeleteView):
    """보고서 템플릿 삭제"""
    model = ReportTemplate
    template_name = 'reports/template_confirm_delete.html'
    success_url = reverse_lazy('reports:template_list')
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(created_by=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '보고서 템플릿이 성공적으로 삭제되었습니다.')
        return super().delete(request, *args, **kwargs)

class GeneratedReportDetailView(LoginRequiredMixin, DetailView):
    """생성된 보고서 상세"""
    model = GeneratedReport
    template_name = 'reports/generated_detail.html'
    slug_field = 'report_id'
    slug_url_kwarg = 'report_id'
    
    def get_queryset(self):
        return GeneratedReport.objects.filter(
            generated_by=self.request.user
        )

class ReportScheduleListView(LoginRequiredMixin, ListView):
    """보고서 스케줄 목록"""
    model = ReportSchedule
    template_name = 'reports/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 20
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(
            created_by=self.request.user
        ).order_by('-created_at')

class ReportScheduleCreateView(LoginRequiredMixin, CreateView):
    """보고서 스케줄 생성"""
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:schedule_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '보고서 스케줄이 성공적으로 생성되었습니다.')
        return super().form_valid(form)

class ReportScheduleUpdateView(LoginRequiredMixin, UpdateView):
    """보고서 스케줄 수정"""
    model = ReportSchedule
    form_class = ReportScheduleForm
    template_name = 'reports/schedule_form.html'
    success_url = reverse_lazy('reports:schedule_list')
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(created_by=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, '보고서 스케줄이 성공적으로 수정되었습니다.')
        return super().form_valid(form)

class ReportBookmarkListView(LoginRequiredMixin, ListView):
    """보고서 북마크 목록"""
    model = ReportBookmark
    template_name = 'reports/bookmark_list.html'
    context_object_name = 'bookmarks'
    
    def get_queryset(self):
        return ReportBookmark.objects.filter(
            user=self.request.user
        ).select_related('template').order_by('-created_at')

@login_required
def toggle_schedule(request, pk):
    """스케줄 활성화/비활성화 토글"""
    schedule = get_object_or_404(ReportSchedule, pk=pk, created_by=request.user)
    
    schedule.is_active = not schedule.is_active
    schedule.save()
    
    status = '활성화' if schedule.is_active else '비활성화'
    messages.success(request, f'스케줄이 {status}되었습니다.')
    
    return redirect('reports:schedule_list')

@login_required
def add_bookmark(request):
    """보고서 북마크 추가"""
    if request.method == 'POST':
        form = ReportBookmarkForm(request.POST, user=request.user)
        if form.is_valid():
            bookmark = form.save(commit=False)
            bookmark.user = request.user
            bookmark.save()
            messages.success(request, '북마크가 추가되었습니다.')
            return redirect('reports:bookmark_list')
    else:
        form = ReportBookmarkForm(user=request.user)
    
    return render(request, 'reports/bookmark_form.html', {'form': form})

@login_required
def delete_bookmark(request, pk):
    """보고서 북마크 삭제"""
    bookmark = get_object_or_404(ReportBookmark, pk=pk, user=request.user)
    bookmark.delete()
    messages.success(request, '북마크가 삭제되었습니다.')
    return redirect('reports:bookmark_list')

@login_required
def advanced_reports(request):
    """고급 보고서 기능"""
    context = {
        'title': '고급 보고서',
    }
    return render(request, 'reports/advanced.html', context)

@login_required
def comparison_reports(request):
    """비교 보고서"""
    context = {
        'title': '비교 분석',
    }
    return render(request, 'reports/comparison.html', context)

@login_required
def trend_analysis(request):
    """트렌드 분석"""
    context = {
        'title': '트렌드 분석',
    }
    return render(request, 'reports/trends.html', context)

@login_required
def realtime_dashboard(request):
    """실시간 대시보드"""
    context = {
        'title': '실시간 대시보드',
    }
    return render(request, 'reports/realtime.html', context)

@login_required
def report_alerts(request):
    """보고서 알림"""
    context = {
        'title': '보고서 알림',
    }
    return render(request, 'reports/alerts.html', context)

@login_required
def api_generate_report(request):
    """보고서 생성 API"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 메소드만 허용됩니다.'}, status=405)
    
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        filters = data.get('filters', {})
        format_type = data.get('format', 'excel')
        
        if not template_id:
            return JsonResponse({'error': '템플릿 ID가 필요합니다.'}, status=400)
        
        # 비동기 보고서 생성 작업 시작
        from .tasks import generate_report_async
        task = generate_report_async.delay(
            template_id=template_id,
            user_id=request.user.id,
            filters=filters,
            format_type=format_type
        )
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'message': '보고서 생성이 시작되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '올바르지 않은 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_quick_stats(request):
    """빠른 통계 API"""
    try:
        today = timezone.now().date()
        
        # 오늘의 주요 지표
        today_orders = Order.objects.filter(order_date__date=today).count()
        today_revenue = Order.objects.filter(
            order_date__date=today,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # 최근 활동
        recent_reports = GeneratedReport.objects.filter(
            generated_by=request.user
        ).order_by('-generated_at')[:5]
        
        recent_reports_data = [{
            'id': str(report.report_id),
            'title': report.title,
            'status': report.status,
            'generated_at': report.generated_at.isoformat(),
        } for report in recent_reports]
        
        return JsonResponse({
            'today_orders': today_orders,
            'today_revenue': float(today_revenue),
            'recent_reports': recent_reports_data,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

class InventoryReportView(LoginRequiredMixin, TemplateView):
    """실제 데이터 연동 재고 리포트 메인 뷰"""
    template_name = 'reports/inventory.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 카테고리 목록
        try:
            context['categories'] = Category.objects.filter(is_active=True).order_by('name')
        except:
            context['categories'] = []
        
        # 브랜드 목록 (있는 경우)
        try:
            context['brands'] = Brand.objects.filter(is_active=True).order_by('name')
        except:
            context['brands'] = []
        
        # 플랫폼 목록
        try:
            context['platforms'] = Platform.objects.filter(is_active=True).order_by('name')
        except:
            context['platforms'] = []
        
        return context


@login_required
def inventory_report_data(request):
    """재고 리포트 데이터 API"""
    try:
        # 필터 파라미터 받기
        filters = {
            'start_date': request.GET.get('start_date'),
            'end_date': request.GET.get('end_date'),
            'category_id': request.GET.get('category'),
            'brand_id': request.GET.get('brand'),
            'stock_status': request.GET.get('stock_status'),
            'search': request.GET.get('search'),
        }
        
        # 페이지네이션 파라미터
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        sort_by = request.GET.get('sort_by', 'name')
        sort_direction = request.GET.get('sort_direction', 'asc')
        
        # 기본 쿼리셋
        products = Product.objects.select_related('category').filter(status='ACTIVE')
        
        # 필터 적용
        if filters['category_id']:
            products = products.filter(category_id=filters['category_id'])
                
        if filters['search']:
            search_query = filters['search']
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # 재고 상태 필터
        if filters['stock_status']:
            if filters['stock_status'] == 'normal':
                products = products.filter(stock_quantity__gt=F('min_stock_level'))
            elif filters['stock_status'] == 'low':
                products = products.filter(
                    stock_quantity__lte=F('min_stock_level'),
                    stock_quantity__gt=0
                )
            elif filters['stock_status'] == 'out':
                products = products.filter(stock_quantity=0)
        
        # 총 통계 계산
        total_products = products.count()
        
        # 재고 가치 계산
        products_with_value = products.annotate(
            stock_value=Case(
                When(cost_price__isnull=False, then=F('stock_quantity') * F('cost_price')),
                default=F('stock_quantity') * F('selling_price'),
                output_field=DecimalField(max_digits=15, decimal_places=2)
            )
        )
        
        # 통계 계산
        stats = {
            'totalProducts': total_products,
            'totalValue': products_with_value.aggregate(
                total=Sum('stock_value')
            )['total'] or 0,
            'lowStockCount': products.filter(
                stock_quantity__lte=F('min_stock_level'),
                stock_quantity__gt=0
            ).count(),
            'outOfStockCount': products.filter(stock_quantity=0).count(),
        }
        
        # 정렬
        sort_mapping = {
            'name': 'name',
            'stock': 'stock_quantity',
            'value': 'stock_value',
            'category': 'category__name',
        }
        
        if sort_by in sort_mapping:
            sort_field = sort_mapping[sort_by]
            if sort_direction == 'desc':
                sort_field = f'-{sort_field}'
            products_with_value = products_with_value.order_by(sort_field)
        
        # 페이지네이션
        paginator = Paginator(products_with_value, page_size)
        page_obj = paginator.get_page(page)
        
        # 상품 데이터 직렬화
        products_data = []
        for product in page_obj:
            # 재고 상태 결정
            if product.stock_quantity == 0:
                status = 'out'
            elif product.stock_quantity <= product.min_stock_level:
                status = 'low'
            else:
                status = 'normal'
            
            # 재고 가치 계산
            cost_price = getattr(product, 'cost_price', None) or product.selling_price or 0
            stock_value = product.stock_quantity * cost_price
            
            # 상품 이미지 URL
            image_url = None
            try:
                if hasattr(product, 'primary_image') and product.primary_image:
                    image_url = product.primary_image.image.url
                elif hasattr(product, 'images') and product.images.exists():
                    image_url = product.images.first().image.url
            except:
                pass
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'category': product.category.name if product.category else '미분류',
                'current_stock': product.stock_quantity,
                'min_stock': product.min_stock_level,
                'stock_value': float(stock_value),
                'cost_price': float(cost_price),
                'selling_price': float(product.selling_price or 0),
                'status': status,
                'image': image_url,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None,
            })
        
        # 카테고리별 분석
        category_analysis = products.values('category__name').annotate(
            product_count=Count('id'),
            total_stock=Sum('stock_quantity'),
            total_value=Sum(
                Case(
                    When(cost_price__isnull=False, then=F('stock_quantity') * F('cost_price')),
                    default=F('stock_quantity') * F('selling_price'),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                )
            )
        ).order_by('-total_value')[:10]
        
        # 재고 경고 알림 생성
        alerts = []
        
        # 품절 상품 알림
        out_of_stock_products = products.filter(stock_quantity=0)[:5]
        for product in out_of_stock_products:
            alerts.append({
                'id': f'out_of_stock_{product.id}',
                'type': 'error',
                'title': '품절 상품 발생',
                'message': f'{product.name}({product.sku}) 상품의 재고가 소진되었습니다.',
                'product_id': product.id,
                'priority': 'high'
            })
        
        # 재고 부족 상품 알림
        low_stock_products = products.filter(
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        )[:5]
        for product in low_stock_products:
            alerts.append({
                'id': f'low_stock_{product.id}',
                'type': 'warning',
                'title': '재고 부족 경고',
                'message': f'{product.name}({product.sku}) 상품의 재고가 안전재고({product.min_stock_level}) 이하입니다. 현재고: {product.stock_quantity}',
                'product_id': product.id,
                'priority': 'medium'
            })
        
        response_data = {
            'success': True,
            'stats': stats,
            'products': products_data,
            'categoryAnalysis': list(category_analysis),
            'alerts': alerts,
            'pagination': {
                'currentPage': page,
                'totalPages': paginator.num_pages,
                'totalItems': paginator.count,
                'pageSize': page_size,
                'hasNext': page_obj.has_next(),
                'hasPrevious': page_obj.has_previous(),
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def inventory_chart_data(request):
    """재고 차트 데이터 API"""
    try:
        chart_type = request.GET.get('type', 'stock_status')
        
        if chart_type == 'stock_status':
            # 재고 상태별 분포
            products = Product.objects.filter(status='ACTIVE')
            
            normal_count = products.filter(stock_quantity__gt=F('min_stock_level')).count()
            low_count = products.filter(
                stock_quantity__lte=F('min_stock_level'),
                stock_quantity__gt=0
            ).count()
            out_count = products.filter(stock_quantity=0).count()
            
            data = {
                'labels': ['정상', '부족', '품절'],
                'datasets': [{
                    'data': [normal_count, low_count, out_count],
                    'backgroundColor': ['#10b981', '#f59e0b', '#ef4444'],
                    'borderWidth': 0
                }]
            }
            
        elif chart_type == 'category_value':
            # 카테고리별 재고 가치
            category_data = Product.objects.filter(status='ACTIVE').values(
                'category__name'
            ).annotate(
                total_value=Sum(
                    Case(
                        When(cost_price__isnull=False, then=F('stock_quantity') * F('cost_price')),
                        default=F('stock_quantity') * F('selling_price'),
                        output_field=DecimalField(max_digits=15, decimal_places=2)
                    )
                )
            ).order_by('-total_value')[:10]
            
            labels = [item['category__name'] or '미분류' for item in category_data]
            values = [float(item['total_value'] or 0) / 1000000 for item in category_data]  # 백만원 단위
            
            data = {
                'labels': labels,
                'datasets': [{
                    'label': '재고 가치 (백만원)',
                    'data': values,
                    'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                    'borderColor': 'rgba(59, 130, 246, 1)',
                    'borderWidth': 1
                }]
            }
            
        elif chart_type == 'trend':
            # 모의 트렌드 데이터
            days = int(request.GET.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            labels = []
            data_points = []
            
            import random
            base_value = 450
            for i in range(days):
                date = start_date + timedelta(days=i)
                labels.append(date.strftime('%m/%d'))
                value = base_value + random.randint(-30, 30)
                data_points.append(value)
                base_value = value
            
            data = {
                'labels': labels,
                'datasets': [{
                    'label': '총 재고 가치 (백만원)',
                    'data': data_points,
                    'borderColor': 'rgba(59, 130, 246, 1)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'fill': True,
                    'tension': 0.4
                }]
            }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def export_inventory_report(request):
    """재고 리포트 Excel 내보내기"""
    try:
        # 필터 파라미터 받기
        if request.method == 'POST':
            import json
            filters = json.loads(request.body)
        else:
            filters = dict(request.GET)
        
        # 상품 데이터 가져오기
        products = Product.objects.select_related('category').filter(status='ACTIVE')
        
        # 필터 적용
        if filters.get('category_id'):
            products = products.filter(category_id=filters['category_id'])
        if filters.get('search'):
            search_query = filters['search']
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Excel 파일 생성
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('재고현황')
        
        # 헤더 스타일
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F46E5',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # 데이터 스타일
        data_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0'
        })
        
        currency_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0"원"'
        })
        
        # 헤더 작성
        headers = [
            'SKU', '상품명', '카테고리', '현재고', '안전재고', 
            '원가', '판매가', '재고가치', '재고상태', '최종수정일'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터 작성
        for row, product in enumerate(products, 1):
            # 재고 상태 결정
            if product.stock_quantity == 0:
                status = '품절'
            elif product.stock_quantity <= product.min_stock_level:
                status = '부족'
            else:
                status = '정상'
            
            # 재고 가치 계산
            cost_price = getattr(product, 'cost_price', None) or product.selling_price or 0
            stock_value = product.stock_quantity * cost_price
            
            worksheet.write(row, 0, product.sku, data_format)
            worksheet.write(row, 1, product.name, data_format)
            worksheet.write(row, 2, product.category.name if product.category else '미분류', data_format)
            worksheet.write(row, 3, product.stock_quantity, number_format)
            worksheet.write(row, 4, product.min_stock_level, number_format)
            worksheet.write(row, 5, float(cost_price), currency_format)
            worksheet.write(row, 6, float(product.selling_price or 0), currency_format)
            worksheet.write(row, 7, float(stock_value), currency_format)
            worksheet.write(row, 8, status, data_format)
            worksheet.write(row, 9, product.updated_at.strftime('%Y-%m-%d %H:%M') if product.updated_at else '', data_format)
        
        # 열 너비 조정
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 30)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:H', 12)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 18)
        
        workbook.close()
        output.seek(0)
        
        # HTTP 응답
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        filename = f'inventory_report_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'내보내기 실패: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def inventory_alerts_api(request):
    """재고 경고 알림 API"""
    try:
        # 품절 상품
        out_of_stock = Product.objects.filter(
            status='ACTIVE',
            stock_quantity=0
        ).select_related('category')
        
        # 재고 부족 상품
        low_stock = Product.objects.filter(
            status='ACTIVE',
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        ).select_related('category')
        
        alerts = []
        
        # 품절 알림
        for product in out_of_stock[:10]:
            alerts.append({
                'id': f'out_{product.id}',
                'type': 'error',
                'title': '품절 상품',
                'message': f'{product.name} 상품이 품절되었습니다.',
                'product_id': product.id,
                'priority': 'high',
                'created_at': timezone.now().isoformat()
            })
        
        # 재고 부족 알림
        for product in low_stock[:10]:
            alerts.append({
                'id': f'low_{product.id}',
                'type': 'warning',
                'title': '재고 부족',
                'message': f'{product.name} 상품의 재고가 부족합니다. (현재: {product.stock_quantity}, 최소: {product.min_stock_level})',
                'product_id': product.id,
                'priority': 'medium',
                'created_at': timezone.now().isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'alerts': alerts,
            'total_count': len(alerts)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)