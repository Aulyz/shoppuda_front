from django import template
from core.models import SystemSettings

register = template.Library()

@register.simple_tag
def get_system_setting(key, default=''):
    """시스템 설정값을 가져오는 템플릿 태그"""
    try:
        settings = SystemSettings.get_settings()
        return getattr(settings, key, default)
    except:
        return default

@register.simple_tag
def get_site_name():
    """사이트 이름을 가져오는 템플릿 태그"""
    try:
        return SystemSettings.get_settings().site_name
    except:
        return 'Shopuda'

@register.simple_tag
def get_site_tagline():
    """사이트 태그라인을 가져오는 템플릿 태그"""
    try:
        return SystemSettings.get_settings().site_tagline
    except:
        return '온라인 쇼핑몰 통합 관리 시스템'

@register.simple_tag
def get_site_logo():
    """사이트 로고 URL을 가져오는 템플릿 태그"""
    try:
        settings = SystemSettings.get_settings()
        if settings.site_logo:
            return settings.site_logo.url
        return '/media/system/Logo_background_transparent.png'
    except:
        return '/media/system/Logo_background_transparent.png'

@register.simple_tag
def get_contact_email():
    """연락처 이메일을 가져오는 템플릿 태그"""
    try:
        return SystemSettings.get_settings().contact_email
    except:
        return 'admin@shopuda.com'

@register.simple_tag
def get_contact_phone():
    """연락처 전화번호를 가져오는 템플릿 태그"""
    try:
        return SystemSettings.get_settings().contact_phone
    except:
        return '1234-5678'