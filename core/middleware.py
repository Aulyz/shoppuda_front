from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from .models import SystemSettings


class MaintenanceModeMiddleware:
    """유지보수 모드 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 시스템 설정 가져오기
        system_settings = SystemSettings.get_settings()
        
        # 유지보수 모드가 활성화되어 있는지 확인
        if system_settings.maintenance_mode:
            # 제외할 URL 패턴들
            allowed_urls = [
                reverse('accounts:login'),
                reverse('accounts:logout'),
                reverse('admin:index'),
            ]
            
            # 정적 파일 및 미디어 파일 요청 허용
            if any([
                request.path.startswith('/static/'),
                request.path.startswith('/media/'),
                request.path.startswith('/admin/'),
                request.path in allowed_urls,
            ]):
                response = self.get_response(request)
                return response
            
            # 관리자는 접근 허용
            if request.user.is_authenticated and request.user.user_type == 'ADMIN':
                response = self.get_response(request)
                return response
            
            # 일반 사용자는 유지보수 페이지로 리다이렉트
            return render(request, 'core/maintenance.html', {
                'maintenance_message': system_settings.maintenance_message or '시스템 점검 중입니다. 잠시 후 다시 시도해주세요.',
                'site_name': system_settings.site_name
            })
        
        response = self.get_response(request)
        return response


class AdminAccessMiddleware:
    """관리자/사용자 접근 제어 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 정적 파일, 미디어 파일은 제외
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)
            
        # 로그인 관련 URL은 제외
        if request.path in ['/accounts/login/', '/accounts/logout/', '/accounts/signup/']:
            return self.get_response(request)
        
        # 사용자가 로그인한 경우
        if request.user.is_authenticated:
            is_admin = request.user.user_type == 'ADMIN'
            
            # 관리자 전용 경로 목록
            admin_paths = [
                '/dashboard/',
                '/products/',
                '/orders/',
                '/inventory/',
                '/platforms/',
                '/reports/',
                '/core/',
                '/notifications/',
                '/search/',
            ]
            
            # 일반 사용자가 관리자 페이지 접근 시도
            is_admin_path = any(request.path.startswith(path) for path in admin_paths)
            
            if not is_admin and is_admin_path:
                messages.error(request, '관리자 권한이 필요합니다.')
                return redirect('shop:home')
        else:
            # 비로그인 사용자가 관리자 페이지 접근 시도
            admin_paths = [
                '/dashboard/',
                '/products/',
                '/orders/',
                '/inventory/',
                '/platforms/',
                '/reports/',
                '/core/',
                '/notifications/',
                '/search/',
            ]
            
            is_admin_path = any(request.path.startswith(path) for path in admin_paths)
            
            if is_admin_path:
                messages.warning(request, '로그인이 필요합니다.')
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
        
        response = self.get_response(request)
        return response


class UserTypeRedirectMiddleware:
    """사용자 타입에 따른 리디렉션 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # 이 미들웨어는 더 이상 필요하지 않음
        # 루트 경로는 이미 shop:home으로 매핑되어 있음
        response = self.get_response(request)
        return response