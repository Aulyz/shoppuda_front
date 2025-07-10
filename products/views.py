# products/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Avg, Max, Min
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
import json
import csv
import re
import logging
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Product, Category, Brand, ProductImage
from .forms import ProductForm, BrandForm, CategoryForm

logger = logging.getLogger(__name__)

@login_required
def product_list(request):
    """상품 목록 및 필터링"""
    products = Product.objects.select_related('brand', 'category').all().order_by('status')
    
    products = apply_product_filters(products, request)
    
    sort = request.GET.get('sort', '-created_at')
    valid_sorts = ['name', '-name', 'sku', '-sku', 'selling_price', '-selling_price', 
                   'stock_quantity', '-stock_quantity', 'created_at', '-created_at']
    if sort in valid_sorts:
        products = products.order_by(sort)
    
    # 페이지네이션
    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # 통계 및 컨텍스트 데이터
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        **get_product_stats(),
        **get_filter_data(),
        'current_filters': extract_current_filters(request)
    }
    
    return render(request, 'products/product_list.html', context)

@login_required
def product_create(request):
    """상품 등록"""
    if request.method == 'POST':
        return handle_product_create(request)
    
    context = {
        'categories': Category.objects.filter(is_active=True).order_by('sort_order', 'name'),
        'brands': Brand.objects.filter(is_active=True).order_by('name'),
    }
    return render(request, 'products/product_create.html', context)

@login_required
def product_detail(request, pk):
    """상품 상세 정보"""
    product = get_object_or_404(Product, pk=pk)
    
    context = {
        'product': product,
        'images': product.images.all().order_by('sort_order'),
        'recent_movements': get_recent_stock_movements(product),
        'related_products': get_related_products(product),
        'stock_status': check_stock_level(product),
        'profit_margin': calculate_profit_margin(product.cost_price, product.selling_price)
    }
    
    return render(request, 'products/product_detail.html', context)

@login_required
def product_edit(request, pk):
    """상품 수정"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        return handle_product_update(request, product)
    
    context = {
        'product': product,
        'categories': Category.objects.filter(is_active=True).order_by('sort_order', 'name'),
        'brands': Brand.objects.filter(is_active=True).order_by('name'),
    }
    
    return render(request, 'products/product_edit.html', context)

@login_required
@require_POST
def product_delete(request, pk):
    """상품 삭제"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        product_name = product.name
        product.delete()
        messages.success(request, f'상품 "{product_name}"이 삭제되었습니다.')
    except Exception as e:
        messages.error(request, f'상품 삭제 중 오류: {str(e)}')
    
    return redirect('products:list')

@login_required
def product_clone(request, pk):
    """상품 복제"""
    original_product = get_object_or_404(Product, pk=pk)
    
    try:
        cloned_product = clone_product(original_product, request.user)
        messages.success(request, f'상품이 복제되었습니다. 새 SKU: {cloned_product.sku}')
        return redirect('products:edit', pk=cloned_product.pk)
    except Exception as e:
        messages.error(request, f'상품 복제 중 오류: {str(e)}')
        return redirect('products:detail', pk=pk)

# ====================== 브랜드 CBV ======================
# 브랜드 관련 CBV (Class-Based Views) 구현
# ==================================================

class BrandListView(LoginRequiredMixin, ListView):
    """브랜드 목록 CBV"""
    model = Brand
    template_name = 'products/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Brand.objects.filter(is_active=True).order_by('name')
        search = self.request.GET.get('search', '').strip()
        status = self.request.GET.get('status', '')
        sort_by = self.request.GET.get('sort_by', 'name')
        
        # 검색 필터
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        # 상태 필터
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # 정렬
        if sort_by in ['name', '-name', 'code', '-code', 'created_at', '-created_at', 'updated_at', '-updated_at']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['status'] = self.request.GET.get('status', '')
        context['sort_by'] = self.request.GET.get('sort_by', 'name')
        
        # 통계 정보
        context['total_brands'] = Brand.objects.count()
        context['active_brands'] = Brand.objects.filter(is_active=True).count()
        context['brands_with_products'] = Brand.objects.filter(products__isnull=False).distinct().count()
        
        # 이번 달 신규 브랜드
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['new_this_month'] = Brand.objects.filter(created_at__gte=current_month).count()
        
        return context

class BrandCreateView(LoginRequiredMixin, CreateView):
    """브랜드 생성 CBV"""
    model = Brand
    form_class = BrandForm
    template_name = 'products/brand_create.html'
    success_url = reverse_lazy('products:brand_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'브랜드 "{form.instance.name}"이 생성되었습니다.')
        return super().form_valid(form)

class BrandUpdateView(LoginRequiredMixin, UpdateView):
    """브랜드 수정 CBV"""
    model = Brand
    form_class = BrandForm
    template_name = 'products/brand_edit.html'
    success_url = reverse_lazy('products:brand_list')
    
    def form_valid(self, form):
        # 로고 제거 처리
        if self.request.POST.get('remove_logo') == 'true':
            if self.object.logo:
                self.object.logo.delete(save=False)
                form.instance.logo = None
        
        messages.success(self.request, f'브랜드 "{form.instance.name}"이 수정되었습니다.')
        return super().form_valid(form)

class BrandDeleteView(LoginRequiredMixin, DeleteView):
    """브랜드 삭제 CBV"""
    model = Brand
    template_name = 'products/brand_delete.html'
    success_url = reverse_lazy('products:brand_list')
    
    def delete(self, request, *args, **kwargs):
        brand = self.get_object()
        if brand.products.exists():
            messages.error(request, '이 브랜드를 사용하는 상품이 있어 삭제할 수 없습니다.')
            return redirect('products:brand_list')
        
        brand_name = brand.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'브랜드 "{brand_name}"이 삭제되었습니다.')
        return response

class BrandDetailView(LoginRequiredMixin, DetailView):
    """브랜드 상세 CBV"""
    model = Brand
    template_name = 'products/brand_detail.html'
    context_object_name = 'brand'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.get_object()
        
        # 브랜드 관련 상품들
        products = brand.products.filter(status='ACTIVE').order_by('-created_at')[:10]
        context['recent_products'] = products
        context['total_products'] = brand.products.count()
        
        # 브랜드 통계
        context['stats'] = {
            'total_products': brand.products.count(),
            'active_products': brand.products.filter(status='ACTIVE').count(),
            'inactive_products': brand.products.filter(status='INACTIVE').count(),
            'discontinued_products': brand.products.filter(status='DISCONTINUED').count(),
        }
        
        return context

# ====================== 브랜드 AJAX 뷰 ======================

@login_required
@require_http_methods(["POST"])
def brand_bulk_action(request):
    """브랜드 일괄 작업 처리"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        brand_ids = data.get('brand_ids', [])
        
        if not action or not brand_ids:
            return JsonResponse({
                'success': False,
                'message': '작업 유형과 브랜드를 선택해주세요.'
            })
        
        brands = Brand.objects.filter(id__in=brand_ids)
        
        if action == 'activate':
            updated_count = brands.update(is_active=True)
            return JsonResponse({
                'success': True,
                'message': f'{updated_count}개의 브랜드가 활성화되었습니다.'
            })
        
        elif action == 'deactivate':
            updated_count = brands.update(is_active=False)
            return JsonResponse({
                'success': True,
                'message': f'{updated_count}개의 브랜드가 비활성화되었습니다.'
            })
        
        elif action == 'delete':
            brands_with_products = brands.filter(products__isnull=False).distinct()
            
            if brands_with_products.exists():
                brand_names = ', '.join(brands_with_products.values_list('name', flat=True))
                return JsonResponse({
                    'success': False,
                    'message': f'다음 브랜드들은 연결된 상품이 있어 삭제할 수 없습니다: {brand_names}'
                })
            
            deletable_brands = brands.filter(products__isnull=True)
            deleted_count, _ = deletable_brands.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{deleted_count}개의 브랜드가 삭제되었습니다.'
            })
        
        else:
            return JsonResponse({
                'success': False,
                'message': '알 수 없는 작업입니다.'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'오류가 발생했습니다: {str(e)}'
        })

@login_required
@require_http_methods(["GET"])
def check_brand_code(request):
    """브랜드 코드 중복 확인"""
    code = request.GET.get('code', '').strip().upper()
    brand_id = request.GET.get('brand_id')
    
    if not code:
        return JsonResponse({
            'available': False,
            'message': '브랜드 코드를 입력해주세요.'
        })
    
    if not re.match(r'^[A-Z0-9_]+$', code):
        return JsonResponse({
            'available': False,
            'message': '브랜드 코드는 영문 대문자, 숫자, 언더스코어만 사용할 수 있습니다.'
        })
    
    existing_brand = Brand.objects.filter(code__iexact=code)
    if brand_id:
        existing_brand = existing_brand.exclude(id=brand_id)
    
    if existing_brand.exists():
        return JsonResponse({
            'available': False,
            'message': '이미 사용 중인 브랜드 코드입니다.'
        })
    
    return JsonResponse({
        'available': True,
        'message': '사용 가능한 브랜드 코드입니다.'
    })

@login_required
@require_http_methods(["GET"])
def brand_stats(request):
    """브랜드 통계 정보"""
    try:
        total_brands = Brand.objects.count()
        active_brands = Brand.objects.filter(is_active=True).count()
        
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = Brand.objects.filter(created_at__gte=current_month).count()
        
        brands_with_products = Brand.objects.filter(products__isnull=False).distinct().count()
        
        return JsonResponse({
            'success': True,
            'data': {
                'total_brands': total_brands,
                'active_brands': active_brands,
                'new_this_month': new_this_month,
                'brands_with_products': brands_with_products,
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'통계 조회 중 오류가 발생했습니다: {str(e)}'
        })

# ================================
# 카테고리 웹페이지 뷰
# ================================

@login_required
def category_list(request):
    """카테고리 목록 페이지 (고급 버전)"""
    categories = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__status='ACTIVE'))
    ).select_related('parent').order_by('sort_order', 'name')
    
    # 템플릿에서 사용할 데이터 직렬화
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description or '',
            'icon': category.icon,
            'is_active': category.is_active,
            'product_count': category.get_product_count(),  # annotate된 값
            'created_at': category.created_at.isoformat(),
            'parent_id': category.parent.id if category.parent else None,
            'sort_order': category.sort_order
        })
    
    # 통계 데이터
    total_categories = categories.count()
    active_categories = categories.filter(is_active=True).count()
    inactive_categories = total_categories - active_categories
    
    context = {
        'categories': categories,
        'categories_json': json.dumps(categories_data, ensure_ascii=False),
        'total_categories': total_categories,
        'active_categories': active_categories,
        'inactive_categories': inactive_categories,
    }
    
    return render(request, 'products/category_list.html', context)


@login_required
def category_detail(request, pk):
    """카테고리 상세 페이지"""
    category = get_object_or_404(Category, pk=pk)
    
    # 하위 카테고리들
    children = category.get_children()
    
    # 카테고리의 상품들 (페이지네이션)
    products = category.get_products().select_related('brand')
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_products = products.count()
    active_products = products.filter(status='ACTIVE').count()
    children_count = children.count()
    
    # 브레드크럼
    breadcrumbs = []
    current = category
    while current:
        breadcrumbs.insert(0, current)
        current = current.parent
    
    return render(request, 'products/category_detail.html', {
        'category': category,
        'children': children,
        'products': page_obj,
        'total_products': total_products,
        'active_products': active_products,
        'children_count': children_count,
        'breadcrumbs': breadcrumbs
    })


@login_required
def category_create(request):
    """카테고리 생성 페이지"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'카테고리 "{category.name}"이 생성되었습니다.')
            return redirect('products:category_list')
        else:
            messages.error(request, '카테고리 생성 중 오류가 발생했습니다.')
    else:
        form = CategoryForm()
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'title': '새 카테고리 추가'
    })


@login_required
def category_edit(request, pk):
    """카테고리 수정 페이지"""
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'카테고리 "{category.name}"이 수정되었습니다.')
            return redirect('products:category_list')
        else:
            messages.error(request, '카테고리 수정 중 오류가 발생했습니다.')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'category': category,
        'title': f'카테고리 수정 - {category.name}'
    })


@login_required
def category_delete(request, pk):
    """카테고리 삭제 페이지"""
    category = get_object_or_404(Category, pk=pk)
    
    # 삭제 가능 여부 확인
    can_delete, reason = category.can_delete()
    
    if request.method == 'POST':
        if can_delete:
            category_name = category.name
            category.delete()
            messages.success(request, f'카테고리 "{category_name}"이 삭제되었습니다.')
            return redirect('products:category_list')
        else:
            messages.error(request, f'삭제할 수 없습니다: {reason}')
            return redirect('products:category_detail', pk=pk)
    
    return render(request, 'products/category_delete.html', {
        'category': category,
        'can_delete': can_delete,
        'reason': reason
    })


# ================================
# 카테고리 AJAX API 뷰
# ================================

@login_required
@require_http_methods(["POST"])
def category_ajax_create(request):
    """AJAX 카테고리 생성"""
    try:
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            
            return JsonResponse({
                'success': True,
                'message': '카테고리가 생성되었습니다.',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description or '',
                    'icon': category.icon,
                    'is_active': category.is_active,
                    'product_count': category.get_product_count(),
                    'created_at': category.created_at.isoformat(),
                    'parent_id': category.parent.id if category.parent else None,
                    'sort_order': category.sort_order
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': '입력값을 확인해주세요.',
                'errors': form.errors
            })
    
    except Exception as e:
        logger.error(f"Category creation error: {e}")
        return JsonResponse({
            'success': False,
            'message': '카테고리 생성 중 오류가 발생했습니다.'
        })


@login_required
@require_http_methods(["POST"])
def category_ajax_update(request, pk):
    """AJAX 카테고리 수정"""
    try:
        category = get_object_or_404(Category, pk=pk)
        form = CategoryForm(request.POST, instance=category)
        
        if form.is_valid():
            category = form.save()
            
            return JsonResponse({
                'success': True,
                'message': '카테고리가 수정되었습니다.',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description or '',
                    'icon': category.icon,
                    'is_active': category.is_active,
                    'product_count': category.get_product_count(),
                    'created_at': category.created_at.isoformat(),
                    'parent_id': category.parent.id if category.parent else None,
                    'sort_order': category.sort_order
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': '입력값을 확인해주세요.',
                'errors': form.errors
            })
    
    except Exception as e:
        logger.error(f"Category update error: {e}")
        return JsonResponse({
            'success': False,
            'message': '카테고리 수정 중 오류가 발생했습니다.'
        })


@login_required
@require_http_methods(["POST"])
def category_ajax_delete(request, pk):
    """AJAX 카테고리 삭제"""
    try:
        category = get_object_or_404(Category, pk=pk)
        
        # 삭제 가능 여부 확인
        can_delete, reason = category.can_delete()
        
        if can_delete:
            category_name = category.name
            category.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'카테고리 "{category_name}"이 삭제되었습니다.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'삭제할 수 없습니다: {reason}'
            })
    
    except Exception as e:
        logger.error(f"Category deletion error: {e}")
        return JsonResponse({
            'success': False,
            'message': '카테고리 삭제 중 오류가 발생했습니다.'
        })


@login_required
@require_http_methods(["POST"])
def category_bulk_action(request):
    """카테고리 일괄 작업"""
    try:
        data = json.loads(request.body)
        action = data.get('action')
        category_ids = data.get('category_ids', [])
        
        if not category_ids:
            return JsonResponse({
                'success': False,
                'message': '선택된 카테고리가 없습니다.'
            })
        
        categories = Category.objects.filter(id__in=category_ids)
        
        if action == 'activate':
            # 일괄 활성화
            updated = categories.update(is_active=True)
            return JsonResponse({
                'success': True,
                'message': f'{updated}개 카테고리가 활성화되었습니다.'
            })
        
        elif action == 'deactivate':
            # 일괄 비활성화
            updated = categories.update(is_active=False)
            return JsonResponse({
                'success': True,
                'message': f'{updated}개 카테고리가 비활성화되었습니다.'
            })
        
        elif action == 'delete':
            # 일괄 삭제
            success_count = 0
            error_messages = []
            
            with transaction.atomic():
                for category in categories:
                    can_delete, reason = category.can_delete()
                    if can_delete:
                        category.delete()
                        success_count += 1
                    else:
                        error_messages.append(f'{category.name}: {reason}')
            
            if success_count > 0 and not error_messages:
                return JsonResponse({
                    'success': True,
                    'message': f'{success_count}개 카테고리가 삭제되었습니다.'
                })
            elif success_count > 0 and error_messages:
                return JsonResponse({
                    'success': True,
                    'message': f'{success_count}개 카테고리가 삭제되었습니다.',
                    'warnings': error_messages
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '삭제할 수 있는 카테고리가 없습니다.',
                    'errors': error_messages
                })
        
        else:
            return JsonResponse({
                'success': False,
                'message': '알 수 없는 작업입니다.'
            })
    
    except Exception as e:
        logger.error(f"Bulk action error: {e}")
        return JsonResponse({
            'success': False,
            'message': '일괄 작업 중 오류가 발생했습니다.'
        })

@login_required
@require_http_methods(["GET"])
def category_delete_check(request, pk):
    """카테고리 삭제 가능 여부 확인"""
    category = get_object_or_404(Category, pk=pk)
    can_delete, reason = category.can_delete()
    return JsonResponse({
        'success': can_delete,
        'message': reason
    })

# ====================== 재고 관리 ======================

@login_required
def product_stock_detail(request, pk):
    """상품 재고 상세"""
    product = get_object_or_404(Product, pk=pk)
    movements = get_recent_stock_movements(product, limit=50)
    
    return render(request, 'products/product_stock_detail.html', {
        'product': product,
        'movements': movements
    })

@login_required
@require_POST
def adjust_product_stock(request, pk):
    """상품 재고 조정"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            adjustment_type = data.get('type', 'set')
            quantity = int(data.get('quantity', 0))
            reason = data.get('reason', '관리자 조정')
        else:
            adjustment_type = request.POST.get('type', 'set')
            quantity = int(request.POST.get('quantity', 0))
            reason = request.POST.get('reason', '관리자 조정')

        old_quantity = product.stock_quantity
        new_quantity = calculate_new_stock(old_quantity, quantity, adjustment_type)
        
        product.stock_quantity = new_quantity
        product.save()
        
        # 재고 이동 기록 생성
        create_stock_movement(product, old_quantity, new_quantity, reason, request.user)
        
        return JsonResponse({
            'success': True,
            'message': f'재고가 {old_quantity}개에서 {new_quantity}개로 조정되었습니다.',
            'old_quantity': old_quantity,
            'new_quantity': new_quantity
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== 가격 관리 ======================

@login_required
@require_POST
def update_product_price(request, pk):
    """상품 가격 업데이트"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        new_cost_price = float(request.POST.get('cost_price', 0))
        new_selling_price = float(request.POST.get('selling_price', 0))
        new_discount_price = request.POST.get('discount_price')
        new_discount_price = float(new_discount_price) if new_discount_price else None
        
        # 가격 유효성 검사
        price_errors = validate_prices(new_cost_price, new_selling_price, new_discount_price)
        if price_errors:
            return JsonResponse({'success': False, 'error': price_errors[0]})
        
        # 가격 업데이트
        product.cost_price = new_cost_price
        product.selling_price = new_selling_price
        product.discount_price = new_discount_price
        product.save()
        
        return JsonResponse({'success': True, 'message': '가격이 성공적으로 업데이트되었습니다.'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def bulk_price_update(request):
    """일괄 가격 업데이트"""
    product_ids = request.POST.getlist('product_ids')
    
    if not product_ids:
        return JsonResponse({'success': False, 'error': '선택된 상품이 없습니다.'})
    
    try:
        update_type = request.POST.get('update_type')
        value = float(request.POST.get('value', 0))
        
        updated_count = update_prices_bulk(product_ids, update_type, value)
        
        return JsonResponse({
            'success': True,
            'message': f'{updated_count}개 상품의 가격이 업데이트되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== 일괄 작업 ======================

@login_required
@require_POST
def product_bulk_update(request):
    """상품 일괄 수정"""
    product_ids = request.POST.getlist('product_ids')
    
    if not product_ids:
        return JsonResponse({'success': False, 'error': '선택된 상품이 없습니다.'})
    
    try:
        update_data = build_bulk_update_data(request.POST)
        
        if not update_data:
            return JsonResponse({'success': False, 'error': '수정할 항목이 없습니다.'})
        
        count = Product.objects.filter(id__in=product_ids).update(**update_data)
        
        return JsonResponse({
            'success': True,
            'message': f'{count}개 상품이 수정되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def product_bulk_delete(request):
    """상품 일괄 삭제"""
    product_ids = request.POST.getlist('product_ids')
    
    if not product_ids:
        return JsonResponse({'success': False, 'error': '선택된 상품이 없습니다.'})
    
    try:
        count = Product.objects.filter(id__in=product_ids).count()
        Product.objects.filter(id__in=product_ids).delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{count}개 상품이 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== 이미지 관리 ======================

@login_required
def product_images(request, pk):
    """상품 이미지 관리"""
    product = get_object_or_404(Product, pk=pk)
    images = product.images.all().order_by('sort_order')
    
    return render(request, 'products/product_images.html', {
        'product': product,
        'images': images
    })

@login_required
@require_POST
def upload_product_image(request, pk):
    """상품 이미지 업로드"""
    product = get_object_or_404(Product, pk=pk)
    
    if 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': '이미지 파일이 없습니다.'})
    
    try:
        image = create_product_image(product, request.FILES['image'], request.POST.get('alt_text', ''))
        
        return JsonResponse({
            'success': True,
            'image': {
                'id': image.id,
                'url': image.image.url,
                'alt_text': image.alt_text,
                'is_primary': image.is_primary,
                'sort_order': image.sort_order
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def delete_product_image(request, image_id):
    """상품 이미지 삭제"""
    image = get_object_or_404(ProductImage, id=image_id)
    
    try:
        handle_image_deletion(image)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def set_primary_image(request, image_id):
    """대표 이미지 설정"""
    image = get_object_or_404(ProductImage, id=image_id)
    
    try:
        set_image_as_primary(image)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== API 엔드포인트 ======================

@login_required
def check_sku(request):
    """SKU 중복 검사"""
    sku = request.GET.get('sku', '').strip()
    product_id = request.GET.get('product_id')
    
    if not sku:
        return JsonResponse({'exists': False})
    
    query = Product.objects.filter(sku=sku)
    if product_id:
        query = query.exclude(pk=product_id)
    
    return JsonResponse({'exists': query.exists()})

@login_required
def product_autocomplete(request):
    """상품 자동완성"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        status='ACTIVE'
    ).select_related('brand')[:10]
    
    results = [{
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'brand': product.brand.name if product.brand else '',
        'price': float(product.selling_price),
        'stock': product.stock_quantity
    } for product in products]
    
    return JsonResponse({'results': results})

@login_required
def get_categories_api(request):
    """카테고리 목록 API"""
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    data = [{
        'id': cat.id,
        'name': cat.name,
        'full_path': cat.full_path,
        'parent_id': cat.parent.id if cat.parent else None
    } for cat in categories]
    
    return JsonResponse({'categories': data})

@login_required
def get_brands_api(request):
    """브랜드 목록 API"""
    brands = Brand.objects.filter(is_active=True).order_by('name')
    
    data = [{
        'id': brand.id,
        'name': brand.name,
        'code': brand.code
    } for brand in brands]
    
    return JsonResponse({'brands': data})

# ====================== 데이터 내보내기/가져오기 ======================

@login_required
def export_products_csv(request):
    """상품 CSV 내보내기"""
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="products_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # UTF-8 BOM
        
        writer = csv.writer(response)
        write_products_to_csv(writer, get_filtered_products(request))
        
        return response
        
    except Exception as e:
        messages.error(request, f'CSV 내보내기 중 오류: {str(e)}')
        return redirect('products:list')

@login_required
def import_products(request):
    """상품 가져오기"""
    if request.method == 'POST':
        return handle_product_import(request)
    
    return render(request, 'products/import_products.html')

@login_required
def download_import_template(request):
    """상품 가져오기 템플릿 다운로드"""
    try:
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="product_import_template.csv"'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        write_import_template(writer)
        
        return response
        
    except Exception as e:
        messages.error(request, f'템플릿 다운로드 중 오류: {str(e)}')
        return redirect('products:list')

# ====================== 통계 및 보고서 ======================

@login_required
def product_stats(request):
    """상품 통계"""
    context = {
        **get_product_stats(),
        **get_detailed_stats(),
        'category_stats': get_category_stats(),
        'brand_stats': get_brand_stats(),
    }
    
    return render(request, 'products/product_stats.html', context)

@login_required
def low_stock_report(request):
    """부족 재고 보고서"""
    products = Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).select_related('category', 'brand').order_by('stock_quantity')
    
    return render(request, 'products/stock_report.html', {
        'products': products,
        'title': '부족 재고 보고서'
    })

# ====================== 상품 상태 변경 ======================

@login_required
@require_POST
def activate_product(request, pk):
    """상품 활성화"""
    return change_product_status(request, pk, 'ACTIVE', '활성화')

@login_required
@require_POST
def deactivate_product(request, pk):
    """상품 비활성화"""
    return change_product_status(request, pk, 'INACTIVE', '비활성화')

@login_required
@require_POST
def feature_product(request, pk):
    """상품 추천 설정"""
    return change_product_feature(request, pk, True, '추천 상품으로 설정')

@login_required
@require_POST
def unfeature_product(request, pk):
    """상품 추천 해제"""
    return change_product_feature(request, pk, False, '추천 해제')

# ====================== 유틸리티 함수 ======================

def apply_product_filters(products, request):
    """상품 목록에 필터 적용"""
    search = request.GET.get('search', '').strip()
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__icontains=search)
        )
    
    category = request.GET.get('category')
    if category:
        products = products.filter(category_id=category)
    
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand_id=brand)
    
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        products = products.filter(stock_quantity__lte=F('min_stock_level'))
    elif stock_status == 'out':
        products = products.filter(stock_quantity=0)
    elif stock_status == 'normal':
        products = products.filter(
            stock_quantity__gt=F('min_stock_level'),
            stock_quantity__lte=F('max_stock_level')
        )
    
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(selling_price__gte=min_price)
    if max_price:
        products = products.filter(selling_price__lte=max_price)
    
    return products

def get_product_stats():
    """기본 상품 통계"""
    return {
        'total_products': Product.objects.filter().count(),
        'low_stock_count': Product.objects.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('min_stock_level')
        ).count(),
        'out_of_stock_count': Product.objects.filter(
            stock_quantity=0
        ).count(),
        'total_value': Product.objects.filter().aggregate(
            total=Sum(F('stock_quantity') * F('selling_price'))
        )['total'] or 0
    }

def get_filter_data():
    """필터용 데이터"""
    return {
        'categories': Category.objects.filter(is_active=True).order_by('name'),
        'brands': Brand.objects.filter(is_active=True).order_by('name')
    }

def extract_current_filters(request):
    """현재 적용된 필터 추출"""
    return {
        'search': request.GET.get('search', ''),
        'category': request.GET.get('category'),
        'brand': request.GET.get('brand'),
        'stock_status': request.GET.get('stock_status'),
        'sort': request.GET.get('sort', '-created_at'),
        'min_price': request.GET.get('min_price'),
        'max_price': request.GET.get('max_price'),
    }

def handle_product_create(request):
    """상품 생성 처리"""
    try:
        with transaction.atomic():
            product_data = extract_product_data(request.POST, request.user)
            
            # 유효성 검사
            errors = validate_product_data(product_data)
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]})
            
            # 상품 생성
            product = Product.objects.create(**product_data)
            
            # 이미지 처리
            process_product_images(product, request.FILES)
            
            return JsonResponse({
                'success': True,
                'message': '상품이 성공적으로 등록되었습니다.',
                'product_id': str(product.id),
                'redirect_url': reverse('products:detail', kwargs={'pk': product.pk})
            })
            
    except Exception as e:
        logger.error(f'상품 등록 오류: {str(e)}', exc_info=True)
        return JsonResponse({'success': False, 'error': f'상품 등록 중 오류: {str(e)}'})

def handle_product_update(request, product):
    """상품 수정 처리"""
    try:
        with transaction.atomic():
            update_product_fields(product, request.POST)
            product.save()
            
            # AJAX 요청이면 JSON 리턴
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': '상품이 성공적으로 수정되었습니다.',
                    'redirect_url': reverse('products:detail', kwargs={'pk': product.pk})
                })
            
            # 일반 요청이면 기존 로직
            messages.success(request, '상품이 성공적으로 수정되었습니다.')
            return redirect('products:detail', pk=product.pk)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        
        messages.error(request, f'상품 수정 중 오류: {str(e)}')
        return redirect('products:edit', pk=product.pk)

def clone_product(original_product, user):
    """상품 복제"""
    with transaction.atomic():
        # 새로운 SKU 생성
        new_sku = generate_unique_sku(original_product.sku)
        
        # 상품 복제
        cloned_product = Product.objects.create(
            sku=new_sku,
            name=f"{original_product.name} (복사본)",
            category=original_product.category,
            brand=original_product.brand,
            short_description=original_product.short_description,
            description=original_product.description,
            cost_price=original_product.cost_price,
            selling_price=original_product.selling_price,
            discount_price=original_product.discount_price,
            stock_quantity=0,
            min_stock_level=original_product.min_stock_level,
            max_stock_level=original_product.max_stock_level,
            weight=original_product.weight,
            dimensions_length=original_product.dimensions_length,
            dimensions_width=original_product.dimensions_width,
            dimensions_height=original_product.dimensions_height,
            tags=original_product.tags,
            status='INACTIVE',
            is_featured=False,
            created_by=user
        )
        
        # 이미지 복제
        clone_product_images(original_product, cloned_product)
        
        return cloned_product

def validate_product_data(data):
    """상품 데이터 유효성 검사"""
    errors = []
    
    # 필수 필드 검사
    if not data.get('name'):
        errors.append('상품명은 필수입니다.')
    
    if not data.get('sku'):
        errors.append('SKU는 필수입니다.')
    elif Product.objects.filter(sku=data['sku']).exists():
        errors.append('이미 사용 중인 SKU입니다.')
    
    # 가격 검증
    try:
        cost_price = float(data.get('cost_price', 0))
        selling_price = float(data.get('selling_price', 0))
        
        if cost_price < 0:
            errors.append('원가는 0 이상이어야 합니다.')
        
        if selling_price <= 0:
            errors.append('판매가는 0보다 커야 합니다.')
        
        if selling_price <= cost_price:
            errors.append('판매가는 원가보다 높아야 합니다.')
        
        discount_price = data.get('discount_price')
        if discount_price and float(discount_price) >= selling_price:
            errors.append('할인가는 판매가보다 낮아야 합니다.')
            
    except (ValueError, TypeError):
        errors.append('올바른 가격을 입력해주세요.')
    
    # 재고 검증
    try:
        stock_quantity = int(data.get('stock_quantity', 0))
        min_stock = int(data.get('min_stock_level', 0))
        max_stock = int(data.get('max_stock_level', 1000))
        
        if stock_quantity < 0:
            errors.append('재고 수량은 0 이상이어야 합니다.')
        
        if min_stock < 0:
            errors.append('최소 재고는 0 이상이어야 합니다.')
        
        if max_stock <= min_stock:
            errors.append('최대 재고는 최소 재고보다 커야 합니다.')
            
    except (ValueError, TypeError):
        errors.append('올바른 재고 수량을 입력해주세요.')
    
    return errors

def validate_prices(cost_price, selling_price, discount_price):
    """가격 유효성 검사"""
    errors = []
    
    if cost_price < 0:
        errors.append('원가는 0 이상이어야 합니다.')
    
    if selling_price <= 0:
        errors.append('판매가는 0보다 커야 합니다.')
    
    if selling_price <= cost_price:
        errors.append('판매가는 원가보다 높아야 합니다.')
    
    if discount_price and discount_price >= selling_price:
        errors.append('할인가는 판매가보다 낮아야 합니다.')
    
    return errors

def extract_product_data(post_data, user):
    """POST 데이터에서 상품 정보 추출"""
    return {
        'sku': post_data.get('sku'),
        'name': post_data.get('name'),
        'category_id': post_data.get('category') if post_data.get('category') else None,
        'brand_id': post_data.get('brand') if post_data.get('brand') else None,
        'short_description': post_data.get('short_description', ''),
        'description': post_data.get('description', ''),
        'status': post_data.get('status', 'ACTIVE'),
        'is_featured': bool(post_data.get('is_featured')),
        'cost_price': float(post_data.get('cost_price', 0)),
        'selling_price': float(post_data.get('selling_price', 0)),
        'discount_price': float(post_data.get('discount_price', 0)) if post_data.get('discount_price') else None,
        'stock_quantity': int(post_data.get('stock_quantity', 0)),
        'min_stock_level': int(post_data.get('min_stock_level', 0)),
        'max_stock_level': int(post_data.get('max_stock_level', 1000)),
        'weight': float(post_data.get('weight', 0)) if post_data.get('weight') else None,
        'dimensions_length': float(post_data.get('dimensions_length', 0)) if post_data.get('dimensions_length') else None,
        'dimensions_width': float(post_data.get('dimensions_width', 0)) if post_data.get('dimensions_width') else None,
        'dimensions_height': float(post_data.get('dimensions_height', 0)) if post_data.get('dimensions_height') else None,
        'barcode': post_data.get('barcode', ''),
        'tags': post_data.get('tags', ''),
        'created_by': user
    }

def update_product_fields(product, post_data):
    """상품 필드 업데이트"""
    update_fields = [
        'sku', 'name', 'short_description', 'description', 'status', 'is_featured',
        'cost_price', 'selling_price', 'discount_price', 'stock_quantity',
        'min_stock_level', 'max_stock_level', 'weight', 'dimensions_length',
        'dimensions_width', 'dimensions_height', 'barcode', 'tags'
    ]
    
    for field in update_fields:
        value = post_data.get(field)
        if value is not None:
            if field in ['cost_price', 'selling_price', 'discount_price', 'weight', 
                       'dimensions_length', 'dimensions_width', 'dimensions_height']:
                value = float(value) if value else (None if field == 'discount_price' else 0)
            elif field in ['stock_quantity', 'min_stock_level', 'max_stock_level']:
                value = int(value) if value else 0
            elif field == 'is_featured':
                value = bool(value)
            
            setattr(product, field, value)
    
    # 카테고리와 브랜드
    category_id = post_data.get('category')
    product.category_id = category_id if category_id else None
    
    brand_id = post_data.get('brand')
    product.brand_id = brand_id if brand_id else None

def process_product_images(product, files):
    """상품 이미지 처리"""
    if 'images' in files:
        images = files.getlist('images')
        for index, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                alt_text=f'{product.name} 이미지 {index + 1}',
                is_primary=(index == 0),
                sort_order=index
            )

def generate_unique_sku(base_sku):
    """고유한 SKU 생성"""
    counter = 1
    new_sku = f"{base_sku}-COPY{counter}"
    
    while Product.objects.filter(sku=new_sku).exists():
        counter += 1
        new_sku = f"{base_sku}-COPY{counter}"
    
    return new_sku

def clone_product_images(original_product, cloned_product):
    """상품 이미지 복제"""
    for image in original_product.images.all():
        ProductImage.objects.create(
            product=cloned_product,
            image=image.image,
            alt_text=image.alt_text,
            is_primary=image.is_primary,
            sort_order=image.sort_order
        )

def get_recent_stock_movements(product, limit=10):
    """최근 재고 이동 이력 조회"""
    try:
        from inventory.models import StockMovement
        return StockMovement.objects.filter(product=product).order_by('-created_at')[:limit]
    except ImportError:
        return []

def calculate_new_stock(old_quantity, quantity, adjustment_type):
    """새 재고 수량 계산"""
    if adjustment_type == 'set':
        return quantity
    elif adjustment_type == 'add':
        return old_quantity + quantity
    elif adjustment_type == 'subtract':
        return max(0, old_quantity - quantity)
    else:
        raise ValueError('잘못된 조정 타입입니다.')

def create_stock_movement(product, old_quantity, new_quantity, reason, user):
    """재고 이동 기록 생성"""
    try:
        from inventory.models import StockMovement
        StockMovement.objects.create(
            product=product,
            movement_type='ADJUST',
            quantity=abs(new_quantity - old_quantity),
            previous_stock=old_quantity,
            current_stock=new_quantity,
            reason=reason,
            created_by=user
        )
    except ImportError:
        pass

def update_prices_bulk(product_ids, update_type, value):
    """일괄 가격 업데이트"""
    products = Product.objects.filter(id__in=product_ids)
    updated_count = 0
    
    for product in products:
        if update_type == 'percentage':
            # 퍼센트 인상/인하
            product.selling_price = product.selling_price * (1 + value / 100)
            if product.discount_price:
                product.discount_price = product.discount_price * (1 + value / 100)
        elif update_type == 'fixed_amount':
            # 고정 금액 인상/인하
            product.selling_price = max(0, product.selling_price + value)
            if product.discount_price:
                product.discount_price = max(0, product.discount_price + value)
        
        product.save()
        updated_count += 1
    
    return updated_count

def build_bulk_update_data(post_data):
    """일괄 업데이트 데이터 구성"""
    update_data = {}
    
    if post_data.get('category'):
        update_data['category_id'] = post_data.get('category')
    if post_data.get('brand'):
        update_data['brand_id'] = post_data.get('brand')
    if post_data.get('status'):
        update_data['status'] = post_data.get('status')
    if 'is_featured' in post_data:
        update_data['is_featured'] = bool(post_data.get('is_featured'))
    
    return update_data

def create_product_image(product, image_file, alt_text):
    """상품 이미지 생성"""
    # 정렬 순서 계산
    max_order = product.images.aggregate(Max('sort_order'))['sort_order__max'] or 0
    sort_order = max_order + 1
    
    # 첫 번째 이미지인지 확인
    is_primary = not product.images.exists()
    
    return ProductImage.objects.create(
        product=product,
        image=image_file,
        alt_text=alt_text,
        is_primary=is_primary,
        sort_order=sort_order
    )

def handle_image_deletion(image):
    """이미지 삭제 처리"""
    # 대표 이미지인 경우 다른 이미지를 대표로 설정
    if image.is_primary and image.product.images.count() > 1:
        next_image = image.product.images.exclude(id=image.id).first()
        if next_image:
            next_image.is_primary = True
            next_image.save()
    
    image.delete()

def set_image_as_primary(image):
    """이미지를 대표 이미지로 설정"""
    # 기존 대표 이미지 해제
    image.product.images.update(is_primary=False)
    
    # 새 대표 이미지 설정
    image.is_primary = True
    image.save()

def change_product_status(request, pk, status, status_name):
    """상품 상태 변경"""
    product = get_object_or_404(Product, pk=pk)
    product.status = status
    product.save()
    
    messages.success(request, f'상품 "{product.name}"이 {status_name}되었습니다.')
    return redirect('products:detail', pk=pk)

def change_product_feature(request, pk, is_featured, action_name):
    """상품 추천 상태 변경"""
    product = get_object_or_404(Product, pk=pk)
    product.is_featured = is_featured
    product.save()
    
    messages.success(request, f'상품 "{product.name}"이 {action_name}되었습니다.')
    return redirect('products:detail', pk=pk)

def get_filtered_products(request):
    """필터가 적용된 상품 쿼리셋 반환"""
    products = Product.objects.select_related('brand', 'category').filter(status='ACTIVE')
    return apply_product_filters(products, request)

def write_products_to_csv(writer, products):
    """상품 데이터를 CSV로 작성"""
    # 헤더
    headers = [
        'SKU', '상품명', '카테고리', '브랜드', '간단설명', '상세설명',
        '상태', '추천상품', '원가', '판매가', '할인가', '재고수량',
        '최소재고', '최대재고', '무게', '길이', '너비', '높이',
        '바코드', '태그', '등록일'
    ]
    writer.writerow(headers)
    
    # 데이터
    for product in products:
        row = [
            product.sku,
            product.name,
            product.category.name if product.category else '',
            product.brand.name if product.brand else '',
            product.short_description,
            product.description,
            product.get_status_display(),
            '예' if product.is_featured else '아니오',
            product.cost_price,
            product.selling_price,
            product.discount_price or '',
            product.stock_quantity,
            product.min_stock_level,
            product.max_stock_level,
            product.weight or '',
            product.dimensions_length or '',
            product.dimensions_width or '',
            product.dimensions_height or '',
            product.barcode,
            product.tags,
            product.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ]
        writer.writerow(row)

def write_import_template(writer):
    """가져오기 템플릿 작성"""
    # 헤더와 샘플 데이터
    headers = [
        'SKU', '상품명', '카테고리코드', '브랜드코드', '간단설명', '상세설명',
        '상태', '추천상품', '원가', '판매가', '할인가', '재고수량',
        '최소재고', '최대재고', '무게', '길이', '너비', '높이',
        '바코드', '태그'
    ]
    writer.writerow(headers)
    
    # 샘플 데이터
    sample_data = [
        'PROD-001', '샘플 상품', 'CAT01', 'BRAND01', '간단한 설명',
        '상세한 설명', 'ACTIVE', '아니오', '10000', '15000', '13000',
        '100', '10', '1000', '500', '10', '15', '5',
        '1234567890123', '태그1, 태그2'
    ]
    writer.writerow(sample_data)

def handle_product_import(request):
    """상품 가져오기 처리"""
    if 'file' not in request.FILES:
        messages.error(request, '파일을 선택해주세요.')
        return redirect('products:import')
    
    try:
        file = request.FILES['file']
        
        # 파일 확장자 확인 및 데이터 읽기
        if file.name.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(file)
        elif file.name.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file)
        else:
            messages.error(request, '지원하지 않는 파일 형식입니다. (CSV, Excel만 지원)')
            return redirect('products:import')
        
        # 데이터 검증
        required_columns = ['SKU', '상품명', '원가', '판매가']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            messages.error(request, f'필수 컬럼이 없습니다: {", ".join(missing_columns)}')
            return redirect('products:import')
        
        # 세션에 데이터 저장 (미리보기용)
        request.session['import_data'] = df.to_dict('records')
        
        return redirect('products:import_preview')
        
    except Exception as e:
        messages.error(request, f'파일 처리 중 오류: {str(e)}')
        return redirect('products:import')

def get_detailed_stats():
    """상세 통계 데이터"""
    price_stats = Product.objects.filter(status='ACTIVE').aggregate(
        avg_price=Avg('selling_price'),
        min_price=Min('selling_price'),
        max_price=Max('selling_price')
    )
    
    return {
        'price_stats': price_stats,
        'featured_count': Product.objects.filter(is_featured=True, status='ACTIVE').count(),
    }

def get_category_stats():
    """카테고리별 통계"""
    return Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__status='ACTIVE'))
    ).order_by('-product_count')[:10]

def get_brand_stats():
    """브랜드별 통계"""
    return Brand.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__status='ACTIVE'))
    ).order_by('-product_count')[:10]

def get_related_products(product, limit=5):
    """관련 상품 조회"""
    related_products = Product.objects.filter(status='ACTIVE').exclude(id=product.id)
    
    # 같은 카테고리 상품 우선
    if product.category:
        same_category = related_products.filter(category=product.category)[:limit]
        if same_category.count() >= limit:
            return same_category
        
        # 부족하면 같은 브랜드 상품 추가
        if product.brand:
            same_brand = related_products.filter(brand=product.brand).exclude(
                id__in=[p.id for p in same_category]
            )[:limit - same_category.count()]
            return list(same_category) + list(same_brand)
    
    # 같은 브랜드 상품
    if product.brand:
        same_brand = related_products.filter(brand=product.brand)[:limit]
        if same_brand.count() >= limit:
            return same_brand
    
    # 랜덤 상품
    return related_products.order_by('?')[:limit]

def check_stock_level(product):
    """재고 수준 체크"""
    if product.stock_quantity == 0:
        return 'out_of_stock'
    elif product.stock_quantity <= product.min_stock_level:
        return 'low_stock'
    elif product.stock_quantity > product.max_stock_level:
        return 'overstock'
    else:
        return 'normal'

def calculate_profit_margin(cost_price, selling_price):
    """수익률 계산"""
    if not cost_price or not selling_price or selling_price <= 0:
        return 0
    
    return round(((selling_price - cost_price) / selling_price) * 100, 2)

def generate_sku():
    """자동 SKU 생성"""
    prefix = 'PROD'
    timestamp = timezone.now().strftime('%y%m%d')
    
    # 오늘 생성된 상품 수 계산
    today = timezone.now().date()
    count = Product.objects.filter(created_at__date=today).count() + 1
    
    return f'{prefix}-{timestamp}-{count:03d}'

def calculate_inventory_value():
    """전체 재고 가치 계산"""
    total_value = Product.objects.filter(status='ACTIVE').aggregate(
        total_cost=Sum(F('stock_quantity') * F('cost_price')),
        total_selling=Sum(F('stock_quantity') * F('selling_price'))
    )
    
    return {
        'cost_value': total_value['total_cost'] or 0,
        'selling_value': total_value['total_selling'] or 0,
        'potential_profit': (total_value['total_selling'] or 0) - (total_value['total_cost'] or 0)
    }

# ====================== 누락된 AJAX API 함수들 ======================

@login_required
def product_quick_info(request, pk):
    """상품 빠른 정보 조회 (AJAX)"""
    product = get_object_or_404(Product, pk=pk)
    
    data = {
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'brand': product.brand.name if product.brand else '',
        'category': product.category.name if product.category else '',
        'selling_price': float(product.selling_price),
        'discount_price': float(product.discount_price) if product.discount_price else None,
        'stock_quantity': product.stock_quantity,
        'status': product.status,
        'is_featured': product.is_featured,
        'stock_status': check_stock_level(product),
        'profit_margin': calculate_profit_margin(product.cost_price, product.selling_price),
        'image_url': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else None
    }
    
    return JsonResponse(data)

@login_required
def dashboard_stats(request):
    """대시보드용 상품 통계 API"""
    stats = {
        'total_products': Product.objects.filter(status='ACTIVE').count(),
        'low_stock_products': Product.objects.filter(
            stock_quantity__lte=F('min_stock_level'),
            status='ACTIVE'
        ).count(),
        'out_of_stock_products': Product.objects.filter(
            stock_quantity=0,
            status='ACTIVE'
        ).count(),
        'featured_products': Product.objects.filter(
            is_featured=True,
            status='ACTIVE'
        ).count(),
        'total_inventory_value': Product.objects.filter(status='ACTIVE').aggregate(
            total=Sum(F('stock_quantity') * F('selling_price'))
        )['total'] or 0,
        'recent_products': [{
            'id': str(p.id),
            'name': p.name,
            'sku': p.sku,
            'created_at': p.created_at.isoformat(),
            'stock_quantity': p.stock_quantity
        } for p in Product.objects.filter(status='ACTIVE').order_by('-created_at')[:5]]
    }
    
    return JsonResponse(stats)

# ====================== 재고 이력 함수 ======================

@login_required
def product_stock_history(request, pk):
    """상품 재고 이력"""
    product = get_object_or_404(Product, pk=pk)
    
    # 페이지네이션
    movements = get_recent_stock_movements(product, limit=None)
    paginator = Paginator(movements, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'products/product_stock_history.html', {
        'product': product,
        'movements': page_obj,
        'page_obj': page_obj
    })

@login_required
def product_price_history(request, pk):
    """상품 가격 이력"""
    product = get_object_or_404(Product, pk=pk)
    
    try:
        from orders.models import OrderItem
        price_history = OrderItem.objects.filter(
            product=product
        ).values('created_at', 'unit_price').order_by('-created_at')[:50]
    except ImportError:
        price_history = []
    
    return render(request, 'products/product_price_history.html', {
        'product': product,
        'price_history': price_history
    })

# ====================== 태그 관리 함수 ======================

@login_required
def tag_list(request):
    """태그 목록"""
    # 모든 상품의 태그를 수집하고 빈도순으로 정렬
    all_tags = []
    for product in Product.objects.filter(status='ACTIVE').exclude(tags=''):
        tags = [tag.strip() for tag in product.tags.split(',') if tag.strip()]
        all_tags.extend(tags)
    
    from collections import Counter
    tag_counts = Counter(all_tags)
    
    # 검색 필터
    search = request.GET.get('search', '').strip()
    if search:
        tag_counts = {tag: count for tag, count in tag_counts.items() 
                     if search.lower() in tag.lower()}
    
    # 정렬 (사용 빈도순)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    return render(request, 'products/tag_list.html', {
        'tags': sorted_tags,
        'search': search,
        'total_tags': len(sorted_tags)
    })

@login_required
def tag_autocomplete(request):
    """태그 자동완성 API"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # 기존 태그들에서 검색
    all_tags = set()
    for product in Product.objects.filter(status='ACTIVE').exclude(tags=''):
        tags = [tag.strip() for tag in product.tags.split(',') if tag.strip()]
        all_tags.update(tags)
    
    # 쿼리와 매치되는 태그 찾기
    matching_tags = [tag for tag in all_tags if query.lower() in tag.lower()]
    matching_tags.sort(key=lambda x: x.lower().startswith(query.lower()), reverse=True)
    
    results = [{'id': tag, 'text': tag} for tag in matching_tags[:10]]
    
    return JsonResponse({'results': results})

# ====================== 보고서 함수들 ======================

@login_required
def bestsellers_report(request):
    """베스트셀러 보고서"""
    try:
        from orders.models import OrderItem
        from django.db.models import Sum, Count, F
        
        # 지난 30일간 주문 데이터 기준
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        bestsellers = OrderItem.objects.filter(
            order__order_date__gte=thirty_days_ago,
            order__status__in=['PROCESSING', 'SHIPPED', 'DELIVERED']
        ).values(
            'product__id', 'product__name', 'product__sku'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price')),
            order_count=Count('order', distinct=True)
        ).order_by('-total_quantity')[:50]
        
    except ImportError:
        bestsellers = []
    
    return render(request, 'products/bestsellers_report.html', {
        'bestsellers': bestsellers,
        'period': '30일'
    })

@login_required
def slow_movers_report(request):
    """느린 회전 상품 보고서"""
    try:
        from orders.models import OrderItem
        
        # 지난 60일간 판매되지 않은 상품들
        sixty_days_ago = timezone.now() - timedelta(days=60)
        
        sold_product_ids = OrderItem.objects.filter(
            order__order_date__gte=sixty_days_ago
        ).values_list('product_id', flat=True).distinct()
        
        slow_movers = Product.objects.filter(
            status='ACTIVE',
            stock_quantity__gt=0
        ).exclude(
            id__in=sold_product_ids
        ).select_related('category', 'brand').order_by('-stock_quantity')
        
    except ImportError:
        # 주문 앱이 없는 경우 재고만으로 판단
        slow_movers = Product.objects.filter(
            status='ACTIVE',
            stock_quantity__gte=F('max_stock_level')
        ).select_related('category', 'brand').order_by('-stock_quantity')
    
    return render(request, 'products/slow_movers_report.html', {
        'slow_movers': slow_movers,
        'period': '60일'
    })

# ====================== 일괄 작업 함수 ======================

@login_required
@require_POST
def product_bulk_action(request):
    """상품 일괄 작업"""
    product_ids = request.POST.getlist('product_ids')
    action = request.POST.get('action')
    
    
    if not product_ids:
        return JsonResponse({'success': False, 'error': '선택된 상품이 없습니다.'})
    
    try:
        products = Product.objects.filter(id__in=product_ids)
        
        if action == 'activate':
            count = products.update(status='ACTIVE')
            message = f'{count}개 상품이 활성화되었습니다.'
        elif action == 'deactivate':
            count = products.update(status='INACTIVE')
            message = f'{count}개 상품이 비활성화되었습니다.'
        elif action == 'feature':
            count = products.update(is_featured=True)
            message = f'{count}개 상품이 추천 상품으로 설정되었습니다.'
        elif action == 'unfeature':
            count = products.update(is_featured=False)
            message = f'{count}개 상품의 추천이 해제되었습니다.'
        elif action == 'delete':
            count = products.count()
            products.delete()
            message = f'{count}개 상품이 삭제되었습니다.'
        else:
            return JsonResponse({'success': False, 'error': '잘못된 작업입니다.'})
        
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== 가져오기 프리뷰 및 확인 ======================

@login_required
def import_preview(request):
    """가져오기 미리보기"""
    import_data = request.session.get('import_data', [])
    
    if not import_data:
        messages.error(request, '가져올 데이터가 없습니다.')
        return redirect('products:import')
    
    # 데이터 검증
    preview_data = []
    errors = []
    
    for index, row in enumerate(import_data[:10]):  # 처음 10개만 미리보기
        row_errors = validate_import_row(row, index + 1)
        preview_data.append({
            'row': row,
            'errors': row_errors,
            'has_errors': bool(row_errors)
        })
        errors.extend(row_errors)
    
    context = {
        'preview_data': preview_data,
        'total_rows': len(import_data),
        'has_errors': bool(errors),
        'error_count': len(errors)
    }
    
    return render(request, 'products/import_preview.html', context)

@login_required
@require_POST
def import_confirm(request):
    """가져오기 확인 및 실행"""
    import_data = request.session.get('import_data', [])
    
    if not import_data:
        return JsonResponse({'success': False, 'error': '가져올 데이터가 없습니다.'})
    
    try:
        with transaction.atomic():
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in enumerate(import_data):
                try:
                    row_errors = validate_import_row(row, index + 1)
                    if row_errors:
                        error_count += 1
                        errors.extend(row_errors)
                        continue
                    
                    # 상품 생성 또는 업데이트
                    create_product_from_import(row, request.user)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f'행 {index + 1}: {str(e)}')
            
            # 세션 데이터 정리
            if 'import_data' in request.session:
                del request.session['import_data']
            
            return JsonResponse({
                'success': True,
                'message': f'총 {success_count}개 상품이 성공적으로 가져왔습니다.',
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors[:10]  # 최대 10개 오류만 표시
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ====================== 웹훅 함수 ======================

@csrf_exempt
@require_POST
def webhook_stock_update(request):
    """외부 플랫폼 재고 업데이트 웹훅"""
    try:
        import json
        data = json.loads(request.body)
        
        sku = data.get('sku')
        new_stock = data.get('stock_quantity')
        platform = data.get('platform', 'unknown')
        
        if not sku or new_stock is None:
            return JsonResponse({'error': 'SKU와 재고 수량이 필요합니다.'}, status=400)
        
        try:
            product = Product.objects.get(sku=sku)
            old_stock = product.stock_quantity
            product.stock_quantity = int(new_stock)
            product.save()
            
            # 재고 이동 기록
            create_stock_movement(
                product, old_stock, int(new_stock), 
                f'{platform} 플랫폼 동기화', None
            )
            
            return JsonResponse({
                'success': True,
                'message': f'상품 {sku}의 재고가 {old_stock}에서 {new_stock}으로 업데이트되었습니다.'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({'error': f'SKU {sku}를 찾을 수 없습니다.'}, status=404)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ====================== 유틸리티 함수들 ======================

def validate_import_row(row, row_number):
    """가져오기 데이터 행 검증"""
    errors = []
    
    # 필수 필드 검사
    if not row.get('SKU'):
        errors.append(f'행 {row_number}: SKU는 필수입니다.')
    
    if not row.get('상품명'):
        errors.append(f'행 {row_number}: 상품명은 필수입니다.')
    
    # SKU 중복 검사
    sku = row.get('SKU')
    if sku and Product.objects.filter(sku=sku).exists():
        errors.append(f'행 {row_number}: SKU "{sku}"는 이미 존재합니다.')
    
    # 가격 검증
    try:
        cost_price = float(row.get('원가', 0))
        selling_price = float(row.get('판매가', 0))
        
        if cost_price < 0:
            errors.append(f'행 {row_number}: 원가는 0 이상이어야 합니다.')
        
        if selling_price <= 0:
            errors.append(f'행 {row_number}: 판매가는 0보다 커야 합니다.')
        
        if selling_price <= cost_price:
            errors.append(f'행 {row_number}: 판매가는 원가보다 높아야 합니다.')
            
    except (ValueError, TypeError):
        errors.append(f'행 {row_number}: 올바른 가격을 입력해주세요.')
    
    return errors

def create_product_from_import(row, user):
    """가져오기 데이터로 상품 생성"""
    # 카테고리 및 브랜드 찾기 또는 생성
    category = None
    if row.get('카테고리코드'):
        category, _ = Category.objects.get_or_create(
            code=row['카테고리코드'],
            defaults={'name': row.get('카테고리명', row['카테고리코드'])}
        )
    
    brand = None
    if row.get('브랜드코드'):
        brand, _ = Brand.objects.get_or_create(
            code=row['브랜드코드'],
            defaults={'name': row.get('브랜드명', row['브랜드코드'])}
        )
    
    # 상품 생성
    product_data = {
        'sku': row['SKU'],
        'name': row['상품명'],
        'category': category,
        'brand': brand,
        'short_description': row.get('간단설명', ''),
        'description': row.get('상세설명', ''),
        'status': 'ACTIVE' if row.get('상태', 'ACTIVE') == 'ACTIVE' else 'INACTIVE',
        'is_featured': row.get('추천상품', '아니오').lower() in ['예', 'yes', 'true', '1'],
        'cost_price': float(row.get('원가', 0)),
        'selling_price': float(row.get('판매가', 0)),
        'discount_price': float(row.get('할인가', 0)) if row.get('할인가') else None,
        'stock_quantity': int(row.get('재고수량', 0)),
        'min_stock_level': int(row.get('최소재고', 0)),
        'max_stock_level': int(row.get('최대재고', 1000)),
        'weight': float(row.get('무게', 0)) if row.get('무게') else None,
        'dimensions_length': float(row.get('길이', 0)) if row.get('길이') else None,
        'dimensions_width': float(row.get('너비', 0)) if row.get('너비') else None,
        'dimensions_height': float(row.get('높이', 0)) if row.get('높이') else None,
        'barcode': row.get('바코드', ''),
        'tags': row.get('태그', ''),
        'created_by': user
    }
    
    return Product.objects.create(**product_data)

@login_required
def export_products_excel(request):
    """상품 Excel 내보내기"""
    try:
        import xlsxwriter
        from io import BytesIO
        from django.http import HttpResponse
        
        # 메모리에 Excel 파일 생성
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('상품목록')
        
        # 스타일 정의
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'text_wrap': True
        })
        
        # 헤더 작성
        headers = [
            'SKU', '상품명', '카테고리', '브랜드', '간단설명', '상세설명',
            '상태', '추천상품', '원가', '판매가', '할인가', '재고수량',
            '최소재고', '최대재고', '무게', '길이', '너비', '높이',
            '바코드', '태그', '등록일'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # 상품 데이터 작성
        products = get_filtered_products(request)
        for row, product in enumerate(products, 1):
            data = [
                product.sku,
                product.name,
                product.category.name if product.category else '',
                product.brand.name if product.brand else '',
                product.short_description,
                product.description,
                product.get_status_display(),
                '예' if product.is_featured else '아니오',
                product.cost_price,
                product.selling_price,
                product.discount_price or '',
                product.stock_quantity,
                product.min_stock_level,
                product.max_stock_level,
                product.weight or '',
                product.dimensions_length or '',
                product.dimensions_width or '',
                product.dimensions_height or '',
                product.barcode,
                product.tags,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            for col, value in enumerate(data):
                worksheet.write(row, col, value, cell_format)
        
        # 컬럼 너비 자동 조정
        for col, header in enumerate(headers):
            worksheet.set_column(col, col, len(header) + 5)
        
        workbook.close()
        output.seek(0)
        
        # HTTP 응답 생성
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="products_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        return response
        
    except ImportError:
        # xlsxwriter가 없는 경우 CSV로 대체
        messages.warning(request, 'Excel 라이브러리가 설치되지 않아 CSV로 내보냅니다.')
        return export_products_csv(request)
    except Exception as e:
        messages.error(request, f'Excel 내보내기 중 오류: {str(e)}')
        return redirect('products:list')
    
def add_product_context(request):
    """템플릿에서 공통으로 사용할 상품 관련 컨텍스트"""
    if request.user.is_authenticated:
        return {
            'total_products_count': Product.objects.filter(status='ACTIVE').count(),
            'low_stock_count': Product.objects.filter(
                stock_quantity__lte=F('min_stock_level'),
                status='ACTIVE'
            ).count()
        }
    return {}

def get_stock_alert_products():
    """재고 부족 상품 조회"""
    return Product.objects.filter(
        stock_quantity__lte=F('min_stock_level'),
        status='ACTIVE'
    ).select_related('category', 'brand')

def calculate_total_inventory_value():
    """전체 재고 가치 계산"""
    return Product.objects.filter(status='ACTIVE').aggregate(
        cost_value=Sum(F('stock_quantity') * F('cost_price')),
        selling_value=Sum(F('stock_quantity') * F('selling_price'))
    )

def get_products_by_category(category_id):
    """카테고리별 상품 조회"""
    return Product.objects.filter(
        category_id=category_id,
        status='ACTIVE'
    ).select_related('brand')

def get_products_by_brand(brand_id):
    """브랜드별 상품 조회"""
    return Product.objects.filter(
        brand_id=brand_id,
        status='ACTIVE'
    ).select_related('category')

def search_products(query):
    """상품 검색"""
    return Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__icontains=query),
        status='ACTIVE'
    ).select_related('category', 'brand')

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

class ProductListView(LoginRequiredMixin, ListView):
    """상품 목록 CBV"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.select_related('brand', 'category').filter(status='ACTIVE')
        return apply_product_filters(queryset, self.request)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_product_stats())
        context.update(get_filter_data())
        context['current_filters'] = extract_current_filters(self.request)
        return context

class ProductDetailView(LoginRequiredMixin, DetailView):
    """상품 상세 CBV"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context.update({
            'images': product.images.all().order_by('sort_order'),
            'recent_movements': get_recent_stock_movements(product),
            'related_products': get_related_products(product),
            'stock_status': check_stock_level(product),
            'profit_margin': calculate_profit_margin(product.cost_price, product.selling_price)
        })
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    """상품 생성 CBV"""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_create.html'
    success_url = reverse_lazy('products:list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '상품이 성공적으로 등록되었습니다.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.filter(is_active=True).order_by('sort_order', 'name'),
            'brands': Brand.objects.filter(is_active=True).order_by('name'),
        })
        return context

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """상품 수정 CBV"""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_edit.html'
    
    def get_success_url(self):
        return reverse_lazy('products:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, '상품이 성공적으로 수정되었습니다.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.filter(is_active=True).order_by('sort_order', 'name'),
            'brands': Brand.objects.filter(is_active=True).order_by('name'),
        })
        return context

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """상품 삭제 CBV"""
    model = Product
    template_name = 'products/product_delete.html'
    success_url = reverse_lazy('products:list')
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'상품 "{product_name}"이 삭제되었습니다.')
        return response

# ====================== 카테고리 CBV ======================

class CategoryListView(LoginRequiredMixin, ListView):
    """카테고리 목록 CBV"""
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('sort_order', 'name')

class CategoryCreateView(LoginRequiredMixin, CreateView):
    """카테고리 생성 CBV"""
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_create.html'
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'카테고리 "{form.instance.name}"이 생성되었습니다.')
        return super().form_valid(form)

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """카테고리 수정 CBV"""
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_edit.html'
    success_url = reverse_lazy('products:category_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'카테고리 "{form.instance.name}"이 수정되었습니다.')
        return super().form_valid(form)

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """카테고리 삭제 CBV"""
    model = Category
    template_name = 'products/category_delete.html'
    success_url = reverse_lazy('products:category_list')
    
    def delete(self, request, *args, **kwargs):
        category = self.get_object()
        if category.products.exists():
            messages.error(request, '이 카테고리를 사용하는 상품이 있어 삭제할 수 없습니다.')
            return redirect('products:category_list')
        elif category.children.exists():
            messages.error(request, '하위 카테고리가 있어 삭제할 수 없습니다.')
            return redirect('products:category_list')
        
        category_name = category.name
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'카테고리 "{category_name}"이 삭제되었습니다.')
        return response

# ====================== 추가 AJAX 뷰들 ======================

@login_required
def get_product_suggestions(request):
    """상품 제안 API (검색 자동완성용)"""
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 10))
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        status='ACTIVE'
    ).select_related('brand', 'category')[:limit]
    
    suggestions = []
    for product in products:
        suggestions.append({
            'id': str(product.id),
            'sku': product.sku,
            'name': product.name,
            'brand': product.brand.name if product.brand else '',
            'category': product.category.name if product.category else '',
            'price': float(product.selling_price),
            'stock': product.stock_quantity,
            'image_url': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else None,
            'display_text': f"{product.name} ({product.sku})"
        })
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def validate_sku_ajax(request):
    """SKU 유효성 검사 AJAX"""
    sku = request.GET.get('sku', '').strip()
    product_id = request.GET.get('product_id')
    
    if not sku:
        return JsonResponse({
            'valid': False,
            'message': 'SKU를 입력해주세요.'
        })
    
    # 길이 검사
    if len(sku) < 3:
        return JsonResponse({
            'valid': False,
            'message': 'SKU는 최소 3자 이상이어야 합니다.'
        })
    
    # 중복 검사
    query = Product.objects.filter(sku=sku)
    if product_id:
        query = query.exclude(pk=product_id)
    
    if query.exists():
        return JsonResponse({
            'valid': False,
            'message': '이미 사용 중인 SKU입니다.'
        })
    
    return JsonResponse({
        'valid': True,
        'message': '사용 가능한 SKU입니다.'
    })

@login_required
def get_category_tree(request):
    """카테고리 트리 구조 API"""
    categories = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
    
    def build_tree(parent_id=None):
        items = []
        for category in categories.filter(parent_id=parent_id):
            item = {
                'id': category.id,
                'name': category.name,
                'code': category.code,
                'level': category.level,
                'product_count': category.products.filter(status='ACTIVE').count(),
                'children': build_tree(category.id)
            }
            items.append(item)
        return items
    
    tree = build_tree()
    return JsonResponse({'tree': tree})

@login_required
def product_quick_edit(request, pk):
    """상품 빠른 수정 AJAX"""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            # 수정 가능한 필드들
            allowed_fields = {
                'name': str,
                'selling_price': float,
                'discount_price': lambda x: float(x) if x else None,
                'stock_quantity': int,
                'status': str,
                'is_featured': lambda x: x.lower() in ['true', '1', 'yes']
            }
            
            updated_fields = []
            for field, converter in allowed_fields.items():
                if field in request.POST:
                    try:
                        new_value = converter(request.POST[field])
                        old_value = getattr(product, field)
                        
                        if new_value != old_value:
                            setattr(product, field, new_value)
                            updated_fields.append(field)
                    except (ValueError, TypeError) as e:
                        return JsonResponse({
                            'success': False,
                            'error': f'{field} 필드 값이 올바르지 않습니다: {str(e)}'
                        })
            
            if updated_fields:
                product.save(update_fields=updated_fields + ['updated_at'])
                return JsonResponse({
                    'success': True,
                    'message': f'{len(updated_fields)}개 필드가 업데이트되었습니다.',
                    'updated_fields': updated_fields
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': '변경된 내용이 없습니다.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET 요청 시 현재 상품 정보 반환
    return JsonResponse({
        'id': str(product.id),
        'sku': product.sku,
        'name': product.name,
        'selling_price': float(product.selling_price),
        'discount_price': float(product.discount_price) if product.discount_price else None,
        'stock_quantity': product.stock_quantity,
        'status': product.status,
        'is_featured': product.is_featured
    })

# ====================== 배치 처리 및 백그라운드 작업 ======================

@login_required
@require_POST
def bulk_import_products(request):
    """대용량 상품 일괄 가져오기"""
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': '파일을 선택해주세요.'})
    
    file = request.FILES['file']
    
    # 파일 크기 검사 (10MB 제한)
    if file.size > 10 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': '파일 크기는 10MB 이하여야 합니다.'})
    
    try:
        # 임시 파일로 저장
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            for chunk in file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # 백그라운드 작업으로 처리 (Celery 사용 시)
        try:
            from .tasks import process_bulk_import
            task = process_bulk_import.delay(tmp_file_path, request.user.id)
            
            return JsonResponse({
                'success': True,
                'message': '파일 처리가 시작되었습니다. 완료되면 알림을 받으실 수 있습니다.',
                'task_id': task.id
            })
        except ImportError:
            # Celery가 없는 경우 동기 처리
            result = process_import_file(tmp_file_path, request.user)
            os.unlink(tmp_file_path)  # 임시 파일 삭제
            
            return JsonResponse({
                'success': True,
                'message': f'{result["success_count"]}개 상품이 처리되었습니다.',
                'details': result
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def process_import_file(file_path, user):
    """가져오기 파일 처리"""
    import pandas as pd
    
    try:
        # 파일 읽기
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 행 검증
                row_dict = row.to_dict()
                validation_errors = validate_import_row(row_dict, index + 1)
                
                if validation_errors:
                    error_count += 1
                    errors.extend(validation_errors)
                    continue
                
                # 상품 생성
                create_product_from_import(row_dict, user)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f'행 {index + 1}: {str(e)}')
        
        return {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors[:20]  # 최대 20개 오류만 반환
        }
        
    except Exception as e:
        return {
            'success_count': 0,
            'error_count': 1,
            'errors': [str(e)]
        }

# ====================== 고급 검색 및 필터링 ======================

@login_required
def advanced_search(request):
    """고급 검색 페이지"""
    return render(request, 'products/advanced_search.html', {
        'categories': Category.objects.filter(is_active=True).order_by('name'),
        'brands': Brand.objects.filter(is_active=True).order_by('name')
    })

@login_required
def search_products_ajax(request):
    """AJAX 상품 검색"""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    brand_id = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    stock_status = request.GET.get('stock_status')
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 20))
    
    # 기본 쿼리셋
    products = Product.objects.filter(status='ACTIVE').select_related('brand', 'category')
    
    # 검색어 필터
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )
    
    # 카테고리 필터
    if category_id:
        products = products.filter(category_id=category_id)
    
    # 브랜드 필터
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # 가격 범위 필터
    if min_price:
        products = products.filter(selling_price__gte=float(min_price))
    if max_price:
        products = products.filter(selling_price__lte=float(max_price))
    
    # 재고 상태 필터
    if stock_status:
        if stock_status == 'in_stock':
            products = products.filter(stock_quantity__gt=0)
        elif stock_status == 'low_stock':
            products = products.filter(stock_quantity__lte=F('min_stock_level'))
        elif stock_status == 'out_of_stock':
            products = products.filter(stock_quantity=0)
    
    # 페이지네이션
    paginator = Paginator(products, per_page)
    page_obj = paginator.get_page(page)
    
    # 결과 직렬화
    results = []
    for product in page_obj:
        results.append({
            'id': str(product.id),
            'sku': product.sku,
            'name': product.name,
            'brand': product.brand.name if product.brand else '',
            'category': product.category.name if product.category else '',
            'selling_price': float(product.selling_price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'stock_quantity': product.stock_quantity,
            'stock_status': check_stock_level(product),
            'is_featured': product.is_featured,
            'image_url': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else None,
            'detail_url': reverse('products:detail', kwargs={'pk': product.pk})
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next()
        }
    })

# ====================== 상품 이미지 최적화 ======================

@login_required
@require_POST
def optimize_product_images(request):
    """상품 이미지 최적화"""
    try:
        from PIL import Image
        import os
        
        optimized_count = 0
        error_count = 0
        errors = []
        
        product_images = ProductImage.objects.all()
        
        for img in product_images:
            try:
                # 이미지 파일 경로
                image_path = img.image.path
                
                # PIL로 이미지 열기
                with Image.open(image_path) as pil_image:
                    # 이미지가 너무 큰 경우 리사이즈
                    max_size = (1200, 1200)
                    if pil_image.size[0] > max_size[0] or pil_image.size[1] > max_size[1]:
                        pil_image.thumbnail(max_size, Image.Resampling.LANCZOS)
                    
                    # JPEG로 변환하여 저장 (품질 85%)
                    if pil_image.mode in ('RGBA', 'LA', 'P'):
                        pil_image = pil_image.convert('RGB')
                    
                    pil_image.save(image_path, 'JPEG', quality=85, optimize=True)
                    optimized_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f'이미지 {img.id}: {str(e)}')
        
        return JsonResponse({
            'success': True,
            'message': f'{optimized_count}개 이미지가 최적화되었습니다.',
            'optimized_count': optimized_count,
            'error_count': error_count,
            'errors': errors[:10]
        })
        
    except ImportError:
        return JsonResponse({
            'success': False,
            'error': 'PIL(Pillow) 라이브러리가 설치되지 않았습니다.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })