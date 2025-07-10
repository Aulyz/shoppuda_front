# inventory/views.py - 완성된 재고 조정 기능
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Case, When, Value, IntegerField
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods
import csv
import json
import logging
import random
from datetime import timedelta
import decimal

from products.models import Product, Category

# StockMovement 모델 안전한 import
try:
    from .models import StockMovement
    HAS_STOCK_MOVEMENT = True
except ImportError:
    HAS_STOCK_MOVEMENT = False
    StockMovement = None

logger = logging.getLogger(__name__)

@login_required
def stock_overview(request):
    """재고 현황 대시보드"""
    # 기본 통계
    total_products = Product.objects.filter(status='ACTIVE').count()
    
    # 재고 상태별 카운트
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    )
    low_stock_count = low_stock_products.count()
    
    out_of_stock_products = Product.objects.filter(
        stock_quantity=0,
        status='ACTIVE'
    )
    out_of_stock_count = out_of_stock_products.count()
    
    overstock_products = Product.objects.filter(
        stock_quantity__gt=F('max_stock_level'),
        status='ACTIVE'
    )
    overstock_count = overstock_products.count()
    
    # 총 재고 가치
    total_stock_value = Product.objects.filter(status='ACTIVE').aggregate(
        total=Sum(F('stock_quantity') * F('cost_price'))
    )['total'] or 0
    
    # 최근 재고 이동 (StockMovement가 있는 경우만)
    recent_movements = []
    if HAS_STOCK_MOVEMENT:
        recent_movements = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:10]
    
    # 위험 재고 상품 (재고 부족 + 재고 없음)
    critical_products = Product.objects.filter(
        Q(stock_quantity__lte=F('min_stock_level')) | Q(stock_quantity=0),
        status='ACTIVE'
    ).order_by('stock_quantity')[:5]
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'overstock_count': overstock_count,
        'total_stock_value': total_stock_value,
        'recent_movements': recent_movements,
        'critical_products': critical_products,
        'has_stock_movement': HAS_STOCK_MOVEMENT,
    }
    
    return render(request, 'inventory/overview.html', context)

@login_required
def stock_adjustment(request):
    """재고 조정 페이지"""
    # 검색 및 필터링
    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '')
    stock_status = request.GET.get('stock_status', '')
    
    # 기본 쿼리셋
    products = Product.objects.select_related('brand', 'category').filter(status='ACTIVE')
    
    # 검색 필터
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search) |
            Q(brand__name__icontains=search)
        )
    
    # 카테고리 필터
    if category:
        products = products.filter(category_id=category)
    
    # 재고 상태 필터
    if stock_status:
        if stock_status == 'low':
            products = products.filter(stock_quantity__lte=F('min_stock_level'))
        elif stock_status == 'normal':
            products = products.filter(
                stock_quantity__gt=F('min_stock_level'),
                stock_quantity__lte=F('max_stock_level')
            )
        elif stock_status == 'excess':
            products = products.filter(stock_quantity__gt=F('max_stock_level'))
        elif stock_status == 'out':
            products = products.filter(stock_quantity=0)
    
    # 통계 계산
    total_products = products.count()
    low_stock_count = products.filter(stock_quantity__lte=F('min_stock_level')).count()
    out_of_stock_count = products.filter(stock_quantity=0).count()
    overstock_count = products.filter(stock_quantity__gt=F('max_stock_level')).count()
    
    # 우선순위별 정렬 (재고 없음 > 재고 부족 > 정상 > 과다)
    products = products.annotate(
        stock_priority=Case(
            When(stock_quantity=0, then=Value(0)),  # 재고 없음
            When(stock_quantity__lte=F('min_stock_level'), then=Value(1)),  # 재고 부족
            When(stock_quantity__gt=F('max_stock_level'), then=Value(3)),  # 과다 재고
            default=Value(2),  # 정상
            output_field=IntegerField(),
        )
    ).order_by('stock_priority', 'sku')
    
    # 페이지네이션
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 필터용 카테고리 목록
    active_product_category_ids = Product.objects.filter(
        status='ACTIVE', 
        category__isnull=False
    ).values_list('category_id', flat=True).distinct()
    
    categories = Category.objects.filter(
        id__in=active_product_category_ids,
        is_active=True
    ).order_by('name')
    
    context = {
        # 통계
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'overstock_count': overstock_count,
        
        # 데이터
        'products': page_obj,
        'categories': categories,
        
        # 검색 상태
        'has_search': bool(search or category or stock_status),
        'search_query': search,
        'selected_category': category,
        'selected_stock_status': stock_status,
    }
    
    return render(request, 'inventory/stock_adjustment.html', context)

@login_required
@require_http_methods(["POST"])
def apply_stock_adjustment(request):
    """개별 재고 조정 적용 - AJAX"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        adjustment_type = data.get('adjustment_type', 'set')
        reason = data.get('reason', '재고 조정').strip()
        
        if not reason:
            return JsonResponse({'error': '조정 사유를 입력해주세요.'}, status=400)
        
        # 조정 값 검증
        if adjustment_type == 'set':
            new_quantity = data.get('new_quantity')
            if new_quantity is None or new_quantity < 0:
                return JsonResponse({'error': '올바른 수량을 입력해주세요.'}, status=400)
        else:
            adjustment_value = data.get('adjustment_value')
            if adjustment_value is None or adjustment_value < 0:
                return JsonResponse({'error': '조정할 수량을 입력해주세요.'}, status=400)
        
        # 상품 조회
        try:
            product = Product.objects.get(id=product_id, status='ACTIVE')
        except Product.DoesNotExist:
            return JsonResponse({'error': '상품을 찾을 수 없습니다.'}, status=404)
        
        old_quantity = product.stock_quantity
        
        # 새 수량 계산
        if adjustment_type == 'set':
            new_quantity = int(new_quantity)
        elif adjustment_type == 'add':
            new_quantity = old_quantity + int(adjustment_value)
        elif adjustment_type == 'subtract':
            new_quantity = old_quantity - int(adjustment_value)
            if new_quantity < 0:
                return JsonResponse({'error': '재고 수량이 음수가 될 수 없습니다.'}, status=400)
        else:
            return JsonResponse({'error': '올바르지 않은 조정 타입입니다.'}, status=400)
        
        # 트랜잭션으로 안전하게 처리
        with transaction.atomic():
            # 재고 업데이트
            product.stock_quantity = new_quantity

            product.save(update_fields=['stock_quantity', 'updated_at'])
            
            # 재고 이동 기록 생성 (StockMovement 모델이 있는 경우만)
            quantity_change = abs(new_quantity - old_quantity)
            if HAS_STOCK_MOVEMENT and quantity_change > 0:
                StockMovement.objects.create(
                    product=product,
                    movement_type='ADJUST',
                    quantity=quantity_change,
                    previous_stock=old_quantity,
                    current_stock=new_quantity,
                    reference_number=f'ADJ-{timezone.now().strftime("%Y%m%d%H%M%S")}-{product.id}',
                    reason=reason,
                    notes=f'재고 조정: {old_quantity}개 → {new_quantity}개',
                    created_by=request.user
                )
        
        # 상태 메시지 생성
        if new_quantity == old_quantity:
            message = f'{product.name}의 재고가 변경되지 않았습니다.'
        else:
            change_text = f"{old_quantity}개에서 {new_quantity}개로"
            message = f'{product.name}의 재고가 {change_text} 조정되었습니다.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'product_name': product.name,
            'product_id': str(product.id)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': f'올바른 숫자를 입력해주세요: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f'재고 조정 오류: {str(e)}', exc_info=True)
        return JsonResponse({'error': '재고 조정 중 오류가 발생했습니다.'}, status=500)

@login_required
@require_http_methods(["POST"])
def apply_bulk_stock_adjustment(request):
    """일괄 재고 조정 적용 - AJAX"""
    try:
        data = json.loads(request.body)
        product_ids = data.get('product_ids', [])
        adjustment_type = data.get('adjustment_type', 'set')
        adjustment_value = data.get('adjustment_value')
        reason = data.get('reason', '일괄 재고 조정').strip()
        
        if not product_ids:
            return JsonResponse({'error': '조정할 상품을 선택해주세요.'}, status=400)
        
        if adjustment_value is None or adjustment_value < 0:
            return JsonResponse({'error': '올바른 조정 값을 입력해주세요.'}, status=400)
        
        if not reason:
            return JsonResponse({'error': '조정 사유를 입력해주세요.'}, status=400)
        
        successful_adjustments = []
        failed_adjustments = []
        
        # 트랜잭션으로 일괄 처리
        with transaction.atomic():
            for product_id in product_ids:
                try:
                    product = Product.objects.get(id=product_id, status='ACTIVE')
                    old_quantity = product.stock_quantity
                    
                    # 새 수량 계산
                    if adjustment_type == 'set':
                        new_quantity = int(adjustment_value)
                    elif adjustment_type == 'add':
                        new_quantity = old_quantity + int(adjustment_value)
                    elif adjustment_type == 'subtract':
                        new_quantity = old_quantity - int(adjustment_value)
                        if new_quantity < 0:
                            failed_adjustments.append({
                                'product_name': product.name,
                                'reason': '재고 수량이 음수가 될 수 없습니다.'
                            })
                            continue
                    else:
                        failed_adjustments.append({
                            'product_name': product.name,
                            'reason': '올바르지 않은 조정 타입입니다.'
                        })
                        continue
                    
                    # 재고 업데이트
                    product.stock_quantity = new_quantity
                    product.save(update_fields=['stock_quantity', 'updated_at'])
                    
                    # 재고 이동 기록 생성
                    if HAS_STOCK_MOVEMENT and new_quantity != old_quantity:
                        quantity_change = abs(new_quantity - old_quantity)
                        
                        StockMovement.objects.create(
                            product=product,
                            movement_type='ADJUST',
                            quantity=quantity_change,
                            previous_stock=old_quantity,
                            current_stock=new_quantity,
                            reference_number=f'BULK-ADJ-{timezone.now().strftime("%Y%m%d%H%M%S")}-{product.id}',
                            reason=reason,
                            notes=f'일괄 재고 조정: {old_quantity}개 → {new_quantity}개',
                            created_by=request.user
                        )
                    
                    successful_adjustments.append({
                        'product_name': product.name,
                        'old_quantity': old_quantity,
                        'new_quantity': new_quantity
                    })
                    
                except Product.DoesNotExist:
                    failed_adjustments.append({
                        'product_name': f'상품 ID {product_id}',
                        'reason': '상품을 찾을 수 없습니다.'
                    })
                except Exception as e:
                    failed_adjustments.append({
                        'product_name': f'상품 ID {product_id}',
                        'reason': str(e)
                    })
        
        # 결과 메시지 생성
        success_count = len(successful_adjustments)
        fail_count = len(failed_adjustments)
        
        if success_count > 0 and fail_count == 0:
            message = f'{success_count}개 상품의 재고가 성공적으로 조정되었습니다.'
        elif success_count > 0 and fail_count > 0:
            message = f'{success_count}개 상품 조정 완료, {fail_count}개 상품 조정 실패'
        else:
            message = '모든 상품의 재고 조정에 실패했습니다.'
        
        return JsonResponse({
            'success': success_count > 0,
            'message': message,
            'successful_count': success_count,
            'failed_count': fail_count,
            'successful_adjustments': successful_adjustments,
            'failed_adjustments': failed_adjustments
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f'일괄 재고 조정 오류: {str(e)}', exc_info=True)
        return JsonResponse({'error': '일괄 재고 조정 중 오류가 발생했습니다.'}, status=500)

@login_required
def export_stock_data(request):
    """재고 데이터 CSV 내보내기"""
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        current_date = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'stock_data_{current_date}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # UTF-8 BOM 추가 (엑셀에서 한글 깨짐 방지)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'SKU', '상품명', '브랜드', '카테고리', '현재재고', '최소재고', '최대재고', 
            '재고상태', '판매가격', '원가', '재고가치', '등록일', '수정일'
        ])
        
        # 현재 필터 조건 적용 (URL 파라미터 기반)
        search = request.GET.get('search', '').strip()
        category = request.GET.get('category', '')
        stock_status = request.GET.get('stock_status', '')
        
        products = Product.objects.select_related('brand', 'category').filter(status='ACTIVE')
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(brand__name__icontains=search)
            )
        
        if category:
            products = products.filter(category_id=category)
        
        if stock_status:
            if stock_status == 'low':
                products = products.filter(stock_quantity__lte=F('min_stock_level'))
            elif stock_status == 'normal':
                products = products.filter(
                    stock_quantity__gt=F('min_stock_level'),
                    stock_quantity__lte=F('max_stock_level')
                )
            elif stock_status == 'excess':
                products = products.filter(stock_quantity__gt=F('max_stock_level'))
            elif stock_status == 'out':
                products = products.filter(stock_quantity=0)
        
        # 데이터 작성
        for product in products:
            # 재고 상태 판단
            if product.stock_quantity == 0:
                stock_status_text = '재고없음'
            elif product.stock_quantity <= product.min_stock_level:
                stock_status_text = '부족'
            elif product.stock_quantity > product.max_stock_level:
                stock_status_text = '과다'
            else:
                stock_status_text = '정상'
            
            # 재고 가치 계산
            stock_value = product.stock_quantity * (product.cost_price or 0)
            
            writer.writerow([
                product.sku,
                product.name,
                product.brand.name if product.brand else '',
                product.category.name if product.category else '',
                product.stock_quantity,
                product.min_stock_level,
                product.max_stock_level,
                stock_status_text,
                product.selling_price,
                product.cost_price or 0,
                stock_value,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'데이터 내보내기 중 오류가 발생했습니다: {str(e)}')
        return redirect('inventory:adjustment')

@login_required
def export_movement_data(request):
    """재고 이동 데이터 CSV 내보내기"""
    if not HAS_STOCK_MOVEMENT:
        messages.error(request, '재고 이동 기록 기능이 활성화되지 않았습니다.')
        return redirect('inventory:adjustment')
    
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        current_date = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'stock_movements_{current_date}.csv'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')  # UTF-8 BOM
        
        writer = csv.writer(response)
        writer.writerow([
            '일시', '상품SKU', '상품명', '이동타입', '수량', '이전재고', '현재재고', '참조번호', '사유', '작업자'
        ])
        
        # 최근 1000개 이동 기록
        movements = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:1000]
        
        for movement in movements:
            writer.writerow([
                movement.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                movement.product.sku,
                movement.product.name,
                movement.get_movement_type_display(),
                movement.quantity,
                movement.previous_stock,
                movement.current_stock,
                movement.reference_number,
                movement.reason,
                movement.created_by.username if movement.created_by else ''
            ])
        
        return response
        
    except Exception as e:
        messages.error(request, f'이동 데이터 내보내기 중 오류가 발생했습니다: {str(e)}')
        return redirect('inventory:movements')

# ListView 클래스들
class StockListView(LoginRequiredMixin, ListView):
    """전체 재고 목록"""
    model = Product
    template_name = 'inventory/stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('brand', 'category').filter(status='ACTIVE')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        
        return queryset.order_by('sku')

class StockMovementListView(LoginRequiredMixin, ListView):
    """재고 이동 이력"""
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 50
    
    def get_queryset(self):
        if not HAS_STOCK_MOVEMENT:
            return Product.objects.none()
        
        return StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')

class LowStockListView(LoginRequiredMixin, ListView):
    """부족 재고 목록"""
    model = Product
    template_name = 'inventory/low_stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).select_related('brand', 'category').order_by('stock_quantity')

class OutOfStockListView(LoginRequiredMixin, ListView):
    """재고 없음 목록"""
    model = Product
    template_name = 'inventory/out_of_stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(
            stock_quantity=0,
            status='ACTIVE'
        ).select_related('brand', 'category').order_by('sku')

class OverstockListView(LoginRequiredMixin, ListView):
    """과다 재고 목록"""
    model = Product
    template_name = 'inventory/overstock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(
            stock_quantity__gt=F('max_stock_level'),
            status='ACTIVE'
        ).select_related('brand', 'category').order_by('-stock_quantity')

# API 엔드포인트들
@login_required
def stock_check_api(request):
    """재고 확인 API"""
    sku = request.GET.get('sku')
    if not sku:
        return JsonResponse({'error': 'SKU가 필요합니다.'}, status=400)
    
    try:
        product = Product.objects.get(sku=sku, status='ACTIVE')
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'stock_quantity': product.stock_quantity,
                'min_stock_level': product.min_stock_level,
                'max_stock_level': product.max_stock_level,
                'is_low_stock': product.stock_quantity <= product.min_stock_level,
                'is_out_of_stock': product.stock_quantity == 0,
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({'error': '상품을 찾을 수 없습니다.'}, status=404)

@login_required
@require_http_methods(["POST"])
def stock_adjust_api(request):
    """재고 조정 API (외부 시스템 연동용)"""
    try:
        data = json.loads(request.body)
        sku = data.get('sku')
        new_quantity = data.get('quantity')
        reason = data.get('reason', 'API 재고 조정')
        
        if not sku or new_quantity is None:
            return JsonResponse({'error': 'SKU와 수량이 필요합니다.'}, status=400)
        
        if new_quantity < 0:
            return JsonResponse({'error': '재고 수량은 0 이상이어야 합니다.'}, status=400)
        
        try:
            product = Product.objects.get(sku=sku, status='ACTIVE')
        except Product.DoesNotExist:
            return JsonResponse({'error': '상품을 찾을 수 없습니다.'}, status=404)
        
        old_quantity = product.stock_quantity
        
        with transaction.atomic():
            product.stock_quantity = int(new_quantity)
            product.save(update_fields=['stock_quantity', 'updated_at'])
            
            # 재고 이동 기록
            if HAS_STOCK_MOVEMENT and new_quantity != old_quantity:
                quantity_change = abs(new_quantity - old_quantity)
                
                StockMovement.objects.create(
                    product=product,
                    movement_type='ADJUST',
                    quantity=quantity_change,
                    previous_stock=old_quantity,
                    current_stock=new_quantity,
                    reference_number=f'API-ADJ-{timezone.now().strftime("%Y%m%d%H%M%S")}-{product.id}',
                    reason=reason,
                    notes=f'API 재고 조정: {old_quantity}개 → {new_quantity}개',
                    created_by=request.user
                )
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name}의 재고가 {old_quantity}개에서 {new_quantity}개로 조정되었습니다.',
            'old_quantity': old_quantity,
            'new_quantity': new_quantity
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        logger.error(f'API 재고 조정 오류: {str(e)}', exc_info=True)
        return JsonResponse({'error': '재고 조정 중 오류가 발생했습니다.'}, status=500)
    
# 재고 관리
@login_required
def inventory_overview(request):
    """재고 관리 개요 대시보드"""
    
    # 날짜 계산
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ===========================================
    # 1. 주요 지표 (Metrics)
    # ===========================================
    
    # 총 상품 수
    total_products = Product.objects.filter(status='ACTIVE').count()
    
    # 총 재고 가치 계산 (cost_price 사용)
    total_value = Product.objects.filter(status='ACTIVE').aggregate(
        total=Sum(F('stock_quantity') * F('cost_price'))
    )['total'] or 0
    
    # 부족 재고 상품 수
    low_stock_count = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).count()
    
    # 품절 상품 수
    out_of_stock_count = Product.objects.filter(
        stock_quantity=0,
        status='ACTIVE'
    ).count()
    
    # 지난 달 대비 성장률 계산 (임시로 랜덤 값 사용, 실제로는 월별 데이터 비교)
    products_growth = f"+{random.uniform(5, 15):.1f}%"
    value_growth = f"+{random.uniform(3, 12):.1f}%"
    
    # ===========================================
    # 2. 재고 상태 분포
    # ===========================================
    
    # 정상 재고 (최소 재고 이상)
    normal_stock = Product.objects.filter(
        stock_quantity__gt=F('min_stock_level'),
        status='ACTIVE'
    ).count()
    
    # 주의 재고 (최소 재고 이하이지만 0이 아님)
    warning_stock = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        stock_quantity__gt=0,
        status='ACTIVE'
    ).count()
    
    # 위험 재고 (품절)
    critical_stock = out_of_stock_count
    
    # 퍼센티지 계산
    if total_products > 0:
        normal_percent = round((normal_stock / total_products) * 100)
        warning_percent = round((warning_stock / total_products) * 100)
        critical_percent = round((critical_stock / total_products) * 100)
    else:
        normal_percent = warning_percent = critical_percent = 0
    
    # ===========================================
    # 3. 부족 재고 목록
    # ===========================================
    
    low_stock_items = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).annotate(
        deficit=F('min_stock_level') - F('stock_quantity')
    ).values(
        'id', 'name', 'stock_quantity', 'min_stock_level', 'deficit'
    ).order_by('stock_quantity')[:10]
    
    # ===========================================
    # 4. 카테고리별 통계
    # ===========================================
    
    category_stats = []
    try:
        # 단순화된 카테고리 통계
        categories = Category.objects.filter(is_active=True)
        
        # 카테고리별 아이콘 및 색상 매핑
        category_icons = {
            '전자제품': {'icon': 'fas fa-laptop', 'color': '#3b82f6'},
            '의류': {'icon': 'fas fa-tshirt', 'color': '#10b981'},
            '가전제품': {'icon': 'fas fa-tv', 'color': '#f59e0b'},
            '생활용품': {'icon': 'fas fa-home', 'color': '#8b5cf6'},
            '뷰티': {'icon': 'fas fa-gem', 'color': '#ec4899'},
            '스포츠': {'icon': 'fas fa-dumbbell', 'color': '#06b6d4'},
            '기타': {'icon': 'fas fa-box', 'color': '#6b7280'},
        }
        
        for category in categories:
            # 각 카테고리별로 개별 쿼리 실행
            products_in_category = Product.objects.filter(
                category=category,
                status='ACTIVE'
            )
            
            product_count = products_in_category.count()
            if product_count > 0:
                # 카테고리 총 가치 계산
                total_value = 0
                for product in products_in_category:
                    total_value += (product.stock_quantity * product.cost_price)
                
                icon_data = category_icons.get(category.name, category_icons['기타'])
                category_stats.append({
                    'name': category.name,
                    'count': product_count,
                    'value': float(total_value),
                    'trend': random.uniform(-5, 15),  # 실제로는 월별 비교 데이터 사용
                    'color': icon_data['color'],
                    'icon': icon_data['icon']
                })
    except Exception as e:
        logger.error(f"카테고리 통계 계산 중 오류: {str(e)}")
        # 오류 발생시 빈 리스트 사용
    
    # ===========================================
    # 5. 최근 재고 이동 내역
    # ===========================================
    
    recent_movements = []
    if HAS_STOCK_MOVEMENT:
        movements = StockMovement.objects.select_related('product').order_by('-created_at')[:10]
        
        for movement in movements:
            quantity_change = movement.current_stock - movement.previous_stock
            
            # 이동 유형 표시명 매핑
            type_display_map = {
                'IN': '입고',
                'OUT': '출고', 
                'ADJUST': '조정',
                'SALE': '판매',
                'PURCHASE': '구매',
                'RETURN': '반품',
                'TRANSFER': '이동',
                'DAMAGE': '손상',
                'CANCEL': '취소',
                'CORRECTION': '수정',
            }
            
            recent_movements.append({
                'id': movement.id,
                'product_name': movement.product.name,
                'type': movement.movement_type,
                'type_display': type_display_map.get(movement.movement_type, movement.movement_type),
                'quantity_change': quantity_change,
                'current_stock': movement.current_stock,
                'created_at': movement.created_at.isoformat(),
            })
    else:
        # StockMovement 모델이 없는 경우 임시 데이터
        recent_movements = [
            {
                'id': 1,
                'product_name': '샘플 상품 1',
                'type': 'SALE',
                'type_display': '판매',
                'quantity_change': -3,
                'current_stock': 47,
                'created_at': timezone.now().isoformat(),
            }
        ]
    
    # ===========================================
    # 6. 차트 데이터 (최근 7일 재고 가치 추이)
    # ===========================================
    
    # 실제로는 일별 재고 가치 데이터를 계산해야 하지만, 
    # 여기서는 임시 데이터 사용
    chart_data = {
        '7days': {
            'labels': ['6/26', '6/27', '6/28', '6/29', '6/30', '7/01', '7/02'],
            'data': [
                int(total_value * decimal.Decimal('0.96')), int(total_value * decimal.Decimal('0.98')), 
                int(total_value * decimal.Decimal('1.01')), int(total_value * decimal.Decimal('0.99')), 
                int(total_value * decimal.Decimal('1.02')), int(total_value * decimal.Decimal('1.00')), 
                int(total_value * decimal.Decimal('1.00'))
            ]
        },
        '30days': {
            'labels': ['6/03', '6/08', '6/13', '6/18', '6/23', '6/28', '7/02'],
            'data': [
                int(total_value * decimal.Decimal('0.85')), int(total_value * decimal.Decimal('0.90')), 
                int(total_value * decimal.Decimal('0.93')), int(total_value * decimal.Decimal('0.96')), 
                int(total_value * decimal.Decimal('0.98')), int(total_value * decimal.Decimal('1.00')), 
                int(total_value * decimal.Decimal('1.00'))
            ]
        },
        '90days': {
            'labels': ['4/03', '4/18', '5/03', '5/18', '6/03', '6/18', '7/02'],
            'data': [
                int(total_value * decimal.Decimal('0.75')), int(total_value * decimal.Decimal('0.80')), 
                int(total_value * decimal.Decimal('0.82')), int(total_value * decimal.Decimal('0.86')), 
                int(total_value * decimal.Decimal('0.90')), int(total_value * decimal.Decimal('0.95')), 
                int(total_value * decimal.Decimal('1.00'))
            ]
        }
    }
    
    # ===========================================
    # 컨텍스트 데이터 구성
    # ===========================================
    
    context = {
        'metrics': {
            'total_products': total_products,
            'total_value': int(total_value),
            'low_stock_items': low_stock_count,
            'out_of_stock_items': out_of_stock_count,
            'products_growth': products_growth,
            'value_growth': value_growth,
        },
        'stock_distribution': {
            'normal': normal_stock,
            'warning': warning_stock,
            'critical': critical_stock,
            'normal_percent': normal_percent,
            'warning_percent': warning_percent,
            'critical_percent': critical_percent,
        },
        'low_stock_items': list(low_stock_items),
        'category_stats': category_stats,
        'recent_movements': recent_movements,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'inventory/overview.html', context)


@login_required
def stock_overview(request):
    """재고 현황 대시보드 (기존 뷰)"""
    # 기본 통계
    total_products = Product.objects.filter(status='ACTIVE').count()
    
    # 재고 상태별 카운트 (간단한 방식)
    low_stock_count = 0
    out_of_stock_count = 0
    overstock_count = 0
    total_inventory_value = 0
    
    for product in Product.objects.filter(status='ACTIVE'):
        # 재고 가치 누적
        total_inventory_value += (product.stock_quantity * product.cost_price)
        
        # 재고 상태 체크
        if product.stock_quantity == 0:
            out_of_stock_count += 1
        elif product.stock_quantity <= product.min_stock_level:
            low_stock_count += 1
        elif product.stock_quantity > product.max_stock_level:
            overstock_count += 1
    
    # 부족 재고 상품들 (상위 10개)
    low_stock_products = []
    out_of_stock_products = []
    overstock_products = []
    
    for product in Product.objects.filter(status='ACTIVE').select_related('category', 'brand'):
        if product.stock_quantity == 0:
            out_of_stock_products.append(product)
        elif product.stock_quantity <= product.min_stock_level:
            low_stock_products.append(product)
        elif product.stock_quantity > product.max_stock_level:
            overstock_products.append(product)
    
    # 카테고리별 통계 (간단한 방식)
    category_stats = []
    for category in Category.objects.filter(is_active=True):
        category_products = Product.objects.filter(category=category, status='ACTIVE')
        product_count = category_products.count()
        
        if product_count > 0:
            total_stock = sum(p.stock_quantity for p in category_products)
            inventory_value = sum(p.stock_quantity * p.cost_price for p in category_products)
            
            category_stats.append({
                'category': category,
                'product_count': product_count,
                'total_stock': total_stock,
                'inventory_value': inventory_value
            })
    
    # 가치 순으로 정렬
    category_stats = sorted(category_stats, key=lambda x: x['inventory_value'], reverse=True)[:10]
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'overstock_count': overstock_count,
        'total_inventory_value': total_inventory_value,
        'low_stock_products': low_stock_products[:10],
        'out_of_stock_products': out_of_stock_products[:10],
        'overstock_products': overstock_products[:10],
        'category_stats': category_stats,
    }
    
    return render(request, 'inventory/stock_overview.html', context)

@login_required
def stock_adjustment(request):
    """재고 조정 페이지"""
    if request.method == 'POST':
        return handle_stock_adjustment(request)
    
    products = Product.objects.filter(status='ACTIVE').select_related('category', 'brand')
    
    # 검색 기능
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(sku__icontains=search)
        )
    
    # 페이지네이션
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'inventory/stock_adjustment.html', {
        'products': page_obj,
        'search': search
    })

def handle_stock_adjustment(request):
    """재고 조정 처리"""
    try:
        with transaction.atomic():
            adjustments = []
            
            for key, value in request.POST.items():
                if key.startswith('adjustment_') and value:
                    product_id = key.split('_')[1]
                    try:
                        product = Product.objects.get(id=product_id)
                        new_quantity = int(value)
                        
                        if new_quantity != product.stock_quantity:
                            old_quantity = product.stock_quantity
                            product.stock_quantity = new_quantity
                            product.save()
                            
                            adjustments.append({
                                'product': product.name,
                                'old_quantity': old_quantity,
                                'new_quantity': new_quantity
                            })
                    
                    except (Product.DoesNotExist, ValueError):
                        continue
            
            if adjustments:
                messages.success(request, f'{len(adjustments)}개 상품의 재고가 조정되었습니다.')
            else:
                messages.info(request, '조정된 재고가 없습니다.')
    
    except Exception as e:
        messages.error(request, f'재고 조정 중 오류가 발생했습니다: {str(e)}')
    
    return redirect('inventory:stock_adjustment')


# ListView 클래스들
class StockListView(LoginRequiredMixin, ListView):
    """재고 목록 뷰"""
    model = Product
    template_name = 'inventory/stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(status='ACTIVE').select_related('category', 'brand')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(barcode__icontains=search)
            )
        
        # 카테고리 필터
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # 정렬
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        return context

# 추가적인 뷰들...
class LowStockListView(LoginRequiredMixin, ListView):
    """부족 재고 목록"""
    model = Product
    template_name = 'inventory/low_stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        low_stock_products = []
        for product in Product.objects.filter(status='ACTIVE').select_related('category', 'brand'):
            if product.stock_quantity <= product.min_stock_level:
                low_stock_products.append(product)
        
        return sorted(low_stock_products, key=lambda x: x.stock_quantity)

class OutOfStockListView(LoginRequiredMixin, ListView):
    """품절 상품 목록"""
    model = Product
    template_name = 'inventory/out_of_stock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(
            stock_quantity=0,
            status='ACTIVE'
        ).select_related('category', 'brand').order_by('name')

class OverstockListView(LoginRequiredMixin, ListView):
    """과재고 목록"""
    model = Product
    template_name = 'inventory/overstock_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        overstock_products = []
        for product in Product.objects.filter(status='ACTIVE').select_related('category', 'brand'):
            if product.stock_quantity > product.max_stock_level:
                overstock_products.append(product)
        
        return sorted(overstock_products, key=lambda x: x.stock_quantity, reverse=True)

@login_required
def export_stock_data(request):
    """재고 데이터 CSV 내보내기"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="stock_data.csv"'
    response.write('\ufeff')  # BOM for UTF-8
    
    writer = csv.writer(response)
    writer.writerow(['SKU', '상품명', '카테고리', '브랜드', '현재재고', '최소재고', '최대재고', '원가', '재고가치'])
    
    products = Product.objects.filter(status='ACTIVE').select_related('category', 'brand')
    for product in products:
        writer.writerow([
            product.sku,
            product.name,
            product.category.name if product.category else '',
            product.brand.name if product.brand else '',
            product.stock_quantity,
            product.min_stock_level,
            product.max_stock_level,
            product.cost_price,
            product.stock_quantity * product.cost_price
        ])
    
    return response