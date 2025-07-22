from .models import SystemSettings


def system_settings(request):
    """모든 템플릿에서 시스템 설정을 사용할 수 있도록 하는 context processor"""
    settings = SystemSettings.get_settings()
    return {
        'system_settings': settings,
        'site_name': settings.site_name,
        'site_tagline': settings.site_tagline,
        'site_logo_url': settings.site_logo_url,
    }