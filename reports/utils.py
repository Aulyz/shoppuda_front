# reports/utils.py
import json
import os
import uuid
import xlsxwriter
import io
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F, Q
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from products.models import Product, Category, Brand
from orders.models import Order, OrderItem
from platforms.models import Platform, PlatformProduct
from inventory.models import StockMovement

class ReportGenerator:
    """보고서 생성 유틸리티 클래스"""
    
    def __init__(self, user=None):
        self.user = user
        self.generated_at = timezone.now()
    
    def generate_inventory_report(self, filters=None):
        """재고 보고서 생성"""
        filters = filters or {}
        
        # 기본 쿼리셋
        products = Product.objects.select_related('category', 'brand').filter(status='ACTIVE')
        
        # 필터 적용
        if filters.get('category_id'):
            products = products.filter(category_id=filters['category_id'])
        if filters.get('brand_id'):
            products = products.filter(brand_id=filters['brand_id'])
        if filters.get('low_stock_only'):
            products = products.filter(stock_quantity__lte=F('min_stock_level'))
        
        # 통계 계산
        stats = {
            'total_products': products.count(),
            'total_stock_quantity': products.aggregate(total=Sum('stock_quantity'))['total'] or 0,
            'total_stock_value': products.aggregate(
                total=Sum(F('stock_quantity') * F('selling_price'))
            )['total'] or 0,
            'low_stock_count': products.filter(stock_quantity__lte=F('min_stock_level')).count(),
            'out_of_stock_count': products.filter(stock_quantity=0).count(),
        }
        
        # 카테고리별 분석
        category_analysis = products.values('category__name').annotate(
            product_count=Count('id'),
            total_stock=Sum('stock_quantity'),
            total_value=Sum(F('stock_quantity') * F('selling_price')),
            low_stock_count=Count(
                Q(stock_quantity__lte=F('min_stock_level'))
            )
        ).order_by('-total_value')
        
        # 재고 상태별 분석
        stock_status_analysis = {
            'normal': products.filter(stock_quantity__gt=F('min_stock_level')).count(),
            'low': products.filter(
                stock_quantity__lte=F('min_stock_level'),
                stock_quantity__gt=0
            ).count(),
            'out': products.filter(stock_quantity=0).count(),
        }
        
        return {
            'type': 'inventory',
            'generated_at': self.generated_at,
            'stats': stats,
            'products': list(products.values(
                'sku', 'name', 'category__name', 'brand__name',
                'stock_quantity', 'min_stock_level', 'selling_price'
            )),
            'category_analysis': list(category_analysis),
            'stock_status_analysis': stock_status_analysis,
            'filters_applied': filters,
        }
    
    def generate_sales_report(self, start_date, end_date, filters=None):
        """매출 보고서 생성"""
        filters = filters or {}
        
        # 기본 쿼리셋
        orders = Order.objects.filter(
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        ).select_related('platform')
        
        # 필터 적용
        if filters.get('platform_id'):
            orders = orders.filter(platform_id=filters['platform_id'])
        if filters.get('status'):
            orders = orders.filter(status=filters['status'])
        
        # 기본 통계
        completed_orders = orders.filter(
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        )
        
        stats = {
            'total_orders': orders.count(),
            'completed_orders': completed_orders.count(),
            'total_revenue': completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0,
            'avg_order_value': completed_orders.aggregate(avg=Avg('total_amount'))['avg'] or 0,
            'conversion_rate': (completed_orders.count() / orders.count() * 100) if orders.count() > 0 else 0,
        }
        
        # 일별 매출 추이
        daily_sales = []
        current_date = start_date
        while current_date <= end_date:
            daily_orders = orders.filter(order_date__date=current_date)
            daily_revenue = daily_orders.filter(
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            daily_sales.append({
                'date': current_date.isoformat(),
                'orders': daily_orders.count(),
                'revenue': float(daily_revenue),
            })
            current_date += timedelta(days=1)
        
        # 플랫폼별 분석
        platform_analysis = completed_orders.values('platform__name').annotate(
            order_count=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount')
        ).order_by('-total_revenue')
        
        # 상품별 판매 분석
        try:
            product_analysis = OrderItem.objects.filter(
                order__in=completed_orders
            ).values(
                'product__name', 'product__sku'
            ).annotate(
                quantity_sold=Sum('quantity'),
                total_revenue=Sum('total_price'),
                order_count=Count('order', distinct=True)
            ).order_by('-total_revenue')[:20]
        except Exception:
            product_analysis = []
        
        return {
            'type': 'sales',
            'generated_at': self.generated_at,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'stats': stats,
            'daily_sales': daily_sales,
            'platform_analysis': list(platform_analysis),
            'product_analysis': list(product_analysis),
            'filters_applied': filters,
        }
    
    def generate_financial_report(self, start_date, end_date):
        """재무 보고서 생성"""
        # 매출 데이터
        completed_orders = Order.objects.filter(
            order_date__date__gte=start_date,
            order_date__date__lte=end_date,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        )
        
        total_revenue = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = completed_orders.count()
        
        # 월별 매출 추이
        monthly_revenue = []
        current_month = start_date.replace(day=1)
        
        while current_month <= end_date:
            next_month = (current_month + timedelta(days=32)).replace(day=1)
            month_end = min(next_month - timedelta(days=1), end_date)
            
            month_revenue = completed_orders.filter(
                order_date__date__gte=current_month,
                order_date__date__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            month_orders = completed_orders.filter(
                order_date__date__gte=current_month,
                order_date__date__lte=month_end
            ).count()
            
            monthly_revenue.append({
                'month': current_month.strftime('%Y-%m'),
                'revenue': float(month_revenue),
                'orders': month_orders,
                'avg_order_value': float(month_revenue / month_orders) if month_orders > 0 else 0,
            })
            
            current_month = next_month
        
        # 재고 자산 가치
        inventory_value = Product.objects.filter(
            status='ACTIVE'
        ).aggregate(
            total=Sum(F('stock_quantity') * F('selling_price'))
        )['total'] or 0
        
        # KPI 계산
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # 성장률 계산 (이전 기간과 비교)
        period_days = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_days)
        previous_end = start_date - timedelta(days=1)
        
        previous_revenue = Order.objects.filter(
            order_date__date__gte=previous_start,
            order_date__date__lte=previous_end,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        growth_rate = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
        
        return {
            'type': 'financial',
            'generated_at': self.generated_at,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'summary': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'avg_order_value': float(avg_order_value),
                'inventory_value': float(inventory_value),
                'growth_rate': float(growth_rate),
            },
            'monthly_revenue': monthly_revenue,
        }

class ChartDataGenerator:
    """차트 데이터 생성 클래스"""
    
    @staticmethod
    def get_sales_trend_data(days=30):
        """매출 추이 차트 데이터"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_revenue = Order.objects.filter(
                order_date__date=current_date,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            data.append({
                'date': current_date.strftime('%m/%d'),
                'revenue': float(daily_revenue)
            })
            
            current_date += timedelta(days=1)
        
        return {
            'labels': [item['date'] for item in data],
            'datasets': [{
                'label': '일별 매출',
                'data': [item['revenue'] for item in data],
                'borderColor': 'rgb(59, 130, 246)',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'tension': 0.4
            }]
        }
    
    @staticmethod
    def get_category_distribution_data():
        """카테고리별 판매 분포 데이터"""
        try:
            # 최근 30일 주문 아이템 기준
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            category_data = OrderItem.objects.filter(
                order__order_date__date__gte=start_date,
                order__status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).values(
                'product__category__name'
            ).annotate(
                total_revenue=Sum('total_price')
            ).order_by('-total_revenue')[:6]
            
            labels = [item['product__category__name'] or '미분류' for item in category_data]
            data = [float(item['total_revenue']) for item in category_data]
            
        except Exception:
            # 임시 데이터
            labels = ['전자제품', '의류', '생활용품', '도서', '스포츠']
            data = [300000, 250000, 200000, 150000, 100000]
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': [
                    '#3B82F6', '#10B981', '#F59E0B', 
                    '#EF4444', '#8B5CF6', '#06B6D4'
                ]
            }]
        }
    
    @staticmethod
    def get_platform_performance_data():
        """플랫폼별 성과 데이터"""
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            
            platform_data = Order.objects.filter(
                order_date__date__gte=start_date,
                status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
            ).values('platform__name').annotate(
                total_revenue=Sum('total_amount'),
                order_count=Count('id')
            ).order_by('-total_revenue')
            
            labels = [item['platform__name'] or '직접판매' for item in platform_data]
            revenue_data = [float(item['total_revenue']) for item in platform_data]
            order_data = [item['order_count'] for item in platform_data]
            
        except Exception:
            labels = ['네이버 스마트스토어', '쿠팡', '지마켓', '옥션']
            revenue_data = [500000, 400000, 300000, 200000]
            order_data = [50, 40, 30, 20]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': '매출액',
                    'data': revenue_data,
                    'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                    'yAxisID': 'y'
                },
                {
                    'label': '주문수',
                    'data': order_data,
                    'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                    'yAxisID': 'y1'
                }
            ]
        }

class ExportManager:
    """보고서 내보내기 관리 클래스"""
    
    def __init__(self, report_data):
        self.report_data = report_data
        self.timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    
    def to_excel(self, filename=None):
        """Excel 파일로 내보내기"""
        if not filename:
            filename = f"report_{self.timestamp}.xlsx"
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # 스타일 정의
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F46E5',
            'font_color': 'white',
            'align': 'center',
            'border': 1
        })
        
        data_format = workbook.add_format({'border': 1})
        currency_format = workbook.add_format({'border': 1, 'num_format': '#,##0"원"'})
        number_format = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        
        if self.report_data['type'] == 'inventory':
            self._write_inventory_excel(workbook, header_format, data_format, currency_format, number_format)
        elif self.report_data['type'] == 'sales':
            self._write_sales_excel(workbook, header_format, data_format, currency_format, number_format)
        elif self.report_data['type'] == 'financial':
            self._write_financial_excel(workbook, header_format, data_format, currency_format, number_format)
        
        workbook.close()
        output.seek(0)
        
        return output, filename
    
    def _write_inventory_excel(self, workbook, header_format, data_format, currency_format, number_format):
        """재고 보고서 Excel 작성"""
        worksheet = workbook.add_worksheet('재고 현황')
        
        # 헤더
        headers = ['SKU', '상품명', '카테고리', '브랜드', '현재재고', '최소재고', '판매가격', '재고가치']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터
        for row, product in enumerate(self.report_data['products'], 1):
            stock_value = product['stock_quantity'] * product['selling_price']
            
            worksheet.write(row, 0, product['sku'], data_format)
            worksheet.write(row, 1, product['name'], data_format)
            worksheet.write(row, 2, product['category__name'] or '', data_format)
            worksheet.write(row, 3, product['brand__name'] or '', data_format)
            worksheet.write(row, 4, product['stock_quantity'], number_format)
            worksheet.write(row, 5, product['min_stock_level'], number_format)
            worksheet.write(row, 6, product['selling_price'], currency_format)
            worksheet.write(row, 7, stock_value, currency_format)
        
        # 요약 시트
        summary_sheet = workbook.add_worksheet('요약')
        summary_sheet.write(0, 0, '재고 요약 정보', header_format)
        
        stats = self.report_data['stats']
        summary_data = [
            ['총 상품 수', stats['total_products']],
            ['총 재고 수량', stats['total_stock_quantity']],
            ['총 재고 가치', stats['total_stock_value']],
            ['재고 부족 상품', stats['low_stock_count']],
            ['품절 상품', stats['out_of_stock_count']],
        ]
        
        for row, (label, value) in enumerate(summary_data, 2):
            summary_sheet.write(row, 0, label, data_format)
            if 'value' in label.lower():
                summary_sheet.write(row, 1, value, currency_format)
            else:
                summary_sheet.write(row, 1, value, number_format)
    
    def _write_sales_excel(self, workbook, header_format, data_format, currency_format, number_format):
        """매출 보고서 Excel 작성"""
        # 일별 매출
        daily_sheet = workbook.add_worksheet('일별 매출')
        daily_sheet.write(0, 0, '날짜', header_format)
        daily_sheet.write(0, 1, '주문수', header_format)
        daily_sheet.write(0, 2, '매출액', header_format)
        
        for row, daily in enumerate(self.report_data['daily_sales'], 1):
            daily_sheet.write(row, 0, daily['date'], data_format)
            daily_sheet.write(row, 1, daily['orders'], number_format)
            daily_sheet.write(row, 2, daily['revenue'], currency_format)
        
        # 상품별 판매
        if self.report_data['product_analysis']:
            product_sheet = workbook.add_worksheet('상품별 판매')
            product_sheet.write(0, 0, '상품명', header_format)
            product_sheet.write(0, 1, 'SKU', header_format)
            product_sheet.write(0, 2, '판매수량', header_format)
            product_sheet.write(0, 3, '매출액', header_format)
            product_sheet.write(0, 4, '주문수', header_format)
            
            for row, product in enumerate(self.report_data['product_analysis'], 1):
                product_sheet.write(row, 0, product['product__name'], data_format)
                product_sheet.write(row, 1, product['product__sku'], data_format)
                product_sheet.write(row, 2, product['quantity_sold'], number_format)
                product_sheet.write(row, 3, product['total_revenue'], currency_format)
                product_sheet.write(row, 4, product['order_count'], number_format)
    
    def _write_financial_excel(self, workbook, header_format, data_format, currency_format, number_format):
        """재무 보고서 Excel 작성"""
        worksheet = workbook.add_worksheet('월별 재무')
        
        # 헤더
        headers = ['월', '매출액', '주문수', '평균 주문금액']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 데이터
        for row, monthly in enumerate(self.report_data['monthly_revenue'], 1):
            worksheet.write(row, 0, monthly['month'], data_format)
            worksheet.write(row, 1, monthly['revenue'], currency_format)
            worksheet.write(row, 2, monthly['orders'], number_format)
            worksheet.write(row, 3, monthly['avg_order_value'], currency_format)

class ReportScheduler:
    """보고서 스케줄링 클래스"""
    
    @staticmethod
    def send_scheduled_report(schedule_id):
        """스케줄된 보고서 전송"""
        try:
            from .models import ReportSchedule, GeneratedReport
            
            schedule = ReportSchedule.objects.get(id=schedule_id, is_active=True)
            
            # 보고서 생성
            generator = ReportGenerator(user=schedule.created_by)
            
            if schedule.template.report_type == 'INVENTORY':
                report_data = generator.generate_inventory_report()
            elif schedule.template.report_type == 'SALES':
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
                report_data = generator.generate_sales_report(start_date, end_date)
            elif schedule.template.report_type == 'FINANCIAL':
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=30)
                report_data = generator.generate_financial_report(start_date, end_date)
            else:
                return False
            
            # 파일 생성
            export_manager = ExportManager(report_data)
            file_content, filename = export_manager.to_excel()
            
            # 이메일 전송
            subject = f"[Shopuda ERP] {schedule.template.name} - {timezone.now().strftime('%Y-%m-%d')}"
            
            html_message = render_to_string('reports/email/scheduled_report.html', {
                'schedule': schedule,
                'report_data': report_data,
                'generated_at': timezone.now(),
            })
            
            # 이메일 발송
            for recipient in schedule.email_recipients:
                send_mail(
                    subject=subject,
                    message='',
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient],
                    attachments=[(filename, file_content.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')],
                    fail_silently=False,
                )
            
            # 다음 실행일 업데이트
            schedule.last_run = timezone.now()
            if schedule.interval_days:
                schedule.next_run = timezone.now() + timedelta(days=schedule.interval_days)
            schedule.save()
            
            return True
            
        except Exception as e:
            print(f"스케줄된 보고서 전송 실패: {str(e)}")
            return False

def get_report_summary_stats():
    """보고서 대시보드용 요약 통계"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    try:
        # 매출 통계
        total_revenue = Order.objects.filter(
            order_date__date__gte=month_ago,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        total_orders = Order.objects.filter(
            order_date__date__gte=month_ago
        ).count()
        
        # 상품 통계
        total_products = Product.objects.filter(status='ACTIVE').count()
        low_stock_count = Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count()
        
        # 플랫폼 통계
        connected_platforms = Platform.objects.filter(is_active=True).count()
        
        # 오늘 활동
        today_orders = Order.objects.filter(order_date__date=today).count()
        today_revenue = Order.objects.filter(
            order_date__date=today,
            status__in=['PROCESSING', 'SHIPPED', 'DELIVERED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        return {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'connected_platforms': connected_platforms,
            'today_orders': today_orders,
            'today_revenue': today_revenue,
        }
        
    except Exception as e:
        # 오류 발생 시 기본값 반환
        return {
            'total_revenue': 0,
            'total_orders': 0,
            'total_products': 0,
            'low_stock_count': 0,
            'connected_platforms': 0,
            'today_orders': 0,
            'today_revenue': 0,
        }