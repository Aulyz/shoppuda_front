from .permissions import get_user_menu_permissions


def user_permissions(request):
    """모든 템플릿에서 사용자 권한 정보를 사용할 수 있도록 하는 컨텍스트 프로세서"""
    if request.user.is_authenticated:
        return {
            'user_permissions': get_user_menu_permissions(request.user),
            'user_type': request.user.user_type,
            'admin_level': request.user.admin_level if request.user.user_type == 'ADMIN' else 0,
        }
    return {
        'user_permissions': {},
        'user_type': None,
        'admin_level': 0,
    }