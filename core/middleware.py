from django.shortcuts import render
from django.urls import reverse
from django.conf import settings
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