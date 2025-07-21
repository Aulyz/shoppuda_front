from .models import SystemSettings


def system_settings(request):
    """시스템 설정을 모든 템플릿에서 사용할 수 있도록 추가"""
    return {
        'system_settings': SystemSettings.get_settings()
    }