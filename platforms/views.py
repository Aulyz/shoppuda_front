# File: platforms/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import Platform
from products.models import Product
from orders.models import Order
from products.models import Category


class PlatformListView(LoginRequiredMixin, ListView):
    """플랫폼 목록 뷰"""
    model = Platform
    template_name = 'platforms/platform_list.html'
    context_object_name = 'platforms'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Platform.objects.annotate(
            product_count=Count('platformproduct'),
            order_count=Count('order'),  # Order 모델의 related_name 확인 필요
            total_sales=Sum('order__total_amount')  # Order 모델의 related_name 확인 필요
        ).order_by('-is_active', 'name')
        
        # 검색 필터
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 통계 데이터
        context['total_platforms'] = Platform.objects.count()
        context['active_platforms'] = Platform.objects.filter(is_active=True).count()
        context['sync_errors'] = Platform.objects.filter(last_sync_status='error').count()
        
        return context


class PlatformDetailView(LoginRequiredMixin, DetailView):
    """플랫폼 상세 뷰"""
    model = Platform
    template_name = 'platforms/platform_detail.html'
    context_object_name = 'platform'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        platform = self.object
        
        # 플랫폼 통계
        context['product_count'] = platform.products.count()
        context['order_count'] = platform.orders.count()
        context['total_sales'] = platform.orders.aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # 최근 주문
        context['recent_orders'] = platform.orders.order_by('-order_date')[:5]
        
        # 최근 동기화 로그
        context['recent_syncs'] = platform.sync_logs.order_by('-created_at')[:10]
        
        return context


class PlatformCreateView(LoginRequiredMixin, CreateView):
    """플랫폼 생성 뷰"""
    model = Platform
    template_name = 'platforms/platform_create.html'
    fields = [
        'name', 'platform_type', 'api_endpoint', 'description',
        'is_active', 'sync_enabled', 'sync_interval'
    ]
    
    def get_success_url(self):
        return reverse_lazy('platforms:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'플랫폼 "{self.object.name}"이 생성되었습니다.')
        return response


class PlatformUpdateView(LoginRequiredMixin, UpdateView):
    """플랫폼 수정 뷰"""
    model = Platform
    template_name = 'platforms/platform_edit.html'
    fields = [
        'name', 'platform_type', 'api_endpoint', 'description',
        'is_active', 'sync_enabled', 'sync_interval'
    ]
    
    def get_success_url(self):
        return reverse_lazy('platforms:detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'플랫폼 "{self.object.name}"이 수정되었습니다.')
        return response


@login_required
def platform_delete(request, pk):
    """플랫폼 삭제 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        # 연결된 주문이나 상품이 있는지 확인
        if platform.orders.exists() or platform.products.exists():
            return JsonResponse({
                'error': '연결된 주문이나 상품이 있는 플랫폼은 삭제할 수 없습니다. 비활성화해 주세요.'
            }, status=400)
        
        platform_name = platform.name
        platform.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'플랫폼 "{platform_name}"이 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'플랫폼 삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)


class PlatformSyncDashboardView(LoginRequiredMixin, TemplateView):
    """플랫폼 동기화 대시보드"""
    template_name = 'platforms/sync_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 활성 플랫폼들
        platforms = Platform.objects.filter(is_active=True)
        
        # 동기화 통계
        context['platforms'] = platforms
        context['total_platforms'] = platforms.count()
        context['sync_enabled_count'] = platforms.filter(sync_enabled=True).count()
        context['error_count'] = platforms.filter(last_sync_status='error').count()
        
        # 최근 동기화 로그
        context['recent_sync_logs'] = []  # SyncLog 모델이 있다면 추가
        
        return context


@login_required
def platform_sync(request, pk):
    """개별 플랫폼 동기화 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        if not platform.is_active:
            return JsonResponse({'error': '비활성화된 플랫폼은 동기화할 수 없습니다.'}, status=400)
        
        # 동기화 작업 실행 (실제로는 Celery 태스크로 처리)
        # 여기서는 간단히 상태만 업데이트
        platform.last_sync_at = timezone.now()
        platform.last_sync_status = 'running'
        platform.save()
        
        # 실제 동기화 로직 (예시)
        try:
            # 동기화 작업 시뮬레이션
            sync_result = simulate_platform_sync(platform)
            
            platform.last_sync_status = 'success' if sync_result['success'] else 'error'
            platform.last_sync_message = sync_result['message']
            platform.save()
            
            return JsonResponse({
                'success': sync_result['success'],
                'message': sync_result['message'],
                'synced_products': sync_result.get('synced_products', 0),
                'synced_orders': sync_result.get('synced_orders', 0)
            })
            
        except Exception as sync_error:
            platform.last_sync_status = 'error'
            platform.last_sync_message = str(sync_error)
            platform.save()
            
            return JsonResponse({
                'success': False,
                'message': f'동기화 중 오류가 발생했습니다: {str(sync_error)}'
            })
        
    except Exception as e:
        return JsonResponse({'error': f'동기화 요청 처리 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def sync_all_platforms(request):
    """모든 플랫폼 동기화 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        active_platforms = Platform.objects.filter(is_active=True, sync_enabled=True)
        
        if not active_platforms.exists():
            return JsonResponse({'error': '동기화 가능한 플랫폼이 없습니다.'}, status=400)
        
        # 모든 플랫폼 동기화 시작
        total_platforms = active_platforms.count()
        success_count = 0
        error_count = 0
        
        for platform in active_platforms:
            try:
                platform.last_sync_at = timezone.now()
                platform.last_sync_status = 'running'
                platform.save()
                
                # 동기화 실행
                sync_result = simulate_platform_sync(platform)
                
                if sync_result['success']:
                    success_count += 1
                    platform.last_sync_status = 'success'
                else:
                    error_count += 1
                    platform.last_sync_status = 'error'
                
                platform.last_sync_message = sync_result['message']
                platform.save()
                
            except Exception as e:
                error_count += 1
                platform.last_sync_status = 'error'
                platform.last_sync_message = str(e)
                platform.save()
        
        return JsonResponse({
            'success': True,
            'message': f'동기화 완료: 성공 {success_count}개, 실패 {error_count}개',
            'total_platforms': total_platforms,
            'success_count': success_count,
            'error_count': error_count
        })
        
    except Exception as e:
        return JsonResponse({'error': f'전체 동기화 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def sync_status(request):
    """동기화 상태 조회 - AJAX"""
    try:
        platforms = Platform.objects.filter(is_active=True).values(
            'id', 'name', 'last_sync_at', 'last_sync_status', 'last_sync_message'
        )
        
        status_data = []
        for platform in platforms:
            status_data.append({
                'id': platform['id'],
                'name': platform['name'],
                'last_sync_at': platform['last_sync_at'].isoformat() if platform['last_sync_at'] else None,
                'status': platform['last_sync_status'] or 'never',
                'message': platform['last_sync_message'] or '',
                'status_display': {
                    'success': '성공',
                    'error': '오류',
                    'running': '진행중',
                    'never': '미실행'
                }.get(platform['last_sync_status'], '알 수 없음')
            })
        
        return JsonResponse({
            'success': True,
            'platforms': status_data,
            'last_updated': timezone.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': f'상태 조회 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def platform_products(request, pk):
    """플랫폼 상품 목록"""
    platform = get_object_or_404(Platform, pk=pk)
    
    # 플랫폼 상품 목록 (실제로는 플랫폼별 상품 매핑 테이블이 있어야 함)
    products = Product.objects.filter(status='ACTIVE')
    
    # 검색 필터
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )
    
    # 페이지네이션
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'platform': platform,
        'products': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }
    
    return render(request, 'platforms/platform_products.html', context)


@login_required
def sync_platform_products(request, pk):
    """플랫폼 상품 동기화 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        # 상품 동기화 로직 (실제로는 플랫폼 API 호출)
        sync_result = simulate_product_sync(platform)
        
        return JsonResponse({
            'success': sync_result['success'],
            'message': sync_result['message'],
            'synced_count': sync_result.get('synced_count', 0)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'상품 동기화 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def platform_orders(request, pk):
    """플랫폼 주문 목록"""
    platform = get_object_or_404(Platform, pk=pk)
    
    orders = platform.orders.order_by('-order_date')
    
    # 검색 필터
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(customer_name__icontains=search)
        )
    
    # 페이지네이션
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'platform': platform,
        'orders': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    }
    
    return render(request, 'platforms/platform_orders.html', context)


@login_required
def sync_platform_orders(request, pk):
    """플랫폼 주문 동기화 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        # 주문 동기화 로직
        sync_result = simulate_order_sync(platform)
        
        return JsonResponse({
            'success': sync_result['success'],
            'message': sync_result['message'],
            'synced_count': sync_result.get('synced_count', 0)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'주문 동기화 중 오류가 발생했습니다: {str(e)}'}, status=500)


class PlatformSettingsView(LoginRequiredMixin, TemplateView):
    """플랫폼 설정 페이지"""
    template_name = 'platforms/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['platforms'] = Platform.objects.all()
        return context


class PlatformSettingUpdateView(LoginRequiredMixin, UpdateView):
    """플랫폼 개별 설정 수정"""
    model = Platform
    template_name = 'platforms/platform_settings.html'
    fields = ['api_key', 'api_secret', 'api_endpoint', 'sync_interval', 'sync_enabled']
    
    def get_success_url(self):
        return reverse('platforms:settings')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'"{self.object.name}" 설정이 저장되었습니다.')
        return response


@login_required
def platform_test_connection(request, pk):
    """플랫폼 연결 테스트 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        # 연결 테스트 로직 (실제로는 플랫폼 API 호출)
        test_result = simulate_connection_test(platform)
        
        return JsonResponse({
            'success': test_result['success'],
            'message': test_result['message'],
            'response_time': test_result.get('response_time', 0)
        })
        
    except Exception as e:
        return JsonResponse({'error': f'연결 테스트 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def platform_api_keys(request, pk):
    """플랫폼 API 키 관리"""
    platform = get_object_or_404(Platform, pk=pk)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            api_key = data.get('api_key', '').strip()
            api_secret = data.get('api_secret', '').strip()
            
            if not api_key or not api_secret:
                return JsonResponse({'error': 'API 키와 시크릿을 모두 입력해주세요.'}, status=400)
            
            # API 키 저장 (실제로는 암호화해서 저장)
            platform.api_key = api_key
            platform.api_secret = api_secret
            platform.save()
            
            return JsonResponse({
                'success': True,
                'message': 'API 키가 저장되었습니다.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'API 키 저장 중 오류가 발생했습니다: {str(e)}'}, status=500)
    
    return render(request, 'platforms/api_keys.html', {'platform': platform})


@login_required
def test_api_keys(request, pk):
    """API 키 테스트 - AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)
    
    try:
        platform = get_object_or_404(Platform, pk=pk)
        
        if not platform.api_key or not platform.api_secret:
            return JsonResponse({'error': 'API 키가 설정되지 않았습니다.'}, status=400)
        
        # API 키 테스트 로직
        test_result = simulate_api_test(platform)
        
        return JsonResponse({
            'success': test_result['success'],
            'message': test_result['message'],
            'api_version': test_result.get('api_version', 'Unknown')
        })
        
    except Exception as e:
        return JsonResponse({'error': f'API 키 테스트 중 오류가 발생했습니다: {str(e)}'}, status=500)


@login_required
def platform_mapping(request, pk):
    """플랫폼 매핑 관리"""
    platform = get_object_or_404(Platform, pk=pk)
    
    context = {
        'platform': platform,
        # 실제로는 매핑 테이블에서 데이터 조회
    }
    
    return render(request, 'platforms/mapping.html', context)


@login_required
def category_mapping(request, pk):
    """카테고리 매핑 관리"""
    platform = get_object_or_404(Platform, pk=pk)
    
    # 실제로는 플랫폼-카테고리 매핑 테이블 조회
    context = {
        'platform': platform,
        'categories': Category.objects.filter(is_active=True),
    }
    
    return render(request, 'platforms/category_mapping.html', context)


@login_required
def attribute_mapping(request, pk):
    """속성 매핑 관리"""
    platform = get_object_or_404(Platform, pk=pk)
    
    context = {
        'platform': platform,
        # 실제로는 속성 매핑 데이터 조회
    }
    
    return render(request, 'platforms/attribute_mapping.html', context)


# 동기화 시뮬레이션 함수들 (실제 환경에서는 실제 API 호출로 대체)
def simulate_platform_sync(platform):
    """플랫폼 동기화 시뮬레이션"""
    import random
    import time
    
    # 실제로는 플랫폼 API 호출
    time.sleep(1)  # API 호출 시뮬레이션
    
    success = random.choice([True, True, True, False])  # 75% 성공률
    
    if success:
        synced_products = random.randint(10, 100)
        synced_orders = random.randint(5, 50)
        return {
            'success': True,
            'message': f'동기화 완료: 상품 {synced_products}개, 주문 {synced_orders}개',
            'synced_products': synced_products,
            'synced_orders': synced_orders
        }
    else:
        error_messages = [
            'API 연결 오류',
            '인증 실패',
            '요청 한도 초과',
            '서버 오류'
        ]
        return {
            'success': False,
            'message': random.choice(error_messages),
            'synced_products': 0,
            'synced_orders': 0
        }


def simulate_product_sync(platform):
    """상품 동기화 시뮬레이션"""
    import random
    import time
    
    time.sleep(0.5)
    success = random.choice([True, True, False])
    
    if success:
        synced_count = random.randint(5, 50)
        return {
            'success': True,
            'message': f'{synced_count}개 상품이 동기화되었습니다.',
            'synced_count': synced_count
        }
    else:
        return {
            'success': False,
            'message': '상품 동기화 중 오류가 발생했습니다.',
            'synced_count': 0
        }


def simulate_order_sync(platform):
    """주문 동기화 시뮬레이션"""
    import random
    import time
    
    time.sleep(0.5)
    success = random.choice([True, True, False])
    
    if success:
        synced_count = random.randint(1, 20)
        return {
            'success': True,
            'message': f'{synced_count}개 주문이 동기화되었습니다.',
            'synced_count': synced_count
        }
    else:
        return {
            'success': False,
            'message': '주문 동기화 중 오류가 발생했습니다.',
            'synced_count': 0
        }


def simulate_connection_test(platform):
    """연결 테스트 시뮬레이션"""
    import random
    import time
    
    start_time = time.time()
    time.sleep(random.uniform(0.1, 0.5))
    response_time = (time.time() - start_time) * 1000
    
    success = random.choice([True, True, True, False])
    
    if success:
        return {
            'success': True,
            'message': '연결 테스트 성공',
            'response_time': round(response_time, 2)
        }
    else:
        return {
            'success': False,
            'message': '연결 테스트 실패: 타임아웃',
            'response_time': round(response_time, 2)
        }


def simulate_api_test(platform):
    """API 키 테스트 시뮬레이션"""
    import random
    import time
    
    time.sleep(0.3)
    success = random.choice([True, True, False])
    
    if success:
        return {
            'success': True,
            'message': 'API 인증 성공',
            'api_version': 'v2.1'
        }
    else:
        return {
            'success': False,
            'message': 'API 인증 실패: 잘못된 키',
            'api_version': None
        }