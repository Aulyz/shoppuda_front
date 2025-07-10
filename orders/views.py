# File: orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, UpdateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import csv
import json
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

from .models import Order
from platforms.models import Platform


class OrderListView(LoginRequiredMixin, ListView):
    """주문 목록 뷰 - 리뉴얼된 버전"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Order.objects.select_related('platform').order_by('-order_date')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_email__icontains=search) |
                Q(platform_order_id__icontains=search) |
                Q(tracking_number__icontains=search)
            )
        
        # 플랫폼 필터
        platform = self.request.GET.get('platform')
        if platform:
            queryset = queryset.filter(platform_id=platform)
        
        # 상태 필터
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # 날짜 범위 필터
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(order_date__date__lte=date_to)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 통계 데이터
        context['total_orders'] = Order.objects.count()
        context['pending_orders'] = Order.objects.filter(status='PENDING').count()
        context['processing_orders'] = Order.objects.filter(status='PROCESSING').count()
        context['completed_orders'] = Order.objects.filter(status='DELIVERED').count()
        context['shipped_orders'] = Order.objects.filter(status='SHIPPED').count()
        context['cancelled_orders'] = Order.objects.filter(status='CANCELLED').count()
        context['refunded_orders'] = Order.objects.filter(status='REFUNDED').count()
        # 필터용 데이터
        context['platforms'] = Platform.objects.filter(is_active=True)
        
        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """주문 상세 뷰"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.select_related('platform').prefetch_related('items__product')


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    """주문 수정 뷰"""
    model = Order
    template_name = 'orders/order_edit.html'
    fields = [
        'customer_name', 'customer_email', 'customer_phone',
        'shipping_address', 'shipping_zipcode', 'shipping_method',
        'tracking_number', 'notes'
    ]
    
    def get_success_url(self):
        return reverse('orders:detail', kwargs={'pk': self.object.pk})


# 상태별 주문 목록 뷰들
class PendingOrderListView(OrderListView):
    """대기 중인 주문 목록"""
    template_name = 'orders/order_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='PENDING')


class ProcessingOrderListView(OrderListView):
    """처리 중인 주문 목록"""
    template_name = 'orders/order_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='PROCESSING')


class ShippedOrderListView(OrderListView):
    """배송 중인 주문 목록"""
    template_name = 'orders/order_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='SHIPPED')


class DeliveredOrderListView(OrderListView):
    """배송 완료된 주문 목록"""
    template_name = 'orders/order_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='DELIVERED')


class CancelledOrderListView(OrderListView):
    """취소된 주문 목록"""
    template_name = 'orders/order_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(status='CANCELLED')


@login_required
def order_status_update(request, pk):
    """주문 상태 업데이트 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if not new_status:
            return JsonResponse({'error': '상태 값이 필요합니다.'}, status=400)
        
        # 유효한 상태 값 확인
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return JsonResponse({'error': '유효하지 않은 상태입니다.'}, status=400)
        
        old_status = order.status
        order.status = new_status.upper()
        
        # 상태별 추가 처리
        if new_status == 'shipped' and old_status != 'shipped':
            order.shipped_date = timezone.now()
        elif new_status == 'delivered' and old_status != 'delivered':
            order.delivered_date = timezone.now()
        elif new_status == 'cancelled':
            order.cancelled_date = timezone.now()
        
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'주문 상태가 "{order.get_status_display()}"로 변경되었습니다.',
            'new_status': new_status,
            'new_status_display': order.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_bulk_action(request):
    """주문 일괄 작업 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        data = json.loads(request.body)
        action = data.get('action')
        order_ids = data.get('order_ids', [])
        
        if not action or not order_ids:
            return JsonResponse({'error': '액션과 주문 ID가 필요합니다.'}, status=400)
        
        orders = Order.objects.filter(id__in=order_ids)
        updated_count = 0
        
        if action == 'update_status':
            new_status = data.get('status')
            if not new_status:
                return JsonResponse({'error': '상태 값이 필요합니다.'}, status=400)
            
            for order in orders:
                old_status = order.status
                order.status = new_status
                
                # 상태별 추가 처리
                if new_status == 'shipped' and old_status != 'shipped':
                    order.shipped_date = timezone.now()
                elif new_status == 'delivered' and old_status != 'delivered':
                    order.delivered_date = timezone.now()
                elif new_status == 'cancelled':
                    order.cancelled_date = timezone.now()
                
                order.save()
                updated_count += 1
        
        elif action == 'delete':
            updated_count = orders.count()
            orders.delete()
        
        else:
            return JsonResponse({'error': '지원하지 않는 액션입니다.'}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count}개 주문이 처리되었습니다.',
            'updated_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_export_csv(request):
    """주문 데이터 CSV 내보내기"""
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        
        # 현재 날짜를 파일명에 포함
        current_date = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orders_{current_date}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # UTF-8 BOM 추가 (Excel에서 한글 깨짐 방지)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # 헤더 작성
        writer.writerow([
            '주문번호', '플랫폼', '플랫폼주문ID', '고객명', '고객이메일', '고객전화번호',
            '상태', '총금액', '배송비', '할인금액', '주문일시', '배송일시', '배송완료일시',
            '배송주소', '우편번호', '배송방법', '송장번호', '비고'
        ])
        
        # 필터링된 주문 데이터 (ListView와 동일한 로직)
        view = OrderListView()
        view.request = request
        orders = view.get_queryset().select_related('platform')
        
        # 데이터 작성
        for order in orders:
            writer.writerow([
                order.order_number,
                order.platform.name if order.platform else '',
                order.platform_order_id or '',
                order.customer_name,
                order.customer_email or '',
                order.customer_phone or '',
                order.get_status_display(),
                order.total_amount,
                order.shipping_fee,
                order.discount_amount,
                order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
                order.shipped_date.strftime('%Y-%m-%d %H:%M:%S') if order.shipped_date else '',
                order.delivered_date.strftime('%Y-%m-%d %H:%M:%S') if order.delivered_date else '',
                order.shipping_address,
                order.shipping_zipcode or '',
                order.shipping_method or '',
                order.tracking_number or '',
                order.notes or ''
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'CSV 내보내기 중 오류가 발생했습니다: {str(e)}')
        return redirect('orders:list')


@login_required
def order_print(request, pk):
    """주문 인쇄용 페이지"""
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'orders/order_print.html', {'order': order})


@login_required
def order_duplicate(request, pk):
    """주문 복사 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        original_order = get_object_or_404(Order, pk=pk)
        
        # 새 주문 생성
        new_order = Order.objects.create(
            platform=original_order.platform,
            customer_name=original_order.customer_name,
            customer_email=original_order.customer_email,
            customer_phone=original_order.customer_phone,
            shipping_address=original_order.shipping_address,
            shipping_zipcode=original_order.shipping_zipcode,
            shipping_method=original_order.shipping_method,
            total_amount=original_order.total_amount,
            shipping_fee=original_order.shipping_fee,
            discount_amount=original_order.discount_amount,
            status='pending',  # 새 주문은 대기 상태로
            notes=f'복사된 주문 (원본: {original_order.order_number})'
        )
        
        # 주문 아이템도 복사 (있는 경우)
        for item in original_order.items.all():
            item.pk = None
            item.order = new_order
            item.save()
        
        return JsonResponse({
            'success': True,
            'message': '주문이 복사되었습니다.',
            'new_order_id': new_order.id,
            'new_order_number': new_order.order_number
        })
        
    except Exception as e:
        return JsonResponse({'error': f'주문 복사 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_cancel(request, pk):
    """주문 취소 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        
        if order.status in ['delivered', 'cancelled']:
            return JsonResponse({
                'error': '이미 배송완료되었거나 취소된 주문은 취소할 수 없습니다.'
            }, status=400)
        
        order.status = 'cancelled'
        order.cancelled_date = timezone.now()
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': '주문이 취소되었습니다.',
            'new_status': 'cancelled',
            'new_status_display': order.get_status_display()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'주문 취소 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_refund(request, pk):
    """주문 환불 처리 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        data = json.loads(request.body)
        refund_amount = data.get('refund_amount', order.total_amount)
        refund_reason = data.get('refund_reason', '')
        
        if order.status != 'delivered':
            return JsonResponse({
                'error': '배송완료된 주문만 환불 처리할 수 있습니다.'
            }, status=400)
        
        # 환불 처리 로직 (실제로는 결제 게이트웨이 API 호출)
        # 여기서는 단순히 상태만 변경
        order.status = 'refunded'
        order.refund_date = timezone.now()
        order.refund_amount = refund_amount
        order.refund_reason = refund_reason
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{refund_amount}원이 환불 처리되었습니다.',
            'refund_amount': refund_amount
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'환불 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_shipping_update(request, pk):
    """배송 정보 업데이트 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        data = json.loads(request.body)
        
        # 배송 정보 업데이트
        if 'shipping_method' in data:
            order.shipping_method = data['shipping_method']
        
        if 'tracking_number' in data:
            order.tracking_number = data['tracking_number']
            
        if 'shipping_address' in data:
            order.shipping_address = data['shipping_address']
            
        if 'shipping_zipcode' in data:
            order.shipping_zipcode = data['shipping_zipcode']
        
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': '배송 정보가 업데이트되었습니다.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'배송 정보 업데이트 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def order_tracking_update(request, pk):
    """송장번호 업데이트 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        data = json.loads(request.body)
        tracking_number = data.get('tracking_number', '').strip()
        
        if not tracking_number:
            return JsonResponse({'error': '송장번호를 입력해주세요.'}, status=400)
        
        order.tracking_number = tracking_number
        
        # 송장번호가 입력되면 자동으로 배송 중 상태로 변경
        if order.status == 'processing':
            order.status = 'shipped'
            order.shipped_date = timezone.now()
        
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': '송장번호가 등록되었습니다.',
            'tracking_number': tracking_number,
            'status': order.status,
            'status_display': order.get_status_display()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'송장번호 업데이트 중 오류가 발생했습니다: {str(e)}'}, status=500)
    ## 주문 생성 관련

## Email
@login_required
def send_order_email(request, pk):
    """주문 이메일 발송 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=pk)
        data = json.loads(request.body)
        
        # 필수 데이터 검증
        recipient_email = data.get('recipient_email', '').strip()
        recipient_name = data.get('recipient_name', '').strip()
        subject = data.get('subject', '').strip()
        content = data.get('content', '').strip()
        email_template = data.get('template', 'custom')
        include_order_details = data.get('include_order_details', False)
        send_copy_to_admin = data.get('send_copy_to_admin', False)
        
        if not all([recipient_email, recipient_name, subject, content]):
            return JsonResponse({'error': '필수 정보가 누락되었습니다.'}, status=400)
        
        # 이메일 주소 유효성 검사
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(recipient_email)
        except ValidationError:
            return JsonResponse({'error': '올바른 이메일 주소를 입력해주세요.'}, status=400)
        
        # 이메일 내용 템플릿 변수 치환
        email_content = replace_email_variables(content, order)
        email_subject = replace_email_variables(subject, order)
        
        # HTML 이메일 생성
        html_content = generate_email_html(
            email_content, 
            order, 
            include_order_details,
            email_template
        )
        
        # 수신자 목록
        recipient_list = [recipient_email]
        if send_copy_to_admin:
            admin_email = getattr(settings, 'ADMIN_EMAIL', 'shopuda@naver.com')
            recipient_list.append(admin_email)
        
        # 이메일 발송
        try:
            email = EmailMessage(
                subject=email_subject,
                body=html_content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'shopuda@naver.com'),
                to=recipient_list,
                headers={'Content-Type': 'text/html'}
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)
            
            # 이메일 발송 기록 저장 (선택사항)
            save_email_log(order, recipient_email, email_subject, email_template)
            
            logger.info(f"Order email sent successfully: Order {order.order_number} to {recipient_email}")
            
            return JsonResponse({
                'success': True,
                'message': '이메일이 성공적으로 발송되었습니다.',
                'recipient': recipient_email,
                'template': email_template
            })
            
        except Exception as email_error:
            logger.error(f"Email send failed: {str(email_error)}")
            return JsonResponse({
                'error': f'이메일 발송에 실패했습니다: {str(email_error)}'
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f"Order email send error: {str(e)}")
        return JsonResponse({'error': f'오류가 발생했습니다: {str(e)}'}, status=500)


def replace_email_variables(content, order):
    """이메일 템플릿 변수 치환"""
    import re
    from django.utils import timezone
    
    # Django 템플릿 변수 패턴 ({{ variable }})
    def replace_var(match):
        var_name = match.group(1).strip()
        
        # 주문 관련 변수
        if var_name == 'order.order_number':
            return order.order_number
        elif var_name == 'order.customer_name':
            return order.customer_name
        elif var_name == 'order.customer_email':
            return order.customer_email or ''
        elif var_name == 'order.customer_phone':
            return order.customer_phone or ''
        elif var_name == 'order.total_amount|floatformat:0':
            return f"{order.total_amount:,.0f}"
        elif var_name == 'order.get_status_display':
            return order.get_status_display()
        elif var_name == 'order.shipping_address':
            return order.shipping_address or ''
        elif var_name == 'order.shipping_method':
            return order.get_shipping_method_display() if hasattr(order, 'get_shipping_method_display') else ''
        elif var_name == 'order.tracking_number':
            return order.tracking_number or ''
        elif var_name == 'order.platform.name':
            return order.platform.name if order.platform else '직접 주문'
        elif var_name == 'order.created_at|date:"Y년 m월 d일 H:i"':
            return order.created_at.strftime('%Y년 %m월 %d일 %H:%M')
        elif var_name == 'order.shipped_date|date:"Y년 m월 d일 H:i"':
            return order.shipped_date.strftime('%Y년 %m월 %d일 %H:%M') if order.shipped_date else ''
        elif var_name == 'order.delivered_date|date:"Y년 m월 d일 H:i"':
            return order.delivered_date.strftime('%Y년 %m월 %d일 %H:%M') if order.delivered_date else ''
        else:
            return match.group(0)  # 매칭되지 않으면 원본 반환
    
    # 변수 치환
    content = re.sub(r'\{\{\s*([^}]+)\s*\}\}', replace_var, content)
    
    return content


def generate_email_html(content, order, include_order_details=False, template_type='custom'):
    """HTML 이메일 생성"""
    
    # 기본 HTML 템플릿
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shopuda 이메일</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', '맑은 고딕', sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f9fafb;
            }}
            .email-container {{
                max-width: 600px;
                margin: 20px auto;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .logo {{
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .tagline {{
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
                color: #374151;
            }}
            .content pre {{
                white-space: pre-wrap;
                font-family: inherit;
                margin: 0;
            }}
            .order-details {{
                margin-top: 30px;
                padding: 20px;
                background: #f8fafc;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
            }}
            .order-details h3 {{
                margin-top: 0;
                color: #1f2937;
                border-bottom: 2px solid #3b82f6;
                padding-bottom: 10px;
            }}
            .details-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }}
            .detail-item {{
                padding: 10px;
                background: white;
                border-radius: 6px;
                border-left: 4px solid #3b82f6;
            }}
            .detail-label {{
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 5px;
            }}
            .detail-value {{
                font-weight: 600;
                color: #1f2937;
            }}
            .items-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            .items-table th,
            .items-table td {{
                padding: 12px;
                text-align: left;
                border: 1px solid #e2e8f0;
            }}
            .items-table th {{
                background: #f1f5f9;
                font-weight: 600;
                color: #1f2937;
            }}
            .items-table tbody tr:nth-child(even) {{
                background: #f8fafc;
            }}
            .total-row {{
                background: #3b82f6 !important;
                color: white;
                font-weight: bold;
            }}
            .footer {{
                background: #f8fafc;
                padding: 20px 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
                color: #6b7280;
                font-size: 14px;
            }}
            .footer a {{
                color: #3b82f6;
                text-decoration: none;
            }}
            @media (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 0;
                }}
                .details-grid {{
                    grid-template-columns: 1fr;
                }}
                .header, .content, .footer {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="logo">📦 Shopuda</div>
                <div class="tagline">온라인 쇼핑몰 통합 관리 시스템</div>
            </div>
            
            <div class="content">
                <pre>{content}</pre>
            </div>
            
            {generate_order_details_html(order) if include_order_details else ''}
            
            <div class="footer">
                <p>본 메일은 Shopuda ERP 시스템에서 자동 발송되었습니다.</p>
                <p>
                    문의사항: <a href="mailto:support@shopuda.com">support@shopuda.com</a> |
                    전화: 02-1234-5678
                </p>
                <p style="margin-top: 15px; font-size: 12px; color: #9ca3af;">
                    © 2024 Shopuda. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template


def generate_order_details_html(order):
    """주문 상세 정보 HTML 생성"""
    items_html = ""
    if hasattr(order, 'items') and order.items.exists():
        for item in order.items.all():
            items_html += f"""
            <tr>
                <td>{item.product.name}</td>
                <td>{item.product.sku}</td>
                <td style="text-align: center;">{item.quantity}개</td>
                <td style="text-align: right;">₩{item.unit_price:,.0f}</td>
                <td style="text-align: right;">₩{item.total_price:,.0f}</td>
            </tr>
            """
    
    return f"""
    <div class="order-details">
        <h3>📋 주문 상세 정보</h3>
        
        <div class="details-grid">
            <div class="detail-item">
                <div class="detail-label">주문번호</div>
                <div class="detail-value">{order.order_number}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">주문일시</div>
                <div class="detail-value">{order.created_at.strftime('%Y년 %m월 %d일 %H:%M')}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">주문상태</div>
                <div class="detail-value">{order.get_status_display()}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">플랫폼</div>
                <div class="detail-value">{order.platform.name if order.platform else '직접 주문'}</div>
            </div>
        </div>
        
        {f'''
        <div style="margin-top: 20px;">
            <h4 style="margin-bottom: 10px; color: #1f2937;">🚚 배송 정보</h4>
            <div style="padding: 15px; background: white; border-radius: 6px;">
                <p style="margin: 5px 0;"><strong>배송지:</strong> {order.shipping_address}</p>
                {f'<p style="margin: 5px 0;"><strong>우편번호:</strong> {order.shipping_zipcode}</p>' if order.shipping_zipcode else ''}
                {f'<p style="margin: 5px 0;"><strong>운송장 번호:</strong> {order.tracking_number}</p>' if order.tracking_number else ''}
            </div>
        </div>
        ''' if order.shipping_address else ''}
        
        {f'''
        <table class="items-table">
            <thead>
                <tr>
                    <th>상품명</th>
                    <th>SKU</th>
                    <th style="text-align: center;">수량</th>
                    <th style="text-align: right;">단가</th>
                    <th style="text-align: right;">합계</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
                <tr class="total-row">
                    <td colspan="4" style="text-align: right; font-weight: bold;">총 주문 금액:</td>
                    <td style="text-align: right; font-weight: bold;">₩{order.total_amount:,.0f}</td>
                </tr>
            </tbody>
        </table>
        ''' if hasattr(order, 'items') and order.items.exists() else ''}
    </div>
    """


def save_email_log(order, recipient_email, subject, template):
    """이메일 발송 기록 저장 (선택사항)"""
    try:
        # EmailLog 모델이 있다면 여기서 저장
        # EmailLog.objects.create(
        #     order=order,
        #     recipient_email=recipient_email,
        #     subject=subject,
        #     template=template,
        #     sent_at=timezone.now(),
        #     sent_by=request.user if hasattr(request, 'user') else None
        # )
        pass
    except Exception as e:
        logger.warning(f"Failed to save email log: {str(e)}")
