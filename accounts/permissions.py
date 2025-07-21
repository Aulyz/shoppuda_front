from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse


def permission_required(permission_code, raise_exception=True):
    """특정 권한이 필요한 뷰에 대한 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if raise_exception:
                    raise PermissionDenied("로그인이 필요합니다.")
                messages.error(request, "로그인이 필요합니다.")
                return redirect('accounts:login')
            
            if not request.user.has_permission(permission_code):
                if raise_exception:
                    raise PermissionDenied(f"'{permission_code}' 권한이 필요합니다.")
                messages.error(request, "해당 작업을 수행할 권한이 없습니다.")
                return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def admin_level_required(min_level):
    """최소 관리자 레벨이 필요한 뷰에 대한 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "로그인이 필요합니다.")
                return redirect('accounts:login')
            
            if request.user.user_type != 'ADMIN':
                messages.error(request, "관리자만 접근 가능합니다.")
                return redirect('dashboard:home')
            
            if request.user.admin_level < min_level:
                messages.error(request, f"레벨 {min_level} 이상의 관리자만 접근 가능합니다.")
                return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def ajax_permission_required(permission_code):
    """AJAX 요청에 대한 권한 체크 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'error': '로그인이 필요합니다.'
                }, status=401)
            
            if not request.user.has_permission(permission_code):
                return JsonResponse({
                    'success': False,
                    'error': '권한이 없습니다.'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


class PermissionRequiredMixin(UserPassesTestMixin):
    """클래스 기반 뷰에서 권한을 체크하는 Mixin"""
    permission_code = None
    
    def test_func(self):
        if not self.permission_code:
            raise ValueError("permission_code를 지정해야 합니다.")
        return self.request.user.has_permission(self.permission_code)
    
    def handle_no_permission(self):
        messages.error(self.request, "해당 작업을 수행할 권한이 없습니다.")
        return redirect('dashboard:home')


class AdminLevelRequiredMixin(UserPassesTestMixin):
    """클래스 기반 뷰에서 관리자 레벨을 체크하는 Mixin"""
    min_admin_level = 1
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.user_type == 'ADMIN' and user.admin_level >= self.min_admin_level
    
    def handle_no_permission(self):
        messages.error(self.request, f"레벨 {self.min_admin_level} 이상의 관리자만 접근 가능합니다.")
        return redirect('dashboard:home')


class MultiplePermissionsMixin(UserPassesTestMixin):
    """여러 권한 중 하나라도 있으면 접근 가능한 Mixin"""
    permissions = []
    require_all = False  # True면 모든 권한 필요, False면 하나만 있어도 됨
    
    def test_func(self):
        if not self.permissions:
            raise ValueError("permissions 리스트를 지정해야 합니다.")
        
        user = self.request.user
        if not user.is_authenticated:
            return False
        
        if self.require_all:
            # 모든 권한이 필요한 경우
            return all(user.has_permission(perm) for perm in self.permissions)
        else:
            # 하나라도 있으면 되는 경우
            return any(user.has_permission(perm) for perm in self.permissions)
    
    def handle_no_permission(self):
        if self.require_all:
            messages.error(self.request, "모든 필수 권한이 필요합니다.")
        else:
            messages.error(self.request, "해당 작업을 수행할 권한이 없습니다.")
        return redirect('dashboard:home')


def get_user_menu_permissions(user):
    """사용자의 권한에 따른 메뉴 표시 정보 반환"""
    if not user.is_authenticated:
        return {}
    
    menu_permissions = {
        'dashboard': True,  # 모든 로그인 사용자
        
        # 사용자 관리
        'users': user.has_permission('user_view'),
        'user_create': user.has_permission('user_create'),
        'user_permissions': user.has_permission('user_permission'),
        
        # 상품 관리
        'products': user.has_permission('product_view'),
        'product_create': user.has_permission('product_create'),
        'product_price': user.has_permission('product_price'),
        
        # 주문 관리
        'orders': user.has_permission('order_view'),
        'order_refund': user.has_permission('order_refund'),
        
        # 재고 관리
        'inventory': user.has_permission('inventory_view'),
        'inventory_move': user.has_permission('inventory_move'),
        
        # 보고서
        'reports': user.has_permission('report_view'),
        'report_create': user.has_permission('report_create'),
        'report_schedule': user.has_permission('report_schedule'),
        
        # 플랫폼 관리
        'platforms': user.has_permission('platform_view'),
        'platform_manage': user.has_permission('platform_manage'),
        
        # 시스템 설정
        'system': user.has_permission('system_view'),
        'system_config': user.has_permission('system_config'),
        
        # 재무 관리
        'financial': user.has_permission('financial_view'),
        'financial_manage': user.has_permission('financial_manage'),
    }
    
    # 관리자 레벨별 추가 권한
    if user.user_type == 'ADMIN':
        menu_permissions['admin_level'] = user.admin_level
        menu_permissions['is_super_admin'] = user.admin_level >= 5
    
    return menu_permissions