from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_dashboard(request):
    """루트 URL에서 대시보드로 리다이렉트"""
    return redirect('dashboard:home')

urlpatterns = [
    # 관리자
    path('admin/', admin.site.urls),
    
    # 루트 URL
    path('', redirect_to_dashboard),
    
    # 앱 URL들
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('inventory/', include('inventory.urls')),
    path('platforms/', include('platforms.urls')),
    path('api/', include('api.urls')),
    path('reports/', include('reports.urls')),
    
    path('notifications/', include('notifications.urls')),
    path('search/', include('search.urls')),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 관리자 사이트 커스터마이징
admin.site.site_header = 'Shopuda ERP 관리'
admin.site.site_title = 'Shopuda ERP'
admin.site.index_title = 'Shopuda ERP 관리자'
